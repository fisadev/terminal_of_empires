import random

BUY_CASTLE_AND_MORE_BUDGET = 400
ATTACK_AND_DEFEND_BUDGET = 300
REQUIRED_CASTLE_TERRAIN_RATIO = 50
MINIMUM_FARM_COUNT = 5
MINIMUM_FORT_COUNT = 2
MIN_DISTANCE_TO_ENEMY = 5
MIN_FARM_TILE_RATIO = 0.2
MINIMUM_DEFENSE = 7
SECURITY_DISTANCE = 5


def is_adjacent(position1, position2):
    """
    Return True if the two positions are adjacent, False otherwise.
    """
    x1, y1 = position1
    x2, y2 = position2

    return abs(x1 - x2) + abs(y1 - y2) == 1


def get_distance(position1, position2):
    x1, y1 = position1
    x2, y2 = position2
    return ((x1-x2)**2 + (y1-y2)**2)**0.5


def find_nearest_position_to_target(map_size, target_position, positions):
    closest_position = None
    min_distance = get_distance(map_size, (0, 0))
    for position in positions:
        current_distance = get_distance(position, target_position)
        if current_distance < min_distance:
            min_distance = current_distance
            closest_position = position
    return closest_position

def my_castles(world):
    return [position for position,terrain in world.items()
            if terrain.owner=="mine" and terrain.structure=="castle"]

def my_farms(world):
    return [position for position,terrain in world.items()
            if terrain.owner=="mine" and terrain.structure=="farm"]

def my_forts(world):
    return [position for position,terrain in world.items()
            if terrain.owner=="mine" and terrain.structure=="fort"]


def my_terrain(world):
    return [position for position,terrain in world.items()
            if terrain.owner=="mine"]

def can_build_new_castle(state):
    if len(state.my_castles):
        ratio_castle_land = len(state.my_terrain) / len(state.my_castles)
        return ratio_castle_land > REQUIRED_CASTLE_TERRAIN_RATIO

def find_close_enemy(map_size, world):
    close_enemy_castles = {}
    enemy_castles = [position for position, terrain in world.items()
                         if terrain.structure == 'castle' and terrain.owner != 'mine']
    for castle in enemy_castles:
        nearest_position = find_nearest_position_to_target(map_size, castle, my_terrain(world))
        distance = get_distance(castle, nearest_position)
        if distance < MIN_DISTANCE_TO_ENEMY:
            close_enemy_castles[castle] = distance
    return close_enemy_castles

def my_terrain_adjacent_to_structure(state, world, structure):
    my_terrain = state.my_terrain
    my_structures =  [position for position in my_terrain
                      if world[position].structure == structure]

    positions_adjacent_to_structure = []
    for my_structure in my_structures:
        for my_position in my_terrain:
            if is_adjacent(my_position, my_structure):
                positions_adjacent_to_structure.append(my_position)

    return positions_adjacent_to_structure

def defense_is_sufficient(state, world):
    my_terrain_adjacent_to_castle = my_terrain_adjacent_to_structure(state, world, 'castle')
    farms_adjacent_to_castle = [position for position in my_terrain_adjacent_to_castle
                                if world[position].structure == 'farm']
    my_terrain_adjacent_to_fort = my_terrain_adjacent_to_structure(state, world, 'fort')
    farms_adjacent_to_fort = [position for position in my_terrain_adjacent_to_fort
                                if world[position].structure == 'farm']
    defense = (len(state.my_forts) + 2*len(state.my_castles)
               + len(farms_adjacent_to_castle) + len(farms_adjacent_to_fort))

    return defense > MINIMUM_DEFENSE

def get_conquerable_terrain(state, world):
    return [position for position, terrain in world.items()
            if any(is_adjacent(position, my_position) for my_position in state.my_terrain)
            and terrain.owner != "mine"]

def get_conquerable_empty_terrain(state, world):
    return [position for position, terrain in world.items()
            if any(is_adjacent(position, my_position) for my_position in state.my_terrain)
            and terrain.owner != "mine" and terrain.structure == "land"]

# def get_enemy_positions_map(state, world):
#     enemy_positions_map = {}
#     for position, terrain in world.items():
#         if owner:
#             enemy_positions_map[terrain.owner]
#         enemy_positions_map.get(terrain.owner, []).append(position)
#     return enemy_positions_map

def get_close_enemy_positions(world, min_distance):
    # [position for position,terrain in world.items()
    #         if terrain.owner != "mine"
    #         and any(get_distance(position, my_position) <
    #                 min_distance for my_position in state.my_terrain)]
    close_enemy_positions = {}
    for position, terrain in world.items():
        for my_position in my_terrain(world):
            distance = get_distance(position, my_position)
            if terrain.owner != "mine" and distance < min_distance:
                close_enemy_positions[position]=distance
    return close_enemy_positions

