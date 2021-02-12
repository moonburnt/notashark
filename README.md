*This started as shark-v2 clone*

# notashark

## Description:

Well, its a small discord bot for King Arthur's Gold, written in python + discord.py. Thus far it doesnt have much features, but I may update it with new stuff... eventually

![Statistics message example](https://files.catbox.moe/uqnrzx.png?raw=true)

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
