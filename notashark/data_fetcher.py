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

# This module contains everything related to fetching
# raw data from kag api and editing it to be usefull

from pykagapi import kag, kagstats
import logging
import threading
import requests
import json
from re import sub
from time import sleep
from notashark import configuration

log = logging.getLogger(__name__)

SERVERLIST_UPDATE_TIME = configuration.SERVERLIST_UPDATE_TIME
countries_locker = threading.Lock()
servers_locker = threading.Lock()
kag_servers = None
known_server_countries = []

def _get_server_country(ip):
    '''Receives str(ip), returns str(country of that ip) in lowercase.
       Format is based on geojs.io data'''
    link = "https://get.geojs.io/v1/ip/country/"+ip+".json"
    response = requests.get(link, timeout = 30)
    pydic = json.loads(response.text)
    return pydic

def _sort_by_players(x):
    '''Sort received list by len of ['players'] in its dictionaries'''
    #This may bork at times, but I cant figure out why.
    #Probably would be better to move it to related embeds handler?
    players = len(x['nicknames'])
    return int(players)

def _clean_server_info(raw_data):
    '''Receives dictionary with raw server info. Prettify it and return back'''
    log.debug(f"Attempting to cleanup following info: {raw_data}")

    data = {}
    data['name'] = raw_data['name']
    data['link'] = f"<kag://{raw_data['IPv4Address']}:{raw_data['port']}>"
    if raw_data['password']:
        data['link'] += " (private)"

    data['country_prefix'] = None
    data['country_name'] = None
    global known_server_countries
    if known_server_countries:
        for item in known_server_countries:
            if item['ip'] == raw_data['IPv4Address']:
                data['country_prefix'] = item['country'].lower()
                data['country_name'] = item['name']
                log.debug(f"{raw_data['IPv4Address']}'s country is "
                          f"{data['country_name']}/{data['country_prefix']},"
                           "no need to fetch again!")

    if not data['country_prefix']:
        log.debug(f"Dont know country of {raw_data['IPv4Address']}, fetching")
        country = _get_server_country(raw_data['IPv4Address'])
        with countries_locker:
            log.debug(f"Adding {country} to list of known countries")
            known_server_countries.append(country)
        data['country_prefix'] = country['country'].lower()
        data['country_name'] = country['name']
    log.debug(f"Got country {data['country_name']}/{data['country_prefix']}")

    if raw_data['description']:
        data['description'] = sub("\n\n.*", "", raw_data['description'])
    else:
        data['description'] = "This server has no description"
    mode = raw_data['gameMode']
    if raw_data['usingMods']:
        mode += " (modded)"
    data['mode'] = mode

    players_amount = len(raw_data['playerList'])
    players = f"{players_amount}/{raw_data['maxPlayers']}"
    if raw_data['spectatorPlayers']:
        players += f" ({raw_data['spectatorPlayers']} spectating)"
    data['players'] = players

    data['nicknames'] = ', '.join(raw_data['playerList'])
    if not data['nicknames']:
        data['nicknames'] = "There are currently no players on this server"

    log.debug(f"Got following clean data: {data}")
    return data

def single_server_fetcher(ip, port):
    '''Receives str/int for ip and port, returns dictionary with server's info'''
    log.debug("Fetching detailed info for server with"
             f"address {ip}:{port} from kag api")
    raw_data = kag.server.status(ip, port)

    log.debug(f"Got the following raw info: {raw_data}")
    log.debug(f"Cleaning up")
    data = _clean_server_info(raw_data)

    log.debug(f"Fetching minimap")
    data['minimap'] = kag.server.minimap(ip, port)

    log.debug(f"Got following data: {data}")

    return data

def serverlist_fetcher():
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
        clean_info = _clean_server_info(server)
        servers.append(clean_info)

    log.debug(f"Sorting servers by amount of players")
    servers.sort(key = _sort_by_players, reverse = True)

    data['servers'] = servers

    log.debug(f"Got following data: {data}")
    return data

