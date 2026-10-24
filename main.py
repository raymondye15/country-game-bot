# -*- coding: utf-8 -*-
"""
Persian Telegram country-management game bot — TEXT ONLY (no maps/images).
Stack: aiogram 3 + MongoDB Atlas (free) + Render web service (webhook)
       + cron-job.com pinging /tick every 1 minute (game clock + keep-alive).
Env: BOT_TOKEN, MONGODB_URI, MONGODB_DB, WEBHOOK_BASE_URL (or RENDER_EXTERNAL_URL),
     TICK_SECRET, ADMIN_ID (optional), PORT
"""
import os, re, asyncio, logging, hashlib
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.mongo import MongoStorage
from motor.motor_asyncio import AsyncIOMotorClient
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, BotCommand, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder

import db as dbm
import logic
from game_data import PLANETS, GOVERNMENTS, BUILDINGS, RESEARCH, RESOURCES, DIRECTIONS

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("gamebot")

BOT_TOKEN = os.environ["BOT_TOKEN"]
TICK_SECRET = os.environ.get("TICK_SECRET", "change-me")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0") or 0)

bot = Bot(BOT_TOKEN)
# FSM state lives in MongoDB (was in-memory: a restart/redeploy used to wipe a
# half-finished country registration). Same cluster/DB as the game data.
_fsm_client = AsyncIOMotorClient(os.environ.get("MONGODB_URI", "mongodb://localhost:27017"))
dp = Dispatcher(storage=MongoStorage(client=_fsm_client,
                                     db_name=os.environ.get("MONGODB_DB", "country_game"),
                                     collection_name="fsm_states"))

EN_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9 '\-]{1,59}$")

# ---------------------------------------------------------------- helpers
async def gate(msg: types.Message) -> bool:
    """Group gate removed by the owner's request (2026-10-22): the game works in
    any group immediately, with no minimum-member condition."""
    return True

@dp.callback_query(F.data == "close")
async def close_message(cb: types.CallbackQuery):
    """Universal close button: removes the bot's menu message."""
    try:
        await cb.message.delete()
    except Exception:
        try:
            await cb.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
    await cb.answer()

def main_kb(selective: bool = False) -> ReplyKeyboardMarkup:
    # NOTE: in groups a reply keyboard is shown to ALL members by Telegram design;
    # callers must use selective=True (with a reply) or skip the keyboard in groups.
    return ReplyKeyboardMarkup(resize_keyboard=True, selective=selective, keyboard=[
        [KeyboardButton(text="🏳️ کشور من"), KeyboardButton(text="🔭 اکتشاف")],
        [KeyboardButton(text="🏗️ ساختمان‌ها"), KeyboardButton(text="🔬 تحقیق")],
        [KeyboardButton(text="🛒 تجارت"), KeyboardButton(text="🤝 دیپلماسی")],
        [KeyboardButton(text="🪖 ارتش و جنگ"), KeyboardButton(text="🏆 رتبه‌بندی")],
        [KeyboardButton(text="💰 درآمد و مالی"), KeyboardButton(text="🧳 مهاجرت")],
        [KeyboardButton(text="❓ راهنما"), KeyboardButton(text="✖️ بستن منو")],
    ])

async def my_country(msg_or_cb) -> dict | None:
    uid = msg_or_cb.from_user.id
    c = await dbm.get_country(uid)
    if not c or not c.get("alive", True):
        text = "هنوز کشوری نداری (یا کشورت فروپاشیده است). با /start در پیوی ربات کشورت را بساز."
        if isinstance(msg_or_cb, types.CallbackQuery):
            await msg_or_cb.answer(text, show_alert=True)
        else:
            await msg_or_cb.answer(text)
        return None
    # BUGFIX: activity must be persisted (the minute-tick freezes countries whose
    # last_seen is 14 days old) and an active player must be un-frozen. Throttled
    # to one small atomic write per hour so viewing menus stays cheap.
    t = logic.now_ts()
    if t - c.get("last_seen_ts", 0) > 3600 or c.get("frozen"):
        c["last_seen_ts"] = t
        c["frozen"] = False
        await dbm.db.countries.update_one({"user_id": uid}, {"$set": {"last_seen_ts": t, "frozen": False}})
    return c

GUIDE_TEXT = (
    "❓ راهنمای بازی کشورداری\n\n"
    "• هر بازیکن یک کشور واقعی دارد؛ همه کشورها توسط انسان‌های واقعی اداره می‌شوند.\n"
    "• 🔭 اکتشاف: هر ساعت ۱ شارژ ذخیره می‌شود (شروع: تا ۳ شارژ). با هر اکتشاف حدود «مساحت اولیه ÷ ۲۴» زمین می‌گیری؛ در جهت دریا یا کشور دیگر متوقف می‌شود.\n"
    "• ⛏️ معادن بر اساس قاره‌ات تعیین شده‌اند: مصرف داخلی، فروش در بازار جهانی یا ساخت تجهیزات جنگی.\n"
    "• 🏗️ ساختمان‌ها تولید و رضایت را بالا می‌برند. مالیات از منوی کشور قابل تنظیم است.\n"
    "• 😊 اگر رضایت زیر ۳۰٪ بیاید اعتراض شروع می‌شود؛ اگر زیر ۱۵٪ بماند کشور فرو می‌پاشد و باید از اول بسازی. (کشتن مردم ممکن نیست!)\n"
    "• ⚔️ جنگ ۳ روز واقعی طول می‌کشد و همزمان فقط یک جنگ می‌توانی داشته باشی. جنگ فقط با کشورهای هم‌سیاره ممکن است و بعد از هر جنگ، هر دو طرف ۳ روز آتش‌بس دارند. پیروزی کامل = تصرف کل کشور حریف؛ پیروزی جزئی = ۲۵٪ خاک و معادنش.\n"
    "• 🤝 همسایه شدن (۱ تا ۴ کشور) تجارت و لجستیک را ارزان و سریع می‌کند.\n"
    "• 🛒 بازار جهانی برای همه بازیکن‌هاست، حتی خارج از گروه تو. پیشنهادهای فروش بعد از ۷ روز منقضی می‌شوند و منابع فروش‌نرفته به انبارت برمی‌گردند. در گروه، برای ترید مستقیم با یک بازیکن روی پیامش ریپلای بزن و بنویس «ترید»."
    "• 💰 از بخش «درآمد و مالی» ببین پولت دقیقاً از کجا می‌آید و کجا می‌رود.\n"
    "• 🧳 مهاجرت: کشورهای شاد از آدم‌های بی‌کشور و مردم کشورهای ناراضی مهاجر می‌گیرند؛ با فرودگاه بین‌سیاره‌ای (ساختمان) از سیاره‌های دیگر هم می‌توانی مهاجر بگیری.\n"
    "• 👶 زاد و ولد و مرگ‌ومیر: هر ساعت در کشورت تولد و مرگ رخ می‌دهد؛ رضایت بالا و بیمارستان تولد را بیشتر و مرگ‌ومیر را کمتر می‌کند و گرسنگی مرگ‌ومیر را شدید بالا می‌برد. همه سیستم‌های زنده بازی (اقتصاد، جمعیت، رضایت، امتیاز تحقیق، مهاجرت) ساعتی کار می‌کنند؛ گزارش کامل هر روز می‌آید.\n"
    "• 🏆 رتبه‌بندی را می‌توانی بر اساس قدرت ملی، امتیاز اقتصادی، امتیاز علمی، جمعیت یا مساحت مرتب کنی. امتیاز اقتصادی از تولید روزانه، ساختمان‌ها و معادن می‌آید (پولِ انباشته به‌تنهایی رتبه نمی‌آورد) و امتیاز علمی از تحقیقات کامل‌شده و سرعت تولید امتیاز تحقیق.\n"
    "• 🎛️ لازم نیست دکمه‌های پایین صفحه را بزنی: اسم هر بخش را فقط بنویس (مثل «لیدربورد»، «تجارت»، «کشور من» یا «منو») تا همان بخش به صورت منوی شیشه‌ای باز شود. منوها در گروه هم فقط برای خودت کار می‌کنند.\n"
)

# ---------------------------------------------------------------- registration wizard
class Reg(StatesGroup):
    planet = State(); continent = State(); government = State()
    cname = State(); capital = State(); city1 = State(); city2 = State(); city3 = State()

