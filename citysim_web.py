# -*- coding: utf-8 -*-
# 🚀 火星殖民地計畫 v2.1 (最終穩定版)
import streamlit as st
import random

st.set_page_config(page_title="🚀 火星殖民地計畫", layout="wide")

# --- 遊戲設定 ---
# 建築規格：成本、產出、維護、所需工人
BUILDING_SPECS = {
    "太陽能板": {"cost": {"鋼材": 50}, "produces": {"電力": 5}, "consumes": {}, "workers_needed": 0},
    "鑽井機": {"cost": {"鋼材": 80}, "produces": {"水源": 5}, "consumes": {"電力": 2}, "workers_needed": 1},
    "溫室": {"cost": {"鋼材": 100}, "produces": {"食物": 4, "氧氣": 3}, "consumes": {"電力": 1, "水源": 2}, "workers_needed": 1},
    "居住艙": {"cost": {"鋼材": 120}, "provides": "人口容量", "capacity": 5, "consumes": {"電力": 1}, "workers_needed": 0},
    "精煉廠": {"cost": {"鋼材": 150}, "produces": {"鋼材": 10}, "consumes": {"電力": 4}, "workers_needed": 1},
    "核融合發電廠": {"cost": {"鋼材": 400}, "produces": {"電力": 50}, "consumes": {}, "workers_needed": 0},
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
        st.session_state.morale = 80.0
        
        st.session_state.resources = {
            "電力": 20.0, "水源": 50.0, "食物": 50.0,
            "氧氣": 100.0, "鋼材": 500.0,
        }
        
        st.session_state.buildings = {
            "太陽能板": 1, "鑽井機": 1, "溫室": 1,
            "居住艙": 1, "精煉廠": 0, "核融合發電廠": 0,
        }

        st.session_state.worker_assignments = {
            "鑽井機": 1,
            "溫室": 1,
            "精煉廠": 0,
        }
        
        st.session_state.event_log = ["🚀 登陸成功！火星殖民地計畫正式開始！"]
        st.session_state.game_over = False
        st.session_state.game_over_reason = ""
        st.session_state.victory = False
        
        st.session_state.special_event_effect = {}


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

    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        display_dashboard()
        display_worker_assignment_panel()
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

    max_resource_for_progress = 200.0
    food_progress = max(0.0, min(1.0, res['食物'] / max_resource_for_progress))
    water_progress = max(0.0, min(1.0, res['水源'] / max_resource_for_progress))
    oxygen_progress = max(0.0, min(1.0, res['氧氣'] / max_resource_for_progress))
    st.progress(food_progress, text=f"食物存量 ({res['食物']:.1f})")
    st.progress(water_progress, text=f"水源存量 ({res['水源']:.1f})")
    st.progress(oxygen_progress, text=f"氧氣存量 ({res['氧氣']:.1f})")
    st.markdown("---")

def display_worker_assignment_panel():
    """顯示工人指派面板"""
    st.header("🧑‍🏭 殖民者指派中心")
    
    # 每次渲染前都校正工人指派，確保數據一致性
    for name, current_assignment in st.session_state.worker_assignments.items():
        spec = BUILDING_SPECS.get(name)
        if not spec or spec["workers_needed"] == 0: continue
        max_workers_for_building = st.session_state.buildings.get(name, 0) * spec["workers_needed"]
        if current_assignment > max_workers_for_building:
            st.session_state.worker_assignments[name] = max_workers_for_building

    total_assigned_workers = sum(st.session_state.worker_assignments.values())
    unassigned_workers = st.session_state.population - total_assigned_workers
    
    st.info(f"可用殖民者: **{unassigned_workers}** / 已指派: **{total_assigned_workers}** / 總人口: **{st.session_state.population}**")

    worker_cols = st.columns(3)
    
    assignable_buildings = {name: spec for name, spec in BUILDING_SPECS.items() if spec["workers_needed"] > 0}
    
    for i, (name, spec) in enumerate(assignable_buildings.items()):
        max_workers_for_building = st.session_state.buildings[name] * spec["workers_needed"]
        current_assignment = st.session_state.worker_assignments.get(name, 0)
        
        safe_value = min(current_assignment, max_workers_for_building)
        
        new_assignment = worker_cols[i].slider(
            f"指派至 {name} (容量: {max_workers_for_building})",
            min_value=0,
            max_value=max_workers_for_building,
            value=safe_value,
            key=f"assign_{name}"
        )
        st.session_state.worker_assignments[name] = new_assignment

    final_total_assigned = sum(st.session_state.worker_assignments.values())
    if final_total_assigned > st.session_state.population:
        st.error("警告：指派的殖民者總數超過了總人口！請重新分配。")
    st.markdown("---")


def display_construction_panel():
    """顯示建築控制面板"""
    st.header("🏗️ 建設中心")
    cols = st.columns(len(BUILDING_SPECS))
    for i, (name, spec) in enumerate(BUILDING_SPECS.items()):
        with cols[i]:
            can_build = all(st.session_state.resources[res] >= cost for res, cost in spec["cost"].items())
            if st.button(f"建造 {name}", key=f"build_{name}", disabled=not can_build, use_container_width=True):
                for res, cost in spec["cost"].items(): st.session_state.resources[res] -= cost
                st.session_state.buildings[name] += 1
                if spec.get("provides") == "人口容量": st.session_state.population_capacity += spec["capacity"]
                log_event(f"✅ 成功建造了一座新的 {name}！")
                st.rerun()

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
    
    morale_emoji = "😊" if st.session_state.morale > 70 else "😐" if st.session_state.morale > 30 else "😟"
    st.metric("士氣", f"{st.session_state.morale:.1f} % {morale_emoji}")

    st.markdown("---")
    
    total_assigned_workers = sum(st.session_state.worker_assignments.values())
    is_over_assigned = total_assigned_workers > st.session_state.population

    if st.button("➡️ 推進到下一天", type="primary", use_container_width=True, disabled=is_over_assigned):
        run_next_day_simulation()
        check_game_status()
        st.rerun()

    st.markdown("---")
    st.subheader("🏢 已建設施")
    for name, count in st.session_state.buildings.items():
        st.write(f"- {name}: {count} 座")

def display_event_log():
    st.subheader("📜 事件日誌")
    log_container = st.container(height=300)
    for event in reversed(st.session_state.event_log):
        log_container.info(event)

def display_game_over_screen():
    st.error(f"### 遊戲結束：{st.session_state.game_day} 天")
    st.warning(f"**原因：{st.session_state.game_over_reason}**")
    if st.button("🚀 重新開始殖民計畫"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

def display_victory_screen():
    st.success(f"### 任務成功！")
    st.balloons()
    st.markdown(f"你在 **{st.session_state.game_day}** 天內成功建立了擁有 **{st.session_state.population}** 位居民的自給自足殖民地！")
    if st.button("🚀 開啟新的殖民計畫"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- 遊戲邏輯 ---
def log_event(message):
    st.session_state.event_log.append(f"第 {st.session_state.game_day} 天: {message}")
    if len(st.session_state.event_log) > 15: st.session_state.event_log.pop(0)

def trigger_special_event():
    """根據士氣觸發特殊事件，並返回效果字典"""
    morale = st.session_state.morale
    effect = {}

    if morale > 90 and random.random() < 0.15:
        effect['production_buff'] = 1.5
        log_event("✨ 士氣高昂，殖民者們充滿幹勁！今日所有設施產出增加 50%！")
    
    elif morale < 30 and random.random() < 0.20:
        event_type = random.choice(["罷工", "疾病", "設施故障"])
        if event_type == "罷工":
            effect['strike'] = True
            log_event("🚨 士氣低落，工人們發起了罷工！本日所有需要指派的設施產出歸零。")
        elif event_type == "疾病" and st.session_state.population > 1:
            st.session_state.population -= 1
            log_event("💔 殖民地爆發了疾病，一名殖民者不幸去世...")
        elif event_type == "設施故障":
            possible_broken = [k for k, v in st.session_state.buildings.items() if v > 0 and BUILDING_SPECS[k]["workers_needed"] > 0]
            if possible_broken:
                broken_building = random.choice(possible_broken)
                effect['broken'] = broken_building
                log_event(f"🔧 一座 {broken_building} 發生嚴重故障，本日完全停止運作。")
    
    st.session_state.special_event_effect = effect

def run_next_day_simulation():
    st.session_state.game_day += 1
    trigger_special_event()
    event_effect = st.session_state.special_event_effect

    # 1. 計算產出
    production = {res: 0.0 for res in st.session_state.resources}
    prod_buff = event_effect.get('production_buff', 1.0)

    for name in ["太陽能板", "核融合發電廠"]:
        count = st.session_state.buildings[name]
        spec = BUILDING_SPECS[name]
        if "produces" in spec:
            for res, amount in spec["produces"].items():
                production[res] += amount * count * prod_buff

    if not event_effect.get('strike'):
        for name, workers in st.session_state.worker_assignments.items():
            if event_effect.get('broken') == name: continue
            spec = BUILDING_SPECS[name]
            if "produces" in spec:
                for res, amount in spec["produces"].items():
                    production[res] += amount * workers * prod_buff

    # 2. 計算消耗
    consumption = {res: 0.0 for res in st.session_state.resources}
    for name, count in st.session_state.buildings.items():
        spec = BUILDING_SPECS[name]
        if "consumes" in spec:
            for res, amount in spec["consumes"].items():
                consumption[res] += amount * count
    for res, amount in COLONIST_CONSUMPTION.items():
        consumption[res] += amount * st.session_state.population

    # 3. 處理常規隨機事件
    event_modifier = {"電力": 1.0}
    if random.random() < 0.15:
        log_event("⚠️ 一場強烈的沙塵暴來襲，太陽能板效率降低！")
        event_modifier["電力"] = 0.3
    if random.random() < 0.05:
        buildings_available = [b for b, c in st.session_state.buildings.items() if c > 0 and b in st.session_state.worker_assignments]
        if buildings_available:
            damaged_building = random.choice(buildings_available)
            st.session_state.buildings[damaged_building] -= 1
            log_event(f"💥 隕石撞擊！一座 {damaged_building} 被摧毀了！")
            # *** BUG 修正 v1.8：在事件發生當下立刻校正狀態 ***
            spec = BUILDING_SPECS[damaged_building]
            new_max_workers = st.session_state.buildings[damaged_building] * spec["workers_needed"]
            if st.session_state.worker_assignments[damaged_building] > new_max_workers:
                st.session_state.worker_assignments[damaged_building] = new_max_workers


    # 4. 更新士氣
    morale_change = 0
    if st.session_state.resources["食物"] < st.session_state.population: morale_change -= 5
    if st.session_state.resources["水源"] < st.session_state.population: morale_change -= 5
    if st.session_state.population > st.session_state.population_capacity: morale_change -= 10
    if morale_change == 0: morale_change += 1 
    st.session_state.morale = max(0, min(100, st.session_state.morale + morale_change))
    morale_modifier = 0.7 + (st.session_state.morale / 100) * 0.6 

    # 5. 更新資源
    net_power = (production["電力"] * event_modifier["電力"]) - consumption["電力"]
    st.session_state.resources["電力"] += net_power
    
    power_deficit_ratio = 1.0
    if st.session_state.resources["電力"] < 0:
        log_event("🚨 電力嚴重短缺！部分設施停止運作！")
        if consumption["電力"] > 0:
            power_deficit_ratio = max(0, (production["電力"] * event_modifier["電力"]) / consumption["電力"])
        else:
            power_deficit_ratio = 0
        st.session_state.resources["電力"] = 0

    for res in ["水源", "食物", "氧氣", "鋼材"]:
        if res in production:
            net_production = production[res] * power_deficit_ratio * morale_modifier
            net_consumption = consumption.get(res, 0)
            st.session_state.resources[res] += net_production - net_consumption

    # 6. 人口增長
    if st.session_state.population < st.session_state.population_capacity and st.session_state.morale > 50:
        if st.session_state.resources["食物"] > st.session_state.population and st.session_state.resources["水源"] > st.session_state.population:
             if random.random() < 0.08:
                 st.session_state.population += 1
                 log_event("🍼 好消息！一位新的殖民者誕生了！")

def check_game_status():
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
    if st.session_state.population >= 30:
        st.session_state.victory = True

if __name__ == "__main__":
    main()
