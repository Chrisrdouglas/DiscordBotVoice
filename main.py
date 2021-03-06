import discord
import requests
from discord.ext import commands
from threading import Thread, Lock
from datetime import datetime
from time import sleep
from flask import Flask, request

import values


client = commands.Bot(command_prefix=values.command_prefix)
lock = Lock() # Locked by the say command. released by the callback from resemble that gets sent to the flask app

@client.command()
async def join(ctx):
    voiceChannel = discord.utils.get(ctx.guild.voice_channels, name=values.Channel_Name)
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice is None or not voice.is_connected():
        await voiceChannel.connect()
        #voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        #voice.play(discord.FFmpegPCMAudio("doom.wav")) # add a wave file that you want it to say upon entry

@client.command()
async def say(ctx, val : str):
    if lock.locked(): # only one thing can be said at a time
        return
    lock.acquire() # lock until the callback has been sent

    voiceChannel = discord.utils.get(ctx.guild.voice_channels, name=values.Channel_Name)
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice is None or not voice.is_connected():
        await voiceChannel.connect()
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

    # create the line that you want read in the voice. to do this get the whole message and delete the command prefix
    create_Voice_Clip(ctx.message.content.replace(values.command_prefix + "say ", ''))

    with lock: # this lock will wait for the callback from resemble
        voice.play(discord.FFmpegPCMAudio("w.wav"))

@client.command()
async def away(ctx):
    voiceChannel = discord.utils.get(ctx.guild.voice_channels, name='Viego\'s Cracked')
    #voiceChannel = discord.utils.get(ctx.guild.voice_channels, name='General')
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_connected():
        voice.play(discord.FFmpegPCMAudio("SlipAway.wav"))
        sleep(2.1)
        await voice.disconnect()


def create_Voice_Clip(val):
    url = "https://app.resemble.ai/api/v1/projects/"+ values.projectID +"/clips"
    headers = {
        'Authorization': 'Token token="'+values.resemble_token+'"',
        'Content-Type': 'application/json'}
    data = {
        'data': {
            'title': str(datetime.now().timestamp()),
            'body': val,
            'voice': values.voiceID
        },
        "callback_uri": "http://"+values.IP+"/service"
    }
    response = requests.post(url, headers=headers, json=data)
    print(response)


# Flask App for callback from resemble.ai

app = Flask(__name__)

@app.route("/service", methods=['POST'])
def hello():
    try:
        data = request.get_json()
        download(data['url'])
    finally:
        lock.release()


def download(url):
    r = requests.get(url, allow_redirects=True)
    open("w.wav", "wb").write(r.content)


c = Thread(target=client.run, args=(values.token,))
c.start() # start discord bot
f = Thread(target=app.run, kwargs={'host': '0.0.0.0', 'debug': False})
f.start() # start flask app
