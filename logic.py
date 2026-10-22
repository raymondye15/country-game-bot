# -*- coding: utf-8 -*-
"""Pure game logic operating on country dicts (no Telegram / DB imports -> unit-testable)."""
import random, time
from game_data import PLANETS, GOVERNMENTS, RESEARCH, BUILDINGS, RANDOM_EVENTS, RESOURCES

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
        "soldiers": 0, "accept_migrants": True, "fin_trade": 0, "last_fin": {}, "fin_day": {}, "carry": {},
        "mig_in_today": [], "mig_out_today": 0, "last_mig_pool": 0, "last_pop_delta": 0,
        "happiness": 65, "tax_rate": 2,  # 1=low 2=mid 3=high
        "neighbors": [], "alliances": [], "naps": [],
        "borders": borders,
        "explore_charges": 3, "last_charge_ts": t,
        "researched": [], "researching": None,  # {id, finish_ts}
        "created_ts": t, "last_daily_ts": t, "last_seen_ts": t,
        "protest_days": 0, "shortage_days": 0, "war_id": None, "peace_until": 0, "newbie_until": t + 7 * DAY,
        "last_econ_ts": t,
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

def plan_migration(countries: list) -> list:
    """Unhappy populations move to the happiest reachable country.
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
        amount = min(int(src_c["population"] * 0.002), 3000, headroom)
        if amount >= 100:
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

def daily_tick(c: dict, t: int = None) -> dict:
    """One in-game day of economy. Returns report lines + notifications."""
    t = t or now_ts()
    b = c["buildings"]
    report = []
    econ_tick(c, 1.0)
    shortage = any(c["res"][r] <= 0 for r in ("food", "water", "energy"))
    # snapshot the accumulated day totals (hourly slices + this full-day call)
    fd = c.get("fin_day", {})
    trade_in = c.get("fin_trade", 0)
    c["fin_trade"] = 0
    income = int(fd.get("tax", 0)); factory_income = int(fd.get("factory", 0))
    upkeep_buildings = int(fd.get("upkeep_buildings", 0))
    upkeep_army = int(fd.get("upkeep_army", 0)); civic = int(fd.get("civic", 0))
    upkeep = upkeep_buildings + upkeep_army + civic
    c["last_fin"] = {"tax": income, "factory": factory_income, "trade": trade_in,
                     "upkeep_buildings": upkeep_buildings, "upkeep_army": upkeep_army,
                     "civic": civic, "net_tick": income + factory_income - upkeep}
    c["fin_day"] = {}
    # research points
    rp_gain = 2 + b.get("university", 0) * 6
    c["rp"] += rp_gain
    # happiness
    h = 55 + mod(c, "happiness") + b.get("hospital", 0) * 2 + b.get("university", 0)
    h -= {1: -4, 2: 0, 3: 9}[c["tax_rate"]]
    if shortage:
        # consecutive shortage days hurt more and more (BUGFIX: flat -18 could never
        # push happiness below the protest threshold, so collapse was unreachable)
        c["shortage_days"] = c.get("shortage_days", 0) + 1
        h -= 25 + min(20, 5 * c["shortage_days"])
    else:
        c["shortage_days"] = 0
    if c["money"] < 0:
        h -= 10
        c["money"] = max(c["money"], -500)
    c["happiness"] = max(0, min(100, int(c["happiness"] * 0.5 + h * 0.5)))
    # population growth & city growth
    growth = 0.004 + (c["happiness"] - 50) / 20000.0 + mod(c, "pop_growth") * 0.002 + b.get("hospital", 0) * 0.0005
    if shortage:
        growth -= 0.004
    if growth > 0:
        ratio = c["population"] / max(1, capacity(c))
        if ratio > 0.8:  # land gets crowded: growth fades out toward capacity
            growth *= max(0.0, 1 - (ratio - 0.8) / 0.4)
    old_pop = c["population"]
    c["population"] = max(10000, int(c["population"] * (1 + growth)))
    ratio = c["population"] / max(1, old_pop)
    for city in c["cities"]:
        city["pop"] = int(city["pop"] * ratio)
    # immigrants without a country arrive daily (same-planet pool; the default
    # international airport makes every country reachable for them)
    c["mig_in_today"] = []
    c["mig_out_today"] = 0
    mig_pool = 0
    if c.get("accept_migrants", True) and c["happiness"] >= 55 and not shortage and not c.get("war_id"):
        attract = 0.5 + (c["happiness"] - 55) / 45.0 + {1: 0.3, 2: 0.0, 3: -0.3}[c["tax_rate"]]
        headroom = int(capacity(c) * 1.1 - c["population"])
        if attract > 0 and headroom > 0:
            mig_pool = min(int(c["population"] * 0.0015 * attract), headroom)
            if mig_pool > 0:
                c["population"] += mig_pool
                adjust_cities(c, mig_pool)
                report.append(f"🧳 مهاجران بی‌کشور: +{mig_pool:,} نفر وارد کشورت شدند.")
    c["last_mig_pool"] = mig_pool
    c["last_pop_delta"] = c["population"] - old_pop
    # protests / collapse
    collapsed = False
    stability = 1 - mod(c, "stability")
    if c["happiness"] < 30:
        c["protest_days"] += 1
        report.append(f"⚠️ اعتراض در کشور! رضایت مردم {c['happiness']}٪ است (روز {c['protest_days']} اعتراض). مالیات را کم کن، غذا/آب/انرژی را تأمین کن یا ساختمان رفاهی بساز.")
    else:
        c["protest_days"] = max(0, c["protest_days"] - 1)
    if c["happiness"] < 15 and c["protest_days"] >= int(3 * stability) + 1:
        collapsed = True
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
    report.append(f"📊 گزارش روزانه: درآمد {income + factory_income:,}، هزینه نگهداری {upkeep:,}، امتیاز تحقیق +{rp_gain}، جمعیت {c['population']:,}")
    return {"report": report, "collapsed": collapsed, "event": event}

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

def country_text(c: dict) -> str:
    from game_data import PLANETS, GOVERNMENTS, RESOURCES
    p = PLANETS[c["planet"]]
    mods = compute_mods(c)
    lines = [
        f"🏳️ کشور «{c['name']}» — پایتخت: {c['capital']}",
        f"🪐 سیاره: {p['name']} ({p['fa']}) | قاره: {p['continents'][c['continent']]['name']}",
        f"🏛️ حکومت: {GOVERNMENTS[c['government']]['fa']}",
        f"👥 جمعیت: {c['population']:,} | 🗺️ مساحت: {c['area']:,} کیلومتر مربع",
        f"😊 رضایت مردم: {c['happiness']}٪ | 💰 خزانه: {c['money']:,} | 🔬 امتیاز تحقیق: {c['rp']}",
        f"🔭 شارژ اکتشاف: {c['explore_charges']}/{int(mods.get('explore_cap', 3))}",
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
