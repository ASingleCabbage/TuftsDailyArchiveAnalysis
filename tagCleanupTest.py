import json

def cleanJson(json):
    del json["_links"]
    print(json);
    
    # htmlParser = HTMLParser()
    # setattr(json, "title_text", htmlParser.unescape(json.title.rendered))

file = open("tags_test.json", "r");
jsons = json.load(file);
file.close();

# for x in jsons:
cleanJson(jsons[0]);

