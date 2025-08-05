# 📡 升級版 Citysim Streamlit UI（滑桿模擬年數 + 城市選擇 + 統計顯示 + 生育/疾病/戰爭/科技/污染 + 稅收/移民/墓園/思想派別/新聞）
import streamlit as st
import random
import pandas as pd # 引入 pandas 用於數據處理和圖表

st.set_page_config(page_title="CitySim 世界模擬器 Pro", layout="wide")

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
            self.emotion = (parent1_emotion + parent2_emotion) / 2 + random.uniform(-0.1, 0.1) # 繼承父母平均情緒，略有波動
            self.emotion = max(0.1, min(1.0, self.emotion)) # 限制在0.1到1.0之間
        else:
            self.emotion = random.uniform(0.4, 0.9) # 預設值

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
        self.history = [] # 城市歷史數據 (年齡, 平均健康, 平均信任)
        self.birth_count = 0 # 年度出生人數
        self.death_count = 0 # 年度死亡人數
        self.immigration_count = 0 # 年度移民遷入人數
        self.emigration_count = 0 # 年度移民遷出人數
        self.graveyard = [] # 墓園記錄 (name, age, ideology, death_cause)
        self.mass_movement_active = False # 是否正在發生群眾運動
        self.cooperative_economy_level = 0.0 # 合作經濟水平
        self.government_type = random.choice(["民主制", "專制", "共和制"]) # 城市政體

class Planet:
    """代表一個行星及其上的城市。"""
    # 新增 is_earth 參數
    def __init__(self, name, alien=False, is_earth=False): 
        self.name = name
        self.cities = [] # 行星上的城市列表
        self.tech = 0.5 # 科技水平
        self.pollution = 0 # 污染水平
        self.alien = alien # 是否為外星行星
        self.conflict_level = 0.0 # 行星間衝突等級，0.0 為和平，1.0 為全面戰爭
        self.is_alive = True # 行星是否存活
        self.relations = {} # 與其他行星的關係 (key: other_planet_name, value: "friendly", "neutral", "hostile")
        self.war_with = set() # 正在與哪些行星交戰 (儲存行星名稱)
        self.war_duration = {} # 與各行星的戰爭持續時間 (key: other_planet_name, value: duration_in_years)
        self.epidemic_active = False # 新增：是否有疫情爆發
        self.epidemic_severity = 0.0 # 新增：疫情嚴重程度
        self.is_earth = is_earth # 新增屬性，標記是否為地球

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
    # 將地球標記為 is_earth=True
    earth = Planet("地球", is_earth=True) 
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

# --- Streamlit UI 控制元件 ---
st.title("🌐 CitySim 世界模擬器 Pro")
st.markdown("---") # 分隔線

# 設置側邊欄用於控制模擬參數
with st.sidebar:
    st.header("⚙️ 模擬設定") # 修正：將表情符號包含在字串引號內
    years_to_simulate = st.slider("模擬年數", 1, 100, 10, help="選擇模擬將進行的年數")
    st.markdown("---")
    st.header("🏙️ 城市選擇") # 修正：將表情符號包含在字串引號內
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
        # 將顯示名稱轉換回內部類型
        policy_type_map = {v: k for k, v in policy_options_display.items()}
        actual_policy_type = chosen_policy_type_display
        
        galaxy.active_federation_policy = {
            "type": actual_policy_type,
            "effect": st.session_state.policy_effect,
            "duration": st.session_state.policy_duration
        }
        galaxy.policy_duration_left = st.session_state.policy_duration
        
        current_year_global_events = st.session_state.get('temp_global_events', [])
        policy_msg = f"{galaxy.year} 年：  聯邦領導人 **{galaxy.federation_leader.name}** 頒布了「**{actual_policy_type}**」政策，將持續 {galaxy.policy_duration_left} 年！"
        current_year_global_events.append(policy_msg)
        galaxy.global_events_log.append({"year": galaxy.year, "events": current_year_global_events}) # 記錄政策事件

        st.session_state.awaiting_policy_choice = False
        st.session_state.temp_global_events = [] # 清空臨時事件
        st.rerun() # 重新運行以繼續模擬

