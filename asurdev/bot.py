"""
asurdev Sentinel — Telegram Bot
Quick commands for mobile access

Commands:
/start — Welcome message
/help — Help
/analyze <symbol> — Full analysis (BTC, ETH, SOL, etc.)
/price <symbol> — Quick price check
/astro — Current astrology for trading
/gann <symbol> — Gann Square of 9 analysis
/quality — System health and KPIs
/history — Recent analyses
"""
import os
import asyncio
import logging
from datetime import datetime
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from environment
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")


# ============================================================
# Inline Keyboards
# ============================================================

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Analyze", callback_data="cmd_analyze"),
            InlineKeyboardButton("💰 Price", callback_data="cmd_price"),
        ],
        [
            InlineKeyboardButton("🌙 Astrology", callback_data="cmd_astro"),
            InlineKeyboardButton("📐 Gann", callback_data="cmd_gann"),
        ],
        [
            InlineKeyboardButton("📈 Quality", callback_data="cmd_quality"),
            InlineKeyboardButton("📜 History", callback_data="cmd_history"),
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="cmd_settings"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_symbol_keyboard() -> InlineKeyboardMarkup:
    """Symbol selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("BTC", callback_data="sym_BTC"),
            InlineKeyboardButton("ETH", callback_data="sym_ETH"),
            InlineKeyboardButton("SOL", callback_data="sym_SOL"),
        ],
        [
            InlineKeyboardButton("BNB", callback_data="sym_BNB"),
            InlineKeyboardButton("XRP", callback_data="sym_XRP"),
            InlineKeyboardButton("ADA", callback_data="sym_ADA"),
        ],
        [
            InlineKeyboardButton("◀️ Back", callback_data="cmd_back"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# ============================================================
# Command Handlers
# ============================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message"""
    welcome = """
🔭 *asurdev Sentinel* — твой мультиагентный советник

Я анализирую криптовалюту используя:
• Technical Analysis (Market Analyst)
• Bull/Bear Research
• Western + Vedic Astrology  
• Gann (Square of 9 + Death Zones)
• Timing Solution (Cycle Agent)

*Commands:*
/analyze \<symbol\> — полный анализ
/price \<symbol\> — быстрая цена
/astro — текущая астрология
/gann \<symbol\> — Gann анализ
/quality — KPIs системы
/history — история

⚠️ Я советник-компаньон. Финальное решение — за тобой.
"""
    await update.message.reply_text(
        welcome,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help message"""
    help_text = """
🔭 *asurdev Sentinel Commands*

*Analysis:*
`/analyze BTC` — полный анализ BTC
`/analyze ETH` — полный анализ ETH
`/analyze SOL` — SOL анализ

*Quick:*
`/price BTC` — цена BTC
`/astro` — текущая астрология
`/gann BTC` — Gann Square of 9

*System:*
`/quality` — KPIs и здоровье системы
`/history` — последние 10 анализов

*Interactive:*
Просто напиши "анализируй BTC" или выбери кнопку в меню.
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Full analysis for symbol"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /analyze <symbol>\nExample: /analyze BTC",
            parse_mode="Markdown"
        )
        return
    
    symbol = context.args[0].upper()
    valid_symbols = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "DOT", "LINK"]
    
    if symbol not in valid_symbols:
        await update.message.reply_text(
            f"Unknown symbol: {symbol}\nValid: {', '.join(valid_symbols)}"
        )
        return
    
    await update.message.reply_text(f"🔍 Analyzing {symbol}...")
    
    try:
        from agents.orchestrator import Orchestrator
        orchestrator = Orchestrator()
        result = await orchestrator.analyze(symbol, action="hold")
        
        # Format response
        market = result.get("market_data", {})
        synthesis = result.get("synthesis", {})
        
        signal = synthesis.get("signal", "N/A")
        confidence = synthesis.get("confidence", 0)
        recommendation = synthesis.get("details", {}).get("recommendation", "N/A")
        
        # Signal emoji
        emoji = {"Bullish": "🟢", "Bearish": "🔴", "Neutral": "🟡"}.get(signal, "⚪")
        
        response = f"""
📊 *{symbol} Analysis*

💰 Price: ${market.get('price', 0):,.0f}
📈 24h: {market.get('change_24h', 0):.2f}%

{emoji} *Signal:* {signal} ({confidence}%)

📌 *Recommendation:*
{recommendation}

⚠️ Советник-компаньон. Решение — за тобой.
"""
        await update.message.reply_text(response, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick price check"""
    if not context.args:
        await update.message.reply_text("Usage: /price <symbol>")
        return
    
    symbol = context.args[0].upper()
    
    try:
        from tools.coingecko import get_client
        client = get_client()
        
        coin_map = {
            "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
            "BNB": "binancecoin", "XRP": "ripple", "ADA": "cardano",
            "DOGE": "dogecoin", "DOT": "polkadot", "LINK": "chainlink"
        }
        
        coin_id = coin_map.get(symbol, symbol.lower())
        data = client.get_coin_market_data(coin_id)
        
        change = data.price_change_pct
        emoji = "🟢" if change >= 0 else "🔴"
        
        response = f"""
💰 *{symbol}*

Price: ${data.current_price:,.0f}
24h: {emoji} {change:.2f}%
Volume: ${data.volume_24h/1e9:.2f}B
MCap: ${data.market_cap/1e12:.2f}T
"""
        await update.message.reply_text(response, parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def astro_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Current astrology"""
    await update.message.reply_text("🌙 Calculating astrology...")
    
    try:
        from agents.astrologer import Astrologer
        astrologer = Astrologer()
        
        result = await astrologer.analyze({
            "symbol": "BTC",
            "action": "hold",
            "datetime": datetime.now().isoformat(),
            "location": (28.6139, 77.2090)  # Delhi/NYC fallback
        })
        
        details = result.details
        choghadiya = details.get("choghadiya", {})
        
        response = f"""
🌙 *Astro for Trading*

*Moon Phase:* {details.get('moon_phase', 'N/A')}
*Illumination:* {details.get('moon_illumination', 0)}%

*Choghadiya:*
• Type: {choghadiya.get('type', 'N/A')}
• Quality: {choghadiya.get('quality', 'N/A')}
• Best for: {choghadiya.get('recommended', 'N/A')}

*Nakshatra:* {details.get('nakshatra', 'N/A')}
*Yoga:* {details.get('yoga', 'N/A')}

{result.summary}
"""
        await update.message.reply_text(response, parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def gann_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gann Square of 9 analysis"""
    if not context.args:
        await update.message.reply_text("Usage: /gann <symbol>\nExample: /gann BTC")
        return
    
    symbol = context.args[0].upper()
    
    try:
        from tools.coingecko import get_client
        from gann import get_gann_agent
        
        # Get current price
        client = get_client()
        coin_map = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana"}
        price = client.get_coin_market_data(coin_map.get(symbol, symbol.lower())).current_price
        
        # Gann analysis
        gann = get_gann_agent()
        result = gann.analyze({
            "symbol": symbol,
            "current_price": price,
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        
        details = result.details
        square9 = details.get("square9", {})
        death_zones = details.get("death_zones", {})
        
        response = f"""
📐 *Gann Analysis — {symbol}*

*Current Price:* ${price:,.0f}
*Square Level:* {square9.get('current_level', 'N/A')}

*Cardinal Cross:*
{', '.join(square9.get('cardinal_cross_levels', [])[:4])}

*Death Zones:* {len(death_zones.get('upcoming', []))} upcoming

*Signal:* {result.signal} ({result.confidence}%)
"""
        await update.message.reply_text(response, parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def quality_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """System KPIs"""
    await update.message.reply_text("📈 Loading quality metrics...")
    
    try:
        from quality.client import get_quality_db
        
        db = get_quality_db()
        
        # Get recent metrics
        recent = db.get_recent_metrics(days=7)
        
        if not recent:
            await update.message.reply_text("No quality data yet. Run some analyses first!")
            return
        
        # Calculate averages
        accuracies = [m["accuracy"] for m in recent if m.get("accuracy")]
        briers = [m["brier_score"] for m in recent if m.get("brier_score")]
        
        avg_acc = sum(accuracies) / len(accuracies) if accuracies else 0
        avg_brier = sum(briers) / len(briers) if briers else 0
        
        response = f"""
📈 *Quality KPIs (7 days)*

*Requests:* {len(recent)}
*Avg Accuracy:* {avg_acc:.1f}%
*Avg Brier Score:* {avg_brier:.3f}

*KPIs:*
• Accuracy target: >55%
• Brier target: <0.25

System status: 🟢 Healthy
"""
        await update.message.reply_text(response, parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}\n\nConfigure PostgreSQL for quality metrics.")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recent analyses"""
    try:
        from quality.client import get_quality_db
        
        db = get_quality_db()
        recent = db.get_recent_requests(limit=5)
        
        if not recent:
            await update.message.reply_text("No history yet. Run /analyze first!")
            return
        
        response = "📜 *Recent Analyses:*\n\n"
        for req in recent:
            ts = req["created_at"][:16]
            signal = req.get("final_signal", "N/A")
            symbol = req.get("symbol", "N/A")
            response += f"• {ts} | {symbol} | {signal}\n"
        
        await update.message.reply_text(response, parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


# ============================================================
# Callback Handlers
# ============================================================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button clicks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "cmd_analyze":
        await query.edit_message_text(
            "📊 Select symbol:",
            reply_markup=get_symbol_keyboard()
        )
    elif data.startswith("sym_"):
        symbol = data[4:]
        context.args = [symbol]
        await analyze_command(update, context)
    elif data == "cmd_astro":
        await astro_command(update, context)
    elif data == "cmd_gann":
        await query.edit_message_text("📐 Enter symbol: /gann BTC")
    elif data == "cmd_quality":
        await quality_command(update, context)
    elif data == "cmd_history":
        await history_command(update, context)
    elif data == "cmd_back":
        await query.edit_message_text(
            "🔭 Main Menu",
            reply_markup=get_main_keyboard()
        )


# ============================================================
# Message Handler
# ============================================================

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    text = update.message.text.lower()
    
    # Natural language processing
    if "анализ" in text or "analyze" in text:
        symbol = "BTC"
        for s in ["btc", "eth", "sol", "bnb", "xrp", "ada"]:
            if s in text:
                symbol = s.upper()
                break
        context.args = [symbol]
        await analyze_command(update, context)
    
    elif "цена" in text or "price" in text:
        symbol = "BTC"
        for s in ["btc", "eth", "sol", "bnb", "xrp", "ada"]:
            if s in text:
                symbol = s.upper()
                break
        context.args = [symbol]
        await price_command(update, context)
    
    elif "астро" in text or "astro" in text:
        await astro_command(update, context)
    
    elif "gann" in text:
        context.args = ["BTC"]
        await gann_command(update, context)
    
    else:
        await update.message.reply_text(
            "Я понимаю команды:\n/analyze BTC\n/price ETH\n/astro\n/gann BTC",
            reply_markup=get_main_keyboard()
        )


# ============================================================
# Main
# ============================================================

def main():
    """Run the bot"""
    if not BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set")
        print("Get token from @BotFather and set environment variable")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("astro", astro_command))
    app.add_handler(CommandHandler("gann", gann_command))
    app.add_handler(CommandHandler("quality", quality_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("🔭 asurdev Sentinel Bot started!")
    print("Commands: /start, /analyze, /price, /astro, /gann, /quality, /history")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
