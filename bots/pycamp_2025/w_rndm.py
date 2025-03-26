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

AGGRESIVE_LEVEL = 3
AGGRESIVE_SWITCH = 200
DEFENSIVE_LEVEL = 1

ALL_WEIGHTS = {CASTLE :1, CONQUER : 1, FARM: 1, FORT  :1 }
END_WEIGHTS = {CASTLE :25, CONQUER : 50, FARM: 1, FORT:25}
STRUCTURES = {CASTLE, FARM, FORT}

def dst(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return abs(x1 - x2) + abs(y1 - y2)

def adj(p1: Position, p2: Position):
    x1, y1 = p1
    x2, y2 = p2
    return abs(x1 - x2) + abs(y1 - y2) <= 1

def is_adj_tile(t1, t2):
    return adj(t1[0], t2[0])

def get_my_tiles(world):
    mine = []
    enem = []
    for p in world.items():
        if p[1].owner == MINE:
            mine.append(p)
        elif p[1].owner != 'neutral':
            enem.append(p) 
    return mine, enem

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
        case 'farm':
            return resources >= 2
        case 'land':
            return resources >= 1

class World:
    def __init__(self, world, resources):
        self.resources = resources
        self.mine, self.enemy = get_my_tiles(world)
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

    def distance_to_castle(self, tile):
        return min([dst(c[0], tile[0]) for c in
            self.structures[CASTLE]])
    
    def distance_to_enemy_castle(self, tile):
        e = [t for t in self.enemy if t[1].structure == CASTLE]
        return min([dst(c[0], tile[0]) for c in e])

    def get_tax_amount(self):
        return len(self.structures[CASTLE] + self.structures[FARM])
        

class BotLogic:
    def turn(self, map_size, my_resources, world):
        world = World(world, my_resources)
        possible_actions = self.get_actions(world)
        return self.make_move(
            possible_actions, world
            )

    def get_actions(self, world):
        if world.get_tax_amount() > AGGRESIVE_SWITCH:
            return END_WEIGHTS.copy()
        return ALL_WEIGHTS.copy()

    def choose_action(self, possible_actions):
        weights = [w for a, w in possible_actions.items()]
        actions = [a for a, w in possible_actions.items()]
        return random.choices(actions, weights)[0]

    def get_weights_by_positon(self, dists):
        n = len(dists)
        options = [(option, n - i * 3) for i, option in enumerate(dists)]
        options = []
        weights = []
        for i, option in enumerate(dists):
            options.append(option)
            weights.append(n-i)
        return (options, weights)


    def choose_position_for(self, tiles, action, world):
        if action in (STRUCTURES - {CASTLE}):
            dists = sorted([(world.distance_to_castle(t), t) for t in tiles])
            options, weights = self.get_weights_by_positon(dists)
            return random.choices(options, weights)[0][1][0]
        dists = sorted([(world.distance_to_enemy_castle(t), t) for t in tiles])
        options, weights = self.get_weights_by_positon(dists)
        return random.choices(options, weights)[0][1][0]
    
    def make_move(
        self, possible_actions: List, world: World):
        if not possible_actions:
            return HARVEST, None
        action = self.choose_action(possible_actions)
        if action == HARVEST:
            return HARVEST, None
        if tiles := world.possible_positions(action):
            return action, self.choose_position_for(tiles, action, world)
        else:
            possible_actions.pop(action, None)
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
        self.assertEqual(get_my_tiles(self.khan_world)[0],
                         [
                             (Position(1,1), Terrain(CASTLE, MINE)),
                         ])

    def test_adjs(self):
        world = self.khan_world
        self.assertEqual(set(get_adj_tiles(world, get_my_tiles(world)[0])),
                         set([
                            (Position(0,1), Terrain(CASTLE, self.other)),
                            (Position(1,0), Terrain(CASTLE, self.other))
                         ]))

    @patch.object(BotLogic, 'choose_position_for', lambda x, y, z, w: Position(1, 0))
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
            
        
