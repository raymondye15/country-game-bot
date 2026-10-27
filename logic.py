# -*- coding: utf-8 -*-
"""Pure game logic operating on country dicts (no Telegram / DB imports -> unit-testable)."""
import math, random, time
from game_data import PLANETS, GOVERNMENTS, RESEARCH, BUILDINGS, RANDOM_EVENTS, RESOURCES, TOURISM_LEVELS

HOUR = 3600
DAY = 86400

def now_ts() -> int:
    return int(time.time())

def compute_mods(c: dict) -> dict:
    mods = {}
    def add(src):
        for k, v in src.items():
            if k == "explore_cap":
                mods[k] = max(mods.get(k, 3), v)
            else:
                mods[k] = mods.get(k, 0) + v
    planet = PLANETS[c["planet"]]
    add(planet["continents"][c["continent"]].get("mods", {}))
    add(GOVERNMENTS[c["government"]].get("mods", {}))
    for rid in c.get("researched", []):
        if rid in RESEARCH:
            add(RESEARCH[rid]["effects"])
    mods.setdefault("explore_cap", 3)
    return mods

def mod(c: dict, key: str, default=0.0):
    return compute_mods(c).get(key, default)

def explore_cap(c: dict) -> int:
    return int(compute_mods(c).get("explore_cap", 3))

def new_country(user_id: int, planet: str, continent: str, government: str,
                name: str, capital: str, cities: list, username: str = "") -> dict:
    pdata = PLANETS[planet]
    cont = pdata["continents"][continent]
    area = random.randint(30000, 87000)
    pop = random.randint(500000, 1000000)
    # mines from continent weights: 3-5 mines
    weights = cont["mine_weights"]
    pool = list(weights.keys())
    wts = [weights[k] for k in pool]
    mines = {}
    for _ in range(random.randint(3, 5)):
        r = random.choices(pool, weights=wts)[0]
        mines[r] = mines.get(r, 0) + 1
    terrains = cont["terrains"]
    borders = {}
    dirs = ["north", "east", "south", "west"]
    sea_dir = random.choice(dirs) if cont.get("seas") else None
    for d in dirs:
        if d == sea_dir:
            borders[d] = {"status": "sea", "label": cont["seas"][0], "country_id": None}
        else:
            borders[d] = {"status": "open", "label": random.choice(terrains), "country_id": None}
    t = now_ts()
    c = {
        "user_id": user_id, "username": username,
        "name": name, "name_lower": name.lower(), "capital": capital,
        "cities": [{"name": capital, "pop": int(pop * 0.30)}] +
                  [{"name": s, "pop": int(pop * f)} for s, f in zip(cities, (0.18, 0.12, 0.08))],
        "planet": planet, "continent": continent, "government": government,
        "population": pop, "area": area, "initial_area": area,
        "money": 1500, "rp": 10,
        "res": {"food": 2000, "water": 2000, "energy": 3000, "materials": 300, "iron": 120, "titanium": 40, "special": 20},
        "mines": mines,
        "buildings": {"farm": 3, "waterplant": 3, "powerplant": 1, "mine": 1, "factory": 1, "university": 0, "hospital": 0, "barracks": 0},
        "soldiers": 0, "accept_migrants": True, "tourism_level": 0, "tourists": 0.0, "fin_trade": 0, "last_fin": {}, "fin_day": {}, "carry": {},
        "day_births": 0, "day_deaths": 0, "day_pool": 0, "day_rp": 0,
        "last_births": 0, "last_deaths": 0, "last_mig_in": [], "last_mig_out": 0,
        "protest_hours": 0, "shortage_hours": 0,
        "mig_in_today": [], "mig_out_today": 0, "last_mig_pool": 0, "last_pop_delta": 0,
        "happiness": 65, "tax_rate": 2,  # 1=low 2=mid 3=high
        "neighbors": [], "alliances": [], "naps": [],
        "borders": borders,
        "explore_charges": 3, "last_charge_ts": t,
        "researched": [], "researching": None,  # {id, finish_ts}
        "created_ts": t, "last_daily_ts": t, "last_seen_ts": t,
        "protest_days": 0, "shortage_days": 0, "war_id": None, "peace_until": 0, "newbie_until": t + 7 * DAY,
        "last_econ_ts": t, "last_hour_ts": t,
        "alive": True, "frozen": False,
    }
    c["mods_cache"] = compute_mods(c)
    return c

