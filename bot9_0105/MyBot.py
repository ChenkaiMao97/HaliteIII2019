#!/usr/bin/env python3
# Python 3.6

# Import the Halite SDK, which will let you interact with the game.
import hlt

# This library contains constant values.
from hlt import constants

# This library contains direction metadata to better interface with the game.
from hlt.positionals import Direction, Position

# This library allows you to generate random numbers.
import random

# Logging allows you to save messages for yourself. This is required because the regular STDOUT
#   (print statements) are reserved for the engine-bot communication.
import logging
import numpy as np
from timeit import default_timer as timer


""" <<<Game Begin>>> """

# This game object contains the initial game state.
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.

game_map = game.game_map
me = game.me

#constant control variables:
RETURN_COEFF = 0.83  # above which percentage of MAX_HALITE we return
IGNORE_COEFF = 0.08  # under which percentage of MAX_HALITE we ignore that cell
EXPLORE_AGAIN = 0.25 # under which percentage of MAX_HALITE go back to explore
LOCAL_RANDOM_TO_DESTINATION = 0.3 # coeffienent for transition from local random walk to heading to destination
MAX_SHIP_SEED = 0.5
MAX_ENERGY_POINTS = 10
DISTANCE_TO_BUILD_DROPOFF = 20
MAX_DROPOFF_SEED = 1/32

MAX_SHIP = MAX_SHIP_SEED*game_map.width
MAX_DROPOFF_NUMBER = MAX_DROPOFF_SEED*game_map.width
#gamestages:
if(constants.MAX_TURNS <450):
    FIRST_BUILD_SHIP = 80
    SECOND_MONEY_FOR_PORT = 120
    THIRD_BUILD_PORT = 180
    FOUTRH_STOP_BUILD_PORT = 350
else:
    FIRST_BUILD_SHIP = 100
    SECOND_MONEY_FOR_PORT = 150
    THIRD_BUILD_PORT = 200
    FOUTRH_STOP_BUILD_PORT = 400
ship_status = {}


# start = timer() 
# maxEnergyPos = gamemap.maxEnergyPositions() 
# end = timer() 
# logging.info("time!! ")
# logging.info(end - start)
# 0.002

