import logging
import random
from typing import List
from game import Position, Terrain 
from game import CASTLE, CONQUER, HARVEST, MINE, FORT, FARM, LAND
import unittest

ALL_ACTIONS = [CASTLE, CONQUER, FARM, FORT]

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
    # logging.info(adjacents)
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

class BotLogic:
    def turn(self, map_size, my_resources, world):
        mine = get_my_tiles(world)
        adjacent = get_adj_tiles(world, mine)
        possible_actions = ALL_ACTIONS.copy()
        action_type = random.choice(possible_actions)
        
        return self.make_move(
            action_type, possible_actions,
            mine, adjacent, world, my_resources
            )
            

    def is_possible(
        self, action, mine, adjacents, world, resources
    ):
        empty_land = [
            t for t in mine if t[1].structure == LAND 
        ]
        if action in (FARM, FORT, CASTLE) and not empty_land:
            return False
        match(action):
            case 'farm':
                if resources >= 5:
                    return empty_land
            case 'fort':
                if resources >= 25:
                    return empty_land
            case 'castle':
                if resources >= 75:
                    return empty_land
            case 'conquer':
                return get_conquerable(adjacents, resources)
                
    def make_move(
        self, action, possible_actions: List,
        mine, adjacents, world, resources
        ):
        if not possible_actions or action == HARVEST:
            return HARVEST, None
        if positions := self.is_possible(
            action, mine, adjacents, world, resources
            ):
            return action, random.choice(positions)[0]
        else:
            return self.make_move(
                random.choice(possible_actions), possible_actions.remove(action),
                mine, adjacents, world, resources
            )
        raise Exception


class TestAuxMethods(unittest.TestCase):
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
        other = "Terminal Khan"
        world = {
                Position(1,1): Terrain(CASTLE, MINE),
                Position(0,0): Terrain(CASTLE, other),
                Position(0,1): Terrain(CASTLE, other),
                Position(1,0): Terrain(CASTLE, other)
        }
        self.assertEqual(get_my_tiles(world),
                         [
                             (Position(1,1), Terrain(CASTLE, MINE)),
                         ])

    def test_adjs(self):
        other = "Terminal Khan"
        world = {
                Position(1,1): Terrain(CASTLE, MINE),
                Position(0,0): Terrain(CASTLE, other),
                Position(0,1): Terrain(CASTLE, other),
                Position(1,0): Terrain(CASTLE, other)
        }
        self.assertEqual(set(get_adj_tiles(world, get_my_tiles(world))),
                         set([
                            (Position(0,1), Terrain(CASTLE, other)),
                            (Position(1,0), Terrain(CASTLE, other))
                         ]))
        
