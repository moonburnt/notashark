*100% not a shark-v2 clone*

**Description:**

Well, its a single-server (meaning that its not designed to be invited to multiple discords at once) discord bot for King Arthur's Gold, written in python and configurable with environment variables (or just via attached .sh file). Thus far it can only list (and autoupdate each 30 seconds) kag server's statistics; also send messages regarding people who join and leave your discord server (in channels you've set up for these purposes). But I may add some stuff in future (dont wanna make it complicated tho)

![Statistics message example](https://files.catbox.moe/uqnrzx.png?raw=true)

**Dependencies:**

- python 3.8 (may work on previous versions, but thats the one running on my machine)
- python-requests
- [discord.py](https://github.com/Rapptz/discord.py)
- [pykagapi](https://github.com/moonburnt/pykagapi)

**Usage:**

- Open bootin_up.sh in your text editor of choice
- Edit its content accordingly (set up DISCORD_KEY, STATISTICS_CHANNEL_ID and LOG_CHANNEL_ID)
- Run `./bootin_up.sh`

**LICENSE**:

[WTFPL](LICENSE)
