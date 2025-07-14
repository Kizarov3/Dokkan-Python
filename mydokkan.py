import os
import random
import time  # Added for Dokkan mini-game
from enum import Enum

# --- ENUMERATIONS (Consolidated) ---
class Attribute(Enum):
    STR = "STR (Red)"
    AGL = "AGL (Blue)"
    TEQ = "TEQ (Green)"
    INT = "INT (Purple)"
    PHY = "PHY (Orange)"
    RAINBOW = "RAINBOW"

class EvasionLevel(Enum):
    NONE = 0
    RARE = 20
    MEDIUM = 30
    HIGH = 50
    GREAT = 70

class StatusEffect(Enum):
    ATK_DOWN = "ATK Down"; DEF_UP = "DEF Up"; IMMUNITY = "Immunity"; DAMAGE_CAP = "Damage Cap"
    NULLIFY_SUPER_SEAL = "Nullify Super Seal"; NULLIFY_STUN = "Nullify Stun"; NULLIFY_ATK_DOWN = "Nullify ATK Down"
    STUN = "Stun"; ATK_UP = "ATK Up"; CRITICAL_HIT = "Critical Hit"; DAMAGE_REDUCTION = "Damage Reduction"
    EFFECTIVE_ALL = "Effective Against All Types"; DOMAIN = "Domain Active"; OMNIPRESENT = "Omnipresent"

class Category(Enum):
    WORLDWIDE_CHAOS = "Worldwide Chaos"; POTARA = "Potara"; REALM_OF_GODS = "Realm of Gods"
    FUSED_FIGHTERS = "Fused Fighters"; TIME_TRAVELERS = "Time Travelers"
    FINAL_TRUMP_CARD = "Final Trump Card"; FUTURE_SAGA = "Future Saga"
    SUPER_BOSSES = "Super Bosses"; CORRODED_BODY = "Corroded Body and Mind"
    ACCELERATED_BATTLE = "Accelerated Battle"; EXPLODING_RAGE = "Exploding Rage"

class SupportItem(Enum):
    GHOST_USHER = "Ghost Usher"; ANDROID_8 = "Android #8"
    PRINCESS_SNAKE = "Princess Snake"; WHIS = "Whis"

class LinkSkillEffect(Enum):
    KI = "Ki"
    ATK_PERCENT = "ATK %"
    DEF_PERCENT = "DEF %"
    EVASION = "Evasion"

LINK_SKILL_DATABASE = {
    "Fierce Battle": (LinkSkillEffect.ATK_PERCENT, 20),
    "Prepared for Battle": (LinkSkillEffect.KI, 2),
    "Godly Power": (LinkSkillEffect.ATK_PERCENT, 15),
    "Big Bad Bosses": (LinkSkillEffect.ATK_PERCENT, 25),
    "Fused Fighter": (LinkSkillEffect.KI, 2),
    "Nightmare": (LinkSkillEffect.ATK_PERCENT, 10),
    "Dismal Future": (LinkSkillEffect.KI, 1),
    "Super Saiyan": (LinkSkillEffect.ATK_PERCENT, 10),
    "Fear and Faith": (LinkSkillEffect.DEF_PERCENT, 15),
    "Kamehameha": (LinkSkillEffect.ATK_PERCENT, 15),
    "Legendary Power": (LinkSkillEffect.ATK_PERCENT, 15),
}

# --- KI SPHERE CLASS ---
class KiSphere:
    def __init__(self, attribute):
        self.attribute = attribute
        self.collected = False
    
    def __str__(self):
        if self.collected:
            return "[X]"
        if self.attribute == Attribute.RAINBOW: 
            return "[R]"
        return f"[{self.attribute.value[0]}]"