@dp.message(CommandStart())
async def cmd_start(msg: types.Message, state: FSMContext):
    if msg.chat.type != "private":
        if not await gate(msg):
            return
        c = await dbm.get_country(msg.from_user.id)
        if c and c.get("alive"):
            await msg.answer(f"🏳️ کشور تو: «{c['name']}» — برای مدیریت کامل به پیوی ربات بیا.")
        else:
            await msg.answer("برای ساخت کشور به پیوی ربات پیام بده و /start را بزن. بازی گروهی از همین‌جا هم قابل انجام است، اگر کشور داشته باشی.")
        return
    c = await dbm.get_country(msg.from_user.id)
    if c and c.get("alive"):
        sent = await msg.answer(f"خوش برگشتی، حاکم «{c['name']}»! 👋", reply_markup=glass_kb())
        await track_menu(sent, msg.from_user.id)
        return
    if c and not c.get("alive"):
        await dbm.delete_country(msg.from_user.id)
    kb = InlineKeyboardBuilder()
    for pid, p in PLANETS.items():
        cnt = await dbm.planet_country_count(pid)
        kb.button(text=f"🪐 {p['name']} ({p['fa']}) — {cnt}/{p['capacity']} کشور", callback_data=f"reg:planet:{pid}")
    kb.adjust(1)
    await state.set_state(Reg.planet)
    await msg.answer("به بازی کشورداری خوش آمدی! 🌍\nاول سیاره‌ات را انتخاب کن:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("reg:planet:"), Reg.planet)
async def reg_planet(cb: types.CallbackQuery, state: FSMContext):
    if cb.message.chat.type != "private":
        await cb.answer("ساخت کشور فقط در پیوی ربات ممکن است؛ به پیوی ربات بیا.", show_alert=True); return
    pid = cb.data.split(":")[2]
    p = PLANETS[pid]
    if await dbm.planet_country_count(pid) >= p["capacity"]:
        await cb.answer("این سیاره پر شده است؛ سیاره دیگری انتخاب کن.", show_alert=True); return
    await state.update_data(planet=pid)
    kb = InlineKeyboardBuilder()
    for cid, cont in p["continents"].items():
        kb.button(text=f"{cont['name']} ({cont['fa']})", callback_data=f"reg:cont:{cid}")
    kb.adjust(1)
    await state.set_state(Reg.continent)
    await cb.message.edit_text(f"🪐 {p['name']} — {p['desc']}\n\nحالا قاره را انتخاب کن:", reply_markup=kb.as_markup())
    await cb.answer()

@dp.callback_query(F.data.startswith("reg:cont:"), Reg.continent)
async def reg_cont(cb: types.CallbackQuery, state: FSMContext):
    if cb.message.chat.type != "private":
        await cb.answer("ساخت کشور فقط در پیوی ربات ممکن است؛ به پیوی ربات بیا.", show_alert=True); return
    cid = cb.data.split(":")[2]
    data = await state.get_data()
    cont = PLANETS[data["planet"]]["continents"][cid]
    await state.update_data(continent=cid)
    kb = InlineKeyboardBuilder()
    for gid, g in GOVERNMENTS.items():
        kb.button(text=f"{g['emoji']} {g['fa']}", callback_data=f"reg:gov:{gid}")
    kb.button(text="📖 راهنمای حکومت‌ها", callback_data="reg:govguide")
    kb.adjust(2, 2, 2, 2, 1)
    await state.set_state(Reg.government)
    await cb.message.edit_text(f"قاره {cont['name']}: {cont['desc']}\n\nحالا نوع حکومت را انتخاب کن (با دکمه راهنما می‌توانی اثر هر کدام را ببینی):", reply_markup=kb.as_markup())
    await cb.answer()

@dp.callback_query(F.data == "reg:govguide", Reg.government)
async def reg_govguide(cb: types.CallbackQuery):
    txt = "📖 راهنمای انواع حکومت:\n\n" + "\n\n".join(f"{g['emoji']} {g['fa']}: {g['guide']}" for g in GOVERNMENTS.values())
    await cb.message.answer(txt)
    await cb.answer()

@dp.callback_query(F.data.startswith("reg:gov:"), Reg.government)
async def reg_gov(cb: types.CallbackQuery, state: FSMContext):
    if cb.message.chat.type != "private":
        await cb.answer("ساخت کشور فقط در پیوی ربات ممکن است؛ به پیوی ربات بیا.", show_alert=True); return
    gid = cb.data.split(":")[2]
    await state.update_data(government=gid)
    await state.set_state(Reg.cname)
    await cb.message.edit_text(f"حکومت: {GOVERNMENTS[gid]['fa']}\n\nحالا اسم کشورت را بنویس — حتماً باید انگلیسی باشد (۲ تا ۶۰ حرف):")
    await cb.answer()

@dp.message(Reg.cname)
async def reg_cname(msg: types.Message, state: FSMContext):
    if msg.chat.type != "private":
        await msg.answer("ساخت کشور فقط در پیوی ربات ممکن است؛ به پیوی ربات بیا و /start بزن."); return
    name = msg.text.strip()
    if not EN_NAME.match(name):
        await msg.answer("❌ اسم کشور باید انگلیسی باشد (فقط حروف انگلیسی، عدد، فاصله). دوباره بفرست:"); return
    if await dbm.get_country_by_name(name):
        await msg.answer("❌ این اسم قبلاً گرفته شده؛ اسم دیگری انتخاب کن:"); return
    await state.update_data(cname=name)
    await state.set_state(Reg.capital)
    await msg.answer("اسم پایتخت را بنویس — آن هم حتماً انگلیسی:")

@dp.message(Reg.capital)
async def reg_capital(msg: types.Message, state: FSMContext):
    if msg.chat.type != "private":
        await msg.answer("ساخت کشور فقط در پیوی ربات ممکن است؛ به پیوی ربات بیا و /start بزن."); return
    cap = msg.text.strip()
    if not EN_NAME.match(cap):
        await msg.answer("❌ اسم پایتخت باید انگلیسی باشد. دوباره بفرست:"); return
    await state.update_data(capital=cap)
    await state.set_state(Reg.city1)
    await msg.answer("اسم اولین شهر بزرگت را خودت انتخاب کن و بفرست — این قدم اختیاریه: اگه نمی‌خوای اسم بذاری، دکمه «رد کردن» رو بزن تا اسم پیش‌فرض بگیره (نوشتن «رد کردن» هم کار می‌کنه):", reply_markup=_city_skip_kb(True))

CITY_SKIP_WORDS = {"رد کردن", "رد", "skip", "Skip", "-"}

def _city_skip_kb(first: bool = False):
    kb = InlineKeyboardBuilder()
    kb.button(text="⏭️ رد کردن این شهر", callback_data="reg:skipcity")
    if first:
        kb.button(text="⏭️ رد کردن هر سه شهر", callback_data="reg:skipall")
    kb.adjust(1)
    return kb.as_markup()

async def _finish_reg(answer, state, user, cities):
    data = await state.get_data()
    c = logic.new_country(user.id, data["planet"], data["continent"], data["government"],
                          data["cname"], data["capital"], cities, user.username or "")
    try:
        await dbm.save_country(c)
    except Exception:
        # two players finishing registration with the same country name at the
        # same moment hit the unique index; the loser gets a friendly error
        await state.clear()
        await answer("❌ متأسفانه همین لحظه بازیکن دیگری همین اسم کشور را ثبت کرد. با /start دوباره شروع کن و اسم دیگری انتخاب کن.")
        return
    await state.clear()
    others = await dbm.continent_countries(c["planet"], c["continent"], c["user_id"])
    hint = ("\n\nکشورهای هم‌قاره‌ای تو: " + "، ".join(o["name"] for o in others[:5]) +
            "\nاز بخش 🤝 دیپلماسی می‌توانی برایشان درخواست همسایگی بفرستی (۱ تا ۴ همسایه).") if others else \
           "\n\nفعلاً در قاره تو کشور دیگری نیست؛ پس نمی‌توانی همسایه انتخاب کنی — بقیه باید همسایه تو شوند!"
    sent = await answer("🎉 کشورت ساخته شد!\n\n" + logic.country_text(c) + hint, reply_markup=glass_kb())
    await track_menu(sent, user.id)

async def _city_advance(answer, state, user, value):
    cur = await state.get_state()
    if cur == Reg.city1.state:
        await state.update_data(city1=value); await state.set_state(Reg.city2)
        await answer("اسم دومین شهر بزرگت (اختیاری):", reply_markup=_city_skip_kb())
    elif cur == Reg.city2.state:
        await state.update_data(city2=value); await state.set_state(Reg.city3)
        await answer("اسم سومین شهر بزرگت (اختیاری):", reply_markup=_city_skip_kb())
    else:
        data = await state.get_data()
        await _finish_reg(answer, state, user, [data["city1"], data["city2"], value])

def _default_city(data: dict) -> str:
    return logic.random_city_name([data.get("capital", ""), data.get("city1", ""), data.get("city2", "")])

@dp.message(Reg.city1)
@dp.message(Reg.city2)
@dp.message(Reg.city3)
async def reg_city(msg: types.Message, state: FSMContext):
    if msg.chat.type != "private":
        await msg.answer("ساخت کشور فقط در پیوی ربات ممکن است؛ به پیوی ربات بیا و /start بزن."); return
    text = msg.text.strip()
    if text in CITY_SKIP_WORDS:
        value = _default_city(await state.get_data())
    elif not (2 <= len(text) <= 60):
        await msg.answer("اسم شهر باید ۲ تا ۶۰ حرف باشد (یا بنویس «رد کردن» تا رد بشه):"); return
    else:
        value = text
    await _city_advance(msg.answer, state, msg.from_user, value)

@dp.callback_query(F.data.in_({"reg:skipcity", "reg:skipall"}))
async def reg_skip_city(cb: types.CallbackQuery, state: FSMContext):
    if cb.message.chat.type != "private":
        await cb.answer("ساخت کشور فقط در پیوی ربات ممکن است؛ به پیوی ربات بیا.", show_alert=True); return
    cur = await state.get_state()
    if cur not in (Reg.city1.state, Reg.city2.state, Reg.city3.state):
        await cb.answer(); return
    data = await state.get_data()
    if cb.data == "reg:skipall":
        cities = [data[k] for k in ("city1", "city2", "city3") if data.get(k)]
        while len(cities) < 3:
            cities.append(logic.random_city_name([data.get("capital", "")] + cities))
        await _finish_reg(cb.message.answer, state, cb.from_user, cities)
    else:
        await _city_advance(cb.message.answer, state, cb.from_user, _default_city(data))
    await cb.answer("⏭️ رد شد")

# ---------------------------------------------------------------- country / exploration
@dp.message(F.text == "🏳️ کشور من")
@dp.message(Command("country"))
async def cmd_country(msg: types.Message):
    if not await gate(msg): return
    c = await my_country(msg)
    if not c: return
    logic.regen_charges(c); await dbm.save_country(c)
    text, kb = country_view(c)
    sent = await msg.answer(text, reply_markup=kb)
    await track_menu(sent, msg.from_user.id)

def country_view(c: dict, back: bool = False):
    kb = InlineKeyboardBuilder()
    kb.button(text="⚙️ تنظیم مالیات", callback_data="tax:menu")
    kb.button(text="🔭 اکتشاف", callback_data="explore:menu")
    kb.adjust(2)
    if back:
        kb.button(text="🔙 منوی اصلی", callback_data="menu:open")
    kb.button(text="✖️ بستن", callback_data="close")
    return logic.country_text(c), kb.as_markup()

@dp.callback_query(F.data == "tax:menu")
async def tax_menu(cb: types.CallbackQuery):
    c = await my_country(cb)
    if not c: return
    kb = InlineKeyboardBuilder()
    for rate, label in ((1, "کم (رضایت ↑، درآمد ↓)"), (2, "متوسط"), (3, "زیاد (درآمد ↑، رضایت ↓)")):
        mark = "✅ " if c["tax_rate"] == rate else ""
        kb.button(text=mark + label, callback_data=f"tax:set:{rate}")
    kb.adjust(1)
    kb.button(text="✖️ بستن", callback_data="close")
    await cb.message.answer(f"مالیات فعلی: {c['tax_rate']}", reply_markup=kb.as_markup()); await cb.answer()

@dp.callback_query(F.data.startswith("tax:set:"))
async def tax_set(cb: types.CallbackQuery):
    c = await my_country(cb)
    if not c: return
    c["tax_rate"] = int(cb.data.split(":")[2]); await dbm.save_country(c)
    await cb.message.edit_text(f"✅ نرخ مالیات روی {c['tax_rate']} تنظیم شد."); await cb.answer()

@dp.message(F.text == "🔭 اکتشاف")
@dp.message(Command("explore"))
async def cmd_explore(msg: types.Message):
    if not await gate(msg): return
    c = await my_country(msg)
    if not c: return
    logic.regen_charges(c); await dbm.save_country(c)
    await send_explore_menu(msg, c)

def explore_view(c: dict, back: bool = False):
    kb = InlineKeyboardBuilder()
    for d, label in DIRECTIONS.items():
        b = c["borders"][d]
        st = {"open": "باز", "sea": "🌊 دریا", "country": "🚧 مرز کشور"}[b["status"]]
        kb.button(text=f"{label} — {st}", callback_data=f"explore:go:{d}")
    kb.adjust(2)
    nxt = ""
    cap = logic.explore_cap(c)
    if c["explore_charges"] < cap:
        left = max(0, logic.HOUR - (logic.now_ts() - c["last_charge_ts"]))
        nxt = f"\nشارژ بعدی: {left // 60} دقیقه دیگر"
    if back:
        kb.button(text="🔙 منوی اصلی", callback_data="menu:open")
    kb.button(text="✖️ بستن", callback_data="close")
    return (f"🔭 شارژ اکتشاف: {c['explore_charges']}/{cap}{nxt}\nهزینه هر اکتشاف: ⚡۱۵ 💧غذا ۲۰ 💰۲۵\nجهت اکتشاف را انتخاب کن:",
            kb.as_markup())

async def send_explore_menu(msg: types.Message, c: dict):
    text, kb = explore_view(c)
    await msg.answer(text, reply_markup=kb)

@dp.callback_query(F.data == "explore:menu")
async def explore_menu_cb(cb: types.CallbackQuery):
    c = await my_country(cb)
    if not c: return
    logic.regen_charges(c); await dbm.save_country(c)
    await send_explore_menu(cb.message, c); await cb.answer()

@dp.callback_query(F.data.startswith("explore:go:"))
async def explore_go(cb: types.CallbackQuery):
    c = await my_country(cb)
    if not c: return
    logic.regen_charges(c)
    direction = cb.data.split(":")[2]
    others_raw = await dbm.continent_countries(c["planet"], c["continent"], c["user_id"])
    others = [o for o in others_raw if o["user_id"] not in c["neighbors"]]
    res = logic.do_exploration(c, direction, others)
    await dbm.save_country(c)
    await cb.message.answer(("✅ " if res["ok"] else "❌ ") + res["msg"] + f"\n🗺️ مساحت فعلی: {c['area']:,} کیلومتر مربع | شارژ باقی‌مانده: {c['explore_charges']}")
    await cb.answer()

# ---------------------------------------------------------------- buildings
@dp.message(F.text == "🏗️ ساختمان‌ها")
@dp.message(Command("build"))
async def cmd_build(msg: types.Message):
    if not await gate(msg): return
    c = await my_country(msg)
    if not c: return
    text, kb = build_view(c)
    sent = await msg.answer(text, reply_markup=kb)
    await track_menu(sent, msg.from_user.id)

def build_view(c: dict, back: bool = False):
    kb = InlineKeyboardBuilder()
    lines = ["🏗️ ساختمان‌های تو:\n"]
    for bid, b in BUILDINGS.items():
        cost = "، ".join(f"{k}:{v}" for k, v in b["cost"].items())
        lines.append(f"{b['fa']} — سطح {c['buildings'].get(bid, 0)} ({b['desc']})\nهزینه ساخت: {cost}")
        kb.button(text=f"ساخت {b['fa']}", callback_data=f"build:{bid}")
    kb.adjust(1)
    if back:
        kb.button(text="🔙 منوی اصلی", callback_data="menu:open")
    kb.button(text="✖️ بستن", callback_data="close")
    return "\n".join(lines), kb.as_markup()

@dp.callback_query(F.data.startswith("build:"))
async def build_cb(cb: types.CallbackQuery):
    c = await my_country(cb)
    if not c: return
    bid = cb.data.split(":")[1]
    cost = BUILDINGS[bid]["cost"]
    for k, v in cost.items():
        have = c["money"] if k == "money" else c["res"].get(k, 0)
        if have < v:
            await cb.answer(f"منابع کافی نداری ({k}: {have}/{v})", show_alert=True); return
    for k, v in cost.items():
        if k == "money": c["money"] -= v
        else: c["res"][k] = c["res"].get(k, 0) - v
    c["buildings"][bid] = c["buildings"].get(bid, 0) + 1
    await dbm.save_country(c)
    await cb.message.answer(f"✅ {BUILDINGS[bid]['fa']} ساخته شد — سطح {c['buildings'][bid]}")
    await cb.answer()

# ---------------------------------------------------------------- research
def research_money_cost(r: dict) -> int:
    """Money sink: large research nodes (50+ RP) also cost treasury money."""
    return r["cost"] * 8 if r["cost"] >= 50 else 0

@dp.message(F.text == "🔬 تحقیق")
@dp.message(Command("research"))
async def cmd_research(msg: types.Message):
    if not await gate(msg): return
    c = await my_country(msg)
    if not c: return
    text, kb = research_view(c)
    sent = await msg.answer(text, reply_markup=kb)
    await track_menu(sent, msg.from_user.id)

def research_view(c: dict, back: bool = False):
    lines = [f"🔬 امتیاز تحقیق: {c['rp']}\n"]
    if c.get("researching"):
        r = RESEARCH[c["researching"]["id"]]
        left = max(0, c["researching"]["finish_ts"] - logic.now_ts())
        lines.append(f"⏳ در حال تحقیق: {r['fa']} — {left // 3600} ساعت و {(left % 3600) // 60} دقیقه مانده\n")
    kb = InlineKeyboardBuilder()
    by_branch = {}
    for rid, r in RESEARCH.items():
        if r.get("planet") and r["planet"] != c["planet"]:
            continue
        by_branch.setdefault(r["branch"], []).append((rid, r))
    for branch, items in by_branch.items():
        lines.append(f"\n🌿 شاخه {branch}:")
        for rid, r in items:
            if rid in c["researched"]:
                lines.append(f"✅ {r['fa']}")
            elif r["prereq"] and r["prereq"] not in c["researched"]:
                lines.append(f"🔒 {r['fa']} (نیازمند: {RESEARCH[r['prereq']]['fa']})")
            else:
                mc = research_money_cost(r)
                mc_txt = f" + {mc:,} 💰" if mc else ""
                lines.append(f"• {r['fa']} — {r['desc']} | هزینه {r['cost']} امتیاز{mc_txt}، {r['hours']} ساعت")
                kb.button(text=f"تحقیق: {r['fa']}", callback_data=f"research:start:{rid}")
    kb.adjust(1)
    if back:
        kb.button(text="🔙 منوی اصلی", callback_data="menu:open")
    kb.button(text="✖️ بستن", callback_data="close")
    return "\n".join(lines), kb.as_markup()

@dp.callback_query(F.data.startswith("research:start:"))
async def research_start(cb: types.CallbackQuery):
    c = await my_country(cb)
    if not c: return
    rid = cb.data.split(":")[2]
    r = RESEARCH[rid]
    if c.get("researching"):
        await cb.answer("یک تحقیق دیگر در جریان است.", show_alert=True); return
    if rid in c["researched"] or (r["prereq"] and r["prereq"] not in c["researched"]):
        await cb.answer("این تحقیق قابل شروع نیست.", show_alert=True); return
    if c["rp"] < r["cost"]:
        await cb.answer(f"امتیاز کافی نداری ({c['rp']}/{r['cost']})", show_alert=True); return
    mc = research_money_cost(r)
    if c["money"] < mc:
        await cb.answer(f"پول کافی برای این تحقیق نداری ({c['money']:,}/{mc:,} 💰)", show_alert=True); return
    c["rp"] -= r["cost"]
    c["money"] -= mc
    hours = r["hours"] / (1 + logic.mod(c, "research_speed"))
    c["researching"] = {"id": rid, "finish_ts": logic.now_ts() + int(hours * 3600)}
    await dbm.save_country(c)
    await cb.message.answer(f"🔬 تحقیق «{r['fa']}» شروع شد؛ حدود {hours:.1f} ساعت طول می‌کشد.")
    await cb.answer()

# ---------------------------------------------------------------- trade (global market)
class Trade(StatesGroup):
    resource = State(); amount = State(); price = State()

@dp.message(F.text == "🛒 تجارت")
@dp.message(Command("trade"))
async def cmd_trade(msg: types.Message):
    if not await gate(msg): return
    c = await my_country(msg)
    if not c: return
    text, kb = trade_view(c)
    sent = await msg.answer(text, reply_markup=kb)
    await track_menu(sent, msg.from_user.id)

def trade_view(c: dict, back: bool = False):
    kb = InlineKeyboardBuilder()
    kb.button(text="📋 بازار جهانی (خرید)", callback_data="trade:list")
    kb.button(text="➕ ثبت پیشنهاد فروش", callback_data="trade:new")
    kb.adjust(1)
    fee_note = "کارمزد بازار: ۵٪ (با همسایه‌ها: بدون کارمزد در معامله مستقیم از پروفایل کشور)"
    if back:
        kb.button(text="🔙 منوی اصلی", callback_data="menu:open")
    kb.button(text="✖️ بستن", callback_data="close")
    return (f"🛒 تجارت جهانی — حتی با بازیکن‌های خارج از گروه تو.\n{fee_note}\n💱 ترید مستقیم در گروه: روی پیام بازیکن ریپلای بزن و بنویس «ترید».",
            kb.as_markup())

@dp.callback_query(F.data == "trade:list")
async def trade_list(cb: types.CallbackQuery):
    c = await my_country(cb)
    if not c: return
    offers = [o async for o in dbm.db.trade_offers.find({"seller_id": {"$ne": c["user_id"]}, "ts": {"$gt": logic.now_ts() - 7 * logic.DAY}}).limit(15)]
    if not offers:
        await cb.message.answer("بازار خالی است؛ اولین پیشنهاد فروش را تو ثبت کن!"); await cb.answer(); return
    kb = InlineKeyboardBuilder()
    lines = ["📋 پیشنهادهای بازار جهانی:\n"]
    for o in offers:
        seller = await dbm.get_country(o["seller_id"])
        sname = seller["name"] if seller else "?"
        lines.append(f"• {RESOURCES[o['resource']]} × {o['amount']:,} — قیمت {o['price']:,} 💰 (فروشنده: {sname})")
        kb.button(text=f"خرید از {sname} ({o['price']:,}💰)", callback_data=f"trade:buy:{o['_id']}")
    kb.adjust(1)
    kb.button(text="✖️ بستن", callback_data="close")
    await cb.message.answer("\n".join(lines), reply_markup=kb.as_markup()); await cb.answer()

@dp.callback_query(F.data.startswith("trade:buy:"))
async def trade_buy(cb: types.CallbackQuery):
    from bson import ObjectId
    c = await my_country(cb)
    if not c: return
    try:
        oid = ObjectId(cb.data.split(":")[2])
    except Exception:
        await cb.answer("پیشنهاد نامعتبر است.", show_alert=True); return
    offer = await dbm.db.trade_offers.find_one({"_id": oid})
    if not offer:
        await cb.answer("این پیشنهاد دیگر نیست.", show_alert=True); return
    seller = await dbm.get_country(offer["seller_id"])
    if not seller or not seller.get("alive"):
        await dbm.db.trade_offers.delete_one({"_id": oid}); await cb.answer("فروشنده دیگر فعال نیست.", show_alert=True); return
    fee = 0 if seller["user_id"] in c["neighbors"] else int(offer["price"] * 0.05)
    total = offer["price"] + fee
    if c["money"] < total:
        await cb.answer(f"پول کافی نداری ({c['money']:,}/{total:,})", show_alert=True); return
    c["money"] -= total
    c["res"][offer["resource"]] = c["res"].get(offer["resource"], 0) + offer["amount"]
    seller["money"] += offer["price"]
    seller["fin_trade"] = seller.get("fin_trade", 0) + offer["price"]
    await dbm.save_country(c); await dbm.save_country(seller)
    await dbm.db.trade_offers.delete_one({"_id": oid})
    try:
        await bot.send_message(seller["user_id"], f"🛒 «{c['name']}» پیشنهاد تو را خرید: {RESOURCES[offer['resource']]} × {offer['amount']:,} به قیمت {offer['price']:,} 💰")
    except Exception:
        pass
    await cb.message.answer(f"✅ خرید انجام شد! {RESOURCES[offer['resource']]} × {offer['amount']:,} (کارمزد: {fee:,} 💰)")
    await cb.answer()

@dp.callback_query(F.data == "trade:new")
async def trade_new(cb: types.CallbackQuery, state: FSMContext):
    c = await my_country(cb)
    if not c: return
    kb = InlineKeyboardBuilder()
    for r, label in RESOURCES.items():
        kb.button(text=f"{label} (موجودی: {c['res'].get(r, 0):,})", callback_data=f"trade:res:{r}")
    kb.adjust(1)
    await state.set_state(Trade.resource)
    kb.button(text="✖️ بستن", callback_data="close")
    await cb.message.answer("کدام منبع را می‌فروشی؟", reply_markup=kb.as_markup()); await cb.answer()

@dp.callback_query(F.data.startswith("trade:res:"), Trade.resource)
async def trade_res(cb: types.CallbackQuery, state: FSMContext):
    await state.update_data(resource=cb.data.split(":")[2])
    await state.set_state(Trade.amount)
    await cb.message.answer("چه مقدار می‌فروشی؟ (فقط عدد بفرست)"); await cb.answer()

@dp.message(Trade.amount)
async def trade_amount(msg: types.Message, state: FSMContext):
    c = await my_country(msg)
    if not c: return
    data = await state.get_data()
    try:
        amount = int(msg.text.strip())
    except ValueError:
        await msg.answer("فقط عدد بفرست:"); return
    if amount <= 0 or amount > c["res"].get(data["resource"], 0):
        await msg.answer("مقدار نامعتبر است (بیشتر از موجودی یا صفر). دوباره بفرست:"); return
    await state.update_data(amount=amount); await state.set_state(Trade.price)
    await msg.answer("قیمت کل به 💰 (عدد بفرست):")

@dp.message(Trade.price)
async def trade_price(msg: types.Message, state: FSMContext):
    c = await my_country(msg)
    if not c: return
    data = await state.get_data()
    try:
        price = int(msg.text.strip())
    except ValueError:
        await msg.answer("فقط عدد بفرست:"); return
    if price <= 0:
        await msg.answer("قیمت باید مثبت باشد:"); return
    c["res"][data["resource"]] -= data["amount"]
    await dbm.save_country(c)
    await dbm.db.trade_offers.insert_one({"seller_id": c["user_id"], "resource": data["resource"], "amount": data["amount"], "price": price, "ts": logic.now_ts()})
    await state.clear()
    await msg.answer(f"✅ پیشنهاد فروش ثبت شد: {RESOURCES[data['resource']]} × {data['amount']:,} به قیمت {price:,} 💰 — در بازار جهانی برای همه قابل خرید است.")

# ---------------------------------------------------------------- finance & migration
def finance_text(c: dict) -> str:
    fin = c.get("last_fin", {})
    prod = logic.production(c)
    b = c["buildings"]
    tax_factor = {1: 0.6, 2: 1.0, 3: 1.6}[c["tax_rate"]]
    est_tax = int(c["population"] * 0.004 * tax_factor * (1 + logic.mod(c, "economy")))
    est_upkeep = (logic.building_upkeep(c)
                  + int(c.get("soldiers", 0) * 0.15) + int(c["population"] * 0.0008))
    cap = logic.capacity(c)
    lines = [f"💰 درآمد و مالی «{c['name']}»", f"خزانه: {c['money']:,} 💰", ""]
    fd = c.get("fin_day", {})
    if any(fd.values()):
        exp = int(fd.get("upkeep_buildings", 0) + fd.get("upkeep_army", 0) + fd.get("civic", 0))
        lines += ["⏳ امروز تا این لحظه (تولید و درآمد ساعتی شده است):",
                  f"• مالیات: +{int(fd.get('tax', 0)):,} | کارخانه: +{int(fd.get('factory', 0)):,} | هزینه‌ها: −{exp:,} 💰", ""]
    if fin:
        lines += ["📅 آخرین روز کامل:",
                  f"• مالیات: +{fin.get('tax', 0):,} 💰",
                  f"• کارخانه‌ها: +{fin.get('factory', 0):,} 💰",
                  f"• فروش تجارت: +{fin.get('trade', 0):,} 💰",
                  f"• نگهداری ساختمان‌ها: −{fin.get('upkeep_buildings', 0):,} 💰",
                  f"• نگهداری ارتش: −{fin.get('upkeep_army', 0):,} 💰",
                  f"• خدمات شهری: −{fin.get('civic', 0):,} 💰",
                  f"• خالص روزانه (بدون تجارت): {fin.get('net_tick', 0):+,} 💰", ""]
    lines += [f"🔮 برآورد امروز: مالیات ~{est_tax:,} 💰 | هزینه‌ها ~{est_upkeep:,} 💰"]
    factor = logic.upkeep_factor(c)
    if factor > 1:
        lines.append(f"🏗️ ضریب نگهداری ساختمان‌ها: ×{factor:.1f} (از ۱۰ ساختمان به بعد، هزینه نگهداری به‌صورت تصاعدی بالا می‌رود)")
    lines += ["", "🏭 تولید روزانه (ناخالص):"]
    for r, v in prod.items():
        if v:
            lines.append(f"• {RESOURCES.get(r, r)}: +{int(v):,}")
    cons_f = int(c["population"] * 0.010)
    cons_w = int(c["population"] * 0.008)
    cons_e = int(c["population"] * 0.005 + sum(b.values()) * 60)
    mig_in_total = sum(m["amount"] for m in c.get("last_mig_in", c.get("mig_in_today", [])))
    lines += ["", f"🍽️ مصرف روزانه: غذا {cons_f:,} | آب {cons_w:,} | انرژی {cons_e:,}",
              f"👥 جمعیت: {c['population']:,} / ظرفیت زمین {cap:,} ({c['population'] / max(1, cap) * 100:.0f}٪ پر)",
              f"📈 تغییر جمعیت دیروز: {c.get('last_pop_delta', 0):+,} نفر",
              f"👶 تولد دیروز: +{c.get('last_births', 0):,} | ⚰️ مرگ‌ومیر دیروز: −{c.get('last_deaths', 0):,}",
              f"🧳 مهاجرت دیروز: بی‌کشور +{c.get('last_mig_pool', 0):,} | از کشورها +{mig_in_total:,} | خروج −{c.get('last_mig_out', c.get('mig_out_today', 0)):,}"]
    eco, eb = logic.eco_score(c)
    sci, sb = logic.sci_score(c)
    lines += ["", f"📊 امتیاز اقتصادی: {eco:,} (تولید {eb['prod']:,} + زیرساخت {eb['infra']:,} + خزانه {eb['treasury']:,})",
              f"🔬 امتیاز علمی: {sci:,} (تحقیقات کامل {sb['done']:,} + ظرفیت تولید تحقیق {sb['rp_day'] * 5:,})",
              f"👑 قدرت ملی: {logic.national_power(c):,}"]
    return "\n".join(lines)

@dp.message(F.text == "💰 درآمد و مالی")
@dp.message(Command("finance"))
async def cmd_finance(msg: types.Message):
    if not await gate(msg): return
    c = await my_country(msg)
    if not c: return
    await msg.answer(finance_text(c))

def migration_text(c: dict) -> str:
    has_inter = c["buildings"].get("airport_inter", 0) > 0
    lines = [f"🧳 مهاجرت «{c['name']}»", "",
             "✈️ فرودگاه بین‌المللی: ✅ داری (پیش‌فرض) — مهاجرت درون سیاره خودت فعال است.",
             ("🛸 فرودگاه بین‌سیاره‌ای: ✅ داری — از همه سیاره‌ها مهاجر می‌گیری."
              if has_inter else
              "🛸 فرودگاه بین‌سیاره‌ای: ❌ نداری — از بخش 🏗️ ساختمان‌ها بسازش (۶٬۰۰۰ 💰 + مصالح/آهن/تیتانیوم) تا از سیاره‌های دیگر هم مهاجر بگیری."),
             "", f"پذیرش مهاجر: {'روشن ✅' if c.get('accept_migrants', True) else 'خاموش ⛔'}",
             "", "📜 قوانین مهاجرت:",
             "• آدم‌های بی‌کشور هر روز به کشورهای شاد (رضایت ≥ ۵۵٪) و بدون جنگ می‌آیند؛ مالیات پایین‌تر = جذب بیشتر.",
             "• مردم کشورهای ناراضی (رضایت < ۴۵٪) به شادترین کشور قابل دسترس مهاجرت می‌کنند؛ رضایت مردم را بالا نگه دار تا جمعیت از دست ندهی.",
             "• ظرفیت جمعیت کشور = مساحت × ۶۰ نفر؛ نزدیک ظرفیت، رشد جمعیت و مهاجرت کند می‌شود."]
    ins = c.get("mig_in_today", [])
    if ins:
        lines.append("")
        lines.append("ورودی‌های امروز از کشورها: " + "، ".join(f"«{m['from']}» +{m['amount']:,}" for m in ins))
    if c.get("mig_out_today"):
        lines.append(f"خروج امروز: −{c['mig_out_today']:,} نفر")
    return "\n".join(lines)

def migration_kb(c: dict, back: bool = False):
    kb = InlineKeyboardBuilder()
    kb.button(text=("⛔ بستن پذیرش مهاجر" if c.get("accept_migrants", True) else "✅ باز کردن پذیرش مهاجر"), callback_data="mig:toggle")
    if back:
        kb.button(text="🔙 منوی اصلی", callback_data="menu:open")
    kb.button(text="✖️ بستن", callback_data="close")
    kb.adjust(1)
    return kb.as_markup()

@dp.message(F.text == "🧳 مهاجرت")
async def cmd_migration(msg: types.Message):
    if not await gate(msg): return
    c = await my_country(msg)
    if not c: return
    await msg.answer(migration_text(c), reply_markup=migration_kb(c))

@dp.callback_query(F.data == "mig:toggle")
async def mig_toggle(cb: types.CallbackQuery):
    c = await dbm.get_country(cb.from_user.id)
    if not c or not c.get("alive", True):
        await cb.answer("کشوری نداری.", show_alert=True); return
    c["accept_migrants"] = not c.get("accept_migrants", True)
    await dbm.save_country(c)
    await cb.message.edit_text(migration_text(c), reply_markup=migration_kb(c))
    await cb.answer("تنظیم پذیرش مهاجر عوض شد.")

# ------------------------------------------------- direct group trade (reply-based)
class DT(StatesGroup):
    resource = State(); amount = State(); price = State()

@dp.message(F.reply_to_message, F.text.in_({"ترید", "/trade"}), F.chat.type.in_({"group", "supergroup"}))
async def dt_start(msg: types.Message, state: FSMContext):
    target_user = msg.reply_to_message.from_user
    if not target_user or target_user.is_bot or target_user.id == msg.from_user.id:
        await msg.answer("برای ترید باید روی پیام یک بازیکن دیگر ریپلای بزنی."); return
    me = await dbm.get_country(msg.from_user.id)
    if not me or not me.get("alive", True):
        await msg.answer("تو هنوز کشوری نداری؛ اول در پیوی ربات با /start کشورت را بساز."); return
    other = await dbm.get_country(target_user.id)
    if not other or not other.get("alive", True):
        await msg.answer("این بازیکن کشوری ندارد."); return
    if not any(me["res"].get(r, 0) > 0 for r in RESOURCES):
        await msg.answer("هیچ منبعی برای فروش نداری."); return
    await state.set_state(DT.resource)
    await state.update_data(target_id=target_user.id, chat_id=msg.chat.id)
    kb = InlineKeyboardBuilder()
    for rkey, rname in RESOURCES.items():
        if me["res"].get(rkey, 0) > 0:
            kb.button(text=f"{rname} ({me['res'][rkey]:,})", callback_data=f"dt:res:{rkey}")
    kb.button(text="✖️ بستن", callback_data="close")
    kb.adjust(2)
    await msg.answer(f"💱 ترید با «{other['name']}» — کدام منبع را می‌فروشی؟", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("dt:res:"), DT.resource)
async def dt_resource(cb: types.CallbackQuery, state: FSMContext):
    rkey = cb.data.split(":")[2]
    await state.update_data(resource=rkey)
    await state.set_state(DT.amount)
    await cb.message.edit_text(f"💱 {RESOURCES[rkey]} — چه مقدار می‌فروشی؟ (عدد بفرست)")
    await cb.answer()

@dp.message(DT.amount)
async def dt_amount(msg: types.Message, state: FSMContext):
    try:
        amount = int(msg.text.replace(",", "").strip())
    except Exception:
        await msg.answer("فقط عدد بفرست:"); return
    data = await state.get_data()
    me = await dbm.get_country(msg.from_user.id)
    if not me or amount <= 0 or amount > me["res"].get(data.get("resource", ""), 0):
        await msg.answer("مقدار نامعتبر است یا موجودی کافی نداری. دوباره بفرست:"); return
    await state.update_data(amount=amount)
    await state.set_state(DT.price)
    await msg.answer("قیمت کل (💰) چقدر باشد؟ (عدد بفرست؛ ۰ = هدیه)")

@dp.message(DT.price)
async def dt_price(msg: types.Message, state: FSMContext):
    try:
        price = int(msg.text.replace(",", "").strip())
    except Exception:
        await msg.answer("فقط عدد بفرست:"); return
    if price < 0:
        await msg.answer("قیمت نمی‌تواند منفی باشد. دوباره بفرست:"); return
    data = await state.get_data()
    me = await dbm.get_country(msg.from_user.id)
    other = await dbm.get_country(data["target_id"])
    if not me or not other or not other.get("alive", True) or me["res"].get(data["resource"], 0) < data["amount"]:
        await state.clear()
        await msg.answer("❌ موجودی یا طرف ترید دیگر معتبر نیست؛ ترید لغو شد."); return
    me["res"][data["resource"]] -= data["amount"]
    await dbm.save_country(me)
    doc = {"seller_id": msg.from_user.id, "buyer_id": data["target_id"], "resource": data["resource"],
           "amount": data["amount"], "price": price, "chat_id": data["chat_id"], "ts": logic.now_ts(), "status": "pending"}
    res = await dbm.db.direct_trades.insert_one(doc)
    await state.clear()
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ قبول ترید", callback_data=f"dt:ok:{res.inserted_id}")
    kb.button(text="❌ رد", callback_data=f"dt:no:{res.inserted_id}")
    kb.adjust(2)
    price_txt = f"{price:,} 💰" if price else "رایگان (هدیه) 🎁"
    await msg.answer(f"💱 پیشنهاد ترید برای «{other['name']}»:\n{RESOURCES[data['resource']]} × {data['amount']:,} در برابر {price_txt}\nفروشنده: «{me['name']}» — فقط خودِ خریدار می‌تواند قبول یا رد کند. (اعتبار پیشنهاد: ۴۸ ساعت)", reply_markup=kb.as_markup())

async def _dt_load(cb: types.CallbackQuery):
    from bson import ObjectId
    try:
        doc = await dbm.db.direct_trades.find_one({"_id": ObjectId(cb.data.split(":")[2])})
    except Exception:
        doc = None
    if not doc or doc["status"] != "pending":
        await cb.answer("این پیشنهاد دیگر معتبر نیست.", show_alert=True); return None
    if cb.from_user.id != doc["buyer_id"]:
        await cb.answer("این پیشنهاد برای تو نیست.", show_alert=True); return None
    return doc

@dp.callback_query(F.data.startswith("dt:ok:"))
async def dt_accept(cb: types.CallbackQuery):
    doc = await _dt_load(cb)
    if not doc:
        return
    buyer = await dbm.get_country(doc["buyer_id"])
    seller = await dbm.get_country(doc["seller_id"])
    if not buyer or not buyer.get("alive", True) or not seller or not seller.get("alive", True):
        await dbm.db.direct_trades.update_one({"_id": doc["_id"]}, {"$set": {"status": "void"}})
        if seller and seller.get("alive", True):
            seller["res"][doc["resource"]] = seller["res"].get(doc["resource"], 0) + doc["amount"]
            await dbm.save_country(seller)
        await cb.message.edit_text("❌ ترید لغو شد (یکی از طرفین دیگر کشور فعالی ندارد) و منابع به فروشنده برگشت.")
        await cb.answer(); return
    fee = 0 if doc["buyer_id"] in seller["neighbors"] else int(doc["price"] * 0.05)
    if buyer["money"] < doc["price"]:
        await cb.answer(f"پول کافی نداری ({buyer['money']:,}/{doc['price']:,} 💰)", show_alert=True); return
    buyer["money"] -= doc["price"]
    seller["money"] += doc["price"] - fee
    seller["fin_trade"] = seller.get("fin_trade", 0) + doc["price"] - fee
    buyer["res"][doc["resource"]] = buyer["res"].get(doc["resource"], 0) + doc["amount"]
    await dbm.save_country(buyer); await dbm.save_country(seller)
    await dbm.db.direct_trades.update_one({"_id": doc["_id"]}, {"$set": {"status": "done"}})
    await cb.message.edit_text(f"✅ ترید انجام شد! {RESOURCES[doc['resource']]} × {doc['amount']:,} از «{seller['name']}» به «{buyer['name']}» رسید ({doc['price']:,} 💰).")
    await notify(doc["seller_id"], f"💱 تریدت با «{buyer['name']}» انجام شد: {RESOURCES[doc['resource']]} × {doc['amount']:,} فروخته شد و {doc['price'] - fee:,} 💰 گرفتی.")
    await cb.answer()

@dp.callback_query(F.data.startswith("dt:no:"))
async def dt_reject(cb: types.CallbackQuery):
    doc = await _dt_load(cb)
    if not doc:
        return
    await dbm.db.direct_trades.update_one({"_id": doc["_id"]}, {"$set": {"status": "rejected"}})
    seller = await dbm.get_country(doc["seller_id"])
    if seller and seller.get("alive", True):
        seller["res"][doc["resource"]] = seller["res"].get(doc["resource"], 0) + doc["amount"]
        await dbm.save_country(seller)
    await cb.message.edit_text("❌ پیشنهاد ترید رد شد و منابع به فروشنده برگشت.")
    await notify(doc["seller_id"], "💱 پیشنهاد تریدت رد شد؛ منابع به انبارت برگشت.")
    await cb.answer()

# ---------------------------------------------------------------- diplomacy
@dp.message(F.text == "🤝 دیپلماسی")
@dp.message(Command("diplomacy"))
async def cmd_diplomacy(msg: types.Message):
    if not await gate(msg): return
    c = await my_country(msg)
    if not c: return
    lines = [f"🤝 دیپلماسی «{c['name']}»\n\nهمسایه‌ها ({len(c['neighbors'])}/۴):"]
    for nid in c["neighbors"]:
        n = await dbm.get_country(nid)
        lines.append(f" • {n['name'] if n else '(حذف شده)'}")
    if c["alliances"]:
        lines.append("\nاتحادها:")
        for aid in c["alliances"]:
            a = await dbm.get_country(aid)
            lines.append(f" • {a['name'] if a else '?'}")
    lines.append("\nبرای تعامل با یک کشور، اسم انگلیسی‌اش را با دستور زیر بفرست:\n/find <CountryName>")
    await msg.answer("\n".join(lines))

async def diplo_text(c: dict) -> str:
    lines = [f"🤝 دیپلماسی «{c['name']}»\n\nهمسایه‌ها ({len(c['neighbors'])}/۴):"]
    for nid in c["neighbors"]:
        n = await dbm.get_country(nid)
        lines.append(f" • {n['name'] if n else '(حذف شده)'}")
    if c["alliances"]:
        lines.append("\nاتحادها:")
        for aid in c["alliances"]:
            a = await dbm.get_country(aid)
            lines.append(f" • {a['name'] if a else '?'}")
    lines.append("\nبرای تعامل با یک کشور، اسم انگلیسی‌اش را با دستور زیر بفرست:\n/find <CountryName>")
    return "\n".join(lines)

@dp.message(Command("find"))
async def cmd_find(msg: types.Message):
    if not await gate(msg): return
    c = await my_country(msg)
    if not c: return
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("اسم کشور را بنویس: /find <CountryName>"); return
    target = await dbm.get_country_by_name(parts[1])
    if not target or not target.get("alive"):
        await msg.answer("چنین کشور فعالی پیدا نشد."); return
    if target["user_id"] == c["user_id"]:
        await msg.answer("این کشور خودت است!"); return
    p = PLANETS[target["planet"]]
    kb = InlineKeyboardBuilder()
    tid = target["user_id"]
    if tid not in c["neighbors"] and len(c["neighbors"]) < 4:
        kb.button(text="🏘️ درخواست همسایگی", callback_data=f"req:neighbor:{tid}")
    if tid not in c["alliances"]:
        kb.button(text="🛡️ درخواست اتحاد", callback_data=f"req:alliance:{tid}")
    if tid not in c.get("naps", []):
        kb.button(text="🕊️ پیمان عدم تجاوز", callback_data=f"req:nap:{tid}")
    kb.button(text="⚔️ اعلان جنگ", callback_data=f"war:declare:{tid}")
    kb.button(text="✖️ بستن", callback_data="close")
    kb.adjust(1)
    rel = []
    if tid in c["neighbors"]: rel.append("همسایه")
    if tid in c["alliances"]: rel.append("متحد")
    if tid in c.get("naps", []): rel.append("پیمان عدم تجاوز")
    await msg.answer(
        f"🏳️ «{target['name']}» — پایتخت {target['capital']}\n🪐 {p['name']} / {p['continents'][target['continent']]['name']}\n"
        f"👥 جمعیت: {target['population']:,} | 🗺️ مساحت: {target['area']:,} | 🪖 قدرت نظامی: {logic.military_power(target):,}\n"
        f"رابطه: {('، '.join(rel)) if rel else 'بدون رابطه'}",
        reply_markup=kb.as_markup())

REQ_LABEL = {"neighbor": "🏘️ درخواست همسایگی", "alliance": "🛡️ درخواست اتحاد", "nap": "🕊️ پیمان عدم تجاوز"}

@dp.callback_query(F.data.startswith("req:"))
async def req_send(cb: types.CallbackQuery):
    c = await my_country(cb)
    if not c: return
    _, kind, tid = cb.data.split(":")
    tid = int(tid)
    target = await dbm.get_country(tid)
    if not target or not target.get("alive"):
        await cb.answer("کشور مقصد فعال نیست.", show_alert=True); return
    if kind == "neighbor" and (len(c["neighbors"]) >= 4 or len(target["neighbors"]) >= 4):
        await cb.answer("یکی از دو کشور سقف ۴ همسایه را پر کرده است.", show_alert=True); return
    await dbm.create_request(kind, c["user_id"], tid)
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ قبول", callback_data=f"reqok:{kind}:{c['user_id']}")
    kb.button(text="❌ رد", callback_data=f"reqno:{kind}:{c['user_id']}")
    kb.adjust(2)
    try:
        await bot.send_message(tid, f"{REQ_LABEL[kind]} از کشور «{c['name']}» برای تو ارسال شد.", reply_markup=kb.as_markup())
        await cb.answer("درخواست ارسال شد.")
    except Exception:
        await cb.answer("نتوانستم به حاکم آن کشور پیام بدهم (ربات را استارت نکرده است).", show_alert=True)

@dp.callback_query(F.data.startswith("reqok:"))
async def req_accept(cb: types.CallbackQuery):
    _, kind, fid = cb.data.split(":")
    fid = int(fid)
    me = await dbm.get_country(cb.from_user.id)
    other = await dbm.get_country(fid)
    if not me or not other or not await dbm.pop_request(kind, fid, cb.from_user.id):
        await cb.answer("این درخواست دیگر معتبر نیست.", show_alert=True); return
    # BUGFIX: re-check the 4-neighbour cap at accept time (it was only checked when
    # the request was sent, so queued requests could push a country past 4).
    if kind == "neighbor":
        if fid in me["neighbors"]:
            await cb.message.edit_text("شما همین حالا هم همسایه‌اید."); await cb.answer(); return
        if len(me["neighbors"]) >= 4 or len(other["neighbors"]) >= 4:
            await cb.message.edit_text("❌ یکی از دو کشور سقف ۴ همسایه را پر کرده است؛ درخواست قبول نشد.")
            await cb.answer(); return
    field = {"neighbor": "neighbors", "alliance": "alliances", "nap": "naps"}[kind]
    for a, b in ((me, other), (other, me)):
        if b["user_id"] not in a[field]:
            a[field].append(b["user_id"])
    # becoming neighbors also opens the blocked border direction if present
    for a, b in ((me, other), (other, me)):
        if kind == "neighbor":
            for d, binfo in a["borders"].items():
                if binfo.get("country_id") == b["user_id"]:
                    binfo["label"] = f"مرز کشور همسایه {b['name']}"
    await dbm.save_country(me); await dbm.save_country(other)
    await cb.message.edit_text(f"✅ {REQ_LABEL[kind]} از «{other['name']}» قبول شد.")
    try:
        await bot.send_message(fid, f"✅ کشور «{me['name']}» {REQ_LABEL[kind]} تو را قبول کرد.")
    except Exception:
        pass
    await cb.answer()

@dp.callback_query(F.data.startswith("reqno:"))
async def req_decline(cb: types.CallbackQuery):
    _, kind, fid = cb.data.split(":")
    await dbm.pop_request(kind, int(fid), cb.from_user.id)
    await cb.message.edit_text("❌ درخواست رد شد.")
    await cb.answer()

# ---------------------------------------------------------------- army & war
@dp.message(F.text == "🪖 ارتش و جنگ")
@dp.message(Command("army"))
async def cmd_army(msg: types.Message):
    if not await gate(msg): return
    c = await my_country(msg)
    if not c: return
    lines = [f"🪖 ارتش «{c['name']}»\nسرباز: {c['soldiers']:,} | قدرت نظامی: {logic.military_power(c):,} | قدرت دفاعی: {logic.defense_power(c):,}"]
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ سربازگیری ۱۰۰ نفر (🧱۵۰ ⛏️۲۰ 💰۱۵۰)", callback_data="army:recruit")
    if c.get("war_id"):
        war = await dbm.db.wars.find_one({"_id": c["war_id"]})
        if war:
            enemy_id = war["defender_id"] if war["attacker_id"] == c["user_id"] else war["attacker_id"]
            enemy = await dbm.get_country(enemy_id)
            left = max(0, war["end_ts"] - logic.now_ts())
            my_score = war["att_score"] if war["attacker_id"] == c["user_id"] else war["def_score"]
            lines.append(f"\n⚔️ در جنگ با «{enemy['name'] if enemy else '?'}» هستی — پایان جنگ: {left // 3600} ساعت دیگر | امتیاز جنگی تو: {my_score:,}")
            kb.button(text="💥 عملیات نظامی امروز", callback_data="war:op")
    kb.adjust(1)
    lines.append("\nبرای اعلان جنگ، کشور هدف را با /find پیدا کن.")
    kb.button(text="✖️ بستن", callback_data="close")
    sent = await msg.answer("\n".join(lines), reply_markup=kb.as_markup())
    await track_menu(sent, msg.from_user.id)

async def army_view(c: dict, back: bool = False):
    lines = [f"🪖 ارتش «{c['name']}»\nسرباز: {c['soldiers']:,} | قدرت نظامی: {logic.military_power(c):,} | قدرت دفاعی: {logic.defense_power(c):,}"]
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ سربازگیری ۱۰۰ نفر (🧱۵۰ ⛏️۲۰ 💰۱۵۰)", callback_data="army:recruit")
    if c.get("war_id"):
        war = await dbm.db.wars.find_one({"_id": c["war_id"]})
        if war:
            enemy_id = war["defender_id"] if war["attacker_id"] == c["user_id"] else war["attacker_id"]
            enemy = await dbm.get_country(enemy_id)
            left = max(0, war["end_ts"] - logic.now_ts())
            my_score = war["att_score"] if war["attacker_id"] == c["user_id"] else war["def_score"]
            lines.append(f"\n⚔️ در جنگ با «{enemy['name'] if enemy else '?'}» هستی — پایان جنگ: {left // 3600} ساعت دیگر | امتیاز جنگی تو: {my_score:,}")
            kb.button(text="💥 عملیات نظامی امروز", callback_data="war:op")
    kb.adjust(1)
    lines.append("\nبرای اعلان جنگ، کشور هدف را با /find پیدا کن.")
    if back:
        kb.button(text="🔙 منوی اصلی", callback_data="menu:open")
    kb.button(text="✖️ بستن", callback_data="close")
    return "\n".join(lines), kb.as_markup()

@dp.callback_query(F.data == "army:recruit")
async def army_recruit(cb: types.CallbackQuery):
    c = await my_country(cb)
    if not c: return
    cost = {"materials": 50, "iron": 20, "money": 150}
    for k, v in cost.items():
        have = c["money"] if k == "money" else c["res"].get(k, 0)
        if have < v:
            await cb.answer(f"منابع کافی نداری ({k})", show_alert=True); return
    c["money"] -= 150; c["res"]["materials"] -= 50; c["res"]["iron"] -= 20
    c["soldiers"] += 100
    await dbm.save_country(c)
    await cb.message.answer(f"🪖 ۱۰۰ سرباز جدید گرفته شد. کل سرباز: {c['soldiers']:,}")
    await cb.answer()

@dp.callback_query(F.data.startswith("war:declare:"))
async def war_declare(cb: types.CallbackQuery):
    c = await my_country(cb)
    if not c: return
    tid = int(cb.data.split(":")[2])
    target = await dbm.get_country(tid)
    if not target or not target.get("alive"):
        await cb.answer("کشور هدف فعال نیست.", show_alert=True); return
    if c.get("war_id") or target.get("war_id"):
        await cb.answer("یکی از دو کشور همین حالا در جنگ دیگری است (همزمان فقط یک جنگ).", show_alert=True); return
    if target["planet"] != c["planet"]:
        await cb.answer("جنگ بین‌سیاره‌ای ممکن نیست؛ فقط با کشورهای هم‌سیاره خودت می‌توانی بجنگی.", show_alert=True); return
    t_now = logic.now_ts()
    for side, who in ((c, "تو"), (target, "کشور هدف")):
        pu = side.get("peace_until", 0)
        if t_now < pu:
            left_h = (pu - t_now) // 3600
            await cb.answer(f"{who} در آتش‌بس پس از جنگ است ({left_h} ساعت مانده).", show_alert=True); return
    if logic.now_ts() < target.get("newbie_until", 0):
        await cb.answer("این کشور تازه‌وارد است و ۷ روز اول محافظت می‌شود.", show_alert=True); return
    if tid in c.get("naps", []):
        await cb.answer("با این کشور پیمان عدم تجاوز داری.", show_alert=True); return
    res = await dbm.db.wars.insert_one({
        "attacker_id": c["user_id"], "defender_id": tid,
        "start_ts": logic.now_ts(), "end_ts": logic.now_ts() + 3 * logic.DAY,
        "att_score": 0, "def_score": 0, "ops": {}})
    c["war_id"] = res.inserted_id; target["war_id"] = res.inserted_id
    c["happiness"] = max(0, c["happiness"] - 3)
    await dbm.save_country(c); await dbm.save_country(target)
    try:
        await bot.send_message(tid, f"🚨 اعلان جنگ! کشور «{c['name']}» به تو اعلان جنگ داد. جنگ ۳ روز طول می‌کشد؛ هر روز از بخش «ارتش و جنگ» عملیات نظامی انجام بده تا امتیاز جنگی بگیری.")
    except Exception:
        pass
    await cb.message.answer(f"⚔️ جنگ با «{target['name']}» شروع شد! ۳ روز واقعی طول می‌کشد. هر روز یک عملیات نظامی می‌توانی انجام بدهی.")
    await cb.answer()

@dp.callback_query(F.data == "war:op")
async def war_op(cb: types.CallbackQuery):
    c = await my_country(cb)
    if not c or not c.get("war_id"): return
    war = await dbm.db.wars.find_one({"_id": c["war_id"]})
    if not war:
        await cb.answer("جنگ پیدا نشد.", show_alert=True); return
    day_key = str(int((logic.now_ts() - war["start_ts"]) // logic.DAY))
    op_key = f"{c['user_id']}:{day_key}"
    if war.get("ops", {}).get(op_key):
        await cb.answer("امروز عملیاتت را انجام داده‌ای؛ فردا دوباره.", show_alert=True); return
    import random as _r
    gain = int(logic.military_power(c) * _r.uniform(0.25, 0.45)) + _r.randint(10, 60)
    field = "att_score" if war["attacker_id"] == c["user_id"] else "def_score"
    war.setdefault("ops", {})[op_key] = gain
    war[field] += gain
    await dbm.db.wars.replace_one({"_id": war["_id"]}, war)
    await cb.message.answer(f"💥 عملیات نظامی انجام شد: +{gain:,} امتیاز جنگی.")
    await cb.answer()


# ---------------------------------------------------------------- glass menu, text triggers, menu ownership
GLASS_TEXT = "🎛️ منوی اصلی — بخش موردنظرت را انتخاب کن:"

def glass_kb():
    kb = InlineKeyboardBuilder()
    for txt, key in [("🏳️ کشور من", "country"), ("🔭 اکتشاف", "explore"),
                     ("🏗️ ساختمان‌ها", "build"), ("🔬 تحقیق", "research"),
                     ("🛒 تجارت", "trade"), ("🤝 دیپلماسی", "diplo"),
                     ("⚔️ ارتش و جنگ", "army"), ("🏆 رتبه‌بندی", "top"),
                     ("💰 درآمد و مالی", "finance"), ("🧳 مهاجرت", "migration"),
                     ("❓ راهنما", "guide")]:
        kb.button(text=txt, callback_data=f"menu:go:{key}")
    kb.button(text="✖️ بستن", callback_data="close")
    kb.adjust(2, 2, 2, 2, 2, 1, 1)
    return kb.as_markup()

def back_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 منوی اصلی", callback_data="menu:open")
    kb.button(text="✖️ بستن", callback_data="close")
    kb.adjust(2)
    return kb.as_markup()

async def render_section(key: str, c: dict):
    """(text, markup) for a main section, with a back-to-glass-menu button."""
    if key == "country":
        return country_view(c, back=True)
    if key == "explore":
        return explore_view(c, back=True)
    if key == "build":
        return build_view(c, back=True)
    if key == "research":
        return research_view(c, back=True)
    if key == "trade":
        return trade_view(c, back=True)
    if key == "diplo":
        return await diplo_text(c), back_kb()
    if key == "army":
        return await army_view(c, back=True)
    if key == "top":
        return await leaderboard_text("power"), lb_kb("power", back=True)
    if key == "finance":
        return finance_text(c), back_kb()
    if key == "migration":
        return migration_text(c), migration_kb(c, back=True)
    if key == "guide":
        return GUIDE_TEXT, back_kb()
    return GLASS_TEXT, glass_kb()

async def track_menu(sent, user_id: int):
    """Remember who a menu message belongs to; the owner middleware then makes
    its buttons work only for that player (in groups everyone sees the message,
    but only the owner can press its buttons)."""
    try:
        if sent is not None:
            await dbm.db.menu_owners.update_one(
                {"_id": f"{sent.chat.id}:{sent.message_id}"},
                {"$set": {"user_id": user_id}}, upsert=True)
    except Exception:
        log.exception("track_menu failed")

async def menu_owner_mw(handler, event, data):
    if isinstance(event, types.CallbackQuery) and event.message is not None:
        try:
            doc = await dbm.db.menu_owners.find_one({"_id": f"{event.message.chat.id}:{event.message.message_id}"})
        except Exception:
            doc = None
        if doc and doc.get("user_id") != event.from_user.id:
            await event.answer("🔒 این منو مال بازیکن دیگری است؛ اسم بخش را بنویس (مثل «لیدربورد») یا «منو» را بفرست تا منوی خودت باز شود.", show_alert=True)
            return None
    return await handler(event, data)

dp.callback_query.outer_middleware(menu_owner_mw)

@dp.callback_query(F.data == "menu:open")
async def menu_open(cb: types.CallbackQuery):
    try:
        await cb.message.edit_text(GLASS_TEXT, reply_markup=glass_kb())
    except Exception:
        sent = await cb.message.answer(GLASS_TEXT, reply_markup=glass_kb())
        await track_menu(sent, cb.from_user.id)
    await cb.answer()

@dp.callback_query(F.data.startswith("menu:go:"))
async def menu_go(cb: types.CallbackQuery):
    c = await my_country(cb)
    if not c: return
    key = cb.data.split(":")[2]
    if key == "explore":
        logic.regen_charges(c); await dbm.save_country(c)
    text, kb = await render_section(key, c)
    try:
        await cb.message.edit_text(text, reply_markup=kb)
    except Exception:
        sent = await cb.message.answer(text, reply_markup=kb)
        await track_menu(sent, cb.from_user.id)
    await cb.answer()

TEXT_TRIGGERS = {
    "لیدربورد": "top", "رتبه‌بندی": "top", "رتبه بندی": "top", "leaderboard": "top", "top": "top",
    "تجارت": "trade", "بازار": "trade", "trade": "trade",
    "کشور من": "country", "کشور": "country", "country": "country",
    "اکتشاف": "explore", "explore": "explore",
    "ساختمان‌ها": "build", "ساختمان ها": "build", "ساختمان": "build", "build": "build",
    "تحقیق": "research", "research": "research",
    "دیپلماسی": "diplo", "diplomacy": "diplo",
    "ارتش": "army", "جنگ": "army", "ارتش و جنگ": "army", "army": "army",
    "درآمد": "finance", "مالی": "finance", "درآمد و مالی": "finance", "finance": "finance",
    "مهاجرت": "migration", "migration": "migration",
    "راهنما": "guide", "کمک": "guide",
    "منو": "menu", "منوی اصلی": "menu", "menu": "menu",
}

# ---------------------------------------------------------------- leaderboard / guide / admin
LB_MODES = {"power": "👑 قدرت ملی", "eco": "💰 امتیاز اقتصادی", "sci": "🔬 امتیاز علمی",
            "pop": "👥 جمعیت", "area": "🗺️ مساحت"}
LB_FIELDS = {"pop": "population", "area": "area"}

def lb_kb(mode: str, back: bool = False):
    kb = InlineKeyboardBuilder()
    for key, label in LB_MODES.items():
        kb.button(text=("✅ " if key == mode else "") + label, callback_data=f"lb:{key}")
    if back:
        kb.button(text="🔙 منوی اصلی", callback_data="menu:open")
    kb.button(text="✖️ بستن", callback_data="close")
    kb.adjust(3, 2, 2 if back else 1)
    return kb.as_markup()

async def leaderboard_text(mode: str) -> str:
    label = LB_MODES[mode]
    lines = [f"🏆 رتبه‌بندی جهانی (بر اساس {label}):"]
    if mode in LB_FIELDS:
        rows = [(c, None) for c in await dbm.top_countries(LB_FIELDS[mode], 10)]
    else:
        # computed scores: fetch all alive countries and sort in Python
        scored = []
        for c in await dbm.all_alive_countries():
            eco, eb = logic.eco_score(c)
            sci, sb = logic.sci_score(c)
            power = logic.national_power(c)
            key = {"power": power, "eco": eco, "sci": sci}[mode]
            scored.append((key, c, (eco, eb, sci, sb, power)))
        scored.sort(key=lambda t: t[0], reverse=True)
        rows = [(c, extra) for _, c, extra in scored[:10]]
    for i, (c, extra) in enumerate(rows, 1):
        # two-line rows: in RTL chat a population figure and an area figure on
        # one line visually merge into one giant number
        if mode == "pop":
            head = f"{i}. «{c['name']}» — 👥 {c['population']:,} نفر"
            sub = f"🗺️ مساحت: {c['area']:,} کیلومتر مربع"
        elif mode == "area":
            head = f"{i}. «{c['name']}» — 🗺️ {c['area']:,} کیلومتر مربع"
            sub = f"👥 جمعیت: {c['population']:,} نفر"
        elif mode == "power":
            eco, eb, sci, sb, power = extra
            head = f"{i}. «{c['name']}» — 👑 قدرت ملی: {power:,}"
            sub = f"💰 اقتصادی: {eco:,} | 🔬 علمی: {sci:,} | 👥 جمعیت: {c['population']:,} نفر"
        elif mode == "eco":
            eco, eb, sci, sb, power = extra
            head = f"{i}. «{c['name']}» — 💰 امتیاز اقتصادی: {eco:,}"
            sub = f"🏭 ارزش تولید روزانه: {eb['prod_value']:,} | 🧱 زیرساخت: {eb['infra']:,} | 💰 خزانه: {c['money']:,}"
        else:  # sci
            eco, eb, sci, sb, power = extra
            head = f"{i}. «{c['name']}» — 🔬 امتیاز علمی: {sci:,}"
            sub = f"📚 تحقیقات کامل: {len(c.get('researched', []))} | ⚗️ تولید تحقیق روزانه: {sb['rp_day']} RP"
        lines += ["", head, sub]
    return "\n".join(lines)

@dp.message(F.text == "🏆 رتبه‌بندی")
@dp.message(Command("top"))
async def cmd_top(msg: types.Message):
    if not await gate(msg): return
    sent = await msg.answer(await leaderboard_text("power"), reply_markup=lb_kb("power"))
    await track_menu(sent, msg.from_user.id)

@dp.callback_query(F.data.startswith("lb:"))
async def lb_cb(cb: types.CallbackQuery):
    mode = cb.data.split(":")[1]
    if mode not in LB_MODES:
        return
    await cb.message.edit_text(await leaderboard_text(mode), reply_markup=lb_kb(mode))
    await cb.answer()

@dp.message(F.text == "❓ راهنما")
@dp.message(F.text == "✖️ بستن منو")
async def close_main_kb(msg: types.Message):
    """Hide the main reply keyboard — per-user in groups (selective), so closing
    one person's menu no longer closes it for everyone."""
    if msg.chat.type == "private":
        await msg.answer("منوی اصلی بسته شد. ✖️\nبرای باز کردنش /menu را بزن.", reply_markup=ReplyKeyboardRemove())
    else:
        await msg.reply("منو فقط برای تو بسته شد. ✖️ برای باز کردنش /menu را بزن.", reply_markup=ReplyKeyboardRemove(selective=True))

@dp.message(Command("menu"))
async def cmd_menu(msg: types.Message):
    # glass (inline) menu instead of the bottom reply keyboard; in groups it is
    # sent as a reply to the user and its buttons are owner-locked
    if msg.chat.type == "private":
        sent = await msg.answer(GLASS_TEXT, reply_markup=glass_kb())
    else:
        sent = await msg.reply(GLASS_TEXT, reply_markup=glass_kb())
    await track_menu(sent, msg.from_user.id)

@dp.message(Command("cancel"))
async def cmd_cancel(msg: types.Message, state: FSMContext):
    await state.clear()
    await msg.answer("✖️ عملیات جاری لغو شد.", reply_markup=glass_kb() if msg.chat.type == "private" else None)

@dp.message(Command("help"))
async def cmd_help(msg: types.Message):
    sent = await msg.answer(GUIDE_TEXT, reply_markup=glass_kb() if msg.chat.type == "private" else None)
    if msg.chat.type == "private":
        await track_menu(sent, msg.from_user.id)

@dp.message(Command("admin_reset_planet"))
async def cmd_admin(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    parts = msg.text.split()
    if len(parts) == 2 and parts[1] in PLANETS:
        res = await dbm.db.countries.delete_many({"planet": parts[1]})
        await msg.answer(f"♻️ سیاره {parts[1]} ریست شد ({res.deleted_count} کشور حذف شد).")

@dp.message(F.text)
async def text_trigger(msg: types.Message, state: FSMContext):
    """Bare-word shortcuts (لیدربورد، تجارت، کشور من، منو...). Registered as the
    LAST message handler and raises SkipHandler on any non-trigger text, so it
    can never shadow a real button or command handler (an earlier placement
    silently swallowed «بستن منو», /menu, /help and the رتبه‌بندی button)."""
    if await state.get_state() is not None:
        raise SkipHandler
    key = TEXT_TRIGGERS.get(msg.text.strip().lower())
    if not key:
        raise SkipHandler
    if not await gate(msg):
        return
    in_group = msg.chat.type != "private"
    if key == "menu":
        sent = await (msg.reply(GLASS_TEXT, reply_markup=glass_kb()) if in_group
                      else msg.answer(GLASS_TEXT, reply_markup=glass_kb()))
        await track_menu(sent, msg.from_user.id)
        return
    c = await my_country(msg)
    if not c:
        return
    if key == "explore":
        logic.regen_charges(c); await dbm.save_country(c)
    text, kb = await render_section(key, c)
    sent = await (msg.reply(text, reply_markup=kb) if in_group else msg.answer(text, reply_markup=kb))
    await track_menu(sent, msg.from_user.id)

# ---------------------------------------------------------------- minute tick (cron-job.com)
async def notify(user_id: int, text: str):
    try:
        await bot.send_message(user_id, text)
    except Exception:
        pass

async def run_tick() -> dict:
    """Called every 1 minute by cron-job.com. Drives ALL game timers."""
    t = logic.now_ts()
    stats = {"charges": 0, "research_done": 0, "daily": 0, "wars_resolved": 0, "collapsed": 0, "frozen": 0, "offers_expired": 0, "migrants": 0}
    countries = await dbm.all_alive_countries()
    for c in countries:
        changed = False
        # inactivity freeze flag (14 days)
        if t - c.get("last_seen_ts", t) > 14 * logic.DAY and not c.get("frozen"):
            c["frozen"] = True; changed = True; stats["frozen"] += 1
        # exploration charges (1/hour, stored up to cap)
        if logic.regen_charges(c, t):
            stats["charges"] += 1; changed = True
        # research completion
        if c.get("researching") and t >= c["researching"]["finish_ts"]:
            rid = c["researching"]["id"]
            c["researched"].append(rid)
            c["researching"] = None
            stats["research_done"] += 1; changed = True
            await notify(c["user_id"], f"🔬 تحقیق «{RESEARCH[rid]['fa']}» کامل شد! اثر آن از حالا فعال است.")
        # hourly living-sim slice: economy, births/deaths, happiness, RP, pool migration
        last_h = c.get("last_hour_ts", c.get("last_econ_ts", c.get("last_daily_ts", t)))
        if t - last_h >= 3600:
            hours = min(48, (t - last_h) // 3600)
            res_h = logic.hourly_tick(c, t, hours)
            c["last_hour_ts"] = last_h + hours * 3600
            c["last_econ_ts"] = c["last_hour_ts"]
            changed = True
            if res_h["collapsed"]:
                c["alive"] = False
                stats["collapsed"] += 1
                await notify(c["user_id"], "💥 کشور تو به دلیل اعتراض‌های پی‌درپی و رضایت بسیار پایین فروپاشید! با /start یک کشور تازه بساز.")
        # daily snapshot & report (the living simulation itself is hourly now)
        if c.get("alive", True) and t - c.get("last_daily_ts", t) >= logic.DAY:
            rep = logic.daily_tick(c, t)
            stats["daily"] += 1; changed = True
            await notify(c["user_id"], "📅 گزارش روزانه کشورت:\n" + "\n".join(rep["report"]))
        if changed:
            await dbm.save_country(c)
    # cross-country migration (HOURLY since the hourly-sim round; before that a
    # DAILY gate fixed the bug where per-day rates ran on every 1-minute tick).
    # Amounts scale with elapsed hours via frac; totals surface in the daily
    # report and finance view instead of a notification per move.
    try:
        meta = await dbm.db.meta.find_one({"_id": "migration"})
        mig_ts = meta.get("ts", 0) if meta else 0
        if t - mig_ts >= 3600:
            mig_hours = min(48, (t - mig_ts) // 3600)
            all_c = [doc async for doc in dbm.db.countries.find({"alive": True, "frozen": {"$ne": True}})]
            by_id = {d["user_id"]: d for d in all_c}
            for src_id, dst_id, amount in logic.plan_migration(all_c, frac=mig_hours / 24):
                src_c, dst_c = by_id[src_id], by_id[dst_id]
                src_c["population"] = max(10000, src_c["population"] - amount)
                logic.adjust_cities(src_c, -amount)
                dst_c["population"] += amount
                logic.adjust_cities(dst_c, amount)
                src_c["mig_out_today"] = src_c.get("mig_out_today", 0) + amount
                dst_c.setdefault("mig_in_today", []).append({"from": src_c["name"], "amount": amount})
                await dbm.save_country(src_c); await dbm.save_country(dst_c)
                stats["migrants"] += amount
            await dbm.db.meta.update_one({"_id": "migration"}, {"$set": {"ts": mig_ts + mig_hours * 3600}}, upsert=True)
    except Exception:
        log.exception("migration phase failed")
    # wars whose 3 days are over
    async for war in dbm.db.wars.find({"end_ts": {"$lte": t}}):
        attacker = await dbm.get_country(war["attacker_id"])
        defender = await dbm.get_country(war["defender_id"])
        await dbm.db.wars.delete_one({"_id": war["_id"]})
        if not attacker or not defender:
            continue
        # BUGFIX: if one side collapsed mid-war its country is dead; resolving the
        # war against it produced nonsense outcomes. Cancel the war instead.
        if not attacker.get("alive", True) or not defender.get("alive", True):
            for side in (attacker, defender):
                if side.get("alive", True) and side.get("war_id") is not None:
                    side["war_id"] = None
                    await dbm.save_country(side)
                    await notify(side["user_id"], "⚔️ جنگ شما به دلیل فروپاشی یکی از طرفین لغو شد.")
            stats["wars_resolved"] += 1
            continue
        outcome = logic.resolve_war(war, attacker, defender)
        stats["wars_resolved"] += 1
        if outcome["result"] == "annex":
            msg_a = f"🏆 پیروزی کامل! کشور «{defender['name']}» به طور کامل تصرف شد (امتیاز {outcome['a_score']:,} در برابر {outcome['d_score']:,}). خاک، معادن و نیمی از منابعش به تو رسید."
            msg_d = f"💀 کشور تو در جنگ با «{attacker['name']}» به طور کامل سقوط کرد (امتیاز {outcome['d_score']:,} در برابر {outcome['a_score']:,}). با /start کشور تازه‌ای بساز."
            await dbm.save_country(attacker)
            await dbm.delete_country(defender["user_id"])
        elif outcome["result"] == "partial":
            msg_a = f"🏆 پیروزی در جنگ با «{defender['name']}»! (امتیاز {outcome['a_score']:,} در برابر {outcome['d_score']:,}) — {outcome['taken']:,} کیلومتر مربع و بخشی از معادن و غرامت گرفتی."
            msg_d = f"⚔️ جنگ با «{attacker['name']}» را باختی (امتیاز {outcome['d_score']:,} در برابر {outcome['a_score']:,}) و ۲۵٪ از خاکت را از دست دادی."
            await dbm.save_country(attacker); await dbm.save_country(defender)
        else:
            msg_a = f"⚔️ حمله‌ات به «{defender['name']}» شکست خورد (امتیاز {outcome['a_score']:,} در برابر {outcome['d_score']:,}) و {outcome['reparations']:,} 💰 غرامت دادی."
            msg_d = f"🛡️ دفاع موفق! حمله «{attacker['name']}» دفع شد (امتیاز {outcome['d_score']:,} در برابر {outcome['a_score']:,}) و {outcome['reparations']:,} 💰 غرامت گرفتی."
            await dbm.save_country(attacker); await dbm.save_country(defender)
        await notify(war["attacker_id"], msg_a)
        if outcome["result"] != "annex":
            await notify(war["defender_id"], msg_d)
        else:
            await notify(war["defender_id"], msg_d)
    # trade offers expire after 7 days; unsold resources return to the seller
    async for offer in dbm.db.trade_offers.find({"ts": {"$lt": t - 7 * logic.DAY}}):
        await dbm.db.trade_offers.delete_one({"_id": offer["_id"]})
        seller = await dbm.get_country(offer["seller_id"])
        if seller and seller.get("alive", True):
            seller["res"][offer["resource"]] = seller["res"].get(offer["resource"], 0) + offer["amount"]
            await dbm.save_country(seller)
            await notify(offer["seller_id"], f"🛒 پیشنهاد فروشت در بازار جهانی منقضی شد (۷ روز گذشت) و {RESOURCES[offer['resource']]} × {offer['amount']:,} به انبارت برگشت.")
        stats["offers_expired"] += 1
    # direct (reply-based) trade offers expire after 48h; resources return to seller
    async for doc in dbm.db.direct_trades.find({"status": "pending", "ts": {"$lt": t - 2 * logic.DAY}}):
        await dbm.db.direct_trades.update_one({"_id": doc["_id"]}, {"$set": {"status": "expired"}})
        seller = await dbm.get_country(doc["seller_id"])
        if seller and seller.get("alive", True):
            seller["res"][doc["resource"]] = seller["res"].get(doc["resource"], 0) + doc["amount"]
            await dbm.save_country(seller)
            await notify(doc["seller_id"], "💱 پیشنهاد ترید مستقیمت منقضی شد (۴۸ ساعت گذشت) و منابع به انبارت برگشت.")
        stats["offers_expired"] += 1
    return stats

async def handle_tick(request: web.Request) -> web.Response:
    secret = request.query.get("secret") or request.headers.get("X-Tick-Secret")
    if secret != TICK_SECRET:
        return web.json_response({"error": "forbidden"}, status=403)
    stats = await run_tick()
    return web.json_response({"ok": True, "ts": logic.now_ts(), **stats})

async def handle_health(request: web.Request) -> web.Response:
    return web.json_response({"ok": True, "service": "country-game-bot"})

async def handle_webhook(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        update = types.Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception:
        log.exception("webhook error")
    return web.json_response({"ok": True})

async def main():
    dbm.init_db()
    try:
        await bot.set_my_commands([
            BotCommand(command="start", description="🏳️ شروع بازی / ساخت کشور"),
            BotCommand(command="help", description="❓ راهنمای بازی"),
            BotCommand(command="cancel", description="✖️ لغو عملیات جاری"),
            BotCommand(command="menu", description="📋 نمایش منوی اصلی"),
            BotCommand(command="finance", description="💰 درآمد و مالی"),
        ])
    except Exception:
        log.exception("set_my_commands failed")
    await dbm.ensure_indexes()
    base = os.environ.get("WEBHOOK_BASE_URL") or os.environ.get("RENDER_EXTERNAL_URL", "")
    app = web.Application()
    app.router.add_get("/", handle_health)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/tick", handle_tick)
    app.router.add_post("/tick", handle_tick)
    port = int(os.environ.get("PORT", "8080"))
    if base:
        # SECURITY FIX: the webhook path carries a hash of the bot token, so the
        # endpoint is not guessable — previously anyone could POST fake Telegram
        # updates (fake users/messages) to the plain /webhook path.
        webhook_path = "/webhook/" + hashlib.sha256(BOT_TOKEN.encode()).hexdigest()[:32]
        app.router.add_post(webhook_path, handle_webhook)
        await bot.set_webhook(base.rstrip("/") + webhook_path)
        log.info("webhook set (secret path)")
        runner = web.AppRunner(app)
        await runner.setup()
        await web.TCPSite(runner, "0.0.0.0", port).start()
        log.info("web server on %s", port)
        await asyncio.Event().wait()
    else:
        # local dev fallback: polling + tick server
        await bot.delete_webhook(drop_pending_updates=True)
        runner = web.AppRunner(app)
        await runner.setup()
        await web.TCPSite(runner, "0.0.0.0", port).start()
        log.info("polling mode on port %s", port)
        await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
