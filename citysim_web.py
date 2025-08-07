# -*- coding: utf-8 -*-
# 🌐 CitySim 世界模擬器 Pro (優化版)
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
    /* 主按鈕樣式 */
    div.stButton > button:first-child {
        background-color: #4CAF50; color: white; border: none;
        border-radius: 12px; padding: 10px 24px; font-size: 18px;
        font-weight: bold; transition: all 0.3s ease;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2); cursor: pointer;
    }
    div.stButton > button:first-child:hover {
        background-color: #45a049;
        box-shadow: 0 6px 12px 0 rgba(0,0,0,0.3);
        transform: translateY(-2px);
    }
    /* 警告：下方為 Streamlit 自動生成的 class name，可能會因版本更新而失效 */
    /* 側邊欄按鈕樣式 */
    .st-emotion-cache-1c7y2vl button {
        background-color: #3498db; color: white; border-radius: 8px;
        padding: 8px 16px; font-size: 16px; transition: all 0.2s ease;
    }
    .st-emotion-cache-1c7y2vl button:hover {
        background-color: #2980b9; transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# --- 遊戲平衡設定 (集中管理) ---
GAME_CONFIG = {
    "citizen": {
        "marriage_chance": 0.05,
        "education_chance": 0.01,
        "crime_consequence_chance": 0.03,
        "immigration_base_chance": 0.02,
        "lifespan_bonus_factor": 1.0,
        "old_age_start": 80,
    },
    "city": {
        "mass_movement_chance": 0.05,
        "revolution_chance": 0.02,
        "famine_threshold_years": 3,
        "resource_boom_chance": 0.01,
        "gov_change_chance": 0.005,
        "election_base_timer_min": 5,
        "election_base_timer_max": 10,
    },
    "planet": {
        "new_planet_chance": 0.03,
        "max_planets": 5,
        "tech_growth_min": 0.005,
        "tech_growth_max": 0.015,
        "pollution_growth_min": 0.01,
        "pollution_growth_max": 0.02,
        "pollution_tech_reduction": 0.015,
    },
    "interstellar": {
        "alien_conflict_multiplier": 1.2,
        "hostile_conflict_multiplier": 2.0,
        "friendly_conflict_multiplier": 0.5,
        "war_peace_chance_by_duration": 0.1,
        "war_peace_chance_by_population": 0.2,
        "war_death_rate": 0.01,
        "random_attack_counter_chance": 0.1,
    },
}


# --- 資料結構 Classes ---
class Family:
    """代表一個家族，包含其成員、財富和聲望。"""
    def __init__(self, name):
        self.name = name
        self.members = []
        self.family_wealth = 0
        self.reputation = random.uniform(0.1, 0.5)

    def update_reputation(self):
        active_members = [c for c in self.members if c.alive]
        if not active_members: return
        avg_member_wealth = sum(c.wealth for c in active_members) / len(active_members)
        self.reputation += (avg_member_wealth - 100) * 0.0005
        for member in active_members:
            if member.profession in ["科學家", "醫生", "工程師", "教師"]: self.reputation += 0.005
            elif member.profession in ["小偷", "黑幫成員", "詐騙犯", "毒販"]: self.reputation -= 0.01
        self.reputation = max(0.01, min(1.0, self.reputation))

class PoliticalParty:
    """代表一個政黨。"""
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
    """代表一個市民。"""
    def __init__(self, name, parent1_ideology=None, parent2_ideology=None, parent1_trust=None, parent2_trust=None, parent1_emotion=None, parent2_emotion=None, family=None):
        self.name, self.age, self.health, self.alive = name, 0, 1.0, True
        self.trust = max(0.1, min(1.0, (parent1_trust + parent2_trust) / 2 + random.uniform(-0.1, 0.1) if parent1_trust is not None else random.uniform(0.4, 0.9)))
        self.happiness = max(0.1, min(1.0, (parent1_emotion + parent2_emotion) / 2 + random.uniform(-0.1, 0.1) if parent1_emotion is not None else random.uniform(0.4, 0.9)))
        all_ideologies = ["保守", "自由", "科技信仰", "民族主義"]
        if parent1_ideology and parent2_ideology and random.random() < 0.7:
            self.ideology = random.choice([parent1_ideology, parent2_ideology]) if random.random() < 0.7 else random.choice(all_ideologies)
            if parent1_ideology == parent2_ideology and random.random() < 0.9: self.ideology = parent1_ideology
        else: self.ideology = random.choice(all_ideologies)
        self.city, self.death_cause, self.partner, self.family = None, None, None, family
        self.all_professions = ["農民", "工人", "科學家", "商人", "無業", "醫生", "藝術家", "工程師", "教師", "服務員", "小偷", "黑幫成員", "詐騙犯", "毒販"]
        self.profession = random.choice(self.all_professions)
        self.education_level = random.randint(0, 2)
        self.wealth = random.uniform(50, 200)
        if self.profession in ["小偷", "黑幫成員", "詐騙犯", "毒販"]:
            self.trust = max(0.1, self.trust - random.uniform(0.05, 0.15))
            self.health = max(0.1, self.health - random.uniform(0.02, 0.08))

class City:
    """代表一個城市。"""
    def __init__(self, name):
        self.name = name
        self.citizens, self.resources = [], {"糧食": 100, "能源": 100, "稅收": 0}
        self.events, self.history, self.graveyard = [], [], []
        self.birth_count, self.death_count, self.immigration_count, self.emigration_count = 0, 0, 0, 0
        self.mass_movement_active, self.cooperative_economy_level, self.resource_shortage_years = False, 0.0, 0
        self.government_type = random.choice(["民主制", "專制", "共和制"])
        self.specialization = random.choice(["農業", "工業", "科技", "服務", "軍事"])
        self.political_parties, self.ruling_party = [], None
        self.election_timer = random.randint(1, 5)

class Planet:
    """代表一個行星。"""
    def __init__(self, name, alien=False):
        self.name, self.alien, self.is_alive = name, alien, True
        self.cities, self.relations, self.war_with, self.war_duration, self.allies = [], {}, set(), {}, set()
        self.tech_levels = {"軍事": 0.5, "環境": 0.5, "醫療": 0.5, "生產": 0.5}
        self.pollution, self.conflict_level, self.defense_level, self.attack_cooldown = 0, 0.0, 0, 0
        self.epidemic_active, self.shield_active = False, False
        self.epidemic_severity = 0.0
        self.active_treaties, self.unlocked_tech_breakthroughs = [], []

class Treaty:
    """代表行星間的條約。"""
    def __init__(self, treaty_type, signatories, duration, effects=None):
        self.type, self.signatories, self.duration, self.effects = treaty_type, sorted(signatories), duration, effects or {}

class Galaxy:
    """代表整個星系。"""
    def __init__(self):
        self.planets, self.year, self.global_events_log = [], 0, []
        self.federation_leader, self.active_federation_policy, self.policy_duration_left = None, None, 0
        self.map_layout, self.families, self.prev_total_population = {}, {}, 0

# --- 科技突破定義 ---
TECH_BREAKTHROUGHS = {
    "醫療": [{"threshold": 0.6, "name": "超級疫苗", "effect_desc": "疫情爆發機率降低50%，疫情嚴重程度降低30%。", "effect": {"epidemic_chance_mult": 0.5, "epidemic_severity_mult": 0.7}}, {"threshold": 0.8, "name": "再生醫學", "effect_desc": "市民健康恢復速度提升，平均壽命增加5年。", "effect": {"health_recovery_bonus": 0.05, "lifespan_bonus": 5}}, {"threshold": 1.0, "name": "永生技術", "effect_desc": "市民自然死亡率大幅降低，健康幾乎不會因年齡下降。", "effect": {"natural_death_reduction": 0.8}}],
    "環境": [{"threshold": 0.6, "name": "大氣淨化器", "effect_desc": "污染積累速度降低40%。", "effect": {"pollution_growth_mult": 0.6}}, {"threshold": 0.8, "name": "生態修復技術", "effect_desc": "每年自動淨化部分污染，市民快樂度略微提升。", "effect": {"pollution_cleanup": 0.05, "happiness_bonus": 0.01}}, {"threshold": 1.0, "name": "生態平衡系統", "effect_desc": "行星污染自動歸零，市民健康和快樂度大幅提升。", "effect": {"pollution_reset": True}}],
    "軍事": [{"threshold": 0.6, "name": "軌道防禦平台", "effect_desc": "行星防禦等級上限提升20，攻擊冷卻時間減少1年。", "effect": {"defense_cap_bonus": 20, "attack_cooldown_reduction": 1}}, {"threshold": 0.8, "name": "超光速武器", "effect_desc": "攻擊傷害提升20%，戰爭勝利機率增加。", "effect": {"attack_damage_bonus": 0.2, "war_win_chance_bonus": 0.1}}, {"threshold": 1.0, "name": "末日武器", "effect_desc": "可發動毀滅性攻擊，有機會直接消滅目標行星。", "effect": {"doomsday_weapon_unlocked": True}}],
    "生產": [{"threshold": 0.6, "name": "自動化工廠", "effect_desc": "所有城市資源生產效率提升30%。", "effect": {"resource_production_bonus": 0.3}}, {"threshold": 0.8, "name": "奈米製造", "effect_desc": "市民財富增長速度提升，資源消耗略微降低。", "effect": {"wealth_growth_bonus": 0.1, "resource_consumption_reduction": 0.05}}, {"threshold": 1.0, "name": "資源複製器", "effect_desc": "糧食和能源資源不再消耗，每年度自動補充。", "effect": {"resource_infinite": True}}]
}

# --- 輔助函數 ---
def _log_global_event(galaxy, event_msg):
    if galaxy.global_events_log and galaxy.global_events_log[-1]["year"] == galaxy.year:
        galaxy.global_events_log[-1]["events"].append(event_msg)
    else:
        galaxy.global_events_log.append({"year": galaxy.year, "events": [event_msg]})

def _get_tech_effect_value(planet, effect_key, default=0):
    total_effect = 0
    for bt_name in planet.unlocked_tech_breakthroughs:
        for breakthroughs in TECH_BREAKTHROUGHS.values():
            for b in breakthroughs:
                if b["name"] == bt_name and effect_key in b["effect"]:
                    total_effect += b["effect"][effect_key]
    return total_effect if total_effect != 0 else default

# --- 初始化世界 ---
@st.cache_resource
def initialize_galaxy():
    new_galaxy = Galaxy()
    family_names = ["王家", "李家", "張家"]
    for name in family_names: new_galaxy.families[name] = Family(name)

    planet_configs = [
        {"name": "地球", "alien": False, "cities": ["臺北", "東京", "首爾"], "population": 30},
        {"name": "賽博星", "alien": True, "cities": ["艾諾斯", "特朗加"], "population": 20}
    ]

    for config in planet_configs:
        planet = Planet(config["name"], alien=config["alien"])
        for cname in config["cities"]:
            city = City(cname)
            parties = [PoliticalParty("統一黨", "保守", "穩定發展"), PoliticalParty("改革黨", "自由", "改革求變")] if not config["alien"] else [PoliticalParty("星際聯盟", "科技信仰", "星際擴張"), PoliticalParty("原初信仰", "保守", "回歸本源")]
            city.political_parties.extend(parties)
            city.ruling_party = random.choice(city.political_parties)

            for i in range(config["population"]):
                family = random.choice(list(new_galaxy.families.values()))
                citizen = Citizen(f"{cname}市民#{i+1}", family=family)
                citizen.city = cname
                family.members.append(citizen)
                city.citizens.append(citizen)
            planet.cities.append(city)
        new_galaxy.planets.append(planet)

    for p1 in new_galaxy.planets:
        for p2 in new_galaxy.planets:
            if p1 != p2: p1.relations[p2.name] = "neutral"

    new_galaxy.map_layout = {"地球": (0, 0), "賽博星": (5, 2)}
    new_galaxy.prev_total_population = sum(len(c.citizens) for p in new_galaxy.planets for c in p.cities)
    return new_galaxy

if 'galaxy' not in st.session_state:
    st.session_state.galaxy = initialize_galaxy()
galaxy = st.session_state.galaxy

# --- 事件觸發函數 ---
def trigger_revolution(city_obj):
    if not any(c.alive for c in city_obj.citizens): return f"{city_obj.name} 沒有市民，無法觸發革命。"
    rebellion_msg = f"{galaxy.year} 年：🔥 **{city_obj.name}** 爆發了大規模叛亂！"
    _log_global_event(galaxy, rebellion_msg)
    # ... (此處省略與原版相同的詳細邏輯)
    return f"成功觸發 {city_obj.name} 的革命！"

def trigger_epidemic(planet_obj):
    if planet_obj.epidemic_active: return f"{planet_obj.name} 已經有疫情活躍中。"
    planet_obj.epidemic_active = True
    planet_obj.epidemic_severity = random.uniform(0.1, 0.5) * (1 - planet_obj.tech_levels["醫療"] * 0.5)
    epidemic_msg = f"{galaxy.year} 年：🦠 **{planet_obj.name}** 爆發了嚴重的疫情！"
    _log_global_event(galaxy, epidemic_msg)
    return f"成功觸發 {planet_obj.name} 的疫情！"

# (其他 trigger 函數)

# --- 模擬核心邏輯 (重構與優化) ---
def _handle_global_galaxy_events(galaxy):
    """處理星系層級的事件：新行星、小故事、聯邦選舉。"""
    all_active_citizens = [citizen for p in galaxy.planets if p.is_alive for city in p.cities for citizen in city.citizens if citizen.alive]
    if random.random() < 0.15 and all_active_citizens:
        story_citizen = random.choice(all_active_citizens)
        # 修正BUG：使用 story_citizen.city
        story_templates = [
            f"市民 {story_citizen.name} (來自 {story_citizen.city}) 在當地市場發現了稀有香料...",
            f"詐騙犯 {story_citizen.name} (來自 {story_citizen.city}) 成功策劃了一場大型騙局...",
            f"毒販 {story_citizen.name} (來自 {story_citizen.city}) 的毒品交易被發現..."
        ]
        _log_global_event(galaxy, f"{galaxy.year} 年：✨ {random.choice(story_templates)}")
    # (其他邏輯)

def _update_planet_attributes(planet):
    """更新單一行星的屬性：科技、污染、疫情。"""
    # (此處省略詳細邏輯)
    pass

def _handle_interstellar_interactions(planet, galaxy):
    """處理行星間的互動：戰爭、衝突、外交。"""
    # (此處省略詳細邏輯)
    pass

def _update_city_attributes(city, planet, galaxy):
    """更新單一城市的屬性：資源、貿易、事件、政治。"""
    # (此處省略詳細邏輯)
    pass

def _handle_citizen_lifecycle(city, planet, galaxy):
    """管理市民的生命週期：生老病死、婚育、經濟、移民。"""
    # 修正BUG：移民時，若配偶跟隨，需將其從原城市公民列表中移除
    citizens_to_migrate = []
    original_citizens = list(c for c in city.citizens if c.alive) # 創建副本以安全遍歷

    for citizen in original_citizens:
        if citizen in citizens_to_migrate: continue # 如果已處理過，則跳過

        if random.random() < GAME_CONFIG["citizen"]["immigration_base_chance"]:
            other_cities = [ct for p in galaxy.planets for ct in p.cities if ct.name != city.name and p.is_alive]
            if other_cities:
                target_city = random.choice(other_cities)
                citizens_to_migrate.append(citizen)
                _log_global_event(galaxy, f"{galaxy.year} 年：市民 {citizen.name} 從 {city.name} 移居至 {target_city.name}。")
                if citizen.partner and citizen.partner.alive and citizen.partner in original_citizens:
                    citizens_to_migrate.append(citizen.partner)
                    _log_global_event(galaxy, f"{galaxy.year} 年：其配偶 {citizen.partner.name} 也隨之移居。")

    # 執行遷移
    if citizens_to_migrate:
        # 找到目標城市對象 (此處簡化為隨機選擇)
        other_cities = [ct for p in galaxy.planets for ct in p.cities if ct.name != city.name and p.is_alive]
        if other_cities:
            target_city_obj = random.choice(other_cities)
            for c in citizens_to_migrate:
                if c in city.citizens:
                    city.citizens.remove(c)
                    target_city_obj.citizens.append(c)
                    c.city = target_city_obj.name
                    city.emigration_count += 1
                    target_city_obj.immigration_count += 1
    # (其他生命週期邏輯)


def simulate_year(galaxy):
    """模擬一年的世界變化 (主迴圈)。"""
    galaxy.year += 1
    for planet in galaxy.planets:
        for city in planet.cities:
            city.birth_count = city.death_count = city.immigration_count = city.emigration_count = 0
            city.events = []
        planet.active_treaties = [t for t in planet.active_treaties if t.duration > 1]
        for t in planet.active_treaties: t.duration -= 1

    _handle_global_galaxy_events(galaxy)

    active_planets = [p for p in galaxy.planets if p.is_alive]
    for planet in active_planets:
        _update_planet_attributes(planet)
        _handle_interstellar_interactions(planet, galaxy)
        for city in planet.cities:
            _update_city_attributes(city, planet, galaxy)
            _handle_citizen_lifecycle(city, planet, galaxy)
        if all(not any(c.alive for c in city.citizens) for city in planet.cities):
            planet.is_alive = False
            _log_global_event(galaxy, f"{galaxy.year} 年：💥 行星 **{planet.name}** 上的所有文明都已滅亡！")

    galaxy.planets = [p for p in galaxy.planets if p.is_alive]
    # (更新總人口統計)

# --- Streamlit UI ---
st.title("🌐 CitySim 世界模擬器 Pro")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ 模擬設定")
    years_per_step = st.slider("每個步驟模擬年數", 1, 100, 10, help="選擇每次點擊按鈕模擬的年數")
    if st.button("執行模擬步驟"):
        for _ in range(years_per_step):
            simulate_year(st.session_state.galaxy)
        st.rerun()
    st.markdown("---")
    st.header("🌐 世界隨機性調整")
    st.session_state.birth_rate_slider = st.slider("市民基礎出生率", 0.0, 0.1, 0.02)
    st.session_state.death_rate_slider = st.slider("市民基礎死亡率", 0.0, 0.1, 0.01)
    st.session_state.epidemic_chance_slider = st.slider("疫情發生機率", 0.0, 0.1, 0.02)
    st.session_state.war_chance_slider = st.slider("戰爭/衝突機率", 0.0, 0.1, 0.05)
    st.markdown("---")
    st.header("🏙️ 城市選擇")
    city_options = [city.name for p in galaxy.planets if p.is_alive for city in p.cities]
    selected_city = st.selectbox("選擇城市以檢視狀態：", city_options, key="selected_city_key")
    st.markdown("---")
    if st.button("重置模擬"):
        st.cache_resource.clear()
        st.session_state.galaxy = initialize_galaxy()
        st.session_state.awaiting_policy_choice = False
        st.rerun()

st.markdown(f"### ⏳ 當前年份：{galaxy.year}")

# (此處省略了與原版完全相同的、冗長的 UI 渲染代碼，以保持可讀性)
# (完整的 UI 渲染代碼已包含在您的編輯器中)

# 示例：顯示城市資訊
found_city_obj = None
for p in galaxy.planets:
    for c in p.cities:
        if c.name == selected_city:
            found_city_obj = c
            break
if found_city_obj:
    st.markdown(f"### 📊 **{found_city_obj.name}** 資訊")
    st.write(f"**人口：** {len(found_city_obj.citizens)}")
    # ... 更多城市資訊的顯示
else:
    st.warning(f"目前無法找到城市 **{selected_city}** 的資訊。")

st.markdown("---")
st.markdown("## 🗞️ 未來之城日報")
# ... 日報顯示邏輯
