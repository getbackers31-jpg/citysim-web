# -*- coding: utf-8 -*-
# 🚀 火星殖民地計畫 v2.0（含特殊事件系統、產出強化完整版）
import streamlit as st
import random

st.set_page_config(page_title="🚀 火星殖民地計畫", layout="wide")

# --- 遊戲設定 ---
BUILDING_SPECS = {
    "太陽能板": {"cost": {"鋼材": 50}, "produces": {"電力": 5}, "consumes": {}, "workers_needed": 0},
    "鑽井機": {"cost": {"鋼材": 80}, "produces": {"水源": 5}, "consumes": {"電力": 2}, "workers_needed": 1},
    "溫室": {"cost": {"鋼材": 100}, "produces": {"食物": 4, "氧氣": 3}, "consumes": {"電力": 1, "水源": 2}, "workers_needed": 1},
    "居住艙": {"cost": {"鋼材": 120}, "provides": "人口容量", "capacity": 5, "consumes": {"電力": 1}, "workers_needed": 0},
    "精煉廠": {"cost": {"鋼材": 150}, "produces": {"鋼材": 10}, "consumes": {"電力": 4}, "workers_needed": 1},
    "核融合發電廠": {"cost": {"鋼材": 400}, "produces": {"電力": 50}, "consumes": {}, "workers_needed": 0},
}

COLONIST_CONSUMPTION = {
    "食物": 0.2,
    "水源": 0.3,
    "氧氣": 0.5,
}

# --- 初始化遊戲 ---
def initialize_game():
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
        st.session_state.special_event = None
        st.session_state.special_event_days_left = 0
        st.session_state.special_event_broken = None
        st.session_state.special_event_broken_left = 0

# --- 工人指派校正 ---
def sanitize_worker_assignments():
    for name, current_assignment in st.session_state.worker_assignments.items():
        spec = BUILDING_SPECS.get(name)
        if not spec or spec["workers_needed"] == 0:
            continue
        max_workers_for_building = st.session_state.buildings.get(name, 0) * spec["workers_needed"]
        if current_assignment > max_workers_for_building:
            st.session_state.worker_assignments[name] = max_workers_for_building

# --- 特殊事件觸發 ---
def trigger_special_event():
    morale = st.session_state.morale
    special_event = None
    special_event_days = 0
    effect_msg = None
    effect = {}
    # 高士氣正向事件
    if morale > 90 and random.random() < 0.15:
        if random.random() < 0.5:
            special_event = "團隊激勵"
            special_event_days = 1
            effect_msg = "全設施今日產出+50%！"
            effect['production_buff'] = 1.5
        else:
            special_event = "科研突破"
            special_event_days = 0
            effect_msg = "科技大突破！隨機科技已完成。"
    # 低士氣負面事件
    elif morale < 30 and random.random() < 0.20:
        r = random.random()
        if r < 0.34:
            special_event = "罷工"
            special_event_days = 1
            effect_msg = "工人罷工！本日所有派工設施產出歸零。"
            effect['strike'] = True
        elif r < 0.67:
            special_event = "疾病"
            special_event_days = 0
            if st.session_state.population > 1:
                st.session_state.population -= 1
                effect_msg = "疾病爆發，一名殖民者死亡..."
            else:
                effect_msg = "疾病爆發，幸運地沒有人受害。"
        else:
            special_event = "設施故障"
            special_event_days = 1
            possible = [k for k, v in st.session_state.buildings.items() if v > 0]
            if possible:
                broken = random.choice(possible)
                st.session_state.special_event_broken = broken
                st.session_state.special_event_broken_left = 1
                effect_msg = f"{broken} 發生嚴重故障，本日完全無產出。"
                effect['broken'] = broken
    if special_event:
        st.session_state.special_event = special_event
        st.session_state.special_event_days_left = special_event_days
        log_event(f"⚡ 特殊事件：{special_event}！{effect_msg}")
    return effect

# --- 日誌 ---
def log_event(message):
    if len(st.session_state.event_log) >= 15:
        st.session_state.event_log.pop(0)
    st.session_state.event_log.append(f"第 {st.session_state.game_day} 天: {message}")

# --- 主程式 ---
def main():
    initialize_game()
    sanitize_worker_assignments()
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

# --- 儀表板 ---
def display_dashboard():
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
    prog_cols = st.columns(3)
    prog_cols[0].progress(food_progress, text=f"食物存量 ({res['食物']:.1f})")
    prog_cols[1].progress(water_progress, text=f"水源存量 ({res['水源']:.1f})")
    prog_cols[2].progress(oxygen_progress, text=f"氧氣存量 ({res['氧氣']:.1f})")
    st.markdown("---")

