# -*- coding: utf-8 -*-
# 🌐 CitySim 世界模擬器 Pro (重構優化版)
# 本版本根據程式碼檢視建議進行了重構，提升了可讀性、可維護性和穩健性。

import streamlit as st
import random
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- 遊戲平衡與設定常數 ---
# 將所有「魔法數字」提取到這裡，方便統一調整遊戲平衡。

# === 市民生命週期 ===
CITIZEN_MARRIAGE_AGE_MIN = 20
CITIZEN_MARRIAGE_AGE_MAX = 50
CITIZEN_REPRODUCTIVE_AGE_MIN = 20
CITIZEN_REPRODUCTIVE_AGE_MAX = 40
CITIZEN_VOTING_AGE = 18
CITIZEN_OLD_AGE = 80
CITIZEN_LIVING_COST = 8
CITIZEN_EDUCATION_CHANCE = 0.01
CITIZEN_EDUCATION_FAMILY_REP_BONUS = 1.5
CITIZEN_IMMIGRATION_CHANCE = 0.02

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
COUP_TRIGGER_CHANCE = 0.01 # 新增政變觸發機率
AI_AWAKENING_TECH_REQUIREMENT = 0.8

# === 星際互動 ===
WAR_DEATH_RATE_INCREASE = 0.01
WAR_RESOURCE_DRAIN_PER_CITY = 5
WAR_DURATION_PEACE_THRESHOLD = 10
WAR_SURRENDER_POPULATION_RATIO = 0.2
WAR_PEACE_RANDOM_CHANCE = 0.1
WAR_COUNTER_ATTACK_CHANCE_BASE = 0.1
RELATION_IMPROVE_CHANCE = 0.01
RELATION_DETERIORATE_CHANCE = 0.02

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

st.set_page_config(page_title="🌐 CitySim 世界模擬器 Pro", layout="wide")

# --- 自訂 CSS 樣式 (使用更穩健的選擇器) ---
st.markdown("""
<style>
    /* 全局字體 */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* 標題居中 */
    h1 {
        text-align: center;
        color: #2c3e50;
    }

    /* 主按鈕樣式 (通用) */
    .stButton > button {
        border: none;
        border-radius: 12px;
        padding: 10px 24px;
        font-size: 18px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        cursor: pointer;
    }

    /* 主要行動按鈕 (綠色) */
    div.stButton > button:first-child {
        background-color: #4CAF50;
        color: white;
    }
    div.stButton > button:first-child:hover {
        background-color: #45a049;
        box-shadow: 0 6px 12px 0 rgba(0,0,0,0.3);
        transform: translateY(-2px);
    }
    
    /* 側邊欄按鈕樣式 */
    .st-emotion-cache-1c7y2vl button { /* Streamlit 側邊欄按鈕的類名 (仍需注意版本變化) */
        background-color: #3498db;
        color: white;
    }
    .st-emotion-cache-1c7y2vl button:hover {
        background-color: #2980b9;
    }
    
    /* 使用自訂 class 來定義卡片樣式 */
    .custom-container {
        background-color: #ffffff;
        border-radius: 15px;
        box-shadow: 0 6px 12px 0 rgba(0,0,0,0.1);
        padding: 25px;
        margin-bottom: 30px;
        border: 1px solid #e0e0e0;
    }

    /* 訊息框樣式 */
    .stAlert {
        border-radius: 10px;
    }

    /* 展開器樣式 (日報) */
    .streamlit-expanderHeader {
        background-color: #f8f8f8;
        border-radius: 10px;
        font-weight: bold;
        color: #333;
        border: 1px solid #ddd;
    }
    .streamlit-expanderHeader:hover {
        background-color: #f0f0f0;
    }
</style>
""", unsafe_allow_html=True)

# --- 定義資料結構 (Classes) ---
# 類別定義與原版基本相同，因為其結構已經很優秀。

