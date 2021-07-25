#!/bin/bash

program_exists() {
    local ret='0'
    command -v $1 >/dev/null 2>&1 || { local ret='1'; }

    # fail on non-zero return value
    if [ "$ret" -ne 0 ]; then
        return 1
    fi

    return 0
}

program_exists rofi
if ! [ $? = 0 ]; then
   dmenu_run
   exit 0
fi

rofi -show combi -combi-modi window,drun,run 
