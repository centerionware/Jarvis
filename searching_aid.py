import subprocess
import queue as libqueue
import threading
import time
import requests
import base64
import json
import os

def enqueue_output(queue, interaction, args, remote_url):
    if(args["model"] == "llava"):
        new_args = {
            "model": args["model"],
            "stream": args["stream"],
            #Make a string out of all the messages roles and contents to fill the prompt
            "prompt": "",
            # fill in the images from the messages that have them
            "images": []
        }
        for message in args["messages"]:
            if(message["role"] != "assistant"):
                content = message["content"]
                if(content[0] == "$"): content = content[1:]
                new_args["prompt"] +=  content + "\n"
            if("images" in message):
                for image in message["images"]:
                    new_args["images"].append(image)
        output = requests.post(remote_url, json=new_args).content.decode('utf-8')
        print("Received output from llava: " + str(output))
        queue.put([output,interaction])
        return
    output = requests.post(remote_url.replace("generate", "chat"), json=args).content.decode('utf-8')
    queue.put([output,interaction])


def get_url_from_message(message):
    if len(message.attachments) > 0:
        attachment = message.attachments[0]
    else:
        return False
    if attachment.filename.endswith(".jpg") or attachment.filename.endswith(".jpeg") or attachment.filename.endswith(".png") or attachment.filename.endswith(".webp") or attachment.filename.endswith(".gif"):
        return attachment.url
    elif "https://images-ext-1.discordapp.net" in message.content or "https://tenor.com/view/" in message.content:
        return message.content

class SearchingAid:
    def __init__(self, client, url):
        self.queue = []
        self.actual_queue = libqueue.Queue()
        self.command = None
        self.client=client
        self.url = url
        self.MC = None
    def set_MC(self, MC):
        self.MC = MC
    def __del__(self):
        print("Cleaning SearchingAid")
        self.kill_pids()
    def dl_and_enc_image(self, url):
        pass
    def look_for_forget_in_messages(self, old_messages):
        pass
    async def launch(self, command, url, interaction, search_query, model):
        client_user = self.client
        
        self.command = command
        args = {}
        
        formatted_messages = []
        any_urls = False
        args = {
            "q":search_query
            "format":json
        }
        # find if .topic is in the interaction.channel
        # Create a base system prompt that's multilines
        base_system_prompt = """
"""
        try:
            if(interaction.channel.topic is not None and any_urls is False):
                nbase_system_prompt = base_system_prompt.replace("%topic%", interaction.channel.topic)
                formatted_messages.insert(0,{"role":"system", "content": nbase_system_prompt})
                
        except:
            pass
        if(any_urls is True):
            #print("A url is true!")
            #print(json.dumps(args))
            args["model"] = "llava"
        else:
            args["model"] = "mistral"            
        #loop each message in formatted_messages but in reverse
        for message in formatted_messages[::-1]:
            #Push message to the front of the list
            args["messages"].insert(0,message)
        # url http://localhost:11434/api/generate -d
        if(any_urls is True):
            print("A url is true!")
            print(json.dumps(args))
        
        time.sleep(0.01)
        # self.pids[-1].stdin.write("\n")
        await self.MC.text_request(interaction, args)
        #stdout_thread = threading.Thread(target=enqueue_output, args=(self.actual_queue, interaction, args, self.url))
        #stdout_thread.daemon = True
        #stdout_thread.start()

    def kill_pids(self):
        pass

    def hear(self):
        try:
            if(not self.actual_queue.empty()):
                while (not self.actual_queue.empty()):
                    self.queue.append(self.actual_queue.get(block=False))
        except Exception as e:
            pass