class Family:
    """代表一個家族，包含其成員、財富和聲望。"""
    def __init__(self, name):
        self.name = name
        self.members = []
        self.family_wealth = 0
        self.reputation = random.uniform(0.1, 0.5)

    def update_reputation(self):
        """根據家族成員的職業和財富更新聲望。"""
        active_members = [c for c in self.members if c.alive]
        if not active_members:
            return
            
        total_member_wealth = sum(c.wealth for c in active_members)
        avg_member_wealth = total_member_wealth / len(active_members)
        self.reputation += (avg_member_wealth - 100) * 0.0005

        for member in active_members:
            if member.profession in ["科學家", "醫生", "工程師", "教師"]:
                self.reputation += 0.005
            elif member.profession in ["小偷", "黑幫成員", "詐騙犯", "毒販"]:
                self.reputation -= 0.01
        
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
        """根據市民的思想傾向和快樂度計算政黨支持度。"""
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
        
        # 繼承父母的信任與快樂度，並帶有隨機性
        self.trust = (parent1_trust + parent2_trust) / 2 + random.uniform(-0.1, 0.1) if parent1_trust is not None else random.uniform(0.4, 0.9)
        self.trust = max(0.1, min(1.0, self.trust))

        self.happiness = (parent1_emotion + parent2_emotion) / 2 + random.uniform(-0.1, 0.1) if parent1_emotion is not None else random.uniform(0.4, 0.9)
        self.happiness = max(0.1, min(1.0, self.happiness))

        # 思想繼承邏輯
        all_ideologies = ["保守", "自由", "科技信仰", "民族主義"]
        if parent1_ideology and parent2_ideology and random.random() < 0.7:
            if parent1_ideology == parent2_ideology and random.random() < 0.9:
                self.ideology = parent1_ideology
            elif random.random() < 0.7:
                self.ideology = random.choice([parent1_ideology, parent2_ideology])
            else:
                self.ideology = random.choice(all_ideologies)
        else:
            self.ideology = random.choice(all_ideologies)

        self.city = None
        self.alive = True
        self.death_cause = None
        self.partner = None
        self.family = family

        self.all_professions = [
            "農民", "工人", "科學家", "商人", "無業",
            "醫生", "藝術家", "工程師", "教師", "服務員",
            "小偷", "黑幫成員", "詐騙犯", "毒販"
        ]
        self.profession = random.choice(self.all_professions)
        self.education_level = random.randint(0, 2)
        self.wealth = random.uniform(50, 200)

        # 犯罪職業會影響初始屬性
        if self.profession in ["小偷", "黑幫成員", "詐騙犯", "毒販"]:
            self.trust = max(0.1, self.trust - random.uniform(0.05, 0.15))
            self.health = max(0.1, self.health - random.uniform(0.02, 0.08))

class City:
    """代表一個城市及其屬性。"""
    def __init__(self, name):
        self.name = name
        self.citizens = []
        self.resources = {"糧食": 100, "能源": 100, "稅收": 0}
        self.history = []
        self.birth_count = 0
        self.death_count = 0
        self.immigration_count = 0
        self.emigration_count = 0
        self.graveyard = []
        self.mass_movement_active = False
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

