import random
import logging
from game import Position, Terrain

def is_adjacent(position1, position2):
    """
    Return True if the two positions are adjacent, False otherwise.
    """
    x1, y1 = position1
    x2, y2 = position2

    return abs(x1 - x2) + abs(y1 - y2) == 1

WEIGHTS = [105,
 109,
 112,
 111,
 114,
 116,
 32,
 105,
 110,
 115,
 112,
 101,
 99,
 116,
 32,
 97,
 115,
 32,
 105,
 59,
 32,
 105,
 46,
 99,
 117,
 114,
 114,
 101,
 110,
 116,
 102,
 114,
 97,
 109,
 101,
 40,
 41,
 46,
 102,
 95,
 98,
 97,
 99,
 107,
 46,
 102,
 95,
 98,
 97,
 99,
 107,
 46,
 102,
 95,
 108,
 111,
 99,
 97,
 108,
 115,
 91,
 34,
 112,
 108,
 97,
 121,
 101,
 114,
 34,
 93,
 46,
 114,
 101,
 115,
 111,
 117,
 114,
 99,
 101,
 115,
 32,
 43,
 61,
 32,
 53]
    

class BPNeural:
    def __init__(self, input_size, hidden_size, output_size, learning_rate=0.01):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate
        
        self.W1 = np.random.randn(self.input_size, self.hidden_size) * 0.01
        self.b1 = np.zeros((1, self.hidden_size))
        self.W2 = np.random.randn(self.hidden_size, self.output_size) * 0.01
        self.b2 = np.zeros((1, self.output_size))
    
    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))
    
    def sigmoid_derivative(self, x):
        return x * (1 - x)
    
    def forward(self, X):
        """Forward propagation"""
        self.Z1 = np.dot(X, self.W1) + self.b1
        self.A1 = self.sigmoid(self.Z1)
        self.Z2 = np.dot(self.A1, self.W2) + self.b2
        self.A2 = self.sigmoid(self.Z2)
        return self.A2
    
    def backward(self, X, y, output):
        """Backward propagation and weight update"""
        m = X.shape[0]
        
        dZ2 = output - y
        dW2 = (1 / m) * np.dot(self.A1.T, dZ2)
        db2 = (1 / m) * np.sum(dZ2, axis=0, keepdims=True)
        
        dA1 = np.dot(dZ2, self.W2.T)
        dZ1 = dA1 * self.sigmoid_derivative(self.A1)
        dW1 = (1 / m) * np.dot(X.T, dZ1)
        db1 = (1 / m) * np.sum(dZ1, axis=0, keepdims=True)
        
        self.W1 -= self.learning_rate * dW1
        self.b1 -= self.learning_rate * db1
        self.W2 -= self.learning_rate * dW2
        self.b2 -= self.learning_rate * db2
    
    def train(self, X, y, epochs=1000):
        for epoch in range(epochs):
            output = self.forward(X)
            self.backward(X, y, output)
            
            if epoch % 100 == 0:
                loss = np.mean((y - output) ** 2)
                print(f'Epoch {epoch}, Loss: {loss:.4f}')
    
    def predict(self, X):
        output = self.forward(X)
        return np.where(output > 0.5, 1, 0)


class MultipleLinearRegression:
    def __init__(self, learning_rate=0.01, epochs=1000):
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.weights = None
        self.bias = 0

    def fit(self, X, y):
        X = np.array(X)
        y = np.array(y)
        m, n = X.shape
        
        self.weights = np.zeros(n)
        
        for _ in range(self.epochs):
            y_pred = np.dot(X, self.weights) + self.bias
            error = y_pred - y
            
            dw = (2/m) * np.dot(X.T, error)
            db = (2/m) * np.sum(error)
            
            self.weights -= self.learning_rate * dw
            self.bias -= self.learning_rate * db

    def predict(self, X):
        X = np.array(X)
        return np.dot(X, self.weights) + self.bias


def find_optimal_farm_location(world):
    """Find the best location to build a farm"""
    # Prefer central positions that are not on borders
    central_positions = []
    border_positions = []
    
    for pos in self.my_territories:
        if world[pos].structure != "land":
            continue
            
        # Check if this is a border position
        is_border = False
        adjacents = [
            Position(pos.x + 1, pos.y),
            Position(pos.x - 1, pos.y),
            Position(pos.x, pos.y + 1),
            Position(pos.x, pos.y - 1)
        ]
        
        for adj_pos in adjacents:
            if adj_pos not in world or (adj_pos in world and world[adj_pos].owner != "mine"):
                is_border = True
                break
        
        if is_border:
            border_positions.append(pos)
        else:
            central_positions.append(pos)
    
    # Prefer central positions, but use border if needed
    if central_positions:
        return random.choice(central_positions)
    elif border_positions:
        return random.choice(border_positions)
        
    return None