def regen_charges(c: dict, t: int = None) -> bool:
    t = t or now_ts()
    cap = explore_cap(c)
    changed = False
    while c["explore_charges"] < cap and t - c["last_charge_ts"] >= HOUR:
        c["explore_charges"] += 1
        c["last_charge_ts"] += HOUR
        changed = True
    if c["explore_charges"] >= cap:
        c["last_charge_ts"] = t
    return changed

def exploration_gain(c: dict) -> int:
    base = c["initial_area"] / 24.0
    base *= (1 + mod(c, "explore"))
    return max(200, int(base * random.uniform(0.8, 1.2)))

EXPLORE_COST = {"energy": 15, "food": 20, "money": 25}

def do_exploration(c: dict, direction: str, other_countries: list) -> dict:
    """Mutates c. other_countries: alive countries on same planet+continent not yet neighbors."""
    b = c["borders"][direction]
    if b["status"] == "sea":
        return {"ok": False, "msg": f"آن جهت دریاست ({b['label']}) و تیم اکتشاف نمی‌تواند از آب بگذرد."}
    if b["status"] == "country":
        return {"ok": False, "msg": "آن جهت به مرز کشور دیگری رسیده است؛ اول باید با او همسایه شوی یا بجنگی."}
    if c["explore_charges"] < 1:
        return {"ok": False, "msg": "شارژ اکتشاف نداری؛ هر ساعت یک شارژ ذخیره می‌شود."}
    for k, v in EXPLORE_COST.items():
        have = c["money"] if k == "money" else c["res"][k]
        if have < v:
            return {"ok": False, "msg": "منابع کافی برای اکتشاف نداری (انرژی/غذا/پول لازم است)."}
    c["explore_charges"] -= 1
    c["money"] -= EXPLORE_COST["money"]
    c["res"]["energy"] -= EXPLORE_COST["energy"]
    c["res"]["food"] -= EXPLORE_COST["food"]
    terrains = PLANETS[c["planet"]]["continents"][c["continent"]]["terrains"]
    def rotate_terrain():
        # the frontier moves: the NEXT stretch of land in this direction gets a
        # fresh terrain (previously the label stayed the creation-time one forever)
        choices = [t for t in terrains if t != b["label"]] or terrains
        b["label"] = random.choice(choices)
    roll = random.random()
    if roll < 0.07 and other_countries:
        other = random.choice(other_countries)
        b["status"] = "country"
        b["country_id"] = other["user_id"]
        b["label"] = f"مرز کشور {other['name']}"
        return {"ok": True, "kind": "country", "other": other,
                "msg": f"تیم اکتشاف به مرز کشور «{other['name']}» رسید! این جهت بسته شد؛ می‌توانی از بخش دیپلماسی درخواست همسایگی بفرستی."}
    gain = exploration_gain(c)
    if roll < 0.22:  # rough terrain: half gain + small salvage
        gain //= 2
        c["area"] += gain
        c["res"]["materials"] = c["res"].get("materials", 0) + 8
        msg = f"زمین سخت بود ({b['label']})؛ فقط {gain:,} کیلومتر مربع تصرف شد و ۸ واحد مصالح از زمین جدید جمع شد."
        rotate_terrain()
        return {"ok": True, "kind": "rough", "gain": gain, "msg": msg}
    if roll < 0.30:  # discovery: a new mine (now named in the message)
        res_found = random.choice(["iron", "titanium", "special", "materials"])
        c["mines"][res_found] = c["mines"].get(res_found, 0) + 1
        c["area"] += gain
        msg = f"⛏️ اکتشاف موفق (+{gain:,} کیلومتر مربع) و یک معدن جدید کشف شد: {RESOURCES.get(res_found, res_found)}! (از این به بعد هر روز از آن برداشت می‌کنی)"
        rotate_terrain()
        return {"ok": True, "kind": "discovery", "gain": gain, "found": res_found, "msg": msg}
    c["area"] += gain
    c["res"]["materials"] = c["res"].get("materials", 0) + 15
    msg = f"اکتشاف موفق! +{gain:,} کیلومتر مربع به کشور اضافه شد و ۱۵ واحد مصالح از زمین جدید جمع شد."
    rotate_terrain()
    return {"ok": True, "kind": "normal", "gain": gain, "msg": msg}

