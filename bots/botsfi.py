import logging
import random
from collections import defaultdict, namedtuple
from dataclasses import dataclass
from typing import Optional

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

EnemyTile = namedtuple("EnemyTile", "enemy_position owner structure near_tile_mine near_tile_to_expand cost_to_conquer distance")
TileToConquer = namedtuple("TileToConquer", "position cost")

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
    my_castle_position: tuple
    enemies: set
    tiles_by_type_and_owner: dict
    all_enemy_tiles: set
    enemy_castles: set
    forts_and_castles: set
    my_tiles: set
    borders: set
    protected_terrain: set
    unprotected_terrain: set
    where_to_fort: dict
    useful_to_expand: set
    where_to_farm: set
    where_to_expand_by_cost: dict
    near_enemy_castle: EnemyTile
    near_enemy_tile: EnemyTile
    near_enemy_to_my_castle: EnemyTile
    conquer_next_to_castle: list


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

    def get_fortify_conquer_action(self):
        for to_conquer in self.insights.conquer_next_to_castle:
            logging.warning(to_conquer)
            if to_conquer.cost < self.my_resources:
                return CONQUER, to_conquer.position

        return False

    def fortify(self):
        fortification_max_benefit = max(self.insights.where_to_fort)

        positions_to_fortify = self.insights.where_to_fort[fortification_max_benefit]
        position = random_choice_from_set(positions_to_fortify)

        return FORT, position

    def decide_to_farm(self):
        if self.my_resources < STRUCTURE_COST[FARM]:
            return False

        if not self.insights.where_to_farm:
            return False

        my_farms = len(self.insights.tiles_by_type_and_owner[FARM][MINE])

        if my_farms < 4:
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
        can_afford = any(cost for cost in self.insights.where_to_expand_by_cost.keys() if cost <= self.my_resources)
        costs = [cost for cost in self.insights.where_to_expand_by_cost.keys()]
        resources = self.my_resources

        if can_afford and random.random() <= 0.8:
            return True

        return False

    def conquer(self):
        if self.insights.near_enemy_castle.cost_to_conquer < self.my_resources:
            return CONQUER, self.insights.near_enemy_castle.near_tile_to_expand

        if self.insights.near_enemy_tile.cost_to_conquer < self.my_resources:
            return CONQUER, self.insights.near_enemy_tile.near_tile_to_expand

        max_affordable_tile = max(cost for cost in self.insights.where_to_expand_by_cost.keys() if cost <= self.my_resources)

        position_to_conquer = random_choice_from_set(self.insights.where_to_expand_by_cost[max_affordable_tile])

        return CONQUER, position_to_conquer

    def decide_to_kill_mode(self):
        if self.insights.near_enemy_castle.distance < 5:
            return True

        return False

    def kill_mode_action(self):
        if self.insights.near_enemy_castle.cost_to_conquer <= self.my_resources:
            return CONQUER, self.insights.near_enemy_castle.near_tile_to_expand

        return self.harvest()

    def decide_defense_mode(self):
        # fortify nearest if not already fortified
        if self.insights.near_enemy_to_my_castle.distance < 4:
            if self.insights.near_enemy_to_my_castle.near_tile_mine in self.insights.unprotected_terrain:
                return True

        return False

    def defense_mode_action(self):
        if STRUCTURE_COST[FORT] <= self.my_resources:
            return FORT, self.insights.near_enemy_to_my_castle.near_tile_mine

        return self.harvest()

    def select_action(self):
        if not self.my_resources:
            return self.harvest()

        build_castle = self.build_castle()
        if build_castle:
            return build_castle

        if self.decide_to_farm():
            return self.farm()

        fortify_action = self.get_fortify_conquer_action()
        if fortify_action:
            return fortify_action

        if self.decide_defense_mode():
            return self.defense_mode_action()


        if self.decide_to_kill_mode():
            return self.kill_mode_action()

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

    @staticmethod
    def _get_all_enemy_tiles(tiles_by_type_and_owner):
        all_enemy_tiles = set()
        for structure, owners in tiles_by_type_and_owner.items():
            for owner, positions in owners.items():
                if owner != MINE:
                    all_enemy_tiles = all_enemy_tiles.union(positions)

        return all_enemy_tiles

    @staticmethod
    def _get_enemy_castles(tiles_by_type_and_owner):
        enemy_castles = set()
        for owner, positions in tiles_by_type_and_owner[CASTLE].items():
            if owner != MINE:
                enemy_castles = enemy_castles.union(positions)

        return enemy_castles

    def _get_near_enemy_castle_to_this_tile(self, tile, enemy_castles):
        near_enemy_castle = None
        min_distance = float("inf")

        for enemy_castle in enemy_castles:
            d = distance(tile, enemy_castle)
            if d < min_distance:
                min_distance = d
                near_enemy_castle = enemy_castle

        return near_enemy_castle, min_distance

    def _get_near_enemy_tile_to_this_tile(self, tile, all_enemy_tiles):
        near_enemy_tile = None
        min_distance = float("inf")

        for enemy_tile in all_enemy_tiles:
            d = distance(tile, enemy_tile)
            if d < min_distance:
                min_distance = d
                near_enemy_tile = enemy_tile

        return near_enemy_tile, min_distance


    def _get_where_to_expand(self, borders, my_tiles, world, tiles_by_type_and_owner, map_size, all_enemy_tiles, enemy_castles):
        where_to_expand_by_cost = defaultdict(set) # {cost: {position,}}
        near_enemy_castle: Optional[EnemyTile] = None
        near_enemy_tile: Optional[EnemyTile] = None
        near_enemy_to_my_castle: Optional[EnemyTile] = None

        my_castle_position = next(iter(tiles_by_type_and_owner[CASTLE][MINE]))
        near_enemy_to_my_castle_position, _ = self._get_near_enemy_tile_to_this_tile(my_castle_position, all_enemy_tiles)

        for tile in borders:
            adjacent_positions = adjacents(tile, map_size)

            not_mine = adjacent_positions - my_tiles
            for not_my_tile in not_mine:
                cost = self._get_conquer_cost(not_my_tile, world, tiles_by_type_and_owner, map_size)

                where_to_expand_by_cost[cost].add(not_my_tile)
                tmp_near_enemy_castle, tmp_distance_castle = self._get_near_enemy_castle_to_this_tile(not_my_tile, enemy_castles)
                tmp_near_enemy_tile, tmp_distance_tile = self._get_near_enemy_tile_to_this_tile(not_my_tile, all_enemy_tiles)

                if not near_enemy_castle or tmp_distance_castle < near_enemy_castle.distance:
                    near_enemy_castle = EnemyTile(
                        enemy_position=tmp_near_enemy_castle,
                        owner=world[tmp_near_enemy_castle].owner,
                        structure=world[tmp_near_enemy_castle].structure,
                        near_tile_mine=tile,
                        near_tile_to_expand=not_my_tile,
                        cost_to_conquer=cost,
                        distance=tmp_distance_castle
                    )

                if not near_enemy_tile or tmp_distance_tile < near_enemy_tile.distance:
                    near_enemy_tile = EnemyTile(
                        enemy_position=tmp_near_enemy_tile,
                        owner=world[tmp_near_enemy_tile].owner,
                        structure=world[tmp_near_enemy_tile].structure,
                        near_tile_mine=tile,
                        near_tile_to_expand=not_my_tile,
                        cost_to_conquer=cost,
                        distance=tmp_distance_tile
                    )

                if tmp_near_enemy_tile == near_enemy_to_my_castle_position:
                    near_enemy_to_my_castle = EnemyTile(
                        enemy_position=tmp_near_enemy_tile,
                        owner=world[tmp_near_enemy_tile].owner,
                        structure=world[tmp_near_enemy_tile].structure,
                        near_tile_mine=tile,
                        near_tile_to_expand=not_my_tile,
                        cost_to_conquer=cost,
                        distance=tmp_distance_tile
                    )

        return where_to_expand_by_cost, near_enemy_castle, near_enemy_tile, near_enemy_to_my_castle

    def _get_fortify_conquer_tiles(self, my_castle_position, world, tiles_by_type_and_owner, map_size, my_tiles):
        conquer_next_to_castle = []

        adjs_to_castle = adjacents(my_castle_position, map_size)

        for adj_c in adjs_to_castle:
            if adj_c not in my_tiles:
                cost = self._get_conquer_cost(adj_c, world, tiles_by_type_and_owner, map_size)
                conquer_next_to_castle.append(TileToConquer(adj_c, cost))

        return conquer_next_to_castle

    def process_world(self, world, map_size):
        enemies, tiles_by_type_and_owner = self._get_enemies_and_tiles_by_type_and_owner(world)
        my_castle_position = next(iter(tiles_by_type_and_owner[CASTLE][MINE]))
        all_enemy_tiles = self._get_all_enemy_tiles(tiles_by_type_and_owner)
        enemy_castles = self._get_enemy_castles(tiles_by_type_and_owner)
        forts_and_castles = tiles_by_type_and_owner[CASTLE][MINE].union(tiles_by_type_and_owner[FORT][MINE])
        my_tiles = self._get_my_tiles(tiles_by_type_and_owner)
        borders, protected_terrain, unprotected_terrain = self._get_borders_protected_and_uprotected_tiles(my_tiles, forts_and_castles, map_size)
        where_to_fort = self._get_where_to_fort(unprotected_terrain, map_size)
        useful_to_expand = self._get_useful_to_expand(forts_and_castles, my_tiles, map_size)
        where_to_farm = self._get_where_to_plant_a_farm(tiles_by_type_and_owner, protected_terrain)
        where_to_expand_by_cost, near_enemy_castle, near_enemy_tile, near_enemy_to_my_castle = self._get_where_to_expand(
            borders, my_tiles, world, tiles_by_type_and_owner, map_size, all_enemy_tiles, enemy_castles
        )
        conquer_next_to_castle = self._get_fortify_conquer_tiles(my_castle_position, world, tiles_by_type_and_owner, map_size, my_tiles)

        return Insights(
            my_castle_position,
            enemies,
            tiles_by_type_and_owner,
            all_enemy_tiles,
            enemy_castles,
            forts_and_castles,
            my_tiles,
            borders,
            protected_terrain,
            unprotected_terrain,
            where_to_fort,
            useful_to_expand,
            where_to_farm,
            where_to_expand_by_cost,
            near_enemy_castle,
            near_enemy_tile,
            near_enemy_to_my_castle,
            conquer_next_to_castle,
        )

    def turn(self, map_size, my_resources, world):
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