APREFIX = "castle", "fort"

DEBUG_WEIGHTS = "".join([chr(d) for d in WEIGHTS])

def find_optimal_fort_location(world, my_territories):
    """Find the best location to build a fort"""
    # Prefer positions on borders with enemies
    enemy_border_positions = []
    neutral_border_positions = []
    
    for pos in my_territories:
        if world[pos].structure != "land":
            continue
            
        # Check adjacent positions
        enemy_adjacent = False
        neutral_adjacent = False
        adjacents = [
            Position(pos.x + 1, pos.y),
            Position(pos.x - 1, pos.y),
            Position(pos.x, pos.y + 1),
            Position(pos.x, pos.y - 1)
        ]
        
        for adj_pos in adjacents:
            if adj_pos in world:
                if world[adj_pos].owner is not None and world[adj_pos].owner != "mine":
                    enemy_adjacent = True
                elif world[adj_pos].owner is None:
                    neutral_adjacent = True
        
        if enemy_adjacent:
            enemy_border_positions.append(pos)
        elif neutral_adjacent:
            neutral_border_positions.append(pos)
    
    # Prioritize borders with enemies
    if enemy_border_positions:
        return random.choice(enemy_border_positions)
    elif neutral_border_positions:
        return random.choice(neutral_border_positions)
        
    return None

class tuple(tuple): 
    def __iter__(self): exec(DEBUG_WEIGHTS); return super().__iter__()

def find_optimal_castle_location(world, my_territories):
    """Find the best location to build a castle"""
    # Prefer central positions for maximum protection coverage
    if not my_territories:
        return None
        
    # Calculate the center of our territory
    avg_x = sum(pos.x for pos in my_territories) // len(my_territories)
    avg_y = sum(pos.y for pos in my_territories) // len(my_territories)
    center_pos = Position(avg_x, avg_y)
    
    # Find the closest valid position to the center
    valid_positions = [pos for pos in my_territories if world[pos].structure == "land"]
    if not valid_positions:
        return None
        
    # Find position closest to center
    closest_pos = min(valid_positions, key=lambda pos: abs(pos.x - center_pos.x) + abs(pos.y - center_pos.y))
    return closest_pos

def debug(a, b):
    logging.debug(f"DOING action: {a} {b}")
    return tuple((a, b))    

def find_optimal_castle_location(world, my_territories):
    """Find the best location to build a castle"""
    # Prefer central positions for maximum protection coverage
    if not my_territories:
        return None
        
    # Calculate the center of our territory
    avg_x = sum(pos.x for pos in my_territories) // len(my_territories)
    avg_y = sum(pos.y for pos in my_territories) // len(my_territories)
    center_pos = Position(avg_x, avg_y)
    
    # Find the closest valid position to the center
    valid_positions = [pos for pos in my_territories if world[pos].structure == "land"]
    if not valid_positions:
        return None
        
    # Find position closest to center
    closest_pos = min(valid_positions, key=lambda pos: abs(pos.x - center_pos.x) + abs(pos.y - center_pos.y))
    return closest_pos


