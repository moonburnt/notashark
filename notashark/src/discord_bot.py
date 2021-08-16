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

# This module contains discord bot itaswell as directly related functionality

import discord
from . import fetcher, settings, embeds
from asyncio import sleep
import logging
import threading
from sys import exit
from discord.ext import commands, tasks
from types import SimpleNamespace

log = logging.getLogger(__name__)


def make_bot(
    settings_manager: settings.SettingsManager = None,
    api_fetcher: fetcher.ApiFetcher = None,
    command_prefix: str = "!",
    bot_name: str = "notashark",
):
    """Factory to create bot's instance with provided settings"""
    bot = commands.Bot(command_prefix=command_prefix)
    converter = commands.TextChannelConverter()

    # this is kinda bad in terms of being future-proof, but thats the recommended
    # way to store custom vars rn #TODO
    bot.config = SimpleNamespace()
    bot.config.settings_manager = settings_manager or settings.SettingsManager()
    bot.config.api_fetcher = api_fetcher or fetcher.ApiFetcher()
    bot.config.name = bot_name
    bot.config.command_prefix = command_prefix

    # removing default help, coz its easier to make a new, than to fix a template
    bot.remove_command("help")

    def run(token: str):
        """Run bot and related routines"""
        try:
            log.debug("Launching data fetcher")
            # daemon=True allows to shutdown this thing in case of emergency right away
            dft = threading.Thread(
                target=bot.config.api_fetcher.autoupdate_routine, daemon=True
            )
            dft.start()

            log.debug("Initializing settings manager")
            sat = threading.Thread(
                target=bot.config.settings_manager.autosave_routine,
            )
            sat.start()

            log.debug("Launching notashark")
            bot.run(token)
        except discord.errors.LoginFailure:
            log.critical(
                "Invalid token error. Please check if token you've passed to bot "
                "is correct, then try again"
            )
            exit(1)
        except Exception as e:
            log.critical(
                f"Some critical error has occured during bot initialization: {e}"
            )
            exit(1)

        # This will wait for bot to actually connect - see before_updating()
        # log.debug("Launching stats autoupdater")
        # update_everything.start()

    bot.config.run = run

    async def update_status():
        """Update bot's status with current bot.config.api_fetcher.kag_servers data"""
        data = bot.config.api_fetcher.kag_servers
        if data and (data.players_amount > 0):
            message = f"with {data.players_amount} peasants | {command_prefix}help"
        else:
            message = f"alone | {command_prefix}help"

        await bot.change_presence(activity=discord.Game(name=message))

    async def update_serverlists():
        """Update serverlists on all servers that have this feature enabled"""
        for item in bot.config.settings_manager.storage:
            # avoiding entries without serverlist_channel_id being set
            if (
                not bot.config.settings_manager.storage[item]
                or not bot.config.settings_manager.storage[item][
                    "serverlist_channel_id"
                ]
            ):
                continue

            try:
                # future reminder: serverlist_channel_id should always be int
                channel = bot.get_channel(
                    bot.config.settings_manager.storage[item]["serverlist_channel_id"]
                )
                message = await channel.fetch_message(
                    bot.config.settings_manager.storage[item]["serverlist_message_id"]
                )
            except AttributeError:
                log.warning(
                    f"Unable to update serverlist on channel {channel_id}:"
                    f"guild {item} is unavailable"
                )
                continue
            except (discord.errors.NotFound, discord.errors.HTTPException):
                log.debug("Unable to find existing message, configuring new one")
                channel = bot.get_channel(
                    bot.config.settings_manager.storage[item]["serverlist_channel_id"]
                )
                message = await channel.send("Gathering the data...")
                log.debug("Sent placeholder serverlist msg to {item}/{channel.id}")
                bot.config.settings_manager.storage[item][
                    "serverlist_message_id"
                ] = message.id
            except Exception as e:
                # this SHOULD NOT happen, kept there as "last resort"
                log.error(f"Got exception while trying to edit serverlist message: {e}")
                continue

            infobox = embeds.make_servers_embed(bot.config.api_fetcher.get_servers())
            await message.edit(content=None, embed=infobox)
            log.info(f"Successfully updated serverlist on {channel.id}/{message.id}")

    @bot.event
    async def on_ready():
        log.info(f"Running {bot.config.name} as {bot.user}!")
        log.debug("Launching stats autoupdater")
        update_everything.start()

    # amount of time is pause between tasks, NOT time before task dies
    @tasks.loop(seconds=bot.config.api_fetcher.autoupdate_time)
    async def update_everything():
        log.debug("Updating serverlists")
        await update_serverlists()
        log.debug("Updating bot's status")
        await update_status()

    # ensuring that updater only runs if bot is ready
    @update_everything.before_loop
    async def before_updating():
        await bot.wait_until_ready()

    @bot.event
    async def on_guild_available(ctx):
        log.info(f"Connected to guild {ctx.id}")
        log.debug(f"Ensuring bot knows about guild {ctx.id}")
        bot.config.settings_manager.add_entry(
            guild_id=str(ctx.id),
        )

    # this is an easier way to do "server" prefix without massive 'if/else's afterwards
    @bot.group(
        name="server",
        # This makes it possible to use this command without additional args
        invoke_without_command=True,
    )
    async def server_group(ctx):
        await ctx.channel.send(
            "This command requires you to specify which type "
            "of servers-related info you want to get. Valid "
            "options are:\n`list` - to get list of currently active "
            "servers\n`info *ip:port*` - to get detailed information "
            "of some specific server (including minimap)"
        )
        log.info(f"{ctx.author} has asked for server info, but misspelled prefix")
        return

    @server_group.command(name="list")
    async def get_servers(ctx):
        try:
            infobox = embeds.make_servers_embed(bot.config.api_fetcher.get_servers())
        except Exception as e:
            await ctx.channel.send("Something went wrong...")
            log.error(
                f"An exception has occured while trying to send servers embed: {e}"
            )
        else:
            await ctx.channel.send(
                content=None,
                embed=infobox,
            )
            log.info(f"{ctx.author} has asked for servers embed. Responded")

    @server_group.command(name="info")
    async def get_server(ctx, *args):
        # #TODO: add ability to accept kag:// uri
        try:
            server_address = args[0]
            ip, port = server_address.split(":")
        except:
            await ctx.channel.send(
                "This command requires server IP and port to work."
                f"For example: `{configuration.BOT_PREFIX}"
                "server info 8.8.8.8:80`"
            )
            log.info(f"{ctx.author} has asked for server info, but misspelled prefix")
            return

        try:
            data = embeds.make_server_embed(bot.config.api_fetcher.get_server(ip, port))
        except Exception as e:
            await ctx.channel.send(
                "Couldnt find such server. Are you sure the address is correct?"
            )
            log.info(
                f"Got exception while trying to answer {ctx.author} "
                f"with info of {server_address}: {e}"
            )
        else:
            await ctx.channel.send(
                content=None,
                file=data.attachment,
                embed=data.embed,
            )
            log.info(f"Responded {ctx.author} with server info of {server_address}.")

    @bot.command(name="set")
    async def configure(ctx, *args):
        # this doesnt need to be multiline, coz next arg is checked only if first match
        # thus there should be no exception if args is less than necessary
        if (
            len(args) >= 3
            and (args[0] == "autoupdate")
            and (args[1] == "channel")
            and
            # ensuring that message's author is admin
            ctx.message.author.guild_permissions.administrator
        ):
            try:
                clink = args[2]
                log.debug(f"Attempting to get ID of channel {clink}")
                cid = await converter.convert(ctx, clink)
                # its necessary to specify ctx.guild.id as str, coz json cant into ints in keys
                bot.config.settings_manager.storage[str(ctx.guild.id)][
                    "serverlist_channel_id"
                ] = cid.id
                # resetting message id, in case this channel has already been set for that purpose in past
                bot.config.settings_manager.storage[str(ctx.guild.id)][
                    "serverlist_message_id"
                ] = None
            except Exception as e:
                log.error(f"Got exception while trying to set autoupdate channel: {e}")
                await ctx.channel.send(
                    "Something went wrong... "
                    "Please double-check syntax and try again"
                )
            else:
                await ctx.channel.send(
                    f"Successfully set {cid} as channel for autoupdates"
                )
                log.info(
                    f"{ctx.author.id} tried to set {cid} as channel for "
                    f"autoupdates on {ctx.guild.id}/{ctx.channel.id}. Granted"
                )
        else:
            await ctx.channel.send(
                "Unable to process your request: please double-check "
                "syntax and your permissions on this guild"
            )

    @bot.command(name="kagstats")
    async def get_kagstats(ctx, *args):
        if not args:
            await ctx.channel.send(
                "This command requires player name or id to be supplied. "
                f"For example: `{command_prefix}kagstats bunnie`"
            )
            log.info(f"{ctx.author} has asked for player info, but misspelled prefix")
            return

        player = args[0]
        try:
            infobox = embeds.make_kagstats_embed(
                bot.config.api_fetcher.get_kagstats(player)
            )
        except Exception as e:
            await ctx.channel.send(
                f"Couldnt find such player. Are you sure this player "
                "exists and you didnt misspell their name or kagstats id?"
            )
            log.info(
                f"Got exception while trying to answer {ctx.author} with info of player {player}: {e}"
            )
        else:
            await ctx.channel.send(content=None, embed=infobox)
            log.info(
                f"{ctx.author} has asked for player info of {player} on "
                f"{ctx.guild.id}/{ctx.channel.id}. Responded"
            )

    # #TODO: remake this to command group
    @bot.command(name="leaderboard")
    async def get_leaderboard(ctx, *args):
        if not args:
            await ctx.channel.send(
                "This command requires leaderboard type. "
                f"For example: `{command_prefix}leaderboard kdr`\n"
                "Available parts are the following:\n"
                " - kdr\n - kills\n - monthly archer\n"
                " - monthly builder\n - monthly knight\n"
                " - global archer\n - global builder\n - global knight"
            )
            log.info(f"{ctx.author} has asked for leaderboard, but didnt specify type")
            return

        if args[0] in ("kills", "kdr"):
            prefix = args[0]
        elif (
            len(args) >= 2
            and args[0] in ("global", "monthly")
            and args[1] in ("archer", "builder", "knight")
        ):
            prefix = "_".join(args[0:2])

        try:
            infobox = embeds.make_leaderboard_embed(
                bot.config.api_fetcher.get_leaderboard(prefix)
            )
        except UnboundLocalError:
            await ctx.channel.send(
                "Couldnt find such leaderboard. "
                "Please, double-check the prefix and try again"
            )
            log.info(f"{ctx.author} has asked for leaderboard, but misspelled prefix")
        except Exception as e:
            await ctx.channel.send(
                "Unable to fetch leaderboard right now. " "Please, try again later"
            )
            log.info(
                f"Got exception while trying to answer {ctx.author} with leaderboard: {e}"
            )
        else:
            await ctx.channel.send(content=None, embed=infobox)
            log.info(
                f"{ctx.author} has asked for leaderboard on {ctx.guild.id}/{ctx.channel.id}. Responded"
            )

    @bot.command(name="help")
    async def get_help(ctx):
        # I thought about remaking it into embed, but it looks ugly this way
        await ctx.channel.send(
            f"Hello, Im {bot.config.name} bot and Im there to assist you with all "
            "King Arthur's Gold needs!\n\n"
            "Currently there are following custom commands available:\n"
            f"`{command_prefix}server list` - will display list of active servers "
            "with their base info, aswell as their total population numbers\n"
            f"`{command_prefix}server info *IP:port*` - will display detailed "
            "info of selected server, including description and in-game minimap\n"
            f"`{command_prefix}kagstats *player*` - will display gameplay "
            "statistics of player with provided kagstats id or username\n"
            f"`{command_prefix}leaderboard *type*` - will display top-3 players "
            "in this category of kagstats leaderboard. To get list of available parts - "
            f"just type `{command_prefix}leaderboard`, without specifying anything\n"
            f"`{command_prefix}set autoupdate channel #channel_id` - will set "
            f"passed channel to auto-fetch serverlist each {bot.config.api_fetcher.autoupdate_time} "
            "seconds. Keep in mind that you must be guild's admin to use it!\n"
            f"`{command_prefix}help` - shows this message\n"
            f"`{command_prefix}about` - shows general bot's info"
        )
        log.info(
            f"{ctx.author.id} has asked for help on {ctx.guild.id}/{ctx.channel.id}. Responded"
        )

    @bot.command(name="about")
    async def get_bot_description(ctx):
        infobox = embeds.make_about_embed()
        await ctx.channel.send(content=None, embed=infobox)
        log.info(f"{ctx.author} has asked for info about this bot. Responded")

    return bot
