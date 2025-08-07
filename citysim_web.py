# -*- coding: utf-8 -*-
# 🚀 火星殖民地計畫 v1.0
import streamlit as st
import random

st.set_page_config(page_title="🚀 火星殖民地計畫", layout="wide")

# --- 遊戲設定 ---
# 建築規格：成本、產出、維護
BUILDING_SPECS = {
    "太陽能板": {"cost": {"鋼材": 50}, "produces": {"電力": 5}, "consumes": {}},
    "鑽井機": {"cost": {"鋼材": 80}, "produces": {"水源": 3}, "consumes": {"電力": 2}},
    "溫室": {"cost": {"鋼材": 100}, "produces": {"食物": 2, "氧氣": 3}, "consumes": {"電力": 1, "水源": 1}},
    "居住艙": {"cost": {"鋼材": 120}, "provides": "人口容量", "capacity": 5, "consumes": {"電力": 1}},
}

# 殖民者消耗
COLONIST_CONSUMPTION = {
    "食物": 0.2,
    "水源": 0.3,
    "氧氣": 0.5,
}

# --- 初始化遊戲 ---
def initialize_game():
    """僅在遊戲初次啟動時執行"""
    if 'game_day' not in st.session_state:
        st.session_state.game_day = 0
        st.session_state.population = 5
        st.session_state.population_capacity = 5
        
        # 資源
        st.session_state.resources = {
            "電力": 20.0,
            "水源": 50.0,
            "食物": 50.0,
            "氧氣": 100.0,
            "鋼材": 500.0,
        }
        
        # 建築
        st.session_state.buildings = {
            "太陽能板": 1,
            "鑽井機": 1,
            "溫室": 1,
            "居住艙": 1,
        }
        
        st.session_state.event_log = ["🚀 登陸成功！火星殖民地計畫正式開始！"]
        st.session_state.game_over = False
        st.session_state.game_over_reason = ""
        st.session_state.victory = False

# --- 遊戲主函式 ---
def main():
    initialize_game()
    
    st.title("🚀 火星殖民地計畫")
    st.markdown("---")

    if st.session_state.game_over:
        display_game_over_screen()
        return
    
    if st.session_state.victory:
        display_victory_screen()
        return

    # 介面佈局
    col1, col2 = st.columns([0.7, 0.3])
    
    with col1:
        display_dashboard()
        display_construction_panel()
    
    with col2:
        display_status_panel()
        display_event_log()

# --- UI 顯示元件 ---
def display_dashboard():
    """顯示主要的資源儀表板"""
    st.header("📊 資源儀表板")
    
    res = st.session_state.resources
    cols = st.columns(5)
    cols[0].metric("⚡ 電力", f"{res['電力']:.1f}")
    cols[1].metric("💧 水源", f"{res['水源']:.1f}")
    cols[2].metric("🌿 食物", f"{res['食物']:.1f}")
    cols[3].metric("💨 氧氣", f"{res['氧氣']:.1f}")
    cols[4].metric("🔩 鋼材", f"{res['鋼材']:.1f}")

    # 使用進度條視覺化關鍵生存資源
    st.progress(max(0, min(100, res['食物'])), text=f"食物存量 ({res['食物']:.1f})")
    st.progress(max(0, min(100, res['水源'])), text=f"水源存量 ({res['水源']:.1f})")
    st.progress(max(0, min(100, res['氧氣'])), text=f"氧氣存量 ({res['氧氣']:.1f})")
    st.markdown("---")

def display_construction_panel():
    """顯示建築控制面板"""
    st.header("🏗️ 建設中心")
    st.write("點擊按鈕來建造新的設施。")
    
    cols = st.columns(len(BUILDING_SPECS))
    for i, (name, spec) in enumerate(BUILDING_SPECS.items()):
        with cols[i]:
            # 檢查是否有足夠資源建造
            can_build = all(st.session_state.resources[res] >= cost for res, cost in spec["cost"].items())
            
            if st.button(f"建造 {name}", key=f"build_{name}", disabled=not can_build, use_container_width=True):
                # 扣除資源
                for res, cost in spec["cost"].items():
                    st.session_state.resources[res] -= cost
                # 增加建築
                st.session_state.buildings[name] += 1
                # 如果是居住艙，增加人口容量
                if spec.get("provides") == "人口容量":
                    st.session_state.population_capacity += spec["capacity"]
                
                log_event(f"✅ 成功建造了一座新的 {name}！")
                st.rerun()

            # 顯示成本和效果
            cost_str = ", ".join([f"{v} {k}" for k, v in spec['cost'].items()])
            st.markdown(f"**成本:** {cost_str}")
            if "produces" in spec:
                prod_str = ", ".join([f"+{v} {k}/天" for k, v in spec['produces'].items()])
                st.markdown(f"**產出:** {prod_str}")
            if "provides" in spec:
                 st.markdown(f"**提供:** +{spec['capacity']} 人口容量")

