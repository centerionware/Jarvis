#!/usr/bin/env python3
from discord.ext import tasks
import discord
import os
import textwrap
import json
import time
import signal
import sys
import subprocess
import requests
import base64

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    global thinking
    thinking.kill_pids()
    sys.exit(0)


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

import queue
import threading

booting = 1
client_user = None

def enqueue_output(queue, interaction, args):
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
        output = requests.post("http://localhost:11434/api/generate", json=new_args).content.decode('utf-8')
        print("Received output from llava: " + str(output))
        queue.put([output,interaction])
        return
    output = requests.post("http://localhost:11434/api/chat", json=args).content.decode('utf-8')
    queue.put([output,interaction])


class ThinkingAid:
    def __init__(self):
        self.queue = []
        self.actual_queue = queue.Queue()
        self.command = None
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
            if(message.author != client_user):
                if(message.content == "forget"):
                    return new_messages
            if(message.content.strip() != ""):
                new_messages.append(message)
        return new_messages
    def launch(self, command, url, interaction, old_messages):
        global client_user
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
            
        if(url is not False):
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
            args ={
                "model": "mistral",
                "stream": False,
                "messages": [
                    {
                    "role": "user",
                    "content": command,
                    }
                ]
            }
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
        stdout_thread = threading.Thread(target=enqueue_output, args=(self.actual_queue, interaction, args))
        stdout_thread.daemon = True
        stdout_thread.start()

    def kill_pids(self):
        pass

    def hear(self):
        try:
            if(not self.actual_queue.empty()):
                while (not self.actual_queue.empty()):
                    self.queue.append(self.actual_queue.get(block=False))
        except Exception as e:
            pass
        

thinking = ThinkingAid()

spinner_index = 0
spinner_list = ["|","/","-","\\"]
def spinner(spinamnt=1):
    global spinner_index
    global spinner_list
    print(spinner_list[spinner_index] ,end="\r"),
    spinner_index = spinner_index + spinamnt
    if(spinner_index >= len(spinner_list)):
        spinner_index = 0
    if(spinner_index < 0):
        spinner_index = len(spinner_list)-1


@tasks.loop(seconds=1.0)
async def hear():
    global thinking
    thinking.hear()
    spinner()
    if( len(thinking.queue) > 0):
        #print("Heard back from the AI Chatbot: " + thinking.queue)
        #ParseResponse(thinking.queue)
        #print()
        for elem in thinking.queue:
            result = elem[0]
            if(result == ""):
                continue
            #print("Result: " + str(result) + " " +str( type(result)))
            try:
                result = json.loads(result)
                #print("Loaded json")
                response = ""
                if("message" not in result):
                    response = result["response"]
                else:
                    response = result["message"]["content"]
                #print("Extracted response" + response)
                model = result["model"]
                #print("Extracted model" + model)
                formatted_response = "Model: " + model + "\n" + response
                #print("Sending result: " + formatted_response)
                await send_result(elem[1],formatted_response)
            except Exception as e:
                print("Error parsing result "  + str(e))
                #try:
                    #await send_result(elem[1],str(e))
                #except Exception as e2:
                #    print("Error parsing result " + str(e2) + "\n" + str(e))
        thinking.queue = []

@client.event
async def on_ready():
    global client_user
    await tree.sync()
    hear.start()
    client_user = client.user
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('$'):
        has_image = get_url_from_message(message)
        old_messages = [message async for message in message.channel.history(limit=10, oldest_first=False)]
        thinking.launch(message.content, has_image, message, old_messages)
        #await message.channel.send('Thinking...')

@tree.command(name = "echo", description = "echo back all text")
async def echo(interaction,*, arg:str, ):
    arguments = arg
    print("Message received: " + arguments)
    send_result(interaction, arguments)

async def send_result(interaction, arguments):
    print ("Sending result: " + arguments)
    messages = []
    wrapped = [arguments] #textwrap.wrap(arguments)
    t_msg = ""
    for m in wrapped:
        if(len(t_msg) + len(m) > 2000):
            messages.append(t_msg)
            t_msg = ""
        t_msg = t_msg + m
    while(len(t_msg) > 2000):
        messages.append(t_msg[0:2000])
        t_msg = t_msg[2000:]
    messages.append(t_msg)

    if(type(interaction) is discord.Interaction):
        print("Sending interaction msg with " + str(len(messages)) + " messages")
        for message in messages:
            # Trim the message, if it's not empty send it

            if(len(message.strip()) > 0):
                await interaction.followup.send(message)
    elif(type(interaction) is discord.Message):
        for message in messages:
            await interaction.channel.send(message)
    else:
        print("Unknown interaction type")
            
        

@tree.command(name = "ask", description = "Ask Jarvis a question")
async def ask(interaction,*, arg:str, ):
    global thinking
    arguments = arg
    print("Message received: " + arguments)
    #print(interaction.data)
    
    #has_image = get_url_from_message(interaction.message)
    old_messages = [message async for message in interaction.channel.history(limit=10, oldest_first=False)]
    thinking.launch(arguments, False, interaction, old_messages)
    await interaction.response.defer(thinking=True)
    #result = "Thinking..."
    #send_result(result)


def get_url_from_message(message):
    if len(message.attachments) > 0:
        attachment = message.attachments[0]
    else:
        return False
    if attachment.filename.endswith(".jpg") or attachment.filename.endswith(".jpeg") or attachment.filename.endswith(".png") or attachment.filename.endswith(".webp") or attachment.filename.endswith(".gif"):
        return attachment.url
    elif "https://images-ext-1.discordapp.net" in message.content or "https://tenor.com/view/" in message.content:
        return message.content


client.run(os.environ["DISCORD_TOKEN"])