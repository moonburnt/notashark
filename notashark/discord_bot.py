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
from notashark import data_fetcher, settings_fetcher
from asyncio import sleep
import logging
from discord.ext import commands
from io import BytesIO
from datetime import datetime

log = logging.getLogger(__name__)

BOT_NAME = "notashark"
BOT_PREFIX = "!"
STATISTICS_UPDATE_TIME = 10
SETTINGS_AUTOSAVE_TIME = 600 #prolly too much. Also would benefit from being configurable as envar

df = data_fetcher.Data_Fetcher()
sf = settings_fetcher.Settings_Fetcher()

def _sanitizer(raw_data):
    '''Receives dictionary with kag servers-related data. Sanitizing all necessary entries and returning it back'''
    log.debug(f"Sanitizing stuff, to avoid weird markdown-related things from happening")
    data = {}
    data['name'] = discord.utils.escape_markdown(raw_data['name'])
    data['country_name'] = raw_data['country_name']
    data['country_prefix'] = raw_data['country_prefix']
    if raw_data['description']:
        data['description'] = discord.utils.escape_markdown(raw_data['description'])
    else:
        data['description'] = "This server has no description"
    data['mode'] = discord.utils.escape_markdown(raw_data['mode'])
    data['players'] = raw_data['players']
    if raw_data['private']:
        data['link'] = f"{raw_data['link']} (private)"
    else:
        data['link'] = raw_data['link']
    if raw_data['nicknames']:
        data['nicknames'] = discord.utils.escape_markdown(raw_data['nicknames'])
    else:
        data['nicknames'] = "There are currently no players on this server"

    return data

def single_server_embed(address):
    '''Receives str(ip:port), returns embed with server's info, aswell as minimap file to attach to message'''
    log.debug(f"Preparing embed for info of server with address {address}")
    ip, port = address.split(":")
    raw_data = df.single_server_fetcher(ip, port)

    log.debug(f"Getting minimap")
    mm = BytesIO(raw_data['minimap'])
    minimap = discord.File(mm, filename="minimap.png")

    data = _sanitizer(raw_data)

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

def serverlist_embed():
    '''Returns list of all up and running kag servers. Meant to be used in loop and not as standalone command'''
    log.debug(f"Fetching data")
    raw_data = df.kag_servers

    log.debug(f"Building embed")
    embed = discord.Embed(timestamp=datetime.utcnow())
    embed.colour = 0x3498DB
    embed_title = f"There are currently {raw_data['servers_amount']} active servers with {raw_data['total_players_amount']} players"
    embed_description = "**Featuring:**"

    log.debug(f"Adding servers to message")
    embed_fields_amount = 0
    message_len = len(embed_title)+len(embed_description)
    leftowers_counter = 0
    for server in raw_data['servers']:
        if embed_fields_amount < 25:
            embed_fields_amount += 1
            data = _sanitizer(server)

            field_title = f"\n**:flag_{data['country_prefix']}: {data['name']}**"
            field_content = ""
            field_content += f"\n**Address:** {data['link']}"
            field_content += f"\n**Game Mode:** {data['mode']}"
            field_content += f"\n**Players:** {data['players']}"
            field_content += f"\n**Currently Playing**: {data['nicknames']}"

            #this part isnt fair coz server with dozen players will be treated as low-populated
            #also it looks like crap and needs to be reworked #TODO
            if len(field_content) <= 1024 and (len(field_content)+len(field_title)+message_len < 6000):
                message_len += len(field_content)+len(field_title)
                embed.add_field(name = field_title[:256], value = field_content, inline=False)
            else:
                leftowers_counter += 1
        else:
            leftowers_counter += 1

    if leftowers_counter > 0:
        embed.add_field(name = f"\n*And {leftowers_counter} less populated servers*", inline=False)

    embed.title = embed_title
    embed.description = embed_description

    return embed

async def status_updater():
    '''Updates current bot's status'''
    #this throws exception if ran "right away", while kag_servers hasnt been populated yet
    raw_data = df.kag_servers
    if raw_data or (int(raw_data['total_players_amount']) > 0):
        message = f"with {raw_data['total_players_amount']} peasants | {BOT_PREFIX}help"
    else:
        message = f"alone | {BOT_PREFIX}help"

    await bot.change_presence(activity=discord.Game(name=message))

