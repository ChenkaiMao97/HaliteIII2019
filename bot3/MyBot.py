#!/usr/bin/env python3
# Python 3.6

# Import the Halite SDK, which will let you interact with the game.
import hlt

# This library contains constant values.
from hlt import constants

# This library contains direction metadata to better interface with the game.
from hlt.positionals import Direction

# This library allows you to generate random numbers.
import random

# Logging allows you to save messages for yourself. This is required because the regular STDOUT
#   (print statements) are reserved for the engine-bot communication.
import logging

""" <<<Game Begin>>> """

# This game object contains the initial game state.
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.

#constant control variables:
RETURN_COEFF = 0.85  # above which percentage of MAX_HALITE we return
IGNORE_COEFF = 0.12  # under which percentage of MAX_HALITE we ignore that cell

ship_status = {}


# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("maomao's Python Bot")

# Now that your bot is initialized, save a message to yourself in the log file with some important information.
#   Here, you log here your id, which you can always fetch from the game object by using my_id.
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

""" <<<Game Loop>>> """

while True:
    # This loop handles each turn of the game. The game object changes every turn, and you refresh that state by
    #   running update_frame().
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map

    # A command queue holds all the commands you will run this turn. You build this list up and submit it at the
    #   end of the turn.
    command_queue = []

    for ship in me.get_ships():
        # For each of your ships, move randomly if the ship is on a low halite location or the ship is full.
        #   Else, collect halite.
        
        if ship.id not in ship_status:
            ship_status[ship.id] = "exploring"
        
        if ship_status[ship.id] == "returning":
            if ship.position == me.shipyard.position:
                ship_status[ship.id] = "exploring"
            else:
                move = game_map.naive_navigate(ship, me.shipyard.position)
                command_queue.append(ship.move(move))
                continue
        elif ship.halite_amount >= constants.MAX_HALITE*RETURN_COEFF:
            ship_status[ship.id] = "returning"
        
        # logging.info("Ship {} has {} halite.".format(ship.id, ship.halite_amount))
        elif ship.halite_amount >= game_map[ship.position].halite_amount*0.1: #able to move
            if game_map[ship.position].halite_amount < constants.MAX_HALITE*IGNORE_COEFF or ship.is_full:
                # moving and 
                moveChoice = None
                fourPos = []
                validDir = []
                fourPos.append((ship.position.directional_offset(Direction.East),Direction.East))
                fourPos.append((ship.position.directional_offset(Direction.South),Direction.South))
                fourPos.append((ship.position.directional_offset(Direction.West),Direction.West))
                fourPos.append((ship.position.directional_offset(Direction.North),Direction.North))

                for item in fourPos:
                    if not game_map[item[0]].is_occupied:
                        validDir.append(item[1])
                y_cardinality, x_cardinality = game_map._get_target_direction(me.shipyard.position, ship.position)
                outwardDir = []
                if x_cardinality is not None:
                    outwardDir += [x_cardinality]
                else: 
                    outwardDir += [(1,0),(-1,0)]
                if y_cardinality is not None:
                    outwardDir += [y_cardinality]
                else: 
                    outwardDir += [(0,1),(0,-1)]
                intersection = list(set(outwardDir).intersection(set(validDir)))
                intersection.sort(key = lambda x: -game_map[ship.position.directional_offset(x)].halite_amount)
                if len(intersection)>0:
                    moveChoice = intersection[0] 
                elif len(validDir) == 0: # all occupied
                    moveChoice = Direction.Still
                elif len(validDir) == 1:
                    moveChoice = validDir[0] # no good choice valid
                else:    
                    moveChoice = random.choice(validDir)
                game_map[ship.position.directional_offset(moveChoice)].mark_unsafe(ship)
                game_map[ship.position].ship = None
                command_queue.append(ship.move(moveChoice))
            else:
                command_queue.append(ship.stay_still())
        else:
            command_queue.append(ship.stay_still())

    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
    if game.turn_number <= 200 and len(me.get_ships())<20 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(me.shipyard.spawn())

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)