# --- CHARACTER CLASS (with enhancements) ---
class Character:
    def __init__(self, name, attribute, hp, attack, defense, 
                 is_enemy=False, links=None, is_leader=False, 
                 categories=None, evasion=EvasionLevel.NONE,
                 is_lr=False, passive_skills=None, super_attack_effects=None):
        self.name = name
        if isinstance(attribute, str):
            for attr_enum in Attribute:
                if attr_enum.value.startswith(attribute):
                    attribute = attr_enum
                    break
        self.attribute = attribute
        
        self.max_hp = hp
        self.hp = hp
        self.base_attack = attack
        self.base_defense = defense
        self.attack = attack
        self.defense = defense
        self._ki = 0  # Private variable for ki control
        self.is_enemy = is_enemy
        self.links = links or []
        self.is_leader = is_leader
        self.categories = categories or []
        self.atk_buff = 0
        self.def_buff = 0
        self.link_atk_buff = 0
        self.link_ki_buff = 0
        self.link_evasion_buff = 0
        self.evasion = evasion
        self.is_lr = is_lr
        
        # Passive skills
        self.passive_skills = passive_skills or {
            "additional_attack": 0,
            "critical_hit_chance": 0,
            "dodge_chance": 0,
            "damage_reduction": 0,
            "guard_chance": 0,
            "foresee_super": False,
            "revival_skill": False,
            "atk_per_super": 0,
            "def_per_super": 0,
            "atk_per_attack_received": 0,
            "def_per_attack_received": 0,
        }
        
        # Super attack effects
        self.super_attack_effects = super_attack_effects or {
            "atk_up": 0,
            "def_up": 0,
            "stun_chance": 0,
            "additional_effects": []
        }
        
        # Other attributes
        self.active_skill_used = False; self.exchange_available = False; self.turn_count = 0
        self.critical_hit_chance = 0; self.damage_reduction = 0; self.effective_against_all = False
        self.guard_all = False; self.additional_attack_chance = 0; self.status_effects = {}
        self.damage_received_count = 0; self.max_attacks_per_turn = 1; self.attacks_this_turn = 0
        self.entry_turn = 0; self.super_attacks_performed = 0; self.attacks_received = 0
        self.ki_sphere_bonus = 0; self.domain_active = False; self.omnipresent = False
        self.domain_turns_remaining = 0
        self.rotation_position = 0  # Position in rotation (1-3)
        self.permanent_atk_buff = 0
        self.permanent_def_buff = 0
        self.dodge_chance = 0
        self.guard_chance = 0

    # Getter/setter for Ki control
    @property
    def ki(self):
        return self._ki
    
    @ki.setter
    def ki(self, value):
        # Limit Ki to maximum 24
        self._ki = max(0, min(value, 24))

    def start_turn_reset(self):
        """Reset temporary buffs at turn start"""
        self.turn_count += 1
        self.attacks_this_turn = 0
        self.link_atk_buff = 0
        self.link_ki_buff = 0
        self.link_evasion_buff = 0
        if self.domain_active:
            self.domain_turns_remaining -= 1
            if self.domain_turns_remaining <= 0:
                self.domain_active = False; self.omnipresent = False

    def apply_passive_skills(self):
        """Apply passive skills at turn start"""
        # Base bonuses (use get with default)
        self.attack += self.passive_skills.get("base_atk", 0)
        self.defense += self.passive_skills.get("base_def", 0)
        
        # Get passive values safely
        atk_per_super = self.passive_skills.get("atk_per_super", 0)
        def_per_super = self.passive_skills.get("def_per_super", 0)
        atk_per_attack_received = self.passive_skills.get("atk_per_attack_received", 0)
        def_per_attack_received = self.passive_skills.get("def_per_attack_received", 0)
        
        # Bonuses from super attacks
        if atk_per_super > 0:
            self.permanent_atk_buff += atk_per_super * self.super_attacks_performed
        if def_per_super > 0:
            self.permanent_def_buff += def_per_super * self.super_attacks_performed
        
        # Bonuses from received attacks
        if atk_per_attack_received > 0:
            self.permanent_atk_buff += atk_per_attack_received * self.attacks_received
        if def_per_attack_received > 0:
            self.permanent_def_buff += def_per_attack_received * self.attacks_received
        
        # Apply permanent buffs
        self.attack += self.permanent_atk_buff
        self.defense += self.permanent_def_buff
        
        # Set chances safely
        self.critical_hit_chance = self.passive_skills.get("critical_hit_chance", 0)
        self.dodge_chance = self.passive_skills.get("dodge_chance", 0)
        self.damage_reduction = self.passive_skills.get("damage_reduction", 0)
        self.guard_chance = self.passive_skills.get("guard_chance", 0)
        self.additional_attack_chance = self.passive_skills.get("additional_attack", 0)

    def apply_link_bonuses(self, active_links):
        """Apply bonuses from active links"""
        for link_name in active_links:
            if link_name in LINK_SKILL_DATABASE:
                effect, value = LINK_SKILL_DATABASE[link_name]
                if effect == LinkSkillEffect.KI:
                    self.link_ki_buff += value
                elif effect == LinkSkillEffect.ATK_PERCENT:
                    self.link_atk_buff += value
                elif effect == LinkSkillEffect.EVASION:
                    self.link_evasion_buff += value

    def get_final_attack(self):
        """Calculate final attack with all buffs"""
        passive_multiplier = 1 + self.atk_buff / 100
        link_multiplier = 1 + self.link_atk_buff / 100
        return self.base_attack * passive_multiplier * link_multiplier + self.permanent_atk_buff

    # Updated attack methods
    def normal_attack(self):
        return self.get_final_attack()

    def super_attack(self):
        base_attack = self.get_final_attack() * 2
        # Apply super attack effects
        self.atk_buff += self.super_attack_effects["atk_up"]
        self.def_buff += self.super_attack_effects["def_up"]
        
        # Stun chance
        if self.super_attack_effects["stun_chance"] > 0 and random.randint(1, 100) <= self.super_attack_effects["stun_chance"]:
            return base_attack, "stun"
        return base_attack, ""

    def ultra_super_attack(self):
        base_attack = self.get_final_attack() * 3
        # Apply super attack effects
        self.atk_buff += self.super_attack_effects["atk_up"]
        self.def_buff += self.super_attack_effects["def_up"]
        
        # Stun chance
        if self.super_attack_effects["stun_chance"] > 0 and random.randint(1, 100) <= self.super_attack_effects["stun_chance"]:
            return base_attack, "stun"
        return base_attack, ""

    def dokkan_attack(self):
        """Powerful attack in Dokkan Mode"""
        base_attack = self.get_final_attack() * 5
        # Apply super attack effects
        self.atk_buff += self.super_attack_effects["atk_up"] * 2
        self.def_buff += self.super_attack_effects["def_up"] * 2
        
        # Increased stun chance
        stun_chance = min(100, self.super_attack_effects["stun_chance"] + 50)
        if stun_chance > 0 and random.randint(1, 100) <= stun_chance:
            return base_attack, "stun"
        return base_attack, ""

    def try_evade(self):
        """Attempt to evade attack"""
        total_evasion = self.evasion.value + self.link_evasion_buff + self.dodge_chance
        if total_evasion <= 0:
            return False
        return random.randint(1, 100) <= total_evasion

    def try_guard(self):
        """Attempt to guard attack"""
        if self.guard_chance <= 0:
            return False
        return random.randint(1, 100) <= self.guard_chance

    def try_critical(self):
        """Attempt critical hit"""
        if self.critical_hit_chance <= 0:
            return False
        return random.randint(1, 100) <= self.critical_hit_chance

    def is_alive(self): 
        return self.hp > 0

    def use_active_skill(self):
        # Active skill implementation remains the same
        pass

    def take_damage(self, damage):
        # Account for damage reduction (character's own passive)
        actual_damage = damage * (1 - self.damage_reduction / 100)
        
        # Account for damage cap
        if StatusEffect.DAMAGE_CAP in self.status_effects:
            actual_damage = min(actual_damage, self.status_effects[StatusEffect.DAMAGE_CAP])
        
        self.hp = max(0, self.hp - actual_damage)
        self.attacks_received += 1
        self.damage_received_count += 1
        return actual_damage

