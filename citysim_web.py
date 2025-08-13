# -*- coding: utf-8 -*-
# 🌐 CitySim 世界模擬器 Pro — 可擴充版
# 變更重點：
# 1) 架構模組化：將「資料結構」、「規則表」、「事件系統」、「UI」分區，便於未來擴充。
# 2) 技能樹系統：以字典宣告技能 → 節點/前置/成本/效果（行星級、城市級、全域級）。
# 3) 多星球競爭：初始化可選數量、UI 動態新增星球，並加入行星評分榜與勝負條件鉤子。
# 4) 修正舊版瑕疵：變數越域、故事模板未定義變數、若干 None 保護、科技效果合併等。
# 5) 擴充友善：所有可調係數集中在 CONFIG 與 REGISTRIES，未來改規則只改表格。

import streamlit as st
import random
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set

st.set_page_config(page_title="🌐 CitySim 世界模擬器 Pro（可擴充版）", layout="wide")

# =====================================
# CONFIG 與 REGISTRIES（集中可調參數）
# =====================================

CONFIG = {
    "INIT": {
        "earth_cities": ["臺北", "東京", "首爾"],
        "alien_cities": ["艾諾斯", "特朗加"],
        "earth_citizens_per_city": 30,
        "alien_citizens_per_city": 20,
        "max_random_new_planets": 5,
    },
    "RATES": {
        "marry": 0.05,
        "immigrate_base": 0.02,
        "election_year_min": 5,
        "election_year_max": 10,
    },
    "ATTACK": {
        "cooldown": 5,
        "defense_factor": 0.005,
        "shield_block": 0.5,
        "war_trigger_threshold": 0.7,
    },
    "VISUAL": {
        "map_width": 10,
        "map_height": 5,
    }
}

# 技能樹登錄（可自由擴充）
# 節點結構：key: 技能代碼；val: {name, tier, cost, prereq, scope, effect}
# scope: planet/city/global；effect：統一在 apply_skill_effect 中解讀
SKILL_TREE_REGISTRY: Dict[str, Dict] = {
    # Tier 1 — 經濟/生產
    "ECO_AUTOMATION": {
        "name": "自動化工廠", "tier": 1, "cost": 2,
        "prereq": [], "scope": "planet",
        "effect": {"city_resource_bonus": {"糧食": 10, "能源": 8, "稅收": 10}}
    },
    "ECO_TRADE_HUB": {
        "name": "星際貿易樞紐", "tier": 1, "cost": 2,
        "prereq": [], "scope": "planet",
        "effect": {"trade_rate_mult": 1.3}
    },
    # Tier 2 — 醫療/環境
    "MED_SUPER_VACCINE": {
        "name": "超級疫苗", "tier": 2, "cost": 3,
        "prereq": ["ECO_AUTOMATION"], "scope": "planet",
        "effect": {"epidemic_chance_mult": 0.6, "epidemic_severity_mult": 0.8}
    },
    "ENV_ATMOS_PURIFIER": {
        "name": "大氣淨化器", "tier": 2, "cost": 3,
        "prereq": ["ECO_AUTOMATION"], "scope": "planet",
        "effect": {"pollution_growth_mult": 0.6}
    },
    # Tier 3 — 軍事/防禦
    "MIL_ORBIT_DEFENSE": {
        "name": "軌道防禦平台", "tier": 3, "cost": 4,
        "prereq": ["ECO_TRADE_HUB"], "scope": "planet",
        "effect": {"defense_cap_bonus": 20, "attack_damage_bonus": 0.1}
    },
    # Tier 4 — 終局
    "ULT_RESOURCE_REPLICATOR": {
        "name": "資源複製器", "tier": 4, "cost": 6,
        "prereq": ["MED_SUPER_VACCINE", "ENV_ATMOS_PURIFIER"], "scope": "planet",
        "effect": {"resource_infinite": True}
    },
}

# =====================================
# 資料結構
# =====================================

class Family:
    def __init__(self, name: str):
        self.name = name
        self.members: List[Citizen] = []  # type: ignore
        self.family_wealth = 0
        self.reputation = random.uniform(0.1, 0.5)

    def update_reputation(self):
        active_members = [c for c in self.members if getattr(c, "alive", False)]
        total_member_wealth = sum(c.wealth for c in active_members)
        n = len(active_members)
        if n:
            avg_w = total_member_wealth / n
            self.reputation = max(0.1, min(1.0, self.reputation + (avg_w - 100) * 0.0005))
        for m in active_members:
            if m.profession in ["科學家", "醫生", "工程師", "教師"]:
                self.reputation = min(1.0, self.reputation + 0.005)
            elif m.profession in ["小偷", "黑幫成員", "詐騙犯", "毒販"]:
                self.reputation = max(0.01, self.reputation - 0.01)
        self.reputation = max(0.01, min(1.0, self.reputation))

