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
                new_galaxy.planets[-1].relations[p1.name] = "neutral" # [修正] 確保新行星也初始化關係
    
    new_galaxy.map_layout = {
        "地球": (0, 0),
        "賽博星": (5, 2)
    }

    # 修正這一行：遍歷 new_galaxy.planets 中的每個 planet，然後再遍歷 planet.cities
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
                f"詐騙犯 {story_citizen.name} (來自 {story_citizen.city}) 成功策劃了一場大型騙局，獲得了巨額財富。",  # [修正] 修正了city變數
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
                # [修正] 這裡應該使用全局的 galaxy.families, 而不是 initialize_galaxy 函式中的 new_galaxy
                initial_family = random.choice(list(galaxy.families.values()))
                citizen = Citizen(f"{new_city_name}市民#{j+1}", family=initial_family)
                citizen.city = new_city_name
                initial_family.members.append(citizen)
                new_city.citizens.append(citizen)
            new_planet.cities.append(new_city)
        
        for p in galaxy.planets:
            p.relations[new_planet.name] = "neutral"
            new_planet.relations[p.name] = "neutral"
        
        galaxy.planets.append(new_planet)
        _log_global_event(galaxy, f"{galaxy.year} 年：  探測器發現了新的宜居行星 **{new_planet_name}**，並迅速建立了 {num_new_cities} 個定居點！")
        
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
                _log_global_event(galaxy, f"{galaxy.year} 年： 星系聯邦舉行了盛大的選舉！來自 {galaxy.federation_leader.city} 的市民 **{galaxy.federation_leader.name}** 以其卓越的信任度被選為新的聯邦領導人！")

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
            elif policy["type"] == "促進貿易": # Added missing policy effect
                for city in planet.cities:
                    for citizen in [c for c in city.citizens if c.alive]:
                        citizen.wealth = min(1000, citizen.wealth + policy["effect"] * 10) # Example effect
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
    
    # [新增] 處理條約持續時間
    for planet in galaxy.planets:
        treaties_to_remove = []
        for treaty in planet.active_treaties:
            treaty.duration -= 1
            if treaty.duration <= 0:
                treaties_to_remove.append(treaty)
        for treaty in treaties_to_remove:
            planet.active_treaties.remove(treaty)
            _log_global_event(galaxy, f"{galaxy.year} 年：條約「{treaty.type}」已失效，簽署方：{', '.join(treaty.signatories)}。")
            
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
            
            # 戰爭結束條件
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
                planet.relations[other_planet_obj.name] = "neutral"
                other_planet_obj.relations[planet.name] = "neutral"
                _log_global_event(galaxy, f"{galaxy.year} 年：🕊️ **{planet.name}** 與 **{other_planet_obj.name}** 簽署和平條約，結束了漫長的戰爭！星際間恢復了短暫的寧靜。")
                
                winner, loser = (planet, other_planet_obj) if planet_pop > other_planet_pop else (other_planet_obj, planet)
                
                # [優化] 戰爭勝利後，如果勝者人口遠大於敗者，則進行資源、稅收、人口和科技轉移
                if winner.name == planet.name and planet_pop > other_planet_pop * 1.5:
                    winner_resource_gain = int(sum(c.resources["糧食"] for c in loser.cities) * 0.1)
                    winner_tax_gain = int(sum(c.resources["稅收"] for c in loser.cities) * 0.2)
                    for city in winner.cities:
                        city.resources["糧食"] += winner_resource_gain / max(1, len(winner.cities))
                        city.resources["稅收"] += winner_tax_gain / max(1, len(winner.cities))
                    
                    pop_transfer = int(sum(len(c.citizens) for c in loser.cities) * 0.05)
                    transfer_candidates = [c for city in loser.cities for c in city.citizens if c.alive]
                    for _ in range(pop_transfer):
                        if transfer_candidates and winner.cities:
                            c = random.choice(transfer_candidates)
                            transfer_from_city = next((city for city in loser.cities if c in city.citizens), None)
                            if transfer_from_city:
                                transfer_from_city.citizens.remove(c)
                                c.city = winner.cities[0].name
                                winner.cities[0].citizens.append(c)
                                transfer_candidates.remove(c)
                    
                    for tech_type in winner.tech_levels.keys():
                        winner.tech_levels[tech_type] = min(1.0, winner.tech_levels[tech_type] + loser.tech_levels[tech_type] * 0.05)
                    _log_global_event(galaxy, f"{galaxy.year} 年：🏆 **{winner.name}** 在戰爭中取得勝利，獲得了資源、人口並竊取了科技！戰敗方付出了沉重代價。")
                    for city in loser.cities:
                        for citizen in [c for c in city.citizens if c.alive]:
                            citizen.trust = max(0.1, citizen.trust - 0.1)
                            citizen.happiness = max(0.1, citizen.happiness - 0.1)
                
                # [修正] 移除此處的 return，讓其他行星的互動能繼續進行
                # return 

        # --- 非戰爭狀態下的衝突觸發與關係演變 ---
        base_conflict_chance = st.session_state.war_chance_slider
        if planet.alien or other_planet_obj.alien:
            base_conflict_chance *= 1.2
        
        # [修正] 修正非侵略條約的影響，使其更為精確
        treaty_multiplier = 1
        for treaty in planet.active_treaties:
            if treaty.type == "非侵略" and other_planet_obj.name in treaty.signatories:
                treaty_multiplier = 0.2 # 大幅降低衝突機率
                break
        
        conflict_chance = max(0.01, base_conflict_chance * (1 - planet.tech_levels["軍事"]))
        conflict_chance *= treaty_multiplier # Apply non-aggression treaty effect
        
        if relation_status == "friendly":
            conflict_chance *= 0.5
        elif relation_status == "hostile":
            conflict_chance *= 2.0

        if random.random() < conflict_chance:
            planet.conflict_level = min(1.0, planet.conflict_level + random.uniform(0.05, 0.15))
            other_planet_obj.conflict_level = min(1.0, other_planet_obj.conflict_level + random.uniform(0.05, 0.15))
            _log_global_event(galaxy, f"{galaxy.year} 年：⚠️ {planet.name} 與 {other_planet_obj.name} 的衝突等級提升至 {planet.conflict_level:.2f}！緊張局勢加劇。")
            
            if relation_status != "hostile":
                planet.relations[other_planet_obj.name] = "hostile"
                other_planet_obj.relations[planet.name] = "hostile"
                _log_global_event(galaxy, f"{galaxy.year} 年：💥 {planet.name} 與 {other_planet_obj.name} 的關係惡化為敵對！外交關係跌至冰點。")
            
            if planet.conflict_level > 0.7 and other_planet_obj.conflict_level > 0.7 and planet.relations[other_planet_obj.name] == "hostile":
                planet.war_with.add(other_planet_obj.name)
                other_planet_obj.war_with.add(planet.name)
                planet.war_duration[other_planet_obj.name] = 0
                other_planet_obj.war_duration[planet.name] = 0
                _log_global_event(galaxy, f"{galaxy.year} 年：⚔️ **{planet.name}** 向 **{other_planet_obj.name}** 宣戰！星際戰爭全面爆發，宇宙為之顫抖！")
        else:
            planet.conflict_level = max(0.0, planet.conflict_level - random.uniform(0.01, 0.05))
            other_planet_obj.conflict_level = max(0.0, other_planet_obj.conflict_level - random.uniform(0.01, 0.05))
            if relation_status == "hostile" and random.random() < 0.02:
                planet.relations[other_planet_obj.name] = "neutral"
                other_planet_obj.relations[planet.name] = "neutral"
                _log_global_event(galaxy, f"{galaxy.year} 年：🤝 {planet.name} 與 {other_planet_obj.name} 的關係從敵對轉為中立。冰釋前嫌的跡象浮現。")
            elif relation_status == "neutral" and random.random() < 0.01:
                planet.relations[other_planet_obj.name] = "friendly"
                other_planet_obj.relations[planet.name] = "friendly"
                _log_global_event(galaxy, f"{galaxy.year} 年：✨ {planet.name} 與 {other_planet_obj.name} 的關係轉為友善。外交新篇章開啟。")

