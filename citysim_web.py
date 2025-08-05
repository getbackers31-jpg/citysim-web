# -*- coding: utf-8 -*-
# 📡 升級版 Citysim Streamlit UI（滑桿模擬年數 + 城市選擇 + 統計顯示 + 生育/疾病/戰爭/科技/污染 + 稅收/移民/墓園/思想派別/新聞）
import streamlit as st
import random
import pandas as pd # 引入 pandas 用於數據處理和圖表
import plotly.graph_objects as go # 引入 plotly 用於互動式圖表
import plotly.express as px # 引入 plotly.express 用於簡化圖表創建

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
class Citizen:
    """代表城市中的一個市民。"""
    def __init__(self, name, parent1_ideology=None, parent2_ideology=None, parent1_trust=None, parent2_trust=None, parent1_emotion=None, parent2_emotion=None):
        self.name = name
        self.age = 0 # 新生兒年齡從0開始
        self.health = 1.0 # 健康值，1.0 為滿血
        
        # 子女家族傳承
        if parent1_trust is not None and parent2_trust is not None:
            self.trust = (parent1_trust + parent2_trust) / 2 + random.uniform(-0.1, 0.1) # 繼承父母平均信任度，略有波動
            self.trust = max(0.1, min(1.0, self.trust)) # 限制在0.1到1.0之間
        else:
            self.trust = random.uniform(0.4, 0.9) # 預設值

        if parent1_emotion is not None and parent2_emotion is not None:
            self.happiness = (parent1_emotion + parent2_emotion) / 2 + random.uniform(-0.1, 0.1) # 繼承父母平均情緒，略有波動 (改為 happiness)
            self.happiness = max(0.1, min(1.0, self.happiness)) # 限制在0.1到1.0之間
        else:
            self.happiness = random.uniform(0.4, 0.9) # 預設值

        if parent1_ideology and parent2_ideology and random.random() < 0.7: # 70% 機率繼承父母之一的思想
            self.ideology = random.choice([parent1_ideology, parent2_ideology])
        else:
            self.ideology = random.choice(["保守", "自由", "科技信仰", "民族主義"]) # 預設值或隨機

        self.city = None # 所屬城市名稱
        self.alive = True # 是否存活
        self.death_cause = None # 死亡原因
        self.partner = None # 配偶對象 (Citizen 物件)

        # 新增市民屬性 (職業/教育/財富)
        # 增加更多職業，包括高風險職業
        all_professions = [
            "農民", "工人", "科學家", "商人", "無業",
            "醫生", "藝術家", "工程師", "教師", "服務員",
            "小偷", "黑幫成員", "詐騙犯", "毒販"
        ]
        self.profession = random.choice(all_professions)
        self.education_level = random.randint(0, 2) # 0: 無, 1: 初等, 2: 中等, 3: 高等 (初始最高中等)
        self.wealth = random.uniform(50, 200) # 初始財富

        # 根據職業調整初始屬性 (輕微影響，反映職業特點)
        if self.profession in ["小偷", "黑幫成員", "詐騙犯", "毒販"]:
            self.trust = max(0.1, self.trust - random.uniform(0.05, 0.15)) # 犯罪職業初始信任度可能較低
            self.health = max(0.1, self.health - random.uniform(0.02, 0.08)) # 犯罪職業初始健康可能較差

class City:
    """代表一個城市及其屬性。"""
    def __init__(self, name):
        self.name = name
        self.citizens = [] # 城市中的市民列表
        self.resources = {"糧食": 100, "能源": 100, "稅收": 0} # 城市資源
        self.events = [] # 城市發生的事件記錄 (年度事件)
        self.history = [] # 城市歷史數據 (年齡, 平均健康, 平均信任, 平均快樂度)
        self.birth_count = 0 # 年度出生人數
        self.death_count = 0 # 年度死亡人數
        self.immigration_count = 0 # 年度移民遷入人數
        self.emigration_count = 0 # 年度移民遷出人數
        self.graveyard = [] # 墓園記錄 (name, age, ideology, death_cause)
        self.mass_movement_active = False # 是否正在發生群眾運動
        self.cooperative_economy_level = 0.0 # 合作經濟水平
        self.government_type = random.choice(["民主制", "專制", "共和制"]) # 城市政體
        # 新增城市產業專精
        self.specialization = random.choice(["農業", "工業", "科技", "服務", "軍事"])
        self.resource_shortage_years = 0 # 記錄糧食短缺的年數，用於觸發饑荒

class Planet:
    """代表一個行星及其上的城市。"""
    def __init__(self, name, alien=False): 
        self.name = name
        self.cities = [] # 行星上的城市列表
        # 科技水平改為字典
        self.tech_levels = {"軍事": 0.5, "環境": 0.5, "醫療": 0.5, "生產": 0.5} 
        self.pollution = 0 # 污染水平
        self.alien = alien # 是否為外星行星
        self.conflict_level = 0.0 # 行星間衝突等級，0.0 為和平，1.0 為全面戰爭
        self.is_alive = True # 行星是否存活
        self.relations = {} # 與其他行星的關係 (key: other_planet_name, value: "friendly", "neutral", "hostile")
        self.war_with = set() # 正在與哪些行星交戰 (儲存行星名稱)
        self.war_duration = {} # 與各行星的戰爭持續時間 (key: other_planet_name, value: duration_in_years)
        self.epidemic_active = False # 新增：是否有疫情爆發
        self.epidemic_severity = 0.0 # 新增：疫情嚴重程度
        # 新增防禦和聯盟相關屬性
        self.defense_level = 0 # 行星防禦等級，0-100
        self.shield_active = False # 行星護盾是否活躍
        self.allies = set() # 結盟的行星名稱集合
        self.attack_cooldown = 0 # 攻擊冷卻時間

class Galaxy:
    """代表整個星系，包含所有行星和年份。"""
    def __init__(self):
        self.planets = [] # 星系中的行星列表
        self.year = 0 # 當前模擬年份
        self.global_events_log = [] # 記錄所有行星和城市的年度事件，用於日報
        self.federation_leader = None # 星系聯邦領導人
        self.active_federation_policy = None # 當前生效的聯邦政策 (字典: {"type": "科技", "duration": 5, "effect": 0.02})
        self.policy_duration_left = 0 # 政策剩餘生效年數
        self.map_layout = {} # 新增：用於可視化地圖的行星位置 {planet_name: (x, y)}

# --- 初始化世界 ---
@st.cache_resource # 使用 Streamlit 緩存資源，避免每次運行都重新初始化
def initialize_galaxy():
    """初始化星系、行星和城市數據。"""
    new_galaxy = Galaxy()
    earth = Planet("地球") 
    for cname in ["臺北", "東京", "首爾"]:
        city = City(cname)
        city.citizens = [Citizen(f"{cname}市民#{i+1}") for i in range(30)]
        for c in city.citizens:
            c.city = cname
        earth.cities.append(city)
    new_galaxy.planets.append(earth)

    alien = Planet("賽博星", alien=True)
    for cname in ["艾諾斯", "特朗加"]:
        city = City(cname)
        city.citizens = [Citizen(f"{cname}市民#{i+1}") for i in range(20)]
        for c in city.citizens:
            c.city = cname
        alien.cities.append(city)
    new_galaxy.planets.append(alien)

    # 初始化行星間關係
    for p1 in new_galaxy.planets:
        for p2 in new_galaxy.planets:
            if p1 != p2:
                p1.relations[p2.name] = "neutral" # 初始為中立
    
    # 初始化地圖佈局
    new_galaxy.map_layout = {
        "地球": (0, 0),
        "賽博星": (5, 2)
    }

    return new_galaxy

# 確保每次運行時，如果沒有緩存，則初始化星系
if 'galaxy' not in st.session_state:
    st.session_state.galaxy = initialize_galaxy()
galaxy = st.session_state.galaxy # 從 session_state 獲取星系對象

# --- 模擬核心邏輯函數 ---