# maxEnergyPos.sort(key = lambda x: game_map.calculate_distance(me.shipyard.position,Position(x[0],x[1])))
# maxEnergyPos = maxEnergyPos[0:MAX_ENERGY_POINTS]
# logging.info(maxEnergyPos)

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
    maxEnergyPos = game_map.maxEnergyPositions()
    maxEnergyPos = [Position(maxEnergyPos[i][0],maxEnergyPos[i][[1]]) for i in range(len(maxEnergyPos))]
    maxEnergyPos.sort(key = lambda x: game_map.calculate_distance(me.shipyard.position,x))
    maxEnergyPos = maxEnergyPos[0:MAX_ENERGY_POINTS]

    bestDropOffPosList, maxAreaPos, topAverage = game_map.convolveMax()
    maxAreaPos.sort(key = lambda x: game_map.calculate_distance(me.shipyard.position,x))
    logging.info("maxAreaPos")
    logging.info(maxAreaPos)

    # logging.info("maxEnergyPos")
    # logging.info(maxEnergyPos)
    # A command queue holds all the commands you will run this turn. You build this list up and submit it at the
    #   end of the turn.
    command_queue = []
    cantMoveIdList = []
    for ship in me.get_ships():
        # first mark all the ships that can't move:
        if(ship.halite_amount<game_map[ship.position].halite_amount*0.1):
            game_map[ship.position].mark_unsafe(ship)
            command_queue.append(ship.stay_still())
            cantMoveIdList.append(ship.id)

    for ship in me.get_ships():
        if(ship.id in cantMoveIdList):
            continue

        mustMove = True if game_map[ship.position].is_occupied else False

        maxsortedforthisship = sorted(maxAreaPos,key = lambda x: game_map.calculate_distance(ship.position,x))
        
        thisDropOff = me.shipyard
        minDis = game_map.calculate_distance(ship.position,me.shipyard.position)
        for dropOff in me.get_dropoffs():
            newDis = game_map.calculate_distance(ship.position,dropOff.position)
            if newDis < minDis:
                minDis = newDis
                thisDropOff = dropOff

        if ship.id not in ship_status:
            thisRand = random.randint(0,9)
            if thisRand <4:
                ship_status[ship.id] = "local_random_walk"
            elif thisRand<7:
                ship_status[ship.id] = "heading"
                ship.destination = random.choice(maxAreaPos[0:3])
            else:
                ship_status[ship.id] = "heading"
                ship.destination = random.choice(maxEnergyPos[0:3])
        if ship_status[ship.id] == "finalReturning":
            move = game_map.naive_navigate(ship, thisDropOff.position,finalReturn = True)
            if move == "buildDropoff":
                command_queue.append(ship.stay_still())
                continue
            game_map[ship.position.directional_offset(move)].mark_unsafe(ship)
            command_queue.append(ship.move(move))
            continue
        elif ship_status[ship.id] == "returning":
            if ship.position == ship.destination: 
                ship_status[ship.id] = "heading"
                thisRand = random.randint(0,9)
                if thisRand<7:
                    ship.destination = random.choice(maxAreaPos[0:2])
                else:
                    ship.destination = random.choice(maxEnergyPos[0:2])

            elif ship.halite_amount < constants.MAX_HALITE*EXPLORE_AGAIN:
                ship_status[ship.id] = "heading"
                ship.destination = maxsortedforthisship[0]
            else:
                move = game_map.naive_navigate(ship, ship.destination)
                if move == "buildDropoff":
                    if me.halite_amount > constants.DROPOFF_COST+constants.SHIP_COST and not game_map[ship.position].has_structure and minDis>12:
                        command_queue.append(ship.make_dropoff())
                        continue
                    else:
                        command_queue.append(ship.stay_still())
                        continue
                game_map[ship.position.directional_offset(move)].mark_unsafe(ship)
                command_queue.append(ship.move(move))
                continue
        elif ship_status[ship.id] == "local_random_max_walk":
            localSum = 0
            localMax = 0
            localMaxPos = None
            for i in range(7):
                for j in range(7):
                    newAmount = game_map[ship.position+Position(i-3,j-3)].halite_amount
                    if newAmount > localMax:
                        localMax = newAmount
                        localMaxPos = ship.position+Position(i-3,j-3)
                    localSum += newAmount
            if localSum < topAverage*LOCAL_RANDOM_TO_DESTINATION:
                logging.info("backToHeading!!")
                ship_status[ship.id] = "heading"
                ship.destination = maxsortedforthisship[0]
            elif ship.halite_amount >= (constants.MAX_HALITE*RETURN_COEFF if game.turn_number<300 else constants.MAX_HALITE*(RETURN_COEFF-0.002*(game.turn_number-300))):
                ship_status[ship.id] = "returning"
                ship.destination = thisDropOff.position
            else:
                #local_random_walk:
                ship.destination = localMaxPos
                if not mustMove and game_map[ship.position].halite_amount >= constants.MAX_HALITE*IGNORE_COEFF and not ship.is_full:
                    #choose to stay
                    game_map[ship.position].mark_unsafe(ship)
                    command_queue.append(ship.stay_still())
                    continue
                else:
                    move = game_map.naive_navigate(ship, ship.destination,maxHalite = True)
                    if move == "buildDropoff":
                        if me.halite_amount > constants.DROPOFF_COST+constants.SHIP_COST and not game_map[ship.position].has_structure and minDis>12:
                            command_queue.append(ship.make_dropoff())
                            continue
                        else:
                            command_queue.append(ship.stay_still())
                            continue
                    game_map[ship.position.directional_offset(move)].mark_unsafe(ship)
                    command_queue.append(ship.move(move))
                    continue
        # then status is heading
        elif ship.halite_amount >= (constants.MAX_HALITE*RETURN_COEFF if game.turn_number<300 else constants.MAX_HALITE*(RETURN_COEFF-0.002*(game.turn_number-300))):
            ship_status[ship.id] = "returning"
            ship.destination = thisDropOff.position
        elif game_map.calculate_distance(ship.position,thisDropOff.position)>(constants.MAX_TURNS-game.turn_number)-15:
            ship_status[ship.id] = "finalReturning"
            move = game_map.naive_navigate(ship, thisDropOff.position,finalReturn = True)
            if(move == "buildDropoff" and me.halite_amount > constants.DROPOFF_COST+constants.SHIP_COST and not game_map[ship.position].has_structure):
                    command_queue.append(ship.make_dropoff())
                    continue
            game_map[ship.position.directional_offset(move)].mark_unsafe(ship)
            command_queue.append(ship.move(move))
            continue
        
        # if it goes here, then it means the ship has a destination, hasn't made a move yet, aslo it can move

        if not mustMove and game_map[ship.position].halite_amount >= constants.MAX_HALITE*IGNORE_COEFF and not ship.is_full:
            #choose to stay
            game_map[ship.position].mark_unsafe(ship)
            command_queue.append(ship.stay_still())
        else:
            # choose to actually move, only if can't move then stay             
            moveChoice = None
            if ship.toBuildDropoff:
                if(len(me.get_dropoffs()) >= MAX_DROPOFF_NUMBER) or ship.destination not in bestDropOffPosList:
                    ship.toBuildDropoff = False
                    ship.destination = maxsortedforthisship[0]
                elif game_map[ship.destination].structure is not None:
                    ship.toBuildDropoff = False
                    ship.destination = maxsortedforthisship[0]
                elif ship.position == ship.destination and me.halite_amount>(constants.DROPOFF_COST-game_map[ship.position].halite_amount):
                    command_queue.append(ship.make_dropoff())
                    game_map.dropoffPosList.append(ship.position)
                    continue
                elif ship.position == ship.destination:
                    game_map[ship.position].mark_unsafe(ship)
                    command_queue.append(ship.stay_still())
                    continue
                else:
                    pass # heading to dropoff position
            elif(game.turn_number>THIRD_BUILD_PORT and game.turn_number<FOUTRH_STOP_BUILD_PORT and len(me.get_dropoffs()) < MAX_DROPOFF_NUMBER and min([game_map.calculate_distance(ship.position,bestDropOffPosList[i]) for i in range(len(bestDropOffPosList))])< DISTANCE_TO_BUILD_DROPOFF):
                disList = [game_map.calculate_distance(ship.position,bestDropOffPosList[i]) for i in range(len(bestDropOffPosList))]
                minIndex = disList.index(min(disList))
                ship.destination = bestDropOffPosList[minIndex]
                ship_status[ship.id] = "heading"
                ship.toBuildDropoff = True

            if ship.destination is None:
                ship.destination = maxsortedforthisship[0]

            moveChoice = game_map.naive_navigate(ship, ship.destination,maxHalite = True)                
            if moveChoice == "buildDropoff":
                if me.halite_amount > constants.DROPOFF_COST+constants.SHIP_COST and not game_map[ship.position].has_structure and minDis>12:
                    command_queue.append(ship.make_dropoff())
                    continue
                else:
                    command_queue.append(ship.stay_still())
                    continue
            
            if not ship.toBuildDropoff and game_map.calculate_distance(ship.position, ship.destination)<=3:
                ship_status[ship.id] = "local_random_max_walk"
                logging.info("local_random_max_walk!!")
            game_map[ship.position.directional_offset(moveChoice)].mark_unsafe(ship)
            command_queue.append(ship.move(moveChoice))

    # spawn ships and ports depends on different stages of the game:
    if game.turn_number <= FIRST_BUILD_SHIP:
        if len(me.get_ships())<MAX_SHIP and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
            command_queue.append(me.shipyard.spawn())
    elif game.turn_number<= SECOND_MONEY_FOR_PORT:
        if len(me.get_ships())<MAX_SHIP and me.halite_amount >= constants.DROPOFF_COST+constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
            command_queue.append(me.shipyard.spawn())
    elif game.turn_number <= THIRD_BUILD_PORT:
        if len(me.get_ships())<MAX_SHIP and me.halite_amount >= constants.DROPOFF_COST and not game_map[me.shipyard].is_occupied:
            command_queue.append(me.shipyard.spawn())
    else:
        if game.turn_number <= constants.MAX_TURNS-100 and len(me.get_ships())<MAX_SHIP*0.5 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
            command_queue.append(me.shipyard.spawn())
    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)