def _update_city_logic(city, planet, current_year_global_events):
    """更新單一城市邏輯，包含人口、資源、政治、事件等。"""
    if not city.citizens:
        city.events.append(f"{galaxy.year} 年：城市 {city.name} 已無市民，陷入廢墟。")
        return

    # 市民個體更新
    birth_count = 0
    death_count = 0
    newborn_citizens = []
    
    # 資源消耗與生產
    production_bonus = 1 + (_get_tech_effect_value(planet, "resource_production_bonus") or 0)
    consumption_reduction = (_get_tech_effect_value(planet, "resource_consumption_reduction") or 0)
    
    if (_get_tech_effect_value(planet, "resource_infinite") or False):
        city.resources["糧食"] = 500
        city.resources["能源"] = 500
    else:
        city.resources["糧食"] += (10 * (city.specialization == "農業")) * production_bonus
        city.resources["能源"] += (10 * (city.specialization == "工業")) * production_bonus

        city.resources["糧食"] = max(0, city.resources["糧食"] - (len(city.citizens) * (1 - consumption_reduction)))
        city.resources["能源"] = max(0, city.resources["能源"] - (len(city.citizens) * 0.5 * (1 - consumption_reduction)))

    # 人口與事件
    living_citizens = [c for c in city.citizens if c.alive]
    for citizen in living_citizens:
        citizen.age += 1
        
        # 健康與老化
        citizen.health = max(0, min(1.0, citizen.health - (citizen.age * 0.0005) + random.uniform(0.005, 0.01)))
        
        # 財富更新
        wealth_growth_bonus = _get_tech_effect_value(planet, "wealth_growth_bonus") or 0
        if citizen.profession == "商人":
            citizen.wealth = min(1000, citizen.wealth + random.uniform(5, 15) * (1 + wealth_growth_bonus))
        elif citizen.profession == "工人" or citizen.profession == "農民":
            citizen.wealth = min(1000, citizen.wealth + random.uniform(1, 5) * (1 + wealth_growth_bonus))
        elif citizen.profession in ["科學家", "醫生", "工程師"]:
            citizen.wealth = min(1000, citizen.wealth + random.uniform(3, 8) * (1 + wealth_growth_bonus))
        elif citizen.profession == "無業":
            citizen.wealth = max(0, citizen.wealth - random.uniform(1, 3))
        elif citizen.profession in ["小偷", "黑幫成員", "詐騙犯", "毒販"]:
            citizen.wealth = min(1000, citizen.wealth + random.uniform(5, 20) * (1 + wealth_growth_bonus))
        
        # 死亡
        natural_death_reduction = _get_tech_effect_value(planet, "natural_death_reduction") or 0
        death_chance = (citizen.age / 100) * (1 - natural_death_reduction)
        if citizen.health < 0.2 and random.random() < 0.5:
            death_chance += 0.2
            
        if not citizen.alive or random.random() < death_chance:
            citizen.alive = False
            citizen.death_cause = "自然死亡" if not citizen.death_cause else citizen.death_cause
            death_count += 1
            city.graveyard.append((citizen.name, citizen.age, citizen.ideology, citizen.death_cause))
            _log_global_event(galaxy, f"{galaxy.year} 年：市民 {citizen.name} (來自 {city.name}) 因 {citizen.death_cause} 而去世，享年 {citizen.age} 歲。")
            
        # 生育
        if citizen.age >= 20 and citizen.age <= 50 and citizen.partner and random.random() < 0.02:
            child_name = f"{city.name}市民#{len(city.citizens) + len(newborn_citizens) + 1}"
            child = Citizen(child_name, 
                            parent1_ideology=citizen.ideology, 
                            parent2_ideology=citizen.partner.ideology,
                            parent1_trust=citizen.trust,
                            parent2_trust=citizen.partner.trust,
                            parent1_emotion=citizen.happiness,
                            parent2_emotion=citizen.partner.happiness,
                            family=citizen.family) # 子女繼承一方家族
            
            newborn_citizens.append(child)
            birth_count += 1
            _log_global_event(galaxy, f"{galaxy.year} 年：恭喜！市民 {citizen.name} (來自 {city.name}) 和伴侶迎來了新生命 {child.name}！")

    city.citizens.extend(newborn_citizens)
    city.birth_count = birth_count
    city.death_count = death_count

    # 政黨選舉與統治
    if city.election_timer <= 0:
        for party in city.political_parties:
            party.calculate_support(city.citizens)
        
        if city.political_parties:
            winner = max(city.political_parties, key=lambda p: p.support)
            if winner != city.ruling_party:
                old_ruling_party_name = city.ruling_party.name if city.ruling_party else "無"
                city.ruling_party = winner
                city.events.append(f"{galaxy.year} 年：政權更迭！**{city.ruling_party.name}** 在選舉中獲勝，取代了 {old_ruling_party_name}。")
                _log_global_event(galaxy, f"{galaxy.year} 年：**{city.name}** 選舉結束，**{city.ruling_party.name}** 成為新的執政黨！")
        city.election_timer = random.randint(3, 7)
    else:
        city.election_timer -= 1
    
    # 政黨政策影響
    if city.ruling_party:
        if city.ruling_party.platform == "穩定發展":
            for citizen in living_citizens:
                citizen.happiness = min(1.0, citizen.happiness + 0.01)
                citizen.trust = min(1.0, citizen.trust + 0.005)
        elif city.ruling_party.platform == "改革求變":
            for citizen in living_citizens:
                citizen.happiness = max(0.1, citizen.happiness - 0.01)
                citizen.trust = max(0.1, citizen.trust - 0.005)
                citizen.wealth = min(1000, citizen.wealth + random.uniform(1, 5))
        elif city.ruling_party.platform in ["加速科技", "星際擴張"]:
            planet.tech_levels["生產"] = min(1.0, planet.tech_levels["生產"] + 0.005)
            planet.tech_levels["軍事"] = min(1.0, planet.tech_levels["軍事"] + 0.005)

    # 移民與移出
    if len(living_citizens) > 100 and random.random() < 0.1:
        emigration_count = int(len(living_citizens) * random.uniform(0.01, 0.05))
        emigrants = random.sample(living_citizens, min(emigration_count, len(living_citizens)))
        for c in emigrants:
            city.citizens.remove(c)
            city.emigration_count += 1
            # 這裡我們假設他們移出星系了
            _log_global_event(galaxy, f"{galaxy.year} 年：市民 {c.name} 厭倦了 {city.name} 的生活，選擇離開。")
    
    if len(living_citizens) < 20 and random.random() < 0.1:
        immigration_count = random.randint(1, 5)
        for _ in range(immigration_count):
            immigrant_name = f"新移民#{galaxy.year}-{random.randint(1, 100)}"
            immigrant = Citizen(immigrant_name, family=random.choice(list(galaxy.families.values())))
            immigrant.city = city.name
            city.citizens.append(immigrant)
            city.immigration_count += 1
            _log_global_event(galaxy, f"{galaxy.year} 年：新市民 {immigrant.name} 抵達 {city.name}，為城市注入新活力。")

    # 革命或政變
    unhappy_citizens = [c for c in living_citizens if c.happiness < 0.3]
    if len(unhappy_citizens) > len(living_citizens) * 0.5 and not city.mass_movement_active:
        city.mass_movement_active = True
        _log_global_event(galaxy, f"{galaxy.year} 年：⚠️ {city.name} 的市民快樂度過低，大規模抗議活動正在醞釀！")

    if city.mass_movement_active and random.random() < 0.3:
        if random.random() < 0.7:
            trigger_revolution(city, current_year_global_events)
        else:
            trigger_coup(city, current_year_global_events)