def _handle_global_galaxy_events(galaxy, current_year_global_events):
    """處理星系層級的事件，例如新行星的誕生、市民小故事、以及聯邦選舉和政策的應用。"""
    # 隨機生成市民小故事
    if random.random() < 0.15: # 15% 機率生成小故事
        all_active_citizens = []
        for p in galaxy.planets:
            if p.is_alive:
                for c in p.cities:
                    all_active_citizens.extend([citizen for citizen in c.citizens if citizen.alive])
        
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
            story_msg = f"{galaxy.year} 年：✨ {random.choice(story_templates)}"
            current_year_global_events.append(story_msg)

    # 動態誕生新行星
    if random.random() < 0.03 and len(galaxy.planets) < 5: # 3% 機率誕生新行星，最多5個行星
        new_planet_name = f"新星系-{random.randint(100, 999)}"
        new_planet = Planet(new_planet_name, alien=True)
        num_new_cities = random.randint(1, 2)
        for i in range(num_new_cities):
            new_city_name = f"{new_planet_name}市#{i+1}"
            new_city = City(new_city_name)
            new_city.citizens = [Citizen(f"{new_city_name}市民#{j+1}") for j in range(random.randint(10, 25))]
            for c in new_city.citizens:
                c.city = new_city_name 
            new_planet.cities.append(new_city)
        
        # 在新增行星時，更新所有現有行星與新行星的關係
        for p in galaxy.planets:
            p.relations[new_planet.name] = "neutral"
            new_planet.relations[p.name] = "neutral" # 新行星也與舊行星建立關係
        
        galaxy.planets.append(new_planet)
        event_msg = f"{galaxy.year} 年：🔭 發現新行星 **{new_planet_name}**，並建立了 {num_new_cities} 個城市！"
        current_year_global_events.append(event_msg)
        
        # 為新行星分配地圖位置
        existing_coords = set(galaxy.map_layout.values())
        new_x, new_y = 0, 0
        while (new_x, new_y) in existing_coords:
            new_x = random.randint(0, 9)
            new_y = random.randint(0, 4)
        galaxy.map_layout[new_planet.name] = (new_x, new_y)

    # 星系聯邦選舉與政策
    if galaxy.year % 20 == 0 and galaxy.year > 0: # 每20年舉行一次選舉
        active_planets_for_election = [p for p in galaxy.planets if p.is_alive and any(c.citizens for c in p.cities)]
        if len(active_planets_for_election) > 0:
            candidates = []
            for planet_candidate in active_planets_for_election:
                eligible_citizens = [c for city in planet_candidate.cities for c in city.citizens if c.alive]
                if eligible_citizens:
                    representative = random.choice(eligible_citizens)
                    candidates.append(representative)
            
            if candidates:
                galaxy.federation_leader = max(candidates, key=lambda c: c.trust)
                leader_msg = f"{galaxy.year} 年：👑 **{galaxy.federation_leader.name}** 被選為星系聯邦領導人！來自 {galaxy.federation_leader.city} 的市民。"
                current_year_global_events.append(leader_msg)

                # 設置標誌，等待用戶選擇政策
                st.session_state.awaiting_policy_choice = True
                st.session_state.policy_effect = random.uniform(0.01, 0.03)
                st.session_state.policy_duration = random.randint(3, 7)
                st.session_state.temp_global_events = current_year_global_events # 暫存事件，待政策選擇後一併記錄
                st.rerun() # 重新運行以顯示政策選擇 UI
            else:
                current_year_global_events.append(f"{galaxy.year} 年：⚠️ 無法舉行聯邦選舉，因為沒有足夠的活著的市民。")
        else:
            current_year_global_events.append(f"{galaxy.year} 年：⚠️ 無法舉行聯邦選舉，因為沒有足夠的活著的行星。")

    # 應用聯邦政策效果
    if galaxy.active_federation_policy and galaxy.policy_duration_left > 0:
        policy = galaxy.active_federation_policy
        for planet in galaxy.planets:
            if policy["type"] == "提升科技":
                # 聯邦政策提升所有科技領域
                for tech_type in planet.tech_levels.keys():
                    planet.tech_levels[tech_type] = min(1.0, planet.tech_levels[tech_type] + policy["effect"])
            elif policy["type"] == "減少污染":
                planet.pollution = max(0, planet.pollution - policy["effect"])
            elif policy["type"] == "促進貿易":
                pass # 貿易機率在貿易邏輯中提升
            elif policy["type"] == "資源補貼":
                for city in planet.cities:
                    city.resources["糧食"] += policy["effect"] * 50
                    city.resources["能源"] += policy["effect"] * 20
            elif policy["type"] == "健康倡議":
                for city in planet.cities:
                    for citizen in city.citizens:
                        citizen.health = min(1.0, citizen.health + policy["effect"] * 0.5)
        galaxy.policy_duration_left -= 1
        if galaxy.policy_duration_left == 0:
            current_year_global_events.append(f"{galaxy.year} 年：政策「{policy['type']}」已失效。")
            galaxy.active_federation_policy = None

def _update_planet_attributes(planet, current_year_global_events):
    """更新單一行星的屬性，包括科技自然增長、污染積累、防禦等級提升，以及疫情的爆發與消退。"""
    # 攻擊冷卻時間減少
    if planet.attack_cooldown > 0:
        planet.attack_cooldown -= 1

    # 科技自然增長
    for tech_type in planet.tech_levels.keys():
        planet.tech_levels[tech_type] += random.uniform(0.005, 0.015) # 緩慢自然增長
        planet.tech_levels[tech_type] = min(1.0, planet.tech_levels[tech_type])

    # 污染積累 (受環境科技影響)
    pollution_growth = random.uniform(0.01, 0.02)
    pollution_reduction_from_tech = planet.tech_levels["環境"] * 0.015 # 環境科技越高，減少越多
    planet.pollution += (pollution_growth - pollution_reduction_from_tech)
    planet.pollution = max(0, planet.pollution) # 污染不為負

    # 軍事科技提升防禦等級
    planet.defense_level = min(100, int(planet.tech_levels["軍事"] * 100))

    # 新型災難：疫情 (受醫療科技影響)
    if not planet.epidemic_active and random.random() < (0.02 * (1 - planet.tech_levels["醫療"])): # 醫療科技越高，疫情爆發機率越低
        planet.epidemic_active = True
        planet.epidemic_severity = random.uniform(0.1, 0.5) * (1 - planet.tech_levels["醫療"] * 0.5) # 醫療科技降低嚴重性
        epidemic_msg = f"{galaxy.year} 年：🦠 **{planet.name}** 爆發了嚴重的疫情！"
        for city in planet.cities: city.events.append(epidemic_msg)
        current_year_global_events.append(epidemic_msg)
    
    if planet.epidemic_active:
        # 疫情影響：市民健康下降，死亡率增加
        epidemic_impact_on_health = planet.epidemic_severity * 0.1 # 基礎影響
        epidemic_impact_on_health *= (1 - planet.tech_levels["醫療"] * 0.8) # 醫療科技大幅減輕影響
        epidemic_impact_on_health = max(0.01, epidemic_impact_on_health)

        for city in planet.cities:
            for citizen in city.citizens:
                if citizen.alive and random.random() < (epidemic_impact_on_health + 0.01): # 疫情導致健康下降和少量死亡
                    citizen.health -= epidemic_impact_on_health
                    citizen.happiness = max(0.1, citizen.happiness - epidemic_impact_on_health * 0.5) # 疫情影響快樂度
                    if citizen.health < 0.1: # 健康極低可能死亡
                        citizen.alive = False
                        citizen.death_cause = "疫情"
                        city.events.append(f"{galaxy.year} 年：{citizen.name} 在 {city.name} 因疫情而死亡。")
                        current_year_global_events.append(f"{galaxy.year} 年：{citizen.name} 在 {city.name} 因疫情而死亡。")
        
        # 疫情隨時間可能減弱或結束
        planet.epidemic_severity = max(0.0, planet.epidemic_severity - random.uniform(0.05, 0.1))
        if planet.epidemic_severity <= 0.05:
            planet.epidemic_active = False
            epidemic_end_msg = f"{galaxy.year} 年：✅ **{planet.name}** 的疫情已得到控制。"
            for city in planet.cities: city.events.append(epidemic_end_msg)
            current_year_global_events.append(epidemic_end_msg)

