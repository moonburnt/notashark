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

from notashark import fetcher, settings, embeds
import discord
from asyncio import sleep
import logging
import threading
from sys import exit
from discord.ext import commands, tasks
from types import SimpleNamespace

log = logging.getLogger(__name__)


class Notashark(commands.Bot):
    """Discord bot for King Arthur's Gold."""

    def __init__(
        self,
        settings_manager: settings.SettingsManager = None,
        api_fetcher: fetcher.ApiFetcher = None,
        command_prefix: str = "!",
        name: str = "notashark",
    ):
        self.settings_manager = settings_manager or settings.SettingsManager()
        self.api_fetcher = api_fetcher or fetcher.ApiFetcher()
        self.name = name
        super().__init__(
            command_prefix=command_prefix,
        )

    def run(self, token, **kwargs):
        """Run bot and related routines."""
        try:
            log.debug("Launching data fetcher")
            # daemon=True allows to shutdown this thing without w8ing for completion
            dft = threading.Thread(
                target=self.api_fetcher.autoupdate_routine,
                daemon=True,
            )
            dft.start()

            log.debug("Initializing settings manager")
            sat = threading.Thread(
                target=self.settings_manager.autosave_routine,
            )
            sat.start()

            log.debug(f"Launching {self.name}")
            super().run(token, **kwargs)
        except discord.errors.LoginFailure:
            log.critical("Invalid bot token! Please double-check and try again")
            exit(1)
        except Exception as e:
            log.critical(f"Unable to initialize {self.name}: {e}")
            exit(1)

    async def on_command_error(self, ctx, error):
        """Process command's error"""

        # Ignoring commands with custom error handlers and invalid commands
        if hasattr(ctx.command, "on_error") or isinstance(
            error, commands.CommandNotFound
        ):
            return

        # Getting original error message from discordpy's wrapper, where available
        error = getattr(error, "original", error)
        log.error(
            f"Command '{self.command_prefix}{ctx.command}' by {ctx.author.id} "
            f"on {ctx.guild.id}/{ctx.channel.id} has raised an exception: "
            f"{type(error).__name__}: {error}"
        )
        await ctx.channel.send(
            "Something went wrong... "
            f"Are you sure you are using '{ctx.command}' correctly?"
        )
        # #TODO: handle specific error types differently


