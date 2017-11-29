import urllib.request
import json
import re
from html.parser import HTMLParser

def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def analyze(data):
    # The text to analyze
    document = types.Document(
        content=data,
        type=enums.Document.Type.PLAIN_TEXT)

    # Detects the sentiment of the text
    sentiment = client.analyze_sentiment(document=document).document_sentiment

    # print('Text: {}'.format(data))
    print('Sentiment: {}, {}'.format(sentiment.score, sentiment.magnitude))


url = "https://tuftsdaily.com/wp-json/wp/v2/tags"
connection = urllib.request.urlopen(url)
input = connection.read()
connection.close()

print(input)

dataAry = json.loads(input)
for x in dataAry:
    x['content']['rendered'] = cleanhtml(x['content']['rendered'])

# Imports the Google Cloud client library
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

# Instantiates a client
client = language.LanguageServiceClient()
#
# htmlParser = HTMLParser()
# for x in dataAry:
#     print('Title:' + htmlParser.unescape(x['title']['rendered']))
#     # analyze(x['content']['rendered'])
#     print('\n')
