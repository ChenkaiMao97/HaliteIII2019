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

import sys
# print(sys.argv[1])
argDict = {}
for item in sys.argv[1:]:
    theKey,theValue = item.split('=')
    argDict[theKey] = float(theValue)

""" <<<Game Begin>>> """

# This game object contains the initial game state.
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.

game_map = game.game_map
me = game.me

#constant control variables:
# RETURN_COEFF = 0.85  # above which percentage of MAX_HALITE we return
# IGNORE_COEFF = 0.05  # under which percentage of MAX_HALITE we ignore that cell
# EXPLORE_AGAIN = 0.25 # under which percentage of MAX_HALITE go back to explore
# LOCAL_RANDOM_TO_DESTINATION = 0.7 # coeffienent for transition from local random walk to heading to destination
# MAX_SHIP_SEED = 0.4
# MAX_DROP_OFF_SEED = 1/28
# MAX_ENERGY_POINTS = 15
# DISTANCE_TO_BUILD_DROPOFF = 8
# BIGFISH_AMOUNT = 400

# FIRST_BUILD_SHIP = 100
# SECOND_MONEY_FOR_PORT = 120
# THIRD_BUILD_PORT = 180
# FOUTRH_STOP_BUILD_PORT = 320

RETURN_COEFF = argDict["RETURN_COEFF"]  # above which percentage of MAX_HALITE we return
IGNORE_COEFF = argDict["IGNORE_COEFF"]  # under which percentage of MAX_HALITE we ignore that cell
EXPLORE_AGAIN = argDict["EXPLORE_AGAIN"] # under which percentage of MAX_HALITE go back to explore
LOCAL_RANDOM_TO_DESTINATION = argDict["LOCAL_RANDOM_TO_DESTINATION"] # coeffienent for transition from local random walk to heading to destination
MAX_SHIP_SEED = argDict["MAX_SHIP_SEED"]
MAX_DROP_OFF_SEED = argDict["MAX_DROP_OFF_SEED"]
MAX_ENERGY_POINTS = int(argDict["MAX_ENERGY_POINTS"])
DISTANCE_TO_BUILD_DROPOFF = int(argDict["DISTANCE_TO_BUILD_DROPOFF"])
BIGFISH_AMOUNT = int(argDict["BIGFISH_AMOUNT"])

FIRST_BUILD_SHIP = int(argDict["FIRST_BUILD_SHIP"])
SECOND_MONEY_FOR_PORT = int(argDict["SECOND_MONEY_FOR_PORT"])
THIRD_BUILD_PORT = int(argDict["THIRD_BUILD_PORT"])
FOUTRH_STOP_BUILD_PORT = int(argDict["FOUTRH_STOP_BUILD_PORT"])

MAX_DROP_OFF_NUMBER = round(MAX_DROP_OFF_SEED*game_map.width)
MAX_SHIP = round(MAX_SHIP_SEED*game_map.width)
#gamestages:
if(constants.MAX_TURNS >401):
    FIRST_BUILD_SHIP = round(FIRST_BUILD_SHIP*constants.MAX_TURNS/400)
    SECOND_MONEY_FOR_PORT =round(SECOND_MONEY_FOR_PORT*constants.MAX_TURNS/400)
    THIRD_BUILD_PORT = round(THIRD_BUILD_PORT*constants.MAX_TURNS/400)
    FOUTRH_STOP_BUILD_PORT = round(FOUTRH_STOP_BUILD_PORT*constants.MAX_TURNS/400)

ship_status = {}

