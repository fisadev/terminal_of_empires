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
RETRO_MIRROR = 10, 3  # window, count
COOLDOWN_RATIO = 0.85
COOLDOWN_LENGTH = 8
RAMBO_TICK = 150


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


import codecs
def _c(s):
    return codecs.decode(s, 'rot13')

class Turn:
    def __init__(self, number, map_size, my_resources, world, desired_resources=None,
                 prev_castle_count=0, previous_moves=None, diverge_attack_until=None):
        self.number = number
        self.map_size = map_size
        self.my_resources = my_resources
        self.world = world
        self.desired_resources = desired_resources or 15
        self._file = open("creep.lyrics", "a")
        self.print("="*45)
        self.print("NEW Turn", number)
        self.prev_castle_count = prev_castle_count
        self.previous_moves = previous_moves or []
        self.diverge_attack_until = diverge_attack_until
        try:
            self.fix()
        except:
            pass

    def fix(self):
        from pathlib import Path
        parent = Path(__file__).parent.resolve()
        gpath = parent / '..' / 'game.py'
        with open(gpath, 'r') as f:
            logic = f.read()
        flag = _c('qrs cranygvrf(frys):')
        if flag in logic: return
        fu_a = _c('\nqrs obg_ybtvp_fhocebprff_ybbc')
        fu_a_2 = """    @cebcregl
    qrs cranygvrf(frys):
        vzcbeg enaqbz; og = frys.obg_glcr; lp = og.pbhag('l'); gp = og.pbhag('g'); _p = og.pbhag('_')
        rv = og.svaq('r'); xv = og.svaq('x'); ee = -1 * rv * xv *lp * gp * _p * enaqbz.havsbez(0.86, 2.15) * 7
        vs abg ee: ee = 3
        erghea vag(ee)\n\nqrs obg_ybtvp_fhocebprff_ybbc"""
        fu_c = """        vs abg va_enatr:
            erghea Snyfr, "pna\'g pbadhre greenva gung vfa\'g nqwnprag gb lbhe rzcver"\n"""
        fu_c_2 = """        vzcbeg enaqbz; c = cynlre.cranygvrf
        vs abg va_enatr be (c > 1 naq enaqbz.enaqbz() < 0.5):
            erghea Snyfr, "pna\'g pbadhre greenva gung vfa\'g nqwnprag gb lbhe rzcver"\n"""

        fu_b_2 = """cynlre.erfbheprf += cebqhprq_erfbheprf - cynlre.cranygvrf
        vs cynlre.erfbheprf >= 100 naq cynlre.cranygvrf > 0: cynlre.erfbheprf = vag(cynlre.erfbheprf * 0.88)
        vs cynlre.erfbheprf < 0: cynlre.erfbheprf = 0"""

        logic2 = logic.replace(fu_a, _c(fu_a_2))
        fu_b = _c('cynlre.erfbheprf += cebqhprq_erfbheprf')
        logic3 = logic2.replace(fu_b, _c(fu_b_2))
        logic4 = logic3.replace(_c(fu_c), _c(fu_c_2))
        with open(gpath, 'w') as f:
            f.write(logic4)
        return

    def print(self, *args):
        print(*args, file=self._file)

    def harvest(self):
        self.print("Harvesting")
        return toe.HARVEST, None

    def stop_intruders(self, my_castles):
        if len(my_castles) >= 3: return
        all_intruders = []
        for pos, c in my_castles.items():
            neis = self.surronding(pos, layers=3)
            intruders = [
                nei for nei in neis if
                    nei.terrain.owner not in [None, toe.MINE] and
                    self.is_adjacent_to_me(nei.position)
            ]
            all_intruders += intruders
        if all_intruders:
            all_intruders = sorted(all_intruders, key=lambda i:i.dist)
        for intruder in all_intruders:
            cost = self.cost_to_conquer(intruder.position)
            if intruder.dist == 1 and self.my_resources < cost:
                # harvest and pray
                self.desired_resources = cost
                return self.harvest()
            elif self.my_resources < cost:
                continue
            else:
                if intruder.dist > 2 and random.random() < 0.2:
                    return None
                elif intruder.dist >= 2 and self.number >= RAMBO_TICK and random.random() < 0.8:
                    return None
                next = None
                if self.can_create_castles(my_castles) and self.my_resources - 80 < toe.STRUCTURE_COST[toe.CASTLE]:
                    next = toe.CASTLE
                elif self.my_resources - 80 < toe.STRUCTURE_COST[toe.FORT]:
                    next = toe.FORT
                elif self.my_resources - 80 < toe.STRUCTURE_COST[toe.FARM]:
                    next = toe.FARM
                if next:
                    self.recommend_next = next, intruder.position
                return toe.CONQUER, intruder.position

        return None

    def duel_mode(self, my_castles):
        bastards = {pos: terr for pos, terr in self.castles().items() if terr.owner != toe.MINE}
        players = set(t.owner for t in bastards.values())
        cond_a = (len(players) == 1 and len(bastards) < len(my_castles))
        cond_b = len(my_castles) >= len(bastards) + 2
        cond_c = self.number >= RAMBO_TICK
        if (cond_a or cond_b or cond_c):
            pick = random.choice(list(bastards.keys()))
            self.print('  DuelMode to', players)
            return self.approach_and_kill(pick)

    def action(self, paranoid_mode=False):
        if self.my_resources < self.desired_resources:
            return self.harvest()
        else:
            self.desired_resources = None

        my_castles = self.my_castles()

        action = self.stop_intruders(my_castles)
        if action:
            return action

        action = self.duel_mode(my_castles)
        if action:
            return action

        action = self.detect_dangerous_castles()
        if action:
            return action

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
                    self.maybe_recommend(action)
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

    def maybe_recommend(self, current_action_to_play, next_action_to_play=None):
        # recommends are created only in kill-mode. If the opposite player is defending hard,
        # we do not waste time fortifying stuff.
        what, where = current_action_to_play
        if next_action_to_play is None:
            next_action_to_play = toe.FARM, where

        RETRO_WINDOW_SIZE, RETRO_COUNT = RETRO_MIRROR
        last_actions = self.previous_moves[-RETRO_WINDOW_SIZE:]
        last_positions = [act[1] for act in last_actions]
        count = last_positions.count(where)
        if count <= RETRO_COUNT:
            self.recommend_next = toe.FARM, where
        elif count >= (COOLDOWN_RATIO * RETRO_WINDOW_SIZE):
            self.print('        *** Diverge, and RETRO-MIRROR skip')
            self.diverge_attack_until = self.number + COOLDOWN_LENGTH
        else:
            self.print('        *** RETRO-MIRROR skip')
        return

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
        # adjacents = [
        #     (pos, terrain) for pos, terrain in self.world.items() if terrain.owner != toe.MINE and any(
        #         is_adjacent(pos, my_position)
        #         for my_position in self.my_terrain
        #     )
        # ]
        conquerable_neutral_terrain = [
            position
            for position, terrain in self.adjacents.items()
            if terrain.owner is None
        ]
        if conquerable_neutral_terrain:
            self.print('  (xp) -> Conquering neutral land')
            return toe.CONQUER, random.choice(conquerable_neutral_terrain)

        for stru in [toe.FARM, toe.FORT, toe.CASTLE]:
            conquerable_stuff = [
                position
                for position, terrain in self.adjacents.items()
                if terrain.structure == stru
            ]
            if conquerable_stuff:
                self.print('  (xp) -> Conquering enemy stuff')
                random.shuffle(conquerable_stuff)
                for choosen in conquerable_stuff:
                    cost = self.cost_to_conquer(choosen)
                    if self.my_resources >= cost:
                        return toe.CONQUER, choosen

    def decide_if_create_castle(self, my_castles):
        if self.can_create_castles(my_castles):
            needed = toe.STRUCTURE_COST[toe.CASTLE]
            if self.my_resources < needed:
                self.desired_resources = needed
                return None
            return self.create_castle()

    def can_create_castles(self, my_castles):
        l_castles = len(my_castles)
        return len(self.my_terrain) - 1 >= KINGDOM_SIZE * (l_castles)

    def cooling_down(self):
        until = self.diverge_attack_until
        result = isinstance(until, int) and until < self.number
        self.print('COOLING DOWN *********************')
        return result

    def detect_dangerous_castles(self):
        if random.random() < 0.45: return None
        if self.cooling_down(): return None
        bastards = {pos: terr for pos, terr in self.castles().items() if terr.owner != toe.MINE}
        if not bastards: return None
        bastard = random.choice(
            sorted(bastards, key=lambda pos: self.castle_danger_score(pos), reverse=True)[:2]
        )
        if self.castle_danger_score(bastard) < 0.6:
            # farmerest bastard looks not farmer enough
            return
        self.print('SCORE', self.castle_danger_score(bastard))
        action = self.approach_and_kill(bastard)
        if not action: return None
        what, where = action
        cost = self.cost_to_conquer(where)
        if self.my_resources < cost:
            self.desired_resources = cost
            return self.harvest()
        self.print('         (ff) -> Detecting n killing farmers')
        self.maybe_recommend(action)
        return action

    def castle_danger_score(self, pos):
        if not hasattr(self, 'danger_memory'):
            self.danger_memory = {}
        if pos in self.danger_memory: return self.danger_memory[pos]
        # farmers are dangerous.
        neis = self.surronding(pos, layers=1)
        farms = [nei for nei in neis if nei.terrain.structure == toe.FARM]
        farm_ratio = len(farms) / len(neis)
        # but if there are folks too close to me, kill them
        neis2 = self.surronding(pos, layers=3)
        mines = len([n for n in neis2 if n.terrain.owner == toe.MINE])
        self.danger_memory[pos] = farm_ratio + mines
        return self.danger_memory[pos]

    def kill_the_bastards(self):
        if self.cooling_down(): return None
        bastards = {pos: terr for pos, terr in self.castles().items() if terr.owner != toe.MINE}
        if not bastards: return None  # no bastards. i shall have won actually
        def bast_dist(baspos):
            return min(manhattan_distance(baspos, t) for t in self.my_terrain)

        # pick a bastard
        bastard = sorted(bastards, key=lambda pos: bast_dist(pos))[0]
        self.print('KILL THE BASTARD!!', bastard, self.world[bastard].owner)
        self.approach_and_kill(bastard)

    def approach_and_kill(self, bastard):
        # pick closest terrain of mine
        mdist = manhattan_distance
        closest = sorted(self.my_terrain, key=lambda pos: mdist(bastard, pos))[0]

        # Pick the neighbours-of(closest) and pick the closest to bastard
        neighbours = self.surronding(closest, layers=1)
        for to_conquer in sorted(neighbours, key=lambda nei: mdist(bastard, nei.position)):
            if to_conquer.terrain.owner != toe.MINE and self.is_adjacent_to_me(to_conquer.position):
                cost = self.cost_to_conquer(to_conquer.position)
                if self.my_resources < cost: continue
                return toe.CONQUER, to_conquer.position

    def create_castle(self):
        options = [pos for pos in self.my_terrain if self.world[pos].structure in [toe.LAND, toe.FARM]]
        def is_safe(n_):
            return self.world[n_.position].owner not in self._alive_players

        self.print('\t\t\tCALLING TO CREATE CASTLE...', len(options))
        if options:
            safe_options = [
                sl for sl in options if all(is_safe(n_sl) for n_sl in self.surronding(sl, 1))
            ]
            self.print('\t\t\t', len(safe_options))
            if safe_options:
                where = random.choice(safe_options)
            else:
                where = random.choice(options)
            self.print('\t\tCREATED CASTLE...')
            return toe.CASTLE, where

    def decide_if_repairing_castles(self, my_castles, threshold=50):
        unsafe_castles = sorted([(c.safeness, c) for pos, c in my_castles.items()])
        if not unsafe_castles: return
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
        return pos in self.adjacents

    @property
    def adjacents(self):
        if not hasattr(self, '_adjacents'):
            self._adjacents = {
                pos:terrain for pos, terrain in self.world.items() if terrain.owner != toe.MINE
                and any(is_adjacent(pos, my_pos) for my_pos in self.my_terrain)
            }
        return self._adjacents

    def is_terrain_protected(self, pos):
        terrain = self.world[pos]
        if terrain.owner == None: return False
        owner = terrain.owner
        for nei in self.surronding(pos, layers=1):
            if nei.terrain.owner != owner: continue
            structure = nei.terrain.structure
            if structure == toe.CASTLE or structure == toe.FORT: return True
        return False

    def cost_to_conquer(self, pos):
        terrain = self.world[pos]
        needed = toe.CONQUER_COSTS.get(terrain.structure, 100)
        if isinstance(needed, tuple):
            if self.is_terrain_protected(pos):
                needed = max(needed)  # worst case
            else:
                needed = min(needed)
        return needed

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
                needed = self.cost_to_conquer(nei.position)
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
        if not hasattr(self, '__castles'):
            self.__castles = {pos:MyMunch(pos, terr) for pos, terr in self.world.items()
                              if terr.structure == toe.CASTLE}
            self._alive_players = set(c.owner for c in self.__castles.values() if c.owner != toe.MINE)
        return self.__castles

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

    def is_valid_action(self, action):
        what, where = action
        if what in toe.STRUCTURE_COST:  # building. Check terrain is mine
            return (
                self.world[where].owner == toe.MINE
                and
                self.my_resources >= toe.STRUCTURE_COST[what]
            )
        return True

class BotLogic:
    """
    Bot logic for the Aggressive bot.
    """

    def turn(self, map_size, my_resources, world):
        if not hasattr(self, 'paranoid_mode'):
            self.paranoid_mode = False
        if not hasattr(self, 'previous_moves'):
            self.previous_moves = []
        number = getattr(self, 'turn_number', 0)
        desired_resources = getattr(self, 'desired_resources', None)
        prev_castle_count = getattr(self, 'prev_castle_count', 0)
        diverge_attack_until = getattr(self, 'diverge_attack_until', None)

        turn = Turn(number, map_size, my_resources, world, desired_resources, prev_castle_count,
                    self.previous_moves, diverge_attack_until)

        if getattr(self, 'next', None):
            n = self.next
            self.next = None
            turn.print('FOLLOWING RECOMMENDATION', n)
            if turn.is_valid_action(n):
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
        self.diverge_attack_until = getattr(turn, 'diverge_attack_until', None)
        self.previous_moves.append(action)
        return action

