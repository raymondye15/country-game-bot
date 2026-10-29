# -*- coding: utf-8 -*-
"""Game static data: planets, continents, governments, buildings, research tree.
All presentation is TEXT ONLY (no maps / images) by design decision."""

RESOURCES = {
    "food": "🍞 غذا",
    "water": "💧 آب",
    "energy": "⚡ انرژی",
    "materials": "🧱 مصالح",
    "iron": "⛏️ آهن",
    "titanium": "🔩 تیتانیوم",
    "vexium": "💎 وکسیوم",
    "deepoil": "🛢️ نفت ژرف",
    "zyphgas": "🟣 گاز زیفرا",
}

PLANETS = {
    "vexus": {
        "name": "Vexus",
        "fa": "وکسوس",
        "capacity": 400,
        "special_name": "Vexium",
        "special_fa": "وکسیوم",
        "special_res": "vexium",
        "desc": "سیاره‌ای خشک و بیابانی، فقیر از آب اما بسیار غنی از معدن. تجارت آب در آن طلاست.",
        "continents": {
            "kharun": {
                "name": "Kharun", "fa": "خارون",
                "desc": "بیابان مرکزی وکسوس؛ معدن فراوان، کشاورزی سخت.",
                "mods": {"mine_prod": 0.30, "food_prod": -0.20},
                "mine_weights": {"iron": 35, "titanium": 30, "special": 25, "materials": 10},
                "terrains": ["بیابان شنی خارون", "فلات سنگی", "دره خشک"],
                "seas": ["دریای نمک Salar Sea"],
            },
            "solmere": {
                "name": "Solmere", "fa": "سولمیر",
                "desc": "قاره ساحلی وکسوس؛ دسترسی به دریا، تجارت قوی‌تر، آب بیشتر.",
                "mods": {"trade": 0.15, "water_prod": 0.25},
                "mine_weights": {"iron": 30, "materials": 30, "titanium": 20, "special": 20},
                "terrains": ["ساحل شنی", "دشت ساحلی", "تپه‌های سبز"],
                "seas": ["اقیانوس Solmere Ocean"],
            },
            "cryovex": {
                "name": "Cryovex", "fa": "کرایووکس",
                "desc": "ناحیه قطبی وکسوس؛ انرژی زمین‌گرمایی بالا، رشد جمعیت کند.",
                "mods": {"energy_prod": 0.25, "pop_growth": -0.15},
                "mine_weights": {"titanium": 35, "iron": 30, "special": 20, "materials": 15},
                "terrains": ["یخ‌بندان قطبی", "دشت یخی", "کوه آتشفشانی خاموش"],
                "seas": ["دریای یخی Frozen Reach"],
            },
        },
    },
    "thalassa": {
        "name": "Thalassa Prime",
        "fa": "تالاسا پرایم",
        "capacity": 1000,
        "special_name": "Deep Oil",
        "special_fa": "نفت ژرف",
        "special_res": "deepoil",
        "desc": "سیاره اقیانوسی؛ جزیره‌ها و قاره‌های ساحلی، غذای دریایی و تجارت دریایی قوی، معدن خشکی کم.",
        "continents": {
            "pelagia": {
                "name": "Pelagia", "fa": "پلاگیا",
                "desc": "مجمع‌الجزایر بزرگ؛ تجارت و غذا عالی، زمین محدود.",
                "mods": {"trade": 0.25, "food_prod": 0.20},
                "mine_weights": {"special": 35, "materials": 30, "iron": 20, "titanium": 15},
                "terrains": ["جزیره مرجانی", "ساحل گرمسیری", "لاگون"],
                "seas": ["اقیانوس Pelagic Ocean"],
            },
            "coralis": {
                "name": "Coralis", "fa": "کورالیس",
                "desc": "قاره مرجانی؛ متعادل، آب و انرژی موجی فراوان.",
                "mods": {"energy_prod": 0.15, "water_prod": 0.20},
                "mine_weights": {"iron": 30, "special": 30, "materials": 25, "titanium": 15},
                "terrains": ["صخره مرجانی", "دشت ساحلی", "جنگل بارانی ساحلی"],
                "seas": ["دریای Coral Sea"],
            },
            "tempest": {
                "name": "Tempest Isles", "fa": "جزایر تمپست",
                "desc": "جزایر طوفانی؛ انرژی بادی بسیار بالا، زندگی سخت و جمعیت سرسخت.",
                "mods": {"energy_prod": 0.35, "happiness": -5},
                "mine_weights": {"titanium": 30, "iron": 30, "special": 20, "materials": 20},
                "terrains": ["جزیره بادخیز", "صخره طوفانی", "فلات باز"],
                "seas": ["اقیانوس Tempest Ocean"],
            },
        },
    },
    "zyphera": {
        "name": "Zyphera",
        "fa": "زیفرا",
        "capacity": 650,
        "special_name": "Zyph Gas",
        "special_fa": "گاز زیفرا",
        "special_res": "zyphgas",
        "desc": "سیاره‌ای با آب‌وهوای متنوع؛ جنگل‌های متراکم، دشت‌ها و ناحیه‌های یخی. متعادل‌ترین سیاره.",
        "continents": {
            "verdania": {
                "name": "Verdania", "fa": "وردانیا",
                "desc": "جنگل‌های انبوه؛ غذا و چوب فراوان، گسترش کندتر میان درختان.",
                "mods": {"food_prod": 0.30, "materials_prod": 0.15},
                "mine_weights": {"materials": 35, "iron": 25, "special": 20, "titanium": 20},
                "terrains": ["جنگل انبوه", "دشت رودخانه‌ای", "تپه جنگلی"],
                "seas": ["دریای Verdant Sea"],
            },
            "glaciera": {
                "name": "Glaciera", "fa": "گلاسیرا",
                "desc": "سرزمین یخی شمال؛ معدن و گاز زیر یخ، کشاورزی تقریباً ناممکن.",
                "mods": {"mine_prod": 0.20, "food_prod": -0.30, "energy_prod": 0.10},
                "mine_weights": {"special": 35, "titanium": 30, "iron": 25, "materials": 10},
                "terrains": ["یخچال طبیعی", "توندرای یخی", "کوه یخی"],
                "seas": ["اقیانوس منجمد Northern Deep"],
            },
            "montara": {
                "name": "Montara", "fa": "مونتارا",
                "desc": "فلات کوهستانی؛ دفاع طبیعی عالی در جنگ، مصالح و فلز خوب.",
                "mods": {"defense": 0.20, "materials_prod": 0.20},
                "mine_weights": {"iron": 35, "titanium": 30, "materials": 20, "special": 15},
                "terrains": ["فلات کوهستانی", "دره عمیق", "دامنه سنگی"],
                "seas": ["دریای Montara Gulf"],
            },
        },
    },
}