def _handle_interstellar_interactions(planet, galaxy, current_year_global_events):
    """處理行星間的複雜互動，包含戰爭邏輯（持續、效果、和平條約）、衝突演變，以及系統觸發的隨機攻擊與反擊。"""
    # 遍歷所有可能的關係，包括還未建立戰爭狀態的
    for other_planet_name, relation_status in list(planet.relations.items()):
        # 確保對方行星仍然存在且存活
        other_planet_obj = next((p for p in galaxy.planets if p.name == other_planet_name and p.is_alive), None)
        if not other_planet_obj:
            # 如果對方行星已滅亡，移除關係並跳過
            if other_planet_name in planet.relations:
                del planet.relations[other_planet_name]
            if other_planet_name in planet.war_duration:
                del planet.war_duration[other_planet_name]
            if other_planet_name in planet.war_with:
                planet.war_with.remove(other_planet_name)
            continue

        # 確保只處理單向關係，避免重複邏輯 (例如 A->B 和 B->A)
        if planet.name > other_planet_name: # 確保只處理一次 (例如只處理 "地球" 對 "賽博星" 的關係，不處理 "賽博星" 對 "地球" 的)
            continue

        # --- 戰爭邏輯 ---
        if other_planet_name in planet.war_with: # 如果正在交戰
            planet.war_duration[other_planet_name] = planet.war_duration.get(other_planet_name, 0) + 1
            other_planet_obj.war_duration[planet.name] = other_planet_obj.war_duration.get(planet.name, 0) + 1

            # 戰爭效果：市民死亡率增加，資源消耗增加，快樂度下降
            war_death_rate_increase = 0.01 # 額外死亡率
            war_resource_drain_per_city = 5 # 每個城市額外消耗資源
            
            for city in planet.cities:
                city.resources["糧食"] -= war_resource_drain_per_city
                city.resources["能源"] -= war_resource_drain_per_city / 2
                for citizen in city.citizens:
                    if citizen.alive:
                        citizen.happiness = max(0.1, citizen.happiness - 0.05) # 戰爭導致快樂度下降
                        if random.random() < war_death_rate_increase:
                            citizen.alive = False
                            citizen.death_cause = "戰爭"
                            city.events.append(f"{galaxy.year} 年：{citizen.name} 在 {city.name} 因與 {other_planet_name} 的戰爭而犧牲。")
                            current_year_global_events.append(f"{galaxy.year} 年：{citizen.name} 在 {city.name} 因戰爭而犧牲。")

            # 和平條約判斷
            war_duration_threshold = 10 # 戰爭至少持續10年
            population_ratio_for_surrender = 0.2 # 如果一方人口少於對方的20%，可能投降

            planet_pop = sum(len(c.citizens) for c in planet.cities)
            other_planet_pop = sum(len(c.citizens) for c in other_planet_obj.cities)

            # 檢查是否滿足和平條件
            peace_conditions_met = False
            if planet.war_duration[other_planet_name] >= war_duration_threshold and random.random() < 0.1: # 戰爭時間夠長，有機會和平
                peace_conditions_met = True
            elif planet_pop < other_planet_pop * population_ratio_for_surrender and random.random() < 0.2: # 我方人口太少，可能投降
                peace_conditions_met = True
            elif other_planet_pop < planet_pop * population_ratio_for_surrender and random.random() < 0.2: # 對方人口太少，可能投降
                peace_conditions_met = True
            
            if peace_conditions_met:
                # 結束戰爭
                planet.war_with.remove(other_planet_name)
                other_planet_obj.war_with.remove(planet.name)
                del planet.war_duration[other_planet_name]
                del other_planet_obj.war_duration[planet.name]

                # 設置為中立關係
                planet.relations[other_planet_name] = "neutral"
                other_planet_obj.relations[planet.name] = "neutral"
                
                peace_msg = f"{galaxy.year} 年：🕊️ **{planet.name}** 與 **{other_planet_obj.name}** 簽署和平條約，結束了戰爭！"
                current_year_global_events.append(peace_msg)
                for city in planet.cities: city.events.append(peace_msg)
                for city in other_planet_obj.cities: city.events.append(peace_msg)
            
            # 如果正在戰爭，跳過下面的衝突觸發和關係變化，因為戰爭狀態優先
            return 

        # --- 非戰爭狀態下的衝突觸發與關係演變 ---
        base_conflict_chance = 0.05
        if planet.alien or other_planet_obj.alien:
            base_conflict_chance *= 1.2

        conflict_chance = max(0.01, base_conflict_chance * (1 - planet.tech_levels["軍事"])) # 軍事科技降低衝突機率

        if relation_status == "friendly":
            conflict_chance *= 0.5 # 友好關係大幅降低衝突機率
        elif relation_status == "hostile":
            conflict_chance *= 2.0 # 敵對關係大幅提高衝突機率

        if random.random() < conflict_chance:
            planet.conflict_level = min(1.0, planet.conflict_level + random.uniform(0.05, 0.15))
            other_planet_obj.conflict_level = min(1.0, other_planet_obj.conflict_level + random.uniform(0.05, 0.15)) # 雙方衝突等級都提升
            
            conflict_msg = f"{galaxy.year} 年：⚠️ {planet.name} 與 {other_planet_obj.name} 的衝突等級提升至 {planet.conflict_level:.2f}！"
            for city in planet.cities:
                city.events.append(conflict_msg)
            for city in other_planet_obj.cities:
                city.events.append(conflict_msg)
            current_year_global_events.append(conflict_msg)

            # 衝突會導致關係惡化
            if relation_status != "hostile": # 如果還不是敵對，則轉為敵對
                planet.relations[other_planet_name] = "hostile"
                other_planet_obj.relations[planet.name] = "hostile"
                current_year_global_events.append(f"{galaxy.year} 年：💥 {planet.name} 與 {other_planet_obj.name} 的關係惡化為敵對！")
            
            # 如果衝突等級非常高且關係敵對，則宣戰
            if planet.conflict_level > 0.7 and other_planet_obj.conflict_level > 0.7 and planet.relations[other_planet_name] == "hostile":
                planet.war_with.add(other_planet_name)
                other_planet_obj.war_with.add(planet.name)
                planet.war_duration[other_planet_name] = 0
                other_planet_obj.war_duration[planet.name] = 0
                war_declare_msg = f"{galaxy.year} 年：⚔️ **{planet.name}** 向 **{other_planet_obj.name}** 宣戰！星際戰爭爆發！"
                current_year_global_events.append(war_declare_msg)
                for city in planet.cities: city.events.append(war_declare_msg)
                for city in other_planet_obj.cities: city.events.append(war_declare_msg)
        else:
            # 沒有衝突時，衝突等級會自然下降
            planet.conflict_level = max(0.0, planet.conflict_level - random.uniform(0.01, 0.05))
            other_planet_obj.conflict_level = max(0.0, other_planet_obj.conflict_level - random.uniform(0.01, 0.05))

            # 如果沒有衝突，關係可能改善
            if relation_status == "hostile" and random.random() < 0.02:
                planet.relations[other_planet_name] = "neutral"
                other_planet_obj.relations[planet.name] = "neutral"
                current_year_global_events.append(f"{galaxy.year} 年：🤝 {planet.name} 與 {other_planet_obj.name} 的關係從敵對轉為中立。")
            elif relation_status == "neutral" and random.random() < 0.01:
                planet.relations[other_planet_name] = "friendly"
                other_planet_obj.relations[planet.name] = "friendly"
                current_year_global_events.append(f"{galaxy.year} 年：✨ {planet.name} 與 {other_planet_obj.name} 的關係從中立轉為友好。")

    # 隨機攻擊邏輯 (現在由系統隨機觸發，而不是外星生物襲擊)
    active_planets = [p for p in galaxy.planets if p.is_alive] # 從 galaxy 獲取最新的活動行星列表
    if random.random() < 0.02 and len(active_planets) > 1: # 2% 機率發生隨機攻擊
        possible_targets = [p for p in active_planets if p.name != planet.name and p.name not in planet.allies]
        if possible_targets:
            target_planet_for_random_attack = random.choice(possible_targets)
            
            # 檢查是否已經在戰爭中，如果是，則不發動新的隨機攻擊
            if target_planet_for_random_attack.name in planet.war_with:
                return

            attack_strength = random.uniform(0.05, 0.2) # 隨機攻擊強度
            
            # 考慮防禦方的防禦等級和護盾
            total_defense_bonus = target_planet_for_random_attack.defense_level * 0.005 # 防禦等級提供減傷
            if target_planet_for_random_attack.shield_active:
                total_defense_bonus += 0.5 # 護盾提供大幅減傷
                target_planet_for_random_attack.shield_active = False # 護盾一次性使用

            # 盟友支援
            alliance_defense_bonus = 0
            for ally_name in target_planet_for_random_attack.allies:
                ally_obj = next((p for p in galaxy.planets if p.name == ally_name and p.is_alive), None)
                if ally_obj:
                    alliance_defense_bonus += 0.1 # 每個盟友提供額外減傷
            total_defense_bonus += alliance_defense_bonus

            actual_attack_strength = max(0.01, attack_strength * (1 - total_defense_bonus))

            # 造成人口和資源損失
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

            random_attack_msg = f"{galaxy.year} 年：🚨 **{planet.name}** 隨機攻擊了 **{target_planet_for_random_attack.name}**！"
            if population_loss > 0:
                random_attack_msg += f" 目標損失約 {population_loss} 人口。"
            current_year_global_events.append(random_attack_msg)
            
            # 被攻擊方有小機率反擊
            if random.random() < (0.1 + target_planet_for_random_attack.tech_levels["軍事"] * 0.1 + alliance_defense_bonus * 0.5): # 科技和盟友會增加反擊機率
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
                counter_attack_msg = f"{galaxy.year} 年：🛡️ **{target_planet_for_random_attack.name}** 成功反擊了 **{planet.name}**！"
                if counter_attack_pop_loss > 0:
                    counter_attack_msg += f" 攻擊方損失約 {counter_attack_pop_loss} 人口。"
                current_year_global_events.append(counter_attack_msg)

    # 衝突對市民的影響 (在戰爭邏輯中已處理，這裡只處理非戰爭衝突)
    # Note: This loop might be redundant if all conflict/war deaths are handled within the above blocks.
    # Keeping it for now for any potential non-war conflict impact not covered.
    for city in planet.cities:
        for citizen in city.citizens:
            if citizen.alive and random.random() < (planet.conflict_level * 0.002): # 輕微的衝突死亡率
                citizen.alive = False
                citizen.death_cause = "衝突"
                city.events.append(f"{galaxy.year} 年：{citizen.name} 在 {city.name} 因星際衝突而犧牲。")
                current_year_global_events.append(f"{galaxy.year} 年：{citizen.name} 在 {city.name} 因星際衝突而犧牲。")

