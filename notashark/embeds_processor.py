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

# This module contains functions related to processing embeds

import logging
from discord import utils, Embed, File
from notashark import data_fetcher, configuration
from io import BytesIO
from datetime import datetime

log = logging.getLogger(__name__)

SERVERLIST_UPDATE_TIME = configuration.SERVERLIST_UPDATE_TIME

def sanitizer(raw_data):
    '''Receives dictionary. Sanitizies its content to dont include anything that could break markdown or ping people. Then return back'''
    log.debug(f"Attempting to sanitize {raw_data}")
    clean_data = []
    for key, value in raw_data.items():
        try:
            nomark = utils.escape_markdown(value)
            nomen = utils.escape_mentions(nomark)
            clean_data.append((key, nomen))
        #this is probably not the best way to handle exceptions
        #but thus far its been thrown only by binary minimap, so...
        except:
            clean_data.append((key, value))

    data = dict(clean_data)
    log.debug(f"Sanitizer returned followed data: {data}")

    return data

def single_server_embed(address):
    '''Receives str(ip:port), returns embed with server's info, aswell as minimap file to attach to message'''
    log.debug(f"Preparing embed for info of server with address {address}")
    ip, port = address.split(":")
    raw_data = data_fetcher.single_server_fetcher(ip, port)

    log.debug(f"Getting minimap")
    mm = BytesIO(raw_data['minimap'])
    minimap = File(mm, filename="minimap.png")

    data = sanitizer(raw_data)

    log.debug(f"Building embed")
    embed = Embed(timestamp=datetime.utcnow())
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
    raw_data = data_fetcher.kag_servers

    log.debug(f"Building embed")
    embed = Embed(timestamp=datetime.utcnow())
    embed.colour = 0x3498DB
    embed_title = f"There are currently {raw_data['servers_amount']} active servers with {raw_data['total_players_amount']} players"
    embed_description = "**Featuring:**"

    log.debug(f"Adding servers to message")
    embed_fields_amount = 0
    message_len = len(embed_title)+len(embed_description)
    leftowers_counter = 0
    #this looks ugly as hell, maybe I should do something about it in future
    for server in raw_data['servers']:
        if embed_fields_amount < 25:
            embed_fields_amount += 1
            data = sanitizer(server)

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
