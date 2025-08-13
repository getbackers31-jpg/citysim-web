# -*- coding: utf-8 -*-
# 🚀 火星殖民地 v4.0 — Streamlit 從零重構（單檔版，含 safe_rerun 防呆 + slider 容量 0 保護）
# 設計目標：
# 1) 架構清晰：資料層(Data) / 規則層(Rules) / 介面層(UI) 分離
# 2) 可擴充：建築/科技/事件以資料驅動，邏輯模組化
# 3) 操作順暢：回合制，支援儲存/載入
# 4) 平衡簡潔：先做核心，再漸進擴充

import streamlit as st
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
import random, json, copy

# --- 安全的 rerun 防呆 ---
def safe_rerun():
    """兼容新舊 Streamlit 版本的 rerun"""
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

# ===============================
# ░░ Core Data Models
# ===============================

RES = ["電力", "水源", "食物", "氧氣", "鋼材", "科研"]

@dataclass
class BuildingSpec:
    name: str
    cost: Dict[str, float]
    produces: Dict[str, float] = field(default_factory=dict)  # 每棟基礎/回合產出
    consumes: Dict[str, float] = field(default_factory=dict)  # 每棟基礎/回合消耗
    workers_needed: int = 0  # 每棟需求工人數
    provides_capacity: int = 0  # 提供人口容量
    tags: List[str] = field(default_factory=list)  # 用於分類/過濾

@dataclass
class Tech:
    key: str
    name: str
    cost: int
    description: str
    # effects: list of (type, payload)
    # 支援： ("prod_mul", {"building":"溫室","resource":"食物","mul":1.3})
    #       ("cost_mul", {"resource":"鋼材","mul":0.85})
    #       ("unlock_building", {"name":"風力渦輪"})
    effects: List[Tuple[str, Dict]]
    unlocked: bool = False

@dataclass
class EventCard:
    key: str
    title: str
    text: str
    # options: [(label, effects)] where effects is list like in Tech
    options: List[Tuple[str, List[Tuple[str, Dict]]]]

@dataclass
class Colony:
    day: int = 0
    population: int = 5
    capacity: int = 5
    morale: float = 80.0
    resources: Dict[str, float] = field(default_factory=lambda: {
        "電力": 20.0, "水源": 50.0, "食物": 50.0,
        "氧氣": 100.0, "鋼材": 400.0, "科研": 0.0,
    })
    buildings: Dict[str, int] = field(default_factory=dict)
    assignments: Dict[str, int] = field(default_factory=dict)  # 建物名 → 已派工人數
    techs: Dict[str, Tech] = field(default_factory=dict)
    unlocked_buildings: Dict[str, BuildingSpec] = field(default_factory=dict)
    log: List[str] = field(default_factory=lambda: ["🚀 登陸成功！殖民地啟動。"])
    game_over: bool = False
    game_over_reason: str = ""
    victory: bool = False

# ===============================
# ░░ Data Definitions (Game Content)
# ===============================

BASE_BUILDINGS: Dict[str, BuildingSpec] = {
    "太陽能板": BuildingSpec("太陽能板", cost={"鋼材": 50}, produces={"電力": 6}),
    "鑽井機": BuildingSpec("鑽井機", cost={"鋼材": 80}, produces={"水源": 5}, consumes={"電力": 2}, workers_needed=1),
    "溫室": BuildingSpec("溫室", cost={"鋼材": 100}, produces={"食物": 4, "氧氣": 3}, consumes={"電力": 1, "水源": 2}, workers_needed=1),
    "居住艙": BuildingSpec("居住艙", cost={"鋼材": 120}, consumes={"電力": 1}, provides_capacity=5),
    "精煉廠": BuildingSpec("精煉廠", cost={"鋼材": 150}, produces={"鋼材": 10}, consumes={"電力": 4}, workers_needed=1),
    "核融合發電廠": BuildingSpec("核融合發電廠", cost={"鋼材": 400}, produces={"電力": 50}),
    "科研中心": BuildingSpec("科研中心", cost={"鋼材": 200}, produces={"科研": 2}, consumes={"電力": 5}, workers_needed=1),
}

