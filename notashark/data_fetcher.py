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

# This module contains everything related to fetching raw data from kag api and editing it to be usefull

from pykagapi import kag
import logging
from time import sleep
import threading
import requests
import json
from re import sub
from notashark import configuration

log = logging.getLogger(__name__)

SERVERLIST_UPDATE_TIME = configuration.SERVERLIST_UPDATE_TIME

class Data_Fetcher:
    '''Class for all the functions related to obtaining data from kag api and preserving it for our needs'''
    def __init__(self):
        self._servers_locker = threading.Lock() #locker for self.kag_servers to ensure there is no race condition happening
        self._countries_locker = threading.Lock() #locker for self.known_server_countries
        self.kag_servers = None
        self.known_server_countries = []
        #daemon=True allows to shutdown this thing in case of emergency right away
        th = threading.Thread(target=self._serverlist_autoupdater, daemon=True)
        th.start()

    def _get_server_country(self, ip):
        '''Receives str(ip), returns str(country of that ip) in lowercase format, based on geojs.io data'''
        link = "https://get.geojs.io/v1/ip/country/"+ip+".json"
        response = requests.get(link, timeout = 30)
        pydic = json.loads(response.text)
        return pydic

    def _sort_by_players(self, x):
        '''Sort received list by len of ['players'] in its dictionaries'''
        #this may bork at times, but I cant figure out why. Probably would be better to move it to related embeds handler?
        players = len(x['nicknames'])
        return int(players)

    def _clean_server_info(self, raw_data):
        '''Receives dictionary with raw server info. Prettify it and return back'''
        log.debug(f"Attempting to cleanup following info: {raw_data}")

        data = {}
        data['name'] = raw_data['name']
        data['link'] = f"<kag://{raw_data['IPv4Address']}:{raw_data['port']}>"

        data['country_prefix'] = None
        data['country_name'] = None
        if self.known_server_countries:
            for item in self.known_server_countries:
                if item['ip'] == raw_data['IPv4Address']:
                    data['country_prefix'] = item['country'].lower()
                    data['country_name'] = item['name']
                    log.debug(f"{raw_data['IPv4Address']}'s country is {data['country_name']}/{data['country_prefix']}, no need to fetch again!")

        if not data['country_prefix']:
            log.debug(f"Didnt find country of {raw_data['IPv4Address']} in list, fetching")
            country = self._get_server_country(raw_data['IPv4Address'])
            with self._countries_locker:
                log.debug(f"Adding {country} to list of known countries")
                self.known_server_countries.append(country)
            data['country_prefix'] = country['country'].lower()
            data['country_name'] = country['name']
        log.debug(f"Got country {data['country_name']}/{data['country_prefix']}")

        data['description'] = sub("\n\n.*", "", raw_data['description'])
        mode = raw_data['gameMode']
        if raw_data['usingMods']:
            mode += " (modded)"
        data['mode'] = mode

        data['private'] = raw_data['password']

        players_amount = len(raw_data['playerList'])
        players = f"{players_amount}/{raw_data['maxPlayers']}"
        if raw_data['spectatorPlayers']:
            players += f" ({raw_data['spectatorPlayers']} spectating)"
        data['players'] = players

        data['nicknames'] = ', '.join(raw_data['playerList'])

        log.debug(f"Got following clean data: {data}")
        return data

    def single_server_fetcher(self, ip, port):
        '''Receives str/int for ip and port, returns dictionary with server's info'''
        log.debug(f'Fetching detailed info for server with address {ip}:{port} from kag api')
        raw_data = kag.server.status(ip, port)

        log.debug(f"Got the following raw info: {raw_data}")
        log.debug(f"Cleaning up")
        data = self._clean_server_info(raw_data)

        log.debug(f"Fetching minimap")
        data['minimap'] = kag.server.minimap(ip, port)

        log.debug(f"Got following data: {data}")

        return data

    def serverlist_fetcher(self):
        '''Fetching raw list of alive kag servers and returning it'''
        log.debug(f'Fetching serverlist from kag api')
        raw_data = kag.servers.active()

        data = {}
        log.debug(f"Calculating amount of servers")
        data['servers_amount'] = len(raw_data)
        log.debug(f"Calculating amount of total players")
        total_players_amount = 0
        for x in raw_data:
            total_players_amount += len(x['playerList'])
        data['total_players_amount'] = total_players_amount

        log.debug(f"Cleaning up servers info")
        servers = []
        for server in raw_data:
            clean_info = self._clean_server_info(server)
            servers.append(clean_info)

        log.debug(f"Sorting servers by amount of players")
        servers.sort(key = self._sort_by_players, reverse = True)

        data['servers'] = servers

        log.debug(f"Got following data: {data}")
        return data

    def _serverlist_autoupdater(self):
        '''Runs serverlist_fetcher in loop, so it keeps updating data inside self.kag_servers'''
        while True:
            log.debug(f"Fetching new server info")
            servers = self.serverlist_fetcher()
            with self._servers_locker:
                log.debug(f"Updating self.kag_servers")
                self.kag_servers = servers
            log.debug(f"Successfully updated self.kag_servers")
            log.debug(f"Awaiting {SERVERLIST_UPDATE_TIME} seconds to update self.kag_servers")
            sleep(SERVERLIST_UPDATE_TIME)