# 如果正在等待政策選擇，則停止模擬迴圈的執行
if st.session_state.awaiting_policy_choice:
    st.stop()


# --- 主模擬邏輯 ---
# 為了避免在迭代時修改列表導致問題，我們將市民的狀態變化分兩個階段處理：
# 1. 判斷市民的變化（死亡、出生、移民、結婚）
# 2. 根據判斷結果更新市民列表

# 使用 st.empty() 創建一個佔位符，用於顯示模擬進度，避免頻繁渲染
progress_status = st.empty()

for _ in range(years_to_simulate):
    galaxy.year += 1
    # 更新進度條，而不是每次都重新渲染整個頁面
    progress_status.markdown(f"**--- 模擬年份 {galaxy.year} ---**")
    
    current_year_global_events = [] # 儲存本年度所有事件，用於日報

    # 重置每年的計數器和事件
    for planet in galaxy.planets:
        for city in planet.cities:
            city.birth_count = 0
            city.death_count = 0
            city.immigration_count = 0
            city.emigration_count = 0
            city.events = [] # 清空年度事件，只保留當前年的事件顯示

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
                # 修正：這裡應該使用 new_city_name，而不是 cname
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
                planet.tech += policy["effect"]
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


    active_planets = [p for p in galaxy.planets if p.is_alive]
    for planet in active_planets:
        # 行星級別的變化
        planet.tech += random.uniform(0.01, 0.03)
        planet.pollution += random.uniform(0.01, 0.02)

        # 科技對污染的影響
        if planet.tech > 0.7:
            planet.pollution = max(0, planet.pollution - 0.01)
        elif planet.tech < 0.3:
            planet.pollution += 0.01

        # 新型災難：疫情
        if not planet.epidemic_active and random.random() < 0.02: # 2% 機率爆發新疫情
            planet.epidemic_active = True
            planet.epidemic_severity = random.uniform(0.1, 0.5)
            epidemic_msg = f"{galaxy.year} 年：🦠 **{planet.name}** 爆發了嚴重的疫情！"
            for city in planet.cities: city.events.append(epidemic_msg)
            current_year_global_events.append(epidemic_msg)
        
        if planet.epidemic_active:
            # 疫情影響：市民健康下降，死亡率增加
            epidemic_impact_on_health = planet.epidemic_severity * 0.1 # 基礎影響
            if planet.tech > 0.6: # 科技可以減輕疫情影響
                epidemic_impact_on_health *= (1 - (planet.tech - 0.6) * 1.5)
                epidemic_impact_on_health = max(0.01, epidemic_impact_on_health)

            for city in planet.cities:
                for citizen in city.citizens:
                    if citizen.alive and random.random() < (epidemic_impact_on_health + 0.01): # 疫情導致健康下降和少量死亡
                        citizen.health -= epidemic_impact_on_health
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

        # 新型災難：外星生物襲擊
        if random.random() < 0.01 and len(planet.cities) > 0: # 1% 機率發生外星生物襲擊
            target_city = random.choice(planet.cities)
            attack_strength = random.uniform(0.1, 0.5) # 襲擊強度
            
            # 科技影響防禦力
            defense_bonus = planet.tech * 0.5 # 科技越高，防禦越好
            actual_attack_strength = max(0.05, attack_strength - defense_bonus) # 實際攻擊強度

            # 造成人口和資源損失
            population_loss = int(len(target_city.citizens) * actual_attack_strength * 0.1) # 損失10%人口
            resource_loss = int(target_city.resources["糧食"] * actual_attack_strength * 0.2) # 損失20%糧食

            for _ in range(population_loss):
                if target_city.citizens:
                    victim = random.choice([c for c in target_city.citizens if c.alive])
                    victim.alive = False
                    victim.death_cause = "外星生物襲擊"
                    target_city.death_count += 1
                    target_city.graveyard.append((victim.name, victim.age, victim.ideology, victim.death_cause))
            
            target_city.resources["糧食"] = max(0, target_city.resources["糧食"] - resource_loss)
            target_city.resources["能源"] = max(0, target_city.resources["能源"] - resource_loss / 2)

            attack_msg = f"{galaxy.year} 年：👾 **{target_city.name}** 遭到外星生物襲擊！損失 {population_loss} 人口，大量資源被毀！"
            target_city.events.append(attack_msg)
            current_year_global_events.append(attack_msg)


        # 星際衝突/外交 (受關係影響)
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

                # 戰爭效果：市民死亡率增加，資源消耗增加
                war_death_rate_increase = 0.01 # 額外死亡率
                war_resource_drain_per_city = 5 # 每個城市額外消耗資源
                
                for city in planet.cities:
                    city.resources["糧食"] -= war_resource_drain_per_city
                    city.resources["能源"] -= war_resource_drain_per_city / 2
                    for citizen in city.citizens:
                        if citizen.alive and random.random() < war_death_rate_increase:
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
                    
                    peace_msg = f"{galaxy.year} 年：🕊️ **{planet.name}** 與 **{other_planet_name}** 簽署和平條約，結束了戰爭！"
                    current_year_global_events.append(peace_msg)
                    for city in planet.cities: city.events.append(peace_msg)
                    for city in other_planet_obj.cities: city.events.append(peace_msg)
                
                # 如果正在戰爭，跳過下面的衝突觸發和關係變化，因為戰爭狀態優先
                continue 

            # --- 非戰爭狀態下的衝突觸發與關係演變 ---
            base_conflict_chance = 0.05
            if planet.alien or other_planet_obj.alien:
                base_conflict_chance *= 1.2

            conflict_chance = max(0.01, base_conflict_chance * (1 - planet.tech)) # 科技降低衝突機率

            if relation_status == "friendly":
                conflict_chance *= 0.5 # 友好關係大幅降低衝突機率
            elif relation_status == "hostile":
                conflict_chance *= 2.0 # 敵對關係大幅提高衝突機率

            if random.random() < conflict_chance:
                planet.conflict_level = min(1.0, planet.conflict_level + random.uniform(0.05, 0.15))
                other_planet_obj.conflict_level = min(1.0, other_planet_obj.conflict_level + random.uniform(0.05, 0.15)) # 雙方衝突等級都提升
                
                conflict_msg = f"{galaxy.year} 年：⚠️ {planet.name} 與 {other_planet_name} 的衝突等級提升至 {planet.conflict_level:.2f}！"
                for city in planet.cities:
                    city.events.append(conflict_msg)
                for city in other_planet_obj.cities:
                    city.events.append(conflict_msg)
                current_year_global_events.append(conflict_msg)

                # 衝突會導致關係惡化
                if relation_status != "hostile": # 如果還不是敵對，則轉為敵對
                    planet.relations[other_planet_name] = "hostile"
                    other_planet_obj.relations[planet.name] = "hostile"
                    current_year_global_events.append(f"{galaxy.year} 年：💥 {planet.name} 與 {other_planet_name} 的關係惡化為敵對！")
                
                # 如果衝突等級非常高且關係敵對，則宣戰
                if planet.conflict_level > 0.7 and other_planet_obj.conflict_level > 0.7 and planet.relations[other_planet_name] == "hostile":
                    planet.war_with.add(other_planet_name)
                    other_planet_obj.war_with.add(planet.name)
                    planet.war_duration[other_planet_name] = 0
                    other_planet_obj.war_duration[planet.name] = 0
                    war_declare_msg = f"{galaxy.year} 年：⚔️ **{planet.name}** 向 **{other_planet_name}** 宣戰！星際戰爭爆發！"
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
                    current_year_global_events.append(f"{galaxy.year} 年：🤝 {planet.name} 與 {other_planet_name} 的關係從敵對轉為中立。")
                elif relation_status == "neutral" and random.random() < 0.01:
                    planet.relations[other_planet_name] = "friendly"
                    other_planet_obj.relations[planet.name] = "friendly"
                    current_year_global_events.append(f"{galaxy.year} 年：✨ {planet.name} 與 {other_planet_name} 的關係從中立轉為友好。")


        # 衝突對市民的影響 (在戰爭邏輯中已處理，這裡只處理非戰爭衝突)
        if planet.conflict_level > 0.5 and other_planet_name not in planet.war_with: # 如果有衝突但未宣戰
            for city in planet.cities:
                for citizen in city.citizens:
                    if citizen.alive and random.random() < (planet.conflict_level * 0.002): # 輕微的衝突死亡率
                        citizen.alive = False
                        citizen.death_cause = "衝突"
                        city.events.append(f"{galaxy.year} 年：{citizen.name} 在 {city.name} 因星際衝突而犧牲。")
                        current_year_global_events.append(f"{galaxy.year} 年：{citizen.name} 在 {city.name} 因星際衝突而犧牲。")


    # 處理城市級別的動態
    for planet in active_planets:
        for city in planet.cities:
            # 城市級別的變化 (受政體影響)
            resource_drain_multiplier = 1.0
            if city.government_type == "專制":
                resource_drain_multiplier = 0.8 # 專制可能更有效率
            elif city.government_type == "民主制":
                resource_drain_multiplier = 1.2 # 民主制可能效率較低（但信任度高）

            if random.random() < 0.1:
                city.resources["糧食"] -= 10 * resource_drain_multiplier
                event_msg = f"{galaxy.year} 年：{city.name} 發生糧食短缺。"
                city.events.append(event_msg)
                current_year_global_events.append(event_msg)
                if city.resources["糧食"] < 0:
                    city.resources["糧食"] = 0

            # 合作經濟發展
            if random.random() < 0.05:
                city.cooperative_economy_level = min(1.0, city.cooperative_economy_level + random.uniform(0.01, 0.05))
                if city.cooperative_economy_level > 0.5 and random.random() < 0.01:
                    event_msg = f"{galaxy.year} 年：🌱 {city.name} 的合作經濟蓬勃發展！"
                    city.events.append(event_msg)
                    current_year_global_events.append(event_msg)
            else:
                city.cooperative_economy_level = max(0.0, city.cooperative_economy_level - random.uniform(0.005, 0.02))

            # 合作經濟效果：提升資源產出和市民信任
            if city.cooperative_economy_level > 0.2:
                resource_bonus = city.cooperative_economy_level * 5
                city.resources["糧食"] += resource_bonus
                city.resources["能源"] += resource_bonus / 2
                for citizen in city.citizens:
                    if citizen.alive:
                        citizen.trust = min(1.0, citizen.trust + city.cooperative_economy_level * 0.005)

            # 群眾運動
            alive_citizens_for_stats = [c for c in city.citizens if c.alive]
            avg_trust = sum(c.trust for c in alive_citizens_for_stats) / max(1, len(alive_citizens_for_stats)) if alive_citizens_for_stats else 0
            
            ideology_counts = {}
            for c in alive_citizens_for_stats:
                ideology_counts[c.ideology] = ideology_counts.get(c.ideology, 0) + 1
            
            dominant_ideology = None
            if ideology_counts:
                dominant_ideology = max(ideology_counts, key=ideology_counts.get)
                dominant_percentage = ideology_counts[dominant_ideology] / len(alive_citizens_for_stats)

            # 觸發群眾運動的條件：低信任度 AND 某個思想派別佔比高 AND 隨機機率
            if avg_trust < 0.5 and dominant_ideology and dominant_percentage > 0.6 and random.random() < 0.05:
                if not city.mass_movement_active:
                    city.mass_movement_active = True
                    movement_msg = f"{galaxy.year} 年：📢 {city.name} 爆發了以 **{dominant_ideology}** 為主的群眾運動！"
                    city.events.append(movement_msg)
                    current_year_global_events.append(movement_msg)
                    city.resources["糧食"] -= random.randint(5, 15)
                    city.resources["能源"] -= random.randint(5, 15)
                    for c in alive_citizens_for_stats:
                        c.trust = max(0.1, c.trust - 0.1)
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
            elif city.mass_movement_active and avg_trust > 0.6:
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
            for citizen in list(city.citizens):
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

                # 犯罪職業的額外風險 (導致財富波動或健康/信任下降)
                if citizen.profession in ["小偷", "黑幫成員", "詐騙犯", "毒販"]:
                    if random.random() < 0.03: # 3% 機率發生負面事件 (被抓或受傷)
                        citizen.wealth = max(0, citizen.wealth - random.uniform(20, 50)) # 財富損失
                        citizen.health = max(0.1, citizen.health - random.uniform(0.1, 0.2)) # 健康受損
                        citizen.trust = max(0.1, citizen.trust - random.uniform(0.05, 0.1)) # 信任度下降
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


                # 污染對健康的影響 (受科技影響)
                pollution_health_impact = 0.3
                if planet.tech > 0.6:
                    pollution_health_impact *= (1 - (planet.tech - 0.6) * 2)
                    pollution_health_impact = max(0.05, pollution_health_impact)

                if planet.pollution > 1.0 and random.random() < 0.03:
                    citizen.health -= pollution_health_impact
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

                # 出生判斷 (現在與配偶關聯)
                if citizen.partner and citizen.partner.alive and 20 <= citizen.age <= 40 and random.random() < 0.02:
                    # 傳遞父母屬性給新生兒 (子女家族傳承)
                    baby = Citizen(
                        f"{citizen.name}-子{random.randint(1,100)}",
                        parent1_ideology=citizen.ideology,
                        parent2_ideology=citizen.partner.ideology,
                        parent1_trust=citizen.trust,
                        parent2_trust=citizen.partner.trust,
                        parent1_emotion=citizen.emotion,
                        parent2_emotion=citizen.partner.emotion
                    )
                    baby.city = city.name
                    newborns_this_year.append(baby)
                    city.birth_count += 1
                    event_msg = f"{galaxy.year} 年：{citizen.name} 與 {citizen.partner.name} 在 {city.name} 生下一名子女。"
                    city.events.append(event_msg)
                    current_year_global_events.append(event_msg)

                # 移民判斷 (受財富影響)
                # 財富越低，移民意願越高；財富越高，越傾向留在原地或移民到更富裕的城市
                immigration_chance = 0.02
                if citizen.wealth < 100: # 財富低，移民機率增加
                    immigration_chance *= 1.5
                elif citizen.wealth > 300: # 財富高，移民機率降低
                    immigration_chance *= 0.5

                if random.random() < immigration_chance:
                    other_cities = [ct for p in galaxy.planets for ct in p.cities if ct.name != city.name and p.is_alive]
                    if other_cities:
                        # 傾向移民到人口更多、資源更豐富的城市
                        target_city = random.choice(other_cities) # 預設隨機
                        
                        # 簡單的偏好邏輯：優先選擇人口多、糧食多的城市
                        sorted_cities = sorted(other_cities, key=lambda c: (len(c.citizens), c.resources["糧食"]), reverse=True)
                        if sorted_cities:
                            target_city = sorted_cities[0] # 選擇最好的城市

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

            # 計算平均健康和信任 (只針對活著的市民)
            alive_citizens_for_stats = [c for c in city.citizens if c.alive]
            avg_health = sum(c.health for c in alive_citizens_for_stats) / max(1, len(alive_citizens_for_stats)) if alive_citizens_for_stats else 0
            avg_trust = sum(c.trust for c in alive_citizens_for_stats) / max(1, len(alive_citizens_for_stats)) if alive_citizens_for_stats else 0
            city.history.append((galaxy.year, avg_health, avg_trust))
        
        # 行星滅亡判斷
        if all(len(c.citizens) == 0 for c in planet.cities):
            if planet.is_earth: # 如果是地球，則不會滅亡，而是嘗試再生人口
                event_msg = f"{galaxy.year} 年：🌍 **{planet.name}** 雖然面臨嚴峻挑戰，但仍奇蹟般地維持了生機！"
                current_year_global_events.append(event_msg)
                # 嘗試在其中一個城市再生人口
                if planet.cities:
                    target_city = random.choice(planet.cities)
                    num_new_citizens = random.randint(5, 15) # 再生一些人口
                    for _ in range(num_new_citizens):
                        new_citizen = Citizen(f"{target_city.name}市民#{random.randint(1000, 9999)}")
                        new_citizen.city = target_city.name
                        target_city.citizens.append(new_citizen)
                    event_msg_regen = f"{galaxy.year} 年：🌱 **{target_city.name}** (在 {planet.name} 上) 在絕境中獲得重生，新增了 {num_new_citizens} 名市民！"
                    current_year_global_events.append(event_msg_regen)
                else: # 如果地球連城市都沒了（理論上不該發生，但為了健壯性）
                    event_msg_no_cities = f"{galaxy.year} 年：⚠️ **{planet.name}** 上的城市都已滅亡，但行星本身仍存續，等待新的生命！"
                    current_year_global_events.append(event_msg_no_cities)
            else: # 對於其他行星，正常滅亡
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

