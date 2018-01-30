#Gets all responses on the Tufts Daily website using Wordpress REST API
import urllib.request
import json
import codecs
import html
import datetime
import os, sys
from bs4 import BeautifulSoup
from print_progress import print_progress

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
    file = open(filename, "w", encoding="utf8")
    file.write("[")
    for x in jsons:
        # ensure ascii needed so json.dump won't print out escaped unicode
        json.dump(x, file, indent=4, sort_keys=True, ensure_ascii=False)
        file.write(",\n")

    print("Cleaning up file ending")
    file.seek(0, os.SEEK_END)
    pos = file.tell() - 3
    file.seek(pos, os.SEEK_SET)
    file.truncate()
    file.write("]")
    file.close()

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

    #changed this to more general terms
    # original was posts_length and posts_gmt

    data["data_length"] = length
    data["retrieve_gmt"] = gmtStr
    metadata = {}
    metadata["metadata"] = data
    posts.insert(0, metadata)
    return posts

def main():
    global target_count
    if(len(sys.argv) == 1):
        print("No post limit set, getting all posts...")
        target_count = sys.maxsize
    else:
        assert int(sys.argv[1]) > 0
        print("Post target set to ", sys.argv[1])
        target_count = int(sys.argv[1])

    #all this for the sake of modularity
    endpoint = "https://tuftsdaily.com/wp-json/wp/v2/categories"
    per_page_value = 100  #1 to 100 inclusive
    per_page = "?per_page=" + str(per_page_value)
    offset = "&offset="
    responses = []
    iteration = 0

    while (len(responses) < target_count):
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
    # responses_clean = []
    # for x in responses:
    #     # x = cleanResponse(x)
    #     if (x["content_text"] != "\n"):
    #         responses_clean.append(x)
    #     index += 1
    #     print_progress(index, response_length, prefix = "Cleaning up jsons: ", bar_length=80)
    #
    # responses_clean = updateMetadata(responses_clean)
    responses = updateMetadata(responses)
    #
    # output_filename = "posts_raw_" + str(len(responses_clean) - 1) + "_" + datetime.datetime.strftime(getGmt(), "%Y%m%d%H%M%S") + ".json"
    output_filename = "categories.json"
    # dumpJsonAry(responses_clean, output_filename)
    dumpJsonAry(responses, output_filename)
    print("Output file ", output_filename, " created")

if __name__ == "__main__":
    main()