# --- TEAM CLASS ---
class Team:
    def __init__(self, is_player=False):
        self.members = []
        self.rotation = []  # Current rotation (3 active characters)
        self.reserve = []   # Characters in reserve
        self.ki_graph = []
        self.is_player = is_player
        self.total_hp = 0
        self.max_hp = 0
        self.active_item_effects = {}
        self.enemies = []
        self.domain_active = False
        self.dokkan_meter = 0  # Dokkan Mode activation counter

    def setup_rotation(self):
        """Set up initial character rotation"""
        if len(self.members) < 3:
            self.rotation = self.members.copy()
            self.reserve = []
        else:
            self.rotation = self.members[:3]
            self.reserve = self.members[3:]
        
        for i, char in enumerate(self.rotation):
            char.rotation_position = i + 1

    def rotate_team(self):
        """Rotate characters Dokkan Battle style"""
        if not self.rotation or not self.reserve:
            return
        
        # Move first character to reserve
        char_out = self.rotation.pop(0)
        self.reserve.append(char_out)
        
        # Add next character from reserve
        char_in = self.reserve.pop(0)
        self.rotation.append(char_in)
        
        # Update positions
        for i, char in enumerate(self.rotation):
            char.rotation_position = i + 1
        return f"Rotation changed: {char_in.name} joined the battle!"

    def add_member(self, character, enemies=[]):
        if len(self.members) < 6:
            self.members.append(character)
            self.enemies = enemies
            if self.is_player:
                self.total_hp += character.hp
                self.max_hp += character.max_hp
            self.update_graph()
            if character.is_leader:
                self.apply_leader_skill(character)
    
    def take_damage(self, damage):
        if self.is_player:
            modified_damage = damage
            if self.domain_active:
                modified_damage *= 1.3
            
            # FIXED: Sum ALL damage reduction effects
            total_reduction = 0
            for effect_name, effect_data in self.active_item_effects.items():
                if 'damage_reduction' in effect_name:
                    total_reduction += effect_data['value']
            
            # Apply combined reduction
            if total_reduction > 0:
                modified_damage *= (1 - total_reduction / 100.0)
            
            # FIXED: Sum ALL defense boosts
            total_def_boost = 0
            for effect_name, effect_data in self.active_item_effects.items():
                if 'def_boost' in effect_name:
                    total_def_boost += effect_data['value']
            
            # Apply combined defense boost
            if total_def_boost > 0:
                modified_damage *= (1 - (total_def_boost * 0.5) / 100.0)

            actual_damage = int(modified_damage)
            self.total_hp = max(0, self.total_hp - actual_damage)
            return actual_damage
        return damage

    def apply_leader_skill(self, leader):
        initial_max_hp = sum(m.max_hp for m in self.members)

        if "Dawn of an Ideal World" in leader.name:
            for member in self.members:
                if any(cat in [Category.WORLDWIDE_CHAOS, Category.POTARA] for cat in member.categories):
                    member.max_hp *= 2.5; member.base_attack *= 2.5; member.base_defense *= 2.5; member.ki += 4
        elif "Infinite Sanctuary" in leader.name:
            for member in self.members:
                if any(cat in [Category.REALM_OF_GODS, Category.WORLDWIDE_CHAOS, Category.FUSED_FIGHTERS] for cat in member.categories):
                    member.max_hp *= 2.7; member.base_attack *= 2.7; member.base_defense *= 2.7; member.ki += 3
                    if any(cat in [Category.TIME_TRAVELERS, Category.FINAL_TRUMP_CARD] for cat in member.categories):
                         member.max_hp *= 1.3; member.base_attack *= 1.3; member.base_defense *= 1.3
                elif not any(cat in [Category.REALM_OF_GODS, Category.WORLDWIDE_CHAOS, Category.FUSED_FIGHTERS] for cat in member.categories):
                    member.max_hp *= 2.5; member.base_attack *= 2.5; member.base_defense *= 2.5; member.ki += 3
        # Leader skills for new characters
        elif "Rose Stained" in leader.name:
            for member in self.members:
                if any(cat in [Category.FUTURE_SAGA, Category.REALM_OF_GODS] for cat in member.categories):
                    member.max_hp *= 3.0; member.base_attack *= 3.0; member.base_defense *= 2.8; member.ki += 4
        elif "Mastery of the Power of Rage" in leader.name:
            for member in self.members:
                if any(cat in [Category.SUPER_BOSSES, Category.CORRODED_BODY] for cat in member.categories):
                    member.max_hp *= 3.2; member.base_attack *= 3.2; member.base_defense *= 3.0; member.ki += 4
        
        new_max_hp = sum(m.max_hp for m in self.members)
        for member in self.members:
            member.hp = member.max_hp
            member.attack = member.base_attack
            member.defense = member.base_defense
        
        self.max_hp = int(new_max_hp)
        self.total_hp = self.max_hp

    def update_graph(self):
        size = len(self.members)
        self.ki_graph = [[False] * size for _ in range(size)]
        for i in range(size):
            for j in range(i + 1, size):
                if self.members[i].links and self.members[j].links:
                    common_links = set(self.members[i].links) & set(self.members[j].links)
                    if common_links:
                        self.ki_graph[i][j] = True
                        self.ki_graph[j][i] = True

    def get_ki_bonus(self, index):
        bonus = 0
        for i in range(len(self.members)):
            if self.ki_graph[index][i] and i != index and self.members[i].is_alive():
                bonus += 2
        return bonus

    def has_alive_members(self):
        if self.is_player:
            return self.total_hp > 0
        return any(member.is_alive() for member in self.members)