# 模擬結束後，清除進度狀態顯示
progress_status.empty()

# --- 顯示資訊 ---
st.markdown("---") # 分隔線
st.markdown("## 🌍 星系概況")
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
                relations_str.append(f"{p2_name}: {status}{war_status}")
        if relations_str:
            st.write(f"- **{p1.name}** 與其他行星的關係: {', '.join(relations_str)}")
        else:
            st.write(f"- **{p1.name}** 目前沒有活躍的行星關係。")
else:
    st.info("星系中只有一個行星，沒有關係可顯示。")

# 可視化地圖
st.markdown("#### 🗺️ 星系地圖：")
if galaxy.planets:
    max_x = max(pos[0] for pos in galaxy.map_layout.values()) + 2
    max_y = max(pos[1] for pos in galaxy.map_layout.values()) + 2
    
    grid = [[' ' for _ in range(max_x)] for _ in range(max_y)]
    planet_symbols = {}
    
    # 放置行星符號
    for i, planet in enumerate(galaxy.planets):
        x, y = galaxy.map_layout[planet.name]
        symbol = '🪐' if not planet.alien else '👽'
        grid[y][x] = symbol
        planet_symbols[planet.name] = symbol

    # 繪製關係線 (簡化為橫向或縱向線)
    for p1 in galaxy.planets:
        for p2_name, status in p1.relations.items():
            p2_obj = next((p for p in galaxy.planets if p.name == p2_name and p.is_alive), None)
            if p2_obj and p1.name < p2_name: # 只繪製一次連接
                x1, y1 = galaxy.map_layout[p1.name]
                x2, y2 = galaxy.map_layout[p2_obj.name] # 使用 p2_obj.name 確保是已存在的行星
                
                line_char = '-' # 中立
                if status == "friendly":
                    line_char = '=' # 友好
                elif status == "hostile":
                    line_char = 'X' # 敵對
                
                if p2_name in p1.war_with: # 戰爭中覆蓋為 W
                    line_char = 'W'

                # 簡單的直線連接
                if x1 == x2: # 垂直線
                    for y in range(min(y1, y2) + 1, max(y1, y2)):
                        if grid[y][x1] == ' ': grid[y][x1] = '|' # 避免覆蓋行星
                elif y1 == y2: # 水平線
                    for x in range(min(x1, x2) + 1, max(x1, x2)):
                        if grid[y1][x] == ' ': grid[y1][x] = line_char
                # 對角線不處理，保持簡潔

    map_str = "```\n"
    for row in grid:
        map_str += "".join(row) + "\n"
    map_str += "```"
    st.markdown(map_str)
    st.markdown("圖例: 🪐=地球行星, 👽=外星行星, -=中立, ==友好, X=敵對, W=戰爭中")
