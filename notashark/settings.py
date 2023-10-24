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

import aiofiles
import asyncio
import logging
import json
from os.path import join
from typing import Optional

log = logging.getLogger(__name__)


class SettingsManager:
    """Everything related to settings loading, updating and saving"""

    def __init__(self, settings_path: str = "settings.json"):
        self._settings_path = settings_path
        self._storage = {}

    @property
    def storage(self) -> dict:
        return self._storage

    @property
    def settings_path(self) -> str:
        return self._settings_path

    async def load_settings(self):
        """Load settings into storage"""

        try:
            async with aiofiles.open(self.settings_path, "r") as f:
                raw = await f.read()
                settings = json.loads(raw)
        except Exception as e:
            log.error(f"Unable to load settings from {self.settings_path}: {e}")
        else:
            self._storage = settings

    async def save_settings(self):
        """Save storage into settings file"""

        data = json.dumps(self.storage)

        async with aiofiles.open(self.settings_path, "w") as f:
            await f.write(data)

        log.debug(f"Successfully saved settings to {self.settings_path}")

    def add_entry(
        self,
        guild_id: int | str,
        serverlist_channel_id: Optional[str] = None,
        serverlist_message_id: Optional[str] = None,
    ) -> bool:
        """Add guild_id to self.storage, in case its not there"""

        # better safe than sorry
        guild_id = str(guild_id)

        if guild_id in self.storage:
            log.debug(f"{guild_id} is already in storage, no need to add again")
            return False

        else:
            log.debug(f"Couldnt find {guild_id} in settings storage, adding")
            x = {}
            # id of serverlist channel
            x["serverlist_channel_id"] = serverlist_channel_id
            # id of message that should be edited
            x["serverlist_message_id"] = serverlist_message_id
            # idk if this needs more settings
            self._storage[guild_id] = x
            # Im not sure if this may go into race condition situation
            # if called for multiple servers at once. Hopefully not
            log.debug(f"Now settings storage looks like: {self.storage}")

            return True

    async def autosave_task(self, autosave_time: int = 300):
        """Run self.save_settings() in a loop"""

        while True:
            log.debug(f"Waiting {self.autosave_time} seconds before next save")
            await asyncio.sleep(self.autosave_time)

            try:
                await self.save_settings()
            except Exception as e:
                log.critical(
                    f"Unable to save settings to {self.settings_path}: {e}"
                )
            else:
                log.info(
                    f"Successfully saved settings into {self.settings_path}"
                )

    # async def run(self):
    #     """Run the whole thing altogether"""

    #     await self.load_settings()
    #     await self.autosave_task()
