#!/usr/bin/env python3

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

from notashark import fetcher, settings, discord_bot
import argparse
from os import environ
from sys import exit
import logging
from logging.handlers import RotatingFileHandler

log = logging.getLogger()


def main():
    # looks like overriding logger's own level isnt the best idea, since it also make
    # logs below its level unaccessible to handlers, regardless of their settings.
    # Correct approach is to set logger itself to some sane level and then toggle
    # things on per-handler basis
    log.setLevel(logging.INFO)

    # Formatter for both handlers
    formatter = logging.Formatter(
        fmt="[%(asctime)s][%(name)s][%(levelname)s] %(message)s",
        datefmt="%d.%m.%y %H:%M:%S",
    )

    # this is a rotating handler that automatically ensures that log wont grow beyond
    # certain size and make backups of older logs. Really cool thing, may tweak it l8r
    file_handler = RotatingFileHandler(
        "notashark.log",
        mode="a",
        maxBytes=(10 * 1024 * 1024),
        backupCount=2,
        encoding=None,
        delay=0,
    )
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)

    # doing it these, because seeing critical errors still may be important
    terminal_handler = logging.StreamHandler()
    terminal_handler.setFormatter(formatter)
    # terminal_handler.setLevel(logging.ERROR)
    log.addHandler(terminal_handler)

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--token",
        help="Use this to supply your token to bot, in case envars arent an option",
    )
    ap.add_argument(
        "--debug", action="store_true", help="Add debug messages to bot's output"
    )
    ap.add_argument(
        "--serverlist-update-time",
        type=int,
        help=(
            "Custom lengh (in seconds) of pause between requests to api in order "
            "to get fresh info about active servers with players on them. Also "
            "used to autoupdate related embed. Could not be less than default "
            f"value, which is {fetcher.DEFAULT_AUTOUPDATE_TIME} seconds"
        ),
    )
    ap.add_argument(
        "--settings-autosave-time",
        type=int,
        help=(
            "Custom lengh (in seconds) of pause between autosaving per-server "
            "settings on disk. Could not be less than default value, which is "
            f"{settings.DEFAULT_AUTOSAVE_TIME} seconds"
        ),
    )
    ap.add_argument(
        "--show-logs",
        action="store_true",
        help=(
            "Enable showcase of logs in terminal. "
            "Else only critical errors will be shown"
        ),
    )
    # TODO: maybe add arg to override log file location/name?
    ap.add_argument(
        "--settings-file",
        help="Custom path to settings file",
    )
    args = ap.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)

    if not args.show_logs:
        terminal_handler.setLevel(logging.CRITICAL)

    bot_token = args.token or environ.get("NOTASHARK_DISCORD_KEY", None)
    if not bot_token:
        log.critical(
            "You didnt specify bot's token! Either set NOTASHARK_DISCORD_KEY "
            "environment variable, or pass it via --token launch argument!\nAbort"
        )
        exit(1)

    servers_autoupdate_time = (
        args.serverlist_update_time
        if args.serverlist_update_time
        and args.serverlist_update_time > fetcher.DEFAULT_AUTOUPDATE_TIME
        else fetcher.DEFAULT_AUTOUPDATE_TIME
    )
    log.info(f"Serverlist will autoupdate each {servers_autoupdate_time} seconds")

    settings_autosave_time = (
        args.settings_autosave_time
        if args.settings_autosave_time
        and args.settings_autosave_time > settings.DEFAULT_AUTOSAVE_TIME
        else settings.DEFAULT_AUTOSAVE_TIME
    )
    log.info(f"Settings will autosave each {settings_autosave_time} seconds")

    # Configuring instances of manager and fetcher to use our settings
    settings_manager = settings.SettingsManager(
        autosave_time=settings_autosave_time,
        settings_file=args.settings_file or settings.DEFAULT_SETTINGS_FILE,
    )
    api_fetcher = fetcher.ApiFetcher(
        autoupdate_time=servers_autoupdate_time,
    )

    # Passing our pre-configured instances to bot
    bot = discord_bot.make_bot(
        settings_manager=settings_manager,
        api_fetcher=api_fetcher,
    )
    bot.run(bot_token)


if __name__ == "__main__":
    main()
