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

# This module contains parts used across the bot

import logging
from dataclasses import dataclass
from discord import Embed, File

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class KagServers:
    servers: list
    players_amount: int = 0


# Not frozen coz of minimap
@dataclass
class KagServerInfo:
    name: str
    link: str
    country_prefix: str
    country_name: str
    description: str
    game_mode: str
    capacity: str
    nicknames: str
    minimap: bytes = None


# I should probably also add nemesis/bullied players #TODO
@dataclass(frozen=True)
class KagstatsProfile:
    _id: str
    account: str
    nickname: str
    clantag: str
    avatar: str
    suicides: int
    team_kills: int
    archer_kills: int
    archer_deaths: int
    archer_kdr: float
    builder_kills: int
    builder_deaths: int
    builder_kdr: float
    knight_kills: int
    knight_deaths: int
    knight_kdr: float
    total_kills: int
    total_deaths: int
    total_kdr: float
    captures: int
    top_weapons: list


@dataclass(frozen=True)
class KillStats:
    weapon: str
    kills: int


# Not frozen due to position
@dataclass
class LeaderboardEntry:
    account: str
    nickname: str
    clantag: str
    kills: int
    deaths: int
    kdr: str


@dataclass(frozen=True)
class Leaderboard:
    url: str
    description: str
    players: list


@dataclass(frozen=True)
class EmbedStorage:
    embed: Embed
    attachment: File
