import urllib.request
import json
import datetime
from getPosts import dumpJsonAry, getGmt
from print_progress import print_progress
import os

entity_type = ('UNKNOWN', 'PERSON', 'LOCATION', 'ORGANIZATION',
                   'EVENT', 'WORK_OF_ART', 'CONSUMER_GOOD', 'OTHER')
# with open(os.environ["GOOGLE_APPLICATION_CREDENTIALS"], "r") as cred:
with open("api_key", "r") as cred:
    API_key = cred.read()
    print("CREDENTIALS: ", API_key)
file = open("posts_sample.db", "r", encoding='utf-8-sig')
posts = json.load(file)
print(str(len(posts) - 1), " posts read")
print("Posts retrieved on ", posts[0]["metadata"]["posts_gmt"], " gmt")

posts[0]["metadata"]["analysis_gmt"] = datetime.datetime.strftime(getGmt(), "%Y-%m-%dT%H:%M:%S")

#merge async results with post
def addResults(responses, posts):
    for x in range(0, len(responses)):
        analysis = {}
        analysis["sentiment_score"] = responses[x][0]["documentSentiment"]["score"]
        analysis["sentiment_magnitude"] = responses[x][0]["documentSentiment"]["magnitude"]

        things = []
        for entity in responses[x][1]["entities"]:
            # print(entity)
            # print("\n")
            thing = {}
            thing["name"] = entity["name"]
            thing["type"] = entity["type"]
            thing["salience"] = entity["salience"]
            thing["sentiment_score"] = entity["sentiment"]["score"]
            thing["sentiment_megnitude"] = entity["sentiment"]["magnitude"]
            things.append(thing)

        analysis["entitiy_sentiments"] = things
        posts[x + 1]["analysis"] = analysis
    return posts

#setting up Google NLP API links
article_sentiment_url = "https://language.googleapis.com/v1/documents:analyzeSentiment?key=" + API_key
entity_sentiment_url = "https://language.googleapis.com/v1/documents:analyzeEntitySentiment?key=" + API_key

#async code
import asyncio
from aiohttp import ClientSession

#gets response
async def fetch(data, session):
    result = []
    async with session.post(article_sentiment_url, data=data) as response:
        result.append(json.loads((await response.read()).decode("utf-8")))
    async with session.post(entity_sentiment_url, data=data) as response:
        result.append(json.loads((await response.read()).decode("utf-8")))
        # print(result)
        # print("\n")
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
    async with ClientSession() as session:
        for x in range(1, length):
            document = {}
            document["type"] = "PLAIN_TEXT"
            document["content"] = posts[x]["content_text"]
            data = {}
            data["encodingType"] = "UTF8"
            data["document"] = document

            # print(document)
            task = asyncio.ensure_future(fetch(json.dumps(data), session))
            tasks.insert(x - 1, task)

        responses = await asyncio.gather(*tasks)

        # you now have all response bodies in this variable
        print(str(len(responses)), " responses gotten")
        print("async requests complete, compiling results")
        output = addResults(responses, posts)
        dumpJsonAry(output, "async_result_" + str(len(posts) - 1) + "_" + datetime.datetime.strftime(getGmt(), "%Y%m%d%H%M%S") + ".json")

        # with open("test.json","w") as file:

loop = asyncio.get_event_loop()
future = asyncio.ensure_future(run(posts))
loop.run_until_complete(future)
print("DONE")
