import logging
import random
import unittest
from collections import defaultdict
from unittest.mock import Mock, patch
from typing import List
from game import Position, Terrain 
from game import CASTLE, CONQUER, HARVEST, MINE, FORT, FARM, LAND

logging.basicConfig(
    filename="rndmdebug", level=logging.DEBUG,
    filemode="w"
)

ALL_ACTIONS = [CASTLE, CONQUER, FARM, FORT]
STRUCTURES = {CASTLE, FARM, FORT}

def adj(p1: Position, p2: Position):
    x1, y1 = p1
    x2, y2 = p2
    return abs(x1 - x2) + abs(y1 - y2) <= 1

def is_adj_tile(t1, t2):
    return adj(t1[0], t2[0])

def get_my_tiles(world):
    return [p for p in world.items() if p[1].owner == 'mine']

def get_adj_tiles(world, tiles):
    return [a for a in world.items() if
        a[1].owner != 'mine' and
        any(is_adj_tile(a, t) for t in tiles)
    ]

def get_conquerable(adjacents, resources):
    return [
        t for t in adjacents if can_conquer(t, resources)
    ]
    

def can_conquer(tile, resources):
    match(tile[1].structure):
        case 'castle':
            return resources >= 100
        case 'fort':
            return resources >= 50
        case 'fort':
            return resources >= 2
        case 'land':
            return resources >= 1

class World:
    def __init__(self, world, resources):
        self.resources = resources
        self.mine = get_my_tiles(world)
        self.adjacent = get_adj_tiles(world, self.mine)
        self.conquerable = get_conquerable(self.adjacent, self.resources)
        self.structures = defaultdict(list) 
        for t in self.mine:
            self.structures[t[1].structure].append(t)

    def possible_positions(
        self, action 
    ):
        empty_land = self.structures[LAND]
        if action in STRUCTURES and not empty_land:
            return False
        match(action):
            case 'farm':
                if self.resources >= 5:
                    return empty_land
            case 'fort':
                if self.resources >= 25:
                    return empty_land
            case 'castle':
                if (self.resources >= 75 and
                    len(self.mine) > (len(self.structures[CASTLE]) * 50)):
                    return empty_land
            case 'conquer':
                return self.conquerable
        

class BotLogic:
    def turn(self, map_size, my_resources, world):
        world = World(world, my_resources)
        possible_actions = ALL_ACTIONS.copy()
        return self.make_move(
            possible_actions, world
            )

    def choose_action(self, possible_actions):
        return random.choice(possible_actions)

    def choose_position(self, tiles):
        return random.choice(tiles)[0]
    
    def make_move(
        self, possible_actions: List, world: World):
        if not possible_actions:
            return HARVEST, None
        action = self.choose_action(possible_actions)
        if action == HARVEST:
            return HARVEST, None
        if tiles := world.possible_positions(action):
            return action, self.choose_position(tiles)
        else:
            possible_actions.remove(action)
            return self.make_move(possible_actions, world)
        raise Exception


class TestBot(unittest.TestCase):
    other = "Terminal Khan"
    khan_world = {
            Position(1,1): Terrain(CASTLE, MINE),
            Position(0,0): Terrain(CASTLE, other),
            Position(0,1): Terrain(CASTLE, other),
            Position(1,0): Terrain(CASTLE, other)
        }

    farm_vil = {
            Position(1,1): Terrain(CASTLE, MINE),
            Position(0,0): Terrain(LAND, MINE),
            Position(0,1): Terrain(LAND, MINE),
            Position(1,0): Terrain(LAND, MINE)
        }
    
    def test_adj(self):
        self.assertTrue(adj(Position(0,0), Position(0,1)))
        self.assertFalse(adj(Position(0,0), Position(1,1)))
        self.assertTrue(adj(Position(0,0), Position(1,0)))
        
    def test_adj_tile(self):
        self.assertTrue(
            is_adj_tile(
                (Position(0,1), Terrain(CASTLE, MINE)),
                (Position(0,0), Terrain(CASTLE, MINE))
            )
        )

    def test_my_tiles(self):
        self.assertEqual(get_my_tiles(self.khan_world),
                         [
                             (Position(1,1), Terrain(CASTLE, MINE)),
                         ])

    def test_adjs(self):
        world = self.khan_world
        self.assertEqual(set(get_adj_tiles(world, get_my_tiles(world))),
                         set([
                            (Position(0,1), Terrain(CASTLE, self.other)),
                            (Position(1,0), Terrain(CASTLE, self.other))
                         ]))

    @patch.object(BotLogic, 'choose_position', lambda x, y: Position(1, 0))
    def test_conquer_khan(self):
        actions = [CONQUER, FORT, FARM]
        def choose(who, cares):
            return actions.pop()
        with patch.object(BotLogic, 'choose_action', choose):
            bot = BotLogic()
            self.assertEqual(
                bot.turn((2,2), 100, self.khan_world),
                (CONQUER, Position(1,0))
            )

    def test_farming_Jin(self):
        bot = BotLogic()
        res = bot.turn((2,2), 10, self.farm_vil)
        self.assertEqual(
             res[0], FARM 
        )
        self.assertIn(
            res[1],
            {Position(0,1), Position(1,0)}
        )
            
        