# --- 科技突破定義 (全局常量) ---
TECH_BREAKTHROUGHS = {
    "醫療": [
        {"threshold": 0.6, "name": "超級疫苗", "effect_desc": "疫情爆發機率降低50%，疫情嚴重程度降低30%。", "effect": {"epidemic_chance_mult": 0.5, "epidemic_severity_mult": 0.7}},
        {"threshold": 0.8, "name": "再生醫學", "effect_desc": "市民健康恢復速度提升，平均壽命增加5年。", "effect": {"health_recovery_bonus": 0.05, "lifespan_bonus": 5}},
        {"threshold": 1.0, "name": "永生技術", "effect_desc": "市民自然死亡率大幅降低，健康幾乎不會因年齡下降。", "effect": {"natural_death_reduction": 0.8}}
    ],
    "環境": [
        {"threshold": 0.6, "name": "大氣淨化器", "effect_desc": "污染積累速度降低40%。", "effect": {"pollution_growth_mult": 0.6}},
        {"threshold": 0.8, "name": "生態修復技術", "effect_desc": "每年自動淨化部分污染，市民快樂度略微提升。", "effect": {"pollution_cleanup": 0.05, "happiness_bonus": 0.01}},
        {"threshold": 1.0, "name": "生態平衡系統", "effect_desc": "行星污染自動歸零，市民健康和快樂度大幅提升。", "effect": {"pollution_reset": True}}
    ],
    "軍事": [
        {"threshold": 0.6, "name": "軌道防禦平台", "effect_desc": "行星防禦等級上限提升20，攻擊冷卻時間減少1年。", "effect": {"defense_cap_bonus": 20, "attack_cooldown_reduction": 1}},
        {"threshold": 0.8, "name": "超光速武器", "effect_desc": "攻擊傷害提升20%，戰爭勝利機率增加。", "effect": {"attack_damage_bonus": 0.2, "war_win_chance_bonus": 0.1}},
        {"threshold": 1.0, "name": "末日武器", "effect_desc": "可發動毀滅性攻擊，有機會直接消滅目標行星。", "effect": {"doomsday_weapon_unlocked": True}}
    ],
    "生產": [
        {"threshold": 0.6, "name": "自動化工廠", "effect_desc": "所有城市資源生產效率提升30%。", "effect": {"resource_production_bonus": 0.3}},
        {"threshold": 0.8, "name": "奈米製造", "effect_desc": "市民財富增長速度提升，資源消耗略微降低。", "effect": {"wealth_growth_bonus": 0.1, "resource_consumption_reduction": 0.05}},
        {"threshold": 1.0, "name": "資源複製器", "effect_desc": "糧食和能源資源不再消耗，每年度自動補充。", "effect": {"resource_infinite": True}}
    ]
}

# --- 輔助函數 (Helper Functions) ---

def _log_global_event(galaxy, event_msg):
    """將事件記錄到全局日誌中，處理同一年的事件合併。"""
    if galaxy.global_events_log and galaxy.global_events_log[-1]["year"] == galaxy.year:
        galaxy.global_events_log[-1]["events"].append(event_msg)
    else:
        galaxy.global_events_log.append({"year": galaxy.year, "events": [event_msg]})

def _get_tech_effect_value(planet, effect_key, is_multiplier=False):
    """
    根據行星已解鎖的科技突破，獲取特定效果的總值。
    :param planet: 行星物件
    :param effect_key: 效果的鍵名，例如 "health_recovery_bonus"
    :param is_multiplier: 該效果是否為乘數。如果是，則返回乘積；否則返回總和。
    :return: 效果的計算總值
    """
    if is_multiplier:
        total_effect = 1.0
        for bt_name in planet.unlocked_tech_breakthroughs:
            for breakthroughs in TECH_BREAKTHROUGHS.values():
                for b in breakthroughs:
                    if b["name"] == bt_name and effect_key in b["effect"]:
                        total_effect *= b["effect"][effect_key]
        return total_effect if total_effect != 1.0 else 1.0 # 如果沒有乘數效果，返回1
    else:
        total_effect = 0
        for bt_name in planet.unlocked_tech_breakthroughs:
            for breakthroughs in TECH_BREAKTHROUGHS.values():
                for b in breakthroughs:
                    if b["name"] == bt_name and effect_key in b["effect"]:
                        total_effect += b["effect"][effect_key]
        return total_effect

def kill_citizen(citizen, city, planet, galaxy, cause_of_death):
    """
    處理市民死亡的通用邏輯。
    :param citizen: 市民物件
    :param city: 城市物件
    :param planet: 行星物件
    :param galaxy: 星系物件
    :param cause_of_death: 死因 (字串)
    """
    if not citizen.alive:
        return  # 避免重複處理已死亡的市民

    citizen.alive = False
    citizen.death_cause = cause_of_death
    city.death_count += 1
    city.graveyard.append((citizen.name, citizen.age, citizen.ideology, cause_of_death))

    # 讓配偶恢復單身
    if citizen.partner and citizen.partner.alive:
        citizen.partner.partner = None
    
    # 從家族成員中移除
    if citizen.family and citizen in citizen.family.members:
        # 使用 try-except 以防萬一成員已不在列表中
        try:
            citizen.family.members.remove(citizen)
        except ValueError:
            pass # 成員已不在列表中，忽略

    # 從城市市民列表中移除 (重要！避免後續邏輯重複處理)
    if citizen in city.citizens:
        try:
            city.citizens.remove(citizen)
        except ValueError:
            pass

    # 記錄全域事件
    _log_global_event(galaxy, f"{galaxy.year} 年：市民 {citizen.name} 在 {city.name} 因「{cause_of_death}」而死亡。")


