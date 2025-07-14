import os
import random
from enum import Enum

# --- ПЕРЕЧИСЛЕНИЯ (Объединенные) ---
class Attribute(Enum):
    STR = "STR (Красный)"
    AGL = "AGL (Синий)"
    TEQ = "TEQ (Зеленый)"
    INT = "INT (Фиолетовый)"
    PHY = "PHY (Оранжевый)"
    RAINBOW = "RAINBOW"

class StatusEffect(Enum):
    ATK_DOWN = "ATK Down"; DEF_UP = "DEF Up"; IMMUNITY = "Immunity"; DAMAGE_CAP = "Damage Cap"
    NULLIFY_SUPER_SEAL = "Nullify Super Seal"; NULLIFY_STUN = "Nullify Stun"; NULLIFY_ATK_DOWN = "Nullify ATK Down"
    STUN = "Stun"; ATK_UP = "ATK Up"; CRITICAL_HIT = "Critical Hit"; DAMAGE_REDUCTION = "Damage Reduction"
    EFFECTIVE_ALL = "Effective Against All Types"; DOMAIN = "Domain Active"; OMNIPRESENT = "Omnipresent"

class Category(Enum):
    WORLDWIDE_CHAOS = "Worldwide Chaos"; POTARA = "Potara"; REALM_OF_GODS = "Realm of Gods"
    FUSED_FIGHTERS = "Fused Fighters"; TIME_TRAVELERS = "Time Travelers"
    FINAL_TRUMP_CARD = "Final Trump Card"; FUTURE_SAGA = "Future Saga"

class SupportItem(Enum):
    GHOST_USHER = "Ghost Usher"; ANDROID_8 = "Android #8"
    PRINCESS_SNAKE = "Princess Snake"; WHIS = "Whis"

class LinkSkillEffect(Enum):
    KI = "Ki"
    ATK_PERCENT = "ATK %"

LINK_SKILL_DATABASE = {
    "Fierce Battle": (LinkSkillEffect.ATK_PERCENT, 20),
    "Prepared for Battle": (LinkSkillEffect.KI, 2),
    "Godly Power": (LinkSkillEffect.ATK_PERCENT, 15),
    "Big Bad Bosses": (LinkSkillEffect.ATK_PERCENT, 25),
    "Fused Fighter": (LinkSkillEffect.KI, 2),
    "Nightmare": (LinkSkillEffect.ATK_PERCENT, 10),
    "Dismal Future": (LinkSkillEffect.KI, 1),
}

# --- КЛАСС KI SPHERE ---
class KiSphere:
    def __init__(self, attribute):
        self.attribute = attribute
    
    def __str__(self):
        if self.attribute == Attribute.RAINBOW: return "[R]"
        return f"[{self.attribute.value[0]}]"

