### Copyright © 2020, moonburnt
###
### This program is free software. It comes without any warranty, to
### the extent permitted by applicable law. You can redistribute it
### and/or modify it under the terms of the Do What The Fuck You Want
### To Public License, Version 2, as published by Sam Hocevar.
### See the LICENSE file for more details.

### Dead-simple discord bot for King Arthur's Gold

### Patch Notes:
## attempted to fix error caused by connection to kag api being timed out
## added ability to customize logging levels
## attempting to fix rare "double-message" bug, happening under unknown conditions when old status message is unavailable to edit
## replacing all .format strings with f-strings for no reason whatsoever
## renames "spectators" to "spectating", to make it sound better with just one player online
## added custom bot's status
## added ability to request detailed server info
## added timestamps to embeds
## attempted to fix member leave notification not working
## added custom help message
## added custom logger
## changed the format of custom logging levels - used to be literal level's numbers. Now words
################
### TODO:
## sanitize stuff in autoupdate mode
## replace autojoin with dedicated function that will only start posting info after someone will tell so

import discord
import pykagapi
from os import environ
from asyncio import sleep
from sys import exit
#import logging as log
import logging

import requests
import json

from discord.ext import commands
from re import sub
from io import BytesIO
from PIL import Image

from datetime import datetime

# Logger shenanigans
#setting up discord logger
dlog = logging.getLogger('discord')
#dlog.setLevel(logging.INFO)
dlog.setLevel(logging.WARNING)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(fmt='[%(asctime)s][%(name)s][%(levelname)s] %(message)s', datefmt='%d.%m.%y %H:%M:%S'))
dlog.addHandler(handler)

#setting up custom logger
try:
    LOGGING_ENVAR = str(environ['SCRIPT_LOGGING_LEVEL'].lower())
except:
    LOGGING_LEVEL = logging.INFO
else:
    if LOGGING_ENVAR == "debug":
        LOGGING_LEVEL = logging.DEBUG
    elif LOGGING_ENVAR == "warning":
        LOGGING_LEVEL = logging.WARNING
    else:
        LOGGING_LEVEL = logging.INFO

log = logging.getLogger(__name__)
log.setLevel(LOGGING_LEVEL)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(fmt='[%(asctime)s][%(name)s][%(levelname)s] %(message)s', datefmt='%d.%m.%y %H:%M:%S'))
log.addHandler(handler)

log.info(f'Logging level has been set to "{LOGGING_ENVAR}"')

## Vars
BOT_NAME = "notashark"
try:
    BOT_TOKEN = environ['DISCORD_KEY']
except KeyError:
    log.critical("DISCORD_KEY environment variable isnt set. Edit bootin_up.sh accordingly, or set it up manually.\nAbort")
    exit(1)

try:
    STATISTICS_CHANNEL_ID = int(environ['STATISTICS_CHANNEL_ID'])
except:
    log.warning("STATISTICS_CHANNEL_ID isnt set, server stats wont be gathered")
#    pass
else:
    log.info(f"STATISTICS_CHANNEL_ID has been set to {STATISTICS_CHANNEL_ID}")

try:
    LOG_CHANNEL_ID = int(environ['LOG_CHANNEL_ID'])
except:
    log.warning("LOG_CHANNEL_ID isnt set, wont gather info about people joining and leaving discord server")
#    pass
else:
    log.info(f"LOG_CHANNEL_ID has been set to {LOG_CHANNEL_ID}")

try:
    STATISTICS_UPDATE_TIME=int(environ['STATISTICS_UPDATE_TIME'])
except:
    log.warning("STATISTICS_UPDATE_TIME isnt set, using defaults instead")
    STATISTICS_UPDATE_TIME = 30
else:
    if STATISTICS_UPDATE_TIME < 10:
        STATISTICS_UPDATE_TIME = 10
log.info(f"STATISTICS_UPDATE_TIME has been set to {STATISTICS_UPDATE_TIME} seconds")

## Functions
def server_country(ip):
    '''Receives str(ip), returns str(country of that ip) in lowercase format, based on geojs.io data'''
    link = "https://get.geojs.io/v1/ip/country/"+ip+".json"
    response = requests.get(link, timeout = 30)
    pydic = json.loads(response.text)
    #country = pydic['country']
    return pydic

def sort_by_players(x):
    '''Sort received list by len of ['playerList'] in its dictionaries'''
    players = len(x['playerList'])
    return int(players)