def _update_city_attributes(city, planet, galaxy, current_year_global_events):
    """更新單一城市的屬性，涵蓋資源消耗與生產（受產業專精和生產科技影響）、盟友間的貿易、資源短缺/繁榮事件、合作經濟發展、群眾運動與叛亂，以及政體演變。"""
    # 城市級別的變化 (受政體影響)
    resource_drain_multiplier = 1.0
    if city.government_type == "專制":
        resource_drain_multiplier = 0.8 # 專制可能更有效率
    elif city.government_type == "民主制":
        resource_drain_multiplier = 1.2 # 民主制可能效率較低（但信任度高）

    # 資源消耗 (受人口影響)
    population_consumption = len(city.citizens) * 0.5 # 每人每月消耗0.5單位糧食/能源
    city.resources["糧食"] -= population_consumption * resource_drain_multiplier
    city.resources["能源"] -= (population_consumption / 2) * resource_drain_multiplier

    # 資源生產 (受產業專精和生產科技影響)
    production_bonus = planet.tech_levels["生產"] * 0.1 # 生產科技提供基礎加成
    if city.specialization == "農業":
        city.resources["糧食"] += 20 * (1 + production_bonus)
    elif city.specialization == "工業":
        city.resources["能源"] += 15 * (1 + production_bonus)
    elif city.specialization == "科技":
        # 科技城市可能直接貢獻稅收或科技點
        city.resources["稅收"] += 10 * (1 + production_bonus)
        planet.tech_levels["生產"] = min(1.0, planet.tech_levels["生產"] + 0.005) # 科技城市額外提升生產科技
    elif city.specialization == "服務":
        city.resources["稅收"] += 15 * (1 + production_bonus)
        for citizen in city.citizens: # 服務業提升市民快樂度
            if citizen.alive: citizen.happiness = min(1.0, citizen.happiness + 0.002)
    elif city.specialization == "軍事":
        city.resources["能源"] += 10 * (1 + production_bonus) # 軍事基地消耗能源也生產能源
        planet.tech_levels["軍事"] = min(1.0, planet.tech_levels["軍事"] + 0.005) # 軍事城市額外提升軍事科技

    # 貿易 (簡化為盟友間資源平衡)
    for ally_name in planet.allies:
        ally_planet = next((p for p in galaxy.planets if p.name == ally_name and p.is_alive), None)
        if ally_planet:
            for ally_city in ally_planet.cities:
                # 如果我方城市糧食過剩，盟友城市糧食短缺，則進行貿易
                if city.resources["糧食"] > 150 and ally_city.resources["糧食"] < 50:
                    trade_amount = min(20, city.resources["糧食"] - 150, 50 - ally_city.resources["糧食"])
                    if trade_amount > 0:
                        city.resources["糧食"] -= trade_amount
                        ally_city.resources["糧食"] += trade_amount
                        city.resources["稅收"] += trade_amount # 賣方賺稅收
                        ally_city.resources["稅收"] -= trade_amount * 0.5 # 買方花費稅收
                        current_year_global_events.append(f"{galaxy.year} 年：🤝 {city.name} 與 {ally_city.name} 進行了糧食貿易。")
                # 能源貿易
                if city.resources["能源"] > 100 and ally_city.resources["能源"] < 30:
                    trade_amount = min(10, city.resources["能源"] - 100, 30 - ally_city.resources["能源"])
                    if trade_amount > 0:
                        city.resources["能源"] -= trade_amount
                        ally_city.resources["能源"] += trade_amount
                        city.resources["稅收"] += trade_amount # 賣方賺稅收
                        ally_city.resources["稅收"] -= trade_amount * 0.5 # 買方花費稅收
                        current_year_global_events.append(f"{galaxy.year} 年：🤝 {city.name} 與 {ally_city.name} 進行了能源貿易。")

    # 資源短缺事件 (饑荒)
    if city.resources["糧食"] < 50 or city.resources["能源"] < 30:
        city.resource_shortage_years += 1
        if city.resource_shortage_years >= 3: # 連續3年短缺觸發饑荒
            famine_msg = f"{galaxy.year} 年：🚨 **{city.name}** 爆發了饑荒！市民健康和快樂度大幅下降！"
            city.events.append(famine_msg)
            current_year_global_events.append(famine_msg)
            for citizen in city.citizens:
                if citizen.alive:
                    citizen.health = max(0.1, citizen.health - random.uniform(0.05, 0.15))
                    citizen.happiness = max(0.1, citizen.happiness - random.uniform(0.1, 0.2))
                    if random.random() < 0.02: # 饑荒導致額外死亡
                        citizen.alive = False
                        citizen.death_cause = "饑荒"
            city.resources["糧食"] = max(0, city.resources["糧食"] - 20) # 繼續消耗
            city.resources["能源"] = max(0, city.resources["能源"] - 10)
    else:
        city.resource_shortage_years = 0 # 短缺結束，重置計數器

    # 資源繁榮事件
    if city.resources["糧食"] > 200 and city.resources["能源"] > 150 and planet.tech_levels["生產"] > 0.7 and random.random() < 0.01:
        boom_msg = f"{galaxy.year} 年：💰 **{city.name}** 迎來了資源繁榮！市民財富和快樂度提升！"
        city.events.append(boom_msg)
        current_year_global_events.append(boom_msg)
        for citizen in city.citizens:
            if citizen.alive:
                citizen.wealth += random.uniform(10, 30)
                citizen.happiness = min(1.0, citizen.happiness + random.uniform(0.05, 0.1))

    # 群眾運動 (受信任度和快樂度影響)
    alive_citizens_for_stats = [c for c in city.citizens if c.alive]
    avg_trust = sum(c.trust for c in alive_citizens_for_stats) / max(1, len(alive_citizens_for_stats)) if alive_citizens_for_stats else 0
    avg_happiness = sum(c.happiness for c in alive_citizens_for_stats) / max(1, len(alive_citizens_for_stats)) if alive_citizens_for_stats else 0
    
    ideology_counts = {}
    for c in alive_citizens_for_stats:
        ideology_counts[c.ideology] = ideology_counts.get(c.ideology, 0) + 1
    
    dominant_ideology = None
    if ideology_counts:
        dominant_ideology = max(ideology_counts, key=ideology_counts.get)
        dominant_percentage = ideology_counts[dominant_ideology] / len(alive_citizens_for_stats)

    # 觸發群眾運動的條件：低信任度 AND 低快樂度 AND 某個思想派別佔比高 AND 隨機機率
    if avg_trust < 0.5 and avg_happiness < 0.5 and dominant_ideology and dominant_percentage > 0.6 and random.random() < 0.05:
        if not city.mass_movement_active:
            city.mass_movement_active = True
            movement_msg = f"{galaxy.year} 年：📢 {city.name} 爆發了以 **{dominant_ideology}** 為主的群眾運動！"
            city.events.append(movement_msg)
            current_year_global_events.append(movement_msg)
            city.resources["糧食"] -= random.randint(5, 15)
            city.resources["能源"] -= random.randint(5, 15)
            for c in alive_citizens_for_stats:
                c.trust = max(0.1, c.trust - 0.1)
                c.happiness = max(0.1, c.happiness - 0.1)
                if random.random() < 0.005:
                    if random.random() < 0.5:
                        c.alive = False
                        c.death_cause = "群眾運動"
                    else:
                        other_cities = [ct for p in galaxy.planets for ct in p.cities if ct.name != city.name and p.is_alive]
                        if other_cities:
                            target_city = random.choice(other_cities)
                            c.city = target_city.name
                            target_city.citizens.append(c)
                            city.emigration_count += 1
                            target_city.immigration_count += 1
                            event_msg = f"{galaxy.year} 年：{c.name} 從 {city.name} 逃離群眾運動，移居至 {target_city.name}。"
                            target_city.events.append(event_msg)
                            current_year_global_events.append(event_msg)
        
        # 叛亂事件 (群眾運動長期不平息)
        if city.mass_movement_active and (avg_trust < 0.3 or avg_happiness < 0.3) and random.random() < 0.02:
            rebellion_msg = f"{galaxy.year} 年：🔥 **{city.name}** 爆發了大規模叛亂！政體可能改變！"
            city.events.append(rebellion_msg)
            current_year_global_events.append(rebellion_msg)
            # 叛亂導致人口和資源大量損失
            rebellion_death_count = int(len(alive_citizens_for_stats) * random.uniform(0.05, 0.15))
            for _ in range(rebellion_death_count):
                if alive_citizens_for_stats:
                    victim = random.choice(alive_citizens_for_stats)
                    victim.alive = False
                    victim.death_cause = "叛亂"
                    city.death_count += 1
                    city.graveyard.append((victim.name, victim.age, victim.ideology, victim.death_cause))
                    alive_citizens_for_stats.remove(victim) # 從活著的市民列表中移除
            
            city.resources["糧食"] = max(0, city.resources["糧食"] - random.uniform(50, 100))
            city.resources["能源"] = max(0, city.resources["能源"] - random.uniform(30, 70))

            # 政體可能改變
            if city.government_type == "專制":
                city.government_type = random.choice(["民主制", "共和制"])
            elif city.government_type == "民主制":
                city.government_type = "專制" # 民主制動盪可能走向專制
            elif city.government_type == "共和制":
                city.government_type = random.choice(["專制", "民主制"])
            
            current_year_global_events.append(f"{galaxy.year} 年：政體在叛亂中變為 **{city.government_type}**！")
            city.mass_movement_active = False # 叛亂結束，運動平息

    elif city.mass_movement_active and avg_trust > 0.6 and avg_happiness > 0.6:
        city.mass_movement_active = False
        movement_msg = f"{galaxy.year} 年：✅ {city.name} 的群眾運動逐漸平息。"
        city.events.append(movement_msg)
        current_year_global_events.append(movement_msg)

    # 政體演化
    if random.random() < 0.01: # 1% 機率觸發政體演化
        if city.government_type == "民主制":
            if avg_trust < 0.4 and city.mass_movement_active: # 民主制下信任度極低且有運動，可能轉為專制
                city.government_type = "專制"
                event_msg = f"{galaxy.year} 年：🚨 {city.name} 的民主制因動盪而演變為專制！"
                city.events.append(event_msg)
                current_year_global_events.append(event_msg)
            elif avg_trust > 0.8: # 民主制下信任度極高，可能更穩定
                pass # 暫時不演變，保持穩定
        elif city.government_type == "專制":
            if avg_trust > 0.7: # 專制下信任度高，可能轉為共和制
                city.government_type = "共和制"
                event_msg = f"{galaxy.year} 年：✨ {city.name} 的專制因民心所向而演變為共和制！"
                city.events.append(event_msg)
                current_year_global_events.append(event_msg)
            elif avg_trust < 0.3 and city.mass_movement_active: # 專制下信任度極低且有運動，可能轉為民主制
                city.government_type = "民主制"
                event_msg = f"{galaxy.year} 年：✊ {city.name} 的專制在群眾運動中演變為民主制！"
                city.events.append(event_msg)
                current_year_global_events.append(event_msg)
        elif city.government_type == "共和制":
            if avg_trust < 0.5: # 共和制下信任度低，可能退化為專制或民主
                city.government_type = random.choice(["專制", "民主制"])
                event_msg = f"{galaxy.year} 年：📉 {city.name} 的共和制因信任度下降而退化為 {city.government_type}！"
                city.events.append(event_msg)
                current_year_global_events.append(event_msg)

