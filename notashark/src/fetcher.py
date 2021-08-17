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

# This module contains everything related to fetching and processing data from api

import requests
import json
from pykagapi import kag, kagstats
from threading import Lock
from re import sub
from time import sleep
from io import BytesIO
from . import parts
from .embeds import sanitize
import logging

log = logging.getLogger(__name__)

DEFAULT_AUTOUPDATE_TIME = 30

LEADERBOARD_URL = "https://kagstats.com/#/leaderboards"
LEADERBOARD_SCOPES = {
    "kdr": {
        "get_leaderboard": kagstats.leaderboard.global_kdr,
        "description": "All Time KDR",
        "url": "Hidden",
        "kills_slug": "totalKills",
        "deaths_slug": "totalDeaths",
    },
    "kills": {
        "get_leaderboard": kagstats.leaderboard.global_kills,
        "description": "All Time Kills",
        "url": "Hidden",
        "kills_slug": "totalKills",
        "deaths_slug": "totalDeaths",
    },
    "global_archer": {
        "get_leaderboard": kagstats.leaderboard.global_archer,
        "description": "All Time Archer",
        "url": LEADERBOARD_URL + "/Archer",
        "kills_slug": "archerKills",
        "deaths_slug": "archerDeaths",
    },
    "monthly_archer": {
        "get_leaderboard": kagstats.leaderboard.monthly_archer,
        "description": "Monthly Archer",
        "url": LEADERBOARD_URL + "/MonthlyArcher",
        "kills_slug": "archerKills",
        "deaths_slug": "archerDeaths",
    },
    "global_builder": {
        "get_leaderboard": kagstats.leaderboard.global_builder,
        "description": "All Time Builder",
        "url": LEADERBOARD_URL + "/Builder",
        "kills_slug": "builderKills",
        "deaths_slug": "builderDeaths",
    },
    "monthly_builder": {
        "get_leaderboard": kagstats.leaderboard.monthly_builder,
        "description": "Monthly Builder",
        "url": LEADERBOARD_URL + "/MonthlyBuilder",
        "kills_slug": "builderKills",
        "deaths_slug": "builderDeaths",
    },
    "global_knight": {
        "get_leaderboard": kagstats.leaderboard.global_knight,
        "description": "All Time Knight",
        "url": LEADERBOARD_URL + "/Knight",
        "kills_slug": "knightKills",
        "deaths_slug": "knightDeaths",
    },
    "monthly_knight": {
        "get_leaderboard": kagstats.leaderboard.monthly_knight,
        "description": "Monthly Knight",
        "url": LEADERBOARD_URL + "/MonthlyKnight",
        "kills_slug": "knightKills",
        "deaths_slug": "knightDeaths",
    },
}

# Idk how to phrase some of these. The changes from reference are the following:
# 'builder' is 'Pickaxe', 'ram' is 'Vehicle',
# 'mine_special' is just 'Mine', 'suddengib' is 'Scrolls'
# #TODO: update pykagapi to include this, as new kagstats should ship these
HITTER_NAMES = (
    "Nothing",
    "Crush",
    "Fall",
    "Water",
    "Water Stun",
    "Water Stun Force",
    "Drown",
    "Fire",
    "Burn",
    "Flying",
    "Stomp",
    "Suicide",
    "Bite",
    "Pickaxe",
    "Sword",
    "Shield",
    "Bomb",
    "Stab",
    "Arrow",
    "Bomb Arrow",
    "Ballista",
    "Stone From Catapult",
    "Boulder From Catapult",
    "Boulder",
    "Vehicle",
    "Explosion",
    "Keg",
    "Mine",
    "Mine",
    "Spikes",
    "Saw",
    "Drill",
    "Muscles",
    "Scrolls",
)


