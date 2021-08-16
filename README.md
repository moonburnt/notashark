# notashark

## Description:

**notashark** -  discord bot for King Arthur's Gold, written in python + discord.py.
Its designed to be able to run on multiple discord guilds at once, feature ability
to setup some per-guild settings via chat commands (and save them between bot's
sessions in simple json file) and be able to display all major information related
to the game, including:
- List of servers with total amount of players
- Detailed server info with minimap and nicknames of players
- Kagstats profile info
- Kagstats leaderboards

You can see some usage screenshots in [screenshots](https://github.com/moonburnt/notashark/tree/master/screenshots).

## Development Status:

This bot is considered to be feature-complete. There may be some small fixes and
improvements, but for the most - bot is already done and ready for daily usage.

## Dependencies:

- python 3.8 (may work on previous versions)
- discord.py
- requests
- [pykagapi](https://github.com/moonburnt/pykagapi)

## Installation:

- `git clone https://github.com/moonburnt/notashark.git`
- `cd notashark`
- `pip install -r requirements.txt`

## Usage:

Bot's development repository contain
[example launcher script](https://github.com/moonburnt/notashark/blob/master/launcher.sh),
which, once configured, can be used as sort of "autorun template" to drop into
cronjob and forget about. Below are examples of how to run bot without it.

### Basic:

- Run `python ./notashark --show-logs --token=YOUR_TOKEN` (where YOUR_TOKEN is
your discord bot's token)
This will run bot in its default configuration, suitable for most needs.

### Recommended:

- Set 'NOTASHARK_DISCORD_KEY' environment variable to your bot's discord token
- `python ./notashark -h` to get list of all available launch flags
- Run `python ./notashark` with whatever flags you like (there is no need to pass
token as launch argument again - it will be fetched from envars).
This is a bit more secure thus recommended way to use this bot.

## LICENSE:

[GPLv3](https://github.com/moonburnt/notashark/blob/master/LICENSE)