def _handle_citizen_lifecycle(city, planet, galaxy, current_year_global_events):
    """管理城市內市民的生命週期，包括年齡增長、財富與稅收、教育提升、污染對健康的影響、生老病死、結婚生子以及移民行為。"""
    next_citizens_list = []
    dead_this_year = []
    immigrated_out_this_year = []
    newborns_this_year = []
    
    # 處理結婚
    unmarried_citizens = [c for c in city.citizens if c.alive and c.partner is None and 20 <= c.age <= 50]
    random.shuffle(unmarried_citizens)
    
    for i in range(0, len(unmarried_citizens) - 1, 2):
        citizen1 = unmarried_citizens[i]
        citizen2 = unmarried_citizens[i+1]
        if random.random() < 0.05:
            citizen1.partner = citizen2
            citizen2.partner = citizen1
            marriage_msg = f"{galaxy.year} 年：💖 {citizen1.name} 與 {citizen2.name} 在 {city.name} 喜結連理！"
            city.events.append(marriage_msg)
            current_year_global_events.append(marriage_msg)

    # 階段 1: 判斷市民的狀態變化
    for citizen in list(city.citizens): # Iterate on a copy as elements might be removed
        if not citizen.alive:
            continue

        citizen.age += 1
        
        # 市民財富與稅收
        profession_income = {
            "農民": 10, "工人": 15, "科學家": 25, "商人": 30, "無業": 5,
            "醫生": 40, "藝術家": 12, "工程師": 35, "教師": 20, "服務員": 10,
            "小偷": 20, "黑幫成員": 25, "詐騙犯": 30, "毒販": 45
        }
        living_cost = 8 # 基本生活開銷
        citizen.wealth += profession_income.get(citizen.profession, 0) - living_cost
        citizen.wealth = max(0, citizen.wealth) # 財富不為負

        # 犯罪職業的額外風險 (導致財富波動或健康/信任/快樂度下降)
        if citizen.profession in ["小偷", "黑幫成員", "詐騙犯", "毒販"]:
            if random.random() < 0.03: # 3% 機率發生負面事件 (被抓或受傷)
                citizen.wealth = max(0, citizen.wealth - random.uniform(20, 50)) # 財富損失
                citizen.health = max(0.1, citizen.health - random.uniform(0.1, 0.2)) # 健康受損
                citizen.trust = max(0.1, citizen.trust - random.uniform(0.05, 0.1)) # 信任度下降
                citizen.happiness = max(0.1, citizen.happiness - random.uniform(0.05, 0.1)) # 快樂度下降
                event_msg = f"{galaxy.year} 年：🚨 {citizen.name} ({citizen.profession}) 在 {city.name} 遭遇了麻煩！"
                city.events.append(event_msg)
                current_year_global_events.append(event_msg)

        # 稅收基於財富和政體
        tax_rate = 0.05 # 基礎稅率
        if city.government_type == "專制":
            tax_rate = 0.08 # 專制稅率可能更高
        elif city.government_type == "民主制":
            tax_rate = 0.03 # 民主制稅率可能更低
        city.resources["稅收"] += int(citizen.wealth * tax_rate)


        # 教育水平提升
        if citizen.education_level < 3 and random.random() < 0.01: # 1% 機率提升教育水平
            citizen.education_level += 1
            # 教育提升可能影響職業
            if citizen.education_level == 3: # 高等教育
                eligible_high_professions = ["科學家", "醫生", "工程師"]
                if citizen.profession not in eligible_high_professions and random.random() < 0.3: # 30% 機率轉為高階職業
                    citizen.profession = random.choice(eligible_high_professions)
                    event_msg = f"{galaxy.year} 年：🎓 {citizen.name} 晉升為 {citizen.profession}！"
                    city.events.append(event_msg)
                    current_year_global_events.append(event_msg)
            elif citizen.education_level == 2: # 中等教育
                eligible_mid_professions = ["教師", "商人"]
                if citizen.profession not in eligible_mid_professions and random.random() < 0.1: # 10% 機率轉為中階職業
                    citizen.profession = random.choice(eligible_mid_professions)
                    event_msg = f"{galaxy.year} 年：📚 {citizen.name} 轉職為 {citizen.profession}！"
                    city.events.append(event_msg)
                    current_year_global_events.append(event_msg)


        # 污染對健康的影響 (受環境科技影響)
        pollution_health_impact = 0.3
        pollution_health_impact *= (1 - planet.tech_levels["環境"] * 0.5) # 環境科技降低影響
        pollution_health_impact = max(0.05, pollution_health_impact)

        if planet.pollution > 1.0 and random.random() < 0.03:
            citizen.health -= pollution_health_impact
            citizen.happiness = max(0.1, citizen.happiness - pollution_health_impact * 0.5) # 污染影響快樂度
            event_msg = f"{galaxy.year} 年：{citizen.name} 在 {city.name} 因污染而健康惡化。"
            city.events.append(event_msg)
            current_year_global_events.append(event_msg)
            if citizen.health < 0:
                citizen.alive = False
                citizen.death_cause = "疾病/污染"
                event_msg = f"{galaxy.year} 年：{citizen.name} 在 {city.name} 因健康惡化而死亡。"
                city.events.append(event_msg)
                current_year_global_events.append(event_msg)

        # 死亡判斷
        if not citizen.alive:
            dead_this_year.append(citizen)
        elif citizen.age > 80 and random.random() < 0.1:
            citizen.alive = False
            citizen.death_cause = "壽終正寢"
            dead_this_year.append(citizen)
            event_msg = f"{galaxy.year} 年：{citizen.name} 在 {city.name} 壽終正寢。"
            city.events.append(event_msg)
            current_year_global_events.append(event_msg)
        elif random.random() < 0.01:
            citizen.alive = False
            citizen.death_cause = "意外"
            dead_this_year.append(citizen)
            event_msg = f"{galaxy.year} 年：{citizen.name} 在 {city.name} 突然死亡。"
            city.events.append(event_msg)
            current_year_global_events.append(event_msg)

        # 如果市民死亡，處理其配偶關係
        if not citizen.alive:
            city.death_count += 1
            city.graveyard.append((citizen.name, citizen.age, citizen.ideology, citizen.death_cause))
            if citizen.partner and citizen.partner.alive:
                citizen.partner.partner = None
            continue

        # 出生判斷 (現在與配偶關聯，受快樂度影響)
        birth_chance = 0.02 * (1 + citizen.happiness * 0.5) # 快樂度越高，出生機率越高
        if citizen.partner and citizen.partner.alive and 20 <= citizen.age <= 40 and random.random() < birth_chance:
            # 傳遞父母屬性給新生兒 (子女家族傳承)
            baby = Citizen(
                f"{citizen.name}-子{random.randint(1,100)}",
                parent1_ideology=citizen.ideology,
                parent2_ideology=citizen.partner.ideology,
                parent1_trust=citizen.trust,
                parent2_trust=citizen.partner.trust,
                parent1_emotion=citizen.happiness, # 傳遞快樂度
                parent2_emotion=citizen.partner.happiness # 傳遞快樂度
            )
            baby.city = city.name
            newborns_this_year.append(baby)
            city.birth_count += 1
            event_msg = f"{galaxy.year} 年：{citizen.name} 與 {citizen.partner.name} 在 {city.name} 生下一名子女。"
            city.events.append(event_msg)
            current_year_global_events.append(event_msg)

        # 移民判斷 (受財富和快樂度影響)
        # 財富和快樂度越低，移民意願越高；財富和快樂度越高，越傾向留在原地或移民到更富裕的城市
        immigration_chance = 0.02
        if citizen.wealth < 100: # 財富低，移民機率增加
            immigration_chance *= 1.5
        elif citizen.wealth > 300: # 財富高，移民機率降低
            immigration_chance *= 0.5
        
        if citizen.happiness < 0.4: # 快樂度低，移民機率增加
            immigration_chance *= 1.5
        elif citizen.happiness > 0.8: # 快樂度高，移民機率降低
            immigration_chance *= 0.5

        if random.random() < immigration_chance:
            other_cities = [ct for p in galaxy.planets for ct in p.cities if ct.name != city.name and p.is_alive]
            if other_cities:
                # 傾向移民到人口更多、資源更豐富、快樂度更高的城市
                # 綜合偏好邏輯：優先選擇人口多、糧食多、平均快樂度高的城市
                sorted_cities = sorted(other_cities, key=lambda c: (len(c.citizens), c.resources["糧食"], sum(cit.happiness for cit in c.citizens if cit.alive) / max(1, len([cit for cit in c.citizens if cit.alive]))), reverse=True)
                if sorted_cities:
                    target_city = sorted_cities[0] # 選擇最好的城市
                else:
                    target_city = random.choice(other_cities) # fallback to random

                citizen.city = target_city.name
                target_city.citizens.append(citizen)
                immigrated_out_this_year.append(citizen)
                city.emigration_count += 1
                target_city.immigration_count += 1
                event_msg = f"{galaxy.year} 年：{citizen.name} 從 {city.name} 移居至 {target_city.name}。"
                target_city.events.append(event_msg)
                current_year_global_events.append(event_msg)
                # 如果有配偶，配偶也一起移民
                if citizen.partner and citizen.partner.alive and citizen.partner in city.citizens and citizen.partner not in immigrated_out_this_year:
                    partner = citizen.partner
                    partner.city = target_city.name
                    target_city.citizens.append(partner)
                    immigrated_out_this_year.append(partner)
                    city.emigration_count += 1
                    target_city.immigration_count += 1
                    event_msg = f"{galaxy.year} 年：{citizen.name} 的配偶 {partner.name} 也隨其移居至 {target_city.name}。"
                    target_city.events.append(event_msg)
                    current_year_global_events.append(event_msg)
                continue
        
        # 如果市民沒有死亡也沒有遷出，則加入下一年的市民列表
        next_citizens_list.append(citizen)

    # 階段 2: 更新市民列表
    # 從原列表中移除已死亡或已移民的市民
    city.citizens = [c for c in next_citizens_list if c not in immigrated_out_this_year] + newborns_this_year

    # 計算平均健康、信任和快樂度 (只針對活著的市民)
    alive_citizens_for_stats = [c for c in city.citizens if c.alive]
    avg_health = sum(c.health for c in alive_citizens_for_stats) / max(1, len(alive_citizens_for_stats)) if alive_citizens_for_stats else 0
    avg_trust = sum(c.trust for c in alive_citizens_for_stats) / max(1, len(alive_citizens_for_stats)) if alive_citizens_for_stats else 0
    avg_happiness = sum(c.happiness for c in alive_citizens_for_stats) / max(1, len(alive_citizens_for_stats)) if alive_citizens_for_stats else 0
    city.history.append((galaxy.year, avg_health, avg_trust, avg_happiness))


