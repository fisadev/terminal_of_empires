import random
from collections import defaultdict, namedtuple
import game as toe
from game import Position


KINGDOM_SIZE = toe.TILES_PER_CASTLE_LIMIT
SPARTANS = 90
KEEP_FORTING = 0.15
SEASONNALITY = 5
MIN_FARMS = 10
MIN_CASTLES_KILL_MODE = 1
MIN_RESOURCES_KILL_MODE = 100

def is_adjacent(position1, position2):
    """
    Return True if the two positions are adjacent, False otherwise.
    """
    x1, y1 = position1
    x2, y2 = position2

    return abs(x1 - x2) + abs(y1 - y2) <= 1

def manhattan_distance(position1, position2):
    x1, y1 = position1
    x2, y2 = position2

    return abs(x1 - x2) + abs(y1 - y2)


FA = toe.FARM
FO = toe.FORT


pattern = [
    [FA, FA, FA, FA, FA, FA, FA],
    [FA, FO, FA, FO, FA, FO, FA],
    [FA, FA, FA, FA, FA, FA, FA],
    [FA, FO, FA,  0, FA, FO, FA],
    [FA, FA, FA, FA, FA, FA, FA],
    [FA, FO, FA, FO, FA, FO, FA],
    [FA, FA, FA, FA, FA, FA, FA],
]

paranoid = [
    [FO, FO, FO, FO, FO],
    [FO, FO, FO, FO, FO],
    [FO, FO,  0, FO, FO],
    [FO, FO, FO, FO, FO],
    [FO, FO, FO, FO, FO],
]


def desired_contribution(dx, dy):
    # both dx and dy range from -2 to 2. Shift now to 0 to 5
    s_dx = dx + 2
    s_dy = dy + 2
    structure = pattern[s_dy][s_dx]
    structure_mult = toe.STRUCTURE_COST.get(structure, 1)
    manhattan_dist = abs(dx) + abs(dy)
    return structure_mult / manhattan_dist

def _perfect_score():
    result = 0
    for dx in [-2, -1, 0, 1, 2]:
        for dy in [-2, -1, 0, 1, 2]:
            if dx == 0 and dy == 0:
                continue
            result += desired_contribution(dx, dy)
    return result
PERFECT_SCORE = _perfect_score()

def desired_structure(dx, dy):
    # both dx and dy range from -2 to 2. Shift now to 0 to 5
    s_dx = dx + 2
    s_dy = dy + 2
    return pattern[s_dy][s_dx]


Neighbour = namedtuple("Neighbour", "position terrain dist dx dy")

class MyMunch:
    def __init__(self, position, terrain):
        self._position = position
        self.terrain = terrain

    @property
    def position(self):
        return self._position

    @property
    def owner(self):
        return self.terrain.owner

    @property
    def structure(self):
        return self.terrain.structure

    def __lt__(self, other):
        return self.position < other.position


