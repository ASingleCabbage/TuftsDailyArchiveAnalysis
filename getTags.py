#Gets all responses on the Tufts Daily website using Wordpress REST API
import urllib.request
import json
import codecs
import html
import datetime
from bs4 import BeautifulSoup
from print_progress import print_progress

#remove html tags and decodes html
def cleanhtml(raw_html):
    soup = BeautifulSoup(raw_html, "html5lib");
    return soup.get_text()

#get greenwich mean time
def getGmt():
    endpoint = "http://api.timezonedb.com/v2/get-time-zone"
    key = "I1IL8FGV1FXS"
    format = "json"
    zone = "UTC"
    request = endpoint + "?key=" + key + "&format=" + format + "&by=zone&zone=" + zone
    print("Request: ", request, end="\r")
    connection = urllib.request.urlopen(request)
    response = json.loads(connection.read())
    connection.close()
    return datetime.datetime.fromtimestamp(response["timestamp"])
 

    
#all this for the sake of modularity
endpoint = "https://tuftsdaily.com/wp-json/wp/v2/tags"
per_page_value = 100  #1 to 100 inclusive
per_page = "?per_page=" + str(per_page_value)
offset = "&offset="
responses = []
iteration = 0
while True:
    request = endpoint + per_page + offset + str(iteration * per_page_value) 
    print("Request: ", request, end="\r")
    connection = urllib.request.urlopen(request)
    response_array = json.loads(connection.read())
    connection.close()
    
    if(len(response_array) == 0):
        break
    else:
        # print(len(response_array), "response gotten from connection", end="\r")
        #shallow copying arrays, hopefully ends out okay
        responses += response_array
        iteration += 1

def dumpJsonAry(jsons, filename):
    file = codecs.open(filename, "w", "utf-8-sig")
    file.write("[")
    for x in jsons:
        file.write(json.dumps(x, indent=4, sort_keys=True))
        file.write(",\n")
    file.write("]")
    file.close()
    

#dumps unprocessed json array to file
dumpJsonAry(responses, "tags_raw.json")

def cleanResponse(json):
    del json["_links"]
    del json["description"]
    del json["link"]
    del json["meta"]
    del json["slug"]
    del json["taxonomy"]
    return json

response_length = len(responses)
index = 0
cleaned_responses = []
#clean up jsons
for x in responses:
    #deleting tags with 0 occurances (which there actually are many)
    if(x["count"] != 0):
        cleaned_responses.append(cleanResponse(x))
    index += 1
    print_progress(index, response_length, prefix = "Cleaning up jsons: ", bar_length=80)
    
    
dumpJsonAry(cleaned_responses, "tags_cleaned.json")

