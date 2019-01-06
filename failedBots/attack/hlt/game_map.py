import queue
import random
import numpy as np
from . import constants
from .entity import Entity, Shipyard, Ship, Dropoff
from .player import Player
from .positionals import Direction, Position
from .common import read_input
import logging

MAX_ENERGY_POINTS = 15

class MapCell:
    """A cell on the game map."""
    def __init__(self, position, halite_amount):
        self.position = position
        self.halite_amount = halite_amount
        self.ship = None
        self.structure = None

    @property
    def is_empty(self):
        """
        :return: Whether this cell has no ships or structures
        """
        return self.ship is None and self.structure is None

    @property
    def is_occupied(self):
        """
        :return: Whether this cell has any ships
        """
        return self.ship is not None

    @property
    def has_structure(self):
        """
        :return: Whether this cell has any structures
        """
        return self.structure is not None

    @property
    def structure_type(self):
        """
        :return: What is the structure type in this cell
        """
        return None if not self.structure else type(self.structure)

    def mark_unsafe(self, ship):
        """
        Mark this cell as unsafe (occupied) for navigation.

        Use in conjunction with GameMap.naive_navigate.
        """
        self.ship = ship

    def __eq__(self, other):
        return self.position == other.position

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return 'MapCell({}, halite={})'.format(self.position, self.halite_amount)


