#!/bin/bash
### notashark launcher script

## Vars
# Change value of this to be your bot's token in quotes:
DISCORD_KEY=""

# Change it to be the id of channel, you want bot to automatically post statistics into.
# To get channel id, go into discord's settings > appearance > advanced > toggle on "developer mode"
# If you did everything correctly - when you will click on channel's name with rmb, there will be new "Copy ID" entry
STATISTICS_CHANNEL_ID=""

# Change this to int value of seconds between update. Keep in mind that everything below 10 secs will be forcefully set to 10 seconds, as there is no point to fetch info any faster - you will just flood api with requests
STATISTICS_UPDATE_TIME=""

# Change its value to be id of channel, that will be used to greet newcomers and tell if someone has left the server
LOG_CHANNEL_ID=""

# This determines logging level of script itself (dont confuse with log channel) - e.g which info will be displayed in terminal during notashark's uptime
# Available values are the following:
# "Debug". Display literally everything. For the most cases - overkill
# "Info". Shows general usage info and errors, if they occur. Set by default
# "Warning". Only display warnings and errors, nothing else. Use if you dont wanna flood your output
SCRIPT_LOGGING_LEVEL="Info"

# Stuff below reflects the name of bot script and path to it, aswell as the name of bootstrapper. By default, you dont need to change anything there
botname="notashark.py"
botpath="."
scriptname=$(basename "$0")

################
## Script (DONT TOUCH THIS, unless you are 100% sure regarding what you are doing!)
################
# Safety checks, to ensure that you actually provided envars
if [ -z "$DISCORD_KEY" ]; then
    echo "DISCORD_KEY isnt set. Please edit the value of DISCORD_KEY inside $scriptname and try again"
    exit 1
fi

if [ -z "$STATISTICS_CHANNEL_ID" ]; then
    echo "STATISTICS_CHANNEL_ID isnt set, some features will be unavailable"
fi

if [ -z "$LOG_CHANNEL_ID" ]; then
    echo "LOG_CHANNEL_ID isnt set, some features will be unavailable"
fi

if [ -z "$STATISTICS_UPDATE_TIME" ]; then
    echo "STATISTICS_UPDATE_TIME isnt set, will use defaults (30)"
fi

if [ -z "$SCRIPT_LOGGING_LEVEL" ]; then
    echo "SCRIPT_LOGGING_LEVEL isnt set, will use defaults (1)"
fi

echo "Launching $botname into the loop..."
export DISCORD_KEY
export STATISTICS_CHANNEL_ID
export LOG_CHANNEL_ID
export STATISTICS_UPDATE_TIME
export SCRIPT_LOGGING_LEVEL

# Making bot run on the loop, so it will be brought back up even if some collapse will occur
while true; do
    #python "$botpath/$botname" || exit 1
    python "$botpath/$botname"
done