BASE_TECHS: Dict[str, Tech] = {
    "improved_solar": Tech(
        key="improved_solar", name="改良太陽能板", cost=50,
        description="太陽能板電力產出 +20%",
        effects=[("prod_mul", {"building":"太陽能板","resource":"電力","mul":1.2})]
    ),
    "hydroponics": Tech(
        key="hydroponics", name="水培農業", cost=80,
        description="溫室食物產出 +30%",
        effects=[("prod_mul", {"building":"溫室","resource":"食物","mul":1.3})]
    ),
    "better_steel": Tech(
        key="better_steel", name="強化鋼材", cost=120,
        description="建築鋼材成本 -15%",
        effects=[("cost_mul", {"resource":"鋼材","mul":0.85})]
    ),
    "wind_turbine": Tech(
        key="wind_turbine", name="風力渦輪", cost=120,
        description="解鎖風力渦輪（受沙塵暴影響較小）",
        effects=[("unlock_building", {"name":"風力渦輪"})]
    ),
}

UNLOCKABLE_BUILDINGS: Dict[str, BuildingSpec] = {
    "風力渦輪": BuildingSpec("風力渦輪", cost={"鋼材": 160}, produces={"電力": 9}, tags=["風力"]),
}

EVENT_CARDS: List[EventCard] = [
    EventCard(
        key="ruins",
        title="遠征發現遺跡",
        text="工程隊在地平線發現一處金屬殘骸，疑似古代設備。",
        options=[
            ("拆解換鋼材", [("gain", {"鋼材": 60})]),
            ("研究換科研", [("gain", {"科研": 12}), ("morale", {"delta": +2})]),
        ],
    ),
    EventCard(
        key="microbe",
        title="沙塵微生物污染",
        text="實驗室報告：微生物可能影響水質。是否投入資源過濾？",
        options=[
            ("製作濾芯（花 40 鋼材）", [("spend", {"鋼材": 40}), ("morale", {"delta": +3})]),
            ("先觀望（有風險）", [("flag", {"key":"water_risk","days":3})]),
        ],
    ),
]

COLONIST_CONSUMPTION = {"食物": 0.2, "水源": 0.3, "氧氣": 0.5}

# ===============================
# ░░ Rules & Simulation
# ===============================

def new_game(seed: Optional[int] = None) -> Colony:
    if seed is not None:
        random.seed(seed)
    c = Colony()
    # 初始解鎖建築
    c.unlocked_buildings = copy.deepcopy(BASE_BUILDINGS)
    # 初始設施
    c.buildings = {k: 0 for k in BASE_BUILDINGS}
    c.buildings.update({"太陽能板": 1, "鑽井機": 1, "溫室": 1, "居住艙": 1})
    # 初始派工（只針對需要工人的）
    c.assignments = {k: 0 for k, v in c.unlocked_buildings.items() if v.workers_needed > 0}
    c.assignments.update({"鑽井機": 1, "溫室": 1})
    # 科技樹
    c.techs = copy.deepcopy(BASE_TECHS)
    return c


def sanitize(c: Colony):
    # 防止負值
    for r in RES:
        if r in c.resources and c.resources[r] < 0:
            c.resources[r] = 0.0
    # 派工上限 = 建築數 * 每棟需求
    for name, spec in c.unlocked_buildings.items():
        if spec.workers_needed > 0:
            cap = c.buildings.get(name, 0) * spec.workers_needed
            c.assignments[name] = max(0, min(c.assignments.get(name, 0), cap))
    # 人口容量 = 居住艙 * 5
    c.capacity = c.buildings.get("居住艙", 0) * BASE_BUILDINGS["居住艙"].provides_capacity


def tech_cost_multiplier(c: Colony) -> float:
    mul = 1.0
    t = c.techs.get("better_steel")
    if t and t.unlocked:
        for eff, payload in t.effects:
            if eff == "cost_mul" and payload.get("resource") == "鋼材":
                mul *= payload.get("mul", 1.0)
    return mul


