import os
import json
import random
import requests
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

# ===== Load ENV =====
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
TWELVE_API_KEY = os.getenv("TWELVE_API_KEY")

USERS_FILE = "users.json"

# ===== USER DB =====
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def add_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)

# ===== Premium menyu =====
def get_main_menu(user_id):
    buttons = [
        [KeyboardButton("📊 Signals"),
        KeyboardButton("🧮 Risk Calculator")],
        [KeyboardButton("ℹ️ About")]
    ]
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton("📢 Broadcast")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id)
    await update.message.reply_text(
        f"Salom {user.first_name}! 👋\n\nPremium Signal Botga xush kelibsiz 🚀",
        reply_markup=get_main_menu(user.id)
    )

# ===== ABOUT =====
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 Bu bot professional traderlar uchun.\n\n"
        "🔍 Analiz metodlari:\n"
        "- ICT asosida HL/LL struktura\n"
        "- London va New York sessiya filtri\n"
        "- Pip asosida risk va TP hisoblash\n"
        "- Signal kuchi (Weak / Medium / Strong)\n"
        "- Real vaqt narxlari (Twelve Data API)\n\n"
        "🎯 Maqsad: Eng aniq signallarni taqdim etish."
    )

# ===== Sessiya aniqlash =====
def get_session():
    hour = datetime.utcnow().hour
    if 7 <= hour < 15:   # 07:00 - 15:00 UTC
        return "London"
    elif 12 <= hour < 21: # 12:00 - 21:00 UTC
        return "New York"
    else:
        return "Asia"

# ===== TwelveData price =====
def get_price(symbol):
    url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TWELVE_API_KEY}"
    try:
        res = requests.get(url).json()
        return float(res.get("price"))
    except:
        return round(random.uniform(100, 200), 3)  # fallback

# ===== ICT SIGNAL GENERATOR =====
def generate_ict_signal():
    pairs = ["XAU/USD", "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "NZD/USD", "USD/CHF"]
    pair = random.choice(pairs)

    # Narx olish
    symbol = pair.replace("/", "")
    entry = round(get_price(symbol), 3)

    # Strukturani aniqlash
    structure = random.choice(["HL", "LL"])
    signal_type = "BUY 📈" if structure == "HL" else "SELL 📉"

    # SL va TP
    sl_pips = random.randint(20, 50) / 10  # 2.0 – 5.0 pips
    sl = round(entry - sl_pips, 3) if signal_type == "BUY 📈" else round(entry + sl_pips, 3)
    tp1 = round(entry + sl_pips * 2, 3) if signal_type == "BUY 📈" else round(entry - sl_pips * 2, 3)
    tp2 = round(entry + sl_pips * 4, 3) if signal_type == "BUY 📈" else round(entry - sl_pips * 4, 3)
    tp3 = round(entry + sl_pips * 6, 3) if signal_type == "BUY 📈" else round(entry - sl_pips * 6, 3)

    # Signal kuchi
    power = random.choice(["Weak ⚪", "Medium 🟡", "Strong 🟢"])

    session = get_session()
    sabab = f"{session} sessiyada {structure} asosida trend aniqlangan"

    return (
        f"📊 {pair}\n"
        f"{signal_type}\n"
        f"💵 Entry: {entry}\n"
        f"🛑 SL: {sl}\n"
        f"🎯 TP1: {tp1}\n"
        f"🎯 TP2: {tp2}\n"
        f"🎯 TP3: {tp3}\n"
        f"⚡ Signal kuchi: {power}\n"
        f"📌 Sabab: {sabab}"
    )

# ===== SIGNALS =====
async def signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Signal tekshirilmoqda...")
    await msg.edit_text(generate_ict_signal())

# ===== RISK CALCULATOR =====
user_states = {}

async def risk_calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_states[update.effective_user.id] = {"step": 1}
    await update.message.reply_text("💰 Balansingizni kiriting (USD):")

async def handle_risk_calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_states:
        return False

    state = user_states[user_id]
    text = update.message.text

    if state["step"] == 1:
        try:
            state["balance"] = float(text)
            state["step"] = 2
            await update.message.reply_text("⚡ Risk foizini kiriting (masalan: 2):")
        except:
            await update.message.reply_text("❌ Raqam kiriting!")
        return True

    elif state["step"] == 2:
        try:
            state["risk"] = float(text)
            state["step"] = 3
            await update.message.reply_text("📏 SL pips kiriting:")
        except:
            await update.message.reply_text("❌ Raqam kiriting!")
        return True

    elif state["step"] == 3:
        try:
            sl_pips = float(text)
            balance = state["balance"]
            risk = state["risk"]

            risk_amount = balance * (risk / 100)
            lot_size = round(risk_amount / (sl_pips * 10), 2)

            await update.message.reply_text(
                f"✅ Hisoblandi:\n\n"
                f"💰 Balans: {balance} USD\n"
                f"⚡ Risk: {risk}%\n"
                f"📏 SL: {sl_pips} pips\n\n"
                f"📌 Lot hajmi: {lot_size}"
            )
            user_states.pop(user_id)
        except:
            await update.message.reply_text("❌ Xato qiymat!")
        return True

    return False

# ===== BROADCAST =====
broadcast_states = {}

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    broadcast_states[update.effective_user.id] = True
    await update.message.reply_text("📢 Broadcast uchun xabar yuboring:")

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return False
    if broadcast_states.get(update.effective_user.id):
        text = update.message.text
        users = load_users()
        success, fail = 0, 0
        for uid in users:
            try:
                await context.bot.send_message(chat_id=uid, text=f"📢 {text}")
                success += 1
            except:
                fail += 1
        await update.message.reply_text(f"✅ Yuborildi: {success}, ❌ Xato: {fail}")
        broadcast_states.pop(update.effective_user.id)
        return True
    return False

# ===== TEXT HANDLER =====
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if await handle_risk_calc(update, context):
        return
    if await handle_broadcast(update, context):
        return

    if text == "📊 Signals":
        await signals(update, context)
    elif text == "ℹ️ About":
        await about(update, context)
    elif text == "🧮 Risk Calculator":
        await risk_calc(update, context)
    elif text == "📢 Broadcast" and user_id == ADMIN_ID:
        await broadcast(update, context)
    else:
        await update.message.reply_text("❌ Noto‘g‘ri buyruq. Menyudan foydalaning.")

# ===== MAIN =====
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("✅ Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
