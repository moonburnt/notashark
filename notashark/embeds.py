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

from notashark import parts
import logging
from discord import utils, Embed, File
from datetime import datetime

log = logging.getLogger(__name__)


def sanitize(data: str) -> str:
    """Sanitize provided data to dont include special symbols"""

    return str(utils.escape_mentions(utils.escape_markdown(data)))


def make_server_embed(
    data: parts.KagServerInfo,
) -> parts.EmbedStorage:
    """Build single server embed out of provided data"""

    # This is a nasty workaround to fix the discord's "clever" caching issue
    # Basically - if filename stays the same, sometimes discord decides to show
    # the older image instead of never. Which cause minimap to never update
    # This will crash if minimap doesnt exist #TODO
    timestamp = datetime.utcnow()
    filename = f"{timestamp.timestamp()}_minimap.png"
    minimap = File(data.minimap, filename=filename)

    embed = Embed(timestamp=timestamp)
    embed.colour = 0x3498DB
    embed.title = "KAG Server Info"
    # Idk the correct maximum allowed size of embed field's value.
    # Someone has told that its 1024, but I will use 256
    # to avoid overcoming max allowed size of embed itself.
    embed.add_field(
        name="Name:",
        value=data.name[:256],
        inline=False,
    )
    embed.add_field(
        name="Description:",
        value=(data.description[:256] or "None"),
        inline=False,
    )
    # maybe also include country's icon? #TODO
    embed.add_field(
        name="Location:",
        value=data.country_name,
        inline=False,
    )

    embed.add_field(
        name="Link:",
        value=data.link,
        inline=False,
    )
    embed.add_field(
        name="Game Mode:",
        value=data.game_mode,
        inline=False,
    )
    embed.add_field(
        name="Players:",
        value=data.capacity,
        inline=False,
    )
    embed.add_field(
        name="Currently Playing:",
        value=data.nicknames[:1024],
        inline=False,
    )

    embed.set_image(url=f"attachment://{filename}")

    return parts.EmbedStorage(embed, minimap)


def make_servers_embed(data: parts.KagServers) -> Embed:
    """Build embed with summary about all populated kag servers"""

    embed = Embed(timestamp=datetime.utcnow())
    embed.colour = 0x3498DB
    embed_title = "KAG Server List"
    embed_overview = (
        f"**Current Amount of Players:** {data.players_amount}\n"
        f"**Currently Active Servers:** {len(data.servers)}\n"
    )

    embed.add_field(
        name="Overview:",
        value=embed_overview,
        inline=False,
    )
    embed_fields_amount = 1
    message_len = len(embed_title) + len(embed_overview)
    leftowers_counter = 0
    # this looks ugly as hell, maybe I should do something about it in future
    for server in data.servers:

        if embed_fields_amount < 25:
            embed_fields_amount += 1

            field_title = f"\n**:flag_{server.country_prefix}: {server.name}**"
            field_content = (
                f"\n**Address:** {server.link}"
                f"\n**Game Mode:** {server.game_mode}"
                f"\n**Players:** {server.capacity}"
                f"\n**Currently Playing**: {server.nicknames}"
            )

            # This part isnt fair coz server with dozen players will be treated
            # as low-populated. Also it looks like crap and needs to be reworked.
            # TODO
            field_lengh = len(field_content)
            title_lengh = len(field_title)
            future_message_lengh = field_lengh + title_lengh + message_len
            if field_lengh <= 1024 and (future_message_lengh < 6000):
                message_len += field_lengh + title_lengh
                embed.add_field(
                    name=field_title[:256],
                    value=field_content,
                    inline=False,
                )
                continue

        leftowers_counter += 1

    if leftowers_counter > 0:
        embed.add_field(
            name=f"\n*And {leftowers_counter} less populated servers*",
            inline=False,
        )

    embed.title = embed_title

    return embed


