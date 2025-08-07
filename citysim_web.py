# -*- coding: utf-8 -*-
# 🌐 CitySim 世界模擬器 Pro (精簡優化版)
import streamlit as st
import random
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from collections import deque
import json # 引入 json 庫，用於處理日誌中的複雜結構

# 設定 Streamlit 頁面配置
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
        transform: scale(1.05);
    }
    /* 區塊樣式 */
    .stContainer {
        border-radius: 15px;
        padding: 20px;
        background-color: #f0f2f6;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# 模擬核心：定義物件導向的類別
class PoliticalParty:
    def __init__(self, name, ideology):
        self.name = name
        self.ideology = ideology  # e.g., '自由主義', '社會主義', '保守主義'
        self.popularity = random.uniform(0.1, 0.5)

class Planet:
    def __init__(self, name):
        self.name = name
        self.cities = []
        self.population = 0
        self.tech_levels = {
            '軍事': random.uniform(1.0, 5.0),
            '環境': random.uniform(1.0, 5.0),
            '醫療': random.uniform(1.0, 5.0),
            '生產': random.uniform(1.0, 5.0)
        }
        self.pollution = random.uniform(0.1, 1.0)
        self.conflict_level = random.uniform(0.0, 0.5)
        self.defense_level = 0
        self.total_tax_revenue = 0
        self.total_resource_output = 0

    def add_city(self, city):
        self.cities.append(city)
        self.population += city.population

    def update_planet_stats(self):
        self.population = sum(city.population for city in self.cities)
        self.total_tax_revenue = sum(city.resources['稅收'] for city in self.cities)
        self.total_resource_output = sum(city.resources['食物'] + city.resources['能源'] for city in self.cities)
        # 更新星球科技水平
        for tech in self.tech_levels:
            self.tech_levels[tech] = sum(city.tech_level[tech] for city in self.cities) / len(self.cities) if self.cities else 0
        # 更新污染和衝突等級
        self.pollution = sum(city.pollution for city in self.cities) / len(self.cities) if self.cities else 0
        self.conflict_level = sum(city.conflict_level for city in self.cities) / len(self.cities) if self.cities else 0

class City:
    def __init__(self, name, population, planet_name, specialization=None):
        self.name = name
        self.population = population
        self.planet_name = planet_name
        self.year_established = 0
        self.specialization = specialization if specialization else random.choice(['工業', '農業', '科技', '服務'])
        self.happiness = random.uniform(0.5, 1.0)
        self.crime_rate = random.uniform(0.1, 0.5)
        self.pollution = random.uniform(0.1, 0.5)
        self.cooperative_economy_level = random.uniform(0.0, 0.3)
        self.mass_movement_active = False
        self.mass_movement_progress = 0
        self.conflict_level = 0
        self.government_type = random.choice(['民主', '專制', '寡頭'])
        self.political_parties = [
            PoliticalParty('自由黨', '自由主義'),
            PoliticalParty('工黨', '社會主義'),
            PoliticalParty('保守黨', '保守主義')
        ]
        self.ruling_party = random.choice(self.political_parties)
        self.resources = {
            '食物': population * random.uniform(0.8, 1.2),
            '能源': population * random.uniform(0.5, 1.5),
            '稅收': 0,
        }
        self.tech_level = {
            '軍事': random.uniform(1.0, 5.0),
            '環境': random.uniform(1.0, 5.0),
            '醫療': random.uniform(1.0, 5.0),
            '生產': random.uniform(1.0, 5.0)
        }
        self.city_log = []

    def update_resources(self):
        # 根據特化調整資源產出
        if self.specialization == '工業':
            self.resources['能源'] += self.population * random.uniform(0.2, 0.5)
            self.resources['食物'] -= self.population * random.uniform(0.1, 0.2)
            self.pollution += random.uniform(0.01, 0.05)
        elif self.specialization == '農業':
            self.resources['食物'] += self.population * random.uniform(0.3, 0.6)
            self.resources['能源'] -= self.population * random.uniform(0.05, 0.1)
        elif self.specialization == '科技':
            self.tech_level['生產'] += random.uniform(0.01, 0.05)
            self.tech_level['醫療'] += random.uniform(0.01, 0.05)
        
        # 基本資源消耗
        self.resources['食物'] -= self.population * 0.2
        self.resources['能源'] -= self.population * 0.15
        self.resources['稅收'] = self.population * random.uniform(0.05, 0.1) * self.cooperative_economy_level
        
        # 確保資源不為負
        for resource in self.resources:
            self.resources[resource] = max(0, self.resources[resource])

    def update_happiness(self):
        # 幸福度受資源、污染、犯罪率影響
        resource_factor = (self.resources['食物'] + self.resources['能源']) / self.population
        self.happiness += (resource_factor - 1.0) * 0.05
        self.happiness -= self.pollution * 0.1
        self.happiness -= self.crime_rate * 0.2
        self.happiness = max(0, min(1, self.happiness)) # 確保幸福度在 0 到 1 之間

    def handle_mass_movement(self):
        if self.happiness < 0.3 and not self.mass_movement_active:
            self.mass_movement_active = True
            self.mass_movement_progress = 0.1
        
        if self.mass_movement_active:
            self.mass_movement_progress += (1 - self.happiness) * 0.1
            if self.mass_movement_progress >= 1.0:
                self.trigger_political_revolution()

    def trigger_political_revolution(self):
        old_ruling_party = self.ruling_party
        new_ruling_party = random.choice([p for p in self.political_parties if p != old_ruling_party])
        self.ruling_party = new_ruling_party
        self.government_type = random.choice(['民主', '專制', '寡頭'])
        self.mass_movement_active = False
        self.mass_movement_progress = 0
        self.city_log.append(f"政變！{old_ruling_party.name} 下台，{new_ruling_party.name} 執政，政體變為 {self.government_type}")

    def update_tech_and_pollution(self, planet_techs):
        # 城市的科技水準會隨著星球的平均水準而進步
        for tech in self.tech_level:
            self.tech_level[tech] += (planet_techs[tech] - self.tech_level[tech]) * 0.01
        
        # 污染處理
        self.pollution += (self.resources['能源'] / self.population) * 0.01
        self.pollution -= self.tech_level['環境'] * 0.01
        self.pollution = max(0, self.pollution)

    def generate_report(self):
        # 生成城市年度報告
        return {
            '人口': self.population,
            '幸福度': self.happiness,
            '污染': self.pollution,
            '政體': self.government_type,
            '執政黨': self.ruling_party.name if self.ruling_party else '無',
            '食物': self.resources['食物'],
            '能源': self.resources['能源'],
            '稅收': self.resources['稅收']
        }

    def update(self, planet_techs):
        self.year_established += 1
        self.population = int(self.population * random.uniform(1.01, 1.05))
        self.update_resources()
        self.update_happiness()
        self.handle_mass_movement()
        self.update_tech_and_pollution(planet_techs)

class Galaxy:
    def __init__(self):
        self.planets = []
        self.year = 0
        self.history = {}
        self.global_events_log = deque(maxlen=20)

    def add_planet(self, planet):
        self.planets.append(planet)

    def simulate_year(self):
        self.year += 1
        
        # 模擬每個星球
        for planet in self.planets:
            planet.update_planet_stats()
            # 模擬星球上的每個城市
            for city in planet.cities:
                city.update(planet.tech_levels)
                
            # 隨機事件 (星球層級)
            if random.random() < 0.1: # 10% 機率觸發事件
                self.trigger_planet_event(planet)
        
        self.history[self.year] = {
            'total_population': sum(p.population for p in self.planets),
            'total_tax_revenue': sum(p.total_tax_revenue for p in self.planets),
            'total_resource_output': sum(p.total_resource_output for p in self.planets),
            'avg_tech_level': sum(p.tech_levels['生產'] for p in self.planets) / len(self.planets) if self.planets else 0,
            'avg_pollution': sum(p.pollution for p in self.planets) / len(self.planets) if self.planets else 0
        }

    def trigger_planet_event(self, planet):
        event_type = random.choice(['科技大爆發', '環境危機', '星際貿易協定'])
        event_report = ""
        
        if event_type == '科技大爆發':
            tech = random.choice(list(planet.tech_levels.keys()))
            planet.tech_levels[tech] *= 1.5
            event_report = f"🤖 在 {planet.name} 發生了一場 {tech} 科技大爆發！該領域的科技水準大幅提升。"
        elif event_type == '環境危機':
            planet.pollution += random.uniform(0.5, 1.0)
            event_report = f"🚨 {planet.name} 遭受了嚴重的環境危機，污染等級飆升！"
        elif event_type == '星際貿易協定':
            for city in planet.cities:
                city.resources['食物'] *= 1.2
                city.resources['能源'] *= 1.2
            event_report = f"🤝 簽訂了星際貿易協定，{planet.name} 所有城市的資源產出增加！"
            
        self.global_events_log.append({
            'year': self.year,
            'event': event_report,
            'type': event_type
        })


# --- Streamlit 應用介面 ---
st.title('🌐 CitySim 世界模擬器 Pro')

# 初始化模擬器
if 'galaxy' not in st.session_state:
    st.session_state.galaxy = Galaxy()
    st.session_state.galaxy.add_planet(Planet('賽博坦星'))
    st.session_state.galaxy.add_planet(Planet('諾瓦星'))
    
    # 在初始城市時，確保 `ruling_party` 存在
    planet1 = st.session_state.galaxy.planets[0]
    planet1.add_city(City('未來市', 100000, planet1.name, '科技'))
    planet1.add_city(City('工業城', 150000, planet1.name, '工業'))
    
    planet2 = st.session_state.galaxy.planets[1]
    planet2.add_city(City('綠蔭城', 80000, planet2.name, '農業'))
    planet2.add_city(City('貿易港', 120000, planet2.name, '服務'))
    
    st.session_state.simulation_started = False
    st.session_state.current_year = 0

galaxy = st.session_state.galaxy
current_year = st.session_state.current_year

st.sidebar.title("控制面板")
if st.sidebar.button("開始模擬"):
    st.session_state.simulation_started = True
    st.sidebar.success("模擬已啟動！")

if st.sidebar.button("進行一年"):
    if st.session_state.simulation_started:
        st.session_state.galaxy.simulate_year()
        st.session_state.current_year += 1
        st.sidebar.info(f"成功模擬至第 {st.session_state.current_year} 年")
    else:
        st.sidebar.warning("請先點擊 '開始模擬' 按鈕")

if st.sidebar.button("重設模擬"):
    st.session_state.clear()
    st.experimental_rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(f"**當前年份: {st.session_state.current_year}**")

# 主頁面顯示
if not st.session_state.simulation_started:
    st.info("點擊左側控制面板的 '開始模擬' 按鈕來啟動未來世界的旅程！")
else:
    st.success(f"--- 模擬進行至第 {st.session_state.current_year} 年 ---")

    # 顯示模擬數據總覽
    if st.session_state.current_year > 0:
        history_data = st.session_state.galaxy.history
        df_history = pd.DataFrame(history_data).T
        df_history.index.name = '年份'

        st.markdown("## 📊 模擬數據總覽")
        st.dataframe(df_history)

        st.markdown("---")
        st.markdown("## 📈 趨勢分析")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 總人口趨勢")
            fig = px.line(df_history, y='total_population', title='總人口', labels={'total_population': '總人口'})
            st.plotly_chart(fig)
        with col2:
            st.markdown("### 平均污染趨勢")
            fig = px.line(df_history, y='avg_pollution', title='平均污染', labels={'avg_pollution': '平均污染'})
            st.plotly_chart(fig)

    st.markdown("---")
    st.markdown("## 🪐 行星與城市資訊")
    for planet in galaxy.planets:
        st.markdown(f"### 🌏 {planet.name}")
        with st.expander("點擊查看詳細資訊"):
            st.write(f"**星球總人口**: {planet.population:,}")
            st.write(f"**星球平均污染等級**: {planet.pollution:.2f}")
            
            st.markdown("#### 城市列表")
            all_city_data = []
            for city in planet.cities:
                # 這裡修復了可能的 AttributeError，如果 ruling_party 為 None 則返回 '無'
                ruling_party_name = city.ruling_party.name if city.ruling_party else '無'
                all_city_data.append({
                    "城市": city.name,
                    "人口": city.population,
                    "幸福度": f"{city.happiness:.2f}",
                    "污染": f"{city.pollution:.2f}",
                    "政體": city.government_type,
                    "執政黨": ruling_party_name,
                    "產業專精": city.specialization,
                    "食物": f"{city.resources['食物']:.2f}",
                    "能源": f"{city.resources['能源']:.2f}",
                    "稅收": f"{city.resources['稅收']:.2f}",
                    "合作經濟": f"{city.cooperative_economy_level:.2f}"
                })
            
            if all_city_data:
                df_cities = pd.DataFrame(all_city_data)
                st.dataframe(df_cities.set_index("城市"))

    st.markdown("---")
    st.markdown("## 🗞️ 未來之城日報")
    with st.container():
        if galaxy.global_events_log:
            st.markdown("點擊年份查看當年度事件：")
            # 使用 reversed() 讓最新的事件顯示在最上面
            for report_entry in reversed(galaxy.global_events_log):
                year = report_entry['year']
                event_type = report_entry['type']
                event_content = report_entry['event']
                with st.expander(f"**第 {year} 年** - {event_type}"):
                    st.write(event_content)
        else:
            st.info("目前沒有重大新聞事件發生。")

