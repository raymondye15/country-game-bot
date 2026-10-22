# راهنمای راه‌اندازی (فارسی) — ربات کشورداری تلگرام

معماری: تلگرام (Webhook) → Render.com (رایگان) → MongoDB Atlas (رایگان M0)
موتور زمان بازی: cron-job.com هر ۱ دقیقه `/tick` را صدا می‌زند (هم رندر را بیدار نگه می‌دارد، هم شارژ اکتشاف، تحقیق، جنگ و اقتصاد روزانه را جلو می‌برد).
بازی کاملاً متنی است؛ هیچ نقشه/تصویری ندارد.

## قدم ۱ — ساخت ربات در BotFather
1. در تلگرام به @BotFather برو → `/newbot` → یک اسم و یک یوزرنیم (تمام‌شونده با bot) بده.
2. توکن را کپی کن و نگه دار (BOT_TOKEN). این توکن را در چت عمومی نفرست.

## قدم ۲ — MongoDB Atlas رایگان
1. در mongodb.com/atlas ثبت‌نام کن → Build a Database → **M0 FREE** را انتخاب کن.
2. یک یوزر دیتابیس بساز (Database Access) و در Network Access گزینه `0.0.0.0/0` (Allow from anywhere) را اضافه کن — چون IP رندر ثابت نیست.
3. از Connect → Drivers رشته اتصال (Connection String) را کپی کن و یوزر/پسورد خودت را داخلش بگذار → این می‌شود MONGODB_URI.

## قدم ۳ — آپلود کد در گیت‌هاب
1. یک ریپوی جدید بساز و محتویات همین پوشه `bot/` را داخلش آپلود کن (main.py, logic.py, db.py, game_data.py, requirements.txt, render.yaml).

## قدم ۴ — Render.com
1. در render.com ثبت‌نام کن → New → **Blueprint** → ریپوی گیت‌هابت را وصل کن (render.yaml خودش سرویس را می‌سازد).
   یا دستی: New → Web Service → همان ریپو → Build: `pip install -r requirements.txt` و Start: `python main.py` و پلن Free.
2. در Environment این متغیرها را بگذار:
   - `BOT_TOKEN` = توکن قدم ۱
   - `MONGODB_URI` = رشته اتصال قدم ۲
   - `MONGODB_DB` = country_game
   - `TICK_SECRET` = یک رمز تصادفی طولانی (خودت بساز، نگهش دار)
   - `ADMIN_ID` = آیدی عددی تلگرامت (از @userinfobot بگیر)
3. Deploy کن. آدرس سرویس می‌شود مثل: `https://country-game-bot.onrender.com`
   ربات خودش وبهوک را روی همین آدرس ست می‌کند (از RENDER_EXTERNAL_URL می‌خواند).
4. تست: در مرورگر `https://...onrender.com/health` باید `{"ok": true}` بدهد.

## قدم ۵ — cron-job.com (هر ۱ دقیقه)
1. در cron-job.com ثبت‌نام رایگان کن → Create cronjob:
   - URL: `https://country-game-bot.onrender.com/tick?secret=RAMZ-TO` (همان TICK_SECRET)
   - Schedule: **Every 1 minute**
2. ذخیره و فعال کن. از این به بعد هر دقیقه یک پینگ می‌آید؛ پاسخ باید `{"ok": true, ...}` با آمار تیک باشد.

## قدم ۶ — تست بازی
1. در پیوی ربات `/start` → سیاره، قاره، حکومت (با راهنما)، اسم انگلیسی کشور و پایتخت، ۳ شهر.
2. در گروه: ربات را اد کن؛ گروه بعد از تعامل ۳ انسان متفاوت فعال می‌شود.
3. دستورها: کشور من، اکتشاف (شارژی، ساعتی)، ساختمان‌ها، تحقیق، تجارت (بازار جهانی)، دیپلماسی (`/find اسم‌کشور`)، ارتش و جنگ (جنگ ۳ روزه)، رتبه‌بندی.

## نکات
- پلن رایگان رندر بعد از بی‌کاری می‌خوابد؛ پینگ یک‌دقیقه‌ای cron-job.com جلوی خوابیدن را می‌گیرد.
- سقف MongoDB رایگان ۵۱۲MB است؛ برای چند هزار کشور کافی است.
- ریست یک سیاره (ادمین): `/admin_reset_planet vexus`