def make_kagstats_embed(data: parts.KagstatsProfile) -> Embed:
    """Build embed with someone's kagstats profile data"""

    top_weapons = ""
    for item in data.top_weapons:
        weapon_info = f"**{item.weapon}**: {item.kills} kills\n"
        top_weapons += weapon_info

    embed = Embed(timestamp=datetime.utcnow())
    embed.colour = 0x3498DB
    # if user has no avatar set - this wont do anything
    embed.set_thumbnail(url=data.avatar)
    embed.title = "KAG Stats: Profile"
    embed.add_field(
        name="Overview:",
        value=(
            f"**Name**: {data.clantag[:256]} {data.nickname[:256]}\n"
            f"**Username**: {data.account}\n"
            f"**KAG Stats**: <https://kagstats.com/#/players/{data._id}>"
        ),
        inline=False,
    )
    embed.add_field(
        name="Total Positive:",
        value=(
            f"**KDR**: {data.total_kdr}\n"
            f"**Kills**: {data.total_kills}\n"
            f"**Flags Captured**: {data.captures}"
        ),
    )
    embed.add_field(
        name="Total Negative:",
        value=(
            f"**Team Kills**: {data.team_kills}\n"
            f"**Deaths**: {data.total_deaths}\n"
            f"**Suicides**: {data.suicides}"
        ),
    )
    embed.add_field(
        name="Top Weapons:",
        value=top_weapons,
    )
    embed.add_field(
        name="Archer Stats:",
        value=(
            f"**KDR**: {data.archer_kdr}\n"
            f"**Kills**: {data.archer_kills}\n"
            f"**Deaths**: {data.archer_deaths}"
        ),
    )
    embed.add_field(
        name="Builder Stats:",
        value=(
            f"**KDR**: {data.builder_kdr}\n"
            f"**Kills**: {data.builder_kills}\n"
            f"**Deaths**: {data.builder_deaths}"
        ),
    )
    embed.add_field(
        name="Knight Stats:",
        value=(
            f"**KDR**: {data.knight_kdr}\n"
            f"**Kills**: {data.knight_kills}\n"
            f"**Deaths**: {data.knight_deaths}"
        ),
    )

    return embed


def make_leaderboard_embed(data: parts.Leaderboard) -> Embed:
    """Build leaderboard embed with provided leaderboard content"""

    players = []
    for item, position in zip(data.players, ("First", "Second", "Third")):
        item.position = position
        players.append(item)

    embed = Embed(timestamp=datetime.utcnow())
    embed.colour = 0x3498DB
    embed.title = "KAG Stats: Leaderboard"
    embed.add_field(
        name="Overview:",
        value=(
            f"**Leaderboard:** {data.description}\n"
            f"**KAG Stats URL:** <{data.url}>"
        ),
        inline=False,
    )

    for player in players:
        embed.add_field(
            name=f"{player.position}:",
            value=(
                f"**Name:** {player.clantag[:256]} "
                f"{player.nickname[:256]}\n"
                f"**Username**: {player.account[:256]}\n"
                f"**KDR**: {player.kdr}\n"
                f"**Kills**: {player.kills}\n"
                f"**Deaths**: {player.deaths}\n"
            ),
            inline=False,
        )

    return embed


def make_about_embed(name: str = "notashark", prefix: str = "!") -> Embed:
    """Build embed with general info about this bot"""

    embed = Embed(timestamp=datetime.utcnow())
    embed.colour = 0x3498DB
    embed.title = "About Bot"
    embed.add_field(
        name="Overview:",
        value=(
            f"**{name}** - discord bot for King Arthur's Gold, written in python "
            "+ discord.py. Its designed to work on multiple discord guilds at "
            "once, feature ability to setup per-guild settings via chat commands "
            "and be able to display all major information related to the game.\n"
            "This bot is completely free and opensource: if you want to run your "
            "own instance or contribute - visit bot's development page below"
        ),
        inline=False,
    )
    embed.add_field(
        name="How to Use:",
        value=f"Just type **{prefix}help** in chat to get all available commands",
        inline=False,
    )
    embed.add_field(
        name="Development Page:",
        value="<https://github.com/moonburnt/notashark>",
        inline=False,
    )

    return embed