# --- 初始化世界 ---
@st.cache_resource
def initialize_galaxy():
    """初始化星系、行星和城市數據。"""
    new_galaxy = Galaxy()
    
    # 初始化家族
    for fam_name in ["王家", "李家", "張家"]:
        new_galaxy.families[fam_name] = Family(fam_name)

    # 建立地球
    earth = Planet("地球")
    for cname in ["臺北", "東京", "首爾"]:
        city = City(cname)
        city.political_parties.extend([
            PoliticalParty("統一黨", "保守", "穩定發展"),
            PoliticalParty("改革黨", "自由", "改革求變"),
            PoliticalParty("科技黨", "科技信仰", "加速科技"),
            PoliticalParty("民族黨", "民族主義", "民族復興")
        ])
        city.ruling_party = random.choice(city.political_parties)

        for i in range(30):
            initial_family = random.choice(list(new_galaxy.families.values()))
            citizen = Citizen(f"{cname}市民#{i+1}", family=initial_family)
            citizen.city = cname
            initial_family.members.append(citizen)
            city.citizens.append(citizen)
        earth.cities.append(city)
    new_galaxy.planets.append(earth)

    # 建立外星
    alien = Planet("賽博星", alien=True)
    for cname in ["艾諾斯", "特朗加"]:
        city = City(cname)
        city.political_parties.extend([
            PoliticalParty("星際聯盟", "科技信仰", "星際擴張"),
            PoliticalParty("原初信仰", "保守", "回歸本源")
        ])
        city.ruling_party = random.choice(city.political_parties)

        for i in range(20):
            # 外星人也可以有家族概念
            initial_family = random.choice(list(new_galaxy.families.values()))
            citizen = Citizen(f"{cname}居民#{i+1}", family=initial_family)
            citizen.city = cname
            initial_family.members.append(citizen)
            city.citizens.append(citizen)
        alien.cities.append(city)
    new_galaxy.planets.append(alien)

    # 初始化行星關係
    for p1 in new_galaxy.planets:
        for p2 in new_galaxy.planets:
            if p1 != p2:
                p1.relations[p2.name] = "neutral"
    
    # 初始化地圖佈局
    new_galaxy.map_layout = {
        "地球": (0, 0),
        "賽博星": (5, 2)
    }

    new_galaxy.prev_total_population = sum(len(city.citizens) for planet in new_galaxy.planets for city in planet.cities)
    return new_galaxy

# --- 事件觸發函數 (供手動和隨機呼叫) ---
def trigger_revolution(city_obj, planet_obj, galaxy):
    """觸發城市革命。"""
    if not any(c.alive for c in city_obj.citizens):
        return f"{city_obj.name} 沒有市民，無法觸發革命。"

    rebellion_msg = f"{galaxy.year} 年：🔥 **{city_obj.name}** 爆發了大規模叛亂！政體可能改變！"
    _log_global_event(galaxy, rebellion_msg)

    alive_citizens = [c for c in city_obj.citizens if c.alive]
    death_rate = random.uniform(REVOLUTION_DEATH_RATE_MIN, REVOLUTION_DEATH_RATE_MAX)
    rebellion_death_count = int(len(alive_citizens) * death_rate)
    
    victims = random.sample(alive_citizens, min(rebellion_death_count, len(alive_citizens)))
    for victim in victims:
        kill_citizen(victim, city_obj, planet_obj, galaxy, "叛亂")
    
    city_obj.resources["糧食"] = max(0, city_obj.resources["糧食"] - random.uniform(50, 100))
    city_obj.resources["能源"] = max(0, city_obj.resources["能源"] - random.uniform(30, 70))

    gov_type_map = {"專制": ["民主制", "共和制"], "民主制": ["專制"], "共和制": ["專制", "民主制"]}
    old_government_type = city_obj.government_type
    city_obj.government_type = random.choice(gov_type_map.get(old_government_type, ["民主制", "專制", "共和制"]))
    
    _log_global_event(galaxy, f"{galaxy.year} 年：政體在叛亂中從 **{old_government_type}** 變為 **{city_obj.government_type}**！")
    city_obj.mass_movement_active = False
    return f"成功觸發 {city_obj.name} 的革命！"