GOVERNMENTS = {
    "democracy": {
        "fa": "جمهوری دموکراتیک", "emoji": "🗳️",
        "guide": "رضایت مردم و رشد جمعیت بالا؛ اما تصمیم‌های جنگی کندتر و ارتش کمی ضعیف‌تر.",
        "mods": {"happiness": 8, "pop_growth": 0.20, "military": -0.05},
    },
    "empire": {
        "fa": "امپراتوری", "emoji": "👑",
        "guide": "امتیاز جنگی و سرعت اکتشاف بالا؛ مردم سرزمین‌های فتح‌شده ناراضی‌ترند.",
        "mods": {"military": 0.15, "explore": 0.10, "happiness": -4},
    },
    "technocracy": {
        "fa": "تکنوکراسی", "emoji": "🧠",
        "guide": "سرعت تحقیق +۳۰٪؛ هزینه نگهداری ساختمان‌ها بیشتر.",
        "mods": {"research_speed": 0.30, "upkeep": 0.20},
    },
    "junta": {
        "fa": "حکومت نظامی", "emoji": "🎖️",
        "guide": "ارتش قوی و ارزان؛ اقتصاد و تجارت ضعیف‌تر.",
        "mods": {"military": 0.20, "trade": -0.15, "economy": -0.10},
    },
    "monarchy": {
        "fa": "پادشاهی", "emoji": "🏰",
        "guide": "ثبات بالا و اعتراض دیرتر؛ تحقیق کندتر.",
        "mods": {"happiness": 5, "stability": 0.25, "research_speed": -0.10},
    },
    "corporate": {
        "fa": "شرکت‌دولت", "emoji": "🏢",
        "guide": "درآمد تجارت +۳۰٪؛ رضایت مردم پایین‌تر و اعتراض زودتر.",
        "mods": {"trade": 0.30, "economy": 0.15, "happiness": -6},
    },
    "federation": {
        "fa": "فدراسیون", "emoji": "🤝",
        "guide": "همسایگی و اتحاد بسیار قوی‌تر و ارزان‌تر؛ درآمد مالیات کمتر.",
        "mods": {"diplomacy": 0.25, "economy": -0.05, "happiness": 4},
    },
    "theocracy": {
        "fa": "دولت ایدئولوژیک", "emoji": "🕊️",
        "guide": "وفاداری و ثبات داخلی بالا؛ تحقیق و تجارت خارجی کندتر.",
        "mods": {"stability": 0.30, "happiness": 3, "research_speed": -0.10, "trade": -0.10},
    },
}

