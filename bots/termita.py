import random
import time
import logging

from game import (
    CASTLE,
    CONQUER,
    CONQUER_COSTS,
    DEFENDER_STRUCTURES,
    FARM,
    FORT,
    HARVEST,
    LAND,
    MINE,
    Position,
)


real_print = print


def print(*texts):
    #real_print(*texts)
    #logging.info(" ".join(map(str, texts)))
    pass


def find_castle(world):
    all_castles = [
        position
        for position, terrain in world.items()
        if terrain.owner == MINE and terrain.structure == CASTLE
    ]
    return all_castles[0]


def find_random_land(world):
    all_our_lands = [
        position
        for position, terrain in world.items()
        if terrain.owner == MINE and terrain.structure == LAND
    ]
    return random.choice(all_our_lands) if all_our_lands else None


def get_around(world, map_size, base_pos, radius):
    base_x, base_y = base_pos
    max_x, max_y = map_size

    result = []
    y = base_y - radius
    for x in range(base_x - radius, base_x + radius + 1):
        result.append(Position(x, y))
    # print("=============== t1", result)
    y = base_y + radius
    for x in range(base_x - radius, base_x + radius + 1):
        result.append(Position(x, y))
    # print("=============== t2", result)

    x = base_x - radius
    for y in range(base_y - radius, base_y + radius + 1):
        result.append(Position(x, y))
    x = base_x + radius
    for y in range(base_y - radius, base_y + radius + 1):
        result.append(Position(x, y))

    filtered = []
    for pos in set(result):
        if pos.x >= max_x or pos.x < 0:
            continue
        if pos.y >= max_y or pos.y < 0:
            continue
        if pos.x == base_x and pos.y == base_y:
            continue
        filtered.append(pos)

    return filtered


def get_path(pos_init, pos_dest):
    full_x = pos_dest.x - pos_init.x
    full_y = pos_dest.y - pos_init.y
    steps = abs(full_x) + abs(full_y)
    dx = full_x / steps
    dy = full_y / steps
    cells = []
    for step in range(1, steps + 1):
        nx = pos_init.x + dx * step
        ny = pos_init.y + dy * step
        int_x = int(round(nx))
        int_y = int(round(ny))

        # avoid diagonal jumping from before
        if cells:
            prev = cells[-1]
        else:
            prev = pos_init

        real_jump_x = abs(int_x - prev.x)
        real_jump_y = abs(int_y - prev.y)
        if real_jump_x == 1 and real_jump_y == 1:
            # break the diagonal jumping not adjacent
            cells.append(Position(int_x, prev.y))

        cells.append(Position(int_x, int_y))
    return cells