def run_simulation_year(galaxy):
    """執行單一年度的模擬步驟。"""
    galaxy.year += 1
    current_year_global_events = []

    # 1. 更新行星屬性 (科技, 污染, 疫情)
    for planet in galaxy.planets:
        if planet.is_alive:
            _update_planet_attributes(planet, current_year_global_events)

    # 2. 處理行星間互動 (戰爭, 關係)
    for planet in galaxy.planets:
        if planet.is_alive:
            _handle_interstellar_interactions(planet, galaxy, current_year_global_events)

    # 3. 更新城市邏輯 (人口, 資源, 政治)
    for planet in galaxy.planets:
        if planet.is_alive:
            for city in planet.cities:
                _update_city_logic(city, planet, current_year_global_events)

    # 4. 全局星系事件 (新行星, 聯邦)
    _handle_global_galaxy_events(galaxy, current_year_global_events)

    # 5. 更新家族聲望與財富
    for family in galaxy.families.values():
        family.update_reputation()

    # 6. 處理行星毀滅
    for planet in [p for p in galaxy.planets if p.is_alive]:
        if not any(c.citizens for c in planet.cities):
            planet.is_alive = False
            _log_global_event(galaxy, f"{galaxy.year} 年：行星 **{planet.name}** 的所有城市都已消亡，該行星被視為死亡。")

    # 7. 匯總本年度事件
    if current_year_global_events:
        event_str = "\n".join(current_year_global_events)
    else:
        event_str = "本年度宇宙一切平靜。"
    galaxy.global_events_log.append({"year": galaxy.year, "events": current_year_global_events})