BUILDINGS = {
    "farm":      {"fa": "🌾 مزرعه",        "cost": {"materials": 40, "money": 200},  "upkeep": 6,  "desc": "تولید غذا"},
    "waterplant":{"fa": "🚰 تصفیه‌خانه آب", "cost": {"materials": 50, "money": 250},  "upkeep": 7,  "desc": "تولید آب"},
    "powerplant":{"fa": "🔋 نیروگاه",       "cost": {"materials": 60, "iron": 20, "money": 300}, "upkeep": 9, "desc": "تولید انرژی"},
    "mine":      {"fa": "⛏️ معدن پیشرفته",  "cost": {"materials": 50, "money": 300},  "upkeep": 9,  "desc": "افزایش برداشت همه معادن"},
    "factory":   {"fa": "🏭 کارخانه",       "cost": {"materials": 80, "iron": 30, "money": 400}, "upkeep": 12, "desc": "تولید مصالح و درآمد"},
    "refinery":  {"fa": "🧪 پالایشگاه",      "cost": {"materials": 90, "iron": 40, "money": 800}, "upkeep": 14, "desc": "مصرف منبع خاص سیارهٔ خودت؛ تولید انرژی و امتیاز تحقیق"},
    "university":{"fa": "🎓 دانشگاه",       "cost": {"materials": 70, "money": 500},  "upkeep": 15,  "desc": "امتیاز تحقیق روزانه"},
    "hospital":  {"fa": "🏥 بیمارستان",     "cost": {"materials": 60, "money": 400},  "upkeep": 12,  "desc": "رضایت و رشد جمعیت"},
    "barracks":  {"fa": "🪖 پادگان",        "cost": {"materials": 70, "iron": 20, "money": 350}, "upkeep": 11, "desc": "ظرفیت و قدرت ارتش"},
    "airport_inter": {"fa": "🛸 فرودگاه بین‌سیاره‌ای", "cost": {"materials": 200, "iron": 200, "titanium": 80, "vexium": 15, "deepoil": 15, "zyphgas": 15, "money": 6000}, "upkeep": 90, "desc": "مهاجرت و گردشگر از سیاره‌های دیگر"},
    "hotel": {"fa": "🏨 هتل گردشگری", "cost": {"materials": 60, "money": 1200}, "upkeep": 15, "desc": "پذیرش گردشگر و درآمد از آن‌ها"},
}