class BotLogic:

    def is_isolated(self, pos):
        """Return if the position is isolated from our lands."""
        px, py = pos
        max_x, max_y = self.map_size
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx = px + dx
            ny = py + dy
            if nx >= max_x or nx < 0:
                continue
            if ny >= max_y or ny < 0:
                continue
            terrain = self.world[(nx, ny)]
            if terrain.owner == MINE:
                return False
        return True

    def get_farmable(self, center, radius):
        """If any of available positions around is a land, let's farm it."""
        ring = get_around(self.world, self.map_size, center, radius)
        # print("========= ring", radius, ring)
        actionable = [pos for pos in ring if not self.is_isolated(pos)]

        # first pass, defend from others
        for pos in actionable:
            terrain = self.world[pos]
            if terrain.owner not in (MINE, None):
                return CONQUER, pos

        # second pass, farm our lands
        for pos in actionable:
            terrain = self.world[pos]
            if terrain.owner == MINE and terrain.structure == LAND:
                return FARM, pos

        # third pass, expand
        for pos in actionable:
            terrain = self.world[pos]
            if terrain.owner != MINE:
                return CONQUER, pos

        return None, pos

    def find_near_enemies(self, center, radius):
        nears = []
        for pos, terrain in self.world.items():
            if terrain.owner not in (MINE, None):
                dist = abs(center.x - pos.x) + abs(center.y - pos.y)
                if dist < radius:
                    nears.append((pos, dist))
        return nears

    def find_closest_enemy_castle(self):
        enemy_castles = [
            position
            for position, terrain in self.world.items()
            if terrain.owner != MINE and terrain.structure == CASTLE
        ]

        closest_distance = 1000000000
        target_pos = None
        source_pos = None
        for pos, terrain in self.world.items():
            if terrain.owner == MINE:
                for enemy_pos in enemy_castles:
                    dist = abs(enemy_pos.x - pos.x) + abs(enemy_pos.y - pos.y)
                    if dist < closest_distance:
                        closest_distance = dist
                        target_pos = enemy_pos
                        source_pos = pos
        return source_pos, target_pos

    def can_build_castle(self):
        total_mine = 0
        total_castles = 0
        for terrain in self.world.values():
            if terrain.owner == MINE:
                total_mine += 1
                if terrain.structure == CASTLE:
                    total_castles += 1
        return total_mine / total_castles > 51

    def is_defended(self, pos):
        base_terrain = self.world[pos]
        px, py = pos
        max_x, max_y = self.map_size
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx = px + dx
            ny = py + dy
            if nx >= max_x or nx < 0:
                continue
            if ny >= max_y or ny < 0:
                continue
            near_terrain = self.world[(nx, ny)]
            if near_terrain.owner == base_terrain.owner:
                if near_terrain.structure in DEFENDER_STRUCTURES:
                    return True
        return False

    def get_cost_to_conquer(self, pos):
        cost_to_conquer = CONQUER_COSTS[self.world[pos].structure]
        print("========== conquer cost?", cost_to_conquer)
        if isinstance(cost_to_conquer, tuple):
            if self.is_defended(pos):
                cost_to_conquer = cost_to_conquer[1]
            else:
                cost_to_conquer = cost_to_conquer[0]
        return cost_to_conquer

    def turn(self, map_size, my_resources, world):
        self.map_size = map_size
        self.world = world

        print("===== my res?", my_resources, time.time())
        castle_pos = find_castle(world)
        print("===== castle", castle_pos)

        # first phase! if any of available positions around is a land, let's farm it
        action, pos = self.get_farmable(castle_pos, 1)
        # if action is None:
        #     action, pos = self.get_farmable(castle_pos, 2)
        print("======= action farm?", action, pos)

        if action == FARM and my_resources >= 5:
            return FARM, pos
        if action == CONQUER:
            cost_to_conquer = self.get_cost_to_conquer(pos)
            if my_resources >= cost_to_conquer:
                return CONQUER, pos
        if action == FARM or action == CONQUER:
            return HARVEST, None

        # second phase, defense!
        near_enemies = self.find_near_enemies(castle_pos, 9)
        print("========== DEFENSE!", len(near_enemies))
        if near_enemies and my_resources < 50:
            return HARVEST, None
        for near_pos, near_distance in near_enemies:
            # print("============= near enemy pos", near_pos, near_distance)
            path = get_path(castle_pos, near_pos)
            # print("========== path", path)
            for pos in path:
                terrain = world[pos]
                if terrain.owner != MINE:
                    cost_to_conquer = self.get_cost_to_conquer(pos)
                    if my_resources >= cost_to_conquer:
                        return CONQUER, pos
                    else:
                        return HARVEST, None
                if terrain.structure == LAND:
                    return FORT, pos
                if terrain.structure == FORT:
                    break

        # phase 2.5, attack or improve positions?
        if random.random() < .05 and my_resources > 100:
            print("============== SAFE NET")
            random_land_pos = find_random_land(self.world)
            if random_land_pos is not None:
                print("======= safe land", random_land_pos)
                if self.can_build_castle():
                    action = CASTLE
                else:
                    action = FARM
                return action, random_land_pos

        # yes, third phase, attack!!
        if my_resources < 200:
            print("==============  (no attack, wait)")
            return HARVEST, None
        attack_source, closest_target = self.find_closest_enemy_castle()
        print("============== ATTACK?", attack_source, closest_target)

        path = get_path(attack_source, closest_target)
        # print("========== path", path)
        for pos in path:
            terrain = world[pos]
            if terrain.owner != MINE:
                return CONQUER, pos

        print("======== Plan Z")
        return HARVEST, None


if __name__ == "__main__":
    src = Position(x=19, y=3)
    dst = Position(x=21, y=1)
    print(get_path(src, dst))