# --- Streamlit UI 介面 ---

st.title("🌐 CitySim 世界模擬器 Pro")
st.markdown("一個基於物件導向的星際社會與政治模擬器。")

# 側邊欄設定
with st.sidebar:
    st.header("⚙️ 模擬設定")
    st.markdown("調整這些參數來改變模擬世界的行為。")

    st.slider('戰爭爆發機率 (每年)', 0.0, 0.2, key='war_chance_slider', value=0.05, step=0.01)
    st.slider('疫情爆發機率 (每年)', 0.0, 0.2, key='epidemic_chance_slider', value=0.05, step=0.01)
    
    st.subheader("手動事件觸發")
    st.markdown("立即在選定的城市或行星觸發特殊事件。")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_planet_name_for_event = st.selectbox("選擇行星", [p.name for p in galaxy.planets])
        selected_planet_for_event = next((p for p in galaxy.planets if p.name == selected_planet_name_for_event), None)
        selected_city_name_for_event = st.selectbox("選擇城市", [c.name for c in selected_planet_for_event.cities if selected_planet_for_event] if selected_planet_for_event else [])
        selected_city_for_event = next((c for c in selected_planet_for_event.cities if c.name == selected_city_name_for_event), None)

    with col2:
        if st.button("🚨 觸發革命", key="trigger_revolution_btn"):
            if selected_city_for_event: st.info(trigger_revolution(selected_city_for_event, st.session_state.temp_global_events))
        if st.button("🦠 觸發疫情", key="trigger_epidemic_btn"):
            if selected_planet_for_event: st.info(trigger_epidemic(selected_planet_for_event, st.session_state.temp_global_events))
        if st.button("⚔️ 觸發政變", key="trigger_coup_btn"):
            if selected_city_for_event: st.info(trigger_coup(selected_city_for_event, st.session_state.temp_global_events))
        if st.button("🤖 觸發AI覺醒", key="trigger_ai_btn"):
            if selected_planet_for_event: st.info(trigger_ai_awakening(selected_planet_for_event, st.session_state.temp_global_events))

    if st.button("重新啟動模擬器", type="primary", use_container_width=True):
        st.session_state.clear()
        st.experimental_rerun()