def military_power(c: dict) -> int:
    base = c["soldiers"] * (1 + mod(c, "military"))
    base *= 1 + 0.15 * c["buildings"].get("barracks", 0)
    return int(base)

def defense_power(c: dict) -> int:
    return int(military_power(c) * (1 + mod(c, "defense")))

def production(c: dict) -> dict:
    """Gross daily production of every resource (used by the tick and the finance view)."""
    b = c["buildings"]
    mine_bonus = 1 + 0.25 * b.get("mine", 0)
    prod = {
        "food": (4000 + b.get("farm", 0) * 4000) * (1 + mod(c, "food_prod")),
        "water": (3000 + b.get("waterplant", 0) * 4000) * (1 + mod(c, "water_prod")),
        "energy": (2500 + b.get("powerplant", 0) * 3500) * (1 + mod(c, "energy_prod")),
        "materials": (150 + b.get("factory", 0) * 220) * (1 + mod(c, "materials_prod")),
        "iron": 0, "titanium": 0, "special": 0,
    }
    for r, cnt in c["mines"].items():
        prod[r] = prod.get(r, 0) + cnt * 90 * mine_bonus * (1 + mod(c, "mine_prod"))
    return prod

# ---------------------------------------------------------------- scores
# Simulator-style composite scores, computed live from existing country data
# (no stored fields, so no DB migration). Shown in the country/finance views
# and used by the leaderboard tabs.
RES_PRICE = {"food": 0.06, "water": 0.06, "energy": 0.08, "materials": 1.0,
             "iron": 1.5, "titanium": 4.0, "special": 6.0}
BUILDING_SCORE = {"farm": 10, "waterplant": 10, "powerplant": 20, "mine": 25,
                  "factory": 30, "university": 25, "hospital": 20, "barracks": 20,
                  "airport_inter": 100, "hotel": 15}

def eco_score(c: dict):
    """Economic score: daily production value (main weight) + infrastructure
    + a log-scaled treasury term, so hoarding unspent cash cannot top the board.
    Returns (total, breakdown)."""
    prod = production(c)
    prod_value = sum(v * RES_PRICE.get(r, 2.0) for r, v in prod.items())
    infra = sum(BUILDING_SCORE.get(k, 10) * n for k, n in c["buildings"].items())
    treasury = int(50 * math.log10(max(0, c["money"]) + 1))
    parts = {"prod": int(prod_value * 0.1), "infra": infra, "treasury": treasury,
             "prod_value": int(prod_value)}
    return parts["prod"] + infra + treasury, parts

def sci_score(c: dict):
    """Science score: total RP cost of completed research (achievement)
    + current daily RP generation x5 (capacity).
    Returns (total, breakdown)."""
    done = sum(RESEARCH[r]["cost"] for r in c.get("researched", []) if r in RESEARCH)
    rp_day = 2 + c["buildings"].get("university", 0) * 6
    parts = {"done": done, "rp_day": rp_day}
    return done + rp_day * 5, parts

def tourism_score(c: dict):
    """Tourism score: hotel infrastructure + industry level + yesterday's
    visitor volume (log-scaled). Returns (total, breakdown)."""
    hotels = c["buildings"].get("hotel", 0)
    level = c.get("tourism_level", 0)
    last = c.get("last_tour", {})
    visitors = int(60 * math.log10(last.get("arrivals", 0) + 1))
    parts = {"hotels": hotels * 40, "level": level * 150, "visitors": visitors}
    return parts["hotels"] + parts["level"] + parts["visitors"], parts

def tourism_rates(c: dict) -> dict:
    """Daily tourism figures for a country (used by the tick and the view)."""
    hotels = c["buildings"].get("hotel", 0)
    level = c.get("tourism_level", 0)
    if hotels <= 0:
        return {"arrivals": 0.0, "spend": 0.0, "cap": 0, "offplanet": False}
    offplanet = c["buildings"].get("airport_inter", 0) > 0
    arrivals = hotels * 120 * (0.6 + level * 0.35) * (0.5 + c["happiness"] / 100.0)
    spend = 0.7 * (1 + level * 0.25)
    if offplanet:
        arrivals *= 1.6
        spend *= 1.5   # off-planet tourists are richer
    return {"arrivals": arrivals, "spend": spend, "cap": hotels * 300, "offplanet": offplanet}