def compute_active_ratio(c: Colony, name: str, spec: BuildingSpec, count: int, strike: bool, broken: Optional[str]) -> float:
    if count <= 0:
        return 0.0
    if spec.workers_needed <= 0:
        return 1.0
    if strike or broken == name:
        return 0.0
    capacity = count * spec.workers_needed
    assigned = min(c.assignments.get(name, 0), capacity)
    return assigned / capacity if capacity > 0 else 0.0


def apply_effects(c: Colony, effects: List[Tuple[str, Dict]]):
    for eff, payload in effects:
        if eff == "gain":
            for r, v in payload.items():
                c.resources[r] = c.resources.get(r, 0.0) + float(v)
        elif eff == "spend":
            for r, v in payload.items():
                c.resources[r] = max(0.0, c.resources.get(r, 0.0) - float(v))
        elif eff == "morale":
            c.morale = max(0, min(100, c.morale + float(payload.get("delta", 0))))
        elif eff == "flag":
            st.session_state.setdefault("flags", {})
            st.session_state.flags[payload["key"]] = payload.get("days", 1)
        elif eff == "unlock_building":
            bname = payload.get("name")
            if bname and bname in UNLOCKABLE_BUILDINGS:
                c.unlocked_buildings[bname] = UNLOCKABLE_BUILDINGS[bname]
                if bname not in c.buildings:
                    c.buildings[bname] = 0
                if UNLOCKABLE_BUILDINGS[bname].workers_needed > 0 and bname not in c.assignments:
                    c.assignments[bname] = 0


def roll_daily_events(c: Colony) -> Dict:
    effects = {"prod_buff": 1.0, "strike": False, "broken": None, "power_src_mod": {}}

    # 士氣事件
    if c.morale > 90 and random.random() < 0.12:
        effects["prod_buff"] = 1.5
        c.log.append(f"第 {c.day} 天：✨ 士氣爆表，今日產出 +50%！")
    elif c.morale < 30 and random.random() < 0.10:
        effects["strike"] = True
        c.log.append(f"第 {c.day} 天：✊ 罷工！需工人設施停擺。")

    # 天氣事件：沙塵暴影響太陽能
    if random.random() < 0.15:
        effects["power_src_mod"]["太陽能板"] = 0.35
        c.log.append(f"第 {c.day} 天：🌪️ 沙塵暴降低太陽能效率！")

    # 隨機設備故障
    worker_buildings = [n for n,s in c.unlocked_buildings.items() if s.workers_needed>0 and c.buildings.get(n,0)>0]
    if worker_buildings and random.random() < 0.08:
        effects["broken"] = random.choice(worker_buildings)
        c.log.append(f"第 {c.day} 天：🔧 {effects['broken']} 故障，今日停擺。")

    # 隕石：毀一座隨機有建的設施
    if random.random() < 0.05:
        built = [n for n,cnt in c.buildings.items() if cnt>0]
        if built:
            target = random.choice(built)
            c.buildings[target] -= 1
            c.log.append(f"第 {c.day} 天：☄️ 隕石擊中，{target} 毀損 1 座！")

    # 旗標倒數（如污染風險）
    if "flags" in st.session_state:
        exp = []
        for k,v in st.session_state.flags.items():
            st.session_state.flags[k] = v-1
            if st.session_state.flags[k] <= 0:
                exp.append(k)
        for k in exp:
            st.session_state.flags.pop(k, None)

    return effects


def compute_production(c: Colony, fx: Dict) -> Dict[str,float]:
    prod = {r:0.0 for r in RES}

    # 科技加成索引
    b_res_mul = {}  # building -> {res: mul}
    for t in c.techs.values():
        if not t.unlocked:
            continue
        for eff,p in t.effects:
            if eff == "prod_mul":
                b = p.get("building"); r = p.get("resource","*"); mul = p.get("mul",1.0)
                b_res_mul.setdefault(b, {})
                b_res_mul[b][r] = b_res_mul[b].get(r,1.0) * mul

    for name, count in c.buildings.items():
        if count <= 0:
            continue
        spec = c.unlocked_buildings.get(name) or BASE_BUILDINGS.get(name)
        if not spec:
            continue
        ratio = compute_active_ratio(c, name, spec, count, fx.get("strike",False), fx.get("broken"))
        if ratio <= 0:
            continue
        eff_units = count * ratio
        for r, base in spec.produces.items():
            mul = b_res_mul.get(name, {}).get(r, b_res_mul.get(name, {}).get("*",1.0))
            src_mod = fx.get("power_src_mod", {}).get(name, 1.0) if r=="電力" else 1.0
            prod[r] += base * eff_units * fx.get("prod_buff",1.0) * mul * src_mod

    return prod


