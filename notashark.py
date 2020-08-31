## Dead-simple discord bot that shows statistics regarding current kag server's activity. 100% not a shark bot clone, definely didnt take few hours to write

import discord
import pykagapi
from os import environ
from asyncio import sleep
from sys import exit

import requests
import json

## Vars
BOT_NAME = "kaginfobot"
BOT_TOKEN = environ['DISCORD_KEY']
try:
    STATISTICS_CHANNEL_ID = int(environ['STATISTICS_CHANNEL_ID'])
except KeyError:
    pass
try:
    LOG_CHANNEL_ID = int(environ['LOG_CHANNEL_ID'])
except KeyError:
    pass

## Functions
def server_country(ip):
    '''Receives str(ip), returns str(country of that ip) in lowercase format, based on geojs.io data'''
    link = "https://get.geojs.io/v1/ip/country/"+ip+".json"
    response = requests.get(link, timeout = 30)
    pydic = json.loads(response.text)
    country = pydic['country']
    return country.lower()

def sort_by_players(x):
    '''Sort received list by len of ['playerList'] in its dictionaries'''
    players = len(x['playerList'])
    return int(players)

## Code
api = pykagapi.KAG_API()
client = discord.Client()

@client.event
async def on_ready():
    print('Running {} as {}!'.format(BOT_NAME, client.user))
    try:
        channel = client.get_channel(STATISTICS_CHANNEL_ID)
        print('Successfully joined the {}, starting to gather statistics'.format(channel))
        message = await channel.send("Gathering the data...")
        while True:
            kag_servers = api.get_active_servers()
            servers_amount = len(kag_servers)
            players_amount = 0
            for x in kag_servers:
                players_amount += len(x['playerList'])

            kag_servers.sort(key = sort_by_players, reverse = True)

            response_message = "Featuring:"
            leftowers_counter = 0
            for server in kag_servers:
                tempmsg = ""
                tempmsg += "\n**:flag_{}: {}**\n".format(server_country(server['IPv4Address']), server['name'])
                tempmsg += "**Address:** <kag://{}:{}>\n".format(server['IPv4Address'], server['port'])
                tempmsg += "**Gamemode:** {}\n".format(server['gameMode'])
                tempmsg += "**Players:** {}/{}\n".format(len(server['playerList']), server['maxPlayers'])
                tempmsg += "**Currently Playing:** {}\n".format((', '.join(server['playerList'])))
                if (len(response_message)+len(tempmsg)) <= 1024:
                    response_message += tempmsg
                else:
                    leftowers_counter += 1

            if leftowers_counter > 0:
                response_message += "\n*And {} less populated servers*".format(leftowers_counter)

            embed = discord.Embed()
            embed.title = "There are currently {} active servers with {} players".format(servers_amount, players_amount)
            embed.colour = 0x3498DB
            embed.description = response_message

            await message.edit(content=None, embed=embed)
            await sleep(30)
    except AttributeError:
        print("Cant find channel with such ID. Server statistics functionality is disabled.\nAre you sure you've set this up correctly?")
    except NameError:
        print("STATISTICS_CHANNEL_ID isnt set. Server statistics functionality disabled.\nAre you sure you've set this up correctly?")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.lower() == "ping":
        await message.channel.send("pong")

@client.event
async def on_member_join(member):
    channel = client.get_channel(LOG_CHANNEL_ID)
    await channel.send("Hello, {}! Welcome to this little discord server. Be nice and eat cookies! Also read #rules!".format(member.mention))

@client.event
async def on_member_leave(member):
    channel = client.get_channel(LOG_CHANNEL_ID)
    await channel.send("{} has left the server. Thats unfortunate :(".format(member.mention))

## Usage
if __name__ == "__main__":
    try:
        client.run(BOT_TOKEN)
    except:
        print("Some fatal error has occured!")
        exit(1)

## Ok, it works.
## TODO: add some indicators for spectators
## TODO: maybe add some footer with info regarding update time
## TODO: safety checks for joinin and leaving
## TODO: move requests shenanigans into pykagapi to make this one even less bloated
## TODO: maybe separate channels for greetings and leavings, instead of just one "log_channel", idk