def simulate_year(galaxy):
    """模擬一年的世界變化。"""
    galaxy.year += 1
    current_year_global_events = [] # 儲存本年度所有事件，用於日報

    # 重置每年的計數器和事件
    for planet in galaxy.planets:
        for city in planet.cities:
            city.birth_count = 0
            city.death_count = 0
            city.immigration_count = 0
            city.emigration_count = 0
            city.events = [] # 清空年度事件，只保留當前年的事件顯示

    _handle_global_galaxy_events(galaxy, current_year_global_events)

    active_planets = [p for p in galaxy.planets if p.is_alive]
    for planet in active_planets:
        _update_planet_attributes(planet, current_year_global_events)
        _handle_interstellar_interactions(planet, galaxy, current_year_global_events) # Pass galaxy to access other planets

        for city in planet.cities:
            _update_city_attributes(city, planet, galaxy, current_year_global_events)
            _handle_citizen_lifecycle(city, planet, galaxy, current_year_global_events)
        
        # 行星滅亡判斷
        if all(len(c.citizens) == 0 for c in planet.cities):
            planet.is_alive = False
            event_msg = f"{galaxy.year} 年：💥 行星 **{planet.name}** 上的所有城市都已滅亡，行星從星系中消失了！"
            current_year_global_events.append(event_msg)

    # 清理已滅亡的行星
    galaxy.planets = [p for p in galaxy.planets if p.is_alive]

    # 將本年度的全球事件記錄到日報日誌中
    if current_year_global_events:
        galaxy.global_events_log.append({
            "year": galaxy.year,
            "events": current_year_global_events
        })

# --- Streamlit UI 控制元件 ---
st.title("🌐 CitySim 世界模擬器 Pro")
st.markdown("---") # 分隔線

# 設置側邊欄用於控制模擬參數
with st.sidebar:
    st.header("⚙️ 模擬設定") 
    years_per_step = st.slider("每個步驟模擬年數", 1, 100, 10, help="選擇每次點擊按鈕模擬的年數")
    simulate_step_button = st.button("執行模擬步驟") # 新增模擬步驟按鈕
    st.markdown("---")
    st.header("🏙️ 城市選擇") 
    # 確保只有活著的行星上的城市才可被選擇
    city_options = [city.name for p in galaxy.planets if p.is_alive for city in p.cities]
    
    # 處理 selected_city 的邏輯，使其更健壯
    current_selected_index = 0
    if 'selected_city' in st.session_state and st.session_state.selected_city in city_options:
        current_selected_index = city_options.index(st.session_state.selected_city)
    elif city_options: # 如果之前選的城市沒了，但還有其他城市，預設選第一個
        st.session_state.selected_city = city_options[0]
    else: # 如果沒有任何城市了
        st.info("目前沒有城市可供選擇。")
        selected_city = None # 確保 selected_city 是 None 如果沒有選項
        
    if city_options: # 只有當有城市選項時才顯示 selectbox
        selected_city = st.selectbox(
            "選擇城市以檢視狀態：",
            city_options,
            help="選擇一個城市來查看其詳細統計數據和事件",
            index=current_selected_index,
            key="selected_city" # 使用 key 來確保 Streamlit 正確追蹤狀態
        )
    else:
        selected_city = None # 確保 selected_city 是 None 如果沒有選項


    st.markdown("---")
    if st.button("重置模擬", help="將模擬器重置為初始狀態"):
        st.session_state.galaxy = initialize_galaxy()
        st.rerun() # 重啟 Streamlit 應用以應用重置

st.markdown(f"### ⏳ 當前年份：{galaxy.year}")

# --- 政策選擇 UI (獨立於模擬迴圈) ---
# 只有在選舉年且沒有活躍政策時才顯示政策選擇
if 'awaiting_policy_choice' not in st.session_state:
    st.session_state.awaiting_policy_choice = False

if st.session_state.awaiting_policy_choice:
    st.markdown("---")
    st.header("📜 聯邦政策選擇")
    st.info(f"聯邦領導人 **{galaxy.federation_leader.name}** (來自 {galaxy.federation_leader.city}) 已選出！請選擇一項新政策。")
    
    # 計算並顯示星系平均科技、污染、衝突等級
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
        policy_msg = f"{galaxy.year} 年：📜 聯邦領導人 **{galaxy.federation_leader.name}** 頒布了「**{actual_policy_type}**」政策，將持續 {galaxy.policy_duration_left} 年！"
        current_year_global_events.append(policy_msg)
        galaxy.global_events_log.append({"year": galaxy.year, "events": current_year_global_events}) # 記錄政策事件

        st.session_state.awaiting_policy_choice = False
        st.session_state.temp_global_events = [] # 清空臨時事件
        st.rerun() # 重新運行以顯示政策選擇 UI

# 如果正在等待政策選擇，則停止模擬迴圈的執行
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
        # 選擇攻擊方
        attacker_planet_name = st.selectbox(
            "選擇攻擊方行星：",
            [p.name for p in active_planets_for_attack],
            key="attacker_planet_select"
        )
        attacker_planet = next((p for p in galaxy.planets if p.name == attacker_planet_name), None)

        # 選擇目標方 (不能是自己，不能是盟友)
        target_options = [p.name for p in active_planets_for_attack if p.name != attacker_planet_name and p.name not in attacker_planet.allies]
        if not target_options:
            st.warning(f"目前沒有可攻擊的行星（不能攻擊自己或盟友）。")
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
                    ["精確打擊 (較低傷害，較低戰爭機率)", "全面開戰 (較高傷害，較高戰爭機率)"],
                    key="attack_type_radio"
                )
                
                attack_cost = 50 # 基礎攻擊成本
                if "全面開戰" in attack_type:
                    attack_cost = 100

                if st.button(f"發動攻擊 ({attack_cost} 稅收)"):
                    if attacker_planet.cities and attacker_planet.cities[0].resources["稅收"] >= attack_cost:
                        # 扣除攻擊方資源
                        attacker_planet.cities[0].resources["稅收"] -= attack_cost

                        # 提升目標衝突等級
                        target_planet.conflict_level = min(1.0, target_planet.conflict_level + random.uniform(0.1, 0.3))
                        
                        # 關係惡化為敵對
                        attacker_planet.relations[target_planet.name] = "hostile"
                        target_planet.relations[attacker_planet.name] = "hostile"

                        # 如果攻擊方是盟友，則聯盟破裂並懲罰
                        if target_planet.name in attacker_planet.allies:
                            attacker_planet.allies.remove(target_planet.name)
                            target_planet.allies.remove(attacker_planet.name)
                            for city in attacker_planet.cities:
                                for citizen in city.citizens:
                                    citizen.trust = max(0.1, citizen.trust - 0.2) # 信任度大幅下降
                                    citizen.happiness = max(0.1, citizen.happiness - 0.2) # 快樂度大幅下降
                            alliance_break_msg = f"{galaxy.year} 年：🚨 **{attacker_planet.name}** 攻擊盟友 **{target_planet.name}**，聯盟破裂，信任度與快樂度大幅下降！"
                            galaxy.global_events_log.append({"year": galaxy.year, "events": [alliance_break_msg]})
                            st.warning(alliance_break_msg)

                        # 傷害計算
                        damage_multiplier = 0.1 # 基礎傷害乘數
                        war_chance = 0.2 # 基礎戰爭機率
                        if "全面開戰" in attack_type:
                            damage_multiplier = 0.2
                            war_chance = 0.5

                        # 考慮防禦方的防禦等級和護盾
                        total_defense_bonus = target_planet.defense_level * 0.005 # 防禦等級提供減傷
                        if target_planet.shield_active:
                            total_defense_bonus += 0.5 # 護盾提供大幅減傷
                            target_planet.shield_active = False # 護盾一次性使用

                        actual_damage_multiplier = max(0.01, damage_multiplier * (1 - total_defense_bonus))

                        # 造成人口和資源損失
                        population_loss = int(sum(len(c.citizens) for c in target_planet.cities) * actual_damage_multiplier)
                        resource_loss = int(sum(c.resources["糧食"] for c in target_planet.cities) * actual_damage_multiplier * 0.5)

                        for city in target_planet.cities:
                            for _ in range(int(population_loss / max(1, len(target_planet.cities)))): # 確保除數不為0
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
                        
                        galaxy.global_events_log.append({"year": galaxy.year, "events": [attack_msg]})
                        st.success(attack_msg)

                        # 有機率直接開戰
                        if random.random() < war_chance:
                            attacker_planet.war_with.add(target_planet.name)
                            target_planet.war_with.add(attacker_planet.name)
                            attacker_planet.war_duration[target_planet.name] = 0
                            target_planet.war_duration[attacker_planet.name] = 0
                            war_declare_msg = f"{galaxy.year} 年：⚔️ **{attacker_planet.name}** 與 **{target_planet.name}** 爆發全面戰爭！"
                            galaxy.global_events_log.append({"year": galaxy.year, "events": [war_declare_msg]})
                            st.error(war_declare_msg)
                        
                        attacker_planet.attack_cooldown = 5 # 設置冷卻時間
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
                        defend_planet.defense_level = min(100, defend_planet.defense_level + 10) # 提升防禦等級
                        st.success(f"成功加強 **{defend_planet.name}** 的城市防禦，防禦等級提升至 {defend_planet.defense_level}！")
                        galaxy.global_events_log.append({"year": galaxy.year, "events": [f"{galaxy.year} 年：🛡️ **{defend_planet.name}** 加強了城市防禦。"]})
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
                            galaxy.global_events_log.append({"year": galaxy.year, "events": [f"{galaxy.year} 年：✨ **{defend_planet.name}** 部署了行星護盾，當年有效。"]})
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
                    defend_planet.tech_levels[tech_type_to_invest] = min(1.0, defend_planet.tech_levels[tech_type_to_invest] + 0.05) # 提升科技
                    st.success(f"成功投資 **{defend_planet.name}** 的 {tech_type_to_invest} 科技，目前為 {defend_planet.tech_levels[tech_type_to_invest]:.2f}！")
                    galaxy.global_events_log.append({"year": galaxy.year, "events": [f"{galaxy.year} 年：🔬 **{defend_planet.name}** 投資了 {tech_type_to_invest} 科技。"]})
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
            "選擇發起結盟請求的行星：",
            [p.name for p in active_planets_for_alliance],
            key="proposing_planet_select"
        )
        proposing_planet = next((p for p in galaxy.planets if p.name == proposing_planet_name), None)

        target_alliance_options = [
            p.name for p in active_planets_for_alliance 
            if p.name != proposing_planet_name and p.name not in proposing_planet.allies and p.name not in proposing_planet.war_with
        ]
        
        if not target_alliance_options:
            st.info(f"**{proposing_planet_name}** 目前沒有可結盟的行星（已結盟或正在交戰）。")
            target_alliance_planet_name = None
        else:
            target_alliance_planet_name = st.selectbox(
                "選擇目標結盟行星：",
                target_alliance_options,
                key="target_alliance_planet_select"
            )
        target_alliance_planet = next((p for p in galaxy.planets if p.name == target_alliance_planet_name), None)

        if proposing_planet and target_alliance_planet:
            if st.button("提出結盟請求", key="propose_alliance_button"):
                proposing_planet.allies.add(target_alliance_planet.name)
                target_alliance_planet.allies.add(proposing_planet.name)
                
                # 結盟會提升關係到友好
                proposing_planet.relations[target_alliance_planet.name] = "friendly"
                target_alliance_planet.relations[proposing_planet.name] = "friendly"

                alliance_msg = f"{galaxy.year} 年：🤝 **{proposing_planet.name}** 與 **{target_alliance_planet.name}** 成功結盟！"
                galaxy.global_events_log.append({"year": galaxy.year, "events": [alliance_msg]})
                st.success(alliance_msg)
                st.rerun()