else:
    st.info("星系中沒有行星可供顯示地圖。")


for planet in galaxy.planets:
    st.markdown(f"#### 🪐 {planet.name} ({'外星' if planet.alien else '地球'})｜科技 **{planet.tech:.2f}**｜汙染 **{planet.pollution:.2f}**｜衝突等級 **{planet.conflict_level:.2f}**{' (疫情活躍中)' if planet.epidemic_active else ''}")
if not galaxy.planets:
    st.warning("所有行星都已滅亡，星系一片死寂...")

st.markdown("---") # 分隔線
# 顯示選擇城市的統計資訊
found_city = False
for planet in galaxy.planets:
    for city in planet.cities:
        if city.name == selected_city:
            found_city = True
            st.markdown(f"### 📊 **{city.name}** 資訊")
            st.write(f"**人口：** {len(city.citizens)} (出生 {city.birth_count} / 死亡 {city.death_count} / 遷入 {city.immigration_count} / 遷出 {city.emigration_count})")
            st.write(f"**資源：** 糧食: {city.resources['糧食']}｜能源: {city.resources['能源']}｜稅收: {city.resources['稅收']}")
            st.write(f"**群眾運動狀態：** {'活躍中' if city.mass_movement_active else '平靜'}")
            st.write(f"**合作經濟水平：** {city.cooperative_economy_level:.2f}") # 顯示合作經濟水平
            st.write(f"**政體：** {city.government_type}") # 顯示政體

            # 歷史趨勢圖
            if city.history:
                history_data = {
                    "年份": [h[0] for h in city.history],
                    "平均健康": [h[1] for h in city.history],
                    "平均信任": [h[2] for h in city.history]
                }
                st.line_chart(history_data, x="年份", y=["平均健康", "平均信任"])
            else:
                st.info("該城市尚無歷史數據可供繪製圖表。")

            # 思想派別分布
            st.markdown("#### 🧠 思想派別分布：")
            ideology_count = {}
            for c in city.citizens:
                if c.alive:
                    ideology_count[c.ideology] = ideology_count.get(c.ideology, 0) + 1
            if ideology_count:
                st.bar_chart(ideology_count)
            else:
                st.info("該城市目前沒有活著的市民。")

            # 死亡原因分析
            st.markdown("#### 💀 死亡原因分析：")
            death_causes = [item[3] for item in city.graveyard if item[3] is not None]
            if death_causes:
                death_cause_counts = pd.Series(death_causes).value_counts()
                st.bar_chart(death_cause_counts)
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
                    st.write(f"- **{c.name}**: 年齡 {c.age}, 健康 {c.health:.2f}, 信任 {c.trust:.2f}, 思想 {c.ideology}, 職業 {c.profession}, 教育 {c.education_level}, 財富 {c.wealth:.2f}, {partner_info}")
            else:
                st.info("該城市目前沒有活著的市民。")

            break
    if found_city:
        break
