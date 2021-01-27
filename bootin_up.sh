#!/bin/bash
### notashark launcher script

## Vars
# Change value of this to be your bot's token in quotes:
DISCORD_KEY=""

# Change this to int value of seconds between update. Keep in mind that everything below 10 secs will be forcefully set to 10 seconds, as there is no point to fetch info any faster - you will just flood api with requests
STATISTICS_UPDATE_TIME=""

# This determines logging level of script itself (dont confuse with log channel) - e.g which info will be displayed in terminal during notashark's uptime
# Available values are the following:
# "Debug". Display literally everything. For the most cases - overkill
# "Info". Shows general usage info and errors, if they occur. Set by default
# "Warning". Only display warnings and errors, nothing else. Use if you dont wanna flood your output
SCRIPT_LOGGING_LEVEL="Info"

# Stuff below reflects the name of bot script and path to it, aswell as the name of bootstrapper. By default, you dont need to change anything there
botname="run_notashark"
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

if [ -z "$STATISTICS_UPDATE_TIME" ]; then
    echo "STATISTICS_UPDATE_TIME isnt set, will use defaults (30)"
fi

if [ -z "$SCRIPT_LOGGING_LEVEL" ]; then
    echo "SCRIPT_LOGGING_LEVEL isnt set, will use defaults (1)"
fi

echo "Launching $botname..."
export DISCORD_KEY
export STATISTICS_UPDATE_TIME
export SCRIPT_LOGGING_LEVEL

chmod +x "$botpath/$botname"
"$botpath/$botname"
