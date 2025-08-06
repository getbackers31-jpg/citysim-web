# logic.py
import random
from models import Family, PoliticalParty, Citizen, City, Planet, Treaty, Galaxy

# --- 事件觸發函數 ---
def trigger_revolution(city_obj, current_year_global_events, galaxy):
    if not city_obj.citizens:
        return f"{city_obj.name} 沒有市民，無法觸發革命。"
    rebellion_msg = f"{galaxy.year} 年：🔥 **{city_obj.name}** 爆發了大規模叛亂！政體可能改變！"
    city_obj.events.append(rebellion_msg)
    current_year_global_events.append(rebellion_msg)
    alive_citizens_for_stats = [c for c in city_obj.citizens if c.alive]
    rebellion_death_count = int(len(alive_citizens_for_stats) * random.uniform(0.05, 0.15))
    for _ in range(rebellion_death_count):
        if alive_citizens_for_stats:
            victim = random.choice(alive_citizens_for_stats)
            victim.alive = False
            victim.death_cause = "叛亂"
            city_obj.death_count += 1
            city_obj.graveyard.append((victim.name, victim.age, victim.ideology, victim.death_cause))
            alive_citizens_for_stats.remove(victim)
    city_obj.resources["糧食"] = max(0, city_obj.resources["糧食"] - random.uniform(50, 100))
    city_obj.resources["能源"] = max(0, city_obj.resources["能源"] - random.uniform(30, 70))
    old_government_type = city_obj.government_type
    if city_obj.government_type == "專制":
        city_obj.government_type = random.choice(["民主制", "共和制"])
    elif city_obj.government_type == "民主制":
        city_obj.government_type = "專制"
    elif city_obj.government_type == "共和制":
        city_obj.government_type = random.choice(["專制", "民主制"])
    current_year_global_events.append(f"{galaxy.year} 年：政體在叛亂中從 **{old_government_type}** 變為 **{city_obj.government_type}**！")
    city_obj.mass_movement_active = False
    return f"成功觸發 {city_obj.name} 的革命！"

def trigger_epidemic(planet_obj, current_year_global_events, galaxy):
    if planet_obj.epidemic_active:
        return f"{planet_obj.name} 已經有疫情活躍中。"
    planet_obj.epidemic_active = True
    planet_obj.epidemic_severity = random.uniform(0.1, 0.5) * (1 - planet_obj.tech_levels["醫療"] * 0.5)
    epidemic_msg = f"{galaxy.year} 年：🦠 **{planet_obj.name}** 爆發了嚴重的疫情！市民們人心惶惶，醫療系統面臨巨大壓力。"
    for city in planet_obj.cities: city.events.append(epidemic_msg)
    current_year_global_events.append(epidemic_msg)
    return f"成功觸發 {planet_obj.name} 的疫情！"

# ...（其餘 trigger_coup, trigger_ai_awakening 以及各類 update_xxx、simulate_xxx、handle_xxx function
# 直接複製你的 citysim_web.py 相關事件邏輯 function 到這裡，記得用 import 或參數將所需 class 傳入）

# 補充：原本 Streamlit 的 st.session_state、st.sidebar、st.slider 等要搬到 main.py 或 ui.py
# 在 logic.py 只保留純計算和數據處理 function，不要有 Streamlit UI 互動元件
