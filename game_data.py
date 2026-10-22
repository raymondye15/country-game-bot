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
    "special": "💎 منبع خاص سیاره",
}

PLANETS = {
    "vexus": {
        "name": "Vexus",
        "fa": "وکسوس",
        "capacity": 400,
        "special_name": "Vexium",
        "special_fa": "وکسیوم",
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
    "farm":      {"fa": "🌾 مزرعه",        "cost": {"materials": 40, "money": 200},  "upkeep": 10,  "desc": "تولید غذا"},
    "waterplant":{"fa": "🚰 تصفیه‌خانه آب", "cost": {"materials": 50, "money": 250},  "upkeep": 12,  "desc": "تولید آب"},
    "powerplant":{"fa": "🔋 نیروگاه",       "cost": {"materials": 60, "iron": 20, "money": 300}, "upkeep": 15, "desc": "تولید انرژی"},
    "mine":      {"fa": "⛏️ معدن پیشرفته",  "cost": {"materials": 50, "money": 300},  "upkeep": 15,  "desc": "افزایش برداشت همه معادن"},
    "factory":   {"fa": "🏭 کارخانه",       "cost": {"materials": 80, "iron": 30, "money": 400}, "upkeep": 20, "desc": "تولید مصالح و درآمد"},
    "university":{"fa": "🎓 دانشگاه",       "cost": {"materials": 70, "money": 500},  "upkeep": 25,  "desc": "امتیاز تحقیق روزانه"},
    "hospital":  {"fa": "🏥 بیمارستان",     "cost": {"materials": 60, "money": 400},  "upkeep": 20,  "desc": "رضایت و رشد جمعیت"},
    "barracks":  {"fa": "🪖 پادگان",        "cost": {"materials": 70, "iron": 20, "money": 350}, "upkeep": 18, "desc": "ظرفیت و قدرت ارتش"},
    "airport_inter": {"fa": "🛸 فرودگاه بین‌سیاره‌ای", "cost": {"materials": 200, "iron": 200, "titanium": 80, "money": 6000}, "upkeep": 150, "desc": "مهاجرت از سیاره‌های دیگر"},
}

# Research tree: id -> data. branch, cost_rp, hours, prereq, effects (flat mods merged into country mods)
RESEARCH = {
    # economy
    "eco1": {"branch": "اقتصاد و صنعت", "fa": "کشاورزی مکانیزه", "cost": 20, "hours": 6,  "prereq": None,   "effects": {"food_prod": 0.20}, "desc": "تولید غذا +۲۰٪"},
    "eco2": {"branch": "اقتصاد و صنعت", "fa": "صنعت سنگین",      "cost": 45, "hours": 12, "prereq": "eco1", "effects": {"materials_prod": 0.20, "mine_prod": 0.10}, "desc": "مصالح +۲۰٪، معدن +۱۰٪"},
    "eco3": {"branch": "اقتصاد و صنعت", "fa": "بازار آزاد",      "cost": 70, "hours": 24, "prereq": "eco2", "effects": {"trade": 0.20, "economy": 0.10}, "desc": "تجارت +۲۰٪"},
    "eco4": {"branch": "اقتصاد و صنعت", "fa": "بانک مرکزی",      "cost": 110, "hours": 36, "prereq": "eco3", "effects": {"economy": 0.20}, "desc": "درآمد مالیاتی +۲۰٪"},
    "eco5": {"branch": "اقتصاد و صنعت", "fa": "اقتصاد مداری",    "cost": 180, "hours": 48, "prereq": "eco4", "effects": {"economy": 0.20, "trade": 0.15}, "desc": "اقتصاد و تجارت مداری"},
    # military
    "mil1": {"branch": "نظامی", "fa": "سربازگیری سازمان‌یافته", "cost": 20, "hours": 6,  "prereq": None,   "effects": {"military": 0.10}, "desc": "قدرت ارتش +۱۰٪"},
    "mil2": {"branch": "نظامی", "fa": "تسلیحات سبک",            "cost": 45, "hours": 12, "prereq": "mil1", "effects": {"military": 0.12}, "desc": "قدرت ارتش +۱۲٪"},
    "mil3": {"branch": "نظامی", "fa": "واحدهای زرهی",           "cost": 80, "hours": 24, "prereq": "mil2", "effects": {"military": 0.15}, "desc": "قدرت ارتش +۱۵٪"},
    "mil4": {"branch": "نظامی", "fa": "سامانه‌های موشکی",        "cost": 130, "hours": 36, "prereq": "mil3", "effects": {"military": 0.18}, "desc": "قدرت ارتش +۱۸٪"},
    "mil5": {"branch": "نظامی", "fa": "دفاع مداری",              "cost": 200, "hours": 48, "prereq": "mil4", "effects": {"military": 0.20, "defense": 0.20}, "desc": "حمله و دفاع مداری"},
    # logistics
    "log1": {"branch": "زیرساخت و لجستیک", "fa": "تیم‌های اکتشاف پیشرفته", "cost": 25, "hours": 8,  "prereq": None,   "effects": {"explore_cap": 6},  "desc": "ظرفیت شارژ اکتشاف: ۶"},
    "log2": {"branch": "زیرساخت و لجستیک", "fa": "راه‌سازی قاره‌ای",        "cost": 50, "hours": 16, "prereq": "log1", "effects": {"explore": 0.10}, "desc": "مقدار هر اکتشاف +۱۰٪"},
    "log3": {"branch": "زیرساخت و لجستیک", "fa": "شبکه لجستیک قاره‌ای",    "cost": 90, "hours": 30, "prereq": "log2", "effects": {"explore_cap": 12}, "desc": "ظرفیت شارژ اکتشاف: ۱۲"},
    "log4": {"branch": "زیرساخت و لجستیک", "fa": "ناوگان حمل‌ونقل سنگین",   "cost": 140, "hours": 40, "prereq": "log3", "effects": {"explore": 0.15, "trade": 0.10}, "desc": "اکتشاف و تجارت سریع‌تر"},
    # science
    "sci1": {"branch": "علم و فضا", "fa": "آموزش عالی همگانی",  "cost": 25, "hours": 8,  "prereq": None,   "effects": {"research_speed": 0.15}, "desc": "سرعت تحقیق +۱۵٪"},
    "sci2": {"branch": "علم و فضا", "fa": "رایانش پیشرفته",     "cost": 55, "hours": 16, "prereq": "sci1", "effects": {"research_speed": 0.15, "economy": 0.05}, "desc": "تحقیق +۱۵٪"},
    "sci3": {"branch": "علم و فضا", "fa": "انرژی همجوشی",       "cost": 100, "hours": 30, "prereq": "sci2", "effects": {"energy_prod": 0.40}, "desc": "تولید انرژی +۴۰٪"},
    "sci4": {"branch": "علم و فضا", "fa": "زیست‌فناوری",        "cost": 150, "hours": 40, "prereq": "sci3", "effects": {"food_prod": 0.25, "pop_growth": 0.15}, "desc": "غذا و رشد جمعیت"},
    "sci5": {"branch": "علم و فضا", "fa": "هوش مصنوعی سیاره‌ای", "cost": 220, "hours": 60, "prereq": "sci4", "effects": {"research_speed": 0.25, "economy": 0.15, "military": 0.10}, "desc": "جهش همه‌جانبه"},
    # society
    "soc1": {"branch": "جامعه و حکومت", "fa": "رفاه اجتماعی",   "cost": 20, "hours": 6,  "prereq": None,   "effects": {"happiness": 5}, "desc": "رضایت پایه +۵"},
    "soc2": {"branch": "جامعه و حکومت", "fa": "بهداشت عمومی",   "cost": 45, "hours": 14, "prereq": "soc1", "effects": {"pop_growth": 0.15, "happiness": 3}, "desc": "رشد جمعیت و رضایت"},
    "soc3": {"branch": "جامعه و حکومت", "fa": "اتحاد ملی",      "cost": 80, "hours": 24, "prereq": "soc2", "effects": {"stability": 0.25}, "desc": "مقاومت در برابر اعتراض +۲۵٪"},
    "soc4": {"branch": "جامعه و حکومت", "fa": "فرهنگ فضایی",    "cost": 130, "hours": 36, "prereq": "soc3", "effects": {"happiness": 6, "research_speed": 0.10}, "desc": "رضایت و تحقیق"},
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