def next_market_price(price: float, base: float, net_volume: float, rng) -> float:
    """One hourly step of the global market price: mean reversion to the base
    price + small random walk + supply/demand pressure from player trades
    (net buying pushes up, net selling pushes down). Clamped to [0.35x, 3x]."""
    drift = 0.03 * (base - price) / base
    noise = rng.uniform(-0.025, 0.025)
    pressure = max(-1.0, min(1.0, net_volume / 5000.0)) * 0.04
    new = price * (1 + drift + noise + pressure)
    return max(base * 0.35, min(base * 3.0, new))

def national_power(c: dict) -> int:
    """Overall index: 40% economy + 25% science + population + military power.
    Lets a small advanced country outrank a big backward one."""
    eco, _ = eco_score(c)
    sci, _ = sci_score(c)
    tour, _ = tourism_score(c)
    return int(eco * 0.40 + sci * 0.25 + tour * 0.10 + c["population"] / 5000 + military_power(c) / 5)

def upkeep_factor(c: dict) -> float:
    """Progressive upkeep (late-game money sink): free up to 10 buildings, then
    +6% per extra building, plus another +10% per building past 25.
    20 buildings = x1.6, 28 = x2.4, 40 = x4.3, 60 = x7.5."""
    total = sum(c["buildings"].values())
    return 1 + max(0, total - 10) * 0.06 + max(0, total - 25) * 0.10

def building_upkeep(c: dict) -> int:
    b = c["buildings"]
    base = sum(BUILDINGS[k]["upkeep"] * v for k, v in b.items())
    return int(base * (1 + mod(c, "upkeep")) * upkeep_factor(c))

def capacity(c: dict) -> int:
    """Soft population capacity of the land: area x 60 people."""
    return int(c["area"] * 60)

def adjust_cities(c: dict, delta: int):
    total = sum(city["pop"] for city in c["cities"]) or 1
    for city in c["cities"]:
        city["pop"] = max(1000, int(city["pop"] + delta * city["pop"] / total))

def plan_migration(countries: list, frac: float = 1.0) -> list:
    """Unhappy populations move to the happiest reachable country.
    frac scales the per-day rates (frac=1/24 = one hourly slice).
    Reachable = same planet, unless the DESTINATION has an interplanetary airport.
    Returns [(src_user_id, dst_user_id, amount)]."""
    moves = []
    dests = [d for d in countries if d.get("alive", True) and d.get("accept_migrants", True)
             and d["happiness"] >= 60 and not d.get("war_id")]
    for src_c in countries:
        if not src_c.get("alive", True) or src_c["happiness"] >= 45 or src_c.get("war_id"):
            continue
        if src_c["population"] <= 30000:
            continue
        reachable = [d for d in dests if d["user_id"] != src_c["user_id"]
                     and (d["planet"] == src_c["planet"] or d["buildings"].get("airport_inter", 0) > 0)
                     and d["population"] < capacity(d) * 1.05]
        if not reachable:
            continue
        dst = max(reachable, key=lambda d: d["happiness"])
        headroom = int(capacity(dst) * 1.05 - dst["population"])
        amount = min(int(src_c["population"] * 0.002 * frac), int(3000 * frac), headroom)
        if amount >= max(1, int(100 * frac)):
            moves.append((src_c["user_id"], dst["user_id"], amount))
    return moves