def server_info(address):
    '''Receives str(ip:port), returns embed with server's info, aswell as minimap file to attach to message'''

    ip, port = address.split(":")
    info = api.get_server_status(ip, port)

    m = api.get_server_minimap(ip, port)
    mm = BytesIO(m)
    minimap = discord.File(mm, filename="minimap.png")

    title = info['name']

    country = server_country(ip)

    description = sub("\n\n.*", "", info['description'])
    mode = info['gameMode']
    if info['usingMods']:
        mode += " (modded)"

    players_amount = len(info['playerList'])
    players = f"{players_amount}/{info['maxPlayers']}"
    if info['spectatorPlayers']:
        players += f" ({info['spectatorPlayers']} spectating)"

    nicknames = ', '.join(info['playerList'])

    #Sanitizing stuff, to avoid weird markdown-related things from happening
    nicknames = discord.utils.escape_markdown(nicknames)
    description = discord.utils.escape_markdown(description)
    title = discord.utils.escape_markdown(title)
    mode = discord.utils.escape_markdown(mode)

    embed = discord.Embed(timestamp=datetime.utcnow())
    embed.colour = 0x3498DB
    embed.title = title[:256]
    #embed.add_field(name="Server:", value=f"**{info['name']}**", inline=False)
    embed.add_field(name="Description:", value=description[:256], inline=False) #idk the correct maximum allowed size of embed field's value for sure. Got told its 1024, but will use 256 to avoid overcoming the size of embed itself
    embed.add_field(name="Location:", value=country['name'], inline=False)
    embed.add_field(name="Link:", value=f"<kag://{address}>", inline=False)
    embed.add_field(name="Game Mode:", value=mode, inline=False)
    embed.add_field(name="Players:", value=players, inline=False)
    #embed.add_field(name="Currently Playing:", value=(', '.join(info['playerList'])), inline=False)
    embed.add_field(name="Currently Playing:", value=nicknames[:1024], inline=False)

    embed.set_image(url="attachment://minimap.png")

    return embed, minimap


## Code
api = pykagapi.KAG_API()
#client = discord.Client()
bot = commands.Bot(command_prefix="gib ")

#removing default help, coz its easier to make a new one than to rewrite template
bot.remove_command('help')

@bot.event
async def on_ready():
    log.info(f'Running {BOT_NAME} as {bot.user}!')
    try:
        await sleep(1) #attempting to fix the issue with double-posting by adding a timer. Idk if it will work lol
        channel = bot.get_channel(STATISTICS_CHANNEL_ID)
        message = await channel.send("Gathering the data...")
    except AttributeError:
        log.warning("Cant find channel with such ID. Server statistics functionality is disabled.\nAre you sure you've set this up correctly?")
    except NameError:
        log.warning("Tried to gather statistics, but STATISTICS_CHANNEL_ID isnt set")
    except discord.errors.Forbidden:
        log.warning("Dont have permissions to send messages into channel with provided ID.\nServer statistics functionality is disabled.\nAre you sure you've set this up correctly?")
    else:
        log.info(f'Successfully joined {channel} channel, starting to gather statistics')
        known_server_countries = []
        while True:
            log.info("Fetching statistics info")
            try:
                kag_servers = api.get_active_servers()
            #except requests.exceptions.ConnectTimeout:
            #    log.error(f"Unable to connect to kag api - connection has timed out. Repeating in {STATISTICS_UPDATE_TIME} seconds")
            except:
                log.exception(f"Some network-related error has occured. Repeating in {STATISTICS_UPDATE_TIME} seconds")
                await sleep(STATISTICS_UPDATE_TIME)
                #continue
            else:
                servers_amount = len(kag_servers)
                total_players_amount = 0
                for x in kag_servers:
                    total_players_amount += len(x['playerList'])

                for server in kag_servers:
                    country = None
                    for item in known_server_countries:
                        if item['ip'] == server['IPv4Address']:
                            country = item['country']
                            log.debug(f"Country of {server['IPv4Address']} is already known, skipped adding to list")
                        else:
                            continue
                    if not country:
                        c = server_country(server['IPv4Address'])
                        country = c['country'].lower()
                        x = {}
                        x['ip'] = server['IPv4Address']
                        x['country'] = country
                        known_server_countries.append(x)
                        log.debug(f"Country of {server['IPv4Address']} is {country}, added to list")
                    server['country'] = country

                kag_servers.sort(key = sort_by_players, reverse = True)

                log.info("Building the message")
                embed_title = f"There are currently {servers_amount} active servers with {total_players_amount} players"
                embed_footer = f"Statistics update each {STATISTICS_UPDATE_TIME} seconds"

                embed = discord.Embed(timestamp=datetime.utcnow())

                if servers_amount == 0:
                    embed_description = "Its dead, Jim :("
                else:
                    embed_fields_amount = 0
                    embed_description = "**Featuring:**"
                    message_len = 0
                    message_len = len(embed_title)+len(embed_footer)+len(embed_description)

                    leftowers_counter = 0
                    for server in kag_servers:
                        if embed_fields_amount < 25:
                            embed_fields_amount += 1

                            field_title = f"\n**:flag_{server['country']}: {server['name']}**"
                            field_content = ""
                            #field_content += "\n**:flag_{}: {}**\n".format(server['country'], server['name'])
                            field_content += f"\n**Address:** <kag://{server['IPv4Address']}:{server['port']}>"
                            if server['password']:
                                field_content += " (password-protected)"
                            field_content += f"\n**Gamemode:** {server['gameMode']}"
                            if server['usingMods']:
                                field_content += " (modded)"
                            server_players_amount = len(server['playerList'])
                            field_content += f"\n**Players:** {server_players_amount}/{server['maxPlayers']}"
                            if server['spectatorPlayers']:
                                field_content += f" ({server['spectatorPlayers']} spectating)"
                            field_content += "\n**Currently Playing:** {}\n".format((', '.join(server['playerList'])))
                            if len(field_content) <= 1024 and (len(field_content)+len(field_title)+message_len < 6000):
                                message_len += len(field_content)+len(field_title)
                                #print("new message len is {}".format(message_len))
                                embed.add_field(name = field_title[:256], value = field_content, inline=False)
                            else:
                                leftowers_counter += 1
                        else:
                            leftowers_counter += 1

                    if leftowers_counter > 0:
                        embed.add_field(name = f"\n*And {leftowers_counter} less populated servers*", inline=False)

                embed.title = embed_title
                embed.colour = 0x3498DB
                embed.description = embed_description
                embed.set_footer(text=embed_footer)

                try:
                    await message.edit(content=None, embed=embed)
                except discord.errors.NotFound:
                    log.warning("Tried to edit the last message but couldnt find it - sending a new one instead")
                    await sleep(3) #attempting to fix the issue with double-posting by adding a timer. If wont help - just remove this line
                    message = await channel.send(content=None, embed=embed)
                log.info("Statistics info has been successfully updated")

                await bot.change_presence(activity=discord.Game(name=f"with {total_players_amount} peasants | gib help"))

                await sleep(STATISTICS_UPDATE_TIME)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.lower() == "ping":
        await message.channel.send("pong")
        log.info(f"{message.author} has pinged the bot, responded")

    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    try:
        channel = bot.get_channel(LOG_CHANNEL_ID)
        await channel.send("{} has joined the server".format(member.mention))
        log.info(f"{member.mention} has joined the server, logged into {LOG_CHANNEL_ID}")
    except AttributeError:
        log.warning(f"Cant find channel with {LOG_CHANNEL_ID} id. Leave/join logging is disabled")
    except NameError:
        log.warning("LOG_CHANNEL_ID isnt set. Leave/join logging is disabled")
    except discord.errors.Forbidden:
        log.warning(f"Dont have permissions to send messages into {channel}. Leave/join logging is disabled")

