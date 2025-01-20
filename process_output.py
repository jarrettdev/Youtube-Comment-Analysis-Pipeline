import json


def process_file(filename: str):
    filepath = f'output/{filename}'
    with open(filepath, 'r') as f:
        json_str = f.read()
    json_str = '[' + json_str[:-2] + ']'
    json_obj = json.loads(json_str)
    return json_obj