def econ_tick(c: dict, frac: float = 1.0):
    """Economy slice: production, consumption, taxes, factory income and upkeep
    for `frac` of a day. Runs hourly with frac=1/24 (so resources and money flow
    every real hour) and inside daily_tick with frac=1. Fractional amounts are
    carried in c['carry'] so nothing is lost to rounding; the day's totals
    accumulate in c['fin_day'] for the finance view."""
    b = c["buildings"]
    prod = production(c)
    cons = {"food": c["population"] * 0.010,
            "water": c["population"] * 0.008,
            "energy": c["population"] * 0.005 + sum(b.values()) * 60}
    carry = c.setdefault("carry", {})
    for r in prod:
        total = carry.get(r, 0.0) + (prod[r] - cons.get(r, 0)) * frac
        applied = int(total) if total >= 0 else -int(-total)
        carry[r] = total - applied
        c["res"][r] = max(0, int(c["res"].get(r, 0) + applied))
    tax_factor = {1: 0.6, 2: 1.0, 3: 1.6}[c["tax_rate"]]
    income = c["population"] * 0.004 * tax_factor * (1 + mod(c, "economy"))
    ub = building_upkeep(c)
    ua = c.get("soldiers", 0) * 0.15
    civic = c["population"] * 0.0008
    factory_income = b.get("factory", 0) * 120
    net = (income + factory_income - ub - ua - civic) * frac
    cm = carry.get("__money__", 0.0) + net
    whole = int(cm) if cm >= 0 else -int(-cm)
    carry["__money__"] = cm - whole
    c["money"] += whole
    fd = c.setdefault("fin_day", {})
    fd["tax"] = fd.get("tax", 0.0) + income * frac
    fd["factory"] = fd.get("factory", 0.0) + factory_income * frac
    fd["upkeep_buildings"] = fd.get("upkeep_buildings", 0.0) + ub * frac
    fd["upkeep_army"] = fd.get("upkeep_army", 0.0) + ua * frac
    fd["civic"] = fd.get("civic", 0.0) + civic * frac

def hourly_tick(c: dict, t: int = None, hours: int = 1) -> dict:
    """One hourly slice of the living simulation (daily_tick only snapshots and
    reports): economy 1/24 per hour, births & deaths, happiness drift, research
    points, countryless-pool migration, protest/collapse counters in hours.
    Fractional amounts ride in c['carry'] so 24 slices == 1 day."""
    t = t or now_ts()
    b = c["buildings"]
    carry = c.setdefault("carry", {})
    econ_tick(c, hours / 24)
    shortage = any(c["res"][r] <= 0 for r in ("food", "water", "energy"))
    if shortage:
        c["shortage_hours"] = c.get("shortage_hours", 0) + hours
    else:
        c["shortage_hours"] = 0
    c["shortage_days"] = c.get("shortage_hours", 0) // 24
    # research points: hourly share of the daily 2 + 6 per university
    rp_f = carry.get("rp", 0.0) + (2 + b.get("university", 0) * 6) * hours / 24
    rp_add = int(rp_f); carry["rp"] = rp_f - rp_add
    c["rp"] += rp_add
    c["day_rp"] = c.get("day_rp", 0) + rp_add
    # happiness: drift toward the target (the old daily step moved halfway/day)
    h_target = 55 + mod(c, "happiness") + b.get("hospital", 0) * 2 + b.get("university", 0)
    h_target -= {1: -4, 2: 0, 3: 9}[c["tax_rate"]]
    if shortage:
        # consecutive shortage hurts more and more (scaled from days to hours)
        h_target -= 25 + min(20, 5 * (c.get("shortage_hours", 0) / 24))
    if c["money"] < 0:
        h_target -= 10
        c["money"] = max(c["money"], -500)
    step = 1 - 0.5 ** (1 / 24)
    for _ in range(hours):
        c["happiness"] = c["happiness"] + (h_target - c["happiness"]) * step
    c["happiness"] = max(0.0, min(100.0, c["happiness"]))
    # ---- births & deaths ----
    hosp = b.get("hospital", 0)
    births_rate = (0.0050 * (0.8 + c["happiness"] / 100 * 0.45) + hosp * 0.0002) * (1 + mod(c, "pop_growth"))
    deaths_rate = 0.0024 * (1.35 - c["happiness"] / 100 * 0.55) * (1 - min(0.4, hosp * 0.06))
    if shortage:
        births_rate *= 0.55
        deaths_rate *= 2.3
    if c.get("war_id"):
        deaths_rate += 0.0004
    ratio = c["population"] / max(1, capacity(c))
    damp = max(0.0, 1 - (ratio - 0.8) / 0.4) if ratio > 0.8 else 1.0
    bf = carry.get("births", 0.0) + c["population"] * births_rate * damp * hours / 24
    births = int(bf); carry["births"] = bf - births
    df = carry.get("deaths", 0.0) + c["population"] * deaths_rate * hours / 24
    deaths = int(df); carry["deaths"] = df - deaths
    old_pop = c["population"]
    new_pop = old_pop + births - deaths
    if new_pop < 10000:
        deaths -= (10000 - new_pop)
        new_pop = 10000
    c["population"] = new_pop
    adjust_cities(c, new_pop - old_pop)
    c["day_births"] = c.get("day_births", 0) + births
    c["day_deaths"] = c.get("day_deaths", 0) + deaths
    # countryless pool migration (hourly share of the daily rate)
    if c.get("accept_migrants", True) and c["happiness"] >= 55 and not shortage and not c.get("war_id"):
        attract = 0.5 + (c["happiness"] - 55) / 45.0 + {1: 0.3, 2: 0.0, 3: -0.3}[c["tax_rate"]]
        headroom = int(capacity(c) * 1.1 - c["population"])
        if attract > 0 and headroom > 0:
            mig = min(int(c["population"] * 0.0015 * attract * hours / 24), headroom)
            if mig > 0:
                c["population"] += mig
                adjust_cities(c, mig)
                c["day_pool"] = c.get("day_pool", 0) + mig
    # tourism: visitors arrive, stay ~3 days, spend money every hour
    tr = tourism_rates(c)
    if tr["cap"] > 0:
        visitors = c.get("tourists", 0.0)
        arr_h = tr["arrivals"] / 24 * hours
        dep_h = visitors * hours / 72.0
        visitors = max(0.0, min(tr["cap"], visitors + arr_h - dep_h))
        c["tourists"] = visitors
        tf = carry.get("tour_income", 0.0) + visitors * tr["spend"] * hours / 24
        tour_income = int(tf); carry["tour_income"] = tf - tour_income
        if tour_income:
            c["money"] += tour_income
            fd = c.setdefault("fin_day", {}); fd["tourism"] = fd.get("tourism", 0) + tour_income
        c["day_tour_arr"] = c.get("day_tour_arr", 0) + arr_h
    # protests & collapse (hour counters; collapse needs ~3+ days under 15%)
    stability = 1 - mod(c, "stability")
    if c["happiness"] < 30:
        c["protest_hours"] = c.get("protest_hours", 0) + hours
    else:
        c["protest_hours"] = max(0, c.get("protest_hours", 0) - hours)
    c["protest_days"] = c.get("protest_hours", 0) // 24
    collapsed = c["happiness"] < 15 and c.get("protest_hours", 0) >= (int(3 * stability) + 1) * 24
    return {"collapsed": collapsed, "shortage": shortage}

