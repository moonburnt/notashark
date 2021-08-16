#!/bin/bash
### example notashark launch script

## Vars
# Change value of this to be your bot's token in quotes:
NOTASHARK_DISCORD_KEY=""

# Dont touch anything below, unless you know what you are doing
botname="notashark"
botpath="."
scriptname=$(basename "$0")

if [ -z "$NOTASHARK_DISCORD_KEY" ]; then
    echo "NOTASHARK_DISCORD_KEY isnt set. Please edit the value of NOTASHARK_DISCORD_KEY inside $scriptname and try again"
    exit 1
fi
export NOTASHARK_DISCORD_KEY

chmod +x "$botpath/$botname"
exec python "$botpath/$botname" --show-logs