# --- 主模擬邏輯 ---
# 使用 st.empty() 創建一個佔位符，用於顯示模擬進度，避免頻繁渲染
progress_status = st.empty()

# 將模擬迴圈包裹在按鈕點擊事件中
if simulate_step_button:
    for _ in range(years_per_step): # 根據用戶選擇的步驟年數進行模擬
        # 更新進度條，而不是每次都重新渲染整個頁面
        progress_status.markdown(f"**--- 模擬年份 {galaxy.year + 1} ---**") # 預先顯示下一年
        simulate_year(galaxy) # 呼叫模組化的模擬函數
    # 每次模擬步驟結束後，強制 Streamlit 重新運行以更新 UI
    st.rerun()

# 模擬結束後，清除進度狀態顯示
progress_status.empty()

# --- 顯示資訊 ---
st.markdown("---") # 分隔線
st.markdown("## 🌍 星系概況")
with st.container(): # 使用容器來應用卡片樣式
    # 顯示聯邦領導人資訊
    if galaxy.federation_leader:
        st.markdown(f"**聯邦領導人：** {galaxy.federation_leader.name} (來自 {galaxy.federation_leader.city})")
    else:
        st.markdown("**聯邦領導人：** 暫無")

    # 顯示當前政策資訊
    if galaxy.active_federation_policy:
        policy = galaxy.active_federation_policy
        st.markdown(f"**當前聯邦政策：** 「{policy['type']}」 (剩餘 {galaxy.policy_duration_left} 年)")
    else:
        st.markdown("**當前聯邦政策：** 無")

    # 顯示行星關係
    st.markdown("#### 🤝 行星關係：")
    if len(galaxy.planets) > 1:
        for p1 in galaxy.planets:
            relations_str = []
            for p2_name, status in p1.relations.items():
                # 確保對方行星仍然存在且存活
                if any(p.name == p2_name and p.is_alive for p in galaxy.planets):
                    war_status = " (戰爭中)" if p2_name in p1.war_with else ""
                    alliance_status = " (盟友)" if p2_name in p1.allies else ""
                    relations_str.append(f"{p2_name}: {status}{war_status}{alliance_status}")
            if relations_str:
                st.write(f"- **{p1.name}** 與其他行星的關係: {', '.join(relations_str)}")
            else:
                st.write(f"- **{p1.name}** 目前沒有活躍的行星關係。")
    else:
        st.info("星系中只有一個行星，沒有關係可顯示。")

# 可視化地圖 (Plotly)
st.markdown("#### 🗺️ 星系地圖：")
if galaxy.planets:
    # 準備行星數據
    planet_data = []
    for planet in galaxy.planets:
        x, y = galaxy.map_layout.get(planet.name, (0,0)) # 確保有位置
        planet_data.append({
            "name": planet.name,
            "x": x,
            "y": y,
            "type": "外星行星" if planet.alien else "地球行星",
            "military_tech": planet.tech_levels["軍事"],
            "environment_tech": planet.tech_levels["環境"],
            "medical_tech": planet.tech_levels["醫療"],
            "production_tech": planet.tech_levels["生產"],
            "pollution": planet.pollution,
            "conflict": planet.conflict_level,
            "defense_level": planet.defense_level,
            "is_alive": planet.is_alive
        })
    df_planets = pd.DataFrame(planet_data)

    fig_map = go.Figure()

    # Add dummy traces for line legends (only one of each type)
    legend_line_types = {
        '中立關係': 'grey',
        '友好關係': 'green',
        '敵對關係': 'orange',
        '戰爭中': 'red'
    }
    for name, color in legend_line_types.items():
        fig_map.add_trace(go.Scatter(
            x=[None], y=[None], # Invisible point
            mode='lines',
            line=dict(color=color, width=2),
            name=name,
            showlegend=True,
            hoverinfo='skip'
        ))

    # Add actual lines for relationships
    for p1 in galaxy.planets:
        for p2_name, status in p1.relations.items():
            p2_obj = next((p for p in galaxy.planets if p.name == p2_name and p.is_alive), None)
            if p2_obj and p1.name < p2_name: # 避免重複繪製和已滅亡行星
                x1, y1 = galaxy.map_layout.get(p1.name, (0,0))
                x2, y2 = galaxy.map_layout.get(p2_obj.name, (0,0))
                
                line_color = 'grey' # Neutral
                if status == "friendly":
                    line_color = 'green'
                elif status == "hostile":
                    line_color = 'orange'
                
                if p2_name in p1.war_with: # War overrides other statuses
                    line_color = 'red'

                fig_map.add_trace(go.Scatter(
                    x=[x1, x2, None], # None separates segments
                    y=[y1, y2, None],
                    mode='lines',
                    line=dict(color=line_color, width=2),
                    hoverinfo='text',
                    text=f"關係: {status}<br>戰爭: {'是' if p2_name in p1.war_with else '否'}",
                    showlegend=False # Do not show legend for each segment
                ))

    # Add separate traces for planet type legends
    earth_planets = df_planets[df_planets['type'] == '地球行星']
    alien_planets = df_planets[df_planets['type'] == '外星行星']

    if not earth_planets.empty:
        fig_map.add_trace(go.Scatter(
            x=[None], y=[None], # Invisible point for legend
            mode='markers',
            marker=dict(
                size=20,
                color='blue',
                symbol='circle',
                line=dict(width=2, color='DarkSlateGrey')
            ),
            name='地球行星',
            showlegend=True,
            hoverinfo='skip'
        ))
    if not alien_planets.empty:
        fig_map.add_trace(go.Scatter(
            x=[None], y=[None], # Invisible point for legend
            mode='markers',
            marker=dict(
                size=20,
                color='purple',
                symbol='circle',
                line=dict(width=2, color='DarkSlateGrey')
            ),
            name='外星行星',
            showlegend=True,
            hoverinfo='skip'
        ))

    # Add actual planet markers with text and hover (without legend, as it's covered by dummy traces)
    fig_map.add_trace(go.Scatter(
        x=df_planets["x"],
        y=df_planets["y"],
        mode='markers+text',
        marker=dict(
            size=20,
            color=df_planets["type"].map({"地球行星": "blue", "外星行星": "purple"}),
            symbol='circle',
            line=dict(width=2, color='DarkSlateGrey')
        ),
        text=df_planets["name"],
        textposition="top center",
        hoverinfo='text',
        texttemplate='%{text}',
        hovertemplate="<b>%{text}</b><br>" +
                      "類型: %{customdata[0]}<br>" +
                      "軍事科技: %{customdata[1]:.2f}<br>" +
                      "環境科技: %{customdata[2]:.2f}<br>" +
                      "醫療科技: %{customdata[3]:.2f}<br>" +
                      "生產科技: %{customdata[4]:.2f}<br>" +
                      "污染: %{customdata[5]:.2f}<br>" +
                      "衝突: %{customdata[6]:.2f}<br>" +
                      "防禦等級: %{customdata[7]}<extra></extra>",
        customdata=df_planets[['type', 'military_tech', 'environment_tech', 'medical_tech', 'production_tech', 'pollution', 'conflict', 'defense_level']],
        showlegend=False # Hide legend for this actual plot trace
    ))

    fig_map.update_layout(
        title='星系地圖',
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        height=500, # Increase height slightly for better visibility
        showlegend=True, # Ensure legend is shown
        legend=dict(
            orientation="h", # Horizontal legend
            yanchor="bottom",
            y=1.02, # Position above the plot
            xanchor="right",
            x=1
        ),
        plot_bgcolor='rgba(0,0,0,0)', # Keep transparent background
        paper_bgcolor='rgba(0,0,0,0)' # Keep transparent background
    )
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.info("星系中沒有行星可供顯示地圖。")