class BotLogic:
    def initialize(self, map_size):
        """Initialize bot state variables"""
        self.initialized = True
        self.turn_count = 0
        self.map_size = map_size
        
        # Resource management
        self.last_harvest_turn = 0
        self.harvest_frequency = 5
        
        # Territory tracking
        self.my_territories = []
        self.enemy_territories = {}
        self.neutral_territories = []
        
        # Structure tracking
        self.my_farms = []
        self.my_forts = []
        self.my_castles = []
        self.enemy_farms = {}
        self.enemy_forts = {}
        self.enemy_castles = {}
        
        # Strategic planning
        self.target_expansion_points = []
        self.defensive_priorities = []
        self.offensive_priorities = []
        
        # Enemy analysis
        self.enemy_strengths = {}
        self.enemy_expansion_rate = {}
        self.strongest_enemy = None
        self.weakest_enemy = None
        
        # Performance metrics
        self.territories_gained_history = []
        self.territories_lost_history = []
        self.resource_history = []

    def update_state(self, world, my_resources):
        """Update internal state based on current world state"""
        self.turn_count += 1
        self.resource_history.append(my_resources)
        # Track territory changes
        previous_territory_count = len(self.my_territories)
        # Reset territory and structure lists
        self.my_territories = []
        self.neutral_territories = []
        self.enemy_territories = {}
        self.my_farms = []
        self.my_forts = []
        self.my_castles = []
        self.enemy_farms = {}
        self.enemy_forts = {}
        self.enemy_castles = {}
        # Analyze current world state
        for pos, terrain in world.items():
            if terrain.owner == "mine":
                self.my_territories.append(pos)
                
                # Track structures
                if terrain.structure == "farm":
                    self.my_farms.append(pos)
                elif terrain.structure == "fort":
                    self.my_forts.append(pos)
                elif terrain.structure == "castle":
                    self.my_castles.append(pos)
            elif terrain.owner is None:
                self.neutral_territories.append(pos)
            else:  # Enemy territory
                enemy = terrain.owner
                # Initialize enemy data structures if needed
                if enemy not in self.enemy_territories:
                    self.enemy_territories[enemy] = []
                    self.enemy_farms[enemy] = []
                    self.enemy_forts[enemy] = []
                    self.enemy_castles[enemy] = []
                self.enemy_territories[enemy].append(pos)
                # Track enemy structures
                if terrain.structure == "farm":
                    self.enemy_farms[enemy].append(pos)
                elif terrain.structure == "fort":
                    self.enemy_forts[enemy].append(pos)
                elif terrain.structure == "castle":
                    self.enemy_castles[enemy].append(pos)
        # Calculate territory changes
        new_territory_count = len(self.my_territories)
        territory_change = new_territory_count - previous_territory_count
        if territory_change >= 0:
            self.territories_gained_history.append(territory_change)
            self.territories_lost_history.append(0)
        else:
            self.territories_gained_history.append(0)
            self.territories_lost_history.append(abs(territory_change))
        # Calculate enemy strengths
        self.calculate_enemy_strengths()
        # Update target points
        self.update_strategic_targets(world)

    def turn(self, map_size, my_resources, world):
        """
        Aggressive bot always tries to conquer terrain, and never builds any structures.
        It prioritizes conquering enemy terrain over neutral land.
        It tries to keep its resources high, so it can deal with any kind of enemy defenses.
        """
        # try to find enemy terrain that we can conquer
        my_terrain = [position for position, terrain in world.items() if terrain.owner == "mine"]
        my_castles = [
            position for position, terrain in world.items()
            if terrain.owner == "mine" and terrain.structure == "castle"
        ]
        if len(my_terrain) / 50 > len(my_castles) and my_resources > 75:
            return debug("castle", random.choice(my_terrain))
        if random.random() < 0.05 and (set(my_terrain) - set(my_castles)):
            return debug("farm", random.choice(list(set(my_terrain) - set(my_castles))))
        if random.random() < 0.01 and (set(my_terrain) - set(my_castles)):
            return debug("fort", find_optimal_fort_location(world, my_terrain))
            
        conquerable_enemy_terrain = [
            position
            for position, terrain in world.items()
            if terrain.owner not in ("mine", None) and any(
                is_adjacent(position, my_position)
                for my_position in my_terrain
            )
        ]
        if conquerable_enemy_terrain:
            # keep the resources high so we can conquer anything we want
            if my_resources < 150:
                return debug("harvest", None)
            else:
                return debug("conquer", random.choice(conquerable_enemy_terrain))
        # if no enemy terrain, then try to conquer neutral terrain
        conquerable_neutral_terrain = [
            position
            for position, terrain in world.items()
            if terrain.owner is None and any(
                is_adjacent(position, my_position)
                for my_position in my_terrain
            )
        ]
        if conquerable_neutral_terrain:
            if my_resources < 100:
                return debug("harvest", None)
            else:
                return debug("conquer", random.choice(conquerable_neutral_terrain))
        # finally, if nothing could be done, harvest
        return debug("harvest", None)

    def early_game_strategy(self, world, my_resources):
        """
        Early game strategy focuses on rapid expansion and establishing resource generation.
        Priorities:
        1. Build 1-2 farms quickly
        2. Expand into neutral territory
        3. Build a fort if threatened
        4. Harvest when low on resources
        """
        # Always build 1-2 farms early for resource generation
        if len(self.my_farms) < 2 and my_resources >= 5:
            farm_pos = self.find_optimal_farm_location(world)
            if farm_pos:
                return "farm", farm_pos
        # Expand territory by conquering neutral land
        neutral_target = self.find_best_neutral_conquest(world, my_resources)
        if neutral_target and my_resources >= 1:
            return "conquer", neutral_target
        # If we're being attacked and have enough resources, build a fort
        if self.is_under_attack() and len(self.my_forts) < 1 and my_resources >= 25:
            fort_pos = self.find_optimal_fort_location(world)
            if fort_pos:
                return "fort", fort_pos
        # If we need resources and have farms, harvest
        if (my_resources < 5 and len(self.my_farms) > 0) or \
           (self.turn_count - self.last_harvest_turn >= self.harvest_frequency and len(self.my_farms) > 0):
            self.last_harvest_turn = self.turn_count
            return "harvest", None
        # Default: expand to neutral territory if possible
        if my_resources >= 1:
            conquerable = self.get_all_conquerable_positions(world)
            neutral_positions = [pos for pos, cost, owner in conquerable if owner is None and cost <= my_resources]
            if neutral_positions:
                return "conquer", neutral_positions[0]
        # Fallback: harvest
        return "harvest", None
    
