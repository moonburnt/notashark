### Copyright © 2020, moonburnt
###
### This program is free software. It comes without any warranty, to
### the extent permitted by applicable law. You can redistribute it
### and/or modify it under the terms of the Do What The Fuck You Want
### To Public License, Version 2, as published by Sam Hocevar.
### See the LICENSE file for more details.

### Dead-simple discord bot for King Arthur's Gold

### Patch Notes:
## Fixed some typos
## Added basic footer to statistics embed, featuring info about amount of time between updates
## Added few safety checks here and there
## Now keeping server's country in memory, which should drammatically reduce the amount of requests to geojs.io
################
### TODO:
## for each server, make another embed's field (up to 25), instead of keeping everything inside description (should increase amount of info possible to show - from 2048 symbols per description to 6k per whole embed)
## add some indicators for spectators and password-protected servers

import discord
import pykagapi
from os import environ
from asyncio import sleep
from sys import exit

import requests
import json

## Vars
BOT_NAME = "notashark"
try:
    BOT_TOKEN = environ['DISCORD_KEY']
except KeyError:
    print("DISCORD_KEY environment variable isnt set. Edit bootin_up.sh accordingly, or set it up manually.\nAbort")
    exit(1)
try:
    STATISTICS_CHANNEL_ID = int(environ['STATISTICS_CHANNEL_ID'])
except KeyError:
    pass
try:
    LOG_CHANNEL_ID = int(environ['LOG_CHANNEL_ID'])
except KeyError:
    pass
INFO_UPDATE_TIME = 30

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
        message = await channel.send("Gathering the data...")
    except AttributeError:
        print("Cant find channel with such ID. Server statistics functionality is disabled.\nAre you sure you've set this up correctly?")
    except NameError:
        print("STATISTICS_CHANNEL_ID isnt set. Server statistics functionality is disabled.\nAre you sure you've set this up correctly?")
    except discord.errors.Forbidden:
        print("Dont have permissions to send messages into channel with provided ID.\nServer statistics functionality is disabled.\nAre you sure you've set this up correctly?")
    else:
        print('Successfully joined {} channel, starting to gather statistics'.format(channel))
        known_server_countries = []
        while True:
            kag_servers = api.get_active_servers()
            servers_amount = len(kag_servers)
            players_amount = 0
            for x in kag_servers:
                players_amount += len(x['playerList'])

            for server in kag_servers:
                country = None
                for item in known_server_countries:
                    if item['ip'] == server['IPv4Address']:
                        country = item['country']
                        #print("Country of {} is already known, skipped adding to list".format(server['IPv4Address']))
                    else:
                        continue
                if not country:
                    country = server_country(server['IPv4Address'])
                    x = {}
                    x['ip'] = server['IPv4Address']
                    x['country'] = country
                    known_server_countries.append(x)
                    print("Country of {} is {}, added to list".format(server['IPv4Address'], country))
                server['country'] = country

            kag_servers.sort(key = sort_by_players, reverse = True)

            if servers_amount == 0:
                response_message = "Its dead, Jim :("
            else:
                response_message = "**Featuring:**"
                leftowers_counter = 0
                for server in kag_servers:
                    tempmsg = ""
                    tempmsg += "\n**:flag_{}: {}**\n".format(server['country'], server['name'])
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
            embed.set_footer(text="Statistics update each {} seconds".format(INFO_UPDATE_TIME))

            await message.edit(content=None, embed=embed)
            await sleep(INFO_UPDATE_TIME)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.lower() == "ping":
        await message.channel.send("pong")

@client.event
async def on_member_join(member):
    try:
        channel = client.get_channel(LOG_CHANNEL_ID)
        await channel.send("{} has joined the server".format(member.mention))
    except AttributeError:
        print("Cant find channel with {} id. Leave/join logging is disabled".format(LOG_CHANNEL_ID))
    except NameError:
        print("LOG_CHANNEL_ID isnt set. Leave/join logging is disabled")
    except discord.errors.Forbidden:
        print("Dont have permissions to send messages into {}. Leave/join logging is disabled".format(channel))

@client.event
async def on_member_leave(member):
    try:
        channel = client.get_channel(LOG_CHANNEL_ID)
        await channel.send("{} has left the server".format(member.mention))
    except AttributeError:
        print("Cant find channel with {} id. Leave/join logging is disabled".format(LOG_CHANNEL_ID))
    except NameError:
        print("LOG_CHANNEL_ID isnt set. Leave/join logging is disabled")
    except discord.errors.Forbidden:
        print("Dont have permissions to send messages into {}. Leave/join logging is disabled".format(channel))

## Usage
if __name__ == "__main__":
    try:
        client.run(BOT_TOKEN)
    except discord.errors.LoginFailure:
        print("Invalid token error: double-check the value of DISCORD_KEY environment variable.\nAbort")
        exit(1)