# game_map._update()
# totalEnergy = np.sum(game_map.energyMap)
# PlayerNumber = game.players()
# energyCoefficient = 

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
logging.info(argDict)
""" <<<Game Loop>>> """
while True:
    # This loop handles each turn of the game. The game object changes every turn, and you refresh that state by
    #   running update_frame().
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map
    maxEnergyPos = game_map.maxEnergyPositions(n = MAX_ENERGY_POINTS)
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

    for ship in me.get_ships():
        maxsortedforthisship = sorted(maxAreaPos,key = lambda x: game_map.calculate_distance(ship.position,x))
        # For each of your ships, move randomly if the ship is on a low halite location or the ship is full.
        #   Else, collect halite.
        
        #find nearest dropoff:
        thisDropOff = me.shipyard
        minDis = game_map.calculate_distance(ship.position,me.shipyard.position)
        for dropOff in me.get_dropoffs():
            newDis = game_map.calculate_distance(ship.position,dropOff.position)
            if newDis < minDis:
                minDis = newDis
                thisDropOff = dropOff

        # find big points/ secondDes:
        if(not ship.toBuildDropoff and ship.secondDes is None):
            for i in range(5):
                for j in range(5):
                    if(game_map[ship.position+Position(i-2,j-2)].halite_amount>BIGFISH_AMOUNT):
                        ship_status[ship.id] = "heading"
                        ship.secondDes = ship.position+Position(i-2,j-2)
            if ship.secondDes is not None:
                move = game_map.naive_navigate(ship, ship.secondDes,maxHalite = True)
                command_queue.append(ship.move(move))
                continue
        elif(not ship.toBuildDropoff and ship.secondDes is not None and ship.secondDes == ship.position):
            ship.secondDes = None
            # if(ship.destination is None and ship_status[ship.id] != "local_random_walk"):
            #     ship_status[ship.id] = "heading"
            #     ship.destination = random.choice(maxsortedforthisship[0:2])



        if ship.id not in ship_status:
            thisRand = random.randint(0,9)
            # if thisRand <3:
            #     ship_status[ship.id] = "local_random_walk"
            if thisRand<7:
                ship_status[ship.id] = "heading"
                ship.destination = random.choice(maxAreaPos[0:2])
            else:
                ship_status[ship.id] = "heading"
                ship.destination = random.choice(maxEnergyPos[0:2])
        elif ship_status[ship.id] == "finalReturning":
            move = game_map.naive_navigate(ship, thisDropOff.position if ship.secondDes is None else ship.secondDes,finalReturn = True)
            command_queue.append(ship.move(move))
            continue
        elif ship_status[ship.id] == "returning":
            if ship.destination != thisDropOff.position:
                ship.destination = thisDropOff.position
            if ship.position == ship.destination: 
                ship_status[ship.id] = "heading"
                # thisRand = random.randint(0,9)
                # if thisRand<7:
                ship.destination = random.choice(maxsortedforthisship[0:2])
                # else:
                #     ship.destination = random.choice(maxEnergyPos[0:2])

            elif ship.halite_amount < constants.MAX_HALITE*EXPLORE_AGAIN:
                ship_status[ship.id] = "heading"
                ship.destination = maxsortedforthisship[0]
            else:
                move = game_map.naive_navigate(ship, ship.destination)
                command_queue.append(ship.move(move))
                continue
        elif not ship.toBuildDropoff and ship.halite_amount >= (constants.MAX_HALITE*RETURN_COEFF if game.turn_number<300 else constants.MAX_HALITE*(RETURN_COEFF-0.003*(game.turn_number-300))):
            ship_status[ship.id] = "returning"
            ship.destination = thisDropOff.position
        elif game_map.calculate_distance(ship.position,thisDropOff.position)>(constants.MAX_TURNS-game.turn_number)-15:
            ship_status[ship.id] = "finalReturning"
        # logging.info("Ship {} has {} halite.".format(ship.id, ship.halite_amount))
        elif ship.halite_amount >= game_map[ship.position].halite_amount*0.1: #able to move
            if game_map[ship.position].halite_amount < constants.MAX_HALITE*IGNORE_COEFF or ship.is_full:
                # choose to actually move                
                moveChoice = None
                if ship.destination is None:
                    ship.destination = maxsortedforthisship[0]
                elif not ship.toBuildDropoff and ship_status[ship.id] != "local_max_walk" and game_map.calculate_distance(ship.position,ship.destination) <= 3:
                    ship.destination = None
                    ship_status[ship.id] = "local_max_walk"
                if ship_status[ship.id] == "local_max_walk":
                    localSum = 0
                    localMaxPos = None
                    localMax = 0
                    for i in range(7):
                        for j in range(7):
                            newHaliteAmount = game_map[ship.position+Position(i-3,j-3)].halite_amount
                            localSum += newHaliteAmount
                            if newHaliteAmount > localMax:
                                localMax = newHaliteAmount
                                localMaxPos = ship.position+Position(i-3,j-3)
                    if localSum < topAverage*LOCAL_RANDOM_TO_DESTINATION:
                        logging.info("backToHeading!!")
                        ship_status[ship.id] = "heading"
                        ship.destination = maxsortedforthisship[0]
                    else:
                        #local_random_walk:
                        ship.destination = localMaxPos
                        moveChoice = game_map.naive_navigate(ship, ship.destination ,maxHalite = True)
                        # if(game.turn_number<FIRST_BUILD_SHIP):
                        #     moveChoice = game_map.outward_navigate(ship,me.shipyard,maxHalite = True)
                        # else:
                        #     moveChoice = game_map.naive_navigate(ship, ship.destination ,maxHalite = True)
                    pass

                elif ship.toBuildDropoff:
                    if(len(me.get_dropoffs()) >= MAX_DROP_OFF_NUMBER) or ship.destination not in bestDropOffPosList:
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
                        command_queue.append(ship.stay_still())
                        continue
                elif(game.turn_number>THIRD_BUILD_PORT and game.turn_number<FOUTRH_STOP_BUILD_PORT and len(me.get_dropoffs()) < MAX_DROP_OFF_NUMBER and min([game_map.calculate_distance(ship.position,bestDropOffPosList[i]) for i in range(len(bestDropOffPosList))])< DISTANCE_TO_BUILD_DROPOFF):
                    disList = [game_map.calculate_distance(ship.position,bestDropOffPosList[i]) for i in range(len(bestDropOffPosList))]
                    minIndex = disList.index(min(disList))
                    ship.destination = bestDropOffPosList[minIndex]
                    ship_status[ship.id] = "heading"
                    ship.toBuildDropoff = True
                
                if moveChoice is None:
                    moveChoice = game_map.naive_navigate(ship, ship.destination ,maxHalite = True)
                    # if(game.turn_number<FIRST_BUILD_SHIP):
                    #     moveChoice = game_map.outward_navigate(ship,me.shipyard,maxHalite = True)
                    # else:
                    #     moveChoice = game_map.naive_navigate(ship, ship.destination ,maxHalite = True)                
                
                # if not ship.toBuildDropoff and ship_status[ship.id] == "heading" and game_map.calculate_distance(ship.position, ship.destination)<=2:
                #     ship.destination = maxsortedforthisship[0]

                game_map[ship.position].ship = None
                game_map[ship.position.directional_offset(moveChoice)].mark_unsafe(ship)
                command_queue.append(ship.move(moveChoice))

            else:
                #choose to stay
                command_queue.append(ship.stay_still())
        else:
            #can only stay
            command_queue.append(ship.stay_still())

        # logging.info("ship:"+str(ship.id))
        # logging.info(ship_status[ship.id])
    # If the game is in the first 200 turns and you have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though - the ships will collide.
    
    # spawn ships and ports depends on different stages of the game:
    if game.turn_number <= FIRST_BUILD_SHIP:
        if len(me.get_ships())<MAX_SHIP and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
            command_queue.append(me.shipyard.spawn())
    elif game.turn_number<= SECOND_MONEY_FOR_PORT:
        if len(me.get_ships())<MAX_SHIP and me.halite_amount >= constants.DROPOFF_COST+constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
            command_queue.append(me.shipyard.spawn())
    elif game.turn_number <= THIRD_BUILD_PORT:
        if len(me.get_ships())<MAX_SHIP and me.halite_amount >= constants.DROPOFF_COST+constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
            command_queue.append(me.shipyard.spawn())
    else:
        if game.turn_number <= constants.MAX_TURNS-100 and len(me.get_ships())<MAX_SHIP*0.5 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
            command_queue.append(me.shipyard.spawn())
    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)