# --- BATTLE SYSTEM CLASS (with enhancements) ---
class BattleSystem:
    TYPE_MATRIX = {
        Attribute.AGL: {Attribute.STR: 1.5, Attribute.TEQ: 0.8},
        Attribute.STR: {Attribute.PHY: 1.5, Attribute.AGL: 0.8},
        Attribute.PHY: {Attribute.INT: 1.5, Attribute.STR: 0.8},
        Attribute.INT: {Attribute.TEQ: 1.5, Attribute.PHY: 0.8},
        Attribute.TEQ: {Attribute.AGL: 1.5, Attribute.INT: 0.8}
    }
    
    def __init__(self, player_team, enemy_team):
        self.player_team = player_team
        self.enemy_team = enemy_team
        self.turn_count = 0
        self.inventory = {
            SupportItem.GHOST_USHER: 2,
            SupportItem.ANDROID_8: 2,
            SupportItem.PRINCESS_SNAKE: 2,
            SupportItem.WHIS: 2,
        }
        self.enemy_turn_delayed = False
        self.ghost_usher_active_this_battle = False
        self.ki_grid = []  # 3x3 grid instead of linear field
        self.generate_ki_grid()
        self.player_team.setup_rotation()
        self.dokkan_available = False  # Dokkan Mode availability
        self.dokkan_character = None   # Character for Dokkan Mode

    def generate_ki_grid(self):
        """Generate 3x3 sphere grid"""
        attributes = [Attribute.STR, Attribute.AGL, Attribute.TEQ, Attribute.INT, Attribute.PHY]
        self.ki_grid = []
        for _ in range(3):
            row = []
            for _ in range(3):
                if random.random() < 0.1:
                    row.append(KiSphere(Attribute.RAINBOW))
                else:
                    row.append(KiSphere(random.choice(attributes)))
            self.ki_grid.append(row)

    def display_ki_grid(self):
        """Display sphere grid"""
        print("\n--- KI SPHERE GRID ---")
        print("    0   1   2")
        for i, row in enumerate(self.ki_grid):
            print(f"{i} | {' | '.join(str(sphere) for sphere in row)} |")
        print("Legend: [S]STR(Red) [A]AGL(Blue) [T]TEQ(Green) [I]INT(Purple) [P]PHY(Orange) [R]Rainbow")

    def collect_ki_path(self, character):
        """Collect spheres along player-chosen path"""
        self.display_battle_state()
        self.display_ki_grid()
        
        collected_ki = 0
        collected_spheres = []
        
        print(f"\n{character.name} ({character.attribute.value}) is collecting Ki.")
        print("Choose starting position (row, column):")
        
        try:
            start_row = int(input("Row (0-2): "))
            start_col = int(input("Column (0-2): "))
            
            if not (0 <= start_row <= 2 and 0 <= start_col <= 2):
                print("Invalid position. Using random values.")
                start_row, start_col = random.randint(0, 2), random.randint(0, 2)
        except ValueError:
            print("Invalid input. Using random values.")
            start_row, start_col = random.randint(0, 2), random.randint(0, 2)
        
        current_row, current_col = start_row, start_col
        path_length = 0
        
        while path_length < 7:
            # Collect sphere at current position
            if not self.ki_grid[current_row][current_col].collected:
                sphere = self.ki_grid[current_row][current_col]
                sphere.collected = True
                collected_spheres.append(sphere)
                
                # Calculate ki from sphere
                if sphere.attribute == Attribute.RAINBOW: 
                    ki_gain = 1
                elif sphere.attribute == character.attribute: 
                    ki_gain = 2
                else: 
                    ki_gain = 1
                collected_ki += ki_gain
                
                # Update Dokkan Mode counter
                self.player_team.dokkan_meter += ki_gain
                
                # Check Dokkan Mode activation
                if self.player_team.dokkan_meter >= 24 and not self.dokkan_available:
                    self.dokkan_available = True
                    self.dokkan_character = character
                    print("\n!!! DOKKAN MODE ACTIVATED !!!")
            
                path_length += 1
            
            # Display progress
            self.display_battle_state()
            self.display_ki_grid()
            print(f"\nCollected: {', '.join(str(s) for s in collected_spheres)}")
            print(f"Current Ki: +{collected_ki} (Total: {character.ki + collected_ki}/24)")
            print(f"Dokkan Counter: {self.player_team.dokkan_meter}/24")
            
            if path_length >= 7:
                break
                
            # Choose next direction
            print("\nChoose direction to continue:")
            print("1. Right")
            print("2. Down")
            print("3. Down-right (diagonal)")
            print("4. Finish collection")
            
            try:
                direction = int(input("Your choice: "))
                if direction == 4:
                    break
                
                # Determine new position
                new_row, new_col = current_row, current_col
                if direction == 1 and current_col < 2:  # Right
                    new_col += 1
                elif direction == 2 and current_row < 2:  # Down
                    new_row += 1
                elif direction == 3 and current_row < 2 and current_col < 2:  # Down-right
                    new_row += 1
                    new_col += 1
                else:
                    print("Cannot move in that direction. Collection finished.")
                    break
                
                current_row, current_col = new_row, new_col
                
            except ValueError:
                print("Invalid input. Collection finished.")
                break
        
        # Update character ki
        character.ki += collected_ki
        print(f"\nTotal collected: +{collected_ki} Ki! (Total: {character.ki}/24)")
        print(f"Dokkan Counter: {self.player_team.dokkan_meter}/24")
        self.press_any_key()

    def dokkan_mini_game(self, character):
        """Mini-game for Dokkan Mode"""
        print("\n=== DOKKAN MODE ===")
        print(f"{character.name} prepares for a powerful attack!")
        print("Quickly trace a Z-shaped trajectory!")
        
        # Z-shaped trajectory: 7 points
        sequence = [
            (0, 0), (0, 1), (0, 2),
            (1, 2),
            (2, 2), (2, 1), (2, 0)
        ]
        
        success_count = 0
        start_time = time.time()
        
        for i, (row, col) in enumerate(sequence):
            print(f"\nPoint {i+1}/7: ({row}, {col})")
            print("Enter coordinates (row column):")
            
            try:
                input_row, input_col = map(int, input().split())
                if input_row == row and input_col == col:
                    success_count += 1
                    print("Success!")
                else:
                    print("Miss!")
            except:
                print("Invalid input!")
            
            # Check time (max 1.5 seconds per point)
            if time.time() - start_time > 1.5 * (i + 1):
                print("Too slow!")
                break
        
        # Calculate success rate
        success_rate = success_count / 7
        print(f"\nSuccess rate: {success_rate:.0%}")
        
        if success_rate >= 0.7:
            print("Perfect execution! Powerful attack activated!")
            return True
        elif success_rate >= 0.5:
            print("Good execution! Attack enhanced!")
            return True
        else:
            print("Failed execution! Attack not enhanced.")
            return False

    def perform_attack(self, player_char):
        """Perform attack with Dokkan Mode support"""
        # Determine attack type based on Ki
        attack_value = 0
        attack_type = "Normal Attack"
        effect = ""
        
        # Check Dokkan Mode availability
        dokkan_attack = False
        if self.dokkan_available and self.dokkan_character == player_char:
            use_dokkan = input("Use Dokkan Mode? (y/n): ").lower() == 'y'
            if use_dokkan:
                dokkan_success = self.dokkan_mini_game(player_char)
                if dokkan_success:
                    attack_value, effect = player_char.dokkan_attack()
                    attack_type = "DOKKAN Attack"
                    self.dokkan_available = False
                    self.player_team.dokkan_meter = 0
        
        if not dokkan_attack:
            if player_char.ki >= 18 and player_char.is_lr:
                attack_value, effect = player_char.ultra_super_attack()
                attack_type = "Ultra Super Attack"
                player_char.super_attacks_performed += 1
                player_char.ki = 0
            elif player_char.ki >= 12:
                attack_value, effect = player_char.super_attack()
                attack_type = "Super Attack"
                player_char.super_attacks_performed += 1
                player_char.ki = 0
            else:
                attack_value = player_char.normal_attack()

        # Choose target
        self.display_battle_state()
        print("\nChoose target:")
        alive_enemies = {i: enemy for i, enemy in enumerate(self.enemy_team.members) if enemy.is_alive()}
        if not alive_enemies: return
        for i, enemy in alive_enemies.items():
            print(f"{i}. {enemy.name} ({enemy.attribute.value}) | HP: {enemy.hp:,.0f}")
        
        try:
            target_index = int(input("Target: "))
            if target_index in alive_enemies:
                target = alive_enemies[target_index]
            else:
                target = next(iter(alive_enemies.values()))
        except:
            target = next(iter(alive_enemies.values()))
            
        # Check evasion
        if target.try_evade():
            print(f"{target.name} evaded the attack!")
            self.press_any_key()
            return
            
        # Calculate damage
        type_multiplier = self.get_type_multiplier(player_char.attribute, target.attribute)
        final_damage = int(attack_value * type_multiplier)
        
        # Check critical hit
        critical = player_char.try_critical()
        if critical:
            final_damage *= 1.5
            effect = "critical" if not effect else effect + ", critical"
        
        if target in self.player_team.members:
            actual_damage = self.player_team.take_damage(final_damage)
        else:
            actual_damage = target.take_damage(final_damage)

        self.display_battle_state()
        print(f"\n{player_char.name} uses {attack_type} on {target.name}!")
        
        if type_multiplier > 1.2: 
            print("It's super effective!")
        elif type_multiplier < 1: 
            print("It's not very effective...")
            
        if critical:
            print("CRITICAL HIT!")
            
        print(f"Total Damage: {final_damage:,.0f} | Actual Damage: {actual_damage:,.0f}")
        
        if effect == "stun":
            print(f"{target.name} is stunned for the next turn!")
            target.status_effects[StatusEffect.STUN] = 1
        
        if not target.is_alive(): 
            print(f"{target.name} defeated!")
        
        self.press_any_key()

    def enemy_turn(self):
        """Enemy turn with slot-based attacks"""
        print("\n--- ENEMY'S TURN ---")
        
        # Determine attack order (3 slots)
        attack_slots = []
        for enemy in self.enemy_team.members:
            if enemy.is_alive():
                # Determine number of attacks for this enemy (1-3)
                attacks = min(3, enemy.max_attacks_per_turn)
                for _ in range(attacks):
                    attack_slots.append(enemy)
        
        # Shuffle attacks
        random.shuffle(attack_slots)
        
        # Execute up to 3 attacks
        for i, attacker in enumerate(attack_slots[:3]):
            # Check for living players
            alive_players = [m for m in self.player_team.rotation if m.is_alive()]
            if not alive_players: 
                return
            
            # Choose random player
            target_char = random.choice(alive_players)
            
            # Check for stun
            if StatusEffect.STUN in attacker.status_effects:
                print(f"{attacker.name} is stunned and cannot attack!")
                del attacker.status_effects[StatusEffect.STUN]
                continue
            
            # Determine attack type (normal or super)
            is_super_attack = False
            if i == 0:  # First slot can be super attack
                is_super_attack = random.random() < 0.3  # 30% super attack chance
            elif random.random() < 0.1:  # 10% chance in other slots
                is_super_attack = True
            
            if is_super_attack:
                damage = attacker.super_attack()[0]
                attack_type = "SUPER ATTACK"
            else:
                damage = attacker.normal_attack()
                attack_type = "normal attack"
            
            # Check evasion
            if target_char.try_evade():
                print(f"{target_char.name} evaded {attacker.name}'s {attack_type}!")
                self.press_any_key()
                continue
                
            # Calculate damage
            type_multiplier = self.get_type_multiplier(attacker.attribute, target_char.attribute)
            final_damage = int(damage * type_multiplier)
            
            # Account for defense effects
            actual_damage = self.player_team.take_damage(final_damage)
            
            self.display_battle_state()
            print(f"\n{attacker.name} uses {attack_type} on {target_char.name} (Slot {i+1})!")
            
            if type_multiplier > 1.2: 
                print("It's super effective!")
            elif type_multiplier < 1: 
                print("It's not very effective...")
                
            print(f"Base Damage: {final_damage:,.0f} | Actual Damage: {actual_damage:,.0f}")
            
            # Check for stun
            if is_super_attack and random.random() < 0.2:  # 20% stun chance from super attack
                print(f"{target_char.name} is stunned for the next turn!")
                target_char.status_effects[StatusEffect.STUN] = 1
            
            self.press_any_key()

            if not self.player_team.has_alive_members():
                return

    def player_character_turn(self, char_index):
        player_char = self.player_team.rotation[char_index]
        
        # Reset temporary buffs
        player_char.start_turn_reset()
        
        # Generate NEW ki grid for this character's turn
        self.generate_ki_grid()  # ADDED: Reset grid for each character
        
        # Apply passive skills
        player_char.apply_passive_skills()

        # Activate Link Skills
        active_links = set()
        for i, ally in enumerate(self.player_team.rotation):
            if i == char_index: continue
            if not ally.is_alive(): continue
            common_links = set(player_char.links) & set(ally.links)
            active_links.update(common_links)
        
        if active_links:
            player_char.apply_link_bonuses(active_links)
            print(f"\nActivated Links for {player_char.name}: {', '.join(active_links)}")
            print(f"Bonuses: +{player_char.link_ki_buff} Ki, +{player_char.link_atk_buff}% ATK")
            if player_char.link_evasion_buff > 0:
                print(f"Evasion Bonus: +{player_char.link_evasion_buff}%")
            self.press_any_key()
        
        # Collect Ki from grid
        self.collect_ki_path(player_char)
        
        # Add Ki from links (with limit)
        player_char.ki += player_char.link_ki_buff

        # Action selection
        while True:
            self.display_battle_state()
            print(f"\n{player_char.name}'s turn! (Position: {player_char.rotation_position})")
            print(f"Current Ki: {player_char.ki}/24")
            if player_char.evasion != EvasionLevel.NONE:
                print(f"Evasion Chance: {player_char.evasion.value + player_char.link_evasion_buff}%")

            print("\n1. Attack")
            print("2. Use Support Item")
            
            # Determine available options based on Ki
            action_index = 3
             # FIXED: Active skill should appear for all characters after turn 4
            show_active_skill = (
                player_char.turn_count >= 4 and 
                not player_char.active_skill_used
            )
            
            if show_active_skill:
                print(f"{action_index}. Use Active Skill")
                active_skill_option = action_index
                action_index += 1
            else:
                active_skill_option = -1
            
            try:
                choice = int(input("Your choice: "))
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue
            
            if choice == 2:
                self.use_support_item()
                continue
            
            if choice == active_skill_option:
                result = player_char.use_active_skill()
                # Check for None and type
                if isinstance(result, tuple): 
                    damage, msg = result
                elif isinstance(result, str): 
                    msg = result
                    damage = 0
                else:
                    msg = "No active skill available"
                    damage = 0
                
                # Check availability
                if "not available" in msg:
                    print(msg)
                    self.press_any_key()
                    continue
                
                if "Lightning of Absolution" in msg:
                    self.display_battle_state()
                    print(f"\n{msg}")
                    
                    # Choose target for active skill
                    print("\nChoose target:")
                    alive_enemies = {i: enemy for i, enemy in enumerate(self.enemy_team.members) if enemy.is_alive()}
                    for i, enemy in alive_enemies.items():
                        print(f"{i}. {enemy.name} ({enemy.attribute.value}) | HP: {enemy.hp:,.0f}")
                    
                    try:
                        target_index = int(input("Target: "))
                        if target_index in alive_enemies:
                            target = alive_enemies[target_index]
                        else:
                            target = next(iter(alive_enemies.values()))
                    except:
                        target = next(iter(alive_enemies.values()))
                    
                    # Check evasion
                    if target.try_evade():
                        print(f"{target.name} evaded the active skill!")
                        self.press_any_key()
                        return
                    
                    # Apply damage
                    actual_damage = target.take_damage(damage)
                    print(f"Dealt {actual_damage:,.0f} damage!")
                    if not target.is_alive():
                        print(f"{target.name} defeated!")
                    self.press_any_key()
                    return
                
                elif "Omnipresence" in msg:
                    self.player_team.domain_active = True
                    print(f"\n{msg}")
                    self.press_any_key()
                    return
            
            if choice == 1:
                self.perform_attack(player_char)
                return
            else:
                print("Invalid choice. Please select again.")
                self.press_any_key()

    @staticmethod
    def clear_screen():
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def press_any_key():
        input("\nPress Enter to continue...")

    @staticmethod
    def get_type_multiplier(attacker_attr, defender_attr):
        if attacker_attr in BattleSystem.TYPE_MATRIX:
            multiplier = BattleSystem.TYPE_MATRIX[attacker_attr].get(defender_attr, 1.0)
            return multiplier * random.uniform(0.95, 1.05)
        return 1.0 * random.uniform(0.95, 1.05)

    def update_turn_effects(self):
        self.enemy_turn_delayed = False
        effects_to_remove = []
        for effect, data in self.player_team.active_item_effects.items():
            data['turns'] -= 1
            if data['turns'] <= 0:
                effects_to_remove.append(effect)
        
        for effect in effects_to_remove:
            del self.player_team.active_item_effects[effect]

    def use_support_item(self):
        self.clear_screen()
        print("===== SUPPORT ITEMS =====\n")
        
        # Create list of available items
        available_items = []
        for item, count in self.inventory.items():
            if count > 0:
                available_items.append(item)
        
        if not available_items:
            print("No items left!")
            self.press_any_key()
            return
        
        # Display available items
        for i, item in enumerate(available_items):
            print(f"{i+1}. {item.value} (x{self.inventory[item]})")
        
        cancel_option = len(available_items) + 1
        print(f"\n{cancel_option}. Cancel")

        try:
            choice = int(input("\nChoose item to use: "))
            if choice == cancel_option: 
                return
            selected_item = available_items[choice-1]
        except (ValueError, IndexError):
            print("Invalid input.")
            self.press_any_key()
            return
            
        self.inventory[selected_item] -= 1
        message = f"Used {selected_item.value}! "

        if selected_item == SupportItem.GHOST_USHER:
            if self.ghost_usher_active_this_battle:
                message += "But its effect does not stack. No effect this time."
            else:
                self.enemy_turn_delayed = True
                self.ghost_usher_active_this_battle = True
                message += "Enemy attacks are delayed for 1 turn."
        elif selected_item == SupportItem.ANDROID_8:
            heal_amount = self.player_team.max_hp * 0.70
            self.player_team.total_hp = min(self.player_team.max_hp, self.player_team.total_hp + heal_amount)
            # CHANGED: Use unique key
            self.player_team.active_item_effects['def_boost_android8'] = {'value': 50, 'turns': 2}
            message += "Recovered 70% HP and all allies' DEF +50% for 2 turns."
        elif selected_item == SupportItem.PRINCESS_SNAKE:
            heal_amount = self.player_team.max_hp * 0.55
            self.player_team.total_hp = min(self.player_team.max_hp, self.player_team.total_hp + heal_amount)
            # CHANGED: Use unique key
            self.player_team.active_item_effects['damage_reduction_snake'] = {'value': 30, 'turns': 1}
            message += "Recovered 55% HP and damage received reduced by 30% for 1 turn."
        elif selected_item == SupportItem.WHIS:
            # CHANGED: Use unique key
            self.player_team.active_item_effects['damage_reduction_whis'] = {'value': 40, 'turns': 2}
            message += "Damage received reduced by 40% for 2 turns."
            
        print(f"\n{message}")
        self.press_any_key()

    def display_team(self, team, is_enemy):
        if is_enemy:
            title = "===== ENEMY TEAM ====="
            print(title)
            for i, member in enumerate(team.members):
                if not member.is_alive(): continue
                status_line = f"[{i}] {member.name} ({member.attribute.value}) | HP: {member.hp:,.0f}"
                buffs = [f"ATK↑{member.atk_buff}%" for _ in range(1) if member.atk_buff > 0]
                buffs.extend([f"DEF↑{member.def_buff}%" for _ in range(1) if member.def_buff > 0])
                buffs.extend([f"DMG RED↓{member.damage_reduction}%" for _ in range(1) if member.damage_reduction > 0])
                if member.evasion != EvasionLevel.NONE:
                    buffs.append(f"EVASION:{member.evasion.value}%")
                if buffs: status_line += " | " + ", ".join(buffs)
                print(status_line)
        else:
            title = "===== YOUR TEAM ====="
            print(title)
            print(f"Team HP: {team.total_hp:,.0f} / {team.max_hp:,.0f}")
            if team.domain_active: print("DOMAIN ACTIVE: Infinite Zamasu")
            
            # Display all item buffs
            active_effects = []
            for effect_name, effect_data in team.active_item_effects.items():
                if effect_name == 'damage_reduction':
                    desc = f"DMG Reduction {effect_data['value']}%"
                elif effect_name == 'def_boost':
                    desc = f"DEF Boost {effect_data['value']}%"
                else:
                    desc = effect_name
                active_effects.append(f"{desc} ({effect_data['turns']} turns)")
            if active_effects:
                print(f"ACTIVE ITEM EFFECTS: {', '.join(active_effects)}")
                
            print("\nActive Rotation:")
            for i, member in enumerate(team.rotation):
                status_line = f"[{i}] {member.name} ({member.attribute.value}) | KI: {member.ki}/24 | HP: {member.hp:,.0f}"
                if member.evasion != EvasionLevel.NONE:
                    status_line += f" | Evasion: {member.evasion.value}%"
                print(status_line)
            
            if team.reserve:
                print("\nReserve:")
                for i, member in enumerate(team.reserve):
                    print(f"{i+3}. {member.name} ({member.attribute.value}) | HP: {member.hp:,.0f}")

    def display_battle_state(self):
        self.clear_screen()
        self.display_team(self.enemy_team, is_enemy=True)
        print("\n" + "=" * 80)
        self.display_team(self.player_team, is_enemy=False)
        print("\n" + "=" * 80)
        print(f"Turn: {self.turn_count}")

    def start_battle(self):
        self.turn_count = 0
        self.player_team.setup_rotation()
        
        while self.player_team.has_alive_members() and self.enemy_team.has_alive_members():
            self.turn_count += 1
            self.update_turn_effects()
            
            self.display_battle_state()
            print(f"\n=== ROUND {self.turn_count} START ===")
            
            # Each character's turn in rotation
            for i in range(len(self.player_team.rotation)):
                if not self.enemy_team.has_alive_members(): break
                if not self.player_team.rotation[i].is_alive(): continue
                self.player_character_turn(i)
            
            if not self.enemy_team.has_alive_members(): break
            
            self.display_battle_state()
            if self.enemy_turn_delayed:
                print("\nEnemy's turn is skipped due to Ghost Usher!")
                self.enemy_turn_delayed = False
                self.press_any_key()
            else:
                print("\n--- ENEMY'S TURN ---")
                self.press_any_key()
                self.enemy_turn()
            
            # Rotate characters after enemy turn
            rotation_msg = self.player_team.rotate_team()
            if rotation_msg:
                print("\n" + rotation_msg)
                self.press_any_key()
        
        self.display_battle_state()
        if self.player_team.has_alive_members():
            print("\n\n" + "="*30 + "\n" + " "*11 + "VICTORY!" + "\n" + "="*30)
        else:
            print("\n\n" + "="*30 + "\n" + " "*11 + "DEFEAT..." + "\n" + "="*30)
        
        self.press_any_key()