# Domestic policies: the player picks ONE option per category (or none).
# Effects merge into logic.compute_mods like research effects; a few keys are
# read directly where they apply (tax, factory, civic, soldier_upkeep, births,
# deaths, migration, emigration, tourism_arrivals, tourism_spend, refinery,
# space_time, trade = market-fee discount). Changing a category locks it 12h.
POLICIES = {
    "economy": {"fa": "💵 اقتصاد و مالیات", "options": {
        "tax_haven": {"fa": "بهشت مالیاتی", "desc": "مالیات −۱۵٪ | کارمزد بازار کمتر | ورودی گردشگر +۱۵٪", "effects": {"tax": -0.15, "trade": 0.20, "tourism_arrivals": 0.15}},
        "wealth_tax": {"fa": "مالیات بر ثروت", "desc": "مالیات +۱۵٪ | رضایت −۳", "effects": {"tax": 0.15, "happiness": -3}},
        "state_econ": {"fa": "اقتصاد دولتی", "desc": "درآمد کارخانه +۲۵٪ | کارمزد بازار بیشتر", "effects": {"factory": 0.25, "trade": -0.15}},
    }},
    "migration": {"fa": "👥 مهاجرت", "options": {
        "open_doors": {"fa": "درهای باز", "desc": "مهاجرت ورودی ×۲ | رضایت −۲", "effects": {"migration": 1.0, "happiness": -2}},
        "closed": {"fa": "مرز بسته", "desc": "مهاجرت ورودی صفر | خروج مردم −۸۰٪ | ثبات +۱۵٪", "effects": {"migration": -1.0, "emigration": -0.8, "stability": 0.15}},
        "elites": {"fa": "جذب نخبگان", "desc": "مهاجرت ورودی +۳۰٪ | سرعت تحقیق +۵٪", "effects": {"migration": 0.3, "research_speed": 0.05}},
    }},
    "welfare": {"fa": "🏥 رفاه و بهداشت", "options": {
        "generous": {"fa": "رفاه سخاوتمندانه", "desc": "رضایت +۶ | تولد +۱۰٪ | هزینه شهری +۴۰٪", "effects": {"happiness": 6, "births": 0.10, "civic": 0.40}},
        "insurance": {"fa": "بیمه همگانی", "desc": "مرگ‌ومیر −۲۰٪ | هزینه شهری +۲۰٪", "effects": {"deaths": -0.20, "civic": 0.20}},
        "minimal": {"fa": "دولت حداقلی", "desc": "هزینه شهری −۴۰٪ | رضایت −۵ | مرگ‌ومیر +۱۰٪", "effects": {"civic": -0.40, "happiness": -5, "deaths": 0.10}},
    }},
    "education": {"fa": "🎓 آموزش", "options": {
        "free_edu": {"fa": "آموزش رایگان", "desc": "سرعت تحقیق +۱۵٪ | هزینه شهری +۱۵٪", "effects": {"research_speed": 0.15, "civic": 0.15}},
        "technical": {"fa": "آموزش فنی‌وحرفه‌ای", "desc": "درآمد کارخانه +۱۵٪ | تولید مصالح +۱۰٪ | سرعت تحقیق −۵٪", "effects": {"factory": 0.15, "materials_prod": 0.10, "research_speed": -0.05}},
        "military_edu": {"fa": "آموزش نظامی", "desc": "قدرت ارتش +۱۰٪ | سرعت تحقیق −۵٪", "effects": {"military": 0.10, "research_speed": -0.05}},
    }},
    "military": {"fa": "🪖 نظامی", "options": {
        "conscription": {"fa": "سربازی اجباری", "desc": "هزینه سرباز −۵۰٪ | قدرت ارتش +۱۰٪ | رضایت −۴", "effects": {"soldier_upkeep": -0.50, "military": 0.10, "happiness": -4}},
        "professional": {"fa": "ارتش حرفه‌ای", "desc": "هزینه سرباز +۵۰٪ | قدرت ارتش +۲۰٪", "effects": {"soldier_upkeep": 0.50, "military": 0.20}},
        "pacifist": {"fa": "صلح‌طلبی", "desc": "ارتش و دفاع −۱۵٪ | رضایت +۴ | ورودی گردشگر +۱۰٪", "effects": {"military": -0.15, "defense": -0.15, "happiness": 4, "tourism_arrivals": 0.10}},
    }},
    "energy": {"fa": "🌱 انرژی و محیط زیست", "options": {
        "green": {"fa": "انرژی سبز", "desc": "تولید انرژی +۱۵٪ | برداشت معدن −۱۰٪ | ورودی گردشگر +۱۰٪", "effects": {"energy_prod": 0.15, "mine_prod": -0.10, "tourism_arrivals": 0.10}},
        "industry_first": {"fa": "صنعت به هر قیمت", "desc": "برداشت معدن +۲۰٪ | درآمد کارخانه +۱۵٪ | رضایت −۵ | ورودی گردشگر −۱۵٪", "effects": {"mine_prod": 0.20, "factory": 0.15, "happiness": -5, "tourism_arrivals": -0.15}},
        "eco_protection": {"fa": "حفاظت محیط زیست", "desc": "رضایت +۲ | ورودی گردشگر +۱۵٪ | تولید انرژی −۱۰٪ | برداشت معدن −۵٪", "effects": {"happiness": 2, "tourism_arrivals": 0.15, "energy_prod": -0.10, "mine_prod": -0.05}},
    }},
    "culture": {"fa": "🏖️ فرهنگ و گردشگری", "options": {
        "tourist_open": {"fa": "کشور توریستی", "desc": "ورودی گردشگر +۲۵٪ | خرج گردشگر +۱۰٪ | ثبات −۱۵٪", "effects": {"tourism_arrivals": 0.25, "tourism_spend": 0.10, "stability": -0.15}},
        "traditional": {"fa": "فرهنگ سنتی", "desc": "ورودی گردشگر −۲۰٪ | رضایت +۵ | ثبات +۲۵٪", "effects": {"tourism_arrivals": -0.20, "happiness": 5, "stability": 0.25}},
        "festival": {"fa": "جشنواره دائمی", "desc": "خرج گردشگر +۲۵٪ | هزینه شهری +۲۰٪", "effects": {"tourism_spend": 0.25, "civic": 0.20}},
    }},
    "industry": {"fa": "🔬 صنعت و فناوری", "options": {
        "tech_hub": {"fa": "قطب فناوری", "desc": "سرعت تحقیق +۱۰٪ | بازده پالایشگاه +۵۰٪", "effects": {"research_speed": 0.10, "refinery": 0.50}},
        "self_sufficiency": {"fa": "خودکفایی", "desc": "غذا، آب و انرژی +۱۰٪ | کارمزد بازار بیشتر", "effects": {"food_prod": 0.10, "water_prod": 0.10, "energy_prod": 0.10, "trade": -0.10}},
        "free_trade": {"fa": "تجارت آزاد جهانی", "desc": "کارمزد بازار خیلی کمتر | درآمد کارخانه −۱۰٪", "effects": {"trade": 0.25, "factory": -0.10}},
    }},
    "order": {"fa": "⚖️ نظم و آزادی", "options": {
        "authoritarian": {"fa": "دولت مقتدر", "desc": "ثبات +۴۰٪ (فروپاشی خیلی دیرتر) | رضایت −۶", "effects": {"stability": 0.40, "happiness": -6}},
        "civil_liberty": {"fa": "آزادی مدنی", "desc": "رضایت +۶ | ثبات −۲۰٪ | سرعت تحقیق +۵٪", "effects": {"happiness": 6, "stability": -0.20, "research_speed": 0.05}},
        "justice": {"fa": "عدالت و تعادل", "desc": "ثبات +۱۵٪ | رضایت +۲", "effects": {"stability": 0.15, "happiness": 2}},
    }},
    "space": {"fa": "🚀 فضا", "options": {
        "space_focus": {"fa": "تمرکز فضایی", "desc": "زمان ساخت پروژه‌های فضایی −۲۵٪ | سرعت تحقیق +۵٪", "effects": {"space_time": -0.25, "research_speed": 0.05}},
        "earth_first": {"fa": "زمین اول", "desc": "زمان ساخت پروژه‌های فضایی +۲۵٪ | تولید غذا +۱۰٪", "effects": {"space_time": 0.25, "food_prod": 0.10}},
        "space_diplomacy": {"fa": "دیپلماسی فضایی", "desc": "زمان فضایی −۱۰٪ | کارمزد بازار کمتر | ورودی گردشگر +۵٪", "effects": {"space_time": -0.10, "trade": 0.10, "tourism_arrivals": 0.05}},
    }},
}

