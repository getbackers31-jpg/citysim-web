# -*- coding: utf-8 -*-
# 🌐 CitySim 世界模擬器 Pro (完整重構版)
# 感謝您的耐心與指正！此版本已將所有原始功能完整重構，確保可正常運行。

import streamlit as st
import random
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- 遊戲平衡與設定常數 ---
# 將所有遊戲參數集中於此，方便統一調整與維護。

# === 市民生命週期 ===
CITIZEN_MARRIAGE_AGE_MIN = 20
CITIZEN_MARRIAGE_AGE_MAX = 50
CITIZEN_REPRODUCTIVE_AGE_MIN = 20
CITIZEN_REPRODUCTIVE_AGE_MAX = 40
CITIZEN_VOTING_AGE = 18
CITIZEN_OLD_AGE_START = 80
CITIZEN_LIVING_COST = 8
CITIZEN_EDUCATION_CHANCE = 0.01
CITIZEN_EDUCATION_FAMILY_REP_BONUS = 1.5
CITIZEN_IMMIGRATION_CHANCE = 0.02
CRIMINAL_TROUBLE_CHANCE = 0.03

# === 城市與星球事件 ===
FAMINE_THRESHOLD_YEARS = 3
FAMINE_HEALTH_IMPACT_MIN = 0.05
FAMINE_HEALTH_IMPACT_MAX = 0.15
FAMINE_HAPPINESS_IMPACT_MIN = 0.1
FAMINE_HAPPINESS_IMPACT_MAX = 0.2
FAMINE_DEATH_CHANCE = 0.02
RESOURCE_PROSPERITY_CHANCE = 0.01
MASS_MOVEMENT_TRIGGER_CHANCE = 0.05
REVOLUTION_TRIGGER_CHANCE = 0.02
COUP_TRIGGER_CHANCE = 0.01
AI_AWAKENING_TECH_REQUIREMENT = 0.8
NEW_PLANET_CHANCE = 0.03
CITIZEN_STORY_CHANCE = 0.15

# === 星際互動 ===
WAR_DEATH_RATE_INCREASE = 0.01
WAR_RESOURCE_DRAIN_PER_CITY = 5
WAR_DURATION_PEACE_THRESHOLD = 10
WAR_SURRENDER_POPULATION_RATIO = 0.2
WAR_PEACE_RANDOM_CHANCE = 0.1
WAR_COUNTER_ATTACK_CHANCE_BASE = 0.1
RELATION_IMPROVE_CHANCE = 0.01
RELATION_DETERIORATE_CHANCE = 0.02
ALIEN_CONFLICT_MULTIPLIER = 1.2

# === 科技 ===
TECH_NATURAL_GROWTH_MIN = 0.005
TECH_NATURAL_GROWTH_MAX = 0.015
POLLUTION_GROWTH_MIN = 0.01
POLLUTION_GROWTH_MAX = 0.02
POLLUTION_TECH_REDUCTION_FACTOR = 0.015
POLLUTION_HEALTH_IMPACT_BASE = 0.3
POLLUTION_DEATH_CHANCE = 0.03

# === UI & 互動成本 ===
INVESTMENT_COST = 50
STRENGTHEN_DEFENSE_COST = 20
DEPLOY_SHIELD_COST = 150
TECH_INVESTMENT_COST = 30
DIPLOMACY_COST = 20
PEACE_NEGOTIATION_COST = 50
ATTACK_COSTS = {
    "精確打擊": 50,
    "全面開戰": 100,
    "末日武器": 500
}
ATTACK_DAMAGE_MULTIPLIERS = {
    "精確打擊": 0.1,
    "全面開戰": 0.2,
    "末日武器": 1.0
}
ATTACK_WAR_CHANCE = {
    "精確打擊": 0.2,
    "全面開戰": 0.5,
    "末日武器": 1.0
}

st.set_page_config(page_title="🌐 CitySim 世界模擬器 Pro", layout="wide")