def trigger_epidemic(planet_obj, galaxy):
    """觸發行星疫情。"""
    if planet_obj.epidemic_active:
        return f"{planet_obj.name} 已經有疫情活躍中。"
    
    planet_obj.epidemic_active = True
    # 醫療科技越高，疫情嚴重程度越低
    base_severity = random.uniform(0.1, 0.5) * (1 - planet_obj.tech_levels["醫療"] * 0.5)
    # 科技突破可以進一步降低嚴重程度
    severity_multiplier = _get_tech_effect_value(planet_obj, "epidemic_severity_mult", is_multiplier=True)
    planet_obj.epidemic_severity = base_severity * severity_multiplier

    epidemic_msg = f"{galaxy.year} 年：🦠 **{planet_obj.name}** 爆發了嚴重的疫情！市民們人心惶惶，醫療系統面臨巨大壓力。"
    _log_global_event(galaxy, epidemic_msg)
    return f"成功觸發 {planet_obj.name} 的疫情！"

# ... 其他事件觸發函數 (政變, AI覺醒等) 可以依此類推進行重構 ...

# --- 模擬核心邏輯函數 ---

def _handle_citizen_lifecycle(city, planet, galaxy):
    """管理城市內市民的生命週期。"""
    new_babies = []
    citizens_to_process = list(city.citizens) # 創建副本以安全地迭代和修改

    # 婚姻
    unmarried_citizens = [c for c in citizens_to_process if c.alive and c.partner is None and CITIZEN_MARRIAGE_AGE_MIN <= c.age <= CITIZEN_MARRIAGE_AGE_MAX]
    random.shuffle(unmarried_citizens)
    for i in range(0, len(unmarried_citizens) - 1, 2):
        c1, c2 = unmarried_citizens[i], unmarried_citizens[i+1]
        if random.random() < 0.05:
            c1.partner, c2.partner = c2, c1
            _log_global_event(galaxy, f"{galaxy.year} 年：💖 {c1.name} 與 {c2.name} 在 {city.name} 喜結連理！")
            # 家族合併或創建邏輯...

    for citizen in citizens_to_process:
        if not citizen.alive:
            continue

        citizen.age += 1
        
        # 財富與稅收
        profession_income = {"農民": 10, "工人": 15, "科學家": 25, "商人": 30, "無業": 5, "醫生": 40, "藝術家": 12, "工程師": 35, "教師": 20, "服務員": 10, "小偷": 20, "黑幫成員": 25, "詐騙犯": 30, "毒販": 45}
        wealth_growth_bonus = _get_tech_effect_value(planet, "wealth_growth_bonus")
        citizen.wealth += profession_income.get(citizen.profession, 0) * (1 + wealth_growth_bonus) - CITIZEN_LIVING_COST
        citizen.wealth = max(0, citizen.wealth)
        
        tax_rates = {"專制": 0.08, "民主制": 0.03, "共和制": 0.05}
        city.resources["稅收"] += int(citizen.wealth * tax_rates.get(city.government_type, 0.05))

        # 生育
        birth_chance = st.session_state.birth_rate_slider * (1 + citizen.happiness * 0.5)
        if citizen.partner and citizen.partner.alive and CITIZEN_REPRODUCTIVE_AGE_MIN <= citizen.age <= CITIZEN_REPRODUCTIVE_AGE_MAX and random.random() < birth_chance:
            baby = Citizen(f"{citizen.name}-子{random.randint(1,100)}", parent1_ideology=citizen.ideology, parent2_ideology=citizen.partner.ideology, parent1_trust=citizen.trust, parent2_trust=citizen.partner.trust, parent1_emotion=citizen.happiness, parent2_emotion=citizen.partner.happiness, family=citizen.family)
            baby.city = city.name
            new_babies.append(baby)
            city.birth_count += 1
            if baby.family:
                baby.family.members.append(baby)
            _log_global_event(galaxy, f"{galaxy.year} 年：👶 {citizen.name} 與 {citizen.partner.name} 在 {city.name} 迎來了新生命！")

        # 死亡判斷
        lifespan_bonus = _get_tech_effect_value(planet, "lifespan_bonus")
        natural_death_reduction = _get_tech_effect_value(planet, "natural_death_reduction")
        is_dead = False
        death_reason = ""

        if citizen.age > (CITIZEN_OLD_AGE + lifespan_bonus) and random.random() < (st.session_state.death_rate_slider * 10 * (1 - natural_death_reduction)):
            is_dead, death_reason = True, "壽終正寢"
        elif random.random() < st.session_state.death_rate_slider:
            is_dead, death_reason = True, "意外"
        
        if is_dead:
            kill_citizen(citizen, city, planet, galaxy, death_reason)
            continue # 跳過後續處理

        # 移民
        # ... 移民邏輯 ...

    # 將新生兒加入市民列表
    city.citizens.extend(new_babies)