def compute_consumption(c: Colony, fx: Dict) -> Tuple[Dict[str,float], Dict[str,float]]:
    cons_bld = {r:0.0 for r in RES}
    cons_col = {"食物":0.0,"水源":0.0,"氧氣":0.0}

    for name, count in c.buildings.items():
        if count <= 0:
            continue
        spec = c.unlocked_buildings.get(name) or BASE_BUILDINGS.get(name)
        ratio = compute_active_ratio(c, name, spec, count, fx.get("strike",False), fx.get("broken"))
        for r, base in spec.consumes.items():
            cons_bld[r] += base * count * ratio

    for r,a in COLONIST_CONSUMPTION.items():
        cons_col[r] += a * c.population

    return cons_bld, cons_col


def settle(c: Colony, prod: Dict[str,float], cons_bld: Dict[str,float], cons_col: Dict[str,float], fx: Dict):
    # 先算電力
    net_power = prod.get("電力",0.0) - cons_bld.get("電力",0.0)
    c.resources["電力"] += net_power

    if c.resources["電力"] < 0:
        # 電力不足 → 建築側產出/消耗縮放；殖民者不縮
        c.log.append(f"第 {c.day} 天：🚨 電力不足！設施降載運轉。")
        denom = cons_bld.get("電力",0.0)
        ratio = max(0.0, min(1.0, prod.get("電力",0.0) / denom)) if denom>0 else 0.0
        c.resources["電力"] = 0.0
    else:
        ratio = 1.0

    morale_mul = 0.7 + (c.morale/100.0)*0.6

    for r in ["水源","食物","氧氣","鋼材","科研"]:
        gain = prod.get(r,0.0) * morale_mul * ratio
        use_b = cons_bld.get(r,0.0) * ratio
        use_c = cons_col.get(r,0.0)
        c.resources[r] = c.resources.get(r,0.0) + gain - (use_b + use_c)
        if c.resources[r] < 0: c.resources[r] = 0.0


def end_of_day(c: Colony):
    # 士氣變化
    delta = 0
    if c.resources["食物"] < c.population: delta -= 5
    if c.resources["水源"] < c.population: delta -= 5
    if c.population > c.capacity: delta -= 10
    if delta == 0: delta += 1
    c.morale = max(0, min(100, c.morale + delta))

    # 自然增長
    if c.population < c.capacity and c.morale > 50 and c.resources["食物"]>c.population and c.resources["水源"]>c.population:
        if random.random() < 0.08:
            c.population += 1
            c.log.append(f"第 {c.day} 天：🍼 新殖民者誕生！人口 {c.population}")

    # 勝負檢查
    if c.resources["食物"] <= 0:
        c.game_over, c.game_over_reason = True, "食物耗盡"
    elif c.resources["水源"] <= 0:
        c.game_over, c.game_over_reason = True, "水源耗盡"
    elif c.resources["氧氣"] <= 0:
        c.game_over, c.game_over_reason = True, "氧氣耗盡"

    if c.population >= 30:
        c.victory = True


# ===============================
# ░░ UI Helpers
# ===============================

def meter_row(c: Colony):
    cols = st.columns(6)
    cols[0].metric("⚡ 電力", f"{c.resources['電力']:.1f}")
    cols[1].metric("💧 水源", f"{c.resources['水源']:.1f}")
    cols[2].metric("🌿 食物", f"{c.resources['食物']:.1f}")
    cols[3].metric("💨 氧氣", f"{c.resources['氧氣']:.1f}")
    cols[4].metric("🔩 鋼材", f"{c.resources['鋼材']:.1f}")
    cols[5].metric("🔬 科研", f"{c.resources['科研']:.1f}")