# Interplanetary Council (IC) laws: players vote each term; the winning law
# applies to EVERY country until the next term. Effects live in logic.py
# (via c["active_law"]) and in main.py (market fees, war declarations).
LAWS = {
    "peace": {"fa": "🕊️ صلح کهکشانی", "desc": "در مدت این قانون هیچ کشوری نمی‌تواند اعلان جنگ جدید بدهد."},
    "tourism_boom": {"fa": "🎪 رونق گردشگری", "desc": "ورودی گردشگر همه کشورها +۵۰٪."},
    "free_market": {"fa": "🆓 بازار آزاد", "desc": "کارمزد بورس و بازار جهانی صفر می‌شود."},
    "food_program": {"fa": "🌾 برنامه غذایی اضطراری", "desc": "تولید غذای همه کشورها +۲۵٪."},
    "science_week": {"fa": "🔬 هفته علم کهکشانی", "desc": "تولید امتیاز تحقیق همه کشورها +۵۰٪."},
    "mining_rush": {"fa": "⛏️ استخراج فشرده", "desc": "برداشت همه معدن‌ها +۴۰٪."},
    "open_borders": {"fa": "🧳 درهای باز", "desc": "مهاجرت به کشورهای شاد دو برابر می‌شود."},
    "industrial_boom": {"fa": "🏭 رونق صنعتی", "desc": "درآمد کارخانه‌های همه کشورها +۵۰٪."},
}

# Achievements: one-time milestones with a reward, checked continuously.
ACHIEVEMENTS = {
    "pop1m": {"fa": "👥 جمعیت میلیونی", "desc": "جمعیت کشورت به ۱ میلیون نفر برسد", "money": 1000, "rp": 0},
    "area200k": {"fa": "🗺️ امپراتوری پهناور", "desc": "مساحت کشورت به ۲۰۰٬۰۰۰ کیلومتر مربع برسد", "money": 1000, "rp": 0},
    "rich50k": {"fa": "💰 خزانه پر", "desc": "موجودی خزانه‌ات به ۵۰٬۰۰۰ 💰 برسد", "money": 0, "rp": 20},
    "scholar5": {"fa": "🔬 دانشمند", "desc": "۵ تحقیق را کامل کن", "money": 500, "rp": 30},
    "miner8": {"fa": "⛏️ معدن‌دار بزرگ", "desc": "مجموع معدن‌هایت به ۸ برسد", "money": 800, "rp": 0},
    "factory5": {"fa": "🏭 قطب صنعتی", "desc": "۵ کارخانه داشته باش", "money": 800, "rp": 0},
    "city5": {"fa": "🏙️ شهرساز", "desc": "یک شهر را به سطح ۵ برسان", "money": 1200, "rp": 0},
    "tour500": {"fa": "🏖️ قطب گردشگری", "desc": "امتیاز گردشگری‌ات به ۵۰۰ برسد", "money": 1500, "rp": 0},
    "astro": {"fa": "🚀 فضانورد", "desc": "اولین پروژه فضایی را کامل کن", "money": 1000, "rp": 20},
    "moon": {"fa": "🌕 فاتح ماه", "desc": "پایگاه قمری را بساز", "money": 3000, "rp": 50},
    "power1k": {"fa": "👑 قدرت بزرگ", "desc": "قدرت ملی‌ات به ۱۰۰۰ برسد", "money": 2000, "rp": 0},
    "trader20k": {"fa": "📈 سلطان بورس", "desc": "مجموع معاملاتت در بورس و بازار به ۲۰٬۰۰۰ 💰 برسد", "money": 1500, "rp": 0},
}

# Missions: one daily + one weekly per player, progress measured from the
# lifetime counters in c["stats"] (snapshot at assignment time).
MISSIONS_DAILY = [
    {"id": "explore3", "fa": "۳ بار اکتشاف انجام بده", "stat": "explore", "target": 3, "money": 300, "rp": 0},
    {"id": "mine1", "fa": "۱ معدن جدید کشف کن", "stat": "mines", "target": 1, "money": 500, "rp": 0},
    {"id": "fx1000", "fa": "در بورس و بازار ۱٬۰۰۰ 💰 معامله کن", "stat": "fx_value", "target": 1000, "money": 200, "rp": 0},
    {"id": "research1", "fa": "۱ تحقیق کامل کن", "stat": "research", "target": 1, "money": 0, "rp": 15},
    {"id": "build1", "fa": "۱ ساختمان بساز", "stat": "built", "target": 1, "money": 250, "rp": 0},
    {"id": "tour300", "fa": "۳۰۰ 💰 از گردشگری درآمد کسب کن", "stat": "tourism_income", "target": 300, "money": 200, "rp": 0},
]
MISSIONS_WEEKLY = [
    {"id": "explore12", "fa": "۱۲ بار اکتشاف انجام بده", "stat": "explore", "target": 12, "money": 1500, "rp": 0},
    {"id": "mine2", "fa": "۲ معدن جدید کشف کن", "stat": "mines", "target": 2, "money": 1800, "rp": 0},
    {"id": "fx8000", "fa": "در بورس و بازار ۸٬۰۰۰ 💰 معامله کن", "stat": "fx_value", "target": 8000, "money": 1200, "rp": 0},
    {"id": "research3", "fa": "۳ تحقیق کامل کن", "stat": "research", "target": 3, "money": 0, "rp": 60},
    {"id": "build4", "fa": "۴ ساختمان بساز", "stat": "built", "target": 4, "money": 1200, "rp": 0},
    {"id": "tour2500", "fa": "۲٬۵۰۰ 💰 از گردشگری درآمد کسب کن", "stat": "tourism_income", "target": 2500, "money": 1500, "rp": 0},
]