for planet in galaxy.planets:
    st.markdown(f"#### 🪐 {planet.name} ({'外星' if planet.alien else '地球'})｜污染 **{planet.pollution:.2f}**｜衝突等級 **{planet.conflict_level:.2f}**{' (疫情活躍中)' if planet.epidemic_active else ''}｜防禦等級 **{planet.defense_level}**{' (護盾活躍中)' if planet.shield_active else ''}")
    st.markdown(f"**科技水平：** 軍事: {planet.tech_levels['軍事']:.2f} | 環境: {planet.tech_levels['環境']:.2f} | 醫療: {planet.tech_levels['醫療']:.2f} | 生產: {planet.tech_levels['生產']:.2f}")
if not galaxy.planets:
    st.warning("所有行星都已滅亡，星系一片死寂...")

st.markdown("---") # 分隔線
# 顯示選擇城市的統計資訊
found_city = False
for planet in galaxy.planets:
    for city in planet.cities:
        if city.name == selected_city:
            found_city = True
            with st.container(): # 使用容器來應用卡片樣式
                st.markdown(f"### 📊 **{city.name}** 資訊")
                st.write(f"**人口：** {len(city.citizens)} (出生 {city.birth_count} / 死亡 {city.death_count} / 遷入 {city.immigration_count} / 遷出 {city.emigration_count})")
                st.write(f"**資源：** 糧食: {city.resources['糧食']:.0f}｜能源: {city.resources['能源']:.0f}｜稅收: {city.resources['稅收']:.0f}")
                st.write(f"**產業專精：** {city.specialization}") # 顯示產業專精
                st.write(f"**群眾運動狀態：** {'活躍中' if city.mass_movement_active else '平靜'}")
                st.write(f"**合作經濟水平：** {city.cooperative_economy_level:.2f}") # 顯示合作經濟水平
                st.write(f"**政體：** {city.government_type}") # 顯示政體

                # 城市投資功能
                st.markdown("#### 💰 城市管理：")
                if st.button(f"投資 {city.name} (花費 50 稅收)"):
                    investment_cost = 50
                    if city.resources["稅收"] >= investment_cost:
                        city.resources["稅收"] -= investment_cost
                        city.resources["糧食"] += 30
                        city.resources["能源"] += 15
                        for citizen in city.citizens:
                            if citizen.alive:
                                citizen.health = min(1.0, citizen.health + 0.05) # 提升健康
                                citizen.trust = min(1.0, citizen.trust + 0.03) # 提升信任
                                citizen.happiness = min(1.0, citizen.happiness + 0.05) # 提升快樂度
                        city.events.append(f"{galaxy.year} 年：💸 對 {city.name} 進行了投資，資源和市民福祉得到提升！")
                        current_year_global_events.append(f"{galaxy.year} 年：💸 對 {city.name} 進行了投資，資源和市民福祉得到提升！")
                        st.success(f"成功投資 {city.name}！")
                        st.rerun() # 重新運行以更新數據
                    else:
                        st.warning(f"{city.name} 稅收不足，無法投資！需要 {investment_cost} 稅收。")

                # 歷史趨勢圖 (Plotly)
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

                # 思想派別分布 (Plotly)
                st.markdown("#### 🧠 思想派別分布：")
                ideology_count = {}
                for c in city.citizens:
                    if c.alive:
                        ideology_count[c.ideology] = ideology_count.get(c.ideology, 0) + 1
                if ideology_count:
                    ideology_df = pd.DataFrame(list(ideology_count.items()), columns=['思想派別', '人數'])
                    fig_ideology = px.bar(ideology_df, x='思想派別', y='人數', title=f"{city.name} 思想派別分布")
                    st.plotly_chart(fig_ideology, use_container_width=True)
                else:
                    st.info("該城市目前沒有活著的市民。")

                # 死亡原因分析 (Plotly)
                st.markdown("#### 💀 死亡原因分析：")
                death_causes = [item[3] for item in city.graveyard if item[3] is not None]
                if death_causes:
                    death_cause_counts = pd.Series(death_causes).value_counts()
                    death_cause_df = pd.DataFrame({'死因': death_cause_counts.index, '人數': death_cause_counts.values})
                    fig_death = px.bar(death_cause_df, x='死因', y='人數', title=f"{city.name} 死亡原因分析")
                    st.plotly_chart(fig_death, use_container_width=True)
                else:
                    st.info("墓園中沒有死亡原因記錄。")

                # 最近事件
                st.markdown("#### 📰 最近事件：")
                if city.events:
                    for evt in city.events[::-1]:
                        st.write(f"- {evt}")
                else:
                    st.info("本年度沒有新事件發生。")

                # 墓園紀錄
                st.markdown("#### 🪦 墓園紀錄：")
                if city.graveyard:
                    for name, age, ideology, cause in city.graveyard[-5:][::-1]:
                        st.write(f"- {name} (享年 {age} 歲，生前信仰：{ideology}，死因：{cause if cause else '未知'})")
                else:
                    st.info("墓園目前沒有記錄。")
                
                # 顯示部分市民詳細資訊
                st.markdown("#### 👤 部分市民詳細資訊：")
                if city.citizens:
                    sample_citizens = random.sample([c for c in city.citizens if c.alive], min(5, len(city.citizens)))
                    for c in sample_citizens:
                        partner_info = f"配偶: {c.partner.name}" if c.partner else "單身"
                        st.write(f"- **{c.name}**: 年齡 {c.age}, 健康 {c.health:.2f}, 信任 {c.trust:.2f}, 快樂度 {c.happiness:.2f}, 思想 {c.ideology}, 職業 {c.profession}, 教育 {c.education_level}, 財富 {c.wealth:.2f}, {partner_info}")
                else:
                    st.info("該城市目前沒有活著的市民。")

            break
    if found_city:
        break
if not found_city and selected_city:
    st.warning(f"目前無法找到城市 **{selected_city}** 的資訊，它可能已經滅亡。")


st.markdown("---") # 分隔線
st.markdown("## 📊 跨城市數據對比") # 新增跨城市對比區塊
with st.container(): # 使用容器來應用卡片樣式
    all_city_data = []
    for planet in galaxy.planets:
        for city in planet.cities:
            alive_citizens = [c for c in city.citizens if c.alive]
            avg_health = sum(c.health for c in alive_citizens) / max(1, len(alive_citizens)) if alive_citizens else 0
            avg_trust = sum(c.trust for c in alive_citizens) / max(1, len(alive_citizens)) if alive_citizens else 0
            avg_happiness = sum(c.happiness for c in alive_citizens) / max(1, len(alive_citizens)) if alive_citizens else 0
            
            all_city_data.append({
                "行星": planet.name,
                "城市": city.name,
                "人口": len(city.citizens),
                "平均健康": f"{avg_health:.2f}",
                "平均信任": f"{avg_trust:.2f}",
                "平均快樂度": f"{avg_happiness:.2f}", # 新增平均快樂度
                "糧食": city.resources['糧食'],
                "能源": city.resources['能源'],
                "稅收": city.resources['稅收'],
                "產業專精": city.specialization, # 新增產業專精
                "軍事科技": f"{planet.tech_levels['軍事']:.2f}", # 顯示各領域科技
                "環境科技": f"{planet.tech_levels['環境']:.2f}",
                "醫療科技": f"{planet.tech_levels['醫療']:.2f}",
                "生產科技": f"{planet.tech_levels['生產']:.2f}",
                "污染": f"{planet.pollution:.2f}",
                "衝突等級": f"{planet.conflict_level:.2f}",
                "防禦等級": planet.defense_level, # 新增防禦等級
                "群眾運動": '是' if city.mass_movement_active else '否',
                "合作經濟": f"{city.cooperative_economy_level:.2f}",
                "政體": city.government_type
            })

    if all_city_data:
        df_cities = pd.DataFrame(all_city_data)
        st.dataframe(df_cities.set_index("城市"))
    else:
        st.info("目前沒有城市數據可供對比。")


st.markdown("---") # 分隔線
st.markdown("## 🗞️ 未來之城日報")
with st.container(): # 使用容器來應用卡片樣式
    if galaxy.global_events_log:
        st.markdown("點擊年份查看當年度事件：")
        # 從最新的年份開始顯示，只顯示最近 50 年
        for report_entry in reversed(galaxy.global_events_log[-50:]): 
            with st.expander(f"**{report_entry['year']} 年年度報告**"):
                if report_entry['events']:
                    for evt in report_entry['events']:
                        st.write(f"- {evt}")
                else:
                    st.info(f"{report_entry['year']} 年全球風平浪靜，沒有重大事件發生。")
    else:
        st.info("目前還沒有未來之城日報的記錄。")

st.markdown("---") # 分隔線
st.info("模擬結束。請調整模擬年數或選擇其他城市查看更多資訊。")
