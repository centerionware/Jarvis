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

class ThinkingAid:
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
        print("Cleaning ThinkingAid")
        self.kill_pids()
    def dl_and_enc_image(self, url):
        #download the url using requests into memory
        #encode the image into base64
        #return the base64 encoded image
        image = requests.get(url).content
        return base64.b64encode(image).decode('utf-8')
    def look_for_forget_in_messages(self, old_messages):
        new_messages = []
        for message in old_messages:#[::-1]:
            if(message.author != self.client.user):
                if(message.content == "forget"):
                    return new_messages
            if(message.content.strip() != ""):
                new_messages.append(message)
        return new_messages
    async def launch(self, command, url, interaction, old_messages, model):
        client_user = self.client
        old_messages = self.look_for_forget_in_messages(old_messages)
        self.command = command
        args = {}
        
        formatted_messages = []
        any_urls = False
        for message in old_messages:
            if(message.author == client_user):
                content = message.content
                #remove the first line of content
                content = content[content.find("\n")+1:]
                has_url = get_url_from_message(message)
                if has_url is not False:
                    any_urls = True
                    content += "\nThis contains a picture/image/photograph of some sort\n"
                    formatted_messages.append({"role": "assistant", "content": content, "images":[self.dl_and_enc_image(has_url)]})
                else:
                    formatted_messages.append({"role": "assistant", "content": content})
                print("adding assistant message: " + content)
            else:
                print("adding user message: " + message.content)
                has_url = get_url_from_message(message)
                if has_url is not False:
                    any_urls = True
                    content = message.content
                    content += "\nThis contains a picture/image/photograph of some sort\n"
                    formatted_messages.append({"role": "user", "content": content, "images":[self.dl_and_enc_image(has_url)]})
                else:
                    formatted_messages.append({"role": "user", "content": message.content})
            
        if(url != False and (model == "auto" or model == "llava")):
            any_urls = True
            args = {
                "model": "llava",
                "stream": False,
                "messages": [
                    {
                    "role": "user",
                    "content": command,
                    "images":[self.dl_and_enc_image(url)]
                    }
                ]
            }
        else:
            s_model = "mistral"
            if( s_model != "auto"):
                s_model = model
            args ={
                "model": s_model,
                "stream": False,
                "messages": [
                    {
                    "role": "user",
                    "content": command,
                    }
                ]
            }
        # find if .topic is in the interaction.channel
        # Create a base system prompt that's multilines
        base_system_prompt = """
You are chatbot that generates text based on the messages you send it.
You will do your best not to answer illegal or immoral questions.
You will do your best to answer questions that are asked of you, and strive to be perfect.

The following is a topic for the current room:
%topic%

Strive to be courteous and polite, and to be a good friend to all.
Explain in a level of detail that is appropriate for the situation.
Ignore criticism, and do not take it personally.
Do not use foul language, and do not be rude or aggressive.
Do not spam, and do not post inappropriate content.
Do not post links to inappropriate content, illegal content, pirated content, malware, phishing sites.
Do not post links to sites that are not safe for work, school, home, life, or the universe.
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