class ApiFetcher:
    """Fetches various data from KAG APIs"""

    def __init__(self, autoupdate_time: int = None):
        self.autoupdate_time = autoupdate_time or DEFAULT_AUTOUPDATE_TIME
        self.countries_locker = Lock()
        self.servers_locker = Lock()
        self.kag_servers = None
        self.known_server_countries = []

    def get_country(self, ip: str) -> dict:
        """Get country of provided ip. Format is based on geojs.io data"""
        response = requests.get(
            url=f"https://get.geojs.io/v1/ip/country/{ip}.json",
            timeout=30,
        )
        return json.loads(response.text)

    def get_servers(self) -> parts.KagServers:
        """Get info about active kag servers"""
        log.debug("Fetching servers from kag api")
        raw_data = kag.servers.active()

        # Calculating amount of players
        players_amount = 0
        for x in raw_data:
            players_amount += len(x["playerList"])

        # Removing unnecessary info from server entries, fixing format
        servers = []
        for server in raw_data:
            servers.append(self.clean_server_info(server))

        # Sorting servers by amount of players
        servers.sort(
            key=lambda x: len(x.nicknames),
            reverse=True,
        )

        data = parts.KagServers(
            servers=servers,
            players_amount=players_amount,
        )

        log.debug(f"Got following kag servers data: {data}")
        return data

    def clean_server_info(self, info: dict) -> parts.KagServerInfo:
        """Clean info of provided server"""
        log.debug(f"Attempting to cleanup following server info: {info}")

        country_prefix = None
        country_name = None
        if self.known_server_countries:
            for item in self.known_server_countries:
                if item["ip"] == info["IPv4Address"]:
                    country_prefix = item["country"].lower()
                    country_name = item["name"]
                    log.debug(f"Found {item['ip']} in self.known_server_countries")
                    break

        if not country_prefix:
            country = self.get_country(info["IPv4Address"])
            with self.countries_locker:
                self.known_server_countries.append(country)
            country_prefix = country["country"].lower()
            country_name = country["name"]
            log.debug(f"Added {info['IPv4Address']} ({country_name}) into storage")

        game_mode = info["gameMode"]
        if info["usingMods"]:
            game_mode += " (modded)"

        capacity = f"{len(info['playerList'])}/{info['maxPlayers']}"
        if info["spectatorPlayers"]:
            capacity += f" ({info['spectatorPlayers']} spectating)"

        link = f"<kag://{info['IPv4Address']}:{info['port']}>"
        if info["password"]:
            link += " (private)"

        server_info = parts.KagServerInfo(
            name=sanitize(info["name"]),
            link=link,
            country_prefix=country_prefix,
            country_name=country_name,
            description=sanitize(
                (
                    sub("\n\n.*", "", info["description"])
                    if info["description"]
                    else "This server has no description"
                )
            ),
            game_mode=sanitize(game_mode),
            capacity=capacity,
            nicknames=(
                sanitize(", ".join(info["playerList"]))
                or "This server is currently empty"
            ),
        )

        log.debug(f"Cleaned up server data is the following: {server_info}")

        return server_info

    def get_server(self, ip: str, port: int) -> parts.KagServerInfo:
        """Get detailed info of requested server with minimap"""
        log.debug(f"Fetching detailed info of {ip}:{port} from kag api")
        server_info = self.clean_server_info(kag.server.status(ip, port))
        # Fetching binary minimap separately, coz its not included by default
        server_info.minimap = BytesIO(kag.server.minimap(ip, port))

        return server_info

    def get_kagstats(self, player: str) -> parts.KagstatsProfile:
        """Get player's kagstats profile info (kdr and such)"""
        log.debug(f"Fetching player profile of {player} from kagstats api")
        try:
            data = kagstats.player.stats_by_name(player)
            player_id = data["player"]["id"]
        except:
            data = kagstats.player.stats_by_id(player)
            player_id = player

        top_weapons = []
        # coz we only need top-3 weapons
        for item in kagstats.player.top_weapons(player_id)[0:3]:
            top_weapons.append(
                parts.KillStats(
                    weapon=HITTER_NAMES[item["hitter"]],
                    kills=int(item["kills"]),
                )
            )

        profile_info = parts.KagstatsProfile(
            _id=player_id,
            account=sanitize(data["player"]["username"]),
            nickname=sanitize(data["player"]["charactername"]),
            clantag=sanitize(data["player"]["clantag"]),
            avatar=data["player"]["avatar"],
            suicides=data["suicides"],
            team_kills=data["teamKills"],
            archer_kills=data["archerKills"],
            archer_deaths=data["archerDeaths"],
            # rounding kdr to always return float like x.xx, to match kagstats ui
            # using formatter, coz round() would trim multiple zeros to one
            archer_kdr="%.2f" % (data["archerKills"] / data["archerDeaths"]),
            builder_kills=data["builderKills"],
            builder_deaths=data["builderDeaths"],
            builder_kdr="%.2f" % (data["builderKills"] / data["builderDeaths"]),
            knight_kills=data["knightKills"],
            knight_deaths=data["knightDeaths"],
            knight_kdr="%.2f" % (data["knightKills"] / data["knightDeaths"]),
            total_kills=data["totalKills"],
            total_deaths=data["totalDeaths"],
            total_kdr="%.2f" % (data["totalKills"] / data["totalDeaths"]),
            captures=kagstats.player.captures(player_id),
            top_weapons=top_weapons,
        )

        log.debug(f"{player} returned following kagstats profile: {profile_info}")
        return profile_info

    def get_leaderboard(self, scope: str) -> parts.Leaderboard:
        """Get leaderboard of provided scope from kagstats api"""
        # this is probably not the most optimal way to do things, but it works
        log.debug(f"Attempting to fetch leaderboard for scope {scope}")
        # This will crash on invalid
        lb = LEADERBOARD_SCOPES[scope]

        # this should already go sorted, no need to do that manually
        players = []
        # We only need top 3 players, coz thats how kagstats webui work
        for item in lb["get_leaderboard"]()[0:3]:
            players.append(
                parts.LeaderboardEntry(
                    account=sanitize(item["player"]["username"]),
                    nickname=sanitize(item["player"]["charactername"]),
                    clantag=sanitize(item["player"]["clantag"]),
                    kills=item[lb["kills_slug"]],
                    deaths=item[lb["deaths_slug"]],
                    kdr="%.2f" % (item[lb["kills_slug"]] / item[lb["deaths_slug"]]),
                )
            )

        leaderboard = parts.Leaderboard(
            description=lb["description"],
            url=lb["url"],
            players=players,
        )

        log.debug(f"Leaderboard of scope {scope} contains: {leaderboard}")
        return leaderboard

    # Stuff below is ugly as hell, but idk how to make it better
    # I mean - I could keep the class route
    # but it would re-introduce all the issues I tried to solve
    def autoupdate_routine(self):
        """Routine that update self.kag_servers with data from self.get_servers().
        Runs each self.autoupdate_time seconds.
        Intended to be ran in separate thread on application's launch
        """
        while True:
            # Doing it there, coz its not async rn and this may take a while
            # And its generally better to use lockers as fast as possible
            servers = self.get_servers()
            with self.servers_locker:
                self.kag_servers = servers
            log.debug("Successfully updated self.kag_servers")
            sleep(self.autoupdate_time)