# City specializations: each city has a level (1-5) and one specialization.
# Effects scale with the city level (applied in logic.compute_mods / rates).
CITY_SPECS = {
    "agri": {"fa": "🌾 کشاورزی", "desc": "هر سطح: +۴٪ تولید غذا و +۳٪ تولید آب"},
    "industry": {"fa": "🏭 صنعتی", "desc": "هر سطح: +۵٪ تولید مصالح"},
    "science": {"fa": "🔬 علمی", "desc": "هر سطح: +۲ امتیاز تحقیق در روز"},
    "tourism": {"fa": "🏖️ توریستی", "desc": "هر سطح: +۱۲٪ ورودی گردشگر"},
    "trade": {"fa": "💰 تجاری", "desc": "هر سطح: +۳٪ درآمد (اقتصاد)"},
}

def city_upgrade_cost(level: int) -> dict:
    """Cost to upgrade a city FROM `level` to level+1."""
    cost = {"money": 600 * level, "materials": 30 * level}
    if level >= 2:
        cost["iron"] = 15 * (level - 1)
    if level >= 4:
        cost["titanium"] = 10
    # prestige tiers draw on ALL THREE planet specials -> interplanetary trade
    if level == 3:
        for k in ("vexium", "deepoil", "zyphgas"):
            cost[k] = 8
    if level >= 4:
        for k in ("vexium", "deepoil", "zyphgas"):
            cost[k] = 20
    return cost

# Space program: a sequential chain of one-time projects. Costs may include
# "rp". Effects are applied in logic (rp/day, tourism factors, special ore).
SPACE_PROJECTS = {
    "satellite": {"fa": "🛰️ ماهواره ارتباطی", "hours": 24, "score": 100, "rp_day": 3,
                  "cost": {"money": 5000, "iron": 150, "titanium": 60, "rp": 80},
                  "desc": "+۳ تحقیق در روز، +۱۵٪ ورودی گردشگر"},
    "telescope": {"fa": "🔭 آرایه تلسکوپ فضایی", "hours": 48, "score": 150, "rp_day": 6,
                  "cost": {"money": 9000, "iron": 200, "titanium": 120, "vexium": 10, "deepoil": 10, "zyphgas": 10, "rp": 150},
                  "desc": "+۶ تحقیق در روز"},
    "station": {"fa": "🛸 ایستگاه فضایی", "hours": 72, "score": 300, "rp_day": 8,
                "cost": {"money": 20000, "materials": 400, "iron": 350, "titanium": 200, "vexium": 25, "deepoil": 25, "zyphgas": 25, "rp": 300},
                "desc": "+۸ تحقیق در روز، +۳۰٪ خرج گردشگرها"},
    "moonbase": {"fa": "🌕 پایگاه قمری", "hours": 96, "score": 500, "rp_day": 10,
                 "cost": {"money": 45000, "materials": 800, "iron": 600, "titanium": 400, "vexium": 65, "deepoil": 65, "zyphgas": 65, "rp": 600},
                 "desc": "+۱۰ تحقیق در روز، +۶ از منبع خاص سیاره‌ات در روز از معادن ماه، +۳۰٪ ورودی گردشگر"},
}
SPACE_ORDER = ["satellite", "telescope", "station", "moonbase"]

# Tourism industry upgrade levels (level -> cost). Level 0 = no industry.
# Each level: more arrivals, higher spending per tourist, bigger visitor cap.
TOURISM_LEVELS = {
    1: {"money": 800, "materials": 40},
    2: {"money": 2000, "materials": 100, "iron": 40},
    3: {"money": 4500, "materials": 180, "iron": 120},
    4: {"money": 9000, "materials": 300, "iron": 200, "titanium": 40, "vexium": 10, "deepoil": 10, "zyphgas": 10},
    5: {"money": 16000, "materials": 500, "iron": 350, "titanium": 120, "vexium": 25, "deepoil": 25, "zyphgas": 25},
}

