#!/bin/bash
### notashark launcher script

## Vars
# Change value of this to be your bot's token in quotes:
DISCORD_KEY=""

# Change it to be the id of channel, you want bot to automatically post statistics into.
# To get channel id, go into discord's settings > appearance > advanced > toggle on "developer mode"
# If you did everything correctly - when you will click on channel's name with rmb, there will be new "Copy ID" entry
STATISTICS_CHANNEL_ID=""

# Change its value to be id of channel, that will be used to greet newcomers and tell if someone has left the server
LOG_CHANNEL_ID=""

# Stuff below reflects the name of bot script and path to it, aswell as the name of bootstrapper. By default, you dont need to change anything there
botname="notashark.py"
botpath="."
scriptname=`basename "$0"`

##-----------------------------------------
## Script (DONT TOUCH THIS, unless you are 100% sure regarding what you are doing!)
#Safety checks, to ensure that you actually provided the key
if [ -z "$DISCORD_KEY" ]; then
    echo "DISCORD_KEY isnt set. Please edit the value of DISCORD_KEY inside $scriptname and try again"
    exit 1
fi

if [ -z "$STATISTICS_CHANNEL_ID" ]; then
    echo "STATISTICS_CHANNEL_ID isnt set. Please edit the value of STATISTICS_CHANNEL_ID inside $scriptname and try again"
    exit 1
fi

if [ -z "$LOG_CHANNEL_ID" ]; then
    echo "LOG_CHANNEL_ID isnt set. Please edit the value of LOG_CHANNEL_ID inside $scriptname and try again"
    exit 1
fi


echo "Launching the $botname into the loop..."
export DISCORD_KEY
export STATISTICS_CHANNEL_ID
export LOG_CHANNEL_ID

#Making bot run on the loop, so it will be brought back up even if some collapse will occur
while true; do
    #python "$botpath/$botname" || exit 1
    python "$botpath/$botname"
done
