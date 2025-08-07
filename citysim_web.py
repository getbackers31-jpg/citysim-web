import streamlit as st
import random
import pandas as pd

# --- 遊戲設定與初始狀態 ---
def initialize_game():
    """初始化遊戲狀態，只在 session state 未建立時執行一次。"""
    if 'game_started' not in st.session_state:
        st.session_state.game_started = True
        st.session_state.day = 0  # 這裡的 "day" 代表一個演化週期 (例如百萬年)
        st.session_state.temperature = -50.0  # 初始溫度 (攝氏)
        st.session_state.oxygen = 0.1  # 初始氧氣濃度 (%)
        st.session_state.co2 = 80.0  # 初始二氧化碳濃度 (%)
        st.session_state.water = 10.0  # 初始海洋覆蓋率 (%)
        st.session_state.biomass = 0.0  # 初始生物質 (噸)
        
        # 用於繪製歷史圖表的列表
        st.session_state.history = {
            '週期': [],
            '溫度': [],
            '氧氣': [],
            '海洋': [],
            '生物質': []
        }
        
        st.session_state.event_log = ["一顆貧瘠的岩石行星誕生了。"]
        st.session_state.game_over = False
        st.session_state.game_over_reason = ""

# --- 遊戲主函式 ---
def main():
    """遊戲主介面與邏輯。"""
    st.set_page_config(page_title="專案：創世紀", layout="wide")
    initialize_game()

    # --- 標題與遊戲說明 ---
    st.title("🌍 專案：創世紀 (Project: Genesis)")
    st.markdown("你的任務是引導這顆星球，將它從一顆死寂的岩石演化成生機盎然的宜居世界。")
    st.markdown("---")

    # 如果遊戲結束，顯示結束畫面
    if st.session_state.game_over:
        display_game_over()
        if st.button("重新開始一個新世界"):
            # 重置遊戲
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        return

    # --- 介面佈局 ---
    col1, col2 = st.columns([0.6, 0.4])

    with col1:
        display_planet_status()
        display_history_chart()

    with col2:
        display_controls()
        display_event_log()

# --- 顯示元件 ---
def display_planet_status():
    """顯示星球的各項核心參數。"""
    st.subheader(f"演化週期：第 {st.session_state.day} 百萬年")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("全球均溫", f"{st.session_state.temperature:.1f} °C")
    c2.metric("氧氣濃度", f"{st.session_state.oxygen:.2f} %")
    c3.metric("海洋覆蓋", f"{st.session_state.water:.1f} %")
    c4.metric("生物質", f"{int(st.session_state.biomass)} 噸")
    
    st.progress(int(max(0, min(100, st.session_state.water))), text=f"💧 海洋覆蓋率")
    st.progress(int(max(0, min(100, st.session_state.oxygen))), text=f"💨 氧氣濃度")
    st.markdown("---")


def display_history_chart():
    """顯示歷史數據圖表。"""
    st.subheader("星球演化歷史")
    if len(st.session_state.history['週期']) > 1:
        chart_data = pd.DataFrame({
            '溫度': st.session_state.history['溫度'],
            '氧氣': st.session_state.history['氧氣'],
            '海洋': st.session_state.history['海洋'],
            '生物質': [b / 1000 for b in st.session_state.history['生物質']] # 縮放以利顯示
        })
        st.line_chart(chart_data)
    else:
        st.info("歷史數據不足，請先推進演化。")

def display_controls():
    """顯示玩家可以操作的地球工程選項。"""
    st.subheader("地球工程控制台")
    st.warning("每個週期你只能專注執行一項工程。")

    action = st.radio(
        "選擇本週期的主要工程：",
        ('引導彗星撞擊 (增加水量)', 
         '觸發火山活動 (提升溫度)', 
         '引入藍綠菌 (製造氧氣)',
         '培育基礎植物 (需氧氣與水)'),
        key="action_choice"
    )

    if st.button(f"🚀 推進一百萬年！", type="primary"):
        run_simulation(action)
        check_game_over()
        st.rerun()

def display_event_log():
    """顯示事件日誌。"""
    st.subheader("事件紀錄")
    log_container = st.container(height=250)
    for event in reversed(st.session_state.event_log):
        log_container.info(event)

