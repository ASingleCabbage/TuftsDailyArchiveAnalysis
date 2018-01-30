import json
import sys
print('Validating file ' + sys.argv[1])
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    json.load(f)
print('Json Validated')