def defend_and_attack_mode(state, world):

    conquerable_terrain = get_conquerable_terrain(state, world)
    closest_enemy = min(state.closest_enemy_positions, key=state.closest_enemy_positions.get)
    my_closest_position = find_nearest_position_to_target(state.map_size, closest_enemy, state.my_terrain)
    next_positions = [position for position in conquerable_terrain if is_adjacent(my_closest_position, position)]
    if next_positions:
        next_positions_distances = [(next_position, get_distance(next_position, closest_enemy))
                                for next_position in next_positions]
        closest_next_position = min(next_positions_distances,  key=lambda x: x[1])[0]
        return 'conquer', closest_next_position
    else:
        return 'conquer', random.choice(conquerable_terrain)

def find_closest_enemy_castle(state, world):
    enemy_castles = state.close_enemy_castles
    distances = []
    for enemy_castle in enemy_castles:
        nearest_position = find_nearest_position_to_target(state.map_size, enemy_castle, state.my_terrain)
        distances.append((get_distance(enemy_castle, nearest_position), enemy_castle))
    return sorted(distances, key=lambda x: x[0])[0]



class State:
    def __init__(self, world, my_resources, map_size):
        self.resources = my_resources
        self.my_castles = my_castles(world)
        self.castle_count = len(my_castles(world))
        self.my_farms = my_farms(world)
        self.farm_count = len(my_farms(world))
        self.my_terrain = my_terrain(world)
        self.my_forts = my_forts(world)
        self.map_size = map_size
        self.close_enemy_castles = find_close_enemy(map_size, world)
        #self.close_enemy_positions = get_close_enemy_positions(world, SECURITY_DISTANCE)

def enforce_defense_mode(state, world):

    conquerable_empty_terrain = get_conquerable_empty_terrain(state, world)
    conquerable_terrain = get_conquerable_terrain(state, world)

    structure_adjacent_positions = my_terrain_adjacent_to_structure(
        state, world, 'castle')
    positions_to_enforce = [position for position in structure_adjacent_positions
                                  if world[position].structure not in ['farm', 'fort']]

    if 25 < state.resources < 100 and len(state.my_terrain) > 1:
        if positions_to_enforce:
            structure = random.choices(['farm', 'fort'], [0.7,0.3])[0]
            return structure, random.choice(positions_to_enforce)
        else:
            my_empty_terrain = [position for position, terrain in world.items()
                                if terrain.structure == "land" and terrain.owner == "mine"]
            if my_empty_terrain:
                return 'farm', random.choice(my_empty_terrain)
            else:
                return 'conquer', random.choice(conquerable_terrain)
    elif state.resources > 100 and len(state.my_terrain) > 1:
        if positions_to_enforce:
            return 'fort', random.choice(positions_to_enforce)
        else:
            my_empty_terrain = [position for position, terrain in world.items()
                                if terrain.structure == "land" and terrain.owner == "mine"]
            if my_empty_terrain:
                return 'fort', random.choice(my_empty_terrain)
            else:
                return 'conquer', random.choice(conquerable_terrain)

    action = random.choices(['harvest', 'build'])[0]

    if action =='build':
        if state.resources > 5 and len(state.my_terrain) > 1:
            if positions_to_enforce:
                return 'farm', random.choice(positions_to_enforce)
        else:
            if conquerable_empty_terrain:
                return 'conquer', random.choice(conquerable_empty_terrain)
            if conquerable_terrain:
                return 'conquer', random.choice(conquerable_terrain)
            else:
                return 'harvest', None
    elif action=='harvest':
        return 'harvest', None