# Research tree: id -> data. branch, cost_rp, hours, prereq, effects (flat mods merged into country mods)
RESEARCH = {
    # economy
    "eco1": {"branch": "اقتصاد و صنعت", "fa": "کشاورزی مکانیزه", "cost": 20, "hours": 6,  "prereq": None,   "effects": {"food_prod": 0.20}, "desc": "تولید غذا +۲۰٪"},
    "eco2": {"branch": "اقتصاد و صنعت", "fa": "صنعت سنگین",      "cost": 45, "hours": 12, "prereq": "eco1", "effects": {"materials_prod": 0.20, "mine_prod": 0.10}, "desc": "مصالح +۲۰٪، معدن +۱۰٪"},
    "eco3": {"branch": "اقتصاد و صنعت", "fa": "بازار آزاد",      "cost": 70, "hours": 24, "prereq": "eco2", "effects": {"trade": 0.20, "economy": 0.10}, "desc": "تجارت +۲۰٪"},
    "eco4": {"branch": "اقتصاد و صنعت", "fa": "بانک مرکزی",      "cost": 110, "hours": 36, "prereq": "eco3", "effects": {"economy": 0.20}, "desc": "درآمد مالیاتی +۲۰٪"},
    "eco5": {"branch": "اقتصاد و صنعت", "fa": "اقتصاد مداری",    "cost": 180, "hours": 48, "prereq": "eco4", "effects": {"economy": 0.20, "trade": 0.15}, "res_cost": {"vexium": 15, "deepoil": 15, "zyphgas": 15}, "desc": "اقتصاد و تجارت مداری"},
    # military
    "mil1": {"branch": "نظامی", "fa": "سربازگیری سازمان‌یافته", "cost": 20, "hours": 6,  "prereq": None,   "effects": {"military": 0.10}, "desc": "قدرت ارتش +۱۰٪"},
    "mil2": {"branch": "نظامی", "fa": "تسلیحات سبک",            "cost": 45, "hours": 12, "prereq": "mil1", "effects": {"military": 0.12}, "desc": "قدرت ارتش +۱۲٪"},
    "mil3": {"branch": "نظامی", "fa": "واحدهای زرهی",           "cost": 80, "hours": 24, "prereq": "mil2", "effects": {"military": 0.15}, "desc": "قدرت ارتش +۱۵٪"},
    "mil4": {"branch": "نظامی", "fa": "سامانه‌های موشکی",        "cost": 130, "hours": 36, "prereq": "mil3", "effects": {"military": 0.18}, "desc": "قدرت ارتش +۱۸٪"},
    "mil5": {"branch": "نظامی", "fa": "دفاع مداری",              "cost": 200, "hours": 48, "prereq": "mil4", "effects": {"military": 0.20, "defense": 0.20}, "res_cost": {"vexium": 15, "deepoil": 15, "zyphgas": 15}, "desc": "حمله و دفاع مداری"},
    # logistics
    "log1": {"branch": "زیرساخت و لجستیک", "fa": "تیم‌های اکتشاف پیشرفته", "cost": 25, "hours": 8,  "prereq": None,   "effects": {"explore_cap": 6},  "desc": "ظرفیت شارژ اکتشاف: ۶"},
    "log2": {"branch": "زیرساخت و لجستیک", "fa": "راه‌سازی قاره‌ای",        "cost": 50, "hours": 16, "prereq": "log1", "effects": {"explore": 0.10}, "desc": "مقدار هر اکتشاف +۱۰٪"},
    "log3": {"branch": "زیرساخت و لجستیک", "fa": "شبکه لجستیک قاره‌ای",    "cost": 90, "hours": 30, "prereq": "log2", "effects": {"explore_cap": 12}, "desc": "ظرفیت شارژ اکتشاف: ۱۲"},
    "log4": {"branch": "زیرساخت و لجستیک", "fa": "ناوگان حمل‌ونقل سنگین",   "cost": 140, "hours": 40, "prereq": "log3", "effects": {"explore": 0.15, "trade": 0.10}, "res_cost": {"vexium": 10, "deepoil": 10, "zyphgas": 10}, "desc": "اکتشاف و تجارت سریع‌تر"},
    # science
    "sci1": {"branch": "علم و فضا", "fa": "آموزش عالی همگانی",  "cost": 25, "hours": 8,  "prereq": None,   "effects": {"research_speed": 0.15}, "desc": "سرعت تحقیق +۱۵٪"},
    "sci2": {"branch": "علم و فضا", "fa": "رایانش پیشرفته",     "cost": 55, "hours": 16, "prereq": "sci1", "effects": {"research_speed": 0.15, "economy": 0.05}, "desc": "تحقیق +۱۵٪"},
    "sci3": {"branch": "علم و فضا", "fa": "انرژی همجوشی",       "cost": 100, "hours": 30, "prereq": "sci2", "effects": {"energy_prod": 0.40}, "desc": "تولید انرژی +۴۰٪"},
    "sci4": {"branch": "علم و فضا", "fa": "زیست‌فناوری",        "cost": 150, "hours": 40, "prereq": "sci3", "effects": {"food_prod": 0.25, "pop_growth": 0.15}, "res_cost": {"vexium": 10, "deepoil": 10, "zyphgas": 10}, "desc": "غذا و رشد جمعیت"},
    "sci5": {"branch": "علم و فضا", "fa": "هوش مصنوعی سیاره‌ای", "cost": 220, "hours": 60, "prereq": "sci4", "effects": {"research_speed": 0.25, "economy": 0.15, "military": 0.10}, "res_cost": {"vexium": 15, "deepoil": 15, "zyphgas": 15}, "desc": "جهش همه‌جانبه"},
    # society
    "soc1": {"branch": "جامعه و حکومت", "fa": "رفاه اجتماعی",   "cost": 20, "hours": 6,  "prereq": None,   "effects": {"happiness": 5}, "desc": "رضایت پایه +۵"},
    "soc2": {"branch": "جامعه و حکومت", "fa": "بهداشت عمومی",   "cost": 45, "hours": 14, "prereq": "soc1", "effects": {"pop_growth": 0.15, "happiness": 3}, "desc": "رشد جمعیت و رضایت"},
    "soc3": {"branch": "جامعه و حکومت", "fa": "اتحاد ملی",      "cost": 80, "hours": 24, "prereq": "soc2", "effects": {"stability": 0.25}, "desc": "مقاومت در برابر اعتراض +۲۵٪"},
    "soc4": {"branch": "جامعه و حکومت", "fa": "فرهنگ فضایی",    "cost": 130, "hours": 36, "prereq": "soc3", "effects": {"happiness": 6, "research_speed": 0.10}, "res_cost": {"vexium": 10, "deepoil": 10, "zyphgas": 10}, "desc": "رضایت و تحقیق"},
    # planet specials
    "sp_vexus_1": {"branch": "ویژه سیاره", "fa": "تصفیه آب بیابانی",   "cost": 40, "hours": 14, "prereq": None, "planet": "vexus",    "effects": {"water_prod": 0.35}, "desc": "تولید آب در وکسوس +۳۵٪"},
    "sp_vexus_2": {"branch": "ویژه سیاره", "fa": "استخراج وکسیوم ژرف", "cost": 90, "hours": 28, "prereq": "sp_vexus_1", "planet": "vexus", "effects": {"mine_prod": 0.25}, "desc": "برداشت معدن +۲۵٪"},
    "sp_thalassa_1": {"branch": "ویژه سیاره", "fa": "مزارع دریایی",    "cost": 40, "hours": 14, "prereq": None, "planet": "thalassa", "effects": {"food_prod": 0.30}, "desc": "غذای دریایی +۳۰٪"},
    "sp_thalassa_2": {"branch": "ویژه سیاره", "fa": "استخراج نفت ژرف", "cost": 90, "hours": 28, "prereq": "sp_thalassa_1", "planet": "thalassa", "effects": {"energy_prod": 0.30, "economy": 0.10}, "desc": "انرژی و درآمد نفتی"},
    "sp_zyphera_1": {"branch": "ویژه سیاره", "fa": "جنگل‌داری پایدار", "cost": 40, "hours": 14, "prereq": None, "planet": "zyphera", "effects": {"materials_prod": 0.30}, "desc": "مصالح +۳۰٪"},
    "sp_zyphera_2": {"branch": "ویژه سیاره", "fa": "سکوی گاز زیفرا",   "cost": 90, "hours": 28, "prereq": "sp_zyphera_1", "planet": "zyphera", "effects": {"energy_prod": 0.25, "trade": 0.10}, "desc": "انرژی گازی و تجارت"},
}

