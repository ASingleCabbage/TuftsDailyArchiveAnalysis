#Gets all responses on the Tufts Daily website using Wordpress REST API
import urllib.request
import json
import codecs
import html
import datetime
from bs4 import BeautifulSoup
from print_progress import print_progress

#PROBLEMS:
#I can't remove random unicode things from the output file
#ze encoding and decoding, zey do nothing

#remove html tags and decodes html
def cleanhtml(raw_html):
    soup = BeautifulSoup(raw_html, "html5lib")
    return soup.get_text()

#get greenwich mean time
def getGmt():
    endpoint = "http://api.timezonedb.com/v2/get-time-zone"
    key = "I1IL8FGV1FXS"
    format = "json"
    zone = "UTC"
    request = endpoint + "?key=" + key + "&format=" + format + "&by=zone&zone=" + zone
    connection = urllib.request.urlopen(request)
    response = json.loads(connection.read())
    connection.close()
    return datetime.datetime.fromtimestamp(response["timestamp"])

def dumpJsonAry(jsons, filename):
    file = codecs.open(filename, "w", "utf-8-sig")
    file.write("[")
    for x in jsons:
        file.write(json.dumps(x, indent=4, sort_keys=True))
        file.write(",\n")
    file.seek(-2, 2)
    file.write("] ")
    file.close()

#process json
#doesnt work maybe try with smaller scale
#problem found use "del json['_links']" instead
def cleanResponse(json):
    del json["_links"]
    del json["comment_status"]
    json["content_text"] = cleanhtml(json["content"]["rendered"])
    json["excerpt_text"] = cleanhtml(json["excerpt"]["rendered"])
    del json["excerpt"]
    del json["content"]
    del json["meta"]
    del json["status"]
    del json["sticky"]
    del json["template"]
    del json["type"]
    del json["ping_status"]
    del json["format"]
    json["guid"] = json["guid"]["rendered"]
    json["title_text"] = cleanhtml(json["title"]["rendered"])
    del json["title"]
    return json

def updateMetadata(posts):
    if hasattr(posts[0], "metadata"):
        length = len(posts) - 1
    else:
        length = len(posts)

    gmtStr = getGmt().strftime("%Y-%m-%dT%H:%M:%S")
    data = {}
    data["posts_length"] = length
    data["posts_gmt"] = gmtStr
    metadata = {}
    metadata["metadata"] = data
    posts.insert(0, metadata)
    return posts

def main():
    #all this for the sake of modularity
    endpoint = "https://tuftsdaily.com/wp-json/wp/v2/posts"
    per_page_value = 100  #1 to 100 inclusive
    per_page = "?per_page=" + str(per_page_value)
    offset = "&offset="
    responses = []
    iteration = 0
    while True:
        request = endpoint + per_page + offset + str(iteration * per_page_value)
        print("Request: ", request)
        connection = urllib.request.urlopen(request)
        response_array = json.loads(connection.read())
        connection.close()

        if(len(response_array) == 0):
            break
        else:
            print(len(response_array), "response gotten from connection")
            #shallow copying arrays, hopefully ends out okay
            responses += response_array
            iteration += 1
            break
    #dumps unprocessed json array to file
    # dumpJsonAry(responses, "posts_raw.json")

    response_length = len(responses)
    index = 0
    #clean up jsons
    responses_clean = []
    for x in responses:
        x = cleanResponse(x)
        if (x["content_text"] != "\n"):
            responses_clean.append(x)
        index += 1
        print_progress(index, response_length, prefix = "Cleaning up jsons: ", bar_length=80)

    responses_clean = updateMetadata(responses_clean)

    dumpJsonAry(responses_clean, "posts_sample.db")

if __name__ == "__main__":
    main()
