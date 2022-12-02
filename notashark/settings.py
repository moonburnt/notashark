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
from os.path import join
from time import sleep

log = logging.getLogger(__name__)

DEFAULT_AUTOSAVE_TIME = 300
DEFAULT_SETTINGS_FILE = join(".", "settings.json")


class SettingsManager:
    """Everything related to settings loading, updating and saving"""

    def __init__(self, settings_file: str = None, autosave_time: int = None):
        self.settings_file = settings_file or DEFAULT_SETTINGS_FILE
        self.autosave_time = autosave_time or DEFAULT_AUTOSAVE_TIME
        self.storage = {}
        self.load_settings()

    def get_settings(self, filepath: str = None) -> dict:
        """Get settings from provided file"""
        filepath = filepath or self.settings_file
        with open(filepath, "r") as j:
            data = json.load(j)
        log.debug(f"Fetched following settings from {filepath}: {data}")
        return data

    def load_settings(self, filepath: str = None):
        """Load settings into self.storage"""
        try:
            settings = self.get_settings(filepath)
        except Exception as e:
            log.error(f"Unable to load settings from {filepath}: {e}")
        else:
            self.storage = settings

    def save_settings(self, filepath: str = None):
        """Save self.storage into json file"""
        filepath = filepath or self.settings_file
        jdata = json.dumps(self.storage)
        with open(filepath, "w") as f:
            f.write(jdata)

        log.debug(f"Successfully saved settings to {filepath}")

    def add_entry(
        self,
        guild_id: str,
        serverlist_channel_id: str = None,
        serverlist_message_id: str = None,
    ):
        """Add guild_id to self.storage, in case its not there"""
        # better safe than sorry
        guild_id = str(guild_id)

        if guild_id not in self.storage:
            log.debug(f"Couldnt find {guild_id} in settings storage, adding")
            x = {}
            # id of serverlist channel
            x["serverlist_channel_id"] = serverlist_channel_id
            # id of message that should be edited
            x["serverlist_message_id"] = serverlist_message_id
            # idk if this needs more settings
            self.storage[guild_id] = x
            # Im not sure if this may go into race condition situation
            # if called for multiple servers at once. Hopefully not
            log.debug(f"Now settings storage looks like: {self.storage}")
            return

        log.debug(f"{guild_id} is already in storage, no need to add again")

    def autosave_routine(self):
        """Routine that runs self.save_settings() each self.autosave_time seconds.
        Intended to be ran in separate thread on application's launch
        """

        while True:
            log.debug(f"Waiting {self.autosave_time} seconds before next save")
            sleep(self.autosave_time)
            try:
                self.save_settings()
            except Exception as e:
                log.critical(
                    f"Unable to save settings to {self.settings_file}: {e}"
                )
            else:
                log.info(
                    f"Successfully saved settings into {self.settings_file}"
                )