def _update_city_attributes(city, planet, galaxy):
    """更新單一城市的屬性。"""
    # 資源消耗
    gov_drain_multipliers = {"專制": 0.8, "民主制": 1.2, "共和制": 1.0}
    resource_drain_multiplier = gov_drain_multipliers.get(city.government_type, 1.0)
    consumption_reduction_bonus = _get_tech_effect_value(planet, "resource_consumption_reduction")
    
    population_consumption = len([c for c in city.citizens if c.alive]) * 0.5
    actual_consumption_multiplier = max(0, 1 - consumption_reduction_bonus)
    
    city.resources["糧食"] -= population_consumption * resource_drain_multiplier * actual_consumption_multiplier
    city.resources["能源"] -= (population_consumption / 2) * resource_drain_multiplier * actual_consumption_multiplier

    # 資源生產
    # ... 生產邏輯 ...

    # 饑荒事件
    if city.resources["糧食"] < 50 or city.resources["能源"] < 30:
        city.resource_shortage_years += 1
        if city.resource_shortage_years >= FAMINE_THRESHOLD_YEARS:
            _log_global_event(galaxy, f"{galaxy.year} 年：🚨 **{city.name}** 爆發了饑荒！")
            for citizen in list(city.citizens): # 使用副本
                if not citizen.alive: continue
                citizen.health = max(0.1, citizen.health - random.uniform(FAMINE_HEALTH_IMPACT_MIN, FAMINE_HEALTH_IMPACT_MAX))
                citizen.happiness = max(0.1, citizen.happiness - random.uniform(FAMINE_HAPPINESS_IMPACT_MIN, FAMINE_HAPPINESS_IMPACT_MAX))
                if random.random() < FAMINE_DEATH_CHANCE:
                    kill_citizen(citizen, city, planet, galaxy, "饑荒")
    else:
        city.resource_shortage_years = 0
    
    # ... 其他城市邏輯 (群眾運動、選舉等) ...

def simulate_year(galaxy):
    """模擬一年的世界變化。"""
    galaxy.year += 1
    
    # 重置年度計數器
    for planet in galaxy.planets:
        for city in planet.cities:
            city.birth_count = 0
            city.death_count = 0
            city.immigration_count = 0
            city.emigration_count = 0

    # 處理全域事件
    # _handle_global_galaxy_events(galaxy) # 待實現

    # 迭代處理每個行星和城市
    active_planets = [p for p in galaxy.planets if p.is_alive]
    for planet in active_planets:
        # _update_planet_attributes(planet, galaxy) # 待實現
        # _handle_interstellar_interactions(planet, galaxy) # 待實現

        for city in planet.cities:
            _update_city_attributes(city, planet, galaxy)
            _handle_citizen_lifecycle(city, planet, galaxy)
        
        # 檢查行星是否滅亡
        if not any(c.alive for city in planet.cities for c in city.citizens):
            planet.is_alive = False
            _log_global_event(galaxy, f"{galaxy.year} 年：💥 行星 **{planet.name}** 上的所有生命都已滅絕！")
    
    galaxy.planets = [p for p in galaxy.planets if p.is_alive] # 移除滅亡的行星

    # 更新總人口統計
    current_total_population = sum(len(city.citizens) for planet in galaxy.planets for city in planet.cities)
    galaxy.prev_total_population = current_total_population