if not found_city and selected_city:
    st.warning(f"目前無法找到城市 **{selected_city}** 的資訊，它可能已經滅亡。")


st.markdown("---") # 分隔線
st.markdown("## 📊 跨城市數據對比") # 新增跨城市對比區塊
all_city_data = []
for planet in galaxy.planets:
    for city in planet.cities:
        alive_citizens = [c for c in city.citizens if c.alive]
        avg_health = sum(c.health for c in alive_citizens) / max(1, len(alive_citizens)) if alive_citizens else 0
        avg_trust = sum(c.trust for c in alive_citizens) / max(1, len(alive_citizens)) if alive_citizens else 0
        
        all_city_data.append({
            "行星": planet.name,
            "城市": city.name,
            "人口": len(city.citizens),
            "平均健康": f"{avg_health:.2f}",
            "平均信任": f"{avg_trust:.2f}",
            "糧食": city.resources['糧食'],
            "能源": city.resources['能源'],
            "稅收": city.resources['稅收'],
            "科技": f"{planet.tech:.2f}",
            "污染": f"{planet.pollution:.2f}",
            "衝突等級": f"{planet.conflict_level:.2f}",
            "群眾運動": '是' if city.mass_movement_active else '否',
            "合作經濟": f"{city.cooperative_economy_level:.2f}", # 顯示合作經濟水平
            "政體": city.government_type # 顯示政體
        })

if all_city_data:
    df_cities = pd.DataFrame(all_city_data)
    st.dataframe(df_cities.set_index("城市"))
else:
    st.info("目前沒有城市數據可供對比。")


st.markdown("---") # 分隔線
st.markdown("## 🗞️ 未來之城日報")
if galaxy.global_events_log:
    # 獲取最新一年的日報
    latest_report = galaxy.global_events_log[-1]
    st.markdown(f"### **{latest_report['year']} 年年度報告**")
    st.write("---")
    if latest_report['events']:
        summary_points = []
        for event in latest_report['events']:
            summary_points.append(f"- {event}")
        st.markdown("\n".join(summary_points))
    else:
        st.info(f"{latest_report['year']} 年全球風平浪靜，沒有重大事件發生。")
else:
    st.info("目前還沒有未來之城日報的記錄。")

st.markdown("---") # 分隔線
st.info("模擬結束。請調整模擬年數或選擇其他城市查看更多資訊。")
 