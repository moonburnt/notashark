*100% not a shark bot clone, definitely didnt take few hours to write*

**Description:**

Well, its a single-server (meaning that its not designed to be invited to multiple discords at once) discord bot for King Arthur's Gold, written in python and configurable with environment variables (or just attached .sh file). Thus far it only lists (and automatically updates each 30 seconds) active servers in channel you will tell it to use for this case and log info regarding who s joined and left your server. But I may add some stuff in future (dont wanna make it complicated tho)

![Statistics message example](https://files.catbox.moe/ojcvax.png?raw=true)

**Dependencies:**

- python 3.8 (may work on previous versions, that just the one that runs on my machine rn)
- python-requests
- [discord.py](https://github.com/Rapptz/discord.py)
- [pykagapi](https://github.com/moonburnt/pykagapi)

**Usage:**

- Open the bootin_up.sh
- Edit its content accordingly (set up DISCORD_KEY, STATISTICS_CHANNEL_ID and LOG_CHANNEL_ID)
- Run `./bootin_up.sh`

**LICENSE**:

[WTFPL](LICENSE)
