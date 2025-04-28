from datetime import datetime, time
from typing import Optional
from src.config.settings import START_HOUR, START_MINUTE, END_HOUR, END_MINUTE, DESIRED_OFFERS_PER_DAY, INTERVAL_BETWEEN_OFFERS, ARGENTINA_TZ
from src.utils.logging import setup_logging

logger = setup_logging()

def get_next_scheduled_time(now: datetime, offers_today: int) -> Optional[datetime]:
    """Calcula el próximo horario programado para publicar una oferta."""
    if offers_today >= DESIRED_OFFERS_PER_DAY:
        return None

    today = now.date()
    scheduled_times = []
    for i in range(DESIRED_OFFERS_PER_DAY):
        minutes_since_start = i * INTERVAL_BETWEEN_OFFERS * 60
        total_minutes = (START_HOUR * 60 + START_MINUTE) + minutes_since_start
        scheduled_hour = int(total_minutes // 60)
        scheduled_minutes = int(total_minutes % 60)
        scheduled_time = datetime.combine(today, time(hour=scheduled_hour, minute=scheduled_minutes), tzinfo=ARGENTINA_TZ)
        scheduled_times.append(scheduled_time)

    for scheduled_time in scheduled_times[offers_today:]:
        time_diff = (scheduled_time - now).total_seconds() / 60
        if time_diff >= -1:
            return scheduled_time
    return None

def should_create_offer(now: datetime, last_offer_time: Optional[datetime], offers_today: int, last_scheduled_time: Optional[datetime] = None) -> bool:
    """Determina si se debe crear una oferta según el horario y las ofertas creadas."""
    current_hour = now.hour
    current_minute = now.minute
    start_total_minutes = START_HOUR * 60 + START_MINUTE
    end_total_minutes = END_HOUR * 60 + END_MINUTE
    current_total_minutes = current_hour * 60 + current_minute

    if not (start_total_minutes <= current_total_minutes < end_total_minutes):
        return False

    if offers_today >= DESIRED_OFFERS_PER_DAY:
        return False

    next_scheduled_time = get_next_scheduled_time(now, offers_today)
    if not next_scheduled_time:
        logger.info("[PROGRAMACION] No hay más horarios programados para hoy")
        return False

    if last_scheduled_time == next_scheduled_time:
        return False

    time_diff = (next_scheduled_time - now).total_seconds() / 60
    if -1 <= time_diff <= 1:
        logger.info(f"[PROGRAMACION] Ejecutando publicación programada: {next_scheduled_time.strftime('%H:%M:%S')}")
        return True

    return False