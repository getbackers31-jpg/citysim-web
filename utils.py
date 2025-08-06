# utils.py

def get_planet_metric(planet, metric):
    # 星球/城市地圖選單指標安全查詢
    if metric == "污染":
        return getattr(planet, "pollution", 0)
    elif metric == "衝突等級":
        return getattr(planet, "conflict_level", 0)
    elif metric == "平均健康":
        citizens = [c for city in getattr(planet, "cities", []) for c in getattr(city, "citizens", []) if getattr(c, "alive", True)]
        return sum(getattr(c, "health", 0.5) for c in citizens) / len(citizens) if citizens else 0.5
    elif metric == "平均信任":
        citizens = [c for city in getattr(planet, "cities", []) for c in getattr(city, "citizens", []) if getattr(c, "alive", True)]
        return sum(getattr(c, "trust", 0.5) for c in citizens) / len(citizens) if citizens else 0.5
    elif metric == "平均快樂度":
        citizens = [c for city in getattr(planet, "cities", []) for c in getattr(city, "citizens", []) if getattr(c, "alive", True)]
        return sum(getattr(c, "happiness", 0.5) for c in citizens) / len(citizens) if citizens else 0.5
    else:
        return 0

def get_city_metric(city, metric):
    if metric == "人口":
        return len(city.citizens)
    elif metric == "糧食":
        return city.resources.get("糧食", 0)
    elif metric == "能源":
        return city.resources.get("能源", 0)
    elif metric == "平均健康":
        vals = [getattr(c, 'health', 0.5) for c in city.citizens if getattr(c, 'alive', True)]
        return sum(vals)/len(vals) if vals else 0.5
    elif metric == "平均信任":
        vals = [getattr(c, 'trust', 0.5) for c in city.citizens if getattr(c, 'alive', True)]
        return sum(vals)/len(vals) if vals else 0.5
    elif metric == "平均快樂度":
        vals = [getattr(c, 'happiness', 0.5) for c in city.citizens if getattr(c, 'alive', True)]
        return sum(vals)/len(vals) if vals else 0.5
    else:
        return 0

def get_citizen_metric(citizen, metric):
    if metric == "健康":
        return getattr(citizen, 'health', 0.5)
    elif metric == "信任":
        return getattr(citizen, 'trust', 0.5)
    elif metric == "快樂度":
        return getattr(citizen, 'happiness', 0.5)
    elif metric == "財富":
        return getattr(citizen, 'wealth', 100)
    else:
        return 0


