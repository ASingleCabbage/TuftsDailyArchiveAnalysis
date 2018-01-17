import urllib.request
import json
import datetime
import types
# import argparse
from getPosts import dumpJsonAry, getGmt
from print_progress import print_progress
from debug_tools import dump
import os, sys
entity_type = ('UNKNOWN', 'PERSON', 'LOCATION', 'ORGANIZATION',
                   'EVENT', 'WORK_OF_ART', 'CONSUMER_GOOD', 'OTHER')

# with open(os.environ["GOOGLE_APPLICATION_CREDENTIALS"], "r") as cred:
# TODO check if file not found
with open("api_key", "r") as cred:
    API_key = cred.read()

# read in filename from command line
if (len(sys.argv) < 2):
    print("Not enough arguments")
    print("usage: ", str(sys.argv[0]), " [input filename]")
    exit(1)

file = open(str(sys.argv[1]), "r", encoding='utf-8-sig')
posts = json.load(file)
post_count = len(posts) - 1
print(str(post_count), " posts read")
print("Posts retrieved on ", posts[0]["metadata"]["posts_gmt"], " gmt")

#adding date tag for analysis
posts[0]["metadata"]["analysis_gmt"] = datetime.datetime.strftime(getGmt(), "%Y-%m-%dT%H:%M:%S")

#merge async results with post
def addResults(responses, posts):
    # responses is a list of response object, which should have 2 fields, entity_sentiment
    # and article_sentiment
    response_count = len(responses)
    for x in range(0, response_count):
        print_progress(x, response_count - 1, prefix = "Compiling Results: ", bar_length = 80)
        analysis = {}
        things = []
        try:
            for entity in responses[x].entity_sentiment["entities"]:
                thing = {}
                thing["name"] = entity["name"]
                thing["type"] = entity["type"]
                thing["salience"] = entity["salience"]
                thing["sentiment_score"] = entity["sentiment"]["score"]
                thing["sentiment_megnitude"] = entity["sentiment"]["magnitude"]
                things.append(thing)
        # its-a-workaround
        except (KeyError, AttributeError) as e:
            dump(responses[x])
            thing = {}
            thing["error"] = True
            thing["message"] = "Error encountered when parsing results for this article..."
        analysis["entitiy_sentiments"] = things

        try:
            analysis["sentiment_magnitude"] = responses[x].article_sentiment["documentSentiment"]["magnitude"]
            analysis["sentiment_score"] = responses[x].article_sentiment["documentSentiment"]["score"]
        except (KeyError, AttributeError) as e:
            analysis["sentiment_magnitude"] = "Error"
            analysis["sentiment_score"] = "Error"

        posts[x + 1]["analysis"] = analysis
    return posts

#setting up Google NLP API links
article_sentiment_url = "https://language.googleapis.com/v1/documents:analyzeSentiment?key=" + API_key
entity_sentiment_url = "https://language.googleapis.com/v1/documents:analyzeEntitySentiment?key=" + API_key
responses_recieved = 0

#async code
import asyncio
import aiohttp
# from contextlib import suppress
#gets response
async def fetch(data, session):
    result = types.SimpleNamespace()
    unexpected_attempts = 5
    while unexpected_attempts != 0:
        async with session.post(article_sentiment_url, data=data) as response:
            if(response.status != 200):
                if(response.status == 429):
                    print("Request quota reached, pausing for 3 seconds...")
                else:
                    unexpected_attempts -= 1
                    print("unanticipated error ", str(response.status), "encountered; retrying after 3 seconds...")
                    print((await response.read()).decode("utf-8"))
                await asyncio.sleep(3)
            else:
                result.article_sentiment = json.loads((await response.read()).decode("utf-8"))
                break;

    if(unexpected_attempts == 0):
        print("skipped after too many errors")
    unexpected_attempts = 5

    while unexpected_attempts != 0:
        async with session.post(entity_sentiment_url, data=data) as response:
            if(response.status != 200):
                if(response.status == 429):
                    print("Request quota reached, pausing for 3 seconds...")
                else:
                    unexpected_attempts -= 1
                    print("unanticipated error ", str(response.status), "encountered; retrying after 3 seconds...")
                    print((await response.read()).decode("utf-8"))
                await asyncio.sleep(3)
            else:
                result.entity_sentiment = json.loads((await response.read()).decode("utf-8"))
                break;
    if(unexpected_attempts == 0):
        print("skipped after too many errors")

    global responses_recieved
    responses_recieved += 1
    print_progress(responses_recieved, post_count, prefix = "Responses recieved: ", bar_length = 80)
    return result

async def run(posts):
    tasks = []
    length = len(posts)

    # Fetch all responses within one Client session,
    # keep connection alive for all requests.
    # Request payload is json that looks like this:
    # {
    #     "encodingType": "UTF8",
    #     "document": {
    #         "type": "PLAIN_TEXT",
    #         "content": posts[x]["content_text"]
    #     }
    # }

    #set limit to 10 fo fit within the quota
    connector = aiohttp.TCPConnector(limit=9)
    client = aiohttp.ClientSession(connector=connector, read_timeout=None)
    print("aiohttp client setup complete, sending out requests...")
    async with client as session:
        for x in range(1, length):
            document = {}
            document["type"] = "PLAIN_TEXT"
            document["content"] = posts[x]["content_text"]
            data = {}
            data["encodingType"] = "UTF8"
            data["document"] = document

            task = asyncio.ensure_future(fetch(json.dumps(data), session))
            tasks.insert(x - 1, task)

        try:
            responses = await asyncio.gather(*tasks)
        except aiohttp.client_exceptions.ServerDisconnectedError as e:
            print("Cannot connect to server...")

        # you now have all response bodies in this variable
        print(str(responses_recieved), " responses gotten")
        output = addResults(responses, posts)
        output_filename = "async_result_" + str(length - 1) + "_" + datetime.datetime.strftime(getGmt(), "%Y%m%d%H%M%S") + ".json"
        dumpJsonAry(output, output_filename)
        print("Results printed to file ", output_filename)

loop = asyncio.get_event_loop()
future = asyncio.ensure_future(run(posts))
loop.run_until_complete(future)
print("DONE")
