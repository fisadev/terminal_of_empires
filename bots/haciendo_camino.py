import logging
import random
from collections import defaultdict
from dataclasses import dataclass

from game import (
    FORT,
    LAND,
    FARM,
    CASTLE,
    MINE,
    CONQUER,
    HARVEST,
    STRUCTURE_COST,
    CONQUER_COSTS,
    TILES_PER_CASTLE_LIMIT
)

def random_choice_from_set(my_set):
    return random.choice(list(my_set))


def distance(p1, p2):
    """
    Manhattan distance
    """
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def is_adjacent(position1, position2):
    """
    Return True if the two positions are adjacent, False otherwise.
    """
    x1, y1 = position1
    x2, y2 = position2

    return abs(x1 - x2) + abs(y1 - y2) <= 1


def adjacents(position, map_size):
    x, y = position
    adjacents = set()
    if x > 0:
        adjacents.add((x-1, y))
    if x < map_size[0]-1:
        adjacents.add((x+1, y))
    if y > 0:
        adjacents.add((x, y-1))
    if y < map_size[1]-1:
        adjacents.add((x, y+1))
    return adjacents


@dataclass
class Insights:
    enemies: set
    tiles_by_type_and_owner: dict
    forts_and_castles: set
    my_tiles: set
    borders: set
    protected_terrain: set
    unprotected_terrain: set
    where_to_fort: dict
    useful_to_expand: set
    where_to_farm: set
    where_to_expand: dict


class Strategy:
    def __init__(self, insights: Insights, my_resources: int):
        self.insights = insights
        self.my_resources = my_resources

    def harvest(self):
        return HARVEST, None

    def build_castle(self):
        my_castles = len(self.insights.tiles_by_type_and_owner[CASTLE][MINE])
        my_tiles = len(self.insights.my_tiles)

        size_enough = my_tiles / my_castles + 1 >= TILES_PER_CASTLE_LIMIT
        money_enough = self.my_resources >= STRUCTURE_COST[CASTLE]

        if size_enough and money_enough:
            # replace a random fort, land or farm
            my_forts = self.insights.tiles_by_type_and_owner[FORT][MINE]
            my_lands = self.insights.tiles_by_type_and_owner[LAND][MINE]
            my_farms = self.insights.tiles_by_type_and_owner[FARM][MINE]

            if my_forts:
                return CASTLE, random_choice_from_set(my_forts)
            elif my_lands:
                return CASTLE, random_choice_from_set(my_lands)
            elif my_farms:
                return CASTLE, random_choice_from_set(my_farms)

        return None

    def decide_to_fortify(self):
        if self.my_resources < STRUCTURE_COST[FORT]:
            return False

        if not self.insights.unprotected_terrain:
            return False

        max_enemy_forts = max(
            len(self.insights.tiles_by_type_and_owner[FORT][enemy])
            for enemy in self.insights.enemies
        )
        my_forts = len(self.insights.tiles_by_type_and_owner[FORT][MINE])

        # fortify if someone has more forts than me or bc 20% random
        if my_forts < max_enemy_forts or random.random() > 0.2:
            return True

        return False


    def fortify(self):
        fortification_max_benefit = max(self.insights.where_to_fort)

        positions_to_fortify = self.insights.where_to_fort[fortification_max_benefit]
        position = random_choice_from_set(positions_to_fortify)

        return FORT, position

    def decide_to_farm(self):
        if self.my_resources < STRUCTURE_COST[FARM]:
            return False

        if not self.insights.tiles_by_type_and_owner[LAND][MINE]:
            return False

        max_enemy_farms = max(
            len(self.insights.tiles_by_type_and_owner[FARM][enemy])
            for enemy in self.insights.enemies
        )
        my_farms = len(self.insights.tiles_by_type_and_owner[FARM][MINE])

        # build farms if someone has more farms than me or bc 20% random
        if my_farms < max_enemy_farms or random.random() <= 0.2:
            return True

        return False

    def farm(self):

        if self.insights.where_to_farm:
            position_to_farm = random_choice_from_set(self.insights.where_to_farm)
        else:
            all_my_lands = self.insights.tiles_by_type_and_owner[LAND][MINE]
            position_to_farm = random_choice_from_set(all_my_lands)

        return FARM, position_to_farm

    def decide_to_conquer(self):
        can_afford = any(cost for cost in self.insights.where_to_expand.keys() if cost <= self.my_resources)
        costs = [cost for cost in self.insights.where_to_expand.keys()]
        resources = self.my_resources

        if can_afford and random.random() <= 0.8:
            return True

        return False

    def conquer(self):
        max_affordable_tile = max(cost for cost in self.insights.where_to_expand.keys() if cost <= self.my_resources)

        position_to_conquer = random_choice_from_set(self.insights.where_to_expand[max_affordable_tile])

        return CONQUER, position_to_conquer

    def select_action(self):
        if not self.my_resources:
            return self.harvest()

        build_castle = self.build_castle()
        if build_castle:
            return build_castle

        if self.decide_to_fortify():
            return self.fortify()

        if self.decide_to_farm():
            return self.farm()

        if self.decide_to_conquer():
            return self.conquer()

        return self.harvest()