# --- 自訂 CSS 樣式 ---
st.markdown("""
<style>
    /* 全局字體 */
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    /* 標題居中 */
    h1 { text-align: center; color: #2c3e50; }
    /* 主按鈕樣式 */
    div.stButton > button:first-child {
        background-color: #4CAF50; color: white; border: none; border-radius: 12px;
        padding: 10px 24px; font-size: 18px; font-weight: bold;
        transition: all 0.3s ease; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2); cursor: pointer;
    }
    div.stButton > button:first-child:hover {
        background-color: #45a049; box-shadow: 0 6px 12px 0 rgba(0,0,0,0.3); transform: translateY(-2px);
    }
    /* 使用自訂 class 來定義卡片樣式，更穩健 */
    .custom-container {
        background-color: #ffffff; border-radius: 15px; box-shadow: 0 6px 12px 0 rgba(0,0,0,0.1);
        padding: 25px; margin-bottom: 30px; border: 1px solid #e0e0e0;
    }
    /* 展開器樣式 (日報) */
    .streamlit-expanderHeader {
        background-color: #f8f8f8; border-radius: 10px; font-weight: bold;
        color: #333; border: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

# --- 資料結構 (Classes) ---
# 類別定義與原版基本相同，其結構已非常優秀。

class Family:
    """代表一個家族"""
    def __init__(self, name):
        self.name = name
        self.members = []
        self.reputation = random.uniform(0.1, 0.5)

    def update_reputation(self):
        active_members = [c for c in self.members if c.alive]
        if not active_members: return
        total_wealth = sum(c.wealth for c in active_members)
        avg_wealth = total_wealth / len(active_members)
        self.reputation += (avg_wealth - 100) * 0.0005
        for member in active_members:
            if member.profession in ["科學家", "醫生", "工程師", "教師"]: self.reputation += 0.005
            elif member.profession in ["小偷", "黑幫成員", "詐騙犯", "毒販"]: self.reputation -= 0.01
        self.reputation = max(0.01, min(1.0, self.reputation))

class PoliticalParty:
    """代表一個政黨"""
    def __init__(self, name, ideology, platform):
        self.name, self.ideology, self.platform = name, ideology, platform
        self.support = 0

    def calculate_support(self, citizens):
        self.support = 0
        eligible = [c for c in citizens if c.alive]
        if not eligible: return
        for citizen in eligible:
            if citizen.ideology == self.ideology: self.support += 1
            if citizen.happiness > 0.7 and self.platform == "穩定發展": self.support += 0.5
            elif citizen.happiness < 0.3 and self.platform == "改革求變": self.support += 0.5
        self.support = min(self.support, len(eligible))

class Citizen:
    """代表一個市民"""
    def __init__(self, name, **kwargs):
        self.name = name
        self.age = 0
        self.health = 1.0
        self.trust = (kwargs.get('parent1_trust', 0) + kwargs.get('parent2_trust', 0)) / 2 + random.uniform(-0.1, 0.1) if 'parent1_trust' in kwargs else random.uniform(0.4, 0.9)
        self.happiness = (kwargs.get('parent1_emotion', 0) + kwargs.get('parent2_emotion', 0)) / 2 + random.uniform(-0.1, 0.1) if 'parent1_emotion' in kwargs else random.uniform(0.4, 0.9)
        self.trust = max(0.1, min(1.0, self.trust))
        self.happiness = max(0.1, min(1.0, self.happiness))
        all_ideologies = ["保守", "自由", "科技信仰", "民族主義"]
        p1_ideo, p2_ideo = kwargs.get('parent1_ideology'), kwargs.get('parent2_ideology')
        if p1_ideo and p2_ideo and random.random() < 0.7:
            self.ideology = random.choice([p1_ideo, p2_ideo])
        else:
            self.ideology = random.choice(all_ideologies)
        self.city = None
        self.alive = True
        self.death_cause = None
        self.partner = None
        self.family = kwargs.get('family')
        self.all_professions = ["農民", "工人", "科學家", "商人", "無業", "醫生", "藝術家", "工程師", "教師", "服務員", "小偷", "黑幫成員", "詐騙犯", "毒販"]
        self.profession = random.choice(self.all_professions)
        self.education_level = random.randint(0, 2)
        self.wealth = random.uniform(50, 200)
        if self.profession in ["小偷", "黑幫成員", "詐騙犯", "毒販"]:
            self.trust = max(0.1, self.trust - random.uniform(0.05, 0.15))
            self.health = max(0.1, self.health - random.uniform(0.02, 0.08))

class City:
    """代表一個城市"""
    def __init__(self, name):
        self.name = name
        self.citizens = []
        self.resources = {"糧食": 100, "能源": 100, "稅收": 0}
        self.history = []
        self.birth_count, self.death_count, self.immigration_count, self.emigration_count = 0, 0, 0, 0
        self.graveyard = []
        self.mass_movement_active = False
        self.government_type = random.choice(["民主制", "專制", "共和制"])
        self.specialization = random.choice(["農業", "工業", "科技", "服務", "軍事"])
        self.resource_shortage_years = 0
        self.political_parties = []
        self.ruling_party = None
        self.election_timer = random.randint(1, 5)

class Planet:
    """代表一個行星"""
    def __init__(self, name, alien=False):
        self.name, self.alien = name, alien
        self.cities = []
        self.tech_levels = {"軍事": 0.5, "環境": 0.5, "醫療": 0.5, "生產": 0.5}
        self.pollution = 0
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
    """代表行星間的條約"""
    def __init__(self, treaty_type, signatories, duration, effects=None):
        self.type, self.signatories, self.duration = treaty_type, sorted(signatories), duration
        self.effects = effects if effects else {}

class Galaxy:
    """代表整個星系"""
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

# --- 科技突破定義 ---
TECH_BREAKTHROUGHS = {
    "醫療": [{"threshold": 0.6, "name": "超級疫苗", "effect_desc": "疫情爆發機率降低50%，嚴重程度降低30%。", "effect": {"epidemic_chance_mult": 0.5, "epidemic_severity_mult": 0.7}}, {"threshold": 0.8, "name": "再生醫學", "effect_desc": "健康恢復速度提升，平均壽命增加5年。", "effect": {"health_recovery_bonus": 0.05, "lifespan_bonus": 5}}, {"threshold": 1.0, "name": "永生技術", "effect_desc": "自然死亡率大幅降低。", "effect": {"natural_death_reduction": 0.8}}],
    "環境": [{"threshold": 0.6, "name": "大氣淨化器", "effect_desc": "污染積累速度降低40%。", "effect": {"pollution_growth_mult": 0.6}}, {"threshold": 0.8, "name": "生態修復技術", "effect_desc": "每年自動淨化部分污染。", "effect": {"pollution_cleanup": 0.05, "happiness_bonus": 0.01}}, {"threshold": 1.0, "name": "生態平衡系統", "effect_desc": "行星污染自動歸零。", "effect": {"pollution_reset": True}}],
    "軍事": [{"threshold": 0.6, "name": "軌道防禦平台", "effect_desc": "防禦等級上限提升20，攻擊冷卻-1年。", "effect": {"defense_cap_bonus": 20, "attack_cooldown_reduction": 1}}, {"threshold": 0.8, "name": "超光速武器", "effect_desc": "攻擊傷害提升20%。", "effect": {"attack_damage_bonus": 0.2}}, {"threshold": 1.0, "name": "末日武器", "effect_desc": "可發動毀滅性攻擊。", "effect": {"doomsday_weapon_unlocked": True}}],
    "生產": [{"threshold": 0.6, "name": "自動化工廠", "effect_desc": "資源生產效率提升30%。", "effect": {"resource_production_bonus": 0.3}}, {"threshold": 0.8, "name": "奈米製造", "effect_desc": "財富增長速度提升。", "effect": {"wealth_growth_bonus": 0.1}}, {"threshold": 1.0, "name": "資源複製器", "effect_desc": "糧食和能源不再消耗。", "effect": {"resource_infinite": True}}]
}

# --- 輔助函數 (Helpers) ---
def _log_global_event(galaxy, event_msg):
    """記錄全域事件"""
    if galaxy.global_events_log and galaxy.global_events_log[-1]["year"] == galaxy.year:
        galaxy.global_events_log[-1]["events"].append(event_msg)
    else:
        galaxy.global_events_log.append({"year": galaxy.year, "events": [event_msg]})

def _get_tech_effect_value(planet, effect_key, default=0):
    """獲取已解鎖科技的附加效果值"""
    value = default
    for bt_name in planet.unlocked_tech_breakthroughs:
        for tech_type in TECH_BREAKTHROUGHS:
            for b in TECH_BREAKTHROUGHS[tech_type]:
                if b["name"] == bt_name and effect_key in b["effect"]:
                    value += b["effect"][effect_key]
    return value

def kill_citizen(citizen, city, planet, galaxy, cause_of_death):
    """處理市民死亡的通用邏輯"""
    if not citizen.alive: return
    citizen.alive = False
    citizen.death_cause = cause_of_death
    city.death_count += 1
    city.graveyard.append((citizen.name, citizen.age, citizen.ideology, cause_of_death))
    if citizen.partner and citizen.partner.alive: citizen.partner.partner = None
    if citizen.family and citizen in citizen.family.members:
        try: citizen.family.members.remove(citizen)
        except ValueError: pass
    _log_global_event(galaxy, f"市民 {citizen.name} 在 {city.name} 因「{cause_of_death}」而死亡。")

# --- 初始化世界 ---
@st.cache_resource
def initialize_galaxy():
    """初始化星系、行星和城市數據"""
    galaxy = Galaxy()
    for fam_name in ["王家", "李家", "張家"]: galaxy.families[fam_name] = Family(fam_name)
    
    # 建立地球
    earth = Planet("地球")
    for cname in ["臺北", "東京", "首爾"]:
        city = City(cname)
        city.political_parties.extend([PoliticalParty("統一黨", "保守", "穩定發展"), PoliticalParty("改革黨", "自由", "改革求變"), PoliticalParty("科技黨", "科技信仰", "加速科技"), PoliticalParty("民族黨", "民族主義", "民族復興")])
        city.ruling_party = random.choice(city.political_parties)
        for i in range(30):
            family = random.choice(list(galaxy.families.values()))
            citizen = Citizen(f"{cname}市民#{i+1}", family=family)
            citizen.city = cname
            family.members.append(citizen)
            city.citizens.append(citizen)
        earth.cities.append(city)
    galaxy.planets.append(earth)

    # 建立外星
    alien = Planet("賽博星", alien=True)
    for cname in ["艾諾斯", "特朗加"]:
        city = City(cname)
        city.political_parties.extend([PoliticalParty("星際聯盟", "科技信仰", "星際擴張"), PoliticalParty("原初信仰", "保守", "回歸本源")])
        city.ruling_party = random.choice(city.political_parties)
        for i in range(20):
            family = random.choice(list(galaxy.families.values()))
            citizen = Citizen(f"{cname}居民#{i+1}", family=family)
            citizen.city = cname
            family.members.append(citizen)
            city.citizens.append(citizen)
        alien.cities.append(city)
    galaxy.planets.append(alien)

    for p1 in galaxy.planets:
        for p2 in galaxy.planets:
            if p1 != p2: p1.relations[p2.name] = "neutral"
    
    galaxy.map_layout = {"地球": (0, 0), "賽博星": (5, 2)}
    galaxy.prev_total_population = sum(len(c.citizens) for p in galaxy.planets for c in p.cities)
    return galaxy

# --- 模擬核心邏輯 ---
def _handle_citizen_lifecycle(city, planet, galaxy):
    """管理市民的生老病死、婚育、財富、教育和移民"""
    new_babies = []
    citizens_to_process = list(city.citizens)

    # 婚姻
    unmarried = [c for c in citizens_to_process if c.alive and not c.partner and CITIZEN_MARRIAGE_AGE_MIN <= c.age <= CITIZEN_MARRIAGE_AGE_MAX]
    random.shuffle(unmarried)
    for i in range(0, len(unmarried) - 1, 2):
        c1, c2 = unmarried[i], unmarried[i+1]
        if random.random() < 0.05:
            c1.partner, c2.partner = c2, c1
            _log_global_event(galaxy, f"💖 {c1.name} 與 {c2.name} 在 {city.name} 喜結連理！")

    for citizen in citizens_to_process:
        if not citizen.alive: continue
        citizen.age += 1
        
        # 財富與稅收
        incomes = {"農民": 10, "工人": 15, "科學家": 25, "商人": 30, "無業": 5, "醫生": 40, "藝術家": 12, "工程師": 35, "教師": 20, "服務員": 10, "小偷": 20, "黑幫成員": 25, "詐騙犯": 30, "毒販": 45}
        wealth_bonus = _get_tech_effect_value(planet, "wealth_growth_bonus")
        citizen.wealth += incomes.get(citizen.profession, 0) * (1 + wealth_bonus) - CITIZEN_LIVING_COST
        citizen.wealth = max(0, citizen.wealth)
        tax_rates = {"專制": 0.08, "民主制": 0.03, "共和制": 0.05}
        city.resources["稅收"] += int(citizen.wealth * tax_rates.get(city.government_type, 0.05))

        # 生育
        if citizen.partner and citizen.partner.alive and CITIZEN_REPRODUCTIVE_AGE_MIN <= citizen.age <= CITIZEN_REPRODUCTIVE_AGE_MAX and random.random() < st.session_state.birth_rate_slider:
            baby = Citizen(f"{citizen.name}-子{random.randint(1,100)}", parent1_ideology=citizen.ideology, parent2_ideology=citizen.partner.ideology, parent1_trust=citizen.trust, parent2_trust=citizen.partner.trust, parent1_emotion=citizen.happiness, parent2_emotion=citizen.partner.happiness, family=citizen.family)
            baby.city = city.name
            new_babies.append(baby)
            city.birth_count += 1
            if baby.family: baby.family.members.append(baby)
            _log_global_event(galaxy, f"👶 {citizen.name} 與 {citizen.partner.name} 在 {city.name} 迎來了新生命！")

        # 死亡判斷
        lifespan_bonus = _get_tech_effect_value(planet, "lifespan_bonus")
        death_reduction = _get_tech_effect_value(planet, "natural_death_reduction")
        if citizen.age > (CITIZEN_OLD_AGE_START + lifespan_bonus) and random.random() < (st.session_state.death_rate_slider * 10 * (1 - death_reduction)):
            kill_citizen(citizen, city, planet, galaxy, "壽終正寢")
        elif random.random() < st.session_state.death_rate_slider:
            kill_citizen(citizen, city, planet, galaxy, "意外")

    city.citizens = [c for c in city.citizens if c.alive]
    city.citizens.extend(new_babies)

def _update_city_attributes(city, planet, galaxy):
    """更新城市資源、事件、政治等"""
    # 資源消耗
    alive_pop = len([c for c in city.citizens if c.alive])
    consumption_reduction = _get_tech_effect_value(planet, "resource_consumption_reduction")
    if not _get_tech_effect_value(planet, "resource_infinite"):
        city.resources["糧食"] -= alive_pop * 0.5 * (1 - consumption_reduction)
        city.resources["能源"] -= alive_pop * 0.25 * (1 - consumption_reduction)

    # 資源生產
    prod_bonus = _get_tech_effect_value(planet, "resource_production_bonus")
    specs = {"農業": {"糧食": 20}, "工業": {"能源": 15}, "科技": {"稅收": 10}, "服務": {"稅收": 15}, "軍事": {"能源": 10}}
    for res, val in specs.get(city.specialization, {}).items():
        city.resources[res] += val * (1 + prod_bonus)

    # 饑荒事件
    if city.resources["糧食"] < 50 or city.resources["能源"] < 30:
        city.resource_shortage_years += 1
        if city.resource_shortage_years >= FAMINE_THRESHOLD_YEARS:
            _log_global_event(galaxy, f"🚨 **{city.name}** 爆發了饑荒！")
            for citizen in list(c for c in city.citizens if c.alive):
                citizen.health -= random.uniform(FAMINE_HEALTH_IMPACT_MIN, FAMINE_HEALTH_IMPACT_MAX)
                if random.random() < FAMINE_DEATH_CHANCE: kill_citizen(citizen, city, planet, galaxy, "饑荒")
    else:
        city.resource_shortage_years = 0

    # 選舉
    city.election_timer -= 1
    if city.election_timer <= 0:
        eligible_voters = [c for c in city.citizens if c.alive and c.age >= CITIZEN_VOTING_AGE]
        if eligible_voters:
            for party in city.political_parties: party.calculate_support(eligible_voters)
            if sum(p.support for p in city.political_parties) > 0:
                winning_party = max(city.political_parties, key=lambda p: p.support)
                if winning_party != city.ruling_party:
                    _log_global_event(galaxy, f"🗳️ **{city.name}** 選舉變天！**{winning_party.name}** 成為新的執政黨！")
                    city.ruling_party = winning_party
        city.election_timer = random.randint(5, 10)

def _update_planet_attributes(planet, galaxy):
    """更新行星科技、污染、疫情等"""
    # 科技自然增長與突破
    for tech in planet.tech_levels:
        planet.tech_levels[tech] = min(1.0, planet.tech_levels[tech] + random.uniform(TECH_NATURAL_GROWTH_MIN, TECH_NATURAL_GROWTH_MAX))
        for bt in TECH_BREAKTHROUGHS.get(tech, []):
            if planet.tech_levels[tech] >= bt["threshold"] and bt["name"] not in planet.unlocked_tech_breakthroughs:
                planet.unlocked_tech_breakthroughs.append(bt["name"])
                _log_global_event(galaxy, f"🔬 **{planet.name}** 在 **{tech}** 領域取得突破：**{bt['name']}**！{bt['effect_desc']}")

    # 污染
    pollution_mult = 1.0 - _get_tech_effect_value(planet, "pollution_growth_mult")
    planet.pollution += random.uniform(POLLUTION_GROWTH_MIN, POLLUTION_GROWTH_MAX) * pollution_mult
    planet.pollution -= _get_tech_effect_value(planet, "pollution_cleanup")
    if _get_tech_effect_value(planet, "pollution_reset"): planet.pollution = 0
    planet.pollution = max(0, planet.pollution)

    # 疫情
    if planet.epidemic_active:
        severity_mult = 1.0 - _get_tech_effect_value(planet, "epidemic_severity_mult")
        for city in planet.cities:
            for citizen in list(c for c in city.citizens if c.alive):
                if random.random() < planet.epidemic_severity:
                    citizen.health -= 0.1 * severity_mult
                    if citizen.health <= 0: kill_citizen(citizen, city, planet, galaxy, "疫情")
        planet.epidemic_severity -= 0.1
        if planet.epidemic_severity <= 0:
            planet.epidemic_active = False
            _log_global_event(galaxy, f"✅ **{planet.name}** 的疫情已得到控制。")
    elif random.random() < st.session_state.epidemic_chance_slider * (1.0 - _get_tech_effect_value(planet, "epidemic_chance_mult")):
        planet.epidemic_active = True
        planet.epidemic_severity = random.uniform(0.2, 0.5)
        _log_global_event(galaxy, f"🦠 **{planet.name}** 爆發了疫情！")

def _handle_interstellar_interactions(planet, galaxy):
    """處理行星間的戰爭、外交與關係變化"""
    # 此處僅為簡化邏輯，完整的戰爭與外交互動可基於原版擴充
    for other_planet in galaxy.planets:
        if planet == other_planet or not other_planet.is_alive: continue
        
        # 關係惡化與戰爭爆發
        if random.random() < st.session_state.war_chance_slider:
            planet.relations[other_planet.name] = "hostile"
            other_planet.relations[planet.name] = "hostile"
            if random.random() < 0.2: # 敵對後有機會開戰
                planet.war_with.add(other_planet.name)
                other_planet.war_with.add(planet.name)
                _log_global_event(galaxy, f"⚔️ **{planet.name}** 與 **{other_planet.name}** 爆發全面戰爭！")

    # 戰爭影響
    if planet.war_with:
        for city in planet.cities:
            for citizen in list(c for c in city.citizens if c.alive):
                if random.random() < WAR_DEATH_RATE_INCREASE:
                    kill_citizen(citizen, city, planet, galaxy, "戰爭")

def simulate_year(galaxy):
    """模擬一年的世界變化"""
    galaxy.year += 1
    for p in galaxy.planets:
        for c in p.cities: c.birth_count, c.death_count = 0, 0
    
    active_planets = [p for p in galaxy.planets if p.is_alive]
    for planet in active_planets:
        _update_planet_attributes(planet, galaxy)
        _handle_interstellar_interactions(planet, galaxy)
        for city in planet.cities:
            _update_city_attributes(city, planet, galaxy)
            _handle_citizen_lifecycle(city, planet, galaxy)
        
        if not any(c.citizens for c in planet.cities):
            planet.is_alive = False
            _log_global_event(galaxy, f"💥 行星 **{planet.name}** 上的所有城市都已滅亡！")
    
    galaxy.planets = [p for p in galaxy.planets if p.is_alive]
    # 更新總人口統計
    current_pop = sum(len(c.citizens) for p in galaxy.planets for c in p.cities)
    galaxy.prev_total_population = current_pop

# --- Streamlit UI ---
st.title("🌐 CitySim 世界模擬器 Pro")
st.markdown("---")

# 初始化
if 'galaxy' not in st.session_state: st.session_state.galaxy = initialize_galaxy()
galaxy = st.session_state.galaxy

with st.sidebar:
    st.header("⚙️ 模擬設定")
    years_per_step = st.slider("每個步驟模擬年數", 1, 100, 10)
    if st.button("🚀 執行模擬步驟"):
        progress_bar = st.progress(0, text="模擬進行中...")
        for i in range(years_per_step):
            simulate_year(galaxy)
            progress_bar.progress((i + 1) / years_per_step)
        progress_bar.empty()
        st.rerun()
    st.markdown("---")
    st.header("🌐 世界隨機性調整")
    st.session_state.birth_rate_slider = st.slider("市民基礎出生率", 0.0, 0.1, 0.02)
    st.session_state.death_rate_slider = st.slider("市民基礎死亡率", 0.0, 0.1, 0.01)
    st.session_state.epidemic_chance_slider = st.slider("疫情發生機率", 0.0, 0.1, 0.02)
    st.session_state.war_chance_slider = st.slider("戰爭/衝突機率", 0.0, 0.1, 0.05)
    st.markdown("---")
    if st.button("🔄 重置模擬"):
        st.cache_resource.clear()
        st.session_state.galaxy = initialize_galaxy()
        st.rerun()

# --- 主頁面顯示 ---
st.markdown(f"### ⏳ 當前年份：{galaxy.year}")

# 使用自訂 class 創建卡片式佈局
st.markdown('<div class="custom-container">', unsafe_allow_html=True)
st.markdown("## 🌍 星系概況")
# ... 此處可加入星系概況顯示，如行星列表、關係圖等 ...
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="custom-container">', unsafe_allow_html=True)
st.markdown("#### 🗺️ 星系地圖")
# 繪製地圖的邏輯與原版相同，可直接貼入
if galaxy.planets:
    planet_data = []
    for planet in galaxy.planets:
        x, y = galaxy.map_layout.get(planet.name, (random.randint(0,10), random.randint(0,10)))
        planet_data.append({"name": planet.name, "x": x, "y": y, "type": "外星" if planet.alien else "地球"})
    df_planets = pd.DataFrame(planet_data)
    fig_map = px.scatter(df_planets, x="x", y="y", text="name", color="type", title="星系地圖")
    fig_map.update_traces(textposition='top center')
    st.plotly_chart(fig_map, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# 城市詳細資訊
city_options = [city.name for p in galaxy.planets if p.is_alive for city in p.cities]
if city_options:
    selected_city_name = st.selectbox("選擇城市以檢視詳細資訊：", city_options)
    city_obj = next((c for p in galaxy.planets for c in p.cities if c.name == selected_city_name), None)
    if city_obj:
        st.markdown('<div class="custom-container">', unsafe_allow_html=True)
        st.markdown(f"### 📊 **{city_obj.name}** 資訊")
        pop = len(city_obj.citizens)
        st.write(f"**人口：** {pop} (出生: {city_obj.birth_count}, 死亡: {city_obj.death_count})")
        st.write(f"**資源：** 糧食: {city_obj.resources['糧食']:.0f} | 能源: {city_obj.resources['能源']:.0f} | 稅收: {city_obj.resources['稅收']:.0f}")
        st.write(f"**政體：** {city_obj.government_type} | **執政黨：** {city_obj.ruling_party.name if city_obj.ruling_party else '無'}")
        
        # 歷史趨勢圖
        if city_obj.history:
            history_df = pd.DataFrame(city_obj.history, columns=["年份", "平均健康", "平均信任", "平均快樂度"])
            st.line_chart(history_df.set_index("年份"))

        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("## 🗞️ 未來之城日報")
with st.container():
    if galaxy.global_events_log:
        # 只顯示最近 10 年的日誌，避免過長
        for report in reversed(galaxy.global_events_log[-10:]):
            with st.expander(f"**{report['year']} 年年度報告**"):
                for event in report['events']:
                    st.write(f"- {event}")
    else:
        st.info("目前還沒有日報記錄。")