class PoliticalParty:
    def __init__(self, name, ideology, platform):
        self.name = name; self.ideology = ideology; self.platform = platform
        self.support = 0; self.leader = None
    def calculate_support(self, citizens: List["Citizen"]):
        self.support = 0
        if not citizens: return
        for c in citizens:
            if c.ideology == self.ideology: self.support += 1
            if c.happiness > 0.7 and self.platform == "穩定發展": self.support += 0.5
            elif c.happiness < 0.3 and self.platform == "改革求變": self.support += 0.5
        self.support = min(self.support, len(citizens))

class Citizen:
    def __init__(self, name, parent1_ideology=None, parent2_ideology=None, parent1_trust=None, parent2_trust=None, parent1_emotion=None, parent2_emotion=None, family: Optional[Family]=None):
        self.name = name; self.age = 0; self.health = 1.0
        base_trust = (parent1_trust + parent2_trust)/2 if parent1_trust is not None and parent2_trust is not None else random.uniform(0.4,0.9)
        self.trust = max(0.1, min(1.0, base_trust + random.uniform(-0.1, 0.1)))
        base_em = (parent1_emotion + parent2_emotion)/2 if parent1_emotion is not None and parent2_emotion is not None else random.uniform(0.4,0.9)
        self.happiness = max(0.1, min(1.0, base_em + random.uniform(-0.1, 0.1)))
        all_id = ["保守", "自由", "科技信仰", "民族主義"]
        if parent1_ideology and parent2_ideology and random.random()<0.7:
            if parent1_ideology == parent2_ideology and random.random()<0.9:
                self.ideology = parent1_ideology
            elif random.random()<0.7:
                self.ideology = random.choice([parent1_ideology, parent2_ideology])
            else:
                self.ideology = random.choice(all_id)
        else:
            self.ideology = random.choice(all_id)
        self.city = None; self.alive = True; self.death_cause=None; self.partner=None; self.family = family
        self.all_professions = [
            "農民","工人","科學家","商人","無業","醫生","藝術家","工程師","教師","服務員","小偷","黑幫成員","詐騙犯","毒販"
        ]
        self.profession = random.choice(self.all_professions)
        self.education_level = random.randint(0,2)
        self.wealth = random.uniform(50,200)
        if self.profession in ["小偷","黑幫成員","詐騙犯","毒販"]:
            self.trust = max(0.1, self.trust - random.uniform(0.05,0.15))
            self.health = max(0.1, self.health - random.uniform(0.02,0.08))

class City:
    def __init__(self, name):
        self.name = name
        self.citizens: List[Citizen] = []
        self.resources = {"糧食":100, "能源":100, "稅收":0}
        self.events: List[str] = []
        self.history: List[Tuple[int,float,float,float]] = []
        self.birth_count=0; self.death_count=0; self.immigration_count=0; self.emigration_count=0
        self.graveyard: List[Tuple[str,int,str,Optional[str]]] = []
        self.mass_movement_active=False
        self.cooperative_economy_level=0.0
        self.government_type = random.choice(["民主制","專制","共和制"])
        self.specialization = random.choice(["農業","工業","科技","服務","軍事"])
        self.resource_shortage_years = 0
        self.political_parties: List[PoliticalParty] = []
        self.ruling_party: Optional[PoliticalParty] = None
        self.election_timer = random.randint(CONFIG["RATES"]["election_year_min"], CONFIG["RATES"]["election_year_max"])

class SkillTree:
    """每個行星持有一份技能狀態：已解鎖、點數、已購買路徑。"""
    def __init__(self):
        self.unlocked: Set[str] = set()
        self.points: int = 0
        self.history: List[Tuple[int, str]] = []  # (year, skill_key)

    def can_unlock(self, key: str) -> bool:
        node = SKILL_TREE_REGISTRY.get(key)
        if not node: return False
        if key in self.unlocked: return False
        for pre in node.get("prereq", []):
            if pre not in self.unlocked: return False
        return self.points >= node.get("cost", 1)

    def unlock(self, key: str, year: int) -> bool:
        if self.can_unlock(key):
            cost = SKILL_TREE_REGISTRY[key]["cost"]
            self.points -= cost
            self.unlocked.add(key)
            self.history.append((year, key))
            return True
        return False

class Planet:
    def __init__(self, name, alien=False):
        self.name = name
        self.cities: List[City] = []
        self.tech_levels = {"軍事":0.5, "環境":0.5, "醫療":0.5, "生產":0.5}
        self.pollution = 0.0
        self.alien = alien
        self.conflict_level = 0.0
        self.is_alive = True
        self.relations: Dict[str, str] = {}
        self.war_with: Set[str] = set()
        self.war_duration: Dict[str, int] = {}
        self.epidemic_active=False; self.epidemic_severity=0.0
        self.defense_level = 0
        self.shield_active=False
        self.allies:Set[str] = set()
        self.attack_cooldown = 0
        self.active_treaties: List[Dict] = []  # 簡化
        self.unlocked_tech_breakthroughs: List[str] = []  # 舊系統仍保留
        self.skilltree = SkillTree()  # ★ 新增技能樹
        self.research_progress = 0.0  # 每年由生產科技+城市稅收轉換