# 聯邦政策選擇 UI
if st.session_state.get('awaiting_policy_choice', False):
    st.warning("星系聯邦新領導人已選出！請選擇一項政策。")
    policy_options = [
        {"type": "提升科技", "desc": "專注於所有行星的科技研發。"},
        {"type": "減少污染", "desc": "實施嚴格的環境法規，減少污染。"},
        {"type": "促進貿易", "desc": "開放貿易路線，提升市民財富。"},
        {"type": "資源補貼", "desc": "為所有城市提供額外的糧食和能源。"},
        {"type": "健康倡議", "desc": "推動全民健康計畫，提升市民健康。"}
    ]
    policy_choice = st.radio("選擇一項政策:", [p["type"] for p in policy_options], key='policy_radio')
    
    if st.button("確認政策", type="secondary"):
        selected_policy_data = next(p for p in policy_options if p["type"] == policy_choice)
        galaxy.active_federation_policy = {
            "type": selected_policy_data["type"],
            "effect": st.session_state.policy_effect
        }
        galaxy.policy_duration_left = st.session_state.policy_duration
        
        _log_global_event(galaxy, f"{galaxy.year} 年：星系聯邦通過了「{policy_choice}」政策，將執行 {galaxy.policy_duration_left} 年。")
        st.session_state.temp_global_events.append(f"{galaxy.year} 年：星系聯邦通過了「{policy_choice}」政策，將執行 {galaxy.policy_duration_left} 年。")
        st.session_state.awaiting_policy_choice = False
        st.rerun()

# 主面板
st.header(f"第 {galaxy.year} 年模擬報告")