def show_assignment_panel(c: Colony):
    st.subheader("🧑‍🏭 殖民者指派")
    total_assigned = sum(c.assignments.values())
    unassigned = c.population - total_assigned
    st.info(f"可用殖民者 **{unassigned}** / 已指派 **{total_assigned}** / 總人口 **{c.population}**")

    need_workers = {n: s for n, s in c.unlocked_buildings.items() if s.workers_needed > 0}
    cols = st.columns(len(need_workers) or 1)

    for i, (n, spec) in enumerate(need_workers.items()):
        cap = int(c.buildings.get(n, 0) * spec.workers_needed)
        cur = int(min(c.assignments.get(n, 0), cap))
        label = f"{n} 工人 (容量 {cap})"

        if cap <= 0:
            # 某些 Streamlit 版本在 min==max 會拋錯，改為禁用 slider 並提示
            cols[i].slider(label, 0, 1, 0, key=f"asg_{n}", disabled=True)
            c.assignments[n] = 0
        else:
            nv = cols[i].slider(label, 0, cap, cur, key=f"asg_{n}")
            c.assignments[n] = int(nv)

    if sum(c.assignments.values()) > c.population:
        st.error("警告：指派超過總人口！")


def show_build_panel(c: Colony):
    st.subheader("🏗️ 建設中心")
    mul = tech_cost_multiplier(c)
    cols = st.columns(len(c.unlocked_buildings) or 1)
    for i,(name,spec) in enumerate(c.unlocked_buildings.items()):
        with cols[i]:
            cost_ok = True
            cost_strs = []
            for r,v in spec.cost.items():
                cost = v * (mul if r=="鋼材" else 1)
                cost_ok = cost_ok and c.resources.get(r,0)>=cost
                cost_strs.append(f"{int(cost)} {r}")
            st.caption(", ".join(cost_strs))
            if st.button(f"建造 {name} (+1)", key=f"build_{name}", disabled=not cost_ok, use_container_width=True):
                for r,v in spec.cost.items():
                    cost = v * (mul if r=="鋼材" else 1)
                    c.resources[r] -= cost
                c.buildings[name] = c.buildings.get(name,0)+1
                if spec.provides_capacity>0:
                    c.capacity += spec.provides_capacity
                c.log.append(f"第 {c.day} 天：✅ 新增 {name} 1 座")
                safe_rerun()
            st.write(f"現有：{c.buildings.get(name,0)}")


def show_research_panel(c: Colony):
    st.subheader("🔬 科研中心")
    cols = st.columns(len(c.techs) or 1)
    for i,(k,t) in enumerate(c.techs.items()):
        with cols[i]:
            if t.unlocked:
                st.success(f"✅ {t.name}")
            else:
                can = c.resources.get("科研",0)>=t.cost
                if st.button(f"研究 {t.name}", key=f"tech_{k}", disabled=not can, use_container_width=True):
                    c.resources["科研"] -= t.cost
                    c.techs[k].unlocked = True
                    apply_effects(c, t.effects)
                    c.log.append(f"第 {c.day} 天：🔬 研發完成：{t.name}")
                    safe_rerun()
                st.caption(f"成本：{t.cost} 科研")
                st.caption(t.description)


def show_right_panel(c: Colony):
    st.metric("🗓️ 火星日", f"第 {c.day} 天")
    emoji = "😊" if c.morale>70 else ("😐" if c.morale>30 else "😟")
    st.metric("士氣", f"{c.morale:.1f}% {emoji}")
    st.metric("人口", f"{c.population} / {c.capacity}")

    # Next day
    over = sum(c.assignments.values()) > c.population
    if st.button("➡️ 結束今天 / 進入下一天", disabled=over, type="primary", use_container_width=True):
        c.day += 1
        fx = roll_daily_events(c)
        prod = compute_production(c, fx)
        cons_bld, cons_col = compute_consumption(c, fx)
        settle(c, prod, cons_bld, cons_col, fx)
        end_of_day(c)
        sanitize(c)
        safe_rerun()

    st.markdown("---")
    st.subheader("📜 事件日誌")
    for e in reversed(c.log[-20:]):
        st.info(e)


