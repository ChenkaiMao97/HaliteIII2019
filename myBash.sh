#!/bin/bash
./halite  --replay-directory replays/ -vvv --width 40 --height 40 \
	"python3 MyBot.py $1"  \
	"python3 MyBot.py $2"