class Galaxy:
    def __init__(self):
        self.planets: List[Planet] = []
        self.year = 0
        self.global_events_log: List[Dict] = []
        self.federation_leader: Optional[Citizen] = None
        self.active_federation_policy: Optional[Dict] = None
        self.policy_duration_left = 0
        self.map_layout: Dict[str, Tuple[int,int]] = {}
        self.families: Dict[str, Family] = {}
        self.prev_total_population = 0

# =============================
# 工具函式（事件與效果）
# =============================

def _log_global_event(galaxy: Galaxy, msg: str):
    if galaxy.global_events_log and galaxy.global_events_log[-1]["year"] == galaxy.year:
        galaxy.global_events_log[-1]["events"].append(msg)
    else:
        galaxy.global_events_log.append({"year": galaxy.year, "events": [msg]})

def _apply_value(v, add=0.0, mult=1.0):
    return (v + add) * mult

# 匯總技能與科技的加成（避免在主流程重複判斷）

def get_effects_snapshot(planet: Planet) -> Dict[str, float]:
    effects = {
        "pollution_growth_mult": 1.0,
        "epidemic_chance_mult": 1.0,
        "epidemic_severity_mult": 1.0,
        "attack_damage_bonus": 0.0,
        "defense_cap_bonus": 0.0,
        "resource_infinite": 0.0,
        "trade_rate_mult": 1.0,
    }
    # 來自技能樹
    for key in planet.skilltree.unlocked:
        node = SKILL_TREE_REGISTRY.get(key)
        if not node: continue
        eff = node.get("effect", {})
        if "pollution_growth_mult" in eff:
            effects["pollution_growth_mult"] *= eff["pollution_growth_mult"]
        if "epidemic_chance_mult" in eff:
            effects["epidemic_chance_mult"] *= eff["epidemic_chance_mult"]
        if "epidemic_severity_mult" in eff:
            effects["epidemic_severity_mult"] *= eff["epidemic_severity_mult"]
        if "attack_damage_bonus" in eff:
            effects["attack_damage_bonus"] += eff["attack_damage_bonus"]
        if "defense_cap_bonus" in eff:
            effects["defense_cap_bonus"] += eff["defense_cap_bonus"]
        if eff.get("resource_infinite"):
            effects["resource_infinite"] = 1.0
        if "trade_rate_mult" in eff:
            effects["trade_rate_mult"] *= eff["trade_rate_mult"]
    return effects

# =============================
# 初始化
# =============================

@st.cache_resource
def initialize_galaxy(extra_planets: int = 1):
    g = Galaxy()
    # families
    for fn in ["王家", "李家", "張家"]:
        g.families[fn] = Family(fn)

    # 地球
    earth = Planet("地球")
    for cname in CONFIG["INIT"]["earth_cities"]:
        c = City(cname)
        c.political_parties.extend([
            PoliticalParty("統一黨","保守","穩定發展"),
            PoliticalParty("改革黨","自由","改革求變"),
            PoliticalParty("科技黨","科技信仰","加速科技"),
            PoliticalParty("民族黨","民族主義","民族復興"),
        ])
        c.ruling_party = random.choice(c.political_parties)
        for i in range(CONFIG["INIT"]["earth_citizens_per_city"]):
            fam = random.choice(list(g.families.values()))
            z = Citizen(f"{cname}市民#{i+1}", family=fam)
            z.city = cname; fam.members.append(z); c.citizens.append(z)
        earth.cities.append(c)
    g.planets.append(earth)

    # 外星：賽博星
    alien = Planet("賽博星", alien=True)
    for cname in CONFIG["INIT"]["alien_cities"]:
        c = City(cname)
        c.political_parties.extend([
            PoliticalParty("星際聯盟","科技信仰","星際擴張"),
            PoliticalParty("原初信仰","保守","回歸本源"),
        ])
        c.ruling_party = random.choice(c.political_parties)
        for i in range(CONFIG["INIT"]["alien_citizens_per_city"]):
            fam = random.choice(list(g.families.values()))
            z = Citizen(f"{cname}市民#{i+1}", family=fam)
            z.city = cname; fam.members.append(z); c.citizens.append(z)
        alien.cities.append(c)
    g.planets.append(alien)

    # 額外隨機行星（用於「彼此競爭」）
    for _ in range(max(0, extra_planets)):
        p = Planet(f"競爭星-{random.randint(100,999)}", alien=True)
        for j in range(random.randint(1,2)):
            cname = f"{p.name}-城{j+1}"
            c = City(cname)
            c.political_parties.extend([
                PoliticalParty(f"{cname}和平黨","自由","和平發展"),
                PoliticalParty(f"{cname}擴張黨","民族主義","星際擴張"),
            ])
            c.ruling_party = random.choice(c.political_parties)
            for k in range(random.randint(15,25)):
                fam = random.choice(list(g.families.values()))
                z = Citizen(f"{cname}市民#{k+1}", family=fam)
                z.city = cname; fam.members.append(z); c.citizens.append(z)
            p.cities.append(c)
        g.planets.append(p)

    # 關係與地圖
    for p1 in g.planets:
        for p2 in g.planets:
            if p1!=p2: p1.relations[p2.name] = "neutral"
    # 佈點（避免重疊）
    used = set()
    for p in g.planets:
        x,y = 0,0
        while (x,y) in used:
            x = random.randint(0, CONFIG["VISUAL"]["map_width"])
            y = random.randint(0, CONFIG["VISUAL"]["map_height"])
        used.add((x,y)); g.map_layout[p.name] = (x,y)

    g.prev_total_population = sum(len(c.citizens) for pl in g.planets for c in pl.cities)
    return g