class Turn:
    def __init__(self, number, map_size, my_resources, world, desired_resources=None, prev_castle_count=0):
        self.number = number
        self.map_size = map_size
        self.my_resources = my_resources
        self.world = world
        self.desired_resources = desired_resources or 15
        self._file = open("creep.lyrics", "a")
        self.print("="*45)
        self.print("NEW Turn", number)
        self.prev_castle_count = prev_castle_count

    def print(self, *args):
        print(*args, file=self._file)

    def harvest(self):
        self.print("Harvesting")
        return toe.HARVEST, None

    def action(self, paranoid_mode=False):
        if self.my_resources < self.desired_resources:
            return self.harvest()

        my_castles = self.my_castles()

        for pos, c in my_castles.items():
            c.safeness = self.compute_castle_safeness(pos)

        if paranoid_mode:
            # we have just lost a castle, and we have now only up to 2
            # TOM YORKE MODE. PARANOID ANDROID.
            # DEFEND. And if nothing else, normal play
            for cast in my_castles.values():
                self.defend(cast)

        self.aggressive_farms()

        # aggressive mode
        if len(my_castles) >= MIN_CASTLES_KILL_MODE:
            if self.my_resources >= MIN_RESOURCES_KILL_MODE:
                action = self.kill_the_bastards()
                if action:
                    what, where = action
                    self.recommend_next = toe.FARM, where
                    return action
            if self.my_resources >= 5000:
                action = self.passive_aggresive_expand()
                if action:
                    return action

        action = self.decide_if_repairing_castles(my_castles)
        if action:
            return action

        action = self.decide_if_time_to_build_farms()
        if action:
            return action

        action = self.decide_if_create_castle(my_castles)
        if action:
            return action

        action = self.passive_aggresive_expand()
        if action:
            return action

        return self.harvest()

    @property
    def my_terrain(self):
        if not hasattr(self, "_my_terrain"):
            self._my_terrain = [position for position, terrain in self.world.items() if terrain.owner == toe.MINE]
        return self._my_terrain

    def aggressive_farms(self):
        lands, farms = [], []
        for pos in self.my_terrain:
            terr = self.world[pos]
            if terr.structure == toe.LAND:
                lands.append(pos)
            elif terr.structure == toe.FARM:
                farms.append(pos)
        if len(farms) < MIN_FARMS:
            if lands:
                return toe.FARM, random.choice(lands)

    def decide_if_time_to_build_farms(self):
        if self.number % SEASONNALITY != 0 or self.my_resources > 20000:
            return None
        lands = [pos for pos in self.my_terrain if self.world[pos].structure == toe.LAND]
        if lands:
            self.print('  (bf) -> Building farm')
            return toe.FARM, random.choice(lands)

    def passive_aggresive_expand(self):
        adjacents = [
            (pos, terrain) for pos, terrain in self.world.items() if terrain.owner != toe.MINE and any(
                is_adjacent(pos, my_position)
                for my_position in self.my_terrain
            )
        ]
        conquerable_neutral_terrain = [
            position
            for position, terrain in adjacents
            if terrain.owner is None
        ]
        if conquerable_neutral_terrain:
            self.print('  (xp) -> Conquering neutral land')
            return toe.CONQUER, random.choice(conquerable_neutral_terrain)

        for stru in [toe.FARM, toe.FORT, toe.CASTLE]:
            conquerable_stuff = [
                position
                for position, terrain in adjacents
                if terrain.structure == stru
            ]
            if conquerable_stuff:
                self.print('  (xp) -> Conquering enemy stuff')
                return toe.CONQUER, random.choice(conquerable_stuff)

    def decide_if_create_castle(self, my_castles):
        l_castles = len(my_castles)
        if len(self.my_terrain) - 1 >= KINGDOM_SIZE * (l_castles):
            needed = toe.STRUCTURE_COST[toe.CASTLE]
            if self.my_resources < needed:
                self.desired_resources = needed
                return None
            return self.create_castle()

    def kill_the_bastards(self):
        bastards = {pos: terr for pos, terr in self.castles().items() if terr.owner != toe.MINE}

        # pick any castle
        bastard = random.choice(list(bastards.keys()))
        self.print('KILL THE BASTARD!!', bastard, self.world[bastard].owner)

        # pick closest terrain of mine
        mdist = manhattan_distance
        closest = sorted(self.my_terrain, key=lambda pos: mdist(bastard, pos))[0]

        # Pick the neighbours-of(closest) and pick the closest to bastard
        neighbours = self.surronding(closest, layers=1)
        for to_conquer in sorted(neighbours, key=lambda nei: mdist(bastard, nei.position)):
            if to_conquer.terrain.owner != toe.MINE and self.is_adjacent_to_me(to_conquer.position):
                return toe.CONQUER, to_conquer.position

    def create_castle(self):
        lands = [pos for pos in self.my_terrain if self.world[pos].structure == toe.LAND]
        if lands:
            return toe.CASTLE, random.choice(lands)

    def decide_if_repairing_castles(self, my_castles, threshold=50):
        unsafe_castles = sorted([(c.safeness, c) for pos, c in my_castles.items()])
        worst = unsafe_castles[0]
        worst_score = worst[0]

        offset = self.number / 10
        final_threshold = min(SPARTANS, threshold + offset) / 100
        self.print('Worst castle score is', worst_score, '?', final_threshold, ' '*40)
        if worst_score < final_threshold or random.uniform(0, 1) < KEEP_FORTING:
            self.print('Worst castle is unsafe, score is', worst_score, '<', final_threshold, ' '*40)
            return self.defend(worst[1])

    def compute_castle_safeness(self, pos):
        # adds if it has owned structres on edges
        # substracts 2x if has enemies
        # boundaries are neutral
        # emptyland substracts 1
        perfect = 0
        now = 0
        for nei in self.surronding(pos):
            if nei.terrain.owner == toe.MINE:
                o_mult = 1
            elif nei.terrain.owner == None:
                o_mult = -1
            else:
                o_mult = -2
            structure = nei.terrain.structure
            if structure == toe.CASTLE:
                structure = toe.FORT # castles are weighted too much otherwise
            s_mult = toe.STRUCTURE_COST.get(structure, 1)
            delta = o_mult * s_mult * (1 / nei.dist)
            now += delta
            perfect += desired_contribution(nei.dx, nei.dy)
        return now / perfect

    def is_adjacent_to_me(self, pos):
        return any(is_adjacent(pos, my_position) for my_position in self.my_terrain)

    def defend(self, castle):
        # Desired pattern on top
        def mine_idx(owner):
            if owner == toe.MINE:
                return 1
            elif owner == None:
                return 0
            else:
                return -1
        neighbours = sorted(
            self.surronding(castle.position),
            key=lambda n: (mine_idx(n.terrain.owner), n.dist)
        )

        nnss = []
        for nn in neighbours:
            if (nn.terrain.owner != toe.MINE and not self.is_adjacent_to_me(nn.position)):
                continue
            o_m = mine_idx(nn.terrain.owner)
            s_m = toe.STRUCTURE_COST.get(nn.terrain.structure, 1)
            factor = (o_m * s_m * (1 / nn.dist)) - desired_contribution(nn.dx, nn.dy)
            nnss.append((factor, nn))

        for factor, nei in sorted(nnss):
            if nei.terrain.owner == None:
                if not self.is_adjacent_to_me(nei.position):
                    continue
                self.print(' (DD) -> conquer neutral')
                return toe.CONQUER, nei.position
            elif nei.terrain.owner != toe.MINE:
                if not self.is_adjacent_to_me(nei.position):
                    continue
                needed = toe.CONQUER_COSTS.get(nei.terrain.structure, 100)
                if isinstance(needed, tuple):
                    needed = max(needed)  # worst case
                if self.my_resources < needed:
                    self.desired_resources = needed
                    self.print(' (DD) -> harvest')
                    return self.harvest()
                self.print(' (DD) -> conquer Enemy')
                return toe.CONQUER, nei.position
            else: # nei.terrain.owner == toe.MINE:
                self.print('     (Ty) -> Trying to improve', nei.terrain.structure, 'at', nei.position, nei.dx, nei.dy)
                expected = desired_structure(nei.dx, nei.dy)
                current = nei.terrain.structure
                # lets compare them in term of costs.
                expected_cost = toe.STRUCTURE_COST.get(expected, 0)
                current_cost = toe.STRUCTURE_COST.get(current, 0)
                if current_cost < expected_cost: # improve terrain
                    if self.my_resources < expected_cost:
                        self.desired_resources = expected_cost
                        self.print(' (DD) -> harvest')
                        return self.harvest()
                    self.print(' (DD) -> improve', expected)
                    return expected, nei.position
                else:
                    self.print('    (XX) -> rejected because current', current, 'is better than expected', expected, 'at', nei.position, nei.dx, nei.dy)
                    self.print('Current', current, 'cost', current_cost)
                    self.print('expected', expected, 'cost', expected_cost)
                    continue

    def castles(self):
        return {pos:MyMunch(pos, terr) for pos, terr in self.world.items() if terr.structure == toe.CASTLE}

    def my_castles(self):
        return {pos:c for pos, c in self.castles().items() if c.owner == toe.MINE}

    def surronding(self, pos, layers=3):
        # Returns a 2 layers circle around the position.
        # Each neighbour will have: position, terrain, distance (manhattan distance)
        #
        #        4 3 2 3 4
        #        3 2 1 2 3
        #        2 1 o 1 3
        #        3 2 1 2 3
        #        4 3 2 3 4
        #
        # If map ends in there, will just not be returned.
        # Result is a list of neighbours, do no depend on ordering.
        nss = []
        _steps = list(range(-layers, layers + 1))
        x, y = pos.x, pos.y
        for dx in _steps:
            _x = x + dx
            if _x < 0 or _x >= self.map_size[0]:
                continue
            for dy in _steps:
                _y = y + dy
                if _y < 0 or _y >= self.map_size[1]:
                    continue
                if dx == 0 and dy == 0:
                    continue
                dist = abs(dx) + abs(dy)
                dpos = Position(_x, _y)
                terrain = self.world[dpos]
                nss.append(Neighbour(dpos, terrain, dist, dx, dy))
        return nss


class BotLogic:
    """
    Bot logic for the Aggressive bot.
    """

    def turn(self, map_size, my_resources, world):

        if not hasattr(self, 'paranoid_mode'):
            self.paranoid_mode = False
        number = getattr(self, 'turn_number', 0)
        desired_resources = getattr(self, 'desired_resources', None)
        prev_castle_count = getattr(self, 'prev_castle_count', 0)

        turn = Turn(number, map_size, my_resources, world, desired_resources, prev_castle_count)

        if getattr(self, 'next', None):
            n = self.next
            self.next = None
            turn.print('FOLLOWING RECOMMENDATION', n)
            return n

        current_castle_count = len(turn.my_castles())
        if prev_castle_count >= 3 and current_castle_count < 3:
            # Loosing castles, 2 remaning
            self.paranoid_mode = True
        elif current_castle_count >= 3:
            self.paranoid_mode = False
        action = turn.action(paranoid_mode=self.paranoid_mode)
        self.turn_number = number + 1
        self.desired_resources = turn.desired_resources
        self.prev_castle_count = len(turn.my_castles())

        self.next = getattr(turn, 'recommend_next', None)

        return action

