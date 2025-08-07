# -*- coding: utf-8 -*-
# 🚀 火星殖民地計畫 v2.0（含特殊事件系統、產出強化）
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
        # --- 特殊事件狀態 ---
        st.session_state.special_event = None
        st.session_state.special_event_days_left = 0
        st.session_state.special_event_broken = None
        st.session_state.special_event_broken_left = 0

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
            # 可於此自動升級一項科技（進階開發預留）
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
            broken = random.choice([k for k, v in st.session_state.buildings.items() if v > 0])
            st.session_state.special_event_broken = broken
            st.session_state.special_event_broken_left = 1
            effect_msg = f"{broken} 發生嚴重故障，本日完全無產出。"
            effect['broken'] = broken
    if special_event:
        st.session_state.special_event = special_event
        st.session_state.special_event_days_left = special_event_days
        log_event(f"⚡ 特殊事件：{special_event}！{effect_msg}")
    return effect

# ...（main, 其餘函式如你現有架構）...

# --- 核心邏輯 ---
def run_next_day_simulation():
    st.session_state.game_day += 1
    # --- 特殊事件觸發 ---
    event_effect = trigger_special_event()
    production = {res: 0.0 for res in st.session_state.resources}
    prod_buff = event_effect.get('production_buff', 1.0)
    if event_effect.get('strike'):
        pass  # 產出全為0，不做任何累加
    else:
        for name in ["太陽能板", "核融合發電廠"]:
            count = st.session_state.buildings[name]
            spec = BUILDING_SPECS[name]
            if "produces" in spec:
                for res, amount in spec["produces"].items():
                    production[res] += amount * count * prod_buff
        for name, workers in st.session_state.worker_assignments.items():
            spec = BUILDING_SPECS[name]
            # 設施若本日故障，跳過產出
            if event_effect.get('broken') == name:
                continue
            if "produces" in spec:
                for res, amount in spec["produces"].items():
                    production[res] += amount * workers * prod_buff
    # （以下消耗、隨機事件、資源更新、人口等同原本）
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
        if st.session_state.resources["食物"] > st.session_state.population and st.session_state.resources["水源"] > st.session_state.population:
            if random.random() < 0.08:
                st.session_state.population += 1
                log_event("🍼 好消息！一位新的殖民者誕生了！")
                if __name__ == "__main__":
    main()