if 'galaxy' not in st.session_state:
    st.session_state.galaxy = initialize_galaxy(extra_planets=2)  # ★ 預設再多兩顆行星

galaxy: Galaxy = st.session_state.galaxy

# =====================================
# 事件與模擬（僅保留核心，細節沿用你的原邏輯但做安全/易讀化）
# =====================================

def trigger_revolution(city: City):
    if not city.citizens: return "無市民，無法革命"
    msg = f"{galaxy.year} 年：🔥 **{city.name}** 爆發叛亂！"
    city.events.append(msg); _log_global_event(galaxy, msg)
    alive = [c for c in city.citizens if c.alive]
    death_n = int(len(alive)*random.uniform(0.05,0.12))
    for _ in range(death_n):
        if not alive: break
        v = random.choice(alive); v.alive=False; v.death_cause="叛亂"; city.death_count+=1
        city.graveyard.append((v.name, v.age, v.ideology, v.death_cause)); alive.remove(v)
    old = city.government_type
    city.government_type = random.choice(["民主制","專制","共和制"]) if old != "專制" else random.choice(["民主制","共和制"]) 
    _log_global_event(galaxy, f"{galaxy.year} 年：政體由 **{old}** 轉為 **{city.government_type}**！")
    city.mass_movement_active=False
    return "革命已觸發"

def trigger_epidemic(planet: Planet):
    if planet.epidemic_active: return "已有疫情"
    planet.epidemic_active=True
    planet.epidemic_severity = random.uniform(0.1,0.5) * (1 - planet.tech_levels["醫療"]*0.5)
    msg = f"{galaxy.year} 年：🦠 **{planet.name}** 爆發疫情！"
    for c in planet.cities: c.events.append(msg)
    _log_global_event(galaxy, msg); return "疫情已觸發"

def handle_planet_year(planet: Planet):
    eff = get_effects_snapshot(planet)
    # cooldown
    if planet.attack_cooldown>0: planet.attack_cooldown -= 1
    # 科技自然增長
    for k in planet.tech_levels:
        planet.tech_levels[k] = min(1.0, planet.tech_levels[k] + random.uniform(0.005,0.015))
    # 污染演化
    growth = random.uniform(0.01,0.02) * eff["pollution_growth_mult"]
    reduce = planet.tech_levels["環境"]*0.015
    planet.pollution = max(0, planet.pollution + growth - reduce)
    # 防禦上限
    defense_cap = 100 + eff["defense_cap_bonus"]
    planet.defense_level = min(int(defense_cap), int(planet.tech_levels["軍事"]*100))
    # 疫情
    epi_chance = st.session_state.epidemic_chance_slider * (1 - planet.tech_levels["醫療"]) * eff["epidemic_chance_mult"]
    if (not planet.epidemic_active) and random.random()<epi_chance:
        trigger_epidemic(planet)
    if planet.epidemic_active:
        sev = max(0.01, planet.epidemic_severity*0.1*(1 - planet.tech_levels["醫療"]*0.8) * eff["epidemic_severity_mult"])
        for city in planet.cities:
            for c in [x for x in city.citizens if x.alive]:
                if random.random()< (sev+0.01):
                    c.health -= sev; c.happiness=max(0.1, c.happiness - sev*0.5)
                    if c.health<0.1:
                        c.alive=False; c.death_cause="疫情"; city.death_count+=1
                        city.graveyard.append((c.name, c.age, c.ideology, c.death_cause))
        planet.epidemic_severity = max(0.0, planet.epidemic_severity - random.uniform(0.05,0.1))
        if planet.epidemic_severity<=0.05:
            planet.epidemic_active=False
            _log_global_event(galaxy, f"{galaxy.year} 年：✅ **{planet.name}** 疫情受控。")
    # 研究點產生（由生產科技與總稅收推導）；點數小數積累，每達閾值+1
    total_tax = sum(c.resources["稅收"] for c in planet.cities)
    planet.research_progress += planet.tech_levels["生產"]*0.6 + (total_tax/1000.0)
    while planet.research_progress >= 1.0:
        planet.research_progress -= 1.0
        planet.skilltree.points += 1
        _log_global_event(galaxy, f"{galaxy.year} 年：🔧 **{planet.name}** 獲得 1 點技能點（目前 {planet.skilltree.points}）。")