# --- MAIN SECTION ---
def main_menu():
    while True:
        BattleSystem.clear_screen()
        print("===== DOKKAN-LIKE BATTLE =====")
        print("1. Start New Battle")
        print("2. View Game Info")
        print("3. Exit")
        try: 
            choice = int(input("\nYour choice: "))
        except ValueError: 
            continue
        if choice == 1: 
            start_new_battle()
        elif choice == 2: 
            show_game_info()
        elif choice == 3: 
            print("\nThanks for playing!")
            break

def show_game_info():
    BattleSystem.clear_screen()
    print("===== GAME INFORMATION =====")
    print("\nKi Spheres: Collect to launch Super Attacks (12 Ki) or Ultra Super Attacks (18 Ki).")
    print("Matching color = 2 Ki, others = 1 Ki, Rainbow (R) = 1 Ki.")
    print("Link Skills: Active when characters with the same link are on the team, give bonuses.")
    print("Support Items:")
    print(f"- {SupportItem.GHOST_USHER.value}: Delay all opponent attacks for 1 turn (once per battle).")
    print(f"- {SupportItem.ANDROID_8.value}: Recover 70% HP, and all allies' DEF +50% for 2 turns.")
    print(f"- {SupportItem.PRINCESS_SNAKE.value}: Recover 55% HP, damage received -30% for 1 turn.")
    print(f"- {SupportItem.WHIS.value}: Damage received -40% for 2 turns.")
    print("\nEvasion System:")
    print("- Rare: 20% chance to evade")
    print("- Medium: 30% chance to evade")
    print("- High: 50% chance to evade")
    print("- Great: 70% chance to evade")
    print("\nRotation System:")
    print("- Teams consist of 3 active characters and 3 in reserve")
    print("- After each enemy turn, characters rotate positions")
    print("\nDokkan Mode:")
    print("- Collect Ki to fill the Dokkan Meter (24 Ki)")
    print("- Activate for a powerful attack with a Z-shape mini-game")
    BattleSystem.press_any_key()

