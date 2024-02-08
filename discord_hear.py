#!/usr/bin/env python3
from discord.ext import tasks
import discord
import os
import json
import sys
import thinking_aid
import drawing_aid
import searching_aid
#import argparse
import io
import logging
import Jarvis_MC
import base64
import webui
import aiohttp
# parser = argparse.ArgumentParser("python jarvis.py -i \"Hello World\" -v \"Jarvis\"")
# parser.add_argument("-u", help="Url", type=str, default="http://localhost:11434/api/generate")
# parser.add_argument("-igu", help="ComfyUI Url", type=str, default="localhost:8188")
# args = parser.parse_args()
comfyui_url = "localhost:8188"
ollama_url = "http://localhost:11434/api/generate"
search_url = "http://searxng:8080/search"
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

try:
    search_url = os.environ["SEARCH_URL"]
except:
    pass
print("Search URL: " + search_url)




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
    
    if(type(interaction) is discord.Interaction):
        #await interaction.followup.send("Here's an image result")
        await interaction.followup.send(files=image_list)
    elif(type(interaction) is discord.Message):
        await interaction.channel.send(files=image_list)

g_search_prompt = None
# with (open(os.path.join(os.path.dirname(__file__), "base_prompt.txt"), "r")) as f:
with open(os.path.join(os.path.dirname(__file__), "search_prompt.txt"), "r") as f:
    g_search_prompt = f.read()
html_search_prompt = None
with open(os.path.join(os.path.dirname(__file__), "search_html_prompt.txt"), "r") as f:
    html_search_prompt = f.read()

@tasks.loop(seconds=1.0)
async def hear():
    global thinking
    global drawing
    global searching
    global g_search_prompt
    drawing.hear()
    thinking.hear()
    spinner()
    if( len(searching.queue) > 0):
        for elem in searching.queue:
            print ("Sending a search result.")
            # await send_result(elem[1], elem[0]) 
            d_prompt = g_search_prompt #  "summerize the information without adding your own thoughts. Don't mention the names of search engines unless it's relevant to the query. Use high quality results from the data provided. focus on the initial query. Provide links to relevant information with a brief description about the link from the data provided - do not make up any information that's not provided. Focus on the query. Do not provide links not closely associated to the data or not from the data. Always include link "
            output = {"result": elem[0], "status": "quick-results"}
            if(type(elem[1]) is aiohttp.web.WebSocketResponse):
                d_prompt = html_search_prompt
                await elem[1].send_str(json.dumps(output))
            model = "auto"
            if(len(elem) == 4):
                model = elem[3]
                # with open("test.txt", "a") as f:
                #     f.write("Model: " + model + "\n")
            await thinking.launch(elem[0] + d_prompt, False, elem[1], [], model, d_prompt)
            
            # await thinking.launch(elem[0] + "\nsummerize the information. Use high quality results from the data provided. focus on the initial query. Include links to relevant sources based on the query and the data provided.", False, elem[1], [], "auto")
            # This should be json search results, 
            # for now dump to discord to examine 
            # but this should be an entrypoint to a search result handler, 
            # which could run async 'requests' to get the page contents, 
            # then have the llm's analyze the pages for relevance and all that, 
            # summerize the pages, etc, 
            # then finally dump the results with the original link to discord.
        searching.queue = []
    if( len(drawing.queue) > 0):
        for elem in drawing.queue:
            nodes = elem[0]        
            for image in nodes:
                images = []
                im_num = 0
                for image_data in nodes[image]:
                    username = "default"
                    try:
                        username = elem[1].user.global_name
                    except Exception as E:
                        pass
                    images.append(discord.File(io.BytesIO(base64.b64decode(image_data.encode('utf-8'))), username+"_0xJarvis_image_batch_"+str(im_num)+".png"))
                    im_num = im_num + 1
                await send_image_result(elem[1], images)
        drawing.queue = []
    if( len(thinking.queue) > 0):
        for elem in thinking.queue:
            result = elem[0]
            if(result == ""):
                continue
            try:
                result = json.loads(result)
                response = ""
                if("message" not in result):
                    response = result["response"]
                else:
                    response = result["message"]["content"]
                model = result["model"]
                formatted_response = "Model: " + model + "\n" + response
                await send_result(elem[1],formatted_response, elem[2])
            except Exception as e:
                logging.warning("Error parsing result "  + str(e))
        thinking.queue = []