class GameMap:
    """
    The game map.

    Can be indexed by a position, or by a contained entity.
    Coordinates start at 0. Coordinates are normalized for you
    """
    def __init__(self, cells, width, height,game):
        self.totalEnergy = 0
        self.topAverage = 0
        self.width = width
        self.height = height
        self._cells = cells
        self.game = game
        self.energyMap = np.zeros((self.width,self.height))
        self.dropoffPosList = [game.me.shipyard.position]
        self.myStartPositions = {}
        self.aveShipCargo = 0
        

    def __getitem__(self, location):
        """
        Getter for position object or entity objects within the game map
        :param location: the position or entity to access in this map
        :return: the contents housing that cell or entity
        """
        if isinstance(location, Position):
            location = self.normalize(location)
            return self._cells[location.y][location.x]
        elif isinstance(location, Entity):
            return self._cells[location.position.y][location.position.x]
        return None

    def opponentNumber(self,pos):
        posNeighbors = []
        posNeighbors.append(pos.directional_offset(Direction.North))
        posNeighbors.append(pos.directional_offset(Direction.South))
        posNeighbors.append(pos.directional_offset(Direction.East))
        posNeighbors.append(pos.directional_offset(Direction.West))
        oppoNumber = 0
        for item in posNeighbors:
            if(self[item].is_occupied and self[item].ship.owner != self.game.me.id):
                oppoNumber += 1
        return oppoNumber

    def oppoCargo(self,pos):
        posNeighbors = [pos]
        posNeighbors.append(pos.directional_offset(Direction.North))
        posNeighbors.append(pos.directional_offset(Direction.South))
        posNeighbors.append(pos.directional_offset(Direction.East))
        posNeighbors.append(pos.directional_offset(Direction.West))
        maxOppoCargo = 0
        for item in posNeighbors:
            if(self[item].is_occupied and self[item].ship.owner != self.game.me.id)\
                and self[item].ship.halite_amount > maxOppoCargo:
                maxOppoCargo = self[item].ship.halite_amount
        return maxOppoCargo
    
    def maxEnergyPositions(self, n = MAX_ENERGY_POINTS):
        positionList = []
        energyMap = self.energyMap.copy()
        for i in range(n):
            maxList = list(np.flip(np.array(np.where(energyMap == energyMap.max())).T,1))
            # logging.info("max: ")
            # logging.info(maxList)
            positionList += maxList
            for pos in maxList:
                energyMap[pos[1]][pos[0]] = 0
        return positionList

    def convolveMax(self,kernelSize = 8, padding = 0, stride = 4):
        # energyMap = self.energyMap.copy()
        newWidth = self.width//stride
        newHeight = self.height//stride
        convolvedMap = np.zeros((newWidth,newHeight))
        for i in range(newWidth):
            for j in range(newHeight):
                for iterx in range(kernelSize):
                    for itery in range(kernelSize):
                        convolvedMap[i][j] += self.energyMap[(i*stride+iterx)%self.width,(j*stride+itery)%self.height]
        originalMap = convolvedMap.copy()

        convolvedMaxPos = []
        topAverage = 0
        for i in range(15):
            thisMax = convolvedMap.max()
            maxList = list(np.flip(np.array(np.where(convolvedMap == thisMax)).T,1))
            topAverage += thisMax
            convolvedMaxPos += maxList
            for pos in maxList:
                convolvedMap[pos[1]][pos[0]] = 0

        topAverage = topAverage/15
        self.topAverage = topAverage

        haliteSort1 = [(convolvedMaxPos[i],i) for i in range(len(convolvedMaxPos))]
        
        def calculate_position(a):
            return Position(int(a[0][0]*stride+kernelSize//2),int(a[0][1]*stride+kernelSize//2))


        disSort2 = sorted(haliteSort1,key = lambda x: max([abs(self.width*0.4-self.calculate_distance(calculate_position(x),self.dropoffPosList[i])) for i in range(len(self.dropoffPosList))]))
        average = [(disSort2[i][0],disSort2[i][1]+5*i) for i in range(len(disSort2))]
        average.sort(key = lambda x: x[1])

        while self[calculate_position(average[0])].structure:
            average[0][0][1]+=1

        return [calculate_position(average[i]) for i in range(6)],[calculate_position(average[i]) for i in range(len(average))]

    def calculate_distance(self, source, target):
        """
        Compute the Manhattan distance between two locations.
        Accounts for wrap-around.
        :param source: The source from where to calculate
        :param target: The target to where calculate
        :return: The distance between these items
        """
        source = self.normalize(source)
        target = self.normalize(target)
        resulting_position = abs(source - target)
        return min(resulting_position.x, self.width - resulting_position.x) + \
            min(resulting_position.y, self.height - resulting_position.y)

    def normalize(self, position):
        """
        Normalized the position within the bounds of the toroidal map.
        i.e.: Takes a point which may or may not be within width and
        height bounds, and places it within those bounds considering
        wraparound.
        :param position: A position object.
        :return: A normalized position object fitting within the bounds of the map
        """
        return Position(position.x % self.width, position.y % self.height)

    @staticmethod
    def _get_target_direction(source, target):
        """
        Returns where in the cardinality spectrum the target is from source. e.g.: North, East; South, West; etc.
        NOTE: Ignores toroid
        :param source: The source position
        :param target: The target position
        :return: A tuple containing the target Direction. A tuple item (or both) could be None if within same coords
        """
        return (Direction.South if target.y > source.y else Direction.North if target.y < source.y else None,
                Direction.East if target.x > source.x else Direction.West if target.x < source.x else None)

    def get_unsafe_moves(self, source, destination, extra = True):
        """
        Return the Direction(s) to move closer to the target point, or empty if the points are the same.
        This move mechanic does not account for collisions. The multiple directions are if both directional movements
        are viable.
        :param source: The starting position
        :param destination: The destination towards which you wish to move your object.
        :return: A list of valid (closest) Directions towards your target.
        """
        source = self.normalize(source)
        destination = self.normalize(destination)
        possible_moves = []
        secondary_moves = []
        distance = Position(abs(destination.x-source.x), abs(destination.y-source.y))
        y_cardinality, x_cardinality = self._get_target_direction(source, destination)

        if distance.x != 0:
            possible_moves.append(x_cardinality if distance.x < (self.width / 2)
                                  else Direction.invert(x_cardinality))
        else:
            secondary_moves.append((1,0))
            secondary_moves.append((-1,0))
        if distance.y != 0:
            possible_moves.append(y_cardinality if distance.y < (self.height / 2)
                                  else Direction.invert(y_cardinality))
        else:
            secondary_moves.append((0,1))
            secondary_moves.append((0,-1))
        return possible_moves,secondary_moves

    def naive_navigate(self, ship, destination,maxHalite = False,finalReturn = False,attack_mode = False):
        """
        Returns a singular safe move towards the destination.

        :param ship: The ship to move.
        :param destination: Ending position
        :return: A direction.
        """
        # No need to normalize destination, since get_unsafe_moves
        # does that
        # choices = [(ship.position,Direction.Still)] if not self[target_pos].is_occupied else []
        choices = []
        secondary_choices = []
        invertDirections = []
        invert_choices = []

        attackList = [(self.oppoCargo(ship.position),ship.position,Direction.Still)] if not self[ship.position].is_occupied else []
        
        oppoList =       [(self.opponentNumber(ship.position),ship.position,Direction.Still)] if not self[ship.position].is_occupied else []

        possible_moves,secondary_moves = self.get_unsafe_moves(ship.position, destination)
        
        for direction in possible_moves:
            invertDirections.append(Direction.invert(direction))
            target_pos = ship.position.directional_offset(direction)
            if not self[target_pos].is_occupied or (finalReturn and (target_pos==ship.destination)):
                choices.append((target_pos,direction))
                oppoList.append((self.opponentNumber(target_pos),target_pos,direction))
                attackList.append((self.oppoCargo(target_pos),target_pos,direction))
            elif self[target_pos].ship.owner != ship.owner:
                attackList.append((self.oppoCargo(target_pos),target_pos,direction))
                if self.calculate_distance(target_pos,self.game.players[ship.owner].shipyard.position)<5:
                    choices.append((target_pos,direction))
                    oppoList.append((self.opponentNumber(target_pos),target_pos,direction))


        for direction in secondary_moves:
            target_pos = ship.position.directional_offset(direction)
            if not self[target_pos].is_occupied or (finalReturn and (target_pos==self.game.players[ship.owner].shipyard.position)):
                secondary_choices.append((target_pos,direction))
                oppoList.append((self.opponentNumber(target_pos),target_pos,direction))
                attackList.append((self.oppoCargo(target_pos),target_pos,direction))
            elif self[target_pos].ship.owner != ship.owner:
                attackList.append((self.oppoCargo(target_pos),target_pos,direction))
                if self.calculate_distance(target_pos,self.game.players[ship.owner].shipyard.position)<5:
                    secondary_choices.append((target_pos,direction))
                    oppoList.append((self.opponentNumber(target_pos),target_pos,direction))


        for direction in invertDirections:
            target_pos = ship.position.directional_offset(direction)
            if not self[target_pos].is_occupied or (finalReturn and (target_pos==self.game.players[ship.owner].shipyard.position)):
                invert_choices.append((target_pos,direction))
                oppoList.append((self.opponentNumber(target_pos),target_pos,direction))
                attackList.append((self.oppoCargo(target_pos),target_pos,direction))
            elif self[target_pos].ship.owner != ship.owner:
                attackList.append((self.oppoCargo(target_pos),target_pos,direction))
                if self.calculate_distance(target_pos,self.game.players[ship.owner].shipyard.position)<5:
                    invert_choices.append((target_pos,direction))
                    oppoList.append((self.opponentNumber(target_pos),target_pos,direction))
       
        oppoList.sort(key = lambda x : x[0])
        attackList.sort(key = lambda x: x[0],reverse = True)
        if attack_mode and ship.halite_amount<100 and len(attackList)>0 and attackList[0][0]>500:            
            logging.info("ATTACK!!!")
            self[attackList[0][1]].mark_unsafe(ship)
            return attackList[0][2] 
        if(len(oppoList) == 0):
            pass # TO DO!
        elif(len(oppoList) == 1):
            self[oppoList[0][1]].mark_unsafe(ship)
            return oppoList[0][2]
        elif(oppoList[0][0]<oppoList[1][0]):
            self[oppoList[0][1]].mark_unsafe(ship)
            return oppoList[0][2]
        elif (len(oppoList) >= 3):
            for item in oppoList[2:]:
                if item[0] > oppoList[0][0]:
                    if (item[1],item[2]) in choices:
                        choices.remove((item[1],item[2]))
                    if (item[1],item[2]) in secondary_choices:
                        secondary_choices.remove((item[1],item[2]))
                    if (item[1],item[2]) in invert_choices:
                        invert_choices.remove((item[1],item[2]))
        if(len(choices)>=1):
            costMinChoice = sorted(choices,key = lambda x : self[x[0]].halite_amount,reverse = maxHalite)            
            self[costMinChoice[0][0]].mark_unsafe(ship)
            return costMinChoice[0][1]
        elif not self[ship.position].is_occupied:
            thisRand = random.randint(0,2)
            if(thisRand<=0): # 6/7 chance stay
                self[ship.position].mark_unsafe(ship)
                return Direction.Still
        
        #to this point: no best moves and not choose stay or can't stay
        if len(secondary_choices)>=1:
            randomChoice = random.choice(secondary_choices)
            self[randomChoice[0]].mark_unsafe(ship)
            return randomChoice[1]
        elif not self[ship.position].is_occupied:
            self[ship.position].mark_unsafe(ship)
            return Direction.Still
        elif len(invert_choices)>=1:    #no best choices
            randomChoice = random.choice(invert_choices)
            self[randomChoice[0]].mark_unsafe(ship)
            return randomChoice[1]
        else: #every move will crash: TO DO: trace the moves and change one by one to resolve
            return "buildDropoff"

    @staticmethod
    def _generate(game):
        """
        Creates a map object from the input given by the game engine
        :return: The map object
        """
        map_width, map_height = map(int, read_input().split())
        game_map = [[None for _ in range(map_width)] for _ in range(map_height)]
        for y_position in range(map_height):
            cells = read_input().split()
            for x_position in range(map_width):
                game_map[y_position][x_position] = MapCell(Position(x_position, y_position,
                                                                    normalize=False),
                                                           int(cells[x_position]))
        return GameMap(game_map, map_width, map_height,game)

    def _update(self):
        """
        Updates this map object from the input given by the game engine
        :return: nothing
        """
        # Mark cells as safe for navigation (will re-mark unsafe cells
        # later)
        for y in range(self.height):
            for x in range(self.width):
                self[Position(x, y)].ship = None

        for _ in range(int(read_input())):
            cell_x, cell_y, cell_energy = map(int, read_input().split())
            self[Position(cell_x, cell_y)].halite_amount = cell_energy

        for i in range(self.width):
            for j in range(self.height):
                self.energyMap[i][j] = self[Position(j,i)].halite_amount