def create_goku_black_characters():
    characters = []
    
    # Rose Stained Super Saiyan
    characters.append(Character(
        name="Rose Stained Super Saiyan Goku Black (Super Saiyan Rosé)",
        attribute=Attribute.AGL,
        hp=2500000,
        attack=18000,
        defense=12000,
        links=["Super Saiyan", "Fear and Faith", "Nightmare", "Prepared for Battle", 
               "Dismal Future", "Big Bad Bosses", "Fierce Battle"],
        categories=[Category.FUTURE_SAGA, Category.REALM_OF_GODS],
        evasion=EvasionLevel.MEDIUM,
        is_lr=True,
        passive_skills={
            "additional_attack": 30,
            "critical_hit_chance": 50,
            "dodge_chance": 20,
            "damage_reduction": 20,
            "guard_chance": 0,
            "atk_per_super": 20,
            "def_per_super": 10,
        },
        super_attack_effects={
            "atk_up": 30,
            "def_up": 20,
            "stun_chance": 30,
            "additional_effects": []
        }
    ))
    
    # Mastery of the Power of Rage
    characters.append(Character(
        name="Mastery of the Power of Rage Goku Black (Super Saiyan Rosé)",
        attribute=Attribute.INT,
        hp=2700000,
        attack=20000,
        defense=14000,
        links=["Super Saiyan", "Big Bad Bosses", "Dismal Future", "Prepared for Battle", 
               "Nightmare", "Fear and Faith", "Fierce Battle"],
        categories=[Category.SUPER_BOSSES, Category.CORRODED_BODY, Category.REALM_OF_GODS],
        evasion=EvasionLevel.HIGH,
        is_lr=True,
        passive_skills={
            "additional_attack": 20,
            "critical_hit_chance": 70,
            "dodge_chance": 10,
            "damage_reduction": 30,
            "guard_chance": 0,
            "atk_per_super": 15,
            "def_per_super": 15,
        },
        super_attack_effects={
            "atk_up": 40,
            "def_up": 10,
            "stun_chance": 20,
            "additional_effects": []
        }
    ))
    
    # Mark of Almighty Power
    characters.append(Character(
        name="Mark of Almighty Power Goku Black (Super Saiyan Rosé)",
        attribute=Attribute.TEQ,
        hp=2300000,
        attack=22000,
        defense=10000,
        links=["Super Saiyan", "Fear and Faith", "Kamehameha", "Dismal Future", 
               "Big Bad Bosses", "Fierce Battle", "Legendary Power"],
        categories=[Category.FUTURE_SAGA, Category.REALM_OF_GODS],
        evasion=EvasionLevel.RARE,
        is_lr=False,
        passive_skills={
            "additional_attack": 10,
            "critical_hit_chance": 30,
            "dodge_chance": 40,
            "damage_reduction": 15,
            "guard_chance": 0,
            "atk_per_super": 25,
            "def_per_super": 5,
        },
        super_attack_effects={
            "atk_up": 25,
            "def_up": 15,
            "stun_chance": 25,
            "additional_effects": []
        }
    ))
    
    # Furious Punishment
    characters.append(Character(
        name="Furious Punishment Goku Black (Super Saiyan Rosé)",
        attribute=Attribute.PHY,
        hp=2600000,
        attack=19000,
        defense=15000,
        links=["Super Saiyan", "Fear and Faith", "Nightmare", "Prepared for Battle", 
               "Dismal Future", "Big Bad Bosses", "Fierce Battle"],
        categories=[Category.REALM_OF_GODS, Category.ACCELERATED_BATTLE],
        evasion=EvasionLevel.GREAT,
        is_lr=False,
        passive_skills={
            "additional_attack": 15,
            "critical_hit_chance": 40,
            "dodge_chance": 30,
            "damage_reduction": 25,
            "guard_chance": 0,
            "atk_per_super": 15,
            "def_per_super": 20,
        },
        super_attack_effects={
            "atk_up": 20,
            "def_up": 30,
            "stun_chance": 15,
            "additional_effects": []
        }
    ))
    
    return characters