def show_events_tab(c: Colony):
    st.subheader("🎴 事件卡（每日機率觸發，示例）")
    st.caption("本頁提供手動測試事件卡機制。實際遊戲會在回合中隨機出現。")
    for card in EVENT_CARDS:
        with st.expander(f"{card.title}"):
            st.write(card.text)
            for idx,(label, effects) in enumerate(card.options):
                if st.button(f"選擇：{label}", key=f"choose_{card.key}_{idx}"):
                    apply_effects(c, effects)
                    st.success(f"已選擇：{label}")


def show_state_tab(c: Colony):
    st.subheader("🧰 存檔 / 載入")
    save_json = json.dumps(asdict(c), ensure_ascii=False, indent=2)
    st.download_button("下載存檔 JSON", data=save_json, file_name="colony_save.json")

    up = st.file_uploader("上傳存檔 (JSON)")
    if up is not None:
        try:
            data = json.loads(up.read().decode("utf-8"))
            # 載入時需要把 Tech / BuildingSpec 重新構建
            c.day = data.get("day",0)
            c.population = data.get("population",5)
            c.capacity = data.get("capacity",5)
            c.morale = data.get("morale",80.0)
            c.resources = data.get("resources", {})
            c.buildings = data.get("buildings", {})
            c.assignments = data.get("assignments", {})
            c.log = data.get("log", [])
            c.game_over = data.get("game_over", False)
            c.game_over_reason = data.get("game_over_reason","")
            c.victory = data.get("victory", False)
            # 重建科技
            c.techs = copy.deepcopy(BASE_TECHS)
            for k,t in c.techs.items():
                t.unlocked = data.get("techs",{}).get(k,{}).get("unlocked", False)
                if t.unlocked:
                    apply_effects(c, t.effects)
            # 重建解鎖建築
            c.unlocked_buildings = copy.deepcopy(BASE_BUILDINGS)
            for b in data.get("unlocked_buildings",{}).keys():
                if b in UNLOCKABLE_BUILDINGS:
                    c.unlocked_buildings[b] = UNLOCKABLE_BUILDINGS[b]
            sanitize(c)
            st.success("載入成功！")
        except Exception as e:
            st.error(f"載入失敗：{e}")

# ===============================
# ░░ App Entrypoint (UI Layout)
# ===============================

st.set_page_config(page_title="🚀 火星殖民地 v4.0", layout="wide")

if "colony" not in st.session_state:
    st.session_state.colony = new_game()

c: Colony = st.session_state.colony
sanitize(c)

st.title("🚀 火星殖民地 v4.0 — 從零重構")
st.caption("設計分層、資料驅動、事件卡、存檔/載入，專為 Streamlit 單檔使用。")

# 頂部工具列
col_top1, col_top2, col_top3 = st.columns([0.6,0.2,0.2])
with col_top1:
    meter_row(c)
with col_top2:
    if st.button("🔄 重新開始 (新局)", use_container_width=True):
        st.session_state.colony = new_game()
        safe_rerun()
with col_top3:
    if st.button("🎲 新局(固定種子)", use_container_width=True):
        st.session_state.colony = new_game(seed=42)
        safe_rerun()

st.markdown("---")

# 主要版面
left, right = st.columns([0.72, 0.28])
with left:
    st.header("🛠️ 管理面板")
    tabs = st.tabs(["指派", "建設", "科研", "事件(測試)", "存檔/載入"])
    with tabs[0]:
        show_assignment_panel(c)
    with tabs[1]:
        show_build_panel(c)
    with tabs[2]:
        show_research_panel(c)
    with tabs[3]:
        show_events_tab(c)
    with tabs[4]:
        show_state_tab(c)

with right:
    st.header("🌍 殖民地狀態")
    show_right_panel(c)

# 結束畫面
if c.game_over:
    st.error(f"遊戲結束：{c.game_over_reason}")
if c.victory:
    st.success("任務成功！你讓殖民地邁向自給自足！")