@client.event
async def on_ready():
    global MC
    global client_user
    global client
    global webui
    await tree.sync()
    hear.start()
    client_user = client.user
    print(f'We have logged in as {client.user}')
    
    client.loop.create_task( MC.start_async() )
    await webui.start_server()

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    global thinking
    if message.content.startswith('$'):
        has_image = thinking_aid.get_url_from_message(message)
        old_messages = [messageo async for messageo in message.channel.history(limit=10, oldest_first=False)]
        await thinking.launch(message.content, has_image, message, old_messages)
        # question = message.content
        # interaction = message
        # arguments = question
        
        # try:
        #     await thinking.launch(arguments, has_image, interaction, old_messages, model)
        #     await interaction.response.defer(thinking=True)
        # except Exception as e:
        #     await interaction.response.defer(thinking=True)
        #     await interaction.followup.send("Something broke!: " + str(e) )

async def send_result(interaction, arguments: str, prompt:str = None):
    print ("Sending result: " + arguments)
    messages = []
    wrapped = [arguments] #textwrap.wrap(arguments)
    t_msg = ""
    if(type(interaction) is not discord.Interaction and type(interaction) is not discord.Message):
        print(type(interaction))
        if(type(interaction) is aiohttp.web.WebSocketResponse):
            ## First load the prompt
            prompt["messages"][0]["content"] = prompt["messages"][0]["content"].replace(g_search_prompt, "").replace(html_search_prompt, "")
            if "}{\"query\":" in prompt["messages"][0]["content"]:
                head, sep, tail = prompt["messages"][0]["content"].partition("}{\"query\":")
                prompt["messages"][0]["content"] = head + "}"
            output = {"result": arguments, "prompt": json.dumps(prompt), "status":"completed"}
            await interaction.send_str(json.dumps(output))
        else:
            print("Unknown interaction type")
            #await interaction.send_str(arguments)
        return
    if( len(arguments) > 4000 ):
        file = [discord.File(io.BytesIO(arguments.encode('utf-8')), interaction.user.global_name+'long_result_utf8.txt')]
        return await send_image_result(interaction, file)

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
    global drawing
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
    
    old_messages = [message async for message in interaction.channel.history(limit=10, oldest_first=False)]
    try: 
        for i in range(image_count):
            await drawing.launch(arguments, interaction, old_messages, negative_prompt, noise_seed+i, cfg, overlay_text, overlay_color, overlay_x, overlay_y, overlay_alignment, use_textlora,use_batch, use_nt=False)
        await interaction.response.defer(thinking=True)
        if(overlay_text != "" and use_batch != False):
            await interaction.followup.send("Warning: overlay_text is not supported with use_batch = false")
    except Exception as e:
        await interaction.response.defer(thinking=True)
        await interaction.followup.send("Something broke!: " + str(e) )
    #await interaction.followup.send("Thinking...")

@tree.command(name = "nt_image", description = "Prompt Jarvis to create an image")
async def nt_image(interaction,*, description:str, negative_prompt:str = "", noise_seed:int = 10301411218912, cfg:float = 7.0, image_count:int = 1,
                overlay_text:str="", overlay_color:str="#000000", overlay_x:int=19, overlay_y:int=0, overlay_alignment:str="left", use_textlora:bool=False, use_batch:bool=True):
    global drawing
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
    
    old_messages = [message async for message in interaction.channel.history(limit=10, oldest_first=False)]
    try:
        for i in range(image_count):
            await drawing.launch(arguments, interaction, old_messages, negative_prompt, noise_seed+i, cfg, overlay_text, overlay_color, overlay_x, overlay_y, overlay_alignment, use_textlora,use_batch, use_nt=True)
        await interaction.response.defer(thinking=True)
        if(overlay_text != "" and use_batch != 1):
            await interaction.followup.send("Warning: overlay_text is not supported with use_batch=false")
    except Exception as e:
        await interaction.response.defer(thinking=True)
        await interaction.followup.send("Something broke!: " + str(e) )
    #await interaction.followup.send("Thinking...")


@tree.command(name = "search", description = "Have Jarvis search the internet for you.")
async def search(interaction,*, question:str, model:str = "auto" ):
    global searching
    arguments = question
    print("Message received: " + arguments)
    old_messages = [message async for message in interaction.channel.history(limit=10, oldest_first=False)]
    try:
        await searching.launch(question, False, interaction, question, model)
        # async def launch(self, command, url, interaction, search_query, model):
        await interaction.response.defer(thinking=True)
    except Exception as e:
        await interaction.response.defer(thinking=True)
        await interaction.followup.send("Something broke!: " + str(e) )

# Sick cyclical dependencies batman.
thinking = thinking_aid.ThinkingAid(client, ollama_url)
drawing = drawing_aid.DrawingAid(client, comfyui_url)
searching = searching_aid.SearchingAid(client, search_url)

MC = Jarvis_MC.JarvisMC(drawing, thinking, searching)
webui = webui.WebUI(drawing, thinking, searching)
thinking.set_MC(MC)
drawing.set_MC(MC)
searching.set_MC(MC)

client.run(os.environ["DISCORD_TOKEN"])