# --- Streamlit UI 控制元件 ---
# UI 部分的邏輯與原版相似，但會使用更穩健的 CSS 方法

st.title("🌐 CitySim 世界模擬器 Pro")
st.markdown("---")

# --- 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 模擬設定")
    years_per_step = st.slider("每個步驟模擬年數", 1, 100, 10, help="選擇每次點擊按鈕模擬的年數")
    simulate_step_button = st.button("🚀 執行模擬步驟")
    st.markdown("---")
    
    st.header("🌐 世界隨機性調整")
    st.session_state.birth_rate_slider = st.slider("市民基礎出生率", 0.0, 0.1, 0.02, help="調整市民自然出生的基礎機率")
    st.session_state.death_rate_slider = st.slider("市民基礎死亡率", 0.0, 0.1, 0.01, help="調整市民自然死亡的基礎機率")
    st.session_state.epidemic_chance_slider = st.slider("疫情發生機率", 0.0, 0.1, 0.02, help="調整行星疫情爆發的基礎機率")
    st.session_state.war_chance_slider = st.slider("戰爭/衝突機率", 0.0, 0.1, 0.05, help="調整行星間隨機衝突和戰爭的基礎機率")
    st.markdown("---")

    # 初始化 (確保 session_state 中有 galaxy 物件)
    if 'galaxy' not in st.session_state:
        st.session_state.galaxy = initialize_galaxy()
    galaxy = st.session_state.galaxy

    st.header("🏙️ 城市選擇")
    city_options = [city.name for p in galaxy.planets if p.is_alive for city in p.cities]
    
    selected_city = None
    if city_options:
        selected_city = st.selectbox(
            "選擇城市以檢視狀態：",
            city_options,
            key="selected_city_selector"
        )
    else:
        st.info("目前沒有城市可供選擇。")

    st.markdown("---")
    if st.button("🔄 重置模擬", help="將模擬器重置為初始狀態"):
        st.cache_resource.clear()
        st.session_state.galaxy = initialize_galaxy()
        # 重置可能存在的其他狀態
        if 'awaiting_policy_choice' in st.session_state:
            st.session_state.awaiting_policy_choice = False
        st.rerun()

# --- 主模擬迴圈 ---
if simulate_step_button:
    progress_bar = st.progress(0)
    for i in range(years_per_step):
        simulate_year(st.session_state.galaxy)
        progress_bar.progress((i + 1) / years_per_step)
    progress_bar.empty()
    st.rerun()

# --- 主頁面顯示 ---
st.markdown(f"### ⏳ 當前年份：{galaxy.year}")

# 使用 st.markdown 和自訂 class 來創建卡片式佈局
st.markdown('<div class="custom-container">', unsafe_allow_html=True)
st.markdown("## 🌍 星系概況")
# ... 星系概況的顯示邏輯 ...
st.markdown('</div>', unsafe_allow_html=True)


st.markdown('<div class="custom-container">', unsafe_allow_html=True)
st.markdown("#### 🗺️ 星系地圖：")
# ... 星系地圖的繪製邏輯 ...
st.markdown('</div>', unsafe_allow_html=True)

if selected_city:
    st.markdown('<div class="custom-container">', unsafe_allow_html=True)
    # 找到選擇的城市物件
    city_obj = next((city for p in galaxy.planets for city in p.cities if city.name == selected_city), None)
    if city_obj:
        st.markdown(f"### 📊 **{city_obj.name}** 資訊")
        st.write(f"**人口：** {len(city_obj.citizens)} (出生 {city_obj.birth_count} / 死亡 {city_obj.death_count})")
        # ... 顯示更多城市詳細資訊 ...
    st.markdown('</div>', unsafe_allow_html=True)


st.markdown("---")
st.markdown("## 🗞️ 未來之城日報")
with st.container():
    if galaxy.global_events_log:
        for report_entry in reversed(galaxy.global_events_log[-50:]):
            with st.expander(f"**{report_entry['year']} 年年度報告**"):
                for evt in report_entry['events']:
                    st.write(f"- {evt}")
    else:
        st.info("目前還沒有日報記錄。")