# --- 工人指派面板 ---
def display_worker_assignment_panel():
    st.header("🧑‍🏭 殖民者指派中心")
    total_assigned_workers = sum(st.session_state.worker_assignments.values())
    unassigned_workers = st.session_state.population - total_assigned_workers
    st.info(f"可用殖民者: **{unassigned_workers}** / 已指派: **{total_assigned_workers}** / 總人口: **{st.session_state.population}**")
    worker_cols = st.columns(3)
    assignable_buildings = {name: spec for name, spec in BUILDING_SPECS.items() if spec["workers_needed"] > 0}
    col_idx = 0
    for name, spec in assignable_buildings.items():
        max_workers_for_building = st.session_state.buildings[name] * spec["workers_needed"]
        if max_workers_for_building == 0:
            st.session_state.worker_assignments[name] = 0
            continue
        current_assignment = st.session_state.worker_assignments.get(name, 0)
        safe_value = min(current_assignment, max_workers_for_building)
        new_assignment = worker_cols[col_idx].slider(
            f"指派至 {name} (容量: {max_workers_for_building})",
            min_value=0,
            max_value=max_workers_for_building,
            value=safe_value,
            key=f"assign_{name}"
        )
        st.session_state.worker_assignments[name] = new_assignment
        col_idx += 1
    final_total_assigned = sum(st.session_state.worker_assignments.values())
    if final_total_assigned > st.session_state.population:
        st.error("警告：指派的殖民者總數超過了總人口！請重新分配。")
    st.markdown("---")

# --- 建築建設面板 ---
def display_construction_panel():
    st.header("🏗️ 建設中心")
    cols = st.columns(len(BUILDING_SPECS))
    for i, (name, spec) in enumerate(BUILDING_SPECS.items()):
        with cols[i]:
            can_build = all(st.session_state.resources[res] >= cost for res, cost in spec["cost"].items())
            if st.button(f"建造 {name}", key=f"build_{name}", disabled=not can_build, use_container_width=True):
                for res, cost in spec["cost"].items():
                    st.session_state.resources[res] -= cost
                st.session_state.buildings[name] += 1
                if spec.get("provides") == "人口容量":
                    st.session_state.population_capacity += spec["capacity"]
                log_event(f"✅ 成功建造了一座新的 {name}！")
                st.rerun()
            cost_str = ", ".join([f"{v} {k}" for k, v in spec['cost'].items()])
            st.markdown(f"**成本:** {cost_str}")
            if "produces" in spec:
                prod_str = ", ".join([f"+{v} {k}/天" for k, v in spec['produces'].items()])
                st.markdown(f"**產出:** {prod_str}")
            if "provides" in spec:
                st.markdown(f"**提供:** +{spec['capacity']} 人口容量")

# --- 狀態面板 ---
def display_status_panel():
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

# --- 事件日誌 ---
def display_event_log():
    st.subheader("📜 事件日誌")
    log_container = st.container(height=300)
    for event in reversed(st.session_state.event_log):
        log_container.info(event)

# --- 遊戲結束畫面 ---
def display_game_over_screen():
    st.error(f"### 遊戲結束：{st.session_state.game_day} 天")
    st.warning(f"**原因：{st.session_state.game_over_reason}**")
    if st.button("🚀 重新開始殖民計畫"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- 任務成功畫面 ---
def display_victory_screen():
    st.success(f"### 任務成功！")
    st.balloons()
    st.markdown(f"你在 **{st.session_state.game_day}** 天內成功建立了擁有 **{st.session_state.population}** 位居民的自給自足殖民地！")
    if st.button("🚀 開啟新的殖民計畫"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- 核心邏輯 ---
def run_next_day_simulation():
    st.session_state.game_day += 1
    event_effect = trigger_special_event()
    production = {res: 0.0 for res in st.session_state.resources}
    prod_buff = event_effect.get('production_buff', 1.0)
    if event_effect.get('strike'):
        pass
    else:
        for name in ["太陽能板", "核融合發電廠"]:
            count = st.session_state.buildings[name]
            spec = BUILDING_SPECS[name]
            if "produces" in spec:
                for res, amount in spec["produces"].items():
                    production[res] += amount * count * prod_buff
        for name, workers in st.session_state.worker_assignments.items():
            spec = BUILDING_SPECS[name]
            if event_effect.get('broken') == name:
                continue
            if "produces" in spec:
                for res, amount in spec["produces"].items():
                    production[res] += amount * workers * prod_buff
    # --- 消耗、隨機事件、資源結算、人口等同舊版 ---
    consumption = {res: 0.0 for res in st.session_state.resources}
    for name, count in st.session_state.buildings.items():
        spec = BUILDING_SPECS[name]
        if "consumes" in spec:
            for res, amount in spec["consumes"].items():
                consumption[res] += amount * count
    for res, amount in COLONIST_CONSUMPTION.items():
        consumption[res] += amount * st.session_state.population
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
    morale_change = 0
    if st.session_state.resources["食物"] < st.session_state.population:
        morale_change -= 5
    if st.session_state.resources["水源"] < st.session_state.population:
        morale_change -= 5
    if st.session_state.population > st.session_state.population_capacity:
        morale_change -= 10
    if morale_change == 0:
        morale_change += 1
    st.session_state.morale = max(0, min(100, st.session_state.morale + morale_change))
    morale_modifier = 0.7 + (st.session_state.morale / 100) * 0.6
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
    if st.session_state.population < st.session_state.population_capacity and st.session_state.morale > 50:
        if st.session_state.resources["食物"] > st.session_state.population and st.session_state.resources["水源"] >