def make_bot(
    settings_manager: settings.SettingsManager = None,
    api_fetcher: fetcher.ApiFetcher = None,
    command_prefix: str = "!",
    name: str = "notashark",
):
    """Factory to create bot's instance with provided settings."""
    bot = Notashark(
        settings_manager=settings_manager,
        api_fetcher=api_fetcher,
        command_prefix=command_prefix,
        name=name,
    )

    # removing default help, coz its easier to make a new, than to fix a template
    bot.remove_command("help")

    converter = commands.TextChannelConverter()

    async def update_status():
        """Update bot's status with current bot.api_fetcher.kag_servers data."""
        data = bot.api_fetcher.kag_servers
        if data and (data.players_amount > 0):
            message = f"with {data.players_amount} peasants | {bot.command_prefix}help"
        else:
            message = f"alone | {bot.command_prefix}help"

        try:
            await bot.change_presence(activity=discord.Game(name=message))
        except Exception as e:
            log.warning(f"Unable to update bot's status: {e}")

    async def update_serverlists():
        """Update serverlists on all servers that have this feature enabled."""
        for item in bot.settings_manager.storage:
            # avoiding entries without serverlist_channel_id being set
            if (
                not bot.settings_manager.storage[item]
                or not bot.settings_manager.storage[item]["serverlist_channel_id"]
            ):
                continue

            chan_id = bot.settings_manager.storage[item]["serverlist_channel_id"]

            try:
                # future reminder: serverlist_channel_id should always be int
                channel = bot.get_channel(chan_id)
                message = await channel.fetch_message(
                    bot.settings_manager.storage[item]["serverlist_message_id"]
                )
            except AttributeError:
                log.warning(
                    f"Unable to update serverlist on channel {chan_id}:"
                    f"guild {item} is unavailable"
                )
                continue
            except (discord.errors.NotFound, discord.errors.HTTPException):
                log.debug("Unable to find existing message, configuring new one")
                try:
                    channel = bot.get_channel(chan_id)
                    message = await channel.send("Gathering the data...")
                except Exception as e:
                    log.warning(
                        f"Unable to create new stats message on {item}/{chan_id}: {e}"
                    )
                    continue
                else:
                    log.debug(f"Sent placeholder serverlist msg to {item}/{channel.id}")
                    bot.settings_manager.storage[item][
                        "serverlist_message_id"
                    ] = message.id
            except Exception as e:
                # this SHOULD NOT happen, kept there as "last resort"
                log.error(
                    "Got exception while trying to edit serverlist message on"
                    f"{item}/{chan_id}: {e}"
                )
                continue

            infobox = embeds.make_servers_embed(bot.api_fetcher.get_servers())
            # Attempting to deal with issues caused by discord api being unavailable.
            try:
                await message.edit(content=None, embed=infobox)
            except Exception as e:
                log.warning(
                    f"Unable to edit serverlist on {item}/{chan_id}: {e}"
                )
                continue
            else:
                log.info(
                    f"Successfully updated serverlist on {channel.id}/{message.id}"
                )

    @bot.event
    async def on_ready():
        """Inform about bot going online and start autoupdating routine."""

        log.info(f"Running {bot.name} as {bot.user}!")
        log.debug("Launching stats autoupdater")
        update_everything.start()

    @tasks.loop(seconds=bot.api_fetcher.autoupdate_time)
    async def update_everything():
        """Update serverlists and bot's status.
        Runs each bot.api_fetcher.autoupdate_time seconds in loop.
        """
        log.debug("Updating serverlists")
        await update_serverlists()
        log.debug("Updating bot's status")
        await update_status()

    @update_everything.before_loop
    async def before_updating():
        """Routine that ensure update_everything() only runs once bot is ready."""
        await bot.wait_until_ready()

    @bot.event
    async def on_guild_available(ctx):
        """Event that triggers each time bot connects to some guild."""
        log.info(f"Connected to guild {ctx.id}")
        log.debug(f"Ensuring bot knows about guild {ctx.id}")
        bot.settings_manager.add_entry(
            guild_id=str(ctx.id),
        )

    # this is a recommended way to handle multi-part commands separated by space
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
        log.info(f"{ctx.author} has asked for server info, but misspelled format")
        return

    @server_group.command(name="list")
    async def get_servers(ctx):
        """Get base info about currently populated servers."""

        infobox = embeds.make_servers_embed(bot.api_fetcher.get_servers())
        await ctx.channel.send(
            content=None,
            embed=infobox,
        )
        log.info(f"{ctx.author} has asked for servers embed. Responded")

    @server_group.command(name="info")
    async def get_server(ctx, *args):
        """Get detailed info about specific kag server."""

        # #TODO: replace this with error handler. Probably
        if not args:
            await ctx.channel.send(
                "This command requires server address or ip:port. For example: "
                f"`{bot.command_prefix}server info kag://138.201.55.232:10592`"
            )
            log.info(f"{ctx.author} has asked for server info, but misspelled format")
            return

        server_address = args[0]
        # avoiding breakage on interactive uri
        if server_address.startswith("<") and server_address.endswith(">"):
            server_address = server_address[1 : (len(server_address) - 1)]
        # support for kag:// uri
        if server_address.startswith("kag://"):
            server_address = server_address[6:]

        data = embeds.make_server_embed(
            bot.api_fetcher.get_server(*server_address.split(":"))
        )
        await ctx.channel.send(
            content=None,
            file=data.attachment,
            embed=data.embed,
        )
        log.info(f"Responded {ctx.author} with server info of {server_address}.")

    @bot.command(name="set")
    async def configure(ctx, *args):
        """Configure bot's autoupdate channel for current server.
        You must have admin rights to use this functionality.
        """
        # ignoring invalid setters. I could rework this to group, but there are
        # no other configuration commands, thus there is no point rn #TODO
        if len(args) >= 3 and (args[0] == "autoupdate") and (args[1] == "channel"):
            # ensuring that message's author is admin
            if not ctx.message.author.guild_permissions.administrator:
                await ctx.channel.send(
                    "You must have admin rights on this guild to do that"
                )

            # Attempting to get ID of channel
            cid = await converter.convert(ctx, args[2])
            # ctx.guild.id must be str, coz json cant into ints in keys
            bot.settings_manager.storage[str(ctx.guild.id)][
                "serverlist_channel_id"
            ] = cid.id
            # resetting message id, in case its already been set in past
            bot.settings_manager.storage[str(ctx.guild.id)][
                "serverlist_message_id"
            ] = None
            await ctx.channel.send(f"Successfully set {cid} as channel for autoupdates")
            log.info(
                f"{ctx.author.id} tried to set {cid} as channel for "
                f"autoupdates on {ctx.guild.id}/{ctx.channel.id}. Granted"
            )

    @bot.command(name="kagstats")
    async def get_kagstats(ctx, *args):
        """Get player's kagstats profile info"""
        if not args:
            await ctx.channel.send(
                "This command requires player name or kagstats id. "
                f"For example: `{bot.command_prefix}kagstats bunnie`"
            )
            # #TODO: maybe make this follow error logging format?
            log.info(f"{ctx.author} has asked for player info, but misspelled format")
            return

        player = args[0]
        infobox = embeds.make_kagstats_embed(bot.api_fetcher.get_kagstats(player))
        await ctx.channel.send(content=None, embed=infobox)
        log.info(
            f"{ctx.author} has asked for player info of {player} on "
            f"{ctx.guild.id}/{ctx.channel.id}. Responded"
        )

    @bot.group(
        name="leaderboard",
        invoke_without_command=True,
    )
    async def leaderboard_group(ctx, *args):
        await ctx.channel.send(
            "This command requires leaderboard type. "
            f"For example: `{bot.command_prefix}leaderboard global kdr`\n"
            "Available types are the following:\n"
            " - global kdr\n - global kills\n - global archer\n"
            " - global builder\n - global knight\n - monthly archer\n"
            " - monthly builder\n - monthly knight\n"
        )
        log.info(f"{ctx.author} has asked for leaderboard, but didnt specify type")

    async def get_leaderboard(ctx, scope: str):
        """Get leaderboard of specified scope"""
        infobox = embeds.make_leaderboard_embed(bot.api_fetcher.get_leaderboard(scope))
        await ctx.channel.send(content=None, embed=infobox)
        log.info(
            f"{ctx.author} has asked for {scope} leaderboard on "
            f"{ctx.guild.id}/{ctx.channel.id}. Responded"
        )

    @leaderboard_group.command(name="global")
    async def get_global_leaderboard(ctx, *args):
        """Get top-3 players from global leaderboard of specified type"""

        if args[0] in ("kills", "kdr"):
            prefix = args[0]
        else:
            prefix = f"global_{args[0]}"

        await get_leaderboard(ctx, prefix)

    @leaderboard_group.command(name="monthly")
    async def get_monthly_leaderboard(ctx, *args):
        """Get top-3 players from monthly leaderboard of specified type"""
        await get_leaderboard(ctx, f"monthly_{args[0]}")

    @bot.command(name="help")
    async def get_help(ctx):
        # I thought about remaking it into embed, but it looks ugly this way
        await ctx.channel.send(
            f"Hello, Im {bot.name} bot and Im there to assist you with all "
            "King Arthur's Gold needs!\n\n"
            "Currently there are following custom commands available:\n"
            f"`{bot.command_prefix}server list` - will display list of active servers "
            "with their base info, aswell as their total population numbers\n"
            f"`{bot.command_prefix}server info *IP:port*` - will display detailed "
            "info of selected server, including description and in-game minimap\n"
            f"`{bot.command_prefix}kagstats *player*` - will display gameplay "
            "statistics of player with provided kagstats id or username\n"
            f"`{bot.command_prefix}leaderboard *type*` - will display top-3 players "
            "in this category of kagstats leaderboard. To get list of available parts - "
            f"just type `{bot.command_prefix}leaderboard`, without specifying anything\n"
            f"`{bot.command_prefix}set autoupdate channel #channel_id` - will set "
            f"passed channel to auto-fetch serverlist each {bot.api_fetcher.autoupdate_time} "
            "seconds. Keep in mind that you must be guild's admin to use it!\n"
            f"`{bot.command_prefix}help` - shows this message\n"
            f"`{bot.command_prefix}about` - shows general bot's info"
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
