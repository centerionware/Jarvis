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
import logging
import Jarvis_MC
import base64

# parser = argparse.ArgumentParser("python jarvis.py -i \"Hello World\" -v \"Jarvis\"")
# parser.add_argument("-u", help="Url", type=str, default="http://localhost:11434/api/generate")
# parser.add_argument("-igu", help="ComfyUI Url", type=str, default="localhost:8188")
# args = parser.parse_args()
comfyui_url = "localhost:8188"
ollama_url = "http://localhost:11434/api/generate"
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
    print('Signal handler called, exiting.')
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


async def send_image_result(interaction, image_list):
    sum_len = 0
    
    print ("Sending image result: ")
    if(type(interaction) is discord.Interaction):
        #await interaction.followup.send("Here's an image result")
        await interaction.followup.send(files=image_list)
    elif(type(interaction) is discord.Message):
        await interaction.channel.send(files=image_list)

@tasks.loop(seconds=1.0)
async def hear():
    global thinking
    global drawing
    drawing.hear()
    thinking.hear()
    spinner()
    if( len(drawing.queue) > 0):
        for elem in drawing.queue:
            nodes = elem[0]        
            for image in nodes:
                images = []
                im_num = 0
                for image_data in nodes[image]:
                    images.append(discord.File(io.BytesIO(base64.b64decode(image_data.encode('utf-8'))), elem[1].user.global_name+"_0xJarvis_image_batch_"+str(im_num)+".png"))
                    im_num = im_num + 1
                    # print("Sending an image result.")
                    # await send_image_result(elem[1], image_data)
                await send_image_result(elem[1], images)
                    #From here we need to upload the image to discord.. assume it'll be a png. might need to fix the template.json to have a save node.

            # for node_id in images:
            #     for image_data in images[node_id]:
            #         from PIL import Image
            #         import io
            #         image = Image.open(io.BytesIO(image_data))
        drawing.queue = []
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
                logging.warning("Error parsing result "  + str(e))
                #try:
                    #await send_result(elem[1],str(e))
                #except Exception as e2:
                #    print("Error parsing result " + str(e2) + "\n" + str(e))
        thinking.queue = []

@client.event
async def on_ready():
    global MC
    global client_user
    global client
    await tree.sync()
    hear.start()
    client_user = client.user
    print(f'We have logged in as {client.user}')
    
    client.loop.create_task( MC.start_async() )

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('$'):
        has_image = thinking_aid.get_url_from_message(message)
        old_messages = [messageo async for messageo in message.channel.history(limit=10, oldest_first=False)]
        thinking.launch(message.content, has_image, message, old_messages)
        #await message.channel.send('Thinking...')


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
        logging.warning("Unknown interaction type")
            
        

@tree.command(name = "ask", description = "Ask Jarvis a question")
async def ask(interaction,*, question:str, model:str = "auto" ):
    global thinking
    arguments = question
    print("Message received: " + arguments)
    old_messages = [message async for message in interaction.channel.history(limit=10, oldest_first=False)]
    try:
        await thinking.launch(arguments, False, interaction, old_messages, model)
        await interaction.response.defer(thinking=True)
    except Exception as e:
        await interaction.response.defer(thinking=True)
        await interaction.followup.send("Something broke!: " + str(e) )

