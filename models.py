# models.py
import random

class Family:
    """代表一個家族，包含其成員、財富和聲望。"""
    def __init__(self, name):
        self.name = name
        self.members = [] # 儲存 Citizen 物件的引用
        self.family_wealth = 0
        self.reputation = random.uniform(0.1, 0.5) # 家族聲望，0-1.0

    def update_reputation(self):
        total_member_wealth = sum(c.wealth for c in self.members if c.alive)
        active_members_count = len([c for c in self.members if c.alive])
        if active_members_count > 0:
            avg_member_wealth = total_member_wealth / active_members_count
            self.reputation = max(0.1, min(1.0, self.reputation + (avg_member_wealth - 100) * 0.0005))
        for member in self.members:
            if member.alive:
                if member.profession in ["科學家", "醫生", "工程師", "教師"]:
                    self.reputation = min(1.0, self.reputation + 0.005)
                elif member.profession in ["小偷", "黑幫成員", "詐騙犯", "毒販"]:
                    self.reputation = max(0.01, self.reputation - 0.01)
        self.reputation = max(0.01, min(1.0, self.reputation))

class PoliticalParty:
    """代表一個政黨，包含其名稱、主要思想、政策主張和支持度。"""
    def __init__(self, name, ideology, platform):
        self.name = name
        self.ideology = ideology
        self.platform = platform
        self.support = 0
        self.leader = None

    def calculate_support(self, citizens):
        self.support = 0
        eligible_citizens = [c for c in citizens if c.alive]
        if not eligible_citizens:
            return
        for citizen in eligible_citizens:
            if citizen.ideology == self.ideology:
                self.support += 1
            if citizen.happiness > 0.7 and self.platform == "穩定發展":
                self.support += 0.5
            elif citizen.happiness < 0.3 and self.platform == "改革求變":
                self.support += 0.5
        self.support = min(self.support, len(eligible_citizens))

class Citizen:
    """代表城市中的一個市民。"""
    def __init__(self, name, parent1_ideology=None, parent2_ideology=None, parent1_trust=None, parent2_trust=None, parent1_emotion=None, parent2_emotion=None, family=None):
        self.name = name
        self.age = 0
        self.health = 1.0
        if parent1_trust is not None and parent2_trust is not None:
            self.trust = (parent1_trust + parent2_trust) / 2 + random.uniform(-0.1, 0.1)
            self.trust = max(0.1, min(1.0, self.trust))
        else:
            self.trust = random.uniform(0.4, 0.9)
        if parent1_emotion is not None and parent2_emotion is not None:
            self.happiness = (parent1_emotion + parent2_emotion) / 2 + random.uniform(-0.1, 0.1)
            self.happiness = max(0.1, min(1.0, self.happiness))
        else:
            self.happiness = random.uniform(0.4, 0.9)
        if parent1_ideology and parent2_ideology and random.random() < 0.7:
            self.ideology = random.choice(["保守", "自由", "科技信仰", "民族主義"])
            if parent1_ideology == parent2_ideology:
                if random.random() < 0.9:
                    self.ideology = parent1_ideology
            elif random.random() < 0.7:
                self.ideology = random.choice([parent1_ideology, parent2_ideology])
            else:
                self.ideology = random.choice(["保守", "自由", "科技信仰", "民族主義"])
        else:
            self.ideology = random.choice(["保守", "自由", "科技信仰", "民族主義"])
        self.city = None
        self.alive = True
        self.death_cause = None
        self.partner = None
        self.family = family
        all_professions = [
            "農民", "工人", "科學家", "商人", "無業",
            "醫生", "藝術家", "工程師", "教師", "服務員",
            "小偷", "黑幫成員", "詐騙犯", "毒販"
        ]
        self.profession = random.choice(all_professions)
        self.education_level = random.randint(0, 2)
        self.wealth = random.uniform(50, 200)
        if self.profession in ["小偷", "黑幫成員", "詐騙犯", "毒販"]:
            self.trust = max(0.1, self.trust - random.uniform(0.05, 0.15))
            self.health = max(0.1, self.health - random.uniform(0.02, 0.08))

class City:
    """代表一個城市及其屬性。"""
    def __init__(self, name):
        self.name = name
        self.citizens = []
        self.resources = {"糧食": 100, "能源": 100, "稅收": 0}
        self.events = []
        self.history = []
        self.birth_count = 0
        self.death_count = 0
        self.immigration_count = 0
        self.emigration_count = 0
        self.graveyard = []
        self.mass_movement_active = False
        self.cooperative_economy_level = 0.0
        self.government_type = random.choice(["民主制", "專制", "共和制"])
        self.specialization = random.choice(["農業", "工業", "科技", "服務", "軍事"])
        self.resource_shortage_years = 0
        self.political_parties = []
        self.ruling_party = None
        self.election_timer = random.randint(1, 5)

class Planet:
    """代表一個行星及其上的城市。"""
    def __init__(self, name, alien=False):
        self.name = name
        self.cities = []
        self.tech_levels = {"軍事": 0.5, "環境": 0.5, "醫療": 0.5, "生產": 0.5}
        self.pollution = 0
        self.alien = alien
        self.conflict_level = 0.0
        self.is_alive = True
        self.relations = {}
        self.war_with = set()
        self.war_duration = {}
        self.epidemic_active = False
        self.epidemic_severity = 0.0
        self.defense_level = 0
        self.shield_active = False
        self.allies = set()
        self.attack_cooldown = 0
        self.active_treaties = []
        self.unlocked_tech_breakthroughs = []

class Treaty:
    """代表行星間的條約。"""
    def __init__(self, treaty_type, signatories, duration, effects=None):
        self.type = treaty_type
        self.signatories = sorted(signatories)
        self.duration = duration
        self.effects = effects if effects else {}

class Galaxy:
    """代表整個星系，包含所有行星和年份。"""
    def __init__(self):
        self.planets = []
        self.year = 0
        self.global_events_log = []
        self.federation_leader = None
        self.active_federation_policy = None
        self.policy_duration_left = 0
        self.map_layout = {}
        self.families = {}
        self.prev_total_population = 0
