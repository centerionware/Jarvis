# This example requires the 'message_content' intent.

import discord
import os
import textwrap
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')



@tree.command(name = "echo", description = "echo back all text")
async def echo(interaction,*, arg:str):
    arguments = arg
    print("Message received: " + arguments)
    messages = []
    wrapped = textwrap.wrap(arguments)
    t_msg = ""
    for m in wrapped:
        if(len(t_msg) + len(m) > 2000):
            messages.append(t_msg)
            t_msg = ""
        t_msg = t_msg + m
    while(len(t_msg) > 2000):
        messages.append(t_msg[0:2000])
        t_msg = t_msg[2000:]
    await interaction.response.send_message(messages[0])
    for message in messages[1:]:
        await interaction.followup.send(message)

client.run(os.environ["DISCORD_TOKEN"])