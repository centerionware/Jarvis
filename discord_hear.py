#!/usr/bin/env python3
from discord.ext import tasks
import discord
import os
import json
import sys
import thinking_aid
import drawing_aid
#import argparse
import io

# parser = argparse.ArgumentParser("python jarvis.py -i \"Hello World\" -v \"Jarvis\"")
# parser.add_argument("-u", help="Url", type=str, default="http://localhost:11434/api/generate")
# parser.add_argument("-igu", help="ComfyUI Url", type=str, default="localhost:8188")
# args = parser.parse_args()
comfyui_url = "localhost:8188"
ollama_url = "localhost:11434/api/generate"
try:
    comfyui_url = os.environ["COMFYUI_URL"]
except:
    pass
print("ComfyUI URL: " + comfyui_url)

try:
    ollama_url = os.environ["OLLAMA_URL"]
except:
    pass
print("Ollam URL: " + ollama_url)



def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    global thinking
    thinking.kill_pids()
    sys.exit(0)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

booting = 1
client_user = None

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
    global drawing
    drawing.hear()
    thinking.hear()
    spinner()
    if( len(drawing.queue) > 0):
        for elem in drawing.queue:
            for image_node in elem[0]:
                for image_data in elem[image_node]:
                    send_image_result(elem[1], image_data)
                    #From here we need to upload the image to discord.. assume it'll be a png. might need to fix the template.json to have a save node.

            # for node_id in images:
            #     for image_data in images[node_id]:
            #         from PIL import Image
            #         import io
            #         image = Image.open(io.BytesIO(image_data))
            #         image.show()
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
        has_image = thinking_aid.get_url_from_message(message)
        old_messages = [messageo async for messageo in message.channel.history(limit=10, oldest_first=False)]
        thinking.launch(message.content, has_image, message, old_messages)
        #await message.channel.send('Thinking...')

@tree.command(name = "echo", description = "echo back all text")
async def echo(interaction,*, arg:str, ):
    arguments = arg
    print("Message received: " + arguments)
    send_result(interaction, arguments)

async def send_image_result(interaction, image_data):
    print ("Sending image result: " + str(len(image_data)))
    messages = []
    if(type(interaction) is discord.Interaction):
        await interaction.followup.send(discord.File(io.BytesIO(image_data), filename="image.png"))
    elif(type(interaction) is discord.Message):
        await interaction.channel.send(discord.File(io.BytesIO(image_data), filename="image.png"))

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
            if(len(message.strip()) > 0):
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

@tree.command(name = "image", description = "Prompt Jarvis to create an image")
async def image(interaction,*, arg:str, ):
    global thinking
    arguments = arg
    print("Message received: " + arguments)
    #print(interaction.data)
    #has_image = get_url_from_message(interaction.message)
    old_messages = [message async for message in interaction.channel.history(limit=10, oldest_first=False)]
    drawing.launch(arguments, interaction, old_messages)
    await interaction.response.defer(thinking=True)
    #result = "Thinking..."
    #send_result(result)



thinking = thinking_aid.ThinkingAid(client, ollama_url)
drawing = drawing_aid.DrawingAid(client, comfyui_url)

client.run(os.environ["DISCORD_TOKEN"])