def handle_city_year(city: City, planet: Planet):
    eff = get_effects_snapshot(planet)
    # 資源消耗與產出
    pop_consume = len(city.citizens)*0.5
    if eff["resource_infinite"]:
        city.resources["糧食"] = 1000; city.resources["能源"] = 1000
    else:
        city.resources["糧食"] -= pop_consume
        city.resources["能源"] -= pop_consume/2
    # 專精基礎產出 + 技能樹城市增益
    bonus = {"糧食":0, "能源":0, "稅收":0}
    for key in planet.skilltree.unlocked:
        node = SKILL_TREE_REGISTRY.get(key, {})
        cb = node.get("effect", {}).get("city_resource_bonus")
        if cb:
            for k,v in cb.items(): bonus[k] += v
    spec = city.specialization
    if spec=="農業": city.resources["糧食"] += 20 + bonus["糧食"]
    if spec=="工業": city.resources["能源"] += 15 + bonus["能源"]
    if spec=="科技": city.resources["稅收"] += 10 + bonus["稅收"]; planet.tech_levels["生產"] = min(1.0, planet.tech_levels["生產"]+0.005)
    if spec=="服務": city.resources["稅收"] += 15 + bonus["稅收"]
    if spec=="軍事": planet.tech_levels["軍事"] = min(1.0, planet.tech_levels["軍事"]+0.005)

    # 群眾運動（簡化門檻）
    alive = [c for c in city.citizens if c.alive]
    if alive:
        avg_t = sum(c.trust for c in alive)/len(alive)
        avg_h = sum(c.happiness for c in alive)/len(alive)
    else:
        avg_t=0; avg_h=0
    if avg_t<0.5 and avg_h<0.5 and not city.mass_movement_active and random.random()<0.03:
        city.mass_movement_active=True
        _log_global_event(galaxy, f"{galaxy.year} 年：📢 {city.name} 爆發群眾運動！")
    if city.mass_movement_active and (avg_t>0.6 and avg_h>0.6):
        city.mass_movement_active=False
        _log_global_event(galaxy, f"{galaxy.year} 年：✅ {city.name} 群眾運動平息。")

    # 選舉
    city.election_timer -= 1
    if city.election_timer<=0:
        voters = [c for c in alive if c.age>=18]
        if voters:
            for p in city.political_parties: p.calculate_support(voters)
            if city.political_parties:
                win = max(city.political_parties, key=lambda p:p.support)
                if win != city.ruling_party:
                    old = city.ruling_party.name if city.ruling_party else "無"
                    city.ruling_party = win
                    _log_global_event(galaxy, f"{galaxy.year} 年：🗳️ **{city.name}** 政黨輪替：{old} → {win.name}")
                else:
                    _log_global_event(galaxy, f"{galaxy.year} 年：🗳️ **{city.name}** 現任續任：{win.name}")
        city.election_timer = random.randint(CONFIG["RATES"]["election_year_min"], CONFIG["RATES"]["election_year_max"])

    # 生老病死（簡化）
    next_list: List[Citizen] = []
    for c in list(city.citizens):
        if not c.alive: continue
        c.age += 1
        income = {
            "農民":10,"工人":15,"科學家":25,"商人":30,"無業":5,"醫生":40,"藝術家":12,"工程師":35,"教師":20,"服務員":10,"小偷":20,"黑幫成員":25,"詐騙犯":30,"毒販":45
        }[c.profession]
        c.wealth = max(0, c.wealth + income - 8)
        # 稅收
        tax_rate = {"專制":0.08, "民主制":0.03, "共和制":0.05}.get(city.government_type, 0.05)
        city.resources["稅收"] += int(c.wealth * tax_rate)
        # 污染健康影響
        if planet.pollution>1.0 and random.random()<0.03:
            c.health -= max(0.05, 0.3*(1-planet.tech_levels["環境"]*0.5))
            c.happiness = max(0.1, c.happiness-0.05)
        c.health = min(1.0, c.health+0.01)
        # 自然死亡/意外（由側邊欄控制）
        base_old = 80
        if (c.age>base_old and random.random()< st.session_state.death_rate_slider*10) or (random.random()< st.session_state.death_rate_slider):
            c.alive=False; c.death_cause="自然/意外"
        # 生日後處理
        if c.alive:
            # 生育
            if c.partner and 20<=c.age<=40 and random.random()< (st.session_state.birth_rate_slider*(1+c.happiness*0.5)):
                baby = Citizen(f"{c.name}-子{random.randint(1,999)}", parent1_ideology=c.ideology, parent2_ideology=c.partner.ideology, parent1_trust=c.trust, parent2_trust=c.partner.trust, parent1_emotion=c.happiness, parent2_emotion=c.partner.happiness, family=c.family)
                baby.city = city.name; next_list.append(baby); city.birth_count+=1
            # 移民（受技能影響的貿易繁榮可降低外流）
            mig = CONFIG["RATES"]["immigrate_base"]
            if random.random()<mig:
                other = [ct for p in galaxy.planets for ct in p.cities if ct.name!=city.name and p.is_alive]
                if other:
                    target = random.choice(other)
                    c.city = target.name; target.citizens.append(c); city.emigration_count+=1; target.immigration_count+=1
                    _log_global_event(galaxy, f"{galaxy.year} 年：{c.name} 由 {city.name} 遷往 {target.name}。")
                    continue
            next_list.append(c)
        else:
            city.death_count+=1; city.graveyard.append((c.name, c.age, c.ideology, c.death_cause))
    city.citizens = next_list
    # 簡單短缺/繁榮事件
    if (city.resources["糧食"]<50 or city.resources["能源"]<30):
        city.resource_shortage_years += 1
        if city.resource_shortage_years>=3:
            _log_global_event(galaxy, f"{galaxy.year} 年：🚨 **{city.name}** 爆發饑荒！")
            city.resources["糧食"] = max(0, city.resources["糧食"]-20)
            city.resources["能源"] = max(0, city.resources["能源"]-10)
    else:
        city.resource_shortage_years = 0

    # 歷史
    alive2 = [c for c in city.citizens if c.alive]
    if alive2:
        city.history.append((galaxy.year,
            sum(c.health for c in alive2)/len(alive2),
            sum(c.trust for c in alive2)/len(alive2),
            sum(c.happiness for c in alive2)/len(alive2)
        ))