# --- КЛАСС CHARACTER (с дополнениями) ---
class Character:
    def __init__(self, name, attribute, hp, attack, defense, is_enemy=False, links=None, is_leader=False, categories=None):
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
        self._ki = 0  # Используем приватную переменную для контроля ограничения
        self.is_enemy = is_enemy
        self.links = links or []
        self.is_leader = is_leader
        self.categories = categories or []
        self.atk_buff = 0
        self.def_buff = 0
        self.link_atk_buff = 0
        self.link_ki_buff = 0
        
        # Остальные атрибуты
        self.active_skill_used = False; self.exchange_available = False; self.turn_count = 0
        self.critical_hit_chance = 0; self.damage_reduction = 0; self.effective_against_all = False
        self.guard_all = False; self.additional_attack_chance = 0; self.status_effects = {}
        self.damage_received_count = 0; self.max_attacks_per_turn = 1; self.attacks_this_turn = 0
        self.entry_turn = 0; self.super_attacks_performed = 0; self.attacks_received = 0
        self.ki_sphere_bonus = 0; self.domain_active = False; self.omnipresent = False
        self.domain_turns_remaining = 0

    # Добавляем геттер/сеттер для контроля Ki
    @property
    def ki(self):
        return self._ki
    
    @ki.setter
    def ki(self, value):
        # Ограничиваем Ki максимум 24
        self._ki = max(0, min(value, 24))

    def start_turn_reset(self):
        """Сброс временных баффов в начале хода"""
        self.turn_count += 1
        self.attacks_this_turn = 0
        self.link_atk_buff = 0
        self.link_ki_buff = 0
        if self.domain_active:
            self.domain_turns_remaining -= 1
            if self.domain_turns_remaining <= 0:
                self.domain_active = False; self.omnipresent = False

    def apply_link_bonuses(self, active_links):
        """Применение бонусов от активных линков"""
        for link_name in active_links:
            if link_name in LINK_SKILL_DATABASE:
                effect, value = LINK_SKILL_DATABASE[link_name]
                if effect == LinkSkillEffect.KI:
                    self.link_ki_buff += value
                elif effect == LinkSkillEffect.ATK_PERCENT:
                    self.link_atk_buff += value

    def get_final_attack(self):
        """Расчет итоговой атаки с учетом всех баффов"""
        passive_multiplier = 1 + self.atk_buff / 100
        link_multiplier = 1 + self.link_atk_buff / 100
        return self.base_attack * passive_multiplier * link_multiplier

    # Обновленные методы атаки
    def normal_attack(self):
        return self.get_final_attack()

    def super_attack(self):
        return self.get_final_attack() * 2

    def ultra_super_attack(self):
        return self.get_final_attack() * 3

    def colossal_damage_attack(self):
        return self.get_final_attack() * 4

    def mega_colossal_damage_attack(self):
        return self.get_final_attack() * 5

    def ultimate_damage_attack(self):
        return self.get_final_attack() * 6

    # Остальные методы без изменений
    def is_alive(self): return self.hp > 0
    
    def _start_turn_old(self):
        if self.domain_active:
            self.domain_turns_remaining -= 1
            if self.domain_turns_remaining <= 0:
                self.domain_active = False
                self.omnipresent = False
        if "Dawn of an Ideal World" in self.name and self.attacks_received >= 5:
            heal = self.max_hp * 0.1
            self.hp = min(self.max_hp, self.hp + heal)
            return f"{self.name} recovered 10% HP!"
        return ""

    def use_active_skill(self):
        if "Dawn of an Ideal World" in self.name:
            if self.super_attacks_performed < 5:
                return "Active Skill not available! (Requires 5 Super Attacks)"
            if self.active_skill_used:
                return "Active Skill already used!"
            self.active_skill_used = True
            self.atk_buff += 300
            damage = self.ultimate_damage_attack()
            return damage, "Lightning of Absolution! Massively raises ATK, stuns enemy!"
        elif "Infinite Sanctuary" in self.name:
            if self.hp > self.max_hp * 0.3:
                return "Active Skill not available! (Requires HP <= 30%)"
            if self.active_skill_used:
                return "Active Skill already used!"
            self.active_skill_used = True
            self.domain_active = True
            self.omnipresent = True
            self.domain_turns_remaining = 5
            return 0, "Omnipresence! Creates the Domain 'Infinite Zamasu'!"
        # Добавлен возврат по умолчанию
        return "No active skill available for this character."

    def apply_passives(self, team):
        if "Dawn of an Ideal World" in self.name:
            self.atk_buff = 100
            self.def_buff = 100
            self.damage_reduction = 20
            self.ki_sphere_bonus = 1
            if self.ki >= 12: self.atk_buff += 50; self.def_buff += 50
            if self.ki >= 18: self.additional_attack_chance = 100
            if self.ki >= 24: self.effective_against_all = True
            self.damage_reduction += min(self.attacks_received, 5) * 2
            # Ограничиваем Ki при добавлении
            self.ki += min(self.attacks_received // 5, 5)
        elif "Infinite Sanctuary" in self.name:
            self.ki += 6
            self.atk_buff = 100
            self.def_buff = 100
            self.damage_reduction = 40
            self.critical_hit_chance = 70
            
            # ИСПРАВЛЕНИЕ: Проверка на наличие врагов перед итерацией
            if team.enemies:
                if not any(Category.REALM_OF_GODS in enemy.categories for enemy in team.enemies):
                    self.ki += 3
                    self.atk_buff += 50
                    self.def_buff += 50
            
            self.def_buff += 50
            if self.hp <= self.max_hp * 0.7: 
                self.def_buff += 50
            self.additional_attack_chance = 80
            self.atk_buff += min(self.attacks_received * 25, 150)
        
        self.attack = self.base_attack * (1 + self.atk_buff / 100)
        self.defense = self.base_defense * (1 + self.def_buff / 100)

    def take_damage(self, damage):
        actual_damage = damage * (1 - self.damage_reduction / 100)
        if StatusEffect.DAMAGE_CAP in self.status_effects:
            actual_damage = min(actual_damage, self.status_effects[StatusEffect.DAMAGE_CAP])
        self.hp = max(0, self.hp - actual_damage)
        self.attacks_received += 1
        self.damage_received_count += 1
        if "Infinite Sanctuary" in self.name:
            self.atk_buff = min(self.atk_buff + 25, 150)
            self.attack = self.base_attack * (1 + self.atk_buff / 100)
        return actual_damage

    def counter_attack(self, damage):
        if "Dawn of an Ideal World" in self.name and random.random() > 0.3:
            return self.ultra_super_attack()
        return 0

# --- КЛАСС TEAM ---
class Team:
    def __init__(self, is_player=False):
        self.members = []
        self.ki_graph = []
        self.is_player = is_player
        self.total_hp = 0
        self.max_hp = 0
        self.active_item_effects = {}
        self.enemies = []
        self.domain_active = False

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
            if 'damage_reduction' in self.active_item_effects:
                reduction_value = self.active_item_effects['damage_reduction']['value']
                modified_damage *= (1 - reduction_value / 100.0)
            if 'def_boost' in self.active_item_effects:
                # Исправление: используем значение из эффекта
                def_boost_value = self.active_item_effects['def_boost']['value']
                modified_damage *= (1 - (def_boost_value * 0.5) / 100.0)

            actual_damage = int(modified_damage)
            self.total_hp = max(0, self.total_hp - actual_damage)
            return actual_damage  # Возвращаем фактический урон
        return damage  # Для врагов не обрабатываем

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

# --- КЛАСС BATTLESYSTEM (с дополнениями) ---
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
        # ИСПРАВЛЕНИЕ: Ghost Usher теперь 2
        self.inventory = {
            SupportItem.GHOST_USHER: 2,
            SupportItem.ANDROID_8: 2,
            SupportItem.PRINCESS_SNAKE: 2,
            SupportItem.WHIS: 2,
        }
        self.enemy_turn_delayed = False
        self.ghost_usher_active_this_battle = False
        self.ki_field = []
        self.generate_ki_field()

    def generate_ki_field(self, count=24):
        attributes = [Attribute.STR, Attribute.AGL, Attribute.TEQ, Attribute.INT, Attribute.PHY]
        while len(self.ki_field) < count:
            if random.random() < 0.1:
                self.ki_field.append(KiSphere(Attribute.RAINBOW))
            else:
                self.ki_field.append(KiSphere(random.choice(attributes)))

    def collect_ki(self, character):
        self.display_battle_state()
        print("\n--- KI SPHERE FIELD ---")
        print(" ".join(map(str, self.ki_field)))
        print(f"\n{character.name} ({character.attribute.value}) is collecting Ki.")
        
        try:
            path_len = int(input("How many spheres to collect? (1-7): "))
            path_len = max(1, min(path_len, 7, len(self.ki_field)))
        except ValueError:
            path_len = random.randint(3, 5)
            print(f"Invalid input, collecting {path_len} spheres.")
        
        collected_ki = 0
        print("Collected:", end=" ")
        for _ in range(path_len):
            sphere = self.ki_field.pop(0)
            print(str(sphere), end=" ")
            if sphere.attribute == Attribute.RAINBOW: collected_ki += 1
            elif sphere.attribute == character.attribute: collected_ki += 2
            else: collected_ki += 1
        
        # Ограничиваем Ki максимум 24
        character.ki += collected_ki
        print(f"\n+ {collected_ki} Ki from spheres! (Total: {character.ki}/24)")
        self.generate_ki_field()
        self.press_any_key()

    # Обновленный метод хода персонажа игрока
    def player_character_turn(self, char_index):
        player_char = self.player_team.members[char_index]
        
        # Сброс временных баффов
        player_char.start_turn_reset()

        # Активация Link Skills
        active_links = set()
        for i, ally in enumerate(self.player_team.members):
            if i == char_index: continue
            if not ally.is_alive(): continue
            common_links = set(player_char.links) & set(ally.links)
            active_links.update(common_links)
        
        if active_links:
            player_char.apply_link_bonuses(active_links)
            print(f"\nActivated Links for {player_char.name}: {', '.join(active_links)}")
            print(f"Bonuses: +{player_char.link_ki_buff} Ki, +{player_char.link_atk_buff}% ATK")
            self.press_any_key()
        
        # Сбор Ki с поля
        self.collect_ki(player_char)
        
        # Добавляем Ki от линков (с ограничением)
        player_char.ki += player_char.link_ki_buff

        # Применение пассивок с проверкой
        if "Zamasu" in player_char.name or "Goku Black" in player_char.name:
            # Убедимся, что враги установлены
            if not self.enemy_team.members:
                self.enemy_team.members = []
            player_char.apply_passives(self.player_team)

        # Выбор действия
        while True:
            self.display_battle_state()
            print(f"\n{player_char.name}'s turn! (Final ATK: {player_char.get_final_attack():,.0f})")
            print(f"Current Ki: {player_char.ki}/24")

            print("\n1. Attack")
            print("2. Use Support Item")
            
            # Определяем доступные опции на основе Ki
            action_index = 3
            show_active_skill = (
                player_char.turn_count >= 4 and 
                not player_char.active_skill_used and 
                ("Goku Black" in player_char.name or "Zamasu" in player_char.name)
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
                # ИСПРАВЛЕНИЕ: Проверка на None и тип
                if isinstance(result, tuple): 
                    damage, msg = result
                elif isinstance(result, str): 
                    msg = result
                    damage = 0
                else:
                    msg = "No active skill available"
                    damage = 0
                
                # Исправленная проверка
                if "not available" in msg:
                    print(msg)
                    self.press_any_key()
                    continue
                
                if "Lightning of Absolution" in msg:
                    self.display_battle_state()
                    print(f"\n{msg}")
                    
                    # Выбор цели для активного скилла
                    print("\nChoose target:")
                    alive_enemies = {i: enemy for i, enemy in enumerate(self.enemy_team.members) if enemy.is_alive()}
                    for i, enemy in alive_enemies.items():
                        print(f"{i}. {enemy.name} ({enemy.attribute.value}) | HP: {enemy.hp:,.0f}")
                    
                    try:
                        target_index = int(input("Target: "))
                        # ПРЯМОЕ ИСПРАВЛЕНИЕ ОШИБКИ: выбор цели без сообщения об ошибке
                        if target_index in alive_enemies:
                            target = alive_enemies[target_index]
                        else:
                            target = next(iter(alive_enemies.values()))
                    except:
                        target = next(iter(alive_enemies.values()))
                    
                    # Нанесение урона
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

    def perform_attack(self, player_char):
        # Определение типа атаки по количеству Ki
        attack_value = 0
        attack_type = "Normal Attack"
        
        if player_char.ki >= 18:
            attack_value = player_char.ultra_super_attack()
            attack_type = "Ultra Super Attack"
            player_char.super_attacks_performed += 1
            player_char.ki = 0
        elif player_char.ki >= 12:
            attack_value = player_char.super_attack()
            attack_type = "Super Attack"
            player_char.super_attacks_performed += 1
            player_char.ki = 0
        else:
            attack_value = player_char.normal_attack()

        # Выбор цели
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
            
        # Расчет урона
        type_multiplier = self.get_type_multiplier(player_char.attribute, target.attribute)
        final_damage = int(attack_value * type_multiplier)
        actual_damage = target.take_damage(final_damage)

        self.display_battle_state()
        print(f"\n{player_char.name} uses {attack_type} on {target.name}!")
        if type_multiplier > 1.2: print("It's Super Effective!")
        elif type_multiplier < 1: print("It's not very effective...")
        print(f"Total Damage: {final_damage:,.0f} | Actual Damage: {actual_damage:,.0f}")
        if not target.is_alive(): print(f"{target.name} defeated!")
        self.press_any_key()

    # Остальные методы без изменений
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
        
        # Создаем список доступных предметов
        available_items = []
        for item, count in self.inventory.items():
            if count > 0:
                available_items.append(item)
        
        if not available_items:
            print("No items left!")
            self.press_any_key()
            return
        
        # Отображаем доступные предметы
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
            self.player_team.active_item_effects['def_boost'] = {'value': 50, 'turns': 2}
            message += "Recovered 70% HP and all allies' DEF +50% for 2 turns."
        elif selected_item == SupportItem.PRINCESS_SNAKE:
            heal_amount = self.player_team.max_hp * 0.55
            self.player_team.total_hp = min(self.player_team.max_hp, self.player_team.total_hp + heal_amount)
            self.player_team.active_item_effects['damage_reduction'] = {'value': 30, 'turns': 1}
            message += "Recovered 55% HP and damage received reduced by 30% for 1 turn."
        elif selected_item == SupportItem.WHIS:
            self.player_team.active_item_effects['damage_reduction'] = {'value': 40, 'turns': 2}
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
                if buffs: status_line += " | " + ", ".join(buffs)
                print(status_line)
        else:
            title = "===== YOUR TEAM ====="
            print(title)
            print(f"Team HP: {team.total_hp:,.0f} / {team.max_hp:,.0f}")
            if team.domain_active: print("DOMAIN ACTIVE: Infinite Zamasu")
            
            # ИСПРАВЛЕНИЕ: Отображение ВСЕХ баффов от предметов
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

            for i, member in enumerate(team.members):
                status_line = f"[{i}] {member.name} ({member.attribute.value}) | KI: {member.ki}/24"
                print(status_line)

    def display_battle_state(self):
        self.clear_screen()
        self.display_team(self.enemy_team, is_enemy=True)
        print("\n" + "=" * 80)
        self.display_team(self.player_team, is_enemy=False)
        print("\n" + "=" * 80)
        print(f"Turn: {self.turn_count}")

    def enemy_turn(self):
        for enemy in self.enemy_team.members:
            if not enemy.is_alive(): continue
            # Для простоты враг атакует случайного живого игрока
            alive_players = [m for m in self.player_team.members]
            if not alive_players: return
            
            random_player_char = random.choice(alive_players)
            damage = enemy.normal_attack() * self.get_type_multiplier(enemy.attribute, random_player_char.attribute)
            
            # Учитываем эффекты защиты
            actual_damage = self.player_team.take_damage(damage)
            
            self.display_battle_state()
            print(f"\n{enemy.name} attacks your team!")
            print(f"Base Damage: {int(damage):,.0f} | Actual Damage: {int(actual_damage):,.0f}")
            self.press_any_key()

            if not self.player_team.has_alive_members():
                return

    def start_battle(self):
        self.turn_count = 0
        while self.player_team.has_alive_members() and self.enemy_team.has_alive_members():
            self.turn_count += 1
            self.update_turn_effects()
            
            self.display_battle_state()
            print(f"\n=== ROUND {self.turn_count} START ===")
            
            for i in range(len(self.player_team.members)):
                if not self.enemy_team.has_alive_members(): break
                if not self.player_team.members[i].is_alive(): continue
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
        
        self.display_battle_state()
        if self.player_team.has_alive_members():
            print("\n\n" + "="*30 + "\n" + " "*11 + "VICTORY!" + "\n" + "="*30)
        else:
            print("\n\n" + "="*30 + "\n" + " "*11 + "DEFEAT..." + "\n" + "="*30)
        
        self.press_any_key()

# --- ГЛАВНАЯ ЧАСТЬ ---
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
    BattleSystem.press_any_key()

def start_new_battle():
    enemy_team = Team()
    vegeta = Character("Super Saiyan God SS Vegeta", Attribute.STR, 12000000, 370000, 150000, is_enemy=True)
    vegeta.damage_reduction = 66
    vegeta.max_attacks_per_turn = 3
    enemy_team.add_member(vegeta)

    player_team = Team(is_player=True)
    zamasu_links = ["Big Bad Bosses", "Dismal Future", "Godly Power", "Fused Fighter", "Fierce Battle"]
    
    player_team.add_member(Character("Dawn of an Ideal World Fusion Zamasu", Attribute.INT, 23000, 25000, 15000, is_leader=True, links=zamasu_links, categories=[Category.WORLDWIDE_CHAOS, Category.POTARA]), enemy_team.members)
    player_team.add_member(Character("Infinite Sanctuary Fusion Zamasu", Attribute.TEQ, 25000, 26000, 14000, links=zamasu_links, categories=[Category.REALM_OF_GODS, Category.WORLDWIDE_CHAOS, Category.FUSED_FIGHTERS, Category.TIME_TRAVELERS]), enemy_team.members)
    player_team.add_member(Character("Terrifying Zero Mortals Plan", Attribute.STR, 21000, 22000, 13000, links=zamasu_links, categories=[Category.POTARA, Category.FUTURE_SAGA]), enemy_team.members)
    
    player_team.apply_leader_skill(player_team.members[0])

    battle = BattleSystem(player_team, enemy_team)
    battle.start_battle()

if __name__ == "__main__":
    random.seed()
    main_menu()