def daily_tick(c: dict, t: int = None) -> dict:
    """Daily snapshot & report only. The living simulation (economy, births and
    deaths, happiness, RP, migration) runs hourly in hourly_tick; this snapshots
    the accumulated day totals, rolls a random event and builds the report."""
    t = t or now_ts()
    report = []
    fd = c.get("fin_day", {})
    trade_in = c.get("fin_trade", 0)
    c["fin_trade"] = 0
    income = int(fd.get("tax", 0)); factory_income = int(fd.get("factory", 0))
    upkeep_buildings = int(fd.get("upkeep_buildings", 0))
    upkeep_army = int(fd.get("upkeep_army", 0)); civic = int(fd.get("civic", 0))
    upkeep = upkeep_buildings + upkeep_army + civic
    tour_income_day = int(fd.get("tourism", 0))
    c["last_fin"] = {"tax": income, "factory": factory_income, "trade": trade_in,
                     "tourism": tour_income_day,
                     "upkeep_buildings": upkeep_buildings, "upkeep_army": upkeep_army,
                     "civic": civic, "net_tick": income + factory_income + tour_income_day - upkeep}
    c["last_tour"] = {"arrivals": int(c.get("day_tour_arr", 0)), "income": tour_income_day}
    c["day_tour_arr"] = 0
    c["fin_day"] = {}
    rp_gain = c.get("day_rp", 0); c["day_rp"] = 0
    # demographics & migration snapshots (accumulated by the hourly slices)
    births = c.get("day_births", 0); deaths = c.get("day_deaths", 0)
    c["last_births"] = births; c["last_deaths"] = deaths
    c["day_births"] = 0; c["day_deaths"] = 0
    pool = c.get("day_pool", 0); c["last_mig_pool"] = pool; c["day_pool"] = 0
    mig_in = c.get("mig_in_today", []); mig_out = c.get("mig_out_today", 0)
    c["last_mig_in"] = mig_in; c["last_mig_out"] = mig_out
    c["mig_in_today"] = []; c["mig_out_today"] = 0
    mig_in_total = sum(m["amount"] for m in mig_in)
    c["last_pop_delta"] = births - deaths + pool + mig_in_total - mig_out
    if pool > 0:
        report.append(f"🧳 مهاجران بی‌کشور: +{pool:,} نفر وارد کشورت شدند.")
    if mig_in_total > 0:
        report.append(f"🧳 مهاجران از کشورهای دیگر: +{mig_in_total:,} نفر به کشورت آمدند.")
    if mig_out > 0:
        report.append(f"🧳 مهاجرت خروجی: −{mig_out:,} نفر کشورت را ترک کردند.")
    if c["happiness"] < 30:
        report.append(f"⚠️ اعتراض در کشور! رضایت مردم {int(c['happiness'])}٪ است ({c.get('protest_days', 0)} روز اعتراض). مالیات را کم کن، غذا/آب/انرژی را تأمین کن یا ساختمان رفاهی بساز.")
    # random event (12%)
    event = None
    if random.random() < 0.12:
        event = random.choice(RANDOM_EVENTS)
        for k, v in event["effects"].items():
            if k == "happiness":
                c["happiness"] = max(0, min(100, c["happiness"] + v))
            elif k == "money":
                c["money"] += v
            elif k == "rp":
                c["rp"] += v
            else:
                c["res"][k] = max(0, c["res"].get(k, 0) + v)
        report.append(f"{event['fa']}: {event['text']}")
    c["last_daily_ts"] = t
    if tour_income_day > 0:
        report.append(f"🏖️ گردشگری: {c['last_tour']['arrivals']:,} گردشگر آمدند و {tour_income_day:,} 💰 خرج کردند.")
    report.append(f"📊 گزارش روزانه: درآمد {income + factory_income:,}، هزینه نگهداری {upkeep:,}، امتیاز تحقیق +{rp_gain}، جمعیت {c['population']:,}")

    report.append(f"👶 تولد: +{births:,} | ⚰️ مرگ‌ومیر: −{deaths:,} | خالص جمعیت: {births - deaths:+,}")
    return {"report": report, "collapsed": False, "event": event}

