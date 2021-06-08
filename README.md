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

You can see some usage screenshots in [screenshots](/screenshots).

## Development Status:

This bot is considered to be feature-complete. There may be some small fixes and
improvements, but for the most - bot is already done and ready for daily usage

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

### Basic:

- Open launcher.sh in your text editor of choice
- Edit 'NOTASHARK_DISCORD_KEY' variable to match your bot's discord token
- Run `./launcher.sh`
This will run bot in its default configuration, suitable for most needs.

### Advanced:
- `./run_notashark -h` to get full list of available launch flags
- Manually setup 'NOTASHARK_DISCORD_KEY' environment variable to match your bot's
discord token
- ALTERNATIVELY: pass your discord bot's token as `--token` launch argument
- `./run_notashark` with whatever flags you want

## LICENSE:

[GPLv3](LICENSE)
