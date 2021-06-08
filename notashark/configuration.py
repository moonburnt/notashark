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

# This module contains default configuration variables, to use from other modules

from os.path import join

BOT_NAME = "notashark"
BOT_PREFIX = "!"
SERVERLIST_UPDATE_TIME = 30
#updating settings file each 5 minutes
SETTINGS_AUTOSAVE_TIME = 300
SETTINGS_FILE = join('.', 'settings.json')
LOG_FILE = f"{BOT_NAME}.log"