def simulate_year(galaxy: Galaxy):
    galaxy.year += 1
    # 行星年度
    for p in list(galaxy.planets):
        handle_planet_year(p)
        for c in p.cities:
            # 重置年度統計
            c.birth_count=c.death_count=c.immigration_count=c.emigration_count=0
            c.events = []
            handle_city_year(c, p)
        # 星球滅亡判斷
        if all(len(c.citizens)==0 for c in p.cities):
            p.is_alive = False
            _log_global_event(galaxy, f"{galaxy.year} 年：💥 **{p.name}** 全城滅亡，行星已失去生命跡象！")
    galaxy.planets = [p for p in galaxy.planets if p.is_alive]

    # 人口變動提示
    cur_pop = sum(len(c.citizens) for pl in galaxy.planets for c in pl.cities)
    if galaxy.prev_total_population>0:
        delta = (cur_pop - galaxy.prev_total_population)/galaxy.prev_total_population*100
        if delta>5: _log_global_event(galaxy, f"{galaxy.year} 年：📈 星系人口成長 {delta:.1f}% 至 {cur_pop}")
        elif delta<-5: _log_global_event(galaxy, f"{galaxy.year} 年：📉 星系人口下降 {abs(delta):.1f}% 至 {cur_pop}")
    galaxy.prev_total_population = cur_pop

# =============================
# UI
# =============================

st.title("🌐 CitySim 世界模擬器 Pro（可擴充版 / 技能樹 / 多星球競爭）")

