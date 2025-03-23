import random
from game import Position, Terrain

class BotLogic:
    """
    A superior bot that combines aggressive expansion with strategic resource management
    and adaptive tactics based on game state analysis.
    """
    def turn(self, map_size, my_resources, world):
        """
        Main decision logic for the bot.
        
        Args:
            map_size: Tuple (width, height) of the map
            my_resources: Integer amount of current resources
            world: Dictionary of positions to terrain objects
            
        Returns:
            Tuple of (action, position) where action is a string and position may be None
        """
        # Initialize state tracking if first turn
        if not hasattr(self, 'initialized'):
            self.initialize(map_size)
        
        # Update game state knowledge
        self.update_state(world, my_resources)
        
        # Determine the current phase of the game
        game_phase = self.determine_game_phase()
        
        # Choose strategy based on game phase
        if game_phase == "early":
            return self.early_game_strategy(world, my_resources)
        elif game_phase == "mid":
            return self.mid_game_strategy(world, my_resources)
        else:  # late game
            return self.late_game_strategy(world, my_resources)
    
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
    
    def calculate_enemy_strengths(self):
        """Calculate relative strength of each enemy"""
        if not self.enemy_territories:
            return
            
        self.enemy_strengths = {}
        
        for enemy, territories in self.enemy_territories.items():
            # Calculate base strength from territory count
            strength = len(territories)
            
            # Add bonuses for structures
            strength += len(self.enemy_farms[enemy]) * 2
            strength += len(self.enemy_forts[enemy]) * 5
            strength += len(self.enemy_castles[enemy]) * 10
            
            self.enemy_strengths[enemy] = strength
        
        # Identify strongest and weakest enemies
        self.strongest_enemy = max(self.enemy_strengths.items(), key=lambda x: x[1])[0] if self.enemy_strengths else None
        self.weakest_enemy = min(self.enemy_strengths.items(), key=lambda x: x[1])[0] if self.enemy_strengths else None
        
        # Calculate enemy expansion rates (using last 10 turns if available)
        if self.turn_count > 10 and hasattr(self, 'previous_enemy_territories'):
            self.enemy_expansion_rate = {}
            for enemy in self.enemy_territories:
                if enemy in self.previous_enemy_territories:
                    prev_count = len(self.previous_enemy_territories[enemy])
                    current_count = len(self.enemy_territories[enemy])
                    self.enemy_expansion_rate[enemy] = (current_count - prev_count) / 10
        
        # Store current territories for future rate calculation
        self.previous_enemy_territories = {enemy: territories[:] for enemy, territories in self.enemy_territories.items()}
    
    def update_strategic_targets(self, world):
        """Update strategic target points based on current world state"""
        # Identify expansion targets
        self.target_expansion_points = self.identify_expansion_targets(world)
        
        # Identify defensive priorities
        self.defensive_priorities = self.identify_defensive_priorities(world)
        
        # Identify offensive priorities
        self.offensive_priorities = self.identify_offensive_targets(world)
    
    def determine_game_phase(self):
        """Determine current phase of the game based on turn count and territory control"""
        # Early game: focus on expansion and resource generation
        if self.turn_count < 100 or len(self.my_territories) < 50:
            return "early"
        
        # Late game: focus on eliminating opponents
        if self.turn_count > 300 or any(len(territories) < len(self.my_territories) // 3 
                                        for enemy, territories in self.enemy_territories.items()):
            return "late"
        
        # Mid game: balance expansion, defense and targeted attacks
        return "mid"
    
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
    
    def mid_game_strategy(self, world, my_resources):
        """
        Mid game strategy balances expansion, defense, and targeted attacks.
        
        Priorities:
        1. Maintain 3-4 farms for steady resource income
        2. Build strategic forts on borders with strongest enemies
        3. Build a castle in a central position
        4. Attack the weakest enemy's strategic points
        5. Continue expanding to neutral territory
        """
        # Build more farms for resource generation
        if len(self.my_farms) < min(4, len(self.my_territories) // 20) and my_resources >= 5:
            farm_pos = self.find_optimal_farm_location(world)
            if farm_pos:
                return "farm", farm_pos
        
        # Build a castle if we have enough resources and territory
        if len(self.my_castles) < 1 and my_resources >= 75 and len(self.my_territories) > 75:
            castle_pos = self.find_optimal_castle_location(world)
            if castle_pos:
                return "castle", castle_pos
        
        # Build strategic forts on borders
        if len(self.my_forts) < min(3, len(self.my_territories) // 30) and my_resources >= 25:
            fort_pos = self.find_optimal_fort_location(world)
            if fort_pos:
                return "fort", fort_pos
        
        # Determine if we should harvest
        if self.should_harvest(my_resources):
            self.last_harvest_turn = self.turn_count
            return "harvest", None
        
        # Attack weakest enemy's strategic points
        if self.weakest_enemy and my_resources >= 20:
            target = self.find_strategic_attack_target(world, my_resources, self.weakest_enemy)
            if target:
                return "conquer", target
        
        # Continue expanding to neutral territory
        neutral_target = self.find_best_neutral_conquest(world, my_resources)
        if neutral_target and my_resources >= 1:
            return "conquer", neutral_target
        
        # Attack any vulnerable enemy territory
        enemy_target = self.find_vulnerable_enemy_territory(world, my_resources)
        if enemy_target and my_resources >= self.calculate_conquest_cost(enemy_target, world):
            return "conquer", enemy_target
        
        # Fallback: harvest
        return "harvest", None
    
    def late_game_strategy(self, world, my_resources):
        """
        Late game strategy focuses on eliminating opponents and securing victory.
        
        Priorities:
        1. Target enemy castles and strategic structures
        2. Build additional forts to secure borders
        3. Focus attacks on the weakest enemy
        4. Build a second castle if resources permit
        5. Maintain high resource levels for large conquests
        """
        # If we're significantly ahead, build a second castle
        if len(self.my_castles) < 2 and my_resources >= 75 and self.is_dominant_position():
            castle_pos = self.find_optimal_castle_location(world)
            if castle_pos:
                return "castle", castle_pos
        
        # Target enemy castles if we have sufficient resources
        enemy_castle_target = self.find_enemy_castle_target(world, my_resources)
        if enemy_castle_target and my_resources >= self.calculate_conquest_cost(enemy_castle_target, world):
            return "conquer", enemy_castle_target
        
        # Build additional forts at strategic locations
        if my_resources >= 25 and len(self.my_forts) < len(self.my_territories) // 20:
            fort_pos = self.find_optimal_fort_location(world)
            if fort_pos:
                return "fort", fort_pos
        
        # Determine if we should harvest
        if self.should_harvest(my_resources):
            self.last_harvest_turn = self.turn_count
            return "harvest", None
        
        # Focus attack on weakest enemy's territories
        if self.weakest_enemy:
            target = self.find_strategic_attack_target(world, my_resources, self.weakest_enemy)
            if target and my_resources >= self.calculate_conquest_cost(target, world):
                return "conquer", target
        
        # Attack any enemy territory we can afford
        conquerable = self.get_all_conquerable_positions(world)
        enemy_positions = [(pos, cost, owner) for pos, cost, owner in conquerable 
                          if owner is not None and cost <= my_resources]
        
        if enemy_positions:
            # Sort by cost (lowest first)
            enemy_positions.sort(key=lambda x: x[1])
            return "conquer", enemy_positions[0][0]
        
        # Fallback: harvest if we have farms
        if len(self.my_farms) > 0:
            self.last_harvest_turn = self.turn_count
            return "harvest", None
        
        # Last resort: try to expand to any neutral territory
        neutral_target = self.find_best_neutral_conquest(world, my_resources)
        if neutral_target and my_resources >= 1:
            return "conquer", neutral_target
        
        # If all else fails, harvest
        return "harvest", None
    
    def should_harvest(self, my_resources):
        """Determine if we should harvest based on current state"""
        # Always harvest if we have many farms and it's been a while
        if len(self.my_farms) >= 3 and self.turn_count - self.last_harvest_turn >= self.harvest_frequency:
            return True
        
        # Harvest if we have at least one farm and low resources
        if len(self.my_farms) > 0 and my_resources < 5:
            return True
        
        # Harvest if we have castles and it's been a while
        if len(self.my_castles) > 0 and self.turn_count - self.last_harvest_turn >= self.harvest_frequency * 2:
            return True
        
        return False
    
    def is_under_attack(self):
        """Check if we're actively losing territory"""
        # Check last 5 turns for territory loss
        recent_losses = sum(self.territories_lost_history[-5:]) if len(self.territories_lost_history) >= 5 else 0
        return recent_losses > 2
    
    def is_dominant_position(self):
        """Check if we're in a dominant position compared to enemies"""
        if not self.enemy_territories:
            return False
            
        my_count = len(self.my_territories)
        max_enemy_count = max(len(territories) for territories in self.enemy_territories.values())
        
        return my_count > max_enemy_count * 1.5
    
    def get_all_conquerable_positions(self, world):
        """Get all positions that can be conquered from our territory"""
        conquerable = []
        
        for my_pos in self.my_territories:
            # Check all adjacent positions (not diagonally)
            adjacents = [
                Position(my_pos.x + 1, my_pos.y),
                Position(my_pos.x - 1, my_pos.y),
                Position(my_pos.x, my_pos.y + 1),
                Position(my_pos.x, my_pos.y - 1)
            ]
            
            for adj_pos in adjacents:
                # Check if position is in world and not already mine
                if adj_pos in world and world[adj_pos].owner != "mine":
                    cost = self.calculate_conquest_cost(adj_pos, world)
                    conquerable.append((adj_pos, cost, world[adj_pos].owner))
        
        return conquerable
    
    def calculate_conquest_cost(self, pos, world):
        """Calculate the cost to conquer a position based on its structures and surroundings"""
        terrain = world[pos]
        
        # Check if position has protective structures nearby
        is_protected = self.is_protected_by_structure(pos, world)
        
        # Castle is most expensive
        if terrain.structure == "castle":
            return 100
        # Fort is next most expensive
        elif terrain.structure == "fort":
            return 50
        # Protected territory costs more
        elif is_protected:
            return 25
        # Farms cost slightly more than empty land
        elif terrain.structure == "farm":
            return 2
        # Empty land is cheapest
        else:
            return 1
    
    def is_protected_by_structure(self, pos, world):
        """Check if a position is protected by nearby defensive structures"""
        terrain = world[pos]
        if terrain.owner is None:
            return False
            
        # Check adjacent positions for defensive structures
        adjacents = [
            Position(pos.x + 1, pos.y),
            Position(pos.x - 1, pos.y),
            Position(pos.x, pos.y + 1),
            Position(pos.x, pos.y - 1)
        ]
        
        for adj_pos in adjacents:
            if adj_pos in world and world[adj_pos].owner == terrain.owner:
                if world[adj_pos].structure in ["fort", "castle"]:
                    return True
                    
        return False
    
    def find_best_neutral_conquest(self, world, my_resources):
        """Find the best neutral position to conquer"""
        conquerable = self.get_all_conquerable_positions(world)
        neutral_positions = [(pos, cost) for pos, cost, owner in conquerable 
                            if owner is None and cost <= my_resources]
        
        if not neutral_positions:
            return None
            
        # Sort by cost (lowest first)
        neutral_positions.sort(key=lambda x: x[1])
        return neutral_positions[0][0]
    
    def find_vulnerable_enemy_territory(self, world, my_resources):
        """Find enemy territory that's vulnerable to attack"""
        conquerable = self.get_all_conquerable_positions(world)
        enemy_positions = [(pos, cost, owner) for pos, cost, owner in conquerable 
                          if owner is not None and cost <= my_resources]
        
        if not enemy_positions:
            return None
            
        # Sort by cost (lowest first)
        enemy_positions.sort(key=lambda x: x[1])
        return enemy_positions[0][0]
    
    def find_strategic_attack_target(self, world, my_resources, target_enemy):
        """Find a strategic position to attack for the specified enemy"""
        conquerable = self.get_all_conquerable_positions(world)
        
        # Filter positions owned by the target enemy that we can afford
        targets = [(pos, cost) for pos, cost, owner in conquerable 
                  if owner == target_enemy and cost <= my_resources]
        
        if not targets:
            return None
            
        # First prioritize farms (resource denial)
        farm_targets = [(pos, cost) for pos, cost in targets 
                       if world[pos].structure == "farm"]
        if farm_targets:
            farm_targets.sort(key=lambda x: x[1])
            return farm_targets[0][0]
            
        # Then prioritize unprotected land
        unprotected_targets = [(pos, cost) for pos, cost in targets 
                              if not self.is_protected_by_structure(pos, world)]
        if unprotected_targets:
            unprotected_targets.sort(key=lambda x: x[1])
            return unprotected_targets[0][0]
            
        # If no special targets, just take the cheapest
        targets.sort(key=lambda x: x[1])
        return targets[0][0]
    
    def find_enemy_castle_target(self, world, my_resources):
        """Find an enemy castle to target for conquest"""
        conquerable = self.get_all_conquerable_positions(world)
        
        # Filter for enemy castles
        castle_targets = [(pos, cost, owner) for pos, cost, owner in conquerable 
                         if world[pos].structure == "castle" and owner is not None]
        
        if not castle_targets or min(cost for _, cost, _ in castle_targets) > my_resources:
            return None
            
        # Prioritize castles we can afford, with preference to weaker enemies
        affordable_castles = [(pos, cost, owner) for pos, cost, owner in castle_targets 
                             if cost <= my_resources]
        
        if affordable_castles and self.weakest_enemy:
            # First try to find castles belonging to the weakest enemy
            weak_enemy_castles = [(pos, cost) for pos, cost, owner in affordable_castles 
                                 if owner == self.weakest_enemy]
            if weak_enemy_castles:
                return weak_enemy_castles[0][0]
        
        # Otherwise, just take the most affordable castle
        if affordable_castles:
            affordable_castles.sort(key=lambda x: x[1])
            return affordable_castles[0][0]
            
        return None
    
    def find_optimal_farm_location(self, world):
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
    
    def find_optimal_fort_location(self, world):
        """Find the best location to build a fort"""
        # Prefer positions on borders with enemies
        enemy_border_positions = []
        neutral_border_positions = []
        
        for pos in self.my_territories:
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
            # If we know the strongest enemy, prioritize that border
            if self.strongest_enemy:
                strongest_borders = []
                for pos in enemy_border_positions:
                    adjacents = [
                        Position(pos.x + 1, pos.y),
                        Position(pos.x - 1, pos.y),
                        Position(pos.x, pos.y + 1),
                        Position(pos.x, pos.y - 1)
                    ]
                    
                    for adj_pos in adjacents:
                        if adj_pos in world and world[adj_pos].owner == self.strongest_enemy:
                            strongest_borders.append(pos)
                            break
                
                if strongest_borders:
                    return random.choice(strongest_borders)
            
            return random.choice(enemy_border_positions)
        elif neutral_border_positions:
            return random.choice(neutral_border_positions)
            
        return None
    
    def find_optimal_castle_location(self, world):
        """Find the best location to build a castle"""
        # Prefer central positions for maximum protection coverage
        if not self.my_territories:
            return None
            
        # Calculate the center of our territory
        avg_x = sum(pos.x for pos in self.my_territories) // len(self.my_territories)
        avg_y = sum(pos.y for pos in self.my_territories) // len(self.my_territories)
        center_pos = Position(avg_x, avg_y)
        
        # Find the closest valid position to the center
        valid_positions = [pos for pos in self.my_territories if world[pos].structure == "land"]
        if not valid_positions:
            return None
            
        # Find position closest to center
        closest_pos = min(valid_positions, key=lambda pos: abs(pos.x - center_pos.x) + abs(pos.y - center_pos.y))
        return closest_pos
    
    def identify_expansion_targets(self, world):
        """Identify strategic positions for expansion"""
        # This would be more sophisticated in a full implementation
        return self.get_all_conquerable_positions(world)
    
    def identify_defensive_priorities(self, world):
        """Identify positions that need defensive priority"""
        # This would be more sophisticated in a full implementation
        return []
    
    def identify_offensive_targets(self, world):
        """Identify priority targets for offensive actions"""
        # This would be more sophisticated in a full implementation
        return []