class BotLogic:

    @staticmethod
    def _get_enemies_and_tiles_by_type_and_owner(world):
        enemies = set()
        tiles_by_type_and_owner = defaultdict(lambda: defaultdict(set))
        for position, terrain in world.items():
            tiles_by_type_and_owner[terrain.structure][terrain.owner].add(position)
            enemies.add(terrain.owner)
        return enemies, tiles_by_type_and_owner

    @staticmethod
    def _get_my_tiles(tiles_by_type_and_owner):
        my_tiles = set()
        for structure, owners in tiles_by_type_and_owner.items():
            for owner, positions in owners.items():
                if owner == MINE:
                    my_tiles = my_tiles.union(positions)

        return my_tiles

    @staticmethod
    def _get_borders_protected_and_uprotected_tiles(my_tiles, forts_and_castles, map_size):
        borders, protected, unprotected = set(), set(), set()
        for tile in my_tiles:
            adjacent_positions = adjacents(tile, map_size)

            if any(adj not in my_tiles for adj in adjacent_positions):
                borders.add(tile)

            # protected terrain: is a fort or castle or is adjacent to one of them
            if tile in forts_and_castles:
                protected.add(tile)
            elif any(adj in forts_and_castles for adj in adjacent_positions):
                protected.add(tile)
            else:
                unprotected.add(tile)

        return borders, protected, unprotected

    @staticmethod
    def _get_where_to_fort(unprotected_terrain, map_size):
        """
        where to fort: unprotected positions with unprotected adjacent land
        """

        where_to_fort = defaultdict(set) # {num_of_new_fortified_lands: {position,}}
        for tile in unprotected_terrain:
            adjacent_positions = adjacents(tile, map_size)

            new_protected_terrain_with_fort = [adj in unprotected_terrain for adj in adjacent_positions].count(True)
            new_protected_terrain_with_fort += 1 # to count the position where to build

            where_to_fort[new_protected_terrain_with_fort].add(tile)

        return where_to_fort

    @staticmethod
    def _get_useful_to_expand(forts_and_castles, my_tiles, map_size):
        # useful to expand: tiles that will be protected as soon as conquered
        useful_to_expand = set()

        for position in forts_and_castles:
            adjacent_positions = adjacents(position, map_size)
            adjacent_not_mine = adjacent_positions - my_tiles

            useful_to_expand = useful_to_expand.union(adjacent_not_mine)

        return useful_to_expand

    @staticmethod
    def _get_where_to_plant_a_farm(tiles_by_type_and_owner, protected_terrain):
        """
        where to plant a farm: in protected land
        """
        where_to_farm = set()
        for position in tiles_by_type_and_owner[LAND][MINE]:
            if position in protected_terrain:
                where_to_farm.add(position)

        return where_to_farm

    @staticmethod
    def _get_conquer_cost(tile, world, tiles_by_type_and_owner, map_size):
        oponent = world[tuple(tile)].owner
        structure = world[tuple(tile)].structure

        oponent_castles_and_forts = tiles_by_type_and_owner[CASTLE][oponent].union(tiles_by_type_and_owner[FORT][oponent])

        adjacent_positions = adjacents(tile, map_size)

        cost = CONQUER_COSTS[structure]

        if isinstance(cost, tuple):
            undefended_cost, defended_cost = cost

            is_defended = any(adj in oponent_castles_and_forts for adj in adjacent_positions)

            if is_defended:
                cost = defended_cost
            else:
                cost = undefended_cost

        return cost


    def _get_where_to_expand(self, my_tiles, world, tiles_by_type_and_owner, map_size):
        where_to_expand = defaultdict(set) # {cost: {position,}}

        for tile in my_tiles:
            adjacent_positions = adjacents(tile, map_size)

            not_mine = adjacent_positions - my_tiles
            for not_my_tile in not_mine:
                cost = self._get_conquer_cost(not_my_tile, world, tiles_by_type_and_owner, map_size)

                where_to_expand[cost].add(not_my_tile)

        return where_to_expand

    def process_world(self, world, map_size):
        enemies, tiles_by_type_and_owner = self._get_enemies_and_tiles_by_type_and_owner(world)
        forts_and_castles = tiles_by_type_and_owner[CASTLE][MINE].union(tiles_by_type_and_owner[FORT][MINE])
        my_tiles = self._get_my_tiles(tiles_by_type_and_owner)
        borders, protected_terrain, unprotected_terrain = self._get_borders_protected_and_uprotected_tiles(my_tiles, forts_and_castles, map_size)
        where_to_fort = self._get_where_to_fort(unprotected_terrain, map_size)
        useful_to_expand = self._get_useful_to_expand(forts_and_castles, my_tiles, map_size)
        where_to_farm = self._get_where_to_plant_a_farm(tiles_by_type_and_owner, protected_terrain)
        where_to_expand = self._get_where_to_expand(my_tiles, world, tiles_by_type_and_owner, map_size)

        return Insights(
            enemies,
            tiles_by_type_and_owner,
            forts_and_castles,
            my_tiles,
            borders,
            protected_terrain,
            unprotected_terrain,
            where_to_fort,
            useful_to_expand,
            where_to_farm,
            where_to_expand,
        )

    def turn(self, map_size, my_resources, world):
        logging.warning("TURNNNNNN")
        try:
            insights = self.process_world(world, map_size)
            strategy = Strategy(insights, my_resources)
            action = strategy.select_action()
            if not isinstance(action, tuple):
                raise Exception()

            return action
        except:
            logging.exception("Error, use default strategy")
        return "harvest", None
