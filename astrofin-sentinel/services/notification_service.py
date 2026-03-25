"""
Сервис уведомлений: Telegram + SMS.
"""

import httpx
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config import settings
from core.database import AlertRecord, NotificationLog

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Сервис отправки уведомлений через Telegram и SMS.
    
    Поддерживает:
    - Telegram Bot API
    - Twilio SMS API
    """
    
    # Emoji для рекомендаций
    EMOJI = {
        "buy": "🟢",
        "sell": "🔴",
        "hold": "🟡",
        "warning": "⚠️",
        "success": "✅",
        "error": "❌",
    }
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.telegram_token = settings.TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = settings.TELEGRAM_CHAT_ID
        self.twilio_sid = settings.TWILIO_ACCOUNT_SID
        self.twilio_token = settings.TWILIO_AUTH_TOKEN
        self.twilio_from = settings.TWILIO_FROM_NUMBER
        self.twilio_to = settings.TWILIO_TO_NUMBER
    
    # === Telegram ===
    
    async def send_telegram(self, alert: AlertRecord) -> dict:
        """
        Отправляет уведомление в Telegram.
        
        Returns:
            dict с результатом отправки
        """
        if not self.telegram_token or not self.telegram_token.startswith("BOT"):
            logger.warning("Telegram bot token not configured")
            return {"status": "skipped", "reason": "not_configured"}
        
        message = self._format_telegram_message(alert)
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                result = response.json()
                
                if result.get("ok"):
                    logger.info(f"[Telegram] Alert #{alert.id} sent successfully")
                    await self._log_notification(alert.id, "telegram", "sent", str(result))
                    return {"status": "sent", "message_id": result["result"]["message_id"]}
                else:
                    error = result.get("description", "Unknown error")
                    logger.error(f"[Telegram] Send failed: {error}")
                    await self._log_notification(alert.id, "telegram", "failed", str(result), error)
                    return {"status": "failed", "error": error}
                    
        except Exception as e:
            logger.error(f"[Telegram] Exception: {e}")
            await self._log_notification(alert.id, "telegram", "failed", None, str(e))
            return {"status": "error", "error": str(e)}
    
    def _format_telegram_message(self, alert: AlertRecord) -> str:
        """Форматирует сообщение для Telegram."""
        rec = alert.synthesis_result.get("recommendation", "hold") if alert.synthesis_result else "hold"
        conf = alert.synthesis_result.get("confidence", 0) if alert.synthesis_result else 0
        emoji = self.EMOJI.get(rec, "❓")
        
        # Board summary
        board = ""
        if alert.synthesis_result and "metadata" in alert.synthesis_result:
            meta = alert.synthesis_result["metadata"]
            if "board_summary" in meta:
                bs = meta["board_summary"]
                board = f"""
📊 <b>Мнения агентов:</b>
• Technical: {bs.get('technical_analyst', 'N/A')}
• Astro: {bs.get('astro_advisor', 'N/A')}
"""
        
        # Warnings
        warnings = ""
        if alert.synthesis_result and alert.synthesis_result.get("warnings"):
            warns = "\n".join([f"  {self.EMOJI['warning']} {w}" for w in alert.synthesis_result["warnings"][:3]])
            warnings = f"\n⚡️ <b>Warnings:</b>\n{warns}"
        
        # Key factors
        factors = ""
        if alert.synthesis_result and alert.synthesis_result.get("key_factors"):
            factor_list = "\n".join([f"  • {f}" for f in alert.synthesis_result["key_factors"][:3]])
            factors = f"\n📌 <b>Key Factors:</b>\n{factor_list}"
        
        return f"""
{emoji} <b>ASTROFIN SENTINEL</b> {emoji}

🔔 <b>Alert #{alert.id[:8]}</b>

📈 <b>{alert.symbol.upper()}</b> | {alert.action.upper()}
💰 Price: <code>${alert.price:,.2f}</code>
📊 Strategy: {alert.strategy}
⏱️ Timeframe: {alert.timeframe}

🎯 <b>Recommendation: {rec.upper()}</b>
📈 Confidence: {conf:.1%}

{board}
{warnings}
{factors}

⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
    
    # === SMS ===
    
    async def send_sms(self, alert: AlertRecord) -> dict:
        """
        Отправляет SMS через Twilio.
        
        Returns:
            dict с результатом отправки
        """
        if not self.twilio_sid or not self.twilio_token:
            logger.warning("Twilio credentials not configured")
            return {"status": "skipped", "reason": "not_configured"}
        
        message = self._format_sms_message(alert)
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json"
        data = {
            "From": self.twilio_from,
            "To": self.twilio_to,
            "Body": message,
        }
        auth = (self.twilio_sid, self.twilio_token)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, data=data, auth=auth)
                result = response.json()
                
                if response.status_code in (200, 201):
                    logger.info(f"[SMS] Alert #{alert.id} sent: {result.get('sid')}")
                    await self._log_notification(alert.id, "sms", "sent", result.get("sid"))
                    return {"status": "sent", "sid": result.get("sid")}
                else:
                    error = result.get("message", "Unknown error")
                    logger.error(f"[SMS] Send failed: {error}")
                    await self._log_notification(alert.id, "sms", "failed", str(result), error)
                    return {"status": "failed", "error": error}
                    
        except Exception as e:
            logger.error(f"[SMS] Exception: {e}")
            await self._log_notification(alert.id, "sms", "failed", None, str(e))
            return {"status": "error", "error": str(e)}
    
    def _format_sms_message(self, alert: AlertRecord) -> str:
        """Формирует короткое SMS-сообщение."""
        rec = alert.synthesis_result.get("recommendation", "hold") if alert.synthesis_result else "hold"
        conf = alert.synthesis_result.get("confidence", 0) if alert.synthesis_result else 0
        
        emoji = {"buy": "▲", "sell": "▼", "hold": "◆"}.get(rec, "●")
        
        return (
            f"[ASTROFIN] {alert.symbol.upper()} {alert.action.upper()} @ ${alert.price:,.0f}\n"
            f"Decision: {emoji} {rec.upper()} ({conf:.0%} conf)\n"
            f"Alert: {alert.id[:8]}"
        )
    
    # === Batch ===
    
    async def send_all(self, alert: AlertRecord) -> dict:
        """Отправляет уведомления во все каналы."""
        results = {}
        
        # Telegram
        results["telegram"] = await self.send_telegram(alert)
        
        # SMS (только для важных сигналов)
        if alert.synthesis_result:
            conf = alert.synthesis_result.get("confidence", 0)
            rec = alert.synthesis_result.get("recommendation", "hold")
            # SMS только для уверенных сигналов или критических
            if conf >= 0.75 or rec in ("buy", "sell"):
                results["sms"] = await self.send_sms(alert)
            else:
                results["sms"] = {"status": "skipped", "reason": "low_confidence"}
        
        return results
    
    # === Logging ===
    
    async def _log_notification(
        self,
        alert_id: str,
        channel: str,
        status: str,
        response: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Логирует попытку отправки в БД."""
        log = NotificationLog(
            alert_id=alert_id,
            channel=channel,
            status=status,
            response=response,
            error=error,
        )
        self.db.add(log)
        await self.db.commit()