def kagstats_fetcher(player):
    '''Receives str(player name) or str (player id).
    Trying to fetch player's kagstats profile info (kdr and such).
    Then return it as dictionary'''
    log.debug(f"Attempting to fetch info of player {player} from api")
    try:
        raw_data = kagstats.player.stats_by_name(player)
        player_id = raw_data['player']['id']
    except:
        raw_data = kagstats.player.stats_by_id(player)
        player_id = player

    captures = kagstats.player.captures(player_id)

    data = {}
    data['id'] = player_id
    data['username'] = raw_data['player']['username']
    data['character_name'] = raw_data['player']['characterName']
    data['clan_tag'] = raw_data['player']['clanTag']
    data['avatar'] = raw_data['player']['avatar']
    data['suicides'] = raw_data['suicides']
    data['team_kills'] = raw_data['teamKills']
    data['archer_kills'] = raw_data['archerKills']
    data['archer_deaths'] = raw_data['archerDeaths']
    #rounding kdr to always return float like x.xx - not shorter nor longer
    #using formatter instead of "round", coz round trimps multiple zeros to one
    data['archer_kdr'] = "%.2f" % (data['archer_kills']/data['archer_deaths'])
    data['builder_kills'] = raw_data['builderKills']
    data['builder_deaths'] = raw_data['builderDeaths']
    data['builder_kdr'] = "%.2f" % (data['builder_kills']/data['builder_deaths'])
    data['knight_kills'] = raw_data['knightKills']
    data['knight_deaths'] = raw_data['knightDeaths']
    data['knight_kdr'] = "%.2f" % (data['knight_kills']/data['knight_deaths'])
    data['total_kills'] = raw_data['totalKills']
    data['total_deaths'] = raw_data['totalDeaths']
    data['total_kdr'] = "%.2f" % (data['total_kills']/data['total_deaths'])
    data['captures'] = captures
    #I should probably also add favorite weapons and nemesis/bullied players

    log.debug(f"Got following data: {data}")
    return data

def leaderboard_fetcher(scope):
    '''Receives str(scope/type of leaderboard).
    Trying to fetch related leaderboard from kagstats.
    Returns list with names of 3 best players and description'''
    #this is probably not the most optimal way to do things
    #but if it works - it works
    log.debug(f"Attempting to fetch kagstats leaderboard for {scope}")
    if scope == 'kdr':
        leaderboard = kagstats.leaderboard.global_kdr()
        description = 'All Time KDR'
    elif scope == 'kills':
        leaderboard = kagstats.leaderboard.global_kills()
        description = 'All Time Kills'
    elif scope == 'global_archer':
        leaderboard = kagstats.leaderboard.global_archer()
        description = 'All Time Archer'
    elif scope == 'monthly_archer':
        leaderboard = kagstats.leaderboard.monthly_archer()
        description = 'Monthly Archer'
    elif scope == 'global_builder':
        leaderboard = kagstats.leaderboard.global_builder()
        description = 'All Time Builder'
    elif scope == 'monthly_builder':
        leaderboard = kagstats.leaderboard.monthly_builder()
        description = 'Monthly Builder'
    elif scope == 'global_knight':
        leaderboard = kagstats.leaderboard.global_knight()
        description = 'All Time Knight'
    else:
        #I probably shouldnt do it like that, but whatever - its 2 am
        leaderboard = kagstats.leaderboard.monthly_knight()
        description = 'Monthly Knight'

    #this should already go sorted, no need to do anything manually
    data = []
    for item in (leaderboard[0:3]):
        userdata = {}
        userdata['username'] = item['player']['username']
        userdata['character_name'] = item['player']['characterName']
        userdata['clan_tag'] = item['player']['clanTag']
        if scope in ('kdr', 'kills'):
            userdata['kills'] = item['totalKills']
            userdata['deaths'] = item['totalDeaths']
        elif scope in ('global_archer', 'monthly_archer'):
            userdata['kills'] = item['archerKills']
            userdata['deaths'] = item['archerDeaths']
        elif scope in ('global_builder', 'monthly_builder'):
            userdata['kills'] = item['builderKills']
            userdata['deaths'] = item['builderDeaths']
        else:
            #I probably shouldnt do like that either
            #But still - assuming that whatever left is knight stuff
            userdata['kills'] = item['knightKills']
            userdata['deaths'] = item['knightDeaths']
        userdata['kdr'] = "%.2f" % (userdata['kills'] / userdata['deaths'])
        data.append(userdata)

    log.debug(f"Got following data: {data}, {description}")
    return data, description

#Stuff below is ugly as hell, but idk how to make it better
#I mean - I could keep the class route
#but it would re-introduce all the issues I tried to solve
def _serverlist_autoupdater():
    '''Runs serverlist_fetcher in loop, to autoupdate kag_servers on background'''
    while True:
        log.debug(f"Fetching new server info")
        servers = serverlist_fetcher()
        with servers_locker:
            log.debug(f"Updating kag_servers")
            global kag_servers
            kag_servers = servers
        log.debug(f"Successfully updated kag_servers")
        log.debug(f"Waiting {SERVERLIST_UPDATE_TIME} seconds "
                   "to update kag_servers again")
        sleep(SERVERLIST_UPDATE_TIME)
