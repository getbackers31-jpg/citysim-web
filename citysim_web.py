# -*- coding: utf-8 -*-
# 🌐 CitySim 世界模擬器 Pro (精簡優化版)
import streamlit as st
import random
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from collections import deque

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
        background-color: #45a049;
        box-shadow: 0 6px 12px 0 rgba(0,0,0,0.25);
        transform: translateY(-2px);
    }
    
    /* 資訊框樣式 */
    .stAlert {
        border-radius: 10px;
    }
    
    /* 容器樣式 */
    .stContainer {
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #e6e6e6;
        margin-bottom: 20px;
    }

    /* 表格樣式 */
    .dataframe {
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# --- 核心模擬器物件 (簡化版) ---
class Government:
    def __init__(self, name, ideology):
        self.name = name
        self.ideology = ideology # e.g., '社會主義', '資本主義', '民主'
        self.leader = f"{self.name} 領袖"
        self.policies = {
            '稅收': random.uniform(0.1, 0.5),
            '公共支出': random.uniform(0.1, 0.5),
        }

class Technology:
    def __init__(self, name, level=0):
        self.name = name
        self.level = level

class Party:
    def __init__(self, name, ideology):
        self.name = name
        self.ideology = ideology
        self.popularity = random.uniform(0, 1)

class City:
    def __init__(self, name, population):
        self.name = name
        self.population = population
        self.resources = {'金錢': 1000, '能源': 500, '稅收': 0}
        self.specialization = "未設定"
        self.mass_movement_active = False
        self.cooperative_economy_level = 0.0
        self.government_type = "共和國"
        self.ruling_party = None

    def update_economy(self, planet_techs, global_events):
        # 簡化經濟模型
        self.resources['金錢'] += (self.population * 0.1)
        self.resources['能源'] -= (self.population * 0.05)
        self.resources['稅收'] = self.population * self.ruling_party.policies.get('稅收', 0.2) if self.ruling_party else self.population * 0.2
        self.resources['金錢'] += self.resources['稅收']
        
        # 考慮合作經濟
        coop_bonus = self.cooperative_economy_level * 0.1
        self.resources['金錢'] *= (1 + coop_bonus)

class Planet:
    def __init__(self, name):
        self.name = name
        self.cities = []
        self.tech_levels = {'軍事': 0, '環境': 0, '醫療': 0, '生產': 0}
        self.pollution = 0
        self.conflict_level = 0
        self.defense_level = 0

    def add_city(self, city):
        self.cities.append(city)

    def update_tech(self):
        # 科技隨時間緩慢增長
        for tech in self.tech_levels:
            self.tech_levels[tech] += random.uniform(0.01, 0.05)
    
    def check_conflict(self):
        if self.conflict_level > 0.8:
            return "全面戰爭爆發！"
        elif self.conflict_level > 0.5:
            return "區域衝突加劇！"
        return None

class Galaxy:
    def __init__(self):
        self.planets = []
        self.global_events_log = deque(maxlen=20)

    def add_planet(self, planet):
        self.planets.append(planet)

# --- 事件系統 (簡化) ---
def generate_random_event(current_year, event_log):
    event_types = ['經濟危機', '科技突破', '自然災害', '社會動盪', '全球峰會']
    event_type = random.choice(event_types)
    event_description = f"在 {current_year} 年發生了【{event_type}】事件。"
    event_log.append(event_description)
    return event_description

def trigger_revolution(city, event_log):
    if not city.mass_movement_active:
        city.mass_movement_active = True
        event_description = f"在 {city.name} 爆發了大規模群眾運動，政權面臨挑戰！"
        event_log.append(event_description)
        return event_description
    return f"{city.name} 已有群眾運動，無需重複觸發。"

def trigger_tech_boom(planet, event_log):
    tech_type = random.choice(list(planet.tech_levels.keys()))
    planet.tech_levels[tech_type] += 0.5 # 顯著提升
    event_description = f"在 {planet.name} 發生了【{tech_type}】科技大爆發！"
    event_log.append(event_description)
    return event_description

def simulate_step(galaxy):
    event_log = []
    for planet in galaxy.planets:
        planet.update_tech()
        planet.pollution += random.uniform(0.01, 0.03)
        planet.conflict_level = min(1.0, planet.conflict_level + random.uniform(-0.01, 0.02))

        for city in planet.cities:
            # 簡化黨派和政策
            if not city.ruling_party:
                city.ruling_party = Party(f"{city.name}執政黨", "無黨派")
            city.ruling_party.policies['稅收'] = random.uniform(0.1, 0.3)
            city.update_economy(planet.tech_levels, event_log)
    
    if random.random() < 0.1: # 10%機率觸發全球事件
        event_log.append(generate_random_event(st.session_state.current_year, st.session_state.temp_global_events))

    st.session_state.current_year += 1
    return event_log

# --- Streamlit UI 函數 ---
def create_dashboard(galaxy):
    st.markdown("### 📊 模擬儀表板")
    
    # 科技與污染趨勢
    tech_data = {
        '年份': list(range(1, st.session_state.current_year + 1)),
        '軍事科技': [0] * st.session_state.current_year,
        '環境科技': [0] * st.session_state.current_year,
        '污染': [0] * st.session_state.current_year
    }
    
    # 填充數據（簡化，假設只有一個星球）
    if galaxy.planets:
        planet = galaxy.planets[0]
        for i in range(st.session_state.current_year):
            tech_data['軍事科技'][i] = planet.tech_levels['軍事'] * (i/st.session_state.current_year)
            tech_data['環境科技'][i] = planet.tech_levels['環境'] * (i/st.session_state.current_year)
            tech_data['污染'][i] = planet.pollution * (i/st.session_state.current_year)
    
    df_trends = pd.DataFrame(tech_data)
    
    fig = px.line(df_trends, x='年份', y=['軍事科技', '環境科技'], title='科技發展趨勢')
    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.line(df_trends, x='年份', y='污染', title='全球污染趨勢')
    st.plotly_chart(fig2, use_container_width=True)

def create_city_comparison_table(galaxy):
    all_city_data = []
    for planet in galaxy.planets:
        for city in planet.cities:
            all_city_data.append({
                "城市": city.name, "人口": city.population,
                "金錢": city.resources['金錢'], "能源": city.resources['能源'], "稅收": city.resources['稅收'],
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


# --- 主要應用程式邏輯 ---
st.title("🌐 CitySim 世界模擬器 Pro")

st.markdown("歡迎來到 CitySim！您是這個模擬世界的觀察者。透過設定參數並運行模擬，您可以觀察城市、星球和星系如何在時間的推移下演變。")

# --- Session State 初始化 (修正錯誤的關鍵) ---
# 確保所有 session state 變數在程式碼執行時都已經存在
if 'galaxy' not in st.session_state:
    st.session_state.galaxy = None
if 'current_year' not in st.session_state:
    st.session_state.current_year = 0
if 'temp_global_events' not in st.session_state:
    st.session_state.temp_global_events = []
if 'is_running' not in st.session_state:
    st.session_state.is_running = False

# --- 參數設定 ---
st.sidebar.markdown("### ⚙️ 模擬參數")
if st.session_state.galaxy is None:
    num_cities = st.sidebar.slider("城市數量", 1, 5, 2)
    start_simulation_button = st.sidebar.button("啟動新模擬", key="start_sim")

    if start_simulation_button:
        # 建立模擬世界
        new_galaxy = Galaxy()
        planet_alpha = Planet("阿爾法星")
        new_galaxy.add_planet(planet_alpha)
        
        for i in range(num_cities):
            city_name = f"城市-{i+1}"
            population = random.randint(100000, 500000)
            new_city = City(city_name, population)
            new_city.specialization = random.choice(['工業', '農業', '科技', '商業'])
            new_city.cooperative_economy_level = random.uniform(0, 1)
            new_city.government_type = random.choice(["共和國", "邦聯", "社會主義"])
            planet_alpha.add_city(new_city)

        st.session_state.galaxy = new_galaxy
        st.session_state.current_year = 0
        st.session_state.is_running = True
        st.experimental_rerun() # 重新執行以顯示模擬介面

# --- 模擬控制 ---
st.markdown("---")
if st.session_state.galaxy and st.session_state.is_running:
    st.markdown("### 🎮 模擬控制")
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        if st.button("運行一年", help="推進模擬一年"):
            simulation_result = simulate_step(st.session_state.galaxy)
            st.info(f"模擬進入第 {st.session_state.current_year} 年。")
            if simulation_result:
                st.info("當年事件：\n- " + "\n- ".join(simulation_result))
    with col2:
        if st.button("重設模擬", help="回到初始狀態"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.is_running = False
            st.experimental_rerun()
    with col3:
        if st.button("自動運行", help="自動運行模擬，直到手動停止"):
            st.session_state.is_running = True
    with col4:
        if st.button("停止自動", help="停止自動運行模擬"):
            st.session_state.is_running = False

    # 自動運行邏輯
    if st.session_state.is_running:
        st.info("模擬正在自動運行...")
        simulation_result = simulate_step(st.session_state.galaxy)
        st.info(f"模擬進入第 {st.session_state.current_year} 年。")
        if simulation_result:
            st.info("當年事件：\n- " + "\n- ".join(simulation_result))
        st.rerun()

# --- 模擬結果顯示 ---
if st.session_state.galaxy and st.session_state.current_year > 0:
    st.markdown("---")
    st.markdown("## 📊 模擬結果")
    st.markdown(f"### 目前年份: {st.session_state.current_year}")
    
    create_dashboard(st.session_state.galaxy)
    
    st.markdown("---")
    st.markdown("## 🏙️ 城市數據對比")
    create_city_comparison_table(st.session_state.galaxy)
    
    st.markdown("---")
    st.markdown("## ⚙️ 手動事件觸發")
    selected_city_for_event = st.selectbox(
        "選擇要觸發事件的城市", 
        [city.name for planet in st.session_state.galaxy.planets for city in planet.cities]
    )

    if st.button("觸發革命", key="trigger_rev"):
        city_obj = next(
            (city for planet in st.session_state.galaxy.planets for city in planet.cities if city.name == selected_city_for_event),
            None
        )
        if city_obj:
            # 這裡就是修正的關鍵，我們已經確保 temp_global_events 存在
            st.info(trigger_revolution(city_obj, st.session_state.temp_global_events))
    
    if st.button("觸發科技大爆發", key="trigger_tech"):
        planet_obj = st.session_state.galaxy.planets[0] # 假設只有一個星球
        st.info(trigger_tech_boom(planet_obj, st.session_state.temp_global_events))

    st.markdown("---")
    st.markdown("## 🗞️ 未來之城日報")
    with st.container():
        if st.session_state.temp_global_events:
            st.markdown("最新事件報告：")
            for entry in reversed(list(st.session_state.temp_global_events)):
                st.write(f"- {entry}")
        else:
            st.info("目前沒有事件報告。")