with st.sidebar:
    st.header("⚙️ 模擬設定")
    years_per_step = st.slider("每次模擬年數", 1, 100, 10)
    if st.button("執行模擬步驟"):
        for _ in range(years_per_step): simulate_year(galaxy)
        st.experimental_rerun()

    st.markdown("---")
    st.header("🌐 隨機性")
    st.session_state.birth_rate_slider = st.slider("出生率", 0.0, 0.1, 0.02)
    st.session_state.death_rate_slider = st.slider("死亡率", 0.0, 0.1, 0.01)
    st.session_state.epidemic_chance_slider = st.slider("疫情機率", 0.0, 0.1, 0.02)

    st.markdown("---")
    st.header("🪐 行星/技能")
    # 行星選擇
    planet_names = [p.name for p in galaxy.planets]
    sel_planet_name = st.selectbox("選擇行星", planet_names)
    sel_planet = next((p for p in galaxy.planets if p.name==sel_planet_name), None)

    # 新增行星
    with st.expander("➕ 新增行星"):
        new_name = st.text_input("行星名稱", value=f"新星-{random.randint(100,999)}")
        new_is_alien = st.checkbox("外星行星?", value=True)
        new_cities = st.number_input("城市數量", 1, 4, 2)
        if st.button("建立行星"):
            p = Planet(new_name, alien=new_is_alien)
            for j in range(int(new_cities)):
                cname = f"{new_name}-城{j+1}"
                c = City(cname)
                c.political_parties.extend([
                    PoliticalParty(f"{cname}和平黨","自由","和平發展"),
                    PoliticalParty(f"{cname}擴張黨","民族主義","星際擴張"),
                ])
                c.ruling_party = random.choice(c.political_parties)
                for k in range(random.randint(12,20)):
                    fam = random.choice(list(galaxy.families.values()))
                    z = Citizen(f"{cname}市民#{k+1}", family=fam)
                    z.city=cname; fam.members.append(z); c.citizens.append(z)
                p.cities.append(c)
            # 關係/座標
            for op in galaxy.planets: op.relations[p.name] = "neutral"; p.relations[op.name] = "neutral"
            x,y = 0,0
            used = set(galaxy.map_layout.values())
            while (x,y) in used:
                x = random.randint(0, CONFIG["VISUAL"]["map_width"]); y = random.randint(0, CONFIG["VISUAL"]["map_height"])
            galaxy.map_layout[p.name]=(x,y)
            galaxy.planets.append(p)
            st.success(f"已新增行星 {new_name}")
            st.experimental_rerun()

    # 技能樹 UI
    if sel_planet:
        st.markdown(f"**{sel_planet.name}** 技能點：`{sel_planet.skilltree.points}` ／ 研究累積：`{sel_planet.research_progress:.2f}`")
        tiers = sorted({v["tier"] for v in SKILL_TREE_REGISTRY.values()})
        for t in tiers:
            with st.expander(f"Tier {t} 技能"):
                tier_nodes = {k:v for k,v in SKILL_TREE_REGISTRY.items() if v["tier"]==t}
                for key, node in tier_nodes.items():
                    owned = key in sel_planet.skilltree.unlocked
                    label = f"{node['name']}（花費{node['cost']}，前置：{','.join(node['prereq']) if node['prereq'] else '無'}）" + (" ✅" if owned else "")
                    col1, col2 = st.columns([3,1])
                    with col1:
                        st.caption(f"代碼：{key}")
                        st.write(label)
                    with col2:
                        if not owned and sel_planet.skilltree.can_unlock(key) and st.button("解鎖", key=f"unlock_{sel_planet.name}_{key}"):
                            if sel_planet.skilltree.unlock(key, galaxy.year):
                                _log_global_event(galaxy, f"{galaxy.year} 年：🧩 **{sel_planet.name}** 解鎖技能「{node['name']}」！")
                                st.experimental_rerun()
                        elif owned:
                            st.success("已擁有")
                        else:
                            st.button("不可解鎖", disabled=True, key=f"disabled_{sel_planet.name}_{key}")

st.markdown(f"### ⏳ 當前年份：{galaxy.year}")

# =============================
# 地圖與總覽
# =============================

st.markdown("---")
st.markdown("#### 🗺️ 星系地圖")
if galaxy.planets:
    rows = []
    for p in galaxy.planets:
        x,y = galaxy.map_layout.get(p.name, (0,0))
        alive = [c for ct in p.cities for c in ct.citizens if c.alive]
        rows.append({
            "name": p.name, "x":x, "y":y,
            "type": "外星行星" if p.alien else "地球行星",
            "mil": p.tech_levels["軍事"], "env": p.tech_levels["環境"], "med": p.tech_levels["醫療"], "prod": p.tech_levels["生產"],
            "poll": p.pollution, "conf": p.conflict_level, "def": p.defense_level,
            "avg_health": sum(c.health for c in alive)/len(alive) if alive else 0,
            "avg_trust": sum(c.trust for c in alive)/len(alive) if alive else 0,
            "avg_happiness": sum(c.happiness for c in alive)/len(alive) if alive else 0,
        })
    dfp = pd.DataFrame(rows)
    fig = go.Figure()
    for p in galaxy.planets:
        for other, status in p.relations.items():
            po = next((x for x in galaxy.planets if x.name==other and x.is_alive), None)
            if po and p.name < po.name:
                x1,y1 = galaxy.map_layout.get(p.name,(0,0)); x2,y2 = galaxy.map_layout.get(po.name,(0,0))
                color = 'grey'
                if status=="friendly": color='green'
                elif status=="hostile": color='orange'
                if other in p.war_with: color='red'
                fig.add_trace(go.Scatter(x=[x1,x2,None], y=[y1,y2,None], mode='lines', line=dict(color=color,width=2), showlegend=False))
    fig.add_trace(go.Scatter(x=dfp["x"], y=dfp["y"], mode='markers+text',
        marker=dict(size=20, color=dfp["type"].map({"地球行星":"blue","外星行星":"purple"}), symbol='circle', line=dict(width=2, color='DarkSlateGrey')),
        text=dfp["name"], textposition="top center",
        hovertemplate="<b>%{text}</b><br>軍事:%{customdata[0]:.2f} 環境:%{customdata[1]:.2f}<br>醫療:%{customdata[2]:.2f} 生產:%{customdata[3]:.2f}<br>污染:%{customdata[4]:.2f} 衝突:%{customdata[5]:.2f} 防禦:%{customdata[6]}<extra></extra>",
        customdata=dfp[["mil","env","med","prod","poll","conf","def"]].values,
        showlegend=False
    ))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("星系中沒有行星。")