def resolve_war(war: dict, attacker: dict, defender: dict) -> dict:
    """Mutates both countries. Returns outcome dict."""
    a_score = war["att_score"] + military_power(attacker)
    d_score = war["def_score"] + defense_power(defender)
    outcome = {"a_score": a_score, "d_score": d_score}
    if a_score > d_score * 1.5:
        outcome["result"] = "annex"
        attacker["area"] += defender["area"]
        for r in defender["res"]:
            attacker["res"][r] += defender["res"][r] // 2
        for m, cnt in defender["mines"].items():
            attacker["mines"][m] = attacker["mines"].get(m, 0) + cnt
        attacker["money"] += defender["money"] // 2
        defender["alive"] = False
    elif a_score > d_score:
        outcome["result"] = "partial"
        taken = int(defender["area"] * 0.25)
        defender["area"] -= taken
        attacker["area"] += taken
        outcome["taken"] = taken
        for m in list(defender["mines"].keys()):
            if defender["mines"][m] > 0 and random.random() < 0.4:
                defender["mines"][m] -= 1
                attacker["mines"][m] = attacker["mines"].get(m, 0) + 1
        rep = defender["money"] // 4
        defender["money"] -= rep
        attacker["money"] += rep
        defender["happiness"] = max(0, defender["happiness"] - 12)
    else:
        outcome["result"] = "defended"
        rep = attacker["money"] // 5
        attacker["money"] -= rep
        defender["money"] += rep
        attacker["happiness"] = max(0, attacker["happiness"] - 8)
        outcome["reparations"] = rep
    # soldier losses
    attacker["soldiers"] = int(attacker["soldiers"] * random.uniform(0.55, 0.8))
    defender["soldiers"] = int(defender["soldiers"] * random.uniform(0.5, 0.75))
    attacker["war_id"] = None
    defender["war_id"] = None
    # post-war peace: neither side can start or be targeted by a new war for 3 days
    peace = now_ts() + 3 * DAY
    attacker["peace_until"] = peace
    defender["peace_until"] = peace
    return outcome