def start_new_battle():
    enemy_team = Team()
    vegeta = Character("Super Saiyan God SS Vegeta", Attribute.STR, 12000000, 370000, 150000, is_enemy=True)
    vegeta.damage_reduction = 66
    vegeta.max_attacks_per_turn = 3
    enemy_team.add_member(vegeta)

    player_team = Team(is_player=True)
    
    # Add new characters
    black_characters = create_goku_black_characters()
    for char in black_characters:
        player_team.add_member(char, enemy_team.members)
    
    # Add two more characters for full team
    player_team.add_member(Character(
        name="Fusion Zamasu",
        attribute=Attribute.INT,
        hp=2300000,
        attack=17000,
        defense=13000,
        links=["Fused Fighter", "Godly Power"],
        categories=[Category.FUTURE_SAGA, Category.REALM_OF_GODS]
    ), enemy_team.members)
    
    player_team.add_member(Character(
        name="Goku Black (Base)",
        attribute=Attribute.PHY,
        hp=2100000,
        attack=16000,
        defense=11000,
        links=["Prodigies", "Cold Judgment"],
        categories=[Category.FUTURE_SAGA]
    ), enemy_team.members)
    
    # Set leader
    player_team.members[0].is_leader = True
    player_team.apply_leader_skill(player_team.members[0])
    
    battle = BattleSystem(player_team, enemy_team)
    battle.start_battle()

if __name__ == "__main__":
    random.seed()
    main_menu()