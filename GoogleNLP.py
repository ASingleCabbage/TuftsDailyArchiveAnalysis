import urllib.request
import json
import datetime
from getPosts import dumpJsonAry, getGmt
from print_progress import print_progress
import aiohttp
import os

entity_type = ('UNKNOWN', 'PERSON', 'LOCATION', 'ORGANIZATION',
                   'EVENT', 'WORK_OF_ART', 'CONSUMER_GOOD', 'OTHER')
with open(os.environ["GOOGLE_APPLICATION_CREDENTIALS"], "r") as cred:
    API_key = cred.read()

# Imports the Google Cloud client library
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

def analyze(post):
    # The text to analyze
    document = types.Document(
        content=post["content_text"],
        type=enums.Document.Type.PLAIN_TEXT)
    # Detects the sentiment of the text
    sentiment = client.analyze_sentiment(document=document).document_sentiment
    print(sentiment)
    analysis = {}
    analysis["sentiment_score"] = sentiment.score
    analysis["sentiment_magnitude"] = sentiment.magnitude

    result = client.analyze_entity_sentiment(document)

    things = []
    for entity in result.entities:
        thing = {}
        thing["name"] = entity.name
        thing["type"] = entity_type[entity.type]
        thing["salience"] = entity.salience
        thing["sentiment_score"] = entity.sentiment.score
        thing["sentiment_megnitude"] = entity.sentiment.magnitude
        things.append(thing)

    analysis["entitiy_sentiments"] = things

    post["analysis"] = analysis
    return post

file = open("posts_sample.db", "r", encoding='utf-8-sig')
posts = json.load(file)
print(str(len(posts) - 1), " posts read")
print("Posts retrieved on ", posts[0]["metadata"]["posts_gmt"], " gmt")

# Instantiates a client
client = language.LanguageServiceClient()

posts[0]["metadata"]["analysis_gmt"] = datetime.datetime.strftime(getGmt(), "%Y-%m-%dT%H:%M:%S")
length =  len(posts)
index = 0
for x in range(1, length):
    print_progress(index, length - 1, prefix = "Running sentiment analysis: ", bar_length = 80)
    posts[x] = analyze(posts[x])
    index += 1

dumpJsonAry(posts, "post_sentiment_entity_" + str(length - 1) + "_" + datetime.datetime.strftime(getGmt(), "%Y%m%d%H%M%S") + ".json")
