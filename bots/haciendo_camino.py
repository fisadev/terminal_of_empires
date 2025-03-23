import logging
from collections import defaultdict
from dataclasses import dataclass

from game import FORT, LAND, FARM, CASTLE, MINE, CONQUER, HARVEST, STRUCTURE_COST, CONQUER_COSTS


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
    tiles_by_type_and_owner: dict
    forts_and_castles: set
    my_tiles: set
    protected_terrain: set
    unprotected_terrain: set
    where_to_fort: dict
    useful_to_expand: set
    where_to_farm: set
    where_to_expand: dict


class BotLogic:

    @staticmethod
    def _get_tiles_by_type_and_owner(world):
        _tiles_by_type_and_owner = defaultdict(lambda: defaultdict(set))
        for position, terrain in world.items():
            _tiles_by_type_and_owner[terrain.structure][terrain.owner].add(position)
        return _tiles_by_type_and_owner

    @staticmethod
    def _get_my_tiles(tiles_by_type_and_owner):
        my_tiles = set()
        for structure, owners in tiles_by_type_and_owner.items():
            for owner, positions in owners.items():
                if owner == MINE:
                    my_tiles = my_tiles.union(positions)

        return my_tiles

    @staticmethod
    def _get_protected_and_uprotected_tiles(my_tiles, forts_and_castles, map_size):
        protected, unprotected = set(), set()
        for tile in my_tiles:
            adjacent_positions = adjacents(tile, map_size)

            # protected terrain: is a fort or castle or is adjacent to one of them
            if tile in forts_and_castles:
                protected.add(tile)
            elif any(adj in forts_and_castles for adj in adjacent_positions):
                protected.add(tile)
            else:
                unprotected.add(tile)

        return protected, unprotected

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
        oponent = world[tile].owner
        structure = world[tile].structure

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
                cost = self._get_conquer_cost(tile, world, tiles_by_type_and_owner, map_size)

                where_to_expand[cost].add(not_my_tile)

        return where_to_expand

    def process_world(self, world, map_size):
        tiles_by_type_and_owner = self._get_tiles_by_type_and_owner(world)
        forts_and_castles = tiles_by_type_and_owner[CASTLE][MINE].union(tiles_by_type_and_owner[FORT][MINE])
        my_tiles = self._get_my_tiles(tiles_by_type_and_owner)
        protected_terrain, unprotected_terrain = self._get_protected_and_uprotected_tiles(my_tiles, forts_and_castles, map_size)
        where_to_fort = self._get_where_to_fort(unprotected_terrain, map_size)
        useful_to_expand = self._get_useful_to_expand(forts_and_castles, my_tiles, map_size)
        where_to_farm = self._get_where_to_plant_a_farm(tiles_by_type_and_owner, protected_terrain)
        where_to_expand = self._get_where_to_expand(my_tiles, world, tiles_by_type_and_owner, map_size)

        return Insights(
            tiles_by_type_and_owner,
            forts_and_castles,
            my_tiles,
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
        except:
            logging.exception("ERRRRORRRR")
        return "harvest", None
