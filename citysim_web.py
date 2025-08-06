# -*- coding: utf-8 -*-
# 🌐 CitySim 世界模擬器 Pro (精簡優化版)
import streamlit as st
import random
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="🌐 CitySim 世界模擬器 Pro", layout="wide")

# --- 自訂 CSS 樣式 ---
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

    /* 按鈕樣式 */
    div.stButton > button:first-child {
        background-color: #4CAF50; /* 綠色 */
        color: white;
        border: none;
        border-radius: 12px;
        padding: 10px 24px;
        font-size: 18px;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        cursor: pointer;
    }
    div.stButton > button:first-child:hover {
        background-color: #45a049; /* 深綠色 */
        box-shadow: 0 6px 12px 0 rgba(0,0,0,0.3);
        transform: translateY(-2px);
    }

    /* 側邊欄按鈕樣式 (與主按鈕區分) */
    .st-emotion-cache-1c7y2vl button { /* 這是 Streamlit 側邊欄按鈕的類名 */
        background-color: #3498db; /* 藍色 */
        color: white;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 16px;
        transition: all 0.2s ease;
    }
    .st-emotion-cache-1c7y2vl button:hover {
        background-color: #2980b9; /* 深藍色 */
        transform: translateY(-1px);
    }

    /* 卡片樣式容器 */
    .st-emotion-cache-eczf16 { /* 這是 st.container 的一個常見類名，可能需要根據實際部署調整 */
        background-color: #ffffff;
        border-radius: 15px;
        box-shadow: 0 6px 12px 0 rgba(0,0,0,0.1);
        padding: 25px;
        margin-bottom: 30px;
        border: 1px solid #e0e0e0;
    }

    /* 訊息框樣式 */
    .st-emotion-cache-1xw879w { /* st.info, st.warning 的容器 */
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
    }

    /* 展開器樣式 (日報) */
    .streamlit-expanderHeader {
        background-color: #f8f8f8;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 8px;
        font-weight: bold;
        color: #333;
        border: 1px solid #ddd;
        transition: background-color 0.2s ease;
    }
    .streamlit-expanderHeader:hover {
        background-color: #f0f0f0;
    }

    /* 進度條文字顏色 */
    .st-emotion-cache-10q2x2u { /* st.markdown 的容器 */
        color: #e67e22; /* 橙色 */
        font-weight: bold;
    }

</style>
""", unsafe_allow_html=True)

# --- 定義資料結構 ---

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
        total_member_wealth = sum(c.wealth for c in active_members)
        active_members_count = len(active_members)
        
        if active_members_count > 0:
            avg_member_wealth = total_member_wealth / active_members_count
            self.reputation = max(0.1, min(1.0, self.reputation + (avg_member_wealth - 100) * 0.0005))
        
        for member in active_members:
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
        
        self.trust = (parent1_trust + parent2_trust) / 2 + random.uniform(-0.1, 0.1) if parent1_trust is not None else random.uniform(0.4, 0.9)
        self.trust = max(0.1, min(1.0, self.trust))

        self.happiness = (parent1_emotion + parent2_emotion) / 2 + random.uniform(-0.1, 0.1) if parent1_emotion is not None else random.uniform(0.4, 0.9)
        self.happiness = max(0.1, min(1.0, self.happiness))

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

# --- 輔助函數 ---

def _log_global_event(galaxy, event_msg):
    """將事件記錄到全局日誌中，處理同一年的事件合併。"""
    if galaxy.global_events_log and galaxy.global_events_log[-1]["year"] == galaxy.year:
        galaxy.global_events_log[-1]["events"].append(event_msg)
    else:
        galaxy.global_events_log.append({"year": galaxy.year, "events": [event_msg]})

def _get_tech_effect_value(planet, effect_key):
    """根據行星已解鎖的科技突破，獲取特定效果的總值。"""
    total_effect = 0
    for bt_name in planet.unlocked_tech_breakthroughs:
        for tech_type, breakthroughs in TECH_BREAKTHROUGHS.items():
            for b in breakthroughs:
                if b["name"] == bt_name and effect_key in b["effect"]:
                    total_effect += b["effect"][effect_key]
    return total_effect

# --- 初始化世界 ---
@st.cache_resource
def initialize_galaxy():
    """初始化星系、行星和城市數據。"""
    new_galaxy = Galaxy()
    
    new_galaxy.families["王家"] = Family("王家")
    new_galaxy.families["李家"] = Family("李家")
    new_galaxy.families["張家"] = Family("張家")

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

    alien = Planet("賽博星", alien=True)
    for cname in ["艾諾斯", "特朗加"]:
        city = City(cname)
        city.political_parties.extend([
            PoliticalParty("星際聯盟", "科技信仰", "星際擴張"),
            PoliticalParty("原初信仰", "保守", "回歸本源")
        ])
        city.ruling_party = random.choice(city.political_parties)

        for i in range(20):
            initial_family = random.choice(list(new_galaxy.families.values()))
            citizen = Citizen(f"{cname}市民#{i+1}", family=initial_family)
            citizen.city = cname
            initial_family.members.append(citizen)
            city.citizens.append(citizen)
    alien.cities.append(city)
    new_galaxy.planets.append(alien)

    for p1 in new_galaxy.planets:
        for p2 in new_galaxy.planets:
            if p1 != p2:
                p1.relations[p2.name] = "neutral"
    
    new_galaxy.map_layout = {
        "地球": (0, 0),
        "賽博星": (5, 2)
    }

    new_galaxy.prev_total_population = sum(len(city.citizens) for planet in new_galaxy.planets for city in planet.cities)

    return new_galaxy

# 確保每次運行時，如果沒有緩存，則初始化星系
if 'galaxy' not in st.session_state:
    st.session_state.galaxy = initialize_galaxy()
galaxy = st.session_state.galaxy

# --- 事件觸發函數 (供手動和隨機呼叫) ---
def trigger_revolution(city_obj, current_year_global_events):
    """觸發城市革命。"""
    if not city_obj.citizens:
        return f"{city_obj.name} 沒有市民，無法觸發革命。"

    rebellion_msg = f"{galaxy.year} 年：🔥 **{city_obj.name}** 爆發了大規模叛亂！政體可能改變！"
    city_obj.events.append(rebellion_msg)
    current_year_global_events.append(rebellion_msg)

    alive_citizens_for_stats = [c for c in city_obj.citizens if c.alive]
    rebellion_death_count = int(len(alive_citizens_for_stats) * random.uniform(0.05, 0.15))
    for _ in range(rebellion_death_count):
        if alive_citizens_for_stats:
            victim = random.choice(alive_citizens_for_stats)
            victim.alive = False
            victim.death_cause = "叛亂"
            city_obj.death_count += 1
            city_obj.graveyard.append((victim.name, victim.age, victim.ideology, victim.death_cause))
            alive_citizens_for_stats.remove(victim)
    
    city_obj.resources["糧食"] = max(0, city_obj.resources["糧食"] - random.uniform(50, 100))
    city_obj.resources["能源"] = max(0, city_obj.resources["能源"] - random.uniform(30, 70))

    gov_type_map = {"專制": ["民主制", "共和制"], "民主制": ["專制"], "共和制": ["專制", "民主制"]}
    old_government_type = city_obj.government_type
    city_obj.government_type = random.choice(gov_type_map.get(city_obj.government_type, ["民主制", "專制", "共和制"]))
    
    current_year_global_events.append(f"{galaxy.year} 年：政體在叛亂中從 **{old_government_type}** 變為 **{city_obj.government_type}**！")
    city_obj.mass_movement_active = False
    return f"成功觸發 {city_obj.name} 的革命！"

def trigger_epidemic(planet_obj, current_year_global_events):
    """觸發行星疫情。"""
    if planet_obj.epidemic_active:
        return f"{planet_obj.name} 已經有疫情活躍中。"
    
    planet_obj.epidemic_active = True
    planet_obj.epidemic_severity = random.uniform(0.1, 0.5) * (1 - planet_obj.tech_levels["醫療"] * 0.5)
    epidemic_msg = f"{galaxy.year} 年：🦠 **{planet_obj.name}** 爆發了嚴重的疫情！市民們人心惶惶，醫療系統面臨巨大壓力。"
    for city in planet_obj.cities: city.events.append(epidemic_msg)
    current_year_global_events.append(epidemic_msg)
    return f"成功觸發 {planet_obj.name} 的疫情！"

def trigger_coup(city_obj, current_year_global_events):
    """觸發城市政變。"""
    if not city_obj.citizens:
        return f"{city_obj.name} 沒有市民，無法觸發政變。"
    
    coup_msg = f"{galaxy.year} 年：🚨 **{city_obj.name}** 發生了政變！權力在暗中易手，城市陷入短暫混亂。"
    city_obj.events.append(coup_msg)
    current_year_global_events.append(coup_msg)

    gov_type_map = {"民主制": "專制", "專制": random.choice(["民主制", "共和制"]), "共和制": "專制"}
    old_government_type = city_obj.government_type
    city_obj.government_type = gov_type_map.get(city_obj.government_type, city_obj.government_type) # Fallback to itself if not in map
    
    current_year_global_events.append(f"{galaxy.year} 年：政變導致政體從 **{old_government_type}** 變為 **{city_obj.government_type}**！新的統治者上台。")
    return f"成功觸發 {city_obj.name} 的政變！"

def trigger_ai_awakening(planet_obj, current_year_global_events):
    """觸發 AI 覺醒事件 (簡易版)。"""
    if planet_obj.alien:
        return f"外星行星 {planet_obj.name} 無法觸發 AI 覺醒。"
    
    if planet_obj.tech_levels["生產"] < 0.8:
        return f"{planet_obj.name} 的科技水平不足以觸發 AI 覺醒 (需要生產科技0.8)。"
    
    ai_msg = f"{galaxy.year} 年：🤖 **{planet_obj.name}** 的 AI 覺醒了！智慧生命的新紀元開啟，未來充滿未知與無限可能！"
    current_year_global_events.append(ai_msg)
    for city in planet_obj.cities:
        city.events.append(ai_msg)
        for citizen in [c for c in city.citizens if c.alive]:
            citizen.happiness = min(1.0, citizen.happiness + 0.1)
            citizen.trust = min(1.0, citizen.trust + 0.1)
    planet_obj.tech_levels["生產"] = min(1.0, planet_obj.tech_levels["生產"] + 0.1)
    planet_obj.tech_levels["軍事"] = min(1.0, planet_obj.tech_levels["軍事"] + 0.1)
    return f"成功觸發 {planet_obj.name} 的 AI 覺醒！"

# --- 模擬核心邏輯函數 ---

def _handle_global_galaxy_events(galaxy, current_year_global_events):
    """處理星系層級的事件，例如新行星的誕生、市民小故事、以及聯邦選舉和政策的應用。"""
    # 隨機生成市民小故事
    if random.random() < 0.15:
        all_active_citizens = [citizen for p in galaxy.planets if p.is_alive for c in p.cities for citizen in c.citizens if citizen.alive]
        if all_active_citizens:
            story_citizen = random.choice(all_active_citizens)
            story_templates = [
                f"市民 {story_citizen.name} (來自 {story_citizen.city}) 在當地市場發現了稀有香料，財富略有增加！",
                f"科學家 {story_citizen.name} (來自 {story_citizen.city}) 發表了關於星際旅行的新理論，引起廣泛關注。",
                f"藝術家 {story_citizen.name} (來自 {story_citizen.city}) 創作了一幅描繪和平星系的畫作，激勵了許多人。",
                f"工程師 {story_citizen.name} (來自 {story_citizen.city}) 成功修復了城市能源系統，避免了一場危機。",
                f"市民 {story_citizen.name} (來自 {story_citizen.city}) 參與了社區志願活動，提升了城市信任度。",
                f"無業的 {story_citizen.name} (來自 {story_citizen.city}) 終於找到了一份 {random.choice(['農民', '服務員'])} 的工作，生活開始好轉。",
                f"商人 {story_citizen.name} (來自 {story_citizen.city}) 成功拓展了跨行星貿易路線，為城市帶來了豐富資源。",
                f"醫生 {story_citizen.name} (來自 {story_citizen.city}) 發現了一種新的疾病治療方法，挽救了許多生命。",
                f"教師 {story_citizen.name} (來自 {story_citizen.city}) 的學生在聯邦科學競賽中獲得了第一名，為城市爭光。",
                f"服務員 {story_citizen.name} (來自 {story_citizen.city}) 以其熱情周到的服務贏得了市民的廣泛讚譽。",
                f"小偷 {story_citizen.name} (來自 {story_citizen.city}) 在一次行動中失手被捕，被關押了一段時間。",
                f"黑幫成員 {story_citizen.name} (來自 {story_citizen.city}) 在一次幫派衝突中受傷，健康狀況惡化。",
                f"詐騙犯 {story_citizen.name} (來自 {story_citizen.city}) 成功策劃了一場大型騙局，獲得了巨額財富。",
                f"毒販 {story_citizen.name} (來自 {story_citizen.city}) 的毒品交易被聯邦特工發現，面臨嚴峻的法律制裁。"
            ]
            _log_global_event(galaxy, f"{galaxy.year} 年：✨ {random.choice(story_templates)}")

    # 動態誕生新行星
    if random.random() < 0.03 and len(galaxy.planets) < 5:
        new_planet_name = f"新星系-{random.randint(100, 999)}"
        new_planet = Planet(new_planet_name, alien=True)
        num_new_cities = random.randint(1, 2)
        for i in range(num_new_cities):
            new_city_name = f"{new_planet_name}市#{i+1}"
            new_city = City(new_city_name)
            new_city.political_parties.extend([
                PoliticalParty(f"{new_city_name}和平黨", "自由", "和平發展"),
                PoliticalParty(f"{new_city_name}擴張黨", "民族主義", "星際擴張")
            ])
            new_city.ruling_party = random.choice(new_city.political_parties)

            for j in range(random.randint(10, 25)):
                initial_family = random.choice(list(new_galaxy.families.values()))
                citizen = Citizen(f"{new_city_name}市民#{j+1}", family=initial_family)
                citizen.city = new_city_name
                initial_family.members.append(citizen)
                new_city.citizens.append(citizen)
            new_planet.cities.append(new_city)
        
        for p in galaxy.planets:
            p.relations[new_planet.name] = "neutral"
            new_planet.relations[p.name] = "neutral"
        
        galaxy.planets.append(new_planet)
        _log_global_event(galaxy, f"{galaxy.year} 年：🔭 探測器發現了新的宜居行星 **{new_planet_name}**，並迅速建立了 {num_new_cities} 個定居點！")
        
        existing_coords = set(galaxy.map_layout.values())
        new_x, new_y = 0, 0
        while (new_x, new_y) in existing_coords:
            new_x = random.randint(0, 9)
            new_y = random.randint(0, 4)
        galaxy.map_layout[new_planet.name] = (new_x, new_y)

    # 星系聯邦選舉與政策
    if galaxy.year % 20 == 0 and galaxy.year > 0:
        active_planets_for_election = [p for p in galaxy.planets if p.is_alive and any(c.citizens for c in p.cities)]
        if active_planets_for_election:
            candidates = [random.choice([c for city in p.cities for c in city.citizens if c.alive]) for p in active_planets_for_election if any(c.citizens for c in p.cities)]
            
            if candidates:
                galaxy.federation_leader = max(candidates, key=lambda c: c.trust)
                _log_global_event(galaxy, f"{galaxy.year} 年：� 星系聯邦舉行了盛大的選舉！來自 {galaxy.federation_leader.city} 的市民 **{galaxy.federation_leader.name}** 以其卓越的信任度被選為新的聯邦領導人！")

                st.session_state.awaiting_policy_choice = True
                st.session_state.policy_effect = random.uniform(0.01, 0.03)
                st.session_state.policy_duration = random.randint(3, 7)
                st.session_state.temp_global_events = current_year_global_events
                st.rerun()
            else:
                _log_global_event(galaxy, f"{galaxy.year} 年：⚠️ 無法舉行聯邦選舉，因為沒有足夠的活著的市民。")
        else:
            _log_global_event(galaxy, f"{galaxy.year} 年：⚠️ 無法舉行聯邦選舉，因為沒有足夠的活著的行星。")

    # 應用聯邦政策效果
    if galaxy.active_federation_policy and galaxy.policy_duration_left > 0:
        policy = galaxy.active_federation_policy
        for planet in galaxy.planets:
            if policy["type"] == "提升科技":
                for tech_type in planet.tech_levels.keys():
                    planet.tech_levels[tech_type] = min(1.0, planet.tech_levels[tech_type] + policy["effect"])
            elif policy["type"] == "減少污染":
                planet.pollution = max(0, planet.pollution - policy["effect"])
            elif policy["type"] == "資源補貼":
                for city in planet.cities:
                    city.resources["糧食"] += policy["effect"] * 50
                    city.resources["能源"] += policy["effect"] * 20
            elif policy["type"] == "健康倡議":
                for city in planet.cities:
                    for citizen in [c for c in city.citizens if c.alive]:
                        citizen.health = min(1.0, citizen.health + policy["effect"] * 0.5)
        galaxy.policy_duration_left -= 1
        if galaxy.policy_duration_left == 0:
            _log_global_event(galaxy, f"{galaxy.year} 年：政策「{policy['type']}」已失效。星系將回歸常態。")
            galaxy.active_federation_policy = None

def _update_planet_attributes(planet, current_year_global_events):
    """更新單一行星的屬性，包括科技自然增長、污染積累、防禦等級提升，以及疫情的爆發與消退。"""
    if planet.attack_cooldown > 0:
        planet.attack_cooldown -= 1

    for tech_type in planet.tech_levels.keys():
        planet.tech_levels[tech_type] = min(1.0, planet.tech_levels[tech_type] + random.uniform(0.005, 0.015))

        if tech_type in TECH_BREAKTHROUGHS:
            for breakthrough in TECH_BREAKTHROUGHS[tech_type]:
                if planet.tech_levels[tech_type] >= breakthrough["threshold"] and breakthrough["name"] not in planet.unlocked_tech_breakthroughs:
                    planet.unlocked_tech_breakthroughs.append(breakthrough["name"])
                    _log_global_event(galaxy, f"{galaxy.year} 年：🔬 **{planet.name}** 在 **{tech_type}** 領域取得了重大突破：**{breakthrough['name']}**！{breakthrough['effect_desc']}")
                    
                    if breakthrough["effect"].get("pollution_cleanup"):
                        planet.pollution = max(0, planet.pollution - breakthrough["effect"]["pollution_cleanup"])
                    if breakthrough["effect"].get("happiness_bonus"):
                        for city in planet.cities:
                            for citizen in [c for c in city.citizens if c.alive]:
                                citizen.happiness = min(1.0, citizen.happiness + breakthrough["effect"]["happiness_bonus"])
                    if breakthrough["effect"].get("pollution_reset"):
                        planet.pollution = 0
                        _log_global_event(galaxy, f"{galaxy.year} 年：✅ **{planet.name}** 的污染已被生態平衡系統完全清除！行星環境煥然一新。")

    pollution_growth = random.uniform(0.01, 0.02) * (1 - (_get_tech_effect_value(planet, "pollution_growth_mult") or 0)) # Added default 0 for multiplier
    pollution_reduction_from_tech = planet.tech_levels["環境"] * 0.015
    planet.pollution = max(0, planet.pollution + pollution_growth - pollution_reduction_from_tech)

    defense_cap = 100 + _get_tech_effect_value(planet, "defense_cap_bonus")
    planet.defense_level = min(defense_cap, int(planet.tech_levels["軍事"] * 100))

    epidemic_chance_base = st.session_state.epidemic_chance_slider * (1 - planet.tech_levels["醫療"])
    epidemic_chance_base *= (_get_tech_effect_value(planet, "epidemic_chance_mult") or 1) # Apply multiplier, default to 1 if not found

    if not planet.epidemic_active and random.random() < epidemic_chance_base:
        trigger_epidemic(planet, current_year_global_events)
    
    if planet.epidemic_active:
        epidemic_impact_on_health = planet.epidemic_severity * 0.1 * (1 - planet.tech_levels["醫療"] * 0.8)
        epidemic_impact_on_health *= (_get_tech_effect_value(planet, "epidemic_severity_mult") or 1)
        epidemic_impact_on_health = max(0.01, epidemic_impact_on_health)

        for city in planet.cities:
            for citizen in [c for c in city.citizens if c.alive]:
                if random.random() < (epidemic_impact_on_health + 0.01):
                    citizen.health -= epidemic_impact_on_health
                    citizen.happiness = max(0.1, citizen.happiness - epidemic_impact_on_health * 0.5)
                    if citizen.health < 0.1:
                        citizen.alive = False
                        citizen.death_cause = "疫情"
                        city.death_count += 1
                        city.graveyard.append((citizen.name, citizen.age, citizen.ideology, citizen.death_cause))
                        _log_global_event(galaxy, f"{galaxy.year} 年：{citizen.name} 在 {city.name} 因疫情而死亡。")
        
        planet.epidemic_severity = max(0.0, planet.epidemic_severity - random.uniform(0.05, 0.1))
        if planet.epidemic_severity <= 0.05:
            planet.epidemic_active = False
            _log_global_event(galaxy, f"{galaxy.year} 年：✅ **{planet.name}** 的疫情已得到控制。市民們開始恢復正常生活。")

def _handle_interstellar_interactions(planet, galaxy, current_year_global_events):
    """處理行星間的複雜互動，包含戰爭邏輯（持續、效果、和平條約）、衝突演變，以及系統觸發的隨機攻擊與反擊。"""
    for other_planet_name, relation_status in list(planet.relations.items()):
        other_planet_obj = next((p for p in galaxy.planets if p.name == other_planet_name and p.is_alive), None)
        if not other_planet_obj:
            planet.relations.pop(other_planet_name, None)
            planet.war_duration.pop(other_planet_name, None)
            planet.war_with.discard(other_planet_name)
            continue

        if planet.name > other_planet_name:
            continue

        # 處理條約效果 (非戰爭狀態)
        for treaty in planet.active_treaties:
            if treaty.type == "非侵略" and other_planet_obj.name in treaty.signatories and random.random() < 0.8:
                continue
            if treaty.type == "科技共享" and other_planet_obj.name in treaty.signatories:
                for tech_type in planet.tech_levels.keys():
                    planet.tech_levels[tech_type] = min(1.0, planet.tech_levels[tech_type] + 0.005)
                    other_planet_obj.tech_levels[tech_type] = min(1.0, other_planet_obj.tech_levels[tech_type] + 0.005)
        
        # --- 戰爭邏輯 ---
        if other_planet_name in planet.war_with:
            planet.war_duration[other_planet_name] = planet.war_duration.get(other_planet_name, 0) + 1
            other_planet_obj.war_duration[planet.name] = other_planet_obj.war_duration.get(planet.name, 0) + 1

            war_death_rate_increase = 0.01
            war_resource_drain_per_city = 5
            
            for city in planet.cities:
                city.resources["糧食"] -= war_resource_drain_per_city
                city.resources["能源"] -= war_resource_drain_per_city / 2
                for citizen in [c for c in city.citizens if c.alive]:
                    citizen.happiness = max(0.1, citizen.happiness - 0.05)
                    if random.random() < war_death_rate_increase:
                        citizen.alive = False
                        citizen.death_cause = "戰爭"
                        city.death_count += 1
                        city.graveyard.append((citizen.name, citizen.age, citizen.ideology, citizen.death_cause))
                        _log_global_event(galaxy, f"{galaxy.year} 年：戰火無情，市民 {citizen.name} 在 {city.name} 因戰爭而犧牲。")

            war_duration_threshold = 10
            population_ratio_for_surrender = 0.2

            planet_pop = sum(len(c.citizens) for c in planet.cities)
            other_planet_pop = sum(len(c.citizens) for c in other_planet_obj.cities)

            peace_conditions_met = False
            if (planet.war_duration[other_planet_name] >= war_duration_threshold and random.random() < 0.1) or \
               (planet_pop < other_planet_pop * population_ratio_for_surrender and random.random() < 0.2) or \
               (other_planet_pop < planet_pop * population_ratio_for_surrender and random.random() < 0.2) or \
               (random.random() < (_get_tech_effect_value(planet, "war_win_chance_bonus") or 0)): # Added default 0 for bonus
                peace_conditions_met = True

            if peace_conditions_met:
                planet.war_with.remove(other_planet_name)
                other_planet_obj.war_with.remove(planet.name)
                del planet.war_duration[other_planet_name]
                del other_planet_obj.war_duration[planet.name]

                planet.relations[other_planet_name] = "neutral"
                other_planet_obj.relations[planet.name] = "neutral"
                
                _log_global_event(galaxy, f"{galaxy.year} 年：🕊️ **{planet.name}** 與 **{other_planet_obj.name}** 簽署和平條約，結束了漫長的戰爭！星際間恢復了短暫的寧靜。")

                winner, loser = (planet, other_planet_obj) if planet_pop > other_planet_pop else (other_planet_obj, planet)
                
                if winner.name == planet.name and planet_pop > other_planet_pop * 1.5:
                    winner_resource_gain = int(sum(c.resources["糧食"] for c in loser.cities) * 0.1)
                    winner_tax_gain = int(sum(c.resources["稅收"] for c in loser.cities) * 0.2)
                    for city in winner.cities:
                        city.resources["糧食"] += winner_resource_gain / max(1, len(winner.cities))
                        city.resources["稅收"] += winner_tax_gain / max(1, len(winner.cities))
                    
                    pop_transfer = int(sum(len(c.citizens) for c in loser.cities) * 0.05)
                    for _ in range(pop_transfer):
                        if loser.cities and loser.cities[0].citizens:
                            c = random.choice([c for c in loser.cities[0].citizens if c.alive])
                            loser.cities[0].citizens.remove(c)
                            c.city = winner.cities[0].name
                            winner.cities[0].citizens.append(c)
                            
                    for tech_type in winner.tech_levels.keys():
                        winner.tech_levels[tech_type] = min(1.0, winner.tech_levels[tech_type] + loser.tech_levels[tech_type] * 0.05)

                    _log_global_event(galaxy, f"{galaxy.year} 年：🏆 **{winner.name}** 在戰爭中取得勝利，獲得了資源、人口並竊取了科技！戰敗方付出了沉重代價。")
                    for city in loser.cities:
                        for citizen in [c for c in city.citizens if c.alive]:
                            citizen.trust = max(0.1, citizen.trust - 0.1)
                            citizen.happiness = max(0.1, citizen.happiness - 0.1)
            return

        # --- 非戰爭狀態下的衝突觸發與關係演變 ---
        base_conflict_chance = st.session_state.war_chance_slider
        if planet.alien or other_planet_obj.alien:
            base_conflict_chance *= 1.2

        conflict_chance = max(0.01, base_conflict_chance * (1 - planet.tech_levels["軍事"]))
        conflict_chance *= (_get_tech_effect_value(planet, "non_aggression_treaty_mult") or 1) # Apply non-aggression treaty effect

        if relation_status == "friendly":
            conflict_chance *= 0.5
        elif relation_status == "hostile":
            conflict_chance *= 2.0

        if random.random() < conflict_chance:
            planet.conflict_level = min(1.0, planet.conflict_level + random.uniform(0.05, 0.15))
            other_planet_obj.conflict_level = min(1.0, other_planet_obj.conflict_level + random.uniform(0.05, 0.15))
            
            _log_global_event(galaxy, f"{galaxy.year} 年：⚠️ {planet.name} 與 {other_planet_obj.name} 的衝突等級提升至 {planet.conflict_level:.2f}！緊張局勢加劇。")

            if relation_status != "hostile":
                planet.relations[other_planet_name] = "hostile"
                other_planet_obj.relations[planet.name] = "hostile"
                _log_global_event(galaxy, f"{galaxy.year} 年：💥 {planet.name} 與 {other_planet_obj.name} 的關係惡化為敵對！外交關係跌至冰點。")
            
            if planet.conflict_level > 0.7 and other_planet_obj.conflict_level > 0.7 and planet.relations[other_planet_name] == "hostile":
                planet.war_with.add(other_planet_name)
                other_planet_obj.war_with.add(planet.name)
                planet.war_duration[other_planet_name] = 0
                other_planet_obj.war_duration[planet.name] = 0
                _log_global_event(galaxy, f"{galaxy.year} 年：⚔️ **{planet.name}** 向 **{other_planet_obj.name}** 宣戰！星際戰爭全面爆發，宇宙為之顫抖！")
        else:
            planet.conflict_level = max(0.0, planet.conflict_level - random.uniform(0.01, 0.05))
            other_planet_obj.conflict_level = max(0.0, other_planet_obj.conflict_level - random.uniform(0.01, 0.05))

            if relation_status == "hostile" and random.random() < 0.02:
                planet.relations[other_planet_name] = "neutral"
                other_planet_obj.relations[planet.name] = "neutral"
                _log_global_event(galaxy, f"{galaxy.year} 年：🤝 {planet.name} 與 {other_planet_obj.name} 的關係從敵對轉為中立。冰釋前嫌的跡象浮現。")
            elif relation_status == "neutral" and random.random() < 0.01:
                planet.relations[other_planet_name] = "friendly"
                other_planet_obj.relations[planet.name] = "friendly"
                _log_global_event(galaxy, f"{galaxy.year} 年：✨ {planet.name} 與 {other_planet_obj.name} 的關係從中立轉為友好。星際友誼的橋樑正在搭建。")

    # 隨機攻擊邏輯
    active_planets = [p for p in galaxy.planets if p.is_alive]
    if random.random() < st.session_state.war_chance_slider and len(active_planets) > 1:
        possible_targets = [p for p in active_planets if p.name != planet.name and p.name not in planet.allies and p.name not in planet.war_with]
        if possible_targets:
            target_planet_for_random_attack = random.choice(possible_targets)
            
            attack_strength = random.uniform(0.05, 0.2)
            
            total_defense_bonus = target_planet_for_random_attack.defense_level * 0.005
            if target_planet_for_random_attack.shield_active:
                total_defense_bonus += 0.5
                target_planet_for_random_attack.shield_active = False

            alliance_defense_bonus = sum(0.1 for ally_name in target_planet_for_random_attack.allies if next((p for p in galaxy.planets if p.name == ally_name and p.is_alive), None))
            total_defense_bonus += alliance_defense_bonus

            actual_attack_strength = max(0.01, attack_strength * (1 - total_defense_bonus))
            actual_attack_strength *= (1 + (_get_tech_effect_value(planet, "attack_damage_bonus") or 0)) # Added default 0 for bonus
            
            population_loss = int(sum(len(c.citizens) for c in target_planet_for_random_attack.cities) * actual_attack_strength)
            resource_loss = int(sum(c.resources["糧食"] for c in target_planet_for_random_attack.cities) * actual_attack_strength * 0.5)

            for city in target_planet_for_random_attack.cities:
                for _ in range(int(population_loss / max(1, len(target_planet_for_random_attack.cities)))):
                    if city.citizens:
                        victim = random.choice([c for c in city.citizens if c.alive])
                        victim.alive = False
                        victim.death_cause = "隨機攻擊"
                        city.death_count += 1
                        city.graveyard.append((victim.name, victim.age, victim.ideology, victim.death_cause))
                city.resources["糧食"] = max(0, city.resources["糧食"] - int(resource_loss / max(1, len(target_planet_for_random_attack.cities))))
                city.resources["能源"] = max(0, city.resources["能源"] - int(resource_loss / max(1, len(target_planet_for_random_attack.cities)) / 2))

            random_attack_msg = f"{galaxy.year} 年：🚨 **{planet.name}** 偵測到不明艦隊，隨機攻擊了 **{target_planet_for_random_attack.name}**！"
            if population_loss > 0:
                random_attack_msg += f" 目標損失約 {population_loss} 人口，城市陷入恐慌。"
            _log_global_event(galaxy, random_attack_msg)
            
            if random.random() < (0.1 + target_planet_for_random_attack.tech_levels["軍事"] * 0.1 + alliance_defense_bonus * 0.5):
                counter_attack_damage = random.uniform(0.01, 0.05)
                counter_attack_pop_loss = int(sum(len(c.citizens) for c in planet.cities) * counter_attack_damage)
                for city in planet.cities:
                    for _ in range(int(counter_attack_pop_loss / max(1, len(planet.cities)))):
                        if city.citizens:
                            victim = random.choice([c for c in city.citizens if c.alive])
                            victim.alive = False
                            victim.death_cause = "反擊"
                            city.death_count += 1
                            city.graveyard.append((victim.name, victim.age, victim.ideology, victim.death_cause))
                counter_attack_msg = f"{galaxy.year} 年：🛡️ **{target_planet_for_random_attack.name}** 成功組織反擊，擊退了 **{planet.name}** 的攻擊！"
                if counter_attack_pop_loss > 0:
                    counter_attack_msg += f" 攻擊方損失約 {counter_attack_pop_loss} 人口。"
                _log_global_event(galaxy, counter_attack_msg)

    for city in planet.cities:
        for citizen in [c for c in city.citizens if c.alive]:
            if random.random() < (planet.conflict_level * 0.002):
                citizen.alive = False
                citizen.death_cause = "衝突"
                city.death_count += 1
                city.graveyard.append((citizen.name, citizen.age, citizen.ideology, citizen.death_cause))
                _log_global_event(galaxy, f"{galaxy.year} 年：星際間的暗流湧動，市民 {citizen.name} 在 {city.name} 因衝突而犧牲。")

def _update_city_attributes(city, planet, galaxy, current_year_global_events):
    """更新單一城市的屬性，涵蓋資源消耗與生產、貿易、資源事件、群眾運動與叛亂，以及政體演變。"""
    gov_drain_multipliers = {"專制": 0.8, "民主制": 1.2, "共和制": 1.0}
    resource_drain_multiplier = gov_drain_multipliers.get(city.government_type, 1.0)

    consumption_reduction_bonus = (_get_tech_effect_value(planet, "resource_consumption_reduction") or 0) # Added default 0 for bonus
    
    population_consumption = len(city.citizens) * 0.5
    actual_consumption_multiplier = max(0, 1 - consumption_reduction_bonus)
    city.resources["糧食"] -= population_consumption * resource_drain_multiplier * actual_consumption_multiplier
    city.resources["能源"] -= (population_consumption / 2) * resource_drain_multiplier * actual_consumption_multiplier

    resource_infinite_active = _get_tech_effect_value(planet, "resource_infinite")
    if resource_infinite_active:
        city.resources["糧食"] = 1000
        city.resources["能源"] = 1000
        _log_global_event(galaxy, f"{galaxy.year} 年：✨ **{city.name}** 的資源複製器啟動，糧食和能源供應無限！城市進入永續發展時代。")

    production_bonus = planet.tech_levels["生產"] * 0.1 + (_get_tech_effect_value(planet, "resource_production_bonus") or 0) # Added default 0 for bonus

    specialization_effects = {
        "農業": {"糧食": 20},
        "工業": {"能源": 15},
        "科技": {"稅收": 10, "生產_tech": 0.005},
        "服務": {"稅收": 15, "happiness_bonus": 0.002},
        "軍事": {"能源": 10, "軍事_tech": 0.005}
    }
    effects = specialization_effects.get(city.specialization, {})
    if "糧食" in effects: city.resources["糧食"] += effects["糧食"] * (1 + production_bonus)
    if "能源" in effects: city.resources["能源"] += effects["能源"] * (1 + production_bonus)
    if "稅收" in effects: city.resources["稅收"] += effects["稅收"] * (1 + production_bonus)
    if "生產_tech" in effects: planet.tech_levels["生產"] = min(1.0, planet.tech_levels["生產"] + effects["生產_tech"])
    if "軍事_tech" in effects: planet.tech_levels["軍事"] = min(1.0, planet.tech_levels["軍事"] + effects["軍事_tech"])
    if "happiness_bonus" in effects:
        for citizen in [c for c in city.citizens if c.alive]:
            citizen.happiness = min(1.0, citizen.happiness + effects["happiness_bonus"])

    trade_chance_modifier = 1.0
    if galaxy.active_federation_policy and galaxy.active_federation_policy["type"] == "促進貿易":
        trade_chance_modifier = 1.5
    
    for treaty in planet.active_treaties:
        if treaty.type == "貿易" and city.name in [c.name for c in planet.cities] and "trade_bonus" in treaty.effects:
            trade_chance_modifier *= (1 + treaty.effects["trade_bonus"])

    for ally_name in planet.allies:
        ally_planet = next((p for p in galaxy.planets if p.name == ally_name and p.is_alive), None)
        if ally_planet:
            for ally_city in ally_planet.cities:
                if random.random() < (0.05 * trade_chance_modifier):
                    if city.resources["糧食"] > 150 and ally_city.resources["糧食"] < 50:
                        trade_amount = min(20, city.resources["糧食"] - 150, 50 - ally_city.resources["糧食"])
                        if trade_amount > 0:
                            city.resources["糧食"] -= trade_amount
                            ally_city.resources["糧食"] += trade_amount
                            city.resources["稅收"] += trade_amount
                            ally_city.resources["稅收"] -= trade_amount * 0.5
                            _log_global_event(galaxy, f"{galaxy.year} 年：🤝 {city.name} 與 {ally_city.name} 進行了糧食貿易。雙方互通有無，共同繁榮。")
                    if city.resources["能源"] > 100 and ally_city.resources["能源"] < 30:
                        trade_amount = min(10, city.resources["能源"] - 100, 30 - ally_city.resources["能源"])
                        if trade_amount > 0:
                            city.resources["能源"] -= trade_amount
                            ally_city.resources["能源"] += trade_amount
                            city.resources["稅收"] += trade_amount
                            ally_city.resources["稅收"] -= trade_amount * 0.5
                            _log_global_event(galaxy, f"{galaxy.year} 年：🤝 {city.name} 與 {ally_city.name} 進行了能源貿易。為彼此的發展注入活力。")

    if city.resources["糧食"] < 50 or city.resources["能源"] < 30:
        city.resource_shortage_years += 1
        if city.resource_shortage_years >= 3:
            _log_global_event(galaxy, f"{galaxy.year} 年：🚨 **{city.name}** 爆發了饑荒！市民健康和快樂度大幅下降！街頭巷尾彌漫著不安的氣氛。")
            for citizen in [c for c in city.citizens if c.alive]:
                citizen.health = max(0.1, citizen.health - random.uniform(0.05, 0.15))
                citizen.happiness = max(0.1, citizen.happiness - random.uniform(0.1, 0.2))
                if random.random() < 0.02:
                    citizen.alive = False
                    citizen.death_cause = "饑荒"
                    city.death_count += 1
                    city.graveyard.append((citizen.name, citizen.age, citizen.ideology, citizen.death_cause))
            city.resources["糧食"] = max(0, city.resources["糧食"] - 20)
            city.resources["能源"] = max(0, city.resources["能源"] - 10)
    else:
        city.resource_shortage_years = 0

    if city.resources["糧食"] > 200 and city.resources["能源"] > 150 and planet.tech_levels["生產"] > 0.7 and random.random() < 0.01:
        _log_global_event(galaxy, f"{galaxy.year} 年：💰 **{city.name}** 迎來了資源繁榮！市場欣欣向榮，市民財富和快樂度顯著提升！")
        for citizen in [c for c in city.citizens if c.alive]:
            citizen.wealth += random.uniform(10, 30)
            citizen.happiness = min(1.0, citizen.happiness + random.uniform(0.05, 0.1))

    alive_citizens_for_stats = [c for c in city.citizens if c.alive]
    avg_trust = sum(c.trust for c in alive_citizens_for_stats) / max(1, len(alive_citizens_for_stats)) if alive_citizens_for_stats else 0
    avg_happiness = sum(c.happiness for c in alive_citizens_for_stats) / max(1, len(alive_citizens_for_stats)) if alive_citizens_for_stats else 0
    
    ideology_counts = pd.Series([c.ideology for c in alive_citizens_for_stats]).value_counts() if alive_citizens_for_stats else pd.Series()
    dominant_ideology = ideology_counts.idxmax() if not ideology_counts.empty else None
    dominant_percentage = ideology_counts.max() / len(alive_citizens_for_stats) if alive_citizens_for_stats else 0

    if avg_trust < 0.5 and avg_happiness < 0.5 and dominant_ideology and dominant_percentage > 0.6 and random.random() < 0.05:
        if not city.mass_movement_active:
            city.mass_movement_active = True
            _log_global_event(galaxy, f"{galaxy.year} 年：📢 {city.name} 爆發了以 **{dominant_ideology}** 為主的群眾運動！市民們走上街頭，要求改變現狀。")
            city.resources["糧食"] -= random.randint(5, 15)
            city.resources["能源"] -= random.randint(5, 15)
            for c in alive_citizens_for_stats:
                c.trust = max(0.1, c.trust - 0.1)
                c.happiness = max(0.1, c.happiness - 0.1)
                if random.random() < 0.005:
                    if random.random() < 0.5:
                        c.alive = False
                        c.death_cause = "群眾運動"
                        city.death_count += 1
                        city.graveyard.append((c.name, c.age, c.ideology, c.death_cause))
                    else:
                        other_cities = [ct for p in galaxy.planets for ct in p.cities if ct.name != city.name and p.is_alive]
                        if other_cities:
                            target_city = random.choice(other_cities)
                            c.city = target_city.name
                            target_city.citizens.append(c)
                            city.emigration_count += 1
                            target_city.immigration_count += 1
                            _log_global_event(galaxy, f"{galaxy.year} 年：市民 {c.name} 從 {city.name} 逃離群眾運動的紛擾，移居至 {target_city.name}。")
        
        if city.mass_movement_active and (avg_trust < 0.3 or avg_happiness < 0.3) and random.random() < 0.02:
            trigger_revolution(city, current_year_global_events)

    elif city.mass_movement_active and avg_trust > 0.6 and avg_happiness > 0.6:
        city.mass_movement_active = False
        _log_global_event(galaxy, f"{galaxy.year} 年：✅ {city.name} 的群眾運動逐漸平息。社會秩序恢復穩定。")

    city.election_timer -= 1
    if city.election_timer <= 0:
        eligible_citizens_for_vote = [c for c in city.citizens if c.alive and c.age >= 18]
        if eligible_citizens_for_vote:
            for party in city.political_parties:
                party.calculate_support(eligible_citizens_for_vote)
            
            total_support = sum(p.support for p in city.political_parties)
            if total_support > 0:
                winning_party = max(city.political_parties, key=lambda p: p.support)
                if winning_party != city.ruling_party:
                    old_ruling_party_name = city.ruling_party.name if city.ruling_party else "無"
                    city.ruling_party = winning_party
                    _log_global_event(galaxy, f"{galaxy.year} 年：🗳️ **{city.name}** 舉行了選舉！**{city.ruling_party.name}** 成為新的執政黨，取代了 {old_ruling_party_name}！城市迎來了新的政治格局。")
                else:
                    _log_global_event(galaxy, f"{galaxy.year} 年：🗳️ **{city.name}** 舉行了選舉！**{city.ruling_party.name}** 繼續執政。政策的延續帶來了穩定。")
            else:
                _log_global_event(galaxy, f"{galaxy.year} 年：⚠️ {city.name} 無法舉行選舉，因為沒有足夠的合格選民。政治真空狀態持續。")
        else:
            _log_global_event(galaxy, f"{galaxy.year} 年：⚠️ {city.name} 無法舉行選舉，因為沒有足夠的合格選民。政治真空狀態持續。")
        
        city.election_timer = random.randint(5, 10)

    if random.random() < 0.005:
        if city.government_type == "民主制" and avg_trust < 0.4 and city.mass_movement_active:
            city.government_type = "專制"
            _log_global_event(galaxy, f"{galaxy.year} 年：🚨 {city.name} 的民主制因動盪而演變為專制！權力集中，秩序得以維護，但自由受到限制。")
        elif city.government_type == "專制" and avg_trust > 0.7:
            city.government_type = "共和制"
            _log_global_event(galaxy, f"{galaxy.year} 年：✨ {city.name} 的專制因民心所向而演變為共和制！市民的呼聲得到了回應，權力開始下放。")
        elif city.government_type == "共和制" and avg_trust < 0.5:
            city.government_type = random.choice(["專制", "民主制"])
            _log_global_event(galaxy, f"{galaxy.year} 年：📉 {city.name} 的共和制因信任度下降而退化為 {city.government_type}！政治體制再次面臨考驗。")

def _handle_citizen_lifecycle(city, planet, galaxy, current_year_global_events):
    """管理城市內市民的生命週期，包括年齡增長、財富與稅收、教育提升、污染對健康的影響、生老病死、結婚生子以及移民行為。"""
    next_citizens_list = []
    
    unmarried_citizens = [c for c in city.citizens if c.alive and c.partner is None and 20 <= c.age <= 50]
    random.shuffle(unmarried_citizens)
    
    for i in range(0, len(unmarried_citizens) - 1, 2):
        citizen1, citizen2 = unmarried_citizens[i], unmarried_citizens[i+1]
        if random.random() < 0.05:
            citizen1.partner, citizen2.partner = citizen2, citizen1
            _log_global_event(galaxy, f"{galaxy.year} 年：💖 {citizen1.name} 與 {citizen2.name} 在 {city.name} 喜結連理！城市中又多了一對幸福的伴侶。")

            if citizen1.family and citizen2.family and citizen1.family != citizen2.family:
                winner_family, loser_family = (citizen1.family, citizen2.family) if citizen1.family.reputation >= citizen2.family.reputation else (citizen2.family, citizen1.family)
                for member in loser_family.members:
                    member.family = winner_family
                    winner_family.members.append(member)
                galaxy.families.pop(loser_family.name, None)
                _log_global_event(galaxy, f"{galaxy.year} 年：家族 {loser_family.name} 併入 {winner_family.name}！家族勢力重新洗牌。")
            elif not citizen1.family and not citizen2.family:
                new_family_name = f"{citizen1.name.split('市民')[0]}家族"
                new_family = Family(new_family_name)
                new_family.members.extend([citizen1, citizen2])
                citizen1.family, citizen2.family = new_family, new_family
                galaxy.families[new_family_name] = new_family
                _log_global_event(galaxy, f"{galaxy.year} 年：新家族 **{new_family_name}** 誕生！為城市注入了新的活力。")
            elif not citizen1.family and citizen2.family:
                citizen1.family = citizen2.family
                citizen2.family.members.append(citizen1)
            elif citizen1.family and not citizen2.family:
                citizen2.family = citizen1.family
                citizen1.family.members.append(citizen2)

    for citizen in list(city.citizens):
        if not citizen.alive:
            continue

        citizen.age += 1
        
        profession_income = {
            "農民": 10, "工人": 15, "科學家": 25, "商人": 30, "無業": 5,
            "醫生": 40, "藝術家": 12, "工程師": 35, "教師": 20, "服務員": 10,
            "小偷": 20, "黑幫成員": 25, "詐騙犯": 30, "毒販": 45
        }
        living_cost = 8
        
        wealth_growth_bonus = (_get_tech_effect_value(planet, "wealth_growth_bonus") or 0) # Added default 0 for bonus
        citizen.wealth = max(0, citizen.wealth + profession_income.get(citizen.profession, 0) * (1 + wealth_growth_bonus) - living_cost)

        if citizen.profession in ["小偷", "黑幫成員", "詐騙犯", "毒販"] and random.random() < 0.03:
            citizen.wealth = max(0, citizen.wealth - random.uniform(20, 50))
            citizen.health = max(0.1, citizen.health - random.uniform(0.1, 0.2))
            citizen.trust = max(0.1, citizen.trust - random.uniform(0.05, 0.1))
            citizen.happiness = max(0.1, citizen.happiness - random.uniform(0.05, 0.1))
            _log_global_event(galaxy, f"{galaxy.year} 年：🚨 市民 {citizen.name} ({citizen.profession}) 在 {city.name} 遭遇了麻煩，財富受損！")

        tax_rates = {"專制": 0.08, "民主制": 0.03, "共和制": 0.05}
        city.resources["稅收"] += int(citizen.wealth * tax_rates.get(city.government_type, 0.05))

        education_chance = 0.01 * (1.5 if citizen.family and citizen.family.reputation > 0.7 else 1)
        if citizen.education_level < 3 and random.random() < education_chance:
            citizen.education_level += 1
            if citizen.education_level == 3 and citizen.profession not in ["科學家", "醫生", "工程師"] and random.random() < 0.3:
                citizen.profession = random.choice(["科學家", "醫生", "工程師"])
                _log_global_event(galaxy, f"{galaxy.year} 年：🎓 市民 {citizen.name} 在 {city.name} 獲得了高等教育，並晉升為 {citizen.profession}！")
            elif citizen.education_level == 2 and citizen.profession not in ["教師", "商人"] and random.random() < 0.1:
                citizen.profession = random.choice(["教師", "商人"])
                _log_global_event(galaxy, f"{galaxy.year} 年：📚 市民 {citizen.name} 在 {city.name} 完成中等教育，轉職為 {citizen.profession}！")

        pollution_health_impact = max(0.05, 0.3 * (1 - planet.tech_levels["環境"] * 0.5))
        if planet.pollution > 1.0 and random.random() < 0.03:
            citizen.health -= pollution_health_impact
            citizen.happiness = max(0.1, citizen.happiness - pollution_health_impact * 0.5)
            _log_global_event(galaxy, f"{galaxy.year} 年：市民 {citizen.name} 在 {city.name} 因嚴重的污染而健康惡化。")
            if citizen.health < 0:
                citizen.alive = False
                citizen.death_cause = "疾病/污染"
                _log_global_event(galaxy, f"{galaxy.year} 年：市民 {citizen.name} 在 {city.name} 因長期暴露於污染而死亡。")
        
        citizen.health = min(1.0, citizen.health + 0.01 + (_get_tech_effect_value(planet, "health_recovery_bonus") or 0)) # Added default 0 for bonus

        lifespan_bonus = (_get_tech_effect_value(planet, "lifespan_bonus") or 0) # Added default 0 for bonus
        natural_death_reduction_factor = (_get_tech_effect_value(planet, "natural_death_reduction") or 0) # Added default 0 for bonus
        effective_old_age_start = 80 + lifespan_bonus
        base_death_chance_old_age = st.session_state.death_rate_slider * 10

        if not citizen.alive:
            pass # Already handled if citizen died previously in this loop
        elif citizen.age > effective_old_age_start and random.random() < (base_death_chance_old_age * (1 - natural_death_reduction_factor)):
            citizen.alive = False
            citizen.death_cause = "壽終正寢"
            _log_global_event(galaxy, f"{galaxy.year} 年：市民 {citizen.name} 在 {city.name} 壽終正寢，安詳離世。")
        elif random.random() < st.session_state.death_rate_slider:
            citizen.alive = False
            citizen.death_cause = "意外"
            _log_global_event(galaxy, f"{galaxy.year} 年：市民 {citizen.name} 在 {city.name} 遭遇意外，不幸身亡。")

        if not citizen.alive:
            city.death_count += 1
            city.graveyard.append((citizen.name, citizen.age, citizen.ideology, citizen.death_cause))
            if citizen.partner and citizen.partner.alive:
                citizen.partner.partner = None
            if citizen.family and citizen in citizen.family.members:
                citizen.family.members.remove(citizen)
            continue

        birth_chance = st.session_state.birth_rate_slider * (1 + citizen.happiness * 0.5)
        if citizen.partner and citizen.partner.alive and 20 <= citizen.age <= 40 and random.random() < birth_chance:
            baby = Citizen(
                f"{citizen.name}-子{random.randint(1,100)}",
                parent1_ideology=citizen.ideology, parent2_ideology=citizen.partner.ideology,
                parent1_trust=citizen.trust, parent2_trust=citizen.partner.trust,
                parent1_emotion=citizen.happiness, parent2_emotion=citizen.partner.happiness,
                family=citizen.family
            )
            baby.city = city.name
            next_citizens_list.append(baby) # Add to next_citizens_list directly
            city.birth_count += 1
            _log_global_event(galaxy, f"{galaxy.year} 年：市民 {citizen.name} 與 {citizen.partner.name} 在 {city.name} 迎來了新生命！城市人口又添新丁。")
            if baby.family:
                baby.family.members.append(baby)

        immigration_chance = 0.02 * (1.5 if citizen.wealth < 100 or citizen.happiness < 0.4 else (0.5 if citizen.wealth > 300 and citizen.happiness > 0.8 else 1))
        if random.random() < immigration_chance:
            other_cities = [ct for p in galaxy.planets for ct in p.cities if ct.name != city.name and p.is_alive]
            if other_cities:
                target_city = sorted(other_cities, key=lambda c: (len(c.citizens), c.resources["糧食"], sum(cit.happiness for cit in c.citizens if cit.alive) / max(1, len([cit for cit in c.citizens if cit.alive]))), reverse=True)[0]

                if citizen.family and citizen in citizen.family.members:
                    citizen.family.members.remove(citizen)

                citizen.city = target_city.name
                target_city.citizens.append(citizen)
                city.emigration_count += 1
                target_city.immigration_count += 1
                _log_global_event(galaxy, f"{galaxy.year} 年：市民 {citizen.name} 從 {city.name} 移居至 {target_city.name}。尋求更好的發展機會。")
                
                if citizen.partner and citizen.partner.alive and citizen.partner in city.citizens:
                    partner = citizen.partner
                    if partner.family and partner in partner.family.members:
                        partner.family.members.remove(partner)
                    
                    partner.city = target_city.name
                    target_city.citizens.append(partner)
                    city.emigration_count += 1
                    target_city.immigration_count += 1
                    _log_global_event(galaxy, f"{galaxy.year} 年：市民 {citizen.name} 的配偶 {partner.name} 也隨其移居至 {target_city.name}。")
                continue # Skip adding to next_citizens_list if immigrated

        next_citizens_list.append(citizen)

    city.citizens = next_citizens_list
    
    alive_citizens_for_stats = [c for c in city.citizens if c.alive]
    avg_health = sum(c.health for c in alive_citizens_for_stats) / max(1, len(alive_citizens_for_stats)) if alive_citizens_for_stats else 0
    avg_trust = sum(c.trust for c in alive_citizens_for_stats) / max(1, len(alive_citizens_for_stats)) if alive_citizens_for_stats else 0
    avg_happiness = sum(c.happiness for c in alive_citizens_for_stats) / max(1, len(alive_citizens_for_stats)) if alive_citizens_for_stats else 0
    city.history.append((galaxy.year, avg_health, avg_trust, avg_happiness))

    for family_name, family_obj in galaxy.families.items():
        family_obj.update_reputation()

def simulate_year(galaxy):
    """模擬一年的世界變化。"""
    galaxy.year += 1
    current_year_global_events = []

    for planet in galaxy.planets:
        for city in planet.cities:
            city.birth_count = 0
            city.death_count = 0
            city.immigration_count = 0
            city.emigration_count = 0
            city.events = []
        
        new_active_treaties = []
        for treaty in planet.active_treaties:
            treaty.duration -= 1
            if treaty.duration > 0:
                new_active_treaties.append(treaty)
            else:
                _log_global_event(galaxy, f"{galaxy.year} 年：條約「{treaty.type}」在 {planet.name} 與 {', '.join([p for p in treaty.signatories if p != planet.name])} 之間已到期。")
        planet.active_treaties = new_active_treaties

    _handle_global_galaxy_events(galaxy, current_year_global_events)

    active_planets = [p for p in galaxy.planets if p.is_alive]
    for planet in active_planets:
        _update_planet_attributes(planet, current_year_global_events)
        _handle_interstellar_interactions(planet, galaxy, current_year_global_events)

        for city in planet.cities:
            _update_city_attributes(city, planet, galaxy, current_year_global_events)
            _handle_citizen_lifecycle(city, planet, galaxy, current_year_global_events)
        
        if all(not c.citizens for c in planet.cities): # Check if all cities on planet have no citizens left
            planet.is_alive = False
            _log_global_event(galaxy, f"{galaxy.year} 年：💥 行星 **{planet.name}** 上的所有城市都已滅亡，行星從星系中消失了！這片土地成為了歷史。")
            for p in galaxy.planets:
                p.active_treaties = [t for t in p.active_treaties if planet.name not in t.signatories]

    galaxy.planets = [p for p in galaxy.planets if p.is_alive]

    current_total_population = sum(len(city.citizens) for planet in galaxy.planets for city in planet.cities)
    if galaxy.year > 0:
        population_change_percentage = ((current_total_population - galaxy.prev_total_population) / max(1, galaxy.prev_total_population)) * 100
        if population_change_percentage > 5:
            _log_global_event(galaxy, f"{galaxy.year} 年：📈 星系總人口快速增長，達 {current_total_population} 人！資源壓力可能隨之而來。")
        elif population_change_percentage < -5:
            _log_global_event(galaxy, f"{galaxy.year} 年：📉 星系總人口持續下降，僅剩 {current_total_population} 人！請注意市民福祉與生存環境。")
    galaxy.prev_total_population = current_total_population

    if current_year_global_events:
        if galaxy.global_events_log and galaxy.global_events_log[-1]["year"] == galaxy.year:
            galaxy.global_events_log[-1]["events"].extend(current_year_global_events)
        else:
            galaxy.global_events_log.append({"year": galaxy.year, "events": current_year_global_events})


# --- Streamlit UI 控制元件 ---
st.title("🌐 CitySim 世界模擬器 Pro")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ 模擬設定")
    years_per_step = st.slider("每個步驟模擬年數", 1, 100, 10, help="選擇每次點擊按鈕模擬的年數")
    simulate_step_button = st.button("執行模擬步驟")
    st.markdown("---")
    st.header("🌐 世界隨機性調整")
    st.session_state.birth_rate_slider = st.slider("市民基礎出生率", 0.0, 0.1, 0.02, help="調整市民自然出生的基礎機率")
    st.session_state.death_rate_slider = st.slider("市民基礎死亡率", 0.0, 0.1, 0.01, help="調整市民自然死亡的基礎機率")
    st.session_state.epidemic_chance_slider = st.slider("疫情發生機率", 0.0, 0.1, 0.02, help="調整行星疫情爆發的基礎機率")
    st.session_state.war_chance_slider = st.slider("戰爭/衝突機率", 0.0, 0.1, 0.05, help="調整行星間隨機衝突和戰爭的基礎機率")
    st.markdown("---")
    st.header("🏙️ 城市選擇")
    city_options = [city.name for p in galaxy.planets if p.is_alive for city in p.cities]
    
    current_selected_index = 0
    if 'selected_city' in st.session_state and st.session_state.selected_city in city_options:
        current_selected_index = city_options.index(st.session_state.selected_city)
    elif city_options:
        st.session_state.selected_city = city_options[0]
    else:
        st.info("目前沒有城市可供選擇。")
        st.session_state.selected_city = None
        
    selected_city = None
    if city_options:
        selected_city = st.selectbox(
            "選擇城市以檢視狀態：",
            city_options,
            help="選擇一個城市來查看其詳細統計數據和事件",
            index=current_selected_index,
            key="selected_city"
        )

    st.markdown("---")
    if st.button("重置模擬", help="將模擬器重置為初始狀態"):
        st.session_state.galaxy = initialize_galaxy()
        st.rerun()

st.markdown(f"### ⏳ 當前年份：{galaxy.year}")

# --- 政策選擇 UI (獨立於模擬迴圈) ---
if 'awaiting_policy_choice' not in st.session_state:
    st.session_state.awaiting_policy_choice = False

if st.session_state.awaiting_policy_choice:
    st.markdown("---")
    st.header("📜 聯邦政策選擇")
    st.info(f"聯邦領導人 **{galaxy.federation_leader.name}** (來自 {galaxy.federation_leader.city}) 已選出！請選擇一項新政策。")
    
    active_planets_for_stats = [p for p in galaxy.planets if p.is_alive]
    avg_galaxy_tech_military = sum(p.tech_levels["軍事"] for p in active_planets_for_stats) / max(1, len(active_planets_for_stats)) if active_planets_for_stats else 0
    avg_galaxy_tech_environment = sum(p.tech_levels["環境"] for p in active_planets_for_stats) / max(1, len(active_planets_for_stats)) if active_planets_for_stats else 0
    avg_galaxy_tech_medical = sum(p.tech_levels["醫療"] for p in active_planets_for_stats) / max(1, len(active_planets_for_stats)) if active_planets_for_stats else 0
    avg_galaxy_tech_production = sum(p.tech_levels["生產"] for p in active_planets_for_stats) / max(1, len(active_planets_for_stats)) if active_planets_for_stats else 0
    
    avg_galaxy_pollution = sum(p.pollution for p in active_planets_for_stats) / max(1, len(active_planets_for_stats)) if active_planets_for_stats else 0
    avg_galaxy_conflict = sum(p.conflict_level for p in active_planets_for_stats) / max(1, len(active_planets_for_stats)) if active_planets_for_stats else 0

    st.markdown(f"**當前星系概況：**")
    st.write(f"- 平均軍事科技: **{avg_galaxy_tech_military:.2f}**")
    st.write(f"- 平均環境科技: **{avg_galaxy_tech_environment:.2f}**")
    st.write(f"- 平均醫療科技: **{avg_galaxy_tech_medical:.2f}**")
    st.write(f"- 平均生產科技: **{avg_galaxy_tech_production:.2f}**")
    st.write(f"- 平均污染水平: **{avg_galaxy_pollution:.2f}**")
    st.write(f"- 平均衝突等級: **{avg_galaxy_conflict:.2f}**")

    policy_options_display = {
        "提升科技": "提升所有行星的科技發展速度。",
        "減少污染": "減緩所有行星的污染積累。",
        "促進貿易": "增加行星間貿易發生的機率。",
        "資源補貼": "為所有城市提供額外的糧食和能源資源。",
        "健康倡議": "提升所有市民的健康水平。"
    }
    
    chosen_policy_type_display = st.selectbox(
        "選擇政策類型：",
        list(policy_options_display.keys()),
        help="選擇一項政策以影響星系的未來發展。"
    )
    st.write(f"**政策描述：** {policy_options_display[chosen_policy_type_display]}")

    if st.button("確認政策並繼續模擬"):
        actual_policy_type = chosen_policy_type_display
        
        galaxy.active_federation_policy = {
            "type": actual_policy_type,
            "effect": st.session_state.policy_effect,
            "duration": st.session_state.policy_duration
        }
        galaxy.policy_duration_left = st.session_state.policy_duration
        
        current_year_global_events = st.session_state.get('temp_global_events', [])
        _log_global_event(galaxy, f"{galaxy.year} 年：📜 聯邦領導人 **{galaxy.federation_leader.name}** 頒布了「**{actual_policy_type}**」政策，將持續 {galaxy.policy_duration_left} 年！")

        st.session_state.awaiting_policy_choice = False
        st.session_state.temp_global_events = []
        st.rerun()

if st.session_state.awaiting_policy_choice:
    st.stop()

# --- 星際行動 UI ---
st.markdown("---")
st.header("⚔️ 星際行動")
with st.container():
    st.markdown("#### 🚀 發動攻擊")
    active_planets_for_attack = [p for p in galaxy.planets if p.is_alive and any(c.citizens for c in p.cities)]
    
    if len(active_planets_for_attack) < 2:
        st.info("需要至少兩個活著的行星才能發動攻擊。")
    else:
        attacker_planet_name = st.selectbox(
            "選擇攻擊方行星：",
            [p.name for p in active_planets_for_attack],
            key="attacker_planet_select"
        )
        attacker_planet = next((p for p in galaxy.planets if p.name == attacker_planet_name), None)

        planets_with_non_aggression_treaty = {signatory for treaty in (attacker_planet.active_treaties if attacker_planet else []) if treaty.type == "非侵略" for signatory in treaty.signatories if signatory != (attacker_planet.name if attacker_planet else "")}
        
        target_options = [p.name for p in active_planets_for_attack if p.name != attacker_planet_name and p.name not in (attacker_planet.allies if attacker_planet else set()) and p.name not in planets_with_non_aggression_treaty]

        if not target_options:
            st.warning(f"目前沒有可攻擊的行星（不能攻擊自己、盟友或有非侵略條約的行星）。")
            target_planet_name = None
        else:
            target_planet_name = st.selectbox(
                "選擇目標行星：",
                target_options,
                key="target_planet_select"
            )
        target_planet = next((p for p in galaxy.planets if p.name == target_planet_name), None)

        if attacker_planet and target_planet:
            if attacker_planet.attack_cooldown > 0:
                st.info(f"**{attacker_planet.name}** 正在攻擊冷卻中，剩餘 {attacker_planet.attack_cooldown} 年。")
            else:
                attack_type = st.radio(
                    "選擇攻擊類型：",
                    ["精確打擊 (較低傷害，較低戰爭機率)", "全面開戰 (較高傷害，較高戰爭機率)", "末日武器 (需解鎖)"],
                    key="attack_type_radio"
                )
                
                attack_costs = {"精確打擊 (較低傷害，較低戰爭機率)": 50, "全面開戰 (較高傷害，較高戰爭機率)": 100, "末日武器 (需解鎖)": 500}
                attack_cost = attack_costs.get(attack_type, -1)

                if attack_type == "末日武器 (需解鎖)" and "末日武器" not in attacker_planet.unlocked_tech_breakthroughs:
                    st.warning("尚未解鎖末日武器科技！")
                    attack_cost = -1

                if st.button(f"發動攻擊 ({attack_cost} 稅收)"):
                    if attack_cost == -1:
                        st.warning("請先解鎖末日武器科技！")
                    elif attacker_planet.cities and attacker_planet.cities[0].resources["稅收"] >= attack_cost:
                        attacker_planet.cities[0].resources["稅收"] -= attack_cost

                        target_planet.conflict_level = min(1.0, target_planet.conflict_level + random.uniform(0.1, 0.3))
                        attacker_planet.relations[target_planet.name] = "hostile"
                        target_planet.relations[attacker_planet.name] = "hostile"

                        if target_planet.name in attacker_planet.allies:
                            attacker_planet.allies.remove(target_planet.name)
                            target_planet.allies.remove(attacker_planet.name)
                            for city in attacker_planet.cities:
                                for citizen in [c for c in city.citizens if c.alive]:
                                    citizen.trust = max(0.1, citizen.trust - 0.2)
                                    citizen.happiness = max(0.1, citizen.happiness - 0.2)
                            _log_global_event(galaxy, f"{galaxy.year} 年：🚨 **{attacker_planet.name}** 攻擊盟友 **{target_planet.name}**，聯盟破裂，信任度與快樂度大幅下降！")
                            st.warning("聯盟破裂！")

                        damage_multipliers = {"精確打擊 (較低傷害，較低戰爭機率)": 0.1, "全面開戰 (較高傷害，較高戰爭機率)": 0.2, "末日武器 (需解鎖)": 1.0}
                        war_chance_manual_map = {"精確打擊 (較低傷害，較低戰爭機率)": 0.2, "全面開戰 (較高傷害，較高戰爭機率)": 0.5, "末日武器 (需解鎖)": 1.0}
                        
                        damage_multiplier = damage_multipliers.get(attack_type, 0.1)
                        war_chance_manual = war_chance_manual_map.get(attack_type, 0.2)

                        total_defense_bonus = target_planet.defense_level * 0.005
                        if target_planet.shield_active:
                            total_defense_bonus += 0.5
                            target_planet.shield_active = False

                        actual_damage_multiplier = max(0.01, damage_multiplier * (1 - total_defense_bonus))
                        actual_damage_multiplier *= (1 + (_get_tech_effect_value(attacker_planet, "attack_damage_bonus") or 0)) # Added default 0 for bonus
                        
                        population_loss = int(sum(len(c.citizens) for c in target_planet.cities) * actual_damage_multiplier)
                        resource_loss = int(sum(c.resources["糧食"] for c in target_planet.cities) * actual_damage_multiplier * 0.5)

                        for city in target_planet.cities:
                            for _ in range(int(population_loss / max(1, len(target_planet.cities)))):
                                if city.citizens:
                                    victim = random.choice([c for c in city.citizens if c.alive])
                                    victim.alive = False
                                    victim.death_cause = "攻擊"
                                    city.death_count += 1
                                    city.graveyard.append((victim.name, victim.age, victim.ideology, victim.death_cause))
                            city.resources["糧食"] = max(0, city.resources["糧食"] - int(resource_loss / max(1, len(target_planet.cities))))
                            city.resources["能源"] = max(0, city.resources["能源"] - int(resource_loss / max(1, len(target_planet.cities)) / 2))

                        attack_msg = f"{galaxy.year} 年：💥 **{attacker_planet.name}** 對 **{target_planet.name}** 發動了「{attack_type.split('(')[0].strip()}」！"
                        if population_loss > 0:
                            attack_msg += f" 目標損失約 {population_loss} 人口。"
                        
                        _log_global_event(galaxy, attack_msg)
                        st.success(attack_msg)

                        if random.random() < war_chance_manual:
                            attacker_planet.war_with.add(target_planet.name)
                            target_planet.war_with.add(attacker_planet.name)
                            attacker_planet.war_duration[target_planet.name] = 0
                            target_planet.war_duration[attacker_planet.name] = 0
                            _log_global_event(galaxy, f"{galaxy.year} 年：⚔️ **{attacker_planet.name}** 與 **{target_planet.name}** 爆發全面戰爭！")
                            st.error("全面戰爭爆發！")
                        
                        attacker_planet.attack_cooldown = 5
                        st.rerun()
                    else:
                        st.warning(f"攻擊方 **{attacker_planet.name}** 稅收不足或沒有活著的城市！需要 {attack_cost} 稅收。")

st.markdown("---")
with st.container():
    st.markdown("#### 🛡️ 防禦策略與科技發展")
    active_planets_for_defense = [p for p in galaxy.planets if p.is_alive and any(c.citizens for c in p.cities)]
    if not active_planets_for_defense:
        st.info("沒有活著的行星可供設置防禦或發展科技。")
    else:
        defend_planet_name = st.selectbox(
            "選擇設置防禦或發展科技的行星：",
            [p.name for p in active_planets_for_defense],
            key="defend_planet_select"
        )
        defend_planet = next((p for p in galaxy.planets if p.name == defend_planet_name), None)

        if defend_planet:
            st.write(f"當前 **{defend_planet.name}** 防禦等級: {defend_planet.defense_level}")
            st.write(f"行星護盾狀態: {'活躍中' if defend_planet.shield_active else '未部署'}")
            st.write(f"軍事科技: {defend_planet.tech_levels['軍事']:.2f} | 環境科技: {defend_planet.tech_levels['環境']:.2f} | 醫療科技: {defend_planet.tech_levels['醫療']:.2f} | 生產科技: {defend_planet.tech_levels['生產']:.2f}")


            col1, col2 = st.columns(2)
            with col1:
                strengthen_cost = 20
                if st.button(f"加強城市防禦 (花費 {strengthen_cost} 稅收)", key="strengthen_defense_button"):
                    if defend_planet.cities and defend_planet.cities[0].resources["稅收"] >= strengthen_cost:
                        defend_planet.cities[0].resources["稅收"] -= strengthen_cost
                        defend_planet.defense_level = min(100, defend_planet.defense_level + 10)
                        st.success(f"成功加強 **{defend_planet.name}** 的城市防禦，防禦等級提升至 {defend_planet.defense_level}！")
                        _log_global_event(galaxy, f"{galaxy.year} 年：🛡️ **{defend_planet.name}** 加強了城市防禦。")
                        st.rerun()
                    else:
                        st.warning(f"稅收不足！需要 {strengthen_cost} 稅收來加強防禦。")
            with col2:
                shield_cost = 150
                if st.button(f"部署行星護盾 (花費 {shield_cost} 稅收，當年有效)", key="deploy_shield_button"):
                    if defend_planet.cities and defend_planet.cities[0].resources["稅收"] >= shield_cost:
                        if not defend_planet.shield_active:
                            defend_planet.cities[0].resources["稅收"] -= shield_cost
                            defend_planet.shield_active = True
                            st.success(f"成功為 **{defend_planet.name}** 部署了行星護盾！")
                            _log_global_event(galaxy, f"{galaxy.year} 年：✨ **{defend_planet.name}** 部署了行星護盾，當年有效。")
                            st.rerun()
                        else:
                            st.info(f"**{defend_planet.name}** 的行星護盾已活躍中。")
                    else:
                        st.warning(f"稅收不足！需要 {shield_cost} 稅收來部署護盾。")
            
            st.markdown("---")
            st.markdown("#### 🔬 科技投資")
            tech_investment_cost = 30
            tech_type_to_invest = st.selectbox(
                "選擇要投資的科技領域：",
                list(defend_planet.tech_levels.keys()),
                key="tech_invest_select"
            )
            if st.button(f"投資 {tech_type_to_invest} 科技 (花費 {tech_investment_cost} 稅收)", key="invest_tech_button"):
                if defend_planet.cities and defend_planet.cities[0].resources["稅收"] >= tech_investment_cost:
                    defend_planet.cities[0].resources["稅收"] -= tech_investment_cost
                    defend_planet.tech_levels[tech_type_to_invest] = min(1.0, defend_planet.tech_levels[tech_type_to_invest] + 0.05)
                    st.success(f"成功投資 **{defend_planet.name}** 的 {tech_type_to_invest} 科技，目前為 {defend_planet.tech_levels[tech_type_to_invest]:.2f}！")
                    _log_global_event(galaxy, f"{galaxy.year} 年：🔬 **{defend_planet.name}** 投資了 {tech_type_to_invest} 科技。科技發展邁向新里程。")
                    st.rerun()
                else:
                    st.warning(f"稅收不足！需要 {tech_investment_cost} 稅收來投資科技。")

st.markdown("---")
with st.container():
    st.markdown("#### 🤝 聯盟外交")
    active_planets_for_alliance = [p for p in galaxy.planets if p.is_alive and any(c.citizens for c in p.cities)]

    if len(active_planets_for_alliance) < 2:
        st.info("需要至少兩個活著的行星才能進行外交。")
    else:
        proposing_planet_name = st.selectbox(
            "選擇發起外交請求的行星：",
            [p.name for p in active_planets_for_alliance],
            key="proposing_planet_select"
        )
        proposing_planet = next((p for p in galaxy.planets if p.name == proposing_planet_name), None)

        if proposing_planet:
            diplomacy_action = st.radio(
                "選擇外交行動：",
                ["提出結盟請求", "提出貿易協議", "提出非侵略條約", "談判和平"],
                key="diplomacy_action_radio"
            )

            target_diplomacy_options = []
            if diplomacy_action == "提出結盟請求":
                target_diplomacy_options = [p.name for p in active_planets_for_alliance if p.name != proposing_planet_name and p.name not in proposing_planet.allies and p.name not in proposing_planet.war_with]
            elif diplomacy_action == "提出貿易協議":
                target_diplomacy_options = [p.name for p in active_planets_for_alliance if p.name != proposing_planet_name and p.name not in proposing_planet.war_with and not any(t.type == "貿易" and p.name in t.signatories for t in proposing_planet.active_treaties)]
            elif diplomacy_action == "提出非侵略條約":
                target_diplomacy_options = [p.name for p in active_planets_for_alliance if p.name != proposing_planet_name and p.name not in proposing_planet.war_with and not any(t.type == "非侵略" and p.name in t.signatories for t in proposing_planet.active_treaties)]
            elif diplomacy_action == "談判和平":
                target_diplomacy_options = [p.name for p in active_planets_for_alliance if p.name in proposing_planet.war_with]


            if not target_diplomacy_options:
                st.info(f"**{proposing_planet_name}** 目前沒有可進行此外交行動的行星。")
                target_diplomacy_planet_name = None
            else:
                target_diplomacy_planet_name = st.selectbox(
                    "選擇目標行星：",
                    target_diplomacy_options,
                    key="target_diplomacy_planet_select"
                )
            target_diplomacy_planet = next((p for p in galaxy.planets if p.name == target_diplomacy_planet_name), None)

            if proposing_planet and target_diplomacy_planet:
                diplomacy_cost = 20 if diplomacy_action != "談判和平" else 50

                if st.button(f"執行外交行動 ({diplomacy_cost} 稅收)", key="execute_diplomacy_button"):
                    if proposing_planet.cities and proposing_planet.cities[0].resources["稅收"] >= diplomacy_cost:
                        proposing_planet.cities[0].resources["稅收"] -= diplomacy_cost

                        if diplomacy_action == "提出結盟請求":
                            proposing_planet.allies.add(target_diplomacy_planet.name)
                            target_diplomacy_planet.allies.add(proposing_planet.name)
                            proposing_planet.relations[target_diplomacy_planet.name] = "friendly"
                            target_diplomacy_planet.relations[proposing_planet.name] = "friendly"
                            _log_global_event(galaxy, f"{galaxy.year} 年：🤝 **{proposing_planet.name}** 與 **{target_diplomacy_planet.name}** 成功結盟！星際間的友誼更進一步。")
                            st.success("成功結盟！")
                        elif diplomacy_action == "提出貿易協議":
                            new_treaty = Treaty("貿易", [proposing_planet.name, target_diplomacy_planet.name], 10, {"trade_bonus": 0.2})
                            proposing_planet.active_treaties.append(new_treaty)
                            target_diplomacy_planet.active_treaties.append(new_treaty)
                            _log_global_event(galaxy, f"{galaxy.year} 年：🤝 **{proposing_planet.name}** 與 **{target_diplomacy_planet.name}** 簽署了貿易協議，持續10年！經濟合作將帶來繁榮。")
                            st.success("貿易協議簽署成功！")
                        elif diplomacy_action == "提出非侵略條約":
                            new_treaty = Treaty("非侵略", [proposing_planet.name, target_diplomacy_planet.name], 20)
                            proposing_planet.active_treaties.append(new_treaty)
                            target_diplomacy_planet.active_treaties.append(new_treaty)
                            _log_global_event(galaxy, f"{galaxy.year} 年：🕊️ **{proposing_planet.name}** 與 **{target_diplomacy_planet.name}** 簽署了非侵略條約，持續20年！為星際和平奠定基礎。")
                            st.success("非侵略條約簽署成功！")
                        elif diplomacy_action == "談判和平":
                            if target_diplomacy_planet.name in proposing_planet.war_with:
                                proposing_planet.war_with.remove(target_diplomacy_planet.name)
                                target_diplomacy_planet.war_with.remove(proposing_planet.name)
                                del proposing_planet.war_duration[target_diplomacy_planet.name]
                                del target_diplomacy_planet.war_duration[proposing_planet.name]

                                proposing_planet.relations[target_diplomacy_planet.name] = "neutral"
                                target_diplomacy_planet.relations[proposing_planet.name] = "neutral"
                                
                                _log_global_event(galaxy, f"{galaxy.year} 年：🕊️ **{proposing_planet.name}** 與 **{target_diplomacy_planet.name}** 成功談判和平，結束了戰爭！和平的曙光再次降臨。")
                                st.success("和平談判成功！")
                            else:
                                st.warning(f"**{proposing_planet.name}** 與 **{target_diplomacy_planet.name}** 並未處於戰爭狀態。")
                        
                        st.rerun()
                    else:
                        st.warning(f"稅收不足！需要 {diplomacy_cost} 稅收來執行此外交行動。")

st.markdown("---")
with st.container():
    st.markdown("#### 🚨 事件控制台")
    event_trigger_type = st.selectbox(
        "選擇要觸發的事件類型：",
        ["革命", "疫情", "政變", "AI覺醒"],
        key="event_trigger_type_select"
    )

    if event_trigger_type in ["革命", "政變"]:
        target_city_for_event = st.selectbox(
            f"選擇目標城市 ({event_trigger_type})：",
            [c.name for p in galaxy.planets for c in p.cities if p.is_alive],
            key="target_city_for_event_select"
        )
        selected_city_obj = next((c for p in galaxy.planets for c in p.cities if c.name == target_city_for_event), None)
        if st.button(f"觸發 {event_trigger_type} 事件"):
            if selected_city_obj:
                if event_trigger_type == "革命":
                    result_msg = trigger_revolution(selected_city_obj, []) # Pass empty list as events are logged via _log_global_event
                elif event_trigger_type == "政變":
                    result_msg = trigger_coup(selected_city_obj, [])
                st.success(result_msg)
                st.rerun()
            else:
                st.warning("請選擇一個有效的城市。")
    elif event_trigger_type in ["疫情", "AI覺醒"]:
        target_planet_for_event = st.selectbox(
            f"選擇目標行星 ({event_trigger_type})：",
            [p.name for p in galaxy.planets if p.is_alive],
            key="target_planet_for_event_select"
        )
        selected_planet_obj = next((p for p in galaxy.planets if p.name == target_planet_for_event), None)
        if st.button(f"觸發 {event_trigger_type} 事件"):
            if selected_planet_obj:
                if event_trigger_type == "疫情":
                    result_msg = trigger_epidemic(selected_planet_obj, [])
                elif event_trigger_type == "AI覺醒":
                    result_msg = trigger_ai_awakening(selected_planet_obj, [])
                st.success(result_msg)
                st.rerun()
            else:
                st.warning("請選擇一個有效的行星。")

# --- 主模擬邏輯 ---
progress_status = st.empty()

if simulate_step_button:
    for _ in range(years_per_step):
        progress_status.markdown(f"**--- 模擬年份 {galaxy.year + 1} ---**")
        simulate_year(galaxy)
    st.rerun()

progress_status.empty()

# --- 顯示資訊 ---
st.markdown("---")
st.markdown("## 🌍 星系概況")
with st.container():
    st.markdown(f"**聯邦領導人：** {galaxy.federation_leader.name} (來自 {galaxy.federation_leader.city})" if galaxy.federation_leader else "**聯邦領導人：** 暫無")
    
    if galaxy.active_federation_policy:
        policy = galaxy.active_federation_policy
        st.markdown(f"**當前聯邦政策：** 「{policy['type']}」 (剩餘 {galaxy.policy_duration_left} 年)")
    else:
        st.markdown("**當前聯邦政策：** 無")
    
    current_total_population_display = sum(len(city.citizens) for planet in galaxy.planets for city in planet.cities)
    if galaxy.year > 0:
        population_change_percentage = ((current_total_population_display - galaxy.prev_total_population) / max(1, galaxy.prev_total_population)) * 100
        if population_change_percentage > 5:
            st.warning(f"⚠️ **星系人口快速成長！** 過去一年增長約 {population_change_percentage:.1f}%，請注意資源壓力。")
        elif population_change_percentage < -5:
            st.error(f"🚨 **星系人口持續下降！** 過去一年下降約 {-population_change_percentage:.1f}%，請檢視市民福祉。")
        else:
            st.info(f"✨ 星系人口穩定變化，過去一年變化約 {population_change_percentage:.1f}%。")

    st.markdown("#### 🤝 行星關係：")
    if len(galaxy.planets) > 1:
        for p1 in galaxy.planets:
            relations_str = []
            for p2_name, status in p1.relations.items():
                if any(p.name == p2_name and p.is_alive for p in galaxy.planets):
                    war_status = " (戰爭中)" if p2_name in p1.war_with else ""
                    alliance_status = " (盟友)" if p2_name in p1.allies else ""
                    treaty_info = [f"{t.type} ({t.duration}年)" for t in p1.active_treaties if p2_name in t.signatories]
                    treaty_str = f" [{', '.join(treaty_info)}]" if treaty_info else ""
                    relations_str.append(f"{p2_name}: {status}{war_status}{alliance_status}{treaty_str}")
            st.write(f"- **{p1.name}** 與其他行星的關係: {', '.join(relations_str) if relations_str else '暫無活躍關係'}")
    else:
        st.info("星系中只有一個行星，沒有關係可顯示。")

# 可視化地圖 (Plotly)
st.markdown("#### 🗺️ 星系地圖：")
if galaxy.planets:
    planet_data = []
    for planet in galaxy.planets:
        x, y = galaxy.map_layout.get(planet.name, (0,0))
        all_citizens_on_planet = [c for city in planet.cities for c in city.citizens if c.alive]
        avg_health_p = sum(c.health for c in all_citizens_on_planet) / max(1, len(all_citizens_on_planet)) if all_citizens_on_planet else 0
        avg_trust_p = sum(c.trust for c in all_citizens_on_planet) / max(1, len(all_citizens_on_planet)) if all_citizens_on_planet else 0
        avg_happiness_p = sum(c.happiness for c in all_citizens_on_planet) / max(1, len(all_citizens_on_planet)) if all_citizens_on_planet else 0

        planet_data.append({
            "name": planet.name, "x": x, "y": y,
            "type": "外星行星" if planet.alien else "地球行星",
            "military_tech": planet.tech_levels["軍事"], "environment_tech": planet.tech_levels["環境"],
            "medical_tech": planet.tech_levels["醫療"], "production_tech": planet.tech_levels["生產"],
            "pollution": planet.pollution, "conflict": planet.conflict_level,
            "defense_level": planet.defense_level, "is_alive": planet.is_alive,
            "avg_health": avg_health_p, "avg_trust": avg_trust_p, "avg_happiness": avg_happiness_p
        })
    df_planets = pd.DataFrame(planet_data)

    fig_map = go.Figure()

    legend_line_types = {'中立關係': 'grey', '友好關係': 'green', '敵對關係': 'orange', '戰爭中': 'red'}
    for name, color in legend_line_types.items():
        fig_map.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color=color, width=2), name=name, showlegend=True, hoverinfo='skip'))

    for p1 in galaxy.planets:
        for p2_name, status in p1.relations.items():
            p2_obj = next((p for p in galaxy.planets if p.name == p2_name and p.is_alive), None)
            if p2_obj and p1.name < p2_name:
                x1, y1 = galaxy.map_layout.get(p1.name, (0,0))
                x2, y2 = galaxy.map_layout.get(p2_obj.name, (0,0))
                
                line_color = 'grey'
                if status == "friendly": line_color = 'green'
                elif status == "hostile": line_color = 'orange'
                if p2_name in p1.war_with: line_color = 'red'

                fig_map.add_trace(go.Scatter(x=[x1, x2, None], y=[y1, y2, None], mode='lines', line=dict(color=line_color, width=2), hoverinfo='text', text=f"關係: {status}<br>戰爭: {'是' if p2_name in p1.war_with else '否'}", showlegend=False))

    earth_planets = df_planets[df_planets['type'] == '地球行星']
    alien_planets = df_planets[df_planets['type'] == '外星行星']

    if not earth_planets.empty:
        fig_map.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(size=20, color='blue', symbol='circle', line=dict(width=2, color='DarkSlateGrey')), name='地球行星', showlegend=True, hoverinfo='skip'))
    if not alien_planets.empty:
        fig_map.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(size=20, color='purple', symbol='circle', line=dict(width=2, color='DarkSlateGrey')), name='外星行星', showlegend=True, hoverinfo='skip'))

    fig_map.add_trace(go.Scatter(
        x=df_planets["x"], y=df_planets["y"], mode='markers+text',
        marker=dict(size=20, color=df_planets["type"].map({"地球行星": "blue", "外星行星": "purple"}), symbol='circle', line=dict(width=2, color='DarkSlateGrey')),
        text=df_planets["name"], textposition="top center", hoverinfo='text', texttemplate='%{text}',
        hovertemplate="<b>%{text}</b><br>" + "類型: %{customdata[0]}<br>" + "軍事科技: %{customdata[1]:.2f}<br>" +
                      "環境科技: %{customdata[2]:.2f}<br>" + "醫療科技: %{customdata[3]:.2f}<br>" +
                      "生產科技: %{customdata[4]:.2f}<br>" + "污染: %{customdata[5]:.2f}<br>" +
                      "衝突: %{customdata[6]:.2f}<br>" + "防禦等級: %{customdata[7]}<extra></extra>",
        customdata=df_planets[['type', 'military_tech', 'environment_tech', 'medical_tech', 'production_tech', 'pollution', 'conflict', 'defense_level']],
        showlegend=False
    ))

    map_color_metric = st.radio(
        "地圖顏色顯示：",
        ["無", "污染", "衝突等級", "平均健康", "平均信任", "平均快樂度"],
        key="map_color_metric_select"
    )

    # --- 修正 KeyError 的部分 ---
    # 建立一個映射字典，將顯示名稱對應到 DataFrame 中的實際列名
    map_color_metric_mapping = {
        "污染": "pollution",
        "衝突等級": "conflict",
        "平均健康": "avg_health",
        "平均信任": "avg_trust",
        "平均快樂度": "avg_happiness"
    }

    if map_color_metric != "無":
        # 使用映射字典獲取正確的列名
        actual_column_name = map_color_metric_mapping.get(map_color_metric)
        if actual_column_name: # 確保映射存在
            color_values = df_planets[actual_column_name]
            colorscale = 'Viridis' if map_color_metric not in ["平均健康", "平均信任", "平均快樂度"] else 'Plasma'
                
            fig_map.add_trace(go.Scatter(x=df_planets["x"], y=df_planets["y"], mode='markers',
                marker=dict(size=25, color=color_values, colorscale=colorscale, showscale=True, colorbar=dict(title=map_color_metric), symbol='circle', line=dict(width=2, color='black'), opacity=0.7),
                hoverinfo='text', hovertemplate="<b>%{text}</b><br>" + f"{map_color_metric}: %{{marker.color:.2f}}<extra></extra>",
                text=df_planets["name"], showlegend=False
            ))
        else:
            st.warning(f"地圖顏色指標 '{map_color_metric}' 無法找到對應的數據列。")


    fig_map.update_layout(
        title='星系地圖',
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        height=500, showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.info("星系中沒有行星可供顯示地圖。")


for planet in galaxy.planets:
    st.markdown(f"#### 🪐 {planet.name} ({'外星' if planet.alien else '地球'})｜污染 **{planet.pollution:.2f}**｜衝突等級 **{planet.conflict_level:.2f}**{' (疫情活躍中)' if planet.epidemic_active else ''}｜防禦等級 **{planet.defense_level}**{' (護盾活躍中)' if planet.shield_active else ''}")
    st.markdown(f"**科技水平：** 軍事: {planet.tech_levels['軍事']:.2f} | 環境: {planet.tech_levels['環境']:.2f} | 醫療: {planet.tech_levels['醫療']:.2f} | 生產: {planet.tech_levels['生產']:.2f}")
    st.markdown("##### 已解鎖科技突破：")
    if planet.unlocked_tech_breakthroughs:
        for bt in planet.unlocked_tech_breakthroughs:
            st.write(f"- {bt}")
    else:
        st.write("- 暫無")

if not galaxy.planets:
    st.warning("所有行星都已滅亡，星系一片死寂...")

st.markdown("---")
found_city = False
for planet in galaxy.planets:
    for city in planet.cities:
        if city.name == selected_city:
            found_city = True
            with st.container():
                st.markdown(f"### 📊 **{city.name}** 資訊")
                st.write(f"**人口：** {len(city.citizens)} (出生 {city.birth_count} / 死亡 {city.death_count} / 遷入 {city.immigration_count} / 遷出 {city.emigration_count})")
                st.write(f"**資源：** 糧食: {city.resources['糧食']:.0f}｜能源: {city.resources['能源']:.0f}｜稅收: {city.resources['稅收']:.0f}")
                st.write(f"**產業專精：** {city.specialization}")
                st.write(f"**群眾運動狀態：** {'活躍中' if city.mass_movement_active else '平靜'}")
                st.write(f"**合作經濟水平：** {city.cooperative_economy_level:.2f}")
                st.write(f"**政體：** {city.government_type}")
                st.write(f"**執政黨：** {city.ruling_party.name if city.ruling_party else '無'} (距離下次選舉: {city.election_timer} 年)")

                st.markdown("#### 💰 城市管理：")
                investment_cost = 50
                if st.button(f"投資 {city.name} (花費 {investment_cost} 稅收)"):
                    if city.resources["稅收"] >= investment_cost:
                        city.resources["稅收"] -= investment_cost
                        city.resources["糧食"] += 30
                        city.resources["能源"] += 15
                        for citizen in [c for c in city.citizens if c.alive]:
                            citizen.health = min(1.0, citizen.health + 0.05)
                            citizen.trust = min(1.0, citizen.trust + 0.03)
                            citizen.happiness = min(1.0, citizen.happiness + 0.05)
                        
                        _log_global_event(galaxy, f"{galaxy.year} 年：💸 對 {city.name} 進行了投資，資源和市民福祉得到提升！")
                        st.success(f"成功投資 {city.name}！")
                        st.rerun()
                    else:
                        st.warning(f"{city.name} 稅收不足，無法投資！需要 {investment_cost} 稅收。")

                st.markdown("#### 📈 歷史趨勢：")
                if city.history:
                    history_df = pd.DataFrame(city.history, columns=["年份", "平均健康", "平均信任", "平均快樂度"])
                    fig_history = go.Figure()
                    fig_history.add_trace(go.Scatter(x=history_df["年份"], y=history_df["平均健康"], mode='lines+markers', name='平均健康'))
                    fig_history.add_trace(go.Scatter(x=history_df["年份"], y=history_df["平均信任"], mode='lines+markers', name='平均信任'))
                    fig_history.add_trace(go.Scatter(x=history_df["年份"], y=history_df["平均快樂度"], mode='lines+markers', name='平均快樂度'))
                    fig_history.update_layout(title_text=f"{city.name} 平均健康、信任與快樂度趨勢")
                    st.plotly_chart(fig_history, use_container_width=True)
                else:
                    st.info("該城市尚無歷史數據可供繪製圖表。")

                st.markdown("#### 🧠 思想派別分布：")
                ideology_count = pd.Series([c.ideology for c in city.citizens if c.alive]).value_counts()
                if not ideology_count.empty:
                    ideology_df = pd.DataFrame(list(ideology_count.items()), columns=['思想派別', '人數'])
                    fig_ideology = px.bar(ideology_df, x='思想派別', y='人數', title=f"{city.name} 思想派別分布")
                    st.plotly_chart(fig_ideology, use_container_width=True)
                else:
                    st.info("該城市目前沒有活著的市民。")

                st.markdown("#### 🏛️ 政黨支持度：")
                if city.political_parties:
                    party_support_data = [{"政黨": party.name, "支持度": party.support} for party in city.political_parties]
                    party_support_df = pd.DataFrame(party_support_data)
                    fig_party_support = px.pie(party_support_df, values='支持度', names='政黨', title=f"{city.name} 政黨支持度")
                    st.plotly_chart(fig_party_support, use_container_width=True)
                else:
                    st.info("該城市沒有政黨記錄。")

                st.markdown("#### 💀 死亡原因分析：")
                death_causes = [item[3] for item in city.graveyard if item[3] is not None]
                if death_causes:
                    death_cause_counts = pd.Series(death_causes).value_counts()
                    death_cause_df = pd.DataFrame({'死因': death_cause_counts.index, '人數': death_cause_counts.values})
                    fig_death = px.bar(death_cause_df, x='死因', y='人數', title=f"{city.name} 死亡原因分析")
                    st.plotly_chart(fig_death, use_container_width=True)
                else:
                    st.info("墓園中沒有死亡原因記錄。")

                st.markdown("#### 📰 最近事件：")
                if city.events:
                    for evt in city.events[::-1]:
                        st.write(f"- {evt}")
                else:
                    st.info("本年度沒有新事件發生。")

                st.markdown("#### 🪦 墓園紀錄：")
                if city.graveyard:
                    for name, age, ideology, cause in city.graveyard[-5:][::-1]:
                        st.write(f"- {name} (享年 {age} 歲，生前信仰：{ideology}，死因：{cause if cause else '未知'})")
                else:
                    st.info("墓園目前沒有記錄。")
                
                st.markdown("#### 👤 部分市民詳細資訊：")
                if city.citizens:
                    sample_citizens = random.sample([c for c in city.citizens if c.alive], min(5, len(city.citizens)))
                    for c in sample_citizens:
                        partner_info = f"配偶: {c.partner.name}" if c.partner else "單身"
                        family_info = f"家族: {c.family.name} (聲望: {c.family.reputation:.2f})" if c.family else "無家族"
                        st.write(f"- **{c.name}**: 年齡 {c.age}, 健康 {c.health:.2f}, 信任 {c.trust:.2f}, 快樂度 {c.happiness:.2f}, 思想 {c.ideology}, 職業 {c.profession}, 教育 {c.education_level}, 財富 {c.wealth:.2f}, {partner_info}, {family_info}")
                else:
                    st.info("該城市目前沒有活著的市民。")

            break
    if found_city:
        break
if not found_city and selected_city:
    st.warning(f"目前無法找到城市 **{selected_city}** 的資訊，它可能已經滅亡。")


st.markdown("---")
st.markdown("## 📊 跨城市數據對比")
with st.container():
    all_city_data = []
    for planet in galaxy.planets:
        for city in planet.cities:
            alive_citizens = [c for c in city.citizens if c.alive]
            avg_health = sum(c.health for c in alive_citizens) / max(1, len(alive_citizens)) if alive_citizens else 0
            avg_trust = sum(c.trust for c in alive_citizens) / max(1, len(alive_citizens)) if alive_citizens else 0
            avg_happiness = sum(c.happiness for c in alive_citizens) / max(1, len(alive_citizens)) if alive_citizens else 0
            
            all_city_data.append({
                "行星": planet.name, "城市": city.name, "人口": len(city.citizens),
                "平均健康": f"{avg_health:.2f}", "平均信任": f"{avg_trust:.2f}", "平均快樂度": f"{avg_happiness:.2f}",
                "糧食": city.resources['糧食'], "能源": city.resources['能源'], "稅收": city.resources['稅收'],
                "產業專精": city.specialization,
                "軍事科技": f"{planet.tech_levels['軍事']:.2f}", "環境科技": f"{planet.tech_levels['環境']:.2f}",
                "醫療科技": f"{planet.tech_levels['醫療']:.2f}", "生產科技": f"{planet.tech_levels['生產']:.2f}",
                "污染": f"{planet.pollution:.2f}", "衝突等級": f"{planet.conflict_level:.2f}",
                "防禦等級": planet.defense_level,
                "群眾運動": '是' if city.mass_movement_active else '否',
                "合作經濟": f"{city.cooperative_economy_level:.2f}",
                "政體": city.government_type,
                "執政黨": city.ruling_party.name if city.ruling_party else '無'
            })

    if all_city_data:
        df_cities = pd.DataFrame(all_city_data)
        st.dataframe(df_cities.set_index("城市"))
    else:
        st.info("目前沒有城市數據可供對比。")


st.markdown("---")
st.markdown("## 🗞️ 未來之城日報")
with st.container():
    if galaxy.global_events_log:
        st.markdown("點擊年份查看當年度事件：")
        for report_entry in reversed(galaxy.global_events_log[-50:]):
            with st.expander(f"**{report_entry['year']} 年年度報告**"):
                if report_entry['events']:
                    for evt in report_entry['events']:
                        st.write(f"- {evt}")
                else:
                    st.info(f"{report_entry['year']} 年全球風平浪靜，沒有重大事件發生。")
    else:
        st.info("目前還沒有未來之城日報的記錄。")

st.markdown("---")
st.info("模擬結束。請調整模擬年數或選擇其他城市查看更多資訊。")
