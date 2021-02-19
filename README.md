*This started as shark-v2 clone*

# notashark

## Description:

**notashark** -  discord bot for King Arthur's Gold, written in python + pykagapi + discord.py. Its designed to be able to run on multiple discord guilds at once, feature ability to setup some per-guild settings via chat commands (and save them between bot's sessions in simple json file) and be able to display all major information related to the game.

## Screenshots:

### Self-Updating Server List:

![Self-Updating Server List](https://i.fiery.me/oHYFM.png?raw=true)

### KAG Stats Profile Showcase:

![KAG Stats Profile Showcase](https://i.fiery.me/OJ5wK.png?raw=true)

### KAG Stats Leaderboard Showcase:

![KAG Stats Leaderboard Showcase](https://i.fiery.me/QlR52.png?raw=true)

## Dependencies:

- python 3.8 (may work on previous versions)
- discord.py
- requests
- [pykagapi](https://github.com/moonburnt/pykagapi)

## Usage:

### Basic:

- Open launcher.sh in your text editor of choice
- Edit 'NOTASHARK_DISCORD_KEY' variable to match your bot's discord token
- Run `./launcher.sh`
This will run bot in its default configuration, suitable for most needs.

### Advanced:
- `./run_notashark -h` to get full list of available launch flags
- Manually setup 'NOTASHARK_DISCORD_KEY' environment variable to match your bot's discord token
- ALTERNATIVELY: pass your discord bot's token as `--token` launch argument
- `./run_notashark` with whatever flags you want

## LICENSE:

[GPLv3](LICENSE)