def display_game_over():
    """顯示遊戲結束畫面。"""
    st.header("演化終結")
    st.error(f"**原因：{st.session_state.game_over_reason}**")
    st.balloons()
    st.markdown("---")
    st.subheader("最終星球狀態：")
    display_planet_status()
    display_history_chart()

# --- 遊戲邏輯 ---
def run_simulation(action):
    """根據玩家的選擇，更新星球狀態。"""
    st.session_state.day += 1
    
    # --- 基礎自然變化 ---
    # 溫度會因二氧化碳濃度自然變化 (溫室效應)
    st.session_state.temperature += st.session_state.co2 * 0.01 - 0.5
    # 氧氣會被緩慢消耗
    st.session_state.oxygen *= 0.98
    
    log_entry = f"週期 {st.session_state.day}: "

    # --- 玩家行動影響 ---
    if action == '引導彗星撞擊 (增加水量)':
        st.session_state.water += random.uniform(2, 5)
        st.session_state.temperature -= random.uniform(1, 3) # 撞擊揚塵降溫
        log_entry += "彗星帶來了豐富的水冰，但也讓天空蒙塵。"
    
    elif action == '觸發火山活動 (提升溫度)':
        st.session_state.co2 += random.uniform(5, 10)
        st.session_state.temperature += random.uniform(2, 5)
        log_entry += "劇烈的火山活動向大氣釋放了大量溫室氣體。"

    elif action == '引入藍綠菌 (製造氧氣)':
        if st.session_state.water > 20:
            o2_increase = st.session_state.water * 0.05
            st.session_state.oxygen += o2_increase
            st.session_state.co2 -= o2_increase * 0.8 # 光合作用消耗CO2
            st.session_state.biomass += o2_increase * 100
            log_entry += "藍綠菌在海洋中大量繁殖，開始製造氧氣。"
        else:
            log_entry += "海洋太少，藍綠菌無法存活。"
            
    elif action == '培育基礎植物 (需氧氣與水)':
        if st.session_state.water > 30 and st.session_state.oxygen > 5 and st.session_state.temperature > 0:
            o2_increase = st.session_state.biomass * 0.01 + 1
            st.session_state.oxygen += o2_increase
            st.session_state.biomass += o2_increase * 200
            log_entry += "頑強的苔蘚和蕨類開始覆蓋潮濕的陸地。"
        else:
            log_entry += "環境過於惡劣，植物無法紮根。你需要更多的水、氧氣和更高的溫度。"
    
    # --- 更新歷史數據 ---
    history = st.session_state.history
    history['週期'].append(st.session_state.day)
    history['溫度'].append(st.session_state.temperature)
    history['氧氣'].append(st.session_state.oxygen)
    history['海洋'].append(st.session_state.water)
    history['生物質'].append(st.session_state.biomass)
    
    # 限制日誌長度
    st.session_state.event_log.append(log_entry)
    if len(st.session_state.event_log) > 10:
        st.session_state.event_log.pop(0)

def check_game_over():
    """檢查是否觸發遊戲結束條件。"""
    temp = st.session_state.temperature
    oxy = st.session_state.oxygen
    water = st.session_state.water
    
    # 勝利條件
    if temp > 10 and temp < 35 and oxy > 18 and oxy < 25 and water > 50 and st.session_state.biomass > 50000:
        st.session_state.game_over = True
        st.session_state.game_over_reason = "恭喜！你成功創造了一個生機盎然的宜居世界！"
        return

    # 失敗條件
    if temp > 100:
        st.session_state.game_over = True
        st.session_state.game_over_reason = "失控的溫室效應！星球變成了無法逆轉的火爐。"
    elif temp < -80:
        st.session_state.game_over = True
        st.session_state.game_over_reason = "全球凍結！星球變成了一顆巨大的冰球。"
    elif st.session_state.day >= 100: # 設置一個最大週期限制
        st.session_state.game_over = True
        st.session_state.game_over_reason = "時間耗盡。雖然星球還在，但你未能在規定時間內達成目標。"


if __name__ == "__main__":
    main()
