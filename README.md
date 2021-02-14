*This started as shark-v2 clone*

# notashark

## Description:

Well, its a small discord bot for King Arthur's Gold, written in python + discord.py. Its able to run on multiple discord guilds at once, has self-updating serverlist (and ability to set it up with just one chat command), supports settings autosaving to json and can showcase player's kagstats information. And thats not all! And more to come!

![Self-updating serverlist](https://i.fiery.me/Pjr9r.png?raw=true)

![Player's kagstats info showcase](https://i.fiery.me/xI6mh.png?raw=true)

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
- Manually setup 'NOTASHARK_DISCORD_KEY' environment variable to match your bot's discord token
- `./run_notashark -h` to get full list of available launch flags
- `./run_notashark` with whatever flags you want

## LICENSE:

[GPLv3](LICENSE)
