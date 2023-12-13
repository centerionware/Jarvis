import argparse
import requests
import json
parser = argparse.ArgumentParser("python think.py -i \"Hello World\" -v \"Jarvis\"")
parser.add_argument("-v", help="Voice to use", type=str, default="Jarvis")
parser.add_argument("-i", help="Input", type=str)
parser.add_argument("-u", help="URL", type=str, default="http://127.0.0.1:5000/v1/chat/completions")
args = parser.parse_args()

def send_to_oobabooga(args):
    data = {
        "mode": "chat",
        "character": args.v,
        "messages": [{"role":"user", "content":args.i}]
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(args.u, headers=headers, json=data, verify=False)
    try:
        reply = response.json()['choices'][0]['message']['content']
    except Exception as E:
        response = "Something went terribly wrong.\n "+str(E)
    return reply

try:
    response = send_to_oobabooga(args)
except Exception as E:
    response = "Something went terribly wrong.\n "+str(E)
print(json.dumps({"response":response,"prompt":args.i }), flush=True)