if st.button("▶️ 執行一年模擬", type="primary"):
    if st.session_state.get('awaiting_policy_choice', False):
        st.warning("請先選擇一項聯邦政策才能繼續。")
    else:
        run_simulation_year(galaxy)
        st.success(f"成功執行第 {galaxy.year} 年模擬。")

col1, col2, col3 = st.columns(3)
with col1:
    total_population = sum(len(c.citizens) for p in galaxy.planets for c in p.cities)
    st.metric("總人口", total_population, delta=total_population - galaxy.prev_total_population, delta_color="normal")
    galaxy.prev_total_population = total_population
with col2:
    alive_planets = len([p for p in galaxy.planets if p.is_alive])
    st.metric("存活行星數", alive_planets)
with col3:
    in_war_planets = len(set(p.name for p in galaxy.planets for w in p.war_with))
    st.metric("正在交戰的行星數", in_war_planets)

# 模擬結果顯示
st.subheader("年度全球事件日誌")
with st.expander("展開查看詳細日誌"):
    if galaxy.global_events_log:
        for event_entry in reversed(galaxy.global_events_log):
            st.markdown(f"#### 第 {event_entry['year']} 年")
            if event_entry['events']:
                for event_msg in event_entry['events']:
                    st.write(event_msg)
            else:
                st.write("本年度無重大事件發生。")
    else:
        st.write("尚未開始模擬，無事件記錄。")

st.subheader("行星狀態總覽")

planet_data = []
for planet in galaxy.planets:
    population = sum(len(c.citizens) for c in planet.cities)
    planet_data.append({
        "行星名稱": planet.name,
        "類型": "外星文明" if planet.alien else "原生文明",
        "人口": population,
        "科技等級": f"軍事: {planet.tech_levels['軍事']:.2f}, 環境: {planet.tech_levels['環境']:.2f}, 醫療: {planet.tech_levels['醫療']:.2f}, 生產: {planet.tech_levels['生產']:.2f}",
        "污染指數": f"{planet.pollution:.2f}",
        "狀態": "存活" if planet.is_alive else "已滅亡",
        "與地球關係": planet.relations.get('地球', 'N/A'),
        "戰爭狀態": "交戰中" if planet.war_with else "和平",
    })
df_planets = pd.DataFrame(planet_data)

st.dataframe(df_planets, use_container_width=True)

# 互動式地圖
st.subheader("星系地圖")
map_df = pd.DataFrame([{'planet': k, 'x': v[0], 'y': v[1], 'size': (sum(len(c.citizens) for c in p.cities) / total_population) * 1000 if total_population > 0 else 100, 'color': 'red' if p.war_with else 'blue'} for k, v in galaxy.map_layout.items() for p in galaxy.planets if p.name == k])

if not map_df.empty:
    fig = px.scatter(map_df, x="x", y="y", size="size", color="color", hover_name="planet", text="planet", title="星系地圖", size_max=100)
    fig.update_layout(xaxis_title="星系X坐標", yaxis_title="星系Y坐標")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("沒有行星資料可供顯示地圖。")

# 城市詳細資訊
st.subheader("城市詳細資訊")
selected_planet_cities = st.selectbox("選擇行星以查看其城市", [p.name for p in galaxy.planets])
planet_for_cities = next((p for p in galaxy.planets if p.name == selected_planet_cities), None)

if planet_for_cities:
    city_data = []
    for city in planet_for_cities.cities:
        pop = len([c for c in city.citizens if c.alive])
        avg_happiness = sum(c.happiness for c in city.citizens if c.alive) / pop if pop > 0 else 0
        avg_trust = sum(c.trust for c in city.citizens if c.alive) / pop if pop > 0 else 0
        city_data.append({
            "城市名稱": city.name,
            "人口": pop,
            "執政黨": city.ruling_party.name if city.ruling_party else "無",
            "政府類型": city.government_type,
            "平均快樂度": f"{avg_happiness:.2f}",
            "平均信任度": f"{avg_trust:.2f}",
            "糧食": f"{city.resources['糧食']:.0f}",
            "能源": f"{city.resources['能源']:.0f}",
            "特色": city.specialization,
            "事件": f"{len(city.events)} 個",
        })
    df_cities = pd.DataFrame(city_data)
    st.dataframe(df_cities, use_container_width=True)
else:
    st.info("請先選擇一個行星。")

st.markdown("---")
st.markdown("© 2024 CitySim Pro (Optimized Version)")
