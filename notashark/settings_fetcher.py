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

# This module contains everything related to working with per-guild settings

import logging
import json
from notashark import configuration
from time import sleep

log = logging.getLogger(__name__)

SETTINGS_FILE = configuration.SETTINGS_FILE
SETTINGS_AUTOSAVE_TIME = configuration.SETTINGS_AUTOSAVE_TIME

class Settings_Fetcher:
    '''All the stuff related to loading and saving per-guild settings'''
    def __init__(self, settings_file = SETTINGS_FILE):
        self.settings_dictionary = {} #is dic to make it easier to search for settings later without involving iteration
        self.settings_file = settings_file
        try:
            s = self.settings_loader()
        except Exception as e:
            log.error(f"An unfortunate exception has occured while trying to load serverlist: {e}")
        else:
            self.settings_dictionary = s

    def settings_loader(self):
        '''Loads settings from self.settings_file, if available'''
        with open(self.settings_file, 'r') as j:
            data = json.load(j)
        log.debug(f"Got following data: {data}")
        return data

    def settings_saver(self):
        '''Converts self.settings_dictionary to json and saves to self.settings_file, if possible'''
        jdata = json.dumps(self.settings_dictionary)
        with open(self.settings_file, 'w') as f:
            f.write(jdata)
        log.debug(f"Successfully wrote data to {self.settings_file}")

    def settings_checker(self, guild_id):
        '''Receive str(guild_id). If guild doesnt exist - add it to list'''
        #I have no idea if this should be there at all, lol
        guild_id = str(guild_id)
        if not guild_id in self.settings_dictionary:
            log.debug(f"Couldnt find {guild_id} in self.settings_dictionary, adding")
            x = {}
            x['serverlist_channel_id'] = None #id of serverlist channel
            x['serverlist_message_id'] = None #id of message that should be edited with actual info
            #idk if this needs more settings

            self.settings_dictionary[guild_id] = x
            #Im not sure if this may go into race condition situation if called for multiple servers at once. Hopefully not
            log.debug(f"Now settings list looks like: {self.settings_dictionary}")
        else:
            log.debug(f"Found {guild_id} on self.settings_dictionary, no need to add manually")

def _settings_autosaver():
    '''Autosaves settings to SETTINGS_FILE each SETTINGS_AUTOSAVE_TIME seconds.
    Intended to be ran in separate thread on application's launch'''
    sf = Settings_Fetcher()

    log.debug(f"Waiting {SETTINGS_AUTOSAVE_TIME} seconds to save settings to {SETTINGS_FILE}")
    sleep(SETTINGS_AUTOSAVE_TIME)
    try:
        sf.settings_saver()
    except Exception as e:
        log.critical(f"Unable to save settings to file: {e}")
