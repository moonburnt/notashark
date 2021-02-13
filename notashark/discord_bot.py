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

# This module contains discord bot itself, aswell as directly related functionality

import discord
from notashark import data_fetcher, settings_fetcher, configuration, embeds_processor
from asyncio import sleep
import logging
from discord.ext import commands

log = logging.getLogger(__name__)

BOT_NAME = configuration.BOT_NAME
BOT_PREFIX = configuration.BOT_PREFIX
SERVERLIST_UPDATE_TIME = configuration.SERVERLIST_UPDATE_TIME
SETTINGS_AUTOSAVE_TIME = configuration.SETTINGS_AUTOSAVE_TIME

sf = settings_fetcher.Settings_Fetcher()

async def status_updater():
    '''Updates current bot's status'''
    #this throws exception if ran "right away", while kag_servers hasnt been populated yet
    raw_data = data_fetcher.kag_servers
    print(raw_data)
    if raw_data and (int(raw_data['total_players_amount']) > 0):
        message = f"with {raw_data['total_players_amount']} peasants | {BOT_PREFIX}help"
    else:
        message = f"alone | {BOT_PREFIX}help"

    await bot.change_presence(activity=discord.Game(name=message))

async def serverlist_autoupdater():
    '''Automatically update serverlist for all matching servers. Expects sf.settings_dictionary to exist and have items inside'''
    for item in sf.settings_dictionary:
        #doing this way, in case original message got wiped. Prolly need to catch some expected exceptions to dont log them
        try:
            #future reminder: serverlist_channel_id should always be int
            channel = bot.get_channel(sf.settings_dictionary[item]['serverlist_channel_id'])
            message_id = sf.settings_dictionary[item]['serverlist_message_id']
            message = await channel.fetch_message(message_id)
        except discord.errors.NotFound:
            log.warning(f"Unable to find message {message_id}, setting up new one")
            channel = bot.get_channel(sf.settings_dictionary[item]['serverlist_channel_id'])
            message = await channel.send("Gathering the data...")
            log.info(f"Sent placeholder serverlist msg to {item}/{channel.id}")
            sf.settings_dictionary[item]['serverlist_message_id'] = message.id
        except Exception as e:
            #this SHOULD NOT happening, kept there as "last resort"
            log.error(f"Got exception while trying to edit serverlist message: {e}")
            return
        finally:
            infobox = embeds_processor.serverlist_embed()
            await message.edit(content=None, embed=infobox)
            log.info(f"Successfully updated serverlist on {channel.id}/{message.id}")

bot = commands.Bot(command_prefix=BOT_PREFIX)
converter = commands.TextChannelConverter()
#removing default help, coz its easier to make a new one than to rewrite a template
bot.remove_command('help')

@bot.event
async def on_ready():
    log.info(f'Running {BOT_NAME} as {bot.user}!')
    while True:
        #sleeping before task to let statistics populate on bot's launch
        await sleep(SERVERLIST_UPDATE_TIME)
        log.debug(f"Updating serverlists")
        await serverlist_autoupdater()
        log.debug(f"Updating bot's status")
        await status_updater()

@bot.event
async def on_guild_available(ctx):
    log.info(f"Connected to guild {ctx.id}")
    log.debug(f"Checking if bot knows about this guild")
    sf.settings_checker(ctx.id) #mybe rewrite this? idk

@bot.command()
async def info(ctx, *args):
    try:
        server_address = args[0]
        ip, port = server_address.split(":")
    except:
        await ctx.channel.send(f"This command requires server IP and port to work. Correct syntax be like: `{BOT_PREFIX}info 8.8.8.8:80`")
        log.info(f"{ctx.author} has asked for server info, but misspelled prefix")
        return

    try:
        infobox, minimap = embeds_processor.single_server_embed(ip, port)
    except Exception as e:
        await ctx.channel.send(f"Couldnt find `{server_address}`. Are you sure the address is correct and server is up and running?")
        log.info(f"Got exception while trying to answer {ctx.author} with info of {server_address}: {e}")
    else:
        await ctx.channel.send(content=None, file=minimap, embed=infobox)
        log.info(f"{ctx.author} has asked for server info of {server_address}. Responded")

@bot.command()
async def set(ctx, *args):
    admin_check = ctx.message.author.guild_permissions.administrator #ensuring that message's author is admin
    #this doesnt need to be multiline, coz next arg is checked only if first match
    #thus there should be no exception if args is less than necessary
    if len(args) >= 3 and (args[0] == "autoupdate") and (args[1] == "channel") and admin_check:
        try:
            clink = args[2]
            log.debug(f"Attempting to get ID of channel {clink}")
            cid = await converter.convert(ctx, clink)
            channel_id = cid.id
            #its necessary to specify ctx.guild.id as str, coz json cant into ints in keys
            sf.settings_dictionary[str(ctx.guild.id)]['serverlist_channel_id'] = channel_id
            #resetting message id, in case this channel has already been set for that purpose in past
            sf.settings_dictionary[str(ctx.guild.id)]['serverlist_message_id'] = None
        except Exception as e:
            log.error(f"Got exception while trying to edit serverlist message: {e}")
            await ctx.channel.send(f"Something went wrong... Please double-check syntax and try again")
        else:
            await ctx.channel.send(f"Successfully set {cid} as channel for autoupdates")
            log.info(f"{ctx.author.id} tried to set {cid} as channel for autoupdates on {ctx.guild.id}/{ctx.channel.id}. Granted")
    else:
        await ctx.channel.send(f"Unable to process your request: please double-check syntax and your permissions on this guild")

@bot.command()
async def serverlist(ctx):
    try:
        infobox = embeds_processor.serverlist_embed()
    except Exception as e:
        await ctx.channel.send(f"Something went wrong...")
        log.error(f"An unfortunate exception has occured while trying to send serverlist: {e}")
    else:
        await ctx.channel.send(content=None, embed=infobox)
        log.info(f"{ctx.author} has asked for serverlist. Responded")

@bot.command()
async def help(ctx):
    #I thought about remaking it into embed, but it looks ugly this way
    await ctx.channel.send(f"Hello, Im {BOT_NAME} bot and Im there to assist you with all King Arthur's Gold needs!\n\n"
    f"Currently there are following custom commands available:\n"
    f"`{BOT_PREFIX}info IP:port` - will display detailed info of selected server, including description and in-game minimap\n"
    f"`{BOT_PREFIX}serverlist` - will display list of active servers with their base info, aswell as total population statistics\n"
    f"`{BOT_PREFIX}set autoupdate channel #channel_id` - will set passed channel to auto-fetch serverlist each {SERVERLIST_UPDATE_TIME} seconds. You must be guild's admin to use it\n"
    )
    log.info(f"{ctx.author.id} has asked for help on {ctx.guild.id}/{ctx.channel.id}. Responded")