DIRECTIONS = {
    "north": "⬆️ شمال",
    "east": "➡️ شرق",
    "south": "⬇️ جنوب",
    "west": "⬅️ غرب",
}

RANDOM_EVENTS = [
    {"fa": "🌾 برداشت استثنایی", "effects": {"food": 800}, "text": "فصل برداشت عالی بود؛ انبار غذا پر شد."},
    {"fa": "⛏️ کشف رگه جدید", "effects": {"iron": 120}, "text": "کارگران معدن رگه تازه‌ای از آهن پیدا کردند."},
    {"fa": "🌪️ طوفان محلی", "effects": {"materials": -80, "energy": -100}, "text": "طوفان به زیرساخت‌ها آسیب زد."},
    {"fa": "🎉 جشن ملی", "effects": {"happiness": 4}, "text": "جشن ملی روحیه مردم را بالا برد."},
    {"fa": "🦠 بیماری فصلی", "effects": {"happiness": -4}, "text": "بیماری فصلی بخشی از مردم را خانه‌نشین کرد."},
    {"fa": "💰 رونق بازار", "effects": {"money": 600}, "text": "بازار داخلی رونق گرفت و مالیات بیشتری جمع شد."},
    {"fa": "🔥 آتش‌سوزی انبار", "effects": {"food": -300}, "text": "بخشی از انبار غذا در آتش سوخت."},
    {"fa": "🧑‍🔬 جهش علمی", "effects": {"rp": 15}, "text": "پژوهشگران به نتیجه زودهنگامی رسیدند."},
]
