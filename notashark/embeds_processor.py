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
from notashark import data_fetcher
from io import BytesIO
from datetime import datetime

log = logging.getLogger(__name__)

def sanitizer(raw_data):
    '''Receives dictionary. Sanitizies its content to dont include anything
    that could accidently break markdown or ping people. Then return dic back'''
    log.debug(f"Attempting to sanitize {raw_data}")
    clean_data = []
    for key, value in raw_data.items():
        try:
            nomark = utils.escape_markdown(value)
            nomen = utils.escape_mentions(nomark)
            clean_data.append((key, nomen))
        #avoiding issue with trying to apply string method to minimap's bytes
        except TypeError:
            clean_data.append((key, value))
        except Exception as e:
            log.warning(f"Unable to sanitize dictionary: {e}")

    data = dict(clean_data)
    log.debug(f"Sanitizer returned followed data: {data}")

    return data

def single_server_embed(ip, port):
    '''Receives ip and port, returns embed with server's
    info and minimap file to attach to message'''
    log.debug(f"Preparing embed for info of server with address {ip}:{port}")
    raw_data = data_fetcher.single_server_fetcher(ip, port)

    log.debug(f"Getting minimap")
    mm = BytesIO(raw_data['minimap'])
    minimap = File(mm, filename="minimap.png")

    data = sanitizer(raw_data)

    log.debug(f"Building single server embed")
    embed = Embed(timestamp=datetime.utcnow())
    embed.colour = 0x3498DB
    embed.title = data['name'][:256]
    #Idk the correct maximum allowed size of embed field's value.
    #Someone has told that its 1024, but I will use 256
    #to avoid overcoming max allowed size of embed itself.
    embed.add_field(name="Description:",
                    value=data['description'][:256],
                    inline=False)
    #maybe also include country's icon? idk
    embed.add_field(name="Location:", value=data['country_name'], inline=False)
    embed.add_field(name="Link:", value=data['link'], inline=False)
    embed.add_field(name="Game Mode:", value=data['mode'], inline=False)
    embed.add_field(name="Players:", value=data['players'], inline=False)
    embed.add_field(name="Currently Playing:",
                    value=data['nicknames'][:1024],
                    inline=False)

    embed.set_image(url="attachment://minimap.png")

    return embed, minimap

def serverlist_embed():
    '''Returns embed with list of all up and running kag servers'''
    log.debug(f"Preparing embed for serverlist")
    raw_data = data_fetcher.kag_servers

    log.debug(f"Building serverlist embed")
    embed = Embed(timestamp=datetime.utcnow())
    embed.colour = 0x3498DB
    embed_title = (f"There are currently {raw_data['servers_amount']} active "
                   f"servers with {raw_data['total_players_amount']} players")
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
            field_content = (f"\n**Address:** {data['link']}"
                             f"\n**Game Mode:** {data['mode']}"
                             f"\n**Players:** {data['players']}"
                             f"\n**Currently Playing**: {data['nicknames']}")

            #This part isnt fair coz server with dozen players will be treated
            #as low-populated. Also it looks like crap and needs to be reworked.
            #TODO
            field_lengh = len(field_content)
            title_lengh = len(field_title)
            future_message_lengh = field_lengh + title_lengh + message_len
            if field_lengh <= 1024 and (future_message_lengh < 6000):
                message_len += field_lengh + title_lengh
                embed.add_field(name = field_title[:256],
                                value = field_content,
                                inline = False)
            else:
                leftowers_counter += 1
        else:
            leftowers_counter += 1

    if leftowers_counter > 0:
        field_name = f"\n*And {leftowers_counter} less populated servers*"
        embed.add_field(name = field_name, inline=False)

    embed.title = embed_title
    embed.description = embed_description

    return embed

def kagstats_embed(player):
    '''Receive str with player name or str/int with player id.
    Returns embed with kagstats info of that player'''
    log.debug(f"Preparing embed for kagstats info of player {player}")

    raw_data = data_fetcher.kagstats_fetcher(player)
    data = sanitizer(raw_data)

    log.debug(f"Building kagstats info embed")
    player_info = (f"**Name**: {data['clan_tag'][:256]} "
                   f"{data['character_name'][:256]}\n"
                   f"**Username**: {data['username']}\n"
                    "**KAG Stats**: "
                   f"<https://kagstats.com/#/players/{data['id']}>")

    positive_stats = (f"**Total KDR**: {data['total_kdr']}\n"
                      f"**Total Kills**: {data['total_kills']}\n"
                      f"**Flags Captured**: {data['captures']}")

    negative_stats = (f"**Team Kills**: {data['team_kills']}\n"
                      f"**Deaths**: {data['total_deaths']}\n"
                      f"**Suicides**: {data['suicides']}")

    archer_stats = (f"**KDR**: {data['archer_kdr']}\n"
                    f"**Kills**: {data['archer_kills']}\n"
                    f"**Deaths**: {data['archer_deaths']}")

    builder_stats = (f"**KDR**: {data['builder_kdr']}\n"
                    f"**Kills**: {data['builder_kills']}\n"
                    f"**Deaths**: {data['builder_deaths']}")

    knight_stats = (f"**KDR**: {data['knight_kdr']}\n"
                    f"**Kills**: {data['knight_kills']}\n"
                    f"**Deaths**: {data['knight_deaths']}")

    top_weapons = ""
    for item in data['top_weapons']:
        weapon_info = f"**{item['weapon']}**: {item['kills']} kills\n"
        top_weapons += weapon_info

    embed = Embed(timestamp=datetime.utcnow())
    embed.colour = 0x3498DB
    #if user has no avatar set - this wont do anything
    embed.set_thumbnail(url=data['avatar'])
    embed.title = "KAG Stats: Profile"
    embed.add_field(name = "User Info", value = player_info, inline = False)
    embed.add_field(name = "Positive", value = positive_stats)
    embed.add_field(name = "Negative", value = negative_stats)
    embed.add_field(name = "Top Weapons", value = top_weapons)
    embed.add_field(name = "Archer", value = archer_stats)
    embed.add_field(name = "Builder", value = builder_stats)
    embed.add_field(name = "Knight", value = knight_stats)

    return embed

def leaderboard_embed(scope):
    '''Receive str with scope/type of leaderboard (e.g archer or monthly_archer).
    Returns embed with kagstats info of that category'''
    log.debug(f"Preparing embed for leaderboard {scope}")
    raw_data, embed_description = data_fetcher.leaderboard_fetcher(scope)

    data = []
    positions = ['First', 'Second', 'Third']
    for item, position in zip(raw_data, positions):
        clean_item = sanitizer(item)
        clean_item['position'] = position
        data.append(clean_item)

    log.debug(f"Building leaderboard embed")
    embed = Embed(timestamp=datetime.utcnow())
    embed.colour = 0x3498DB
    embed.title = "KAG Stats: Leaderboard"
    embed.description = f"**{embed_description}**"
    for item in data:
        user_info = (f"**Name:** {item['clan_tag'][:256]} "
                     f"{item['character_name'][:256]}\n"
                     f"**Username**: {item['username'][:256]}\n"
                     f"**KDR**: {item['kdr']}\n"
                     f"**Kills**: {item['kills']}\n"
                     f"**Deaths**: {item['deaths']}\n")
        embed.add_field(name = f"{item['position']}:",
                        value = user_info, inline = False)

    return embed