_CITY_ROOTS = ["Ar", "Bel", "Cor", "Dra", "El", "Fal", "Gor", "Hel", "Il", "Kor",
               "Lun", "Mar", "Nor", "Ost", "Rav", "Sel", "Tor", "Vel", "Zar", "Xan",
               "Bran", "Kel", "Mir", "Tal", "Vor", "Ash", "Dun", "Gal"]
_CITY_SUFFIXES = ["ia", "opolis", "grad", "port", "haven", "reach", "fall", "crest",
                  "mere", "spire", "holm", "wick", "bourne", "gate"]

def random_city_name(taken=()) -> str:
    """A generated English city name not in `taken` (used when a player skips
    naming one of their 3 big cities — naming them is optional)."""
    taken_l = {str(t).lower() for t in taken if t}
    for _ in range(60):
        name = random.choice(_CITY_ROOTS) + random.choice(_CITY_SUFFIXES)
        if name.lower() not in taken_l:
            return name
    return "New " + random.choice(_CITY_ROOTS) + random.choice(_CITY_SUFFIXES)

def country_text(c: dict) -> str:
    from game_data import PLANETS, GOVERNMENTS, RESOURCES
    p = PLANETS[c["planet"]]
    mods = compute_mods(c)
    lines = [
        f"🏳️ کشور «{c['name']}» — پایتخت: {c['capital']}",
        f"🪐 سیاره: {p['name']} ({p['fa']}) | قاره: {p['continents'][c['continent']]['name']}",
        f"🏛️ حکومت: {GOVERNMENTS[c['government']]['fa']}",
        f"👥 جمعیت: {c['population']:,} | 🗺️ مساحت: {c['area']:,} کیلومتر مربع",
        f"😊 رضایت مردم: {int(round(c['happiness']))}٪ | 💰 خزانه: {c['money']:,} | 🔬 امتیاز تحقیق: {c['rp']}",
        f"📊 امتیازها — 👑 قدرت ملی: {national_power(c):,} | 💰 اقتصادی: {eco_score(c)[0]:,} | 🔬 علمی: {sci_score(c)[0]:,}",
        f"🔭 شارژ اکتشاف: {c['explore_charges']}/{int(mods.get('explore_cap', 3))}",
        f"👶 تولد دیروز: +{c.get('last_births', 0):,} | ⚰️ مرگ‌ومیر دیروز: −{c.get('last_deaths', 0):,}",
        f"🪖 سرباز: {c['soldiers']:,} (قدرت نظامی: {military_power(c):,})",
        "",
        "🏙️ شهرهای بزرگ:",
    ]
    for city in c["cities"]:
        lines.append(f" • {city['name']}: {city['pop']:,} نفر")
    lines.append("\n📦 منابع:")
    for r, label in RESOURCES.items():
        extra = f" ({p['special_fa']})" if r == "special" else ""
        lines.append(f" • {label}{extra}: {c['res'].get(r, 0):,}")
    prod = production(c)
    lines.append(f"\n🏭 تولید روزانه: غذا +{int(prod['food']):,} | آب +{int(prod['water']):,} | انرژی +{int(prod['energy']):,} | مصالح +{int(prod['materials']):,} (جزئیات کامل در بخش 💰 درآمد و مالی)")
    lines.append("\n⛏️ معادن:")
    if c["mines"]:
        for r, cnt in c["mines"].items():
            lines.append(f" • {RESOURCES.get(r, r)}: {cnt} معدن")
    else:
        lines.append(" • معدنی نداری؛ با اکتشاف معدن کشف کن.")
    lines.append("\n🧭 مرزها (متنی):")
    from game_data import DIRECTIONS
    for d, label in DIRECTIONS.items():
        b = c["borders"][d]
        st = {"open": "باز برای اکتشاف", "sea": "دریا — بسته", "country": "مرز کشور دیگر — بسته"}[b["status"]]
        lines.append(f" • {label}: {b['label']} — {st}")
    if c["neighbors"]:
        lines.append(f"\n🤝 همسایه‌ها: {len(c['neighbors'])} کشور (از بخش دیپلماسی ببین)")
    return "\n".join(lines)