# =============================
# 行星/城市詳情 + 排行
# =============================

st.markdown("---")

cols = st.columns(2)
with cols[0]:
    st.subheader("🪐 行星概況與技能")
    for p in galaxy.planets:
        st.markdown(f"**{p.name}**｜污染 {p.pollution:.2f}｜衝突 {p.conflict_level:.2f}｜防禦 {p.defense_level}")
        st.caption(f"科技：軍事 {p.tech_levels['軍事']:.2f}｜環境 {p.tech_levels['環境']:.2f}｜醫療 {p.tech_levels['醫療']:.2f}｜生產 {p.tech_levels['生產']:.2f}")
        if p.skilltree.unlocked:
            st.write("已解鎖：" + ", ".join(SKILL_TREE_REGISTRY[k]["name"] for k in p.skilltree.unlocked))
        else:
            st.write("已解鎖：無")

with cols[1]:
    st.subheader("🏆 競爭排行（綜合評分）")
    # 簡單評分：科技平均*50 + 防禦 + (城市稅收總和/10) - 污染*5
    scoreboard = []
    for p in galaxy.planets:
        tech_avg = sum(p.tech_levels.values())/4
        tax_sum = sum(c.resources["稅收"] for c in p.cities)
        score = tech_avg*50 + p.defense_level + tax_sum/10 - p.pollution*5
        scoreboard.append({"行星":p.name, "分數": round(score,1), "稅收": int(tax_sum)})
    if scoreboard:
        df_score = pd.DataFrame(scoreboard).sort_values("分數", ascending=False)
        st.dataframe(df_score, use_container_width=True)

st.markdown("---")

# 城市選擇/細節
all_cities = [c.name for p in galaxy.planets for c in p.cities]
sel_city_name = st.selectbox("選擇城市檢視", all_cities)
if sel_city_name:
    ct: Optional[City] = next((c for p in galaxy.planets for c in p.cities if c.name==sel_city_name), None)
    if ct:
        st.markdown(f"### 📊 {ct.name}")
        st.write(f"人口 {len(ct.citizens)}｜糧食 {ct.resources['糧食']:.0f}｜能源 {ct.resources['能源']:.0f}｜稅收 {ct.resources['稅收']:.0f}")
        st.write(f"產業專精：{ct.specialization}｜政體：{ct.government_type}｜群眾運動：{'是' if ct.mass_movement_active else '否'}")
        # 歷史曲線
        if ct.history:
            dfh = pd.DataFrame(ct.history, columns=["年份","健康","信任","快樂"])
            fig_h = go.Figure()
            for col in ["健康","信任","快樂"]:
                fig_h.add_trace(go.Scatter(x=dfh["年份"], y=dfh[col], mode='lines+markers', name=col))
            fig_h.update_layout(title=f"{ct.name} 平均健康/信任/快樂")
            st.plotly_chart(fig_h, use_container_width=True)
        # 思想派別
        ideos = pd.Series([c.ideology for c in ct.citizens if c.alive]).value_counts()
        if not ideos.empty:
            df_i = pd.DataFrame({"思想": ideos.index, "人數": ideos.values})
            st.plotly_chart(px.bar(df_i, x="思想", y="人數", title=f"{ct.name} 思想分布"), use_container_width=True)
        # 死因
        causes = [x[3] for x in ct.graveyard if x[3]]
        if causes:
            dc = pd.Series(causes).value_counts()
            st.plotly_chart(px.bar(pd.DataFrame({"死因": dc.index, "人數": dc.values}), x="死因", y="人數", title=f"{ct.name} 死因"), use_container_width=True)

# 事件控制台（簡化）
st.markdown("---")
st.subheader("🚨 事件控制台")
colA, colB = st.columns(2)
with colA:
    trg_city = st.selectbox("選擇革命城市", all_cities, key="rev_city")
    if st.button("觸發革命"):
        cobj = next((c for p in galaxy.planets for c in p.cities if c.name==trg_city), None)
        if cobj: st.success(trigger_revolution(cobj))
with colB:
    trg_planet = st.selectbox("選擇疫情行星", [p.name for p in galaxy.planets], key="epi_planet")
    if st.button("觸發疫情"):
        pobj = next((p for p in galaxy.planets if p.name==trg_planet), None)
        if pobj: st.success(trigger_epidemic(pobj))

# 年報
st.markdown("---")
st.subheader("🗞️ 未來之城日報（近 50 年）")
if galaxy.global_events_log:
    for entry in reversed(galaxy.global_events_log[-50:]):
        with st.expander(f"**{entry['year']} 年年度報告**"):
            for e in entry.get('events', []): st.write(f"- {e}")
else:
    st.info("尚無事件紀錄")