async def serverlist_autoupdater():
    '''Automatically update serverlist for all matching servers. Expects sf.settings_dictionary to exist and have items inside'''
    for item in sf.settings_dictionary:
        #doing this way, in case original message got wiped. Prolly need to catch some expected exceptions to dont log them
        try:
            channel = bot.get_channel(sf.settings_dictionary[item]['serverlist_channel_id']) #this expects int, but it should be tis way anyway, so dont writing it specially
            message_id = sf.settings_dictionary[item]['serverlist_message_id']
            message = await channel.fetch_message(message_id)
            infobox = serverlist_embed()
            await message.edit(content=None, embed=infobox)

        except Exception as e:
            #this may be faulty if some gibberish has got into settings dictionary. But it shouldnt get there, so I dont care
            log.error(f"Got exception while trying to edit serverlist message: {e}")
            channel = bot.get_channel(sf.settings_dictionary[item]['serverlist_channel_id'])
            message = await channel.send("Gathering the data...")
            log.info(f"Sent placeholder serverlist msg to {item}/{channel.id}")
            sf.settings_dictionary[item]['serverlist_message_id'] = message.id

bot = commands.Bot(command_prefix=BOT_PREFIX)
converter = commands.TextChannelConverter()
#removing default help, coz its easier to make a new one than to rewrite a template
bot.remove_command('help')

@bot.event
async def on_ready():
    log.info(f'Running {BOT_NAME} as {bot.user}!')

    settings_file_update_timer = 0 #this is but nasty hack, but Im not doing multithreading for just that
    while True:
        settings_file_update_timer += STATISTICS_UPDATE_TIME
        await sleep(STATISTICS_UPDATE_TIME) #sleeping before task to let statistics update
        log.debug(f"Updating serverlists")
        await serverlist_autoupdater()
        log.debug(f"Updating bot's status")
        await status_updater()

        if settings_file_update_timer >= SETTINGS_AUTOSAVE_TIME:
            settings_file_update_timer = 0
            log.debug(f"Overwriting settings")
            sf.settings_saver()

@bot.event
async def on_guild_available(ctx):
    log.info(f"Connected to guild {ctx.id}")
    log.debug(f"Checking if bot knows about this guild")
    sf.settings_checker(ctx.id) #mybe rewrite this? idk

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
        await ctx.channel.send(f"This command requires server IP and port to work. Correct syntax be like: `{BOT_PREFIX}info 8.8.8.8:80`")
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
            log.info(f"{ctx.author} has asked for server info of {server_address}. Responded")

@bot.command()
async def set(ctx, *args):
    admin_check = ctx.message.author.guild_permissions.administrator #ensuring that message's author is admin
    if len(args) >= 3 and (args[0] == "autoupdate") and (args[1] == "channel") and admin_check: #this doesnt need to be multiline - other args will be checked only if first has matched, thus there should be no accident exceptions
        try:
            clink = args[2]
            log.debug(f"Attempting to get ID of channel {clink}")
            cid = await converter.convert(ctx, clink)
            channel_id = cid.id
            sf.settings_dictionary[str(ctx.guild.id)]['serverlist_channel_id'] = channel_id #its necessary to specify ctx.guild.id as str, coz json cant into ints in keys
            #resettings message id, in case this channel has already been set for that purpose in past
            sf.settings_dictionary[str(ctx.guild.id)]['serverlist_message_id'] = None
            print(sf.settings_dictionary)
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
        infobox = serverlist_embed()
    except Exception as e:
        await ctx.channel.send(f"Something went wrong...")
        log.error(f"An unfortunate exception has occured while trying to send serverlist: {e}")
    else:
        await ctx.channel.send(content=None, embed=infobox)
        log.info(f"{ctx.author} has asked for serverlist. Responded")

@bot.command()
async def help(ctx):
    await ctx.channel.send(f"Hello, Im {BOT_NAME} bot and Im there to assist you with all King Arthur's Gold needs!\n\n"
    f"Currently there are following custom commands available:\n"
    f"`{BOT_PREFIX}info IP:port` - will display detailed info of selected server, including description and in-game minimap\n"
    f"`{BOT_PREFIX}serverlist` - will display list of active servers with their base info, aswell as total population statistics\n"
    f"`{BOT_PREFIX}set autoupdate channel #channel_id` - will set passed channel to auto-fetch serverlist each {STATISTICS_UPDATE_TIME} seconds. You must be guild's admin to use it\n"
    )
    log.info(f"{ctx.author.id} has asked for help on {ctx.guild.id}/{ctx.channel.id}. Responded")

###
def main(bot_token, statistics_update_time):
    '''Running the damn thing'''

    global STATISTICS_UPDATE_TIME
    STATISTICS_UPDATE_TIME = statistics_update_time
    df.statistics_update_time = STATISTICS_UPDATE_TIME

    try:
        bot.run(bot_token)
    except discord.errors.LoginFailure:
        log.critical("Invalid token error: double-check the value of DISCORD_KEY environment variable.\nAbort")
        exit(1)