@tree.command(name = "image", description = "Prompt Jarvis to create an image")
async def image(interaction,*, description:str, negative_prompt:str = "", noise_seed:int = 10301411218912, cfg:float = 1.0, image_count:int = 1,
                overlay_text:str="", overlay_color:str="#000000", overlay_x:int=19, overlay_y:int=0, overlay_alignment:str="left", use_textlora:bool=False, use_batch:bool=True):
    global thinking
    if(image_count > 5):
        image_count = 5
    if(overlay_text != ""):
        if(overlay_color[0] != "#"):
            overlay_color = "#" + overlay_color
            use_batch=False
        #Check if overlay_color is not in the format #XXXXXX where x's are probably hex.
        if(len(overlay_color) != 7):
            overlay_color = "#000000"
        #Use a regex
        for i in range(1,7):
            if(overlay_color[i] not in "0123456789abcdefABCDEF"):
                overlay_color = "#000000"
                break
    arguments = description        
    #print("Message received: " + arguments)
    old_messages = [message async for message in interaction.channel.history(limit=10, oldest_first=False)]
    try: 
        for i in range(image_count):
            await drawing.launch(arguments, interaction, old_messages, negative_prompt, noise_seed+i, cfg, overlay_text, overlay_color, overlay_x, overlay_y, overlay_alignment, use_textlora,use_batch, use_nt=False)
        await interaction.response.defer(thinking=True)
        if(overlay_text != "" and batch_size != 1):
            await interaction.followup.send("Warning: overlay_text is not supported with batch_size != 1")
    except Exception as e:
        await interaction.response.defer(thinking=True)
        await interaction.followup.send("Something broke!: " + str(e) )
    #await interaction.followup.send("Thinking...")

@tree.command(name = "nt_image", description = "Prompt Jarvis to create an image")
async def nt_image(interaction,*, description:str, negative_prompt:str = "", noise_seed:int = 10301411218912, cfg:float = 1.0, image_count:int = 1,
                overlay_text:str="", overlay_color:str="#000000", overlay_x:int=19, overlay_y:int=0, overlay_alignment:str="left", use_textlora:bool=False, use_batch:bool=True):
    global thinking
    if(image_count > 5):
        image_count = 5
    if(overlay_text != ""):
        if(overlay_color[0] != "#"):
            overlay_color = "#" + overlay_color
            use_batch=False
        #Check if overlay_color is not in the format #XXXXXX where x's are probably hex.
        if(len(overlay_color) != 7):
            overlay_color = "#000000"
        #Use a regex
        for i in range(1,7):
            if(overlay_color[i] not in "0123456789abcdefABCDEF"):
                overlay_color = "#000000"
                break
    arguments = description        
    #print("Message received: " + arguments)
    old_messages = [message async for message in interaction.channel.history(limit=10, oldest_first=False)]
    try:
        for i in range(image_count):
            await drawing.launch(arguments, interaction, old_messages, negative_prompt, noise_seed+i, cfg, overlay_text, overlay_color, overlay_x, overlay_y, overlay_alignment, use_textlora,use_batch, use_nt=True)
        await interaction.response.defer(thinking=True)
        if(overlay_text != "" and batch_size != 1):
            await interaction.followup.send("Warning: overlay_text is not supported with batch_size != 1")
    except Exception as e:
        await interaction.response.defer(thinking=True)
        await interaction.followup.send("Something broke!: " + str(e) )
    #await interaction.followup.send("Thinking...")

thinking = thinking_aid.ThinkingAid(client, ollama_url)
drawing = drawing_aid.DrawingAid(client, comfyui_url)

MC = Jarvis_MC.JarvisMC(drawing, thinking)
thinking.set_MC(MC)
drawing.set_MC(MC)

#def real_main(client, MC):
print( "Starting tasks.")
#client.loop.create_task( MC.start_async() )
client.run(os.environ["DISCORD_TOKEN"])
    #task1 = asyncio.create_task( client.start(os.environ["DISCORD_TOKEN"]) )
    #task2 = asyncio.create_task( MC.start_async())
    #await task1
    #await task2
#    The following will only work in python3.11. the above works in 3.9+
#    async with asyncio.TaskGroup() as tg:
#        task1 = tg.create_task( client.start(os.environ["DISCORD_TOKEN"]) )
#        task2 = tg.create_task( MC.start_async())


#import asyncio
#asyncio.run(real_main(client, MC))
#real_main(client, MC)
#client.run(os.environ["DISCORD_TOKEN"])