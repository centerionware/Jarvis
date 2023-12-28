#!/usr/bin/env python3
from discord.ext import tasks
import discord
import os
import json
import sys
import thinking_aid

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
        has_image = thinking_aid.get_url_from_message(message)
        old_messages = [messageo async for messageo in message.channel.history(limit=10, oldest_first=False)]
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




thinking = thinking_aid.ThinkingAid(client)
client.run(os.environ["DISCORD_TOKEN"])