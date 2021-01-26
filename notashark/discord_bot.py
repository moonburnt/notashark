## notashark - discord bot for King Arthur's Gold
## Copyright (c) 2021 moonburnt
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see https://www.gnu.org/licenses/gpl-3.0.txt

import discord
from notashark import data_fetcher
from asyncio import sleep
import logging
from discord.ext import commands
from io import BytesIO
from datetime import datetime

log = logging.getLogger(__name__)

BOT_NAME = ""
STATISTICS_UPDATE_TIME = 0

df = data_fetcher.Data_Fetcher(STATISTICS_UPDATE_TIME)

def single_server_embed(address):
    '''Receives str(ip:port), returns embed with server's info, aswell as minimap file to attach to message'''
    log.debug(f"Preparing embed for info of server with address {address}")
    ip, port = address.split(":")
    raw_data = df.single_server_fetcher(ip, port)

    log.debug(f"Getting minimap")
    mm = BytesIO(raw_data['minimap'])
    minimap = discord.File(mm, filename="minimap.png")

    log.debug(f"Sanitizing stuff, to avoid weird markdown-related things from happening")
    data = {}
    data['name'] = discord.utils.escape_markdown(raw_data['name'])
    data['country_name'] = raw_data['country_name']
    data['description'] = discord.utils.escape_markdown(raw_data['description'])
    data['mode'] = discord.utils.escape_markdown(raw_data['mode'])
    data['players'] = raw_data['players']
    data['link'] = raw_data['link']
    if raw_data['nicknames']:
        data['nicknames'] = discord.utils.escape_markdown(raw_data['nicknames'])
    else:
        data['nicknames'] = "There are currently no players on this server"

    log.debug(f"Building embed")
    embed = discord.Embed(timestamp=datetime.utcnow())
    embed.colour = 0x3498DB
    embed.title = data['name'][:256]
    embed.add_field(name="Description:", value=data['description'][:256], inline=False) #idk the correct maximum allowed size of embed field's value for sure. Was told its 1024, but will use 256 to avoid overcoming the size of embed itself
    embed.add_field(name="Location:", value=data['country_name'], inline=False) #maybe also include country's icon? idk
    embed.add_field(name="Link:", value=data['link'], inline=False)
    embed.add_field(name="Game Mode:", value=data['mode'], inline=False)
    embed.add_field(name="Players:", value=data['players'], inline=False)
    embed.add_field(name="Currently Playing:", value=data['nicknames'][:1024], inline=False)

    embed.set_image(url="attachment://minimap.png")
    log.debug(f"returning embed")

    return embed, minimap

#def serverlist_embed():
#    ''''''

## Code
bot = commands.Bot(command_prefix="gib ")

#removing default help, coz its easier to make a new one than to rewrite template
bot.remove_command('help')

@bot.event
async def on_ready():
    log.info(f'Running {BOT_NAME} as {bot.user}!')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.lower() == "ping":
        await message.channel.send("pong")
        log.info(f"{message.author} has pinged the bot, responded")

    await bot.process_commands(message)

@bot.command()
async def info(ctx, *args):
    if not args:
        await ctx.channel.send(f"This command requires server IP and port to work. Correct syntax be like: `gib info 8.8.8.8:80`")
        log.info(f"{ctx.author} has asked for server info, but misspelled prefix")
    else:
        server_address = args[0]

        try:
            infobox, minimap = single_server_embed(server_address)
        except:
            await ctx.channel.send(f"Couldnt find `{server_address}`. Are you sure the address is correct and server is up and running?")
            log.info(f"{ctx.author} has asked for server info of {server_address}, but there is no such server")
        else:
            await ctx.channel.send(content=None, file=minimap, embed=infobox)
            #await ctx.channel.send(content=None, embed=infobox)
            log.info(f"{ctx.author} has asked for server info of {server_address}. Responded")

@bot.command()
async def help(ctx):
    await ctx.channel.send(f"Hello, Im {BOT_NAME} bot and Im there to assist you with all King Arthur's Gold needs!\n\n"
    f"Currently there is but one custom command available:\n"
    f"`gib info IP:port` - will display detailed info of selected server, including description and in-game minimap\n"
    )
    log.info(f"{ctx.author.id} has asked for help on {ctx.guild.id}/{ctx.channel.id}. Responded")

###
def main(bot_token, bot_name, statistics_update_time):
    '''Running the damn thing'''

    global BOT_NAME
    BOT_NAME = bot_name
    global STATISTICS_UPDATE_TIME
    STATISTICS_UPDATE_TIME = statistics_update_time

    try:
        bot.run(bot_token)
    except discord.errors.LoginFailure:
        log.critical("Invalid token error: double-check the value of DISCORD_KEY environment variable.\nAbort")
        exit(1)