def grow_resources_mode(state, world):

    conquerable_empty_terrain = get_conquerable_empty_terrain(state, world)
    conquerable_terrain = get_conquerable_terrain(state, world)

    if state.resources < 5:
        return 'harvest', None

    action = random.choices(['harvest', 'conquer', 'build'], [0.35, 0.3, 0.35])[0]
    if action == 'harvest':
        return 'harvest', None
    if action == 'conquer':
        if conquerable_empty_terrain:
            return 'conquer', random.choice(conquerable_empty_terrain)
        elif conquerable_terrain:
            return 'conquer', random.choice(conquerable_terrain)
        else:
            return 'harvest', None
    if action == 'build':
        my_empty_terrain = [position for position, terrain in world.items()
                            if terrain.structure == "land" and terrain.owner == "mine"]
        my_terrain_without_castle = [position for position in state.my_terrain
                                     if position not in state.my_castles]
        if state.farm_count < MINIMUM_FARM_COUNT:
            if my_empty_terrain:
                return 'farm', random.choice(my_empty_terrain)
            elif my_terrain_without_castle:
                return 'farm', random.choice(my_terrain_without_castle)
            else:
                return 'harvest', None
        elif state.farm_count >= MINIMUM_FARM_COUNT:
            if state.resources > 25 and len(state.my_forts) < MINIMUM_FORT_COUNT:
                positions_close_to_castle = [position for position in my_terrain_without_castle
                                             if get_distance(position, state.my_castles[0]) < 10]
                return 'fort', random.choice(positions_close_to_castle)
            elif 75 > state.resources > 25 and len(state.my_forts) >= MINIMUM_FORT_COUNT:
                return 'farm', random.choice(my_terrain_without_castle)
            elif  state.resources > 75 and can_build_new_castle(state):
                    if my_empty_terrain:
                        return 'castle', random.choice(my_empty_terrain)
                    else:
                        return 'castle', random.choice(my_terrain_without_castle)
            else:
                return 'harvest', None

def build_new_castle_mode(state, world):
    my_empty_terrain = [position for position in state.my_terrain
                        if world[position].structure == "land"]
    my_terrain_without_castle = [position for position in state.my_terrain
                                     if position not in state.my_castles]
    conquerable_terrain = get_conquerable_terrain(state, world)
    conquerable_empty_terrain = get_conquerable_empty_terrain(state, world)

    if can_build_new_castle(state):
        if my_empty_terrain:
            # TODO: select terrain near farm?
            return 'castle', random.choice(my_empty_terrain)
        elif my_terrain_without_castle:
            return 'castle', random.choice(my_terrain_without_castle)
        else:
            return 'harvest', None
    else:
        if conquerable_empty_terrain:
            return 'conquer', random.choice(conquerable_empty_terrain)
        elif conquerable_terrain:
            return 'conquer', random.choice(conquerable_terrain)
        else:
            return 'harvest', None

def destroy_castle_mode(state, world, weights = (0.8, 0.2)):


    action = random.choices(['destroy', 'build castle'], weights)[0]
    if action == 'destroy':
        conquerable_terrain = get_conquerable_terrain(state, world)
        enemy_castles = [position for position, terrain in world.items()
                         if terrain.structure == 'castle' and not terrain.owner == 'mine']

        target_castle = random.choice(enemy_castles) # change this

        closest_position = find_nearest_position_to_target(state.map_size, target_castle, state.my_terrain)
        next_positions = [position for position in conquerable_terrain if is_adjacent(closest_position, position)]
        if next_positions:
            return 'conquer', random.choice(next_positions)
        else:
            return 'conquer', random.choice(conquerable_terrain)

    elif action == 'build castle':
        return build_new_castle_mode(state, world)
    else:
        return 'harvest', None

def harvest_then_destroy_mode(state, world):
    action = random.choices(['destroy', 'harvest'])[0]
    if action == 'destroy':
        return destroy_castle_mode(state, world, [1, 0]) # only destroy
    if action == 'harvest':
        return 'harvest', None

def select_turn_action(state, world):
    if state.castle_count == 1 and len(state.close_enemy_castles)>0:
        if not defense_is_sufficient(state, world):
            return enforce_defense_mode(state, world)
        else:
            return grow_resources_mode(state, world)
    if state.castle_count == 1 and state.resources < BUY_CASTLE_AND_MORE_BUDGET:
        return grow_resources_mode(state, world)
    elif state.castle_count == 1 and state.resources >= BUY_CASTLE_AND_MORE_BUDGET:
        return build_new_castle_mode(state, world)
    elif state.castle_count == 2 and state.resources > ATTACK_AND_DEFEND_BUDGET:
        return destroy_castle_mode(state, world)
    elif state.castle_count == 2 and state.resources <= ATTACK_AND_DEFEND_BUDGET:
        return harvest_then_destroy_mode(state, world)
    elif state.castle_count > 2 and state.resources > ATTACK_AND_DEFEND_BUDGET:
        return destroy_castle_mode(state, world, [0.8, 0.2])
    elif state.castle_count > 2 and state.resources <= ATTACK_AND_DEFEND_BUDGET:
        return harvest_then_destroy_mode(state, world)
    else:
        return 'harvest', None



class BotLogic:
    """
    This bots is very complicated and inefficient
    """

    def turn(self, map_size, my_resources, world):

        if my_resources < 5:
            return 'harvest', None

        state = State(world, my_resources, map_size)
        return select_turn_action(state, world)