def display_status_panel():
    """顯示殖民地狀態和推進按鈕"""
    st.header("🌍 殖民地狀態")
    st.metric("🗓️ 火星日", f"第 {st.session_state.game_day} 天")
    st.metric("🧑‍🚀 殖民者", f"{st.session_state.population} / {st.session_state.population_capacity}")

    st.markdown("---")
    
    if st.button("➡️ 推進到下一天", type="primary", use_container_width=True):
        run_next_day_simulation()
        check_game_status()
        st.rerun()

    st.markdown("---")
    st.subheader("🏢 已建設施")
    for name, count in st.session_state.buildings.items():
        st.write(f"- {name}: {count} 座")

def display_event_log():
    """顯示事件日誌"""
    st.subheader("📜 事件日誌")
    log_container = st.container(height=300)
    for event in reversed(st.session_state.event_log):
        log_container.info(event)

def display_game_over_screen():
    """顯示遊戲結束畫面"""
    st.error(f"### 遊戲結束：{st.session_state.game_day} 天")
    st.warning(f"**原因：{st.session_state.game_over_reason}**")
    st.image("https://placehold.co/600x300/2c3e50/ffffff?text=Colony+Lost", caption="殖民地已失聯...")
    
    if st.button("🚀 重新開始殖民計畫"):
        # 重置遊戲狀態
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

def display_victory_screen():
    """顯示勝利畫面"""
    st.success(f"### 任務成功！")
    st.balloons()
    st.markdown(f"你在 **{st.session_state.game_day}** 天內成功建立了擁有 **{st.session_state.population}** 位居民的自給自足殖民地！")
    st.image("https://placehold.co/600x300/4CAF50/ffffff?text=Colony+Thrives", caption="火星上的新家園！")

    if st.button("� 開啟新的殖民計畫"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- 遊戲邏輯 ---
def log_event(message):
    """新增事件到日誌"""
    st.session_state.event_log.append(f"第 {st.session_state.game_day} 天: {message}")
    if len(st.session_state.event_log) > 15:
        st.session_state.event_log.pop(0)

def run_next_day_simulation():
    """模擬一天的資源產出與消耗，並觸發隨機事件"""
    st.session_state.game_day += 1
    
    # 1. 計算總產出與總消耗
    production = {res: 0.0 for res in st.session_state.resources}
    consumption = {res: 0.0 for res in st.session_state.resources}
    
    for name, count in st.session_state.buildings.items():
        spec = BUILDING_SPECS[name]
        if "produces" in spec:
            for res, amount in spec["produces"].items():
                production[res] += amount * count
        if "consumes" in spec:
            for res, amount in spec["consumes"].items():
                consumption[res] += amount * count
    
    # 殖民者消耗
    for res, amount in COLONIST_CONSUMPTION.items():
        consumption[res] += amount * st.session_state.population

    # 2. 處理隨機事件
    event_modifier = {"電力": 1.0} # 事件對產出的影響係數
    if random.random() < 0.15: # 15% 機率發生沙塵暴
        log_event("⚠️ 一場強烈的沙塵暴來襲，太陽能板效率降低！")
        event_modifier["電力"] = 0.3 # 電力產出只剩30%
    
    if random.random() < 0.05: # 5% 機率發生隕石撞擊
        buildings_available = [b for b, c in st.session_state.buildings.items() if c > 0]
        if buildings_available:
            damaged_building = random.choice(buildings_available)
            st.session_state.buildings[damaged_building] -= 1
            log_event(f"💥 隕石撞擊！一座 {damaged_building} 被摧毀了！")

    # 3. 更新資源
    # 先處理電力，如果電力不足，其他設施可能無法運作
    net_power = (production["電力"] * event_modifier["電力"]) - consumption["電力"]
    st.session_state.resources["電力"] += net_power
    
    if st.session_state.resources["電力"] < 0:
        log_event("🚨 電力嚴重短缺！部分設施停止運作！")
        power_deficit_ratio = max(0, (production["電力"] * event_modifier["電力"]) / consumption["電力"])
        st.session_state.resources["電力"] = 0
    else:
        power_deficit_ratio = 1.0

    # 更新其他資源
    for res in ["水源", "食物", "氧氣"]:
        net_production = production[res] * power_deficit_ratio
        net_consumption = consumption[res]
        st.session_state.resources[res] += net_production - net_consumption

    # 4. 人口增長
    if st.session_state.population < st.session_state.population_capacity:
        # 資源充足時才有機會增加人口
        if st.session_state.resources["食物"] > st.session_state.population and st.session_state.resources["水源"] > st.session_state.population:
             if random.random() < 0.08: # 8% 機率增加一位殖民者
                 st.session_state.population += 1
                 log_event("🎉 好消息！一位新的殖民者誕生了！")


def check_game_status():
    """檢查遊戲是否結束或勝利"""
    res = st.session_state.resources
    if res["食物"] <= 0:
        st.session_state.game_over = True
        st.session_state.game_over_reason = "食物耗盡，殖民者無法生存。"
    elif res["水源"] <= 0:
        st.session_state.game_over = True
        st.session_state.game_over_reason = "水源耗盡，生命之源已斷絕。"
    elif res["氧氣"] <= 0:
        st.session_state.game_over = True
        st.session_state.game_over_reason = "氧氣耗盡，殖民地陷入窒息。"
    
    # 勝利條件
    if st.session_state.population >= 30:
        st.session_state.victory = True


if __name__ == "__main__":
    main()