@bot.event
#async def on_member_leave(member):
async def on_member_remove(member):
    try:
        channel = bot.get_channel(LOG_CHANNEL_ID)
        await channel.send(f"{member.mention} has left the server")
        log.info(f"{member.mention} has left the server, logged into {LOG_CHANNEL_ID}")
    except AttributeError:
        log.warning(f"Cant find channel with {LOG_CHANNEL_ID} id. Leave/join logging is disabled")
    except NameError:
        log.warning("LOG_CHANNEL_ID isnt set. Leave/join logging is disabled")
    except discord.errors.Forbidden:
        log.warning(f"Dont have permissions to send messages into {channel}. Leave/join logging is disabled")

@bot.command()
async def info(ctx, *args):
    if not args:
        await ctx.channel.send(f"This command requires server IP and port to work. Correct syntax be like: `gib info 8.8.8.8:80`")
        log.info(f"{ctx.author} has asked for server info, but misspelled prefix")
    else:
        server_address = args[0]

        #infobox, minimap = server_info(server_address)

        #await ctx.channel.send(content=None, file=minimap, embed=infobox)

        try:
            infobox, minimap = server_info(server_address)
        except:
            await ctx.channel.send(f"Couldnt find `{server_address}`. Are you sure the address is correct and server is up and running?")
            log.info(f"{ctx.author} has asked for server info of {server_address}, but there is no such server")
        else:
            await ctx.channel.send(content=None, file=minimap, embed=infobox)
            log.info(f"{ctx.author} has asked for server info of {server_address}. Responded")

@bot.command()
async def help(ctx):
    await ctx.channel.send(f"Hello, Im {BOT_NAME} bot and Im there to assist you with all King Arthur's Gold needs!\n\n"
    f"Currently there is but one custom command available:\n"
    f"`gib info IP:port` - will display detailed info of selected server, including description and in-game minimap\n"
    )
    log.info(f"{ctx.author.id} has asked for help on {ctx.guild.id}/{ctx.channel.id}. Responded")

## Usage
if __name__ == "__main__":
    try:
        bot.run(BOT_TOKEN)
    except discord.errors.LoginFailure:
        log.critical("Invalid token error: double-check the value of DISCORD_KEY environment variable.\nAbort")
        exit(1)
