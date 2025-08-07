# -*- coding: utf-8 -*-
# 🌐 資源收集者與殖民地建設模擬器
import streamlit as st
import random
import time

# --- 設定頁面樣式與佈局 ---
st.set_page_config(
    page_title="🌐 殖民地模擬器",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 自訂 CSS 樣式 ---
st.markdown("""
<style>
    /* 全域設定 */
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    h1, h2, h3 { color: #2c3e50; }
    .stButton > button {
        background-color: #3498db; /* 藍色 */
        color: white;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        font-weight: bold;
        border-radius: 8px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        cursor: pointer;
    }
    .stButton > button:hover { background-color: #2980b9; }
    .st-emotion-cache-1pxazr4 {
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        padding: 1.5rem;
    }
    .main-game-display {
        border-radius: 15px;
        padding: 2rem;
        background-color: #ecf0f1;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- 遊戲狀態管理核心：st.session_state ---
# 這是確保遊戲狀態在使用者每次點擊按鈕後不會重置的關鍵。
# 如果 session_state 中沒有 'game_initialized' 這個鍵，就代表是第一次運行。
if 'game_initialized' not in st.session_state:
    st.session_state.game_initialized = False
    st.session_state.event_log = []

# --- 遊戲邏輯函數 ---

# 初始化遊戲狀態
def init_game():
    st.session_state.game_initialized = True
    st.session_state.year = 0
    st.session_state.population = 10
    st.session_state.food = 50
    st.session_state.materials = 20
    st.session_state.event_log = ["遊戲開始！你的殖民地成功著陸，是時候建立一個新家園了。"]
    st.session_state.buildings = {"農場": 0, "礦場": 0}

# 執行一年的模擬
def run_year_simulation():
    st.session_state.year += 1
    
    # 資源消耗與生產
    food_consumption = st.session_state.population * 2
    food_production = st.session_state.buildings["農場"] * 15
    material_production = st.session_state.buildings["礦場"] * 10
    
    # 根據生產和消耗更新資源
    st.session_state.food += food_production - food_consumption
    st.session_state.materials += material_production
    
    st.session_state.event_log.append(
        f"--- 第 {st.session_state.year} 年 ---"
    )
    
    # 人口變化邏輯
    if st.session_state.food >= food_consumption:
        # 食物充足，人口增加
        new_citizens = int(st.session_state.population * 0.1)
        st.session_state.population += new_citizens
        st.session_state.event_log.append(
            f"🎉 豐收的一年！你的殖民地人口增加了 {new_citizens} 人。"
        )
    else:
        # 食物不足，人口減少
        st.session_state.event_log.append(
            f"⚠️ 食物不足！你的殖民地正面臨飢荒，需要更多食物。人口可能會減少。"
        )

    # 隨機事件
    if random.random() < 0.1: # 10% 的機率觸發
        event = random.choice([
            "一顆流星撞擊了附近，帶來了額外的材料！",
            "一場大雨讓農場產量倍增！",
            "奇怪的疾病在殖民地蔓延，影響了工作效率。"
        ])
        st.session_state.event_log.append(f"🔮 隨機事件：{event}")
        if "材料" in event:
            st.session_state.materials += 20
        # ... 可以添加更多事件邏輯

# 建造建築的函數
def build_building(building_type, cost_materials):
    if st.session_state.materials >= cost_materials:
        st.session_state.materials -= cost_materials
        st.session_state.buildings[building_type] += 1
        st.session_state.event_log.append(
            f"🏗️ 成功建造了一個新的 {building_type}！"
        )
    else:
        st.session_state.event_log.append(
            f"❌ 材料不足！建造 {building_type} 需要 {cost_materials} 材料。"
        )

# --- Streamlit 介面佈局 ---
st.title("🌐 殖民地模擬器")
st.markdown('<div class="main-game-display">', unsafe_allow_html=True)

# 主要遊戲資訊區
st.header("殖民地概覽")
col1, col2, col3, col4 = st.columns(4)

if st.session_state.game_initialized:
    with col1: st.metric("年份", st.session_state.year)
    with col2: st.metric("人口", st.session_state.population)
    with col3: st.metric("食物", st.session_state.food)
    with col4: st.metric("材料", st.session_state.materials)
    
    # 建築物狀態
    st.subheader("建築物")
    st.info(f"農場數量: **{st.session_state.buildings['農場']}** (每年生產 {st.session_state.buildings['農場'] * 15} 食物)")
    st.info(f"礦場數量: **{st.session_state.buildings['礦場']}** (每年生產 {st.session_state.buildings['礦場'] * 10} 材料)")
    
    st.markdown("---")
    
    # 遊戲操作區
    st.subheader("遊戲操作")
    op_col1, op_col2, op_col3 = st.columns(3)
    
    with op_col1:
        if st.button("▶️ 進行一年", help="讓時間前進一年，模擬殖民地運作"):
            run_year_simulation()
            st.rerun() # 重跑腳本以更新畫面

    with op_col2:
        if st.button("🏗️ 建造農場 (15 材料)", help="增加食物生產"):
            build_building("農場", 15)
            st.rerun()

    with op_col3:
        if st.button("⛏️ 建造礦場 (20 材料)", help="增加材料生產"):
            build_building("礦場", 20)
            st.rerun()
else:
    st.info("點擊左側側邊欄的 '開始遊戲' 按鈕來啟動模擬器！")
    
st.markdown('</div>', unsafe_allow_html=True)

# 側邊欄與遊戲控制
with st.sidebar:
    st.title("控制面板")
    
    if not st.session_state.game_initialized:
        if st.button("開始遊戲", use_container_width=True):
            init_game()
            st.rerun()
    else:
        if st.button("重啟遊戲", use_container_width=True):
            init_game()
            st.rerun()
            
    st.markdown("---")
    st.subheader("📜 事件日誌")
    for event in reversed(st.session_state.event_log):
        st.caption(event)
