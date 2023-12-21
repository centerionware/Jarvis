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

def enqueue_output(out, queue, interaction,pid):
    #while(1):
    time.sleep(1)
    print("Polling")
    output, err = pid.communicate()
    queue.put([output,interaction])
    pid.terminate()


class ThinkingAid:
    def __init__(self):
        self.pids = []
        self.queue = []
        self.actual_queue = queue.Queue()
        self.command = None
    def __del__(self):
        print("Cleaning ThinkingAid")
        self.kill_pids()
    def dl_and_enc_image(self, url):
        pass
    def launch(self, command, url, interaction):
        self.command = command
        args = {}
        if(url is not False):
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

        # url http://localhost:11434/api/generate -d
        self.pids.append( subprocess.Popen(['curl', 'http://localhost:11434/api/chat', "-d", json.dumps(args)], stderr=subprocess.PIPE, stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True))
        time.sleep(0.01)
        self.pids[-1].stdin.write("\n")
        stdout_thread = threading.Thread(target=enqueue_output, args=(self.pids[-1].stdout, self.actual_queue, interaction, self.pids[-1]))
        stdout_thread.daemon = True
        stdout_thread.start()

    def kill_pids(self):
        for pid in self.pids:
            try:
                if(pid.poll() is None):
                    os.kill(pid.pid, signal.SIGTERM)
            except:
                pass
        self.pids = []

    def hear(self):
        try:
            if(not self.actual_queue.empty()):
                while (not self.actual_queue.empty()):
                    self.queue.append(self.actual_queue.get(block=False))
        except Exception as e:
            pass
        for pid in self.pids:
            if(not (pid.poll() is None)):
                self.pids.remove(pid)

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
            print("Result: " + str(result) + " " +str( type(result)))
            try:
                result = json.loads(result)
                print("Loaded json")
                response = result["message"]["content"]
                print("Extracted response" + response)
                model = result["model"]
                print("Extracted model" + model)
                formatted_response = "Model: " + model + "\n" + response
                print("Sending result: " + formatted_response)
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
    await tree.sync()
    hear.start()
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('$'):
        has_image = get_url_from_message(message)
        thinking.launch(message.content, has_image, message)
        await message.channel.send('Hello!')

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
    thinking.launch(arguments, False, interaction)
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