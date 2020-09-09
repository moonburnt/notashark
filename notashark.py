### Copyright © 2020, moonburnt
###
### This program is free software. It comes without any warranty, to
### the extent permitted by applicable law. You can redistribute it
### and/or modify it under the terms of the Do What The Fuck You Want
### To Public License, Version 2, as published by Sam Hocevar.
### See the LICENSE file for more details.

### Dead-simple discord bot for King Arthur's Gold

### Patch Notes:
## Now keeping per-server's info in separate embed fields, which should drammatically improve the maximum allowed message size
################
### TODO:
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


            embed_title = "There are currently {} active servers with {} players".format(servers_amount, players_amount)
            embed_footer = "Statistics update each {} seconds".format(INFO_UPDATE_TIME)

            embed = discord.Embed()

            if servers_amount == 0:
                embed_description = "Its dead, Jim :("
            else:
                embed_fields_amount = 0
                embed_description = "**Featuring:**"
                message_len = 0
                message_len = len(embed_title)+len(embed_footer)+len(embed_description)
                #print("message lengh is {}".format(message_len))

                leftowers_counter = 0
                for server in kag_servers:
                    if embed_fields_amount < 25:
                        embed_fields_amount += 1

                        field_title = "\n**:flag_{}: {}**\n".format(server['country'], server['name'])
                        field_content = ""
                        #field_content += "\n**:flag_{}: {}**\n".format(server['country'], server['name'])
                        field_content += "**Address:** <kag://{}:{}>\n".format(server['IPv4Address'], server['port'])
                        field_content += "**Gamemode:** {}\n".format(server['gameMode'])
                        field_content += "**Players:** {}/{}\n".format(len(server['playerList']), server['maxPlayers'])
                        field_content += "**Currently Playing:** {}\n".format((', '.join(server['playerList'])))
                        if len(field_content) <= 1024 and (len(field_content)+len(field_title)+message_len < 6000):
                            message_len += len(field_content)+len(field_title)
                            #print("new message len is {}".format(message_len))
                            embed.add_field(name = field_title[:256], value = field_content, inline=False)
                        else:
                            leftowers_counter += 1
                    else:
                        leftowers_counter += 1

                if leftowers_counter > 0:
                    embed.add_field(name = "\n*And {} less populated servers*".format(leftowers_counter), inline=False)

            embed.title = embed_title
            embed.colour = 0x3498DB
            embed.description = embed_description
            embed.set_footer(text=embed_footer)

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
