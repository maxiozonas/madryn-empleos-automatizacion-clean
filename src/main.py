import json
import sys
import os

# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from src.utils.logging import setup_logging
from src.scraper.backend import fetch_existing_offers, create_offer
from src.scheduler.scheduler import should_create_offer, get_next_scheduled_time
from src.config.settings import CHECK_INTERVAL_SECONDS, END_HOUR, END_MINUTE, DESIRED_OFFERS_PER_DAY, ARGENTINA_TZ, START_HOUR, START_MINUTE
from datetime import datetime, timedelta, time as datetime_time
import time as time_module

logger = setup_logging()

STATE_FILE = "script_state.json"

def load_state() -> dict:
    """Carga el estado persistente desde un archivo."""
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_date": None, "offers_today": 0, "last_scheduled_time": None}

def save_state(last_date, offers_today, last_scheduled_time):
    """Guarda el estado persistente en un archivo."""
    state = {
        "last_date": last_date.isoformat() if last_date else None,
        "offers_today": offers_today,
        "last_scheduled_time": last_scheduled_time.isoformat() if last_scheduled_time else None
    }
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception as e:
        logger.error(f"Error al guardar estado: {e}")

def main(test_mode: bool = False, test_5min: bool = False, test_force: bool = False):
    """Función principal para scraping y creación de ofertas de forma continua."""
    existing_offers = fetch_existing_offers()
    logger.info(f"Ofertas existentes en la base de datos: {len(existing_offers)}")
    
    state = load_state()
    last_date = datetime.fromisoformat(state["last_date"]).date() if state["last_date"] else None
    offers_today = state["offers_today"]
    last_scheduled_time = datetime.fromisoformat(state["last_scheduled_time"]) if state["last_scheduled_time"] else None
    last_log_time = None
    last_log_message = None

    while True:
        now = datetime.now(ARGENTINA_TZ)
        today = now.date()
        current_total_minutes = now.hour * 60 + now.minute
        start_total_minutes = START_HOUR * 60 + START_MINUTE
        end_total_minutes = END_HOUR * 60 + END_MINUTE

        # Reiniciar al cambiar de día
        if last_date != today:
            logger.info(f"[SISTEMA] Nuevo día detectado: {today}. Reiniciando contadores.")
            last_date = today
            last_scheduled_time = None
            existing_offers = fetch_existing_offers()
            offers_today = 0
            last_log_time = None
            last_log_message = None
            logger.info(f"[SISTEMA] Ofertas existentes en la base de datos: {len(existing_offers)}")
            save_state(last_date, offers_today, last_scheduled_time)
        else:
            offers_today = sum(1 for offer in existing_offers if datetime.fromisoformat(offer["fechaPublicacion"]).astimezone(ARGENTINA_TZ).date() == today)

        today_offers = [offer for offer in existing_offers if datetime.fromisoformat(offer["fechaPublicacion"]).astimezone(ARGENTINA_TZ).date() == today]
        last_offer_time = max((datetime.fromisoformat(offer["fechaPublicacion"]).astimezone(ARGENTINA_TZ) for offer in today_offers), default=None) if today_offers else None

        # Modo de prueba: forzar 5 publicaciones inmediatas
        if test_force:
            logger.info("[MODO PRUEBA] Forzando 5 publicaciones inmediatas")
            offers_created = create_offer(existing_offers, desired_offers=DESIRED_OFFERS_PER_DAY)
            logger.info(f"[RESUMEN] Se publicaron {offers_created}/{DESIRED_OFFERS_PER_DAY} ofertas")
            save_state(last_date, offers_today + offers_created, last_scheduled_time)
            break

        # Modo de prueba: 5 ofertas en 5 minutos
        if test_5min:
            logger.info("[MODO PRUEBA] 5 ofertas en 5 minutos")
            for i in range(DESIRED_OFFERS_PER_DAY):
                if offers_today >= DESIRED_OFFERS_PER_DAY:
                    logger.info("Se alcanzaron las 5 ofertas. Finalizando modo de prueba.")
                    break
                logger.info(f"[MODO PRUEBA] Publicando oferta {i+1}/{DESIRED_OFFERS_PER_DAY}")
                offers_created = create_offer(existing_offers)
                offers_today += offers_created
                save_state(last_date, offers_today, last_scheduled_time)
                if offers_created > 0 and i < DESIRED_OFFERS_PER_DAY - 1:
                    time_module.sleep(60)
            break

        # Modo de prueba: publicación inmediata (una oferta)
        if test_mode:
            logger.info("[MODO PRUEBA] Ignorando restricciones de horario")
            offers_created = create_offer(existing_offers)
            logger.info(f"[RESUMEN] Se publicó {offers_created} oferta")
            save_state(last_date, offers_today + offers_created, last_scheduled_time)
            break

        # Modo normal: verificar horarios programados
        if offers_today >= DESIRED_OFFERS_PER_DAY:
            if last_log_message != "offers_complete":
                next_start = datetime.combine(today + timedelta(days=1), datetime_time(hour=8, minute=50), tzinfo=ARGENTINA_TZ)
                seconds_to_next_start = (next_start - now).total_seconds()
                if seconds_to_next_start < 0:
                    next_start += timedelta(days=1)
                    seconds_to_next_start = (next_start - now).total_seconds()
                logger.info(f"[SISTEMA] Completadas todas las ofertas del día ({offers_today}). Pausando hasta {next_start.strftime('%H:%M')}")
                last_log_message = "offers_complete"
                last_log_time = now
                time_module.sleep(seconds_to_next_start)
                continue
        elif current_total_minutes < start_total_minutes:
            if last_log_time is None or (now - last_log_time).total_seconds() >= 3600:
                logger.info(f"[HORARIO] Esperando hora de inicio ({START_HOUR}:{START_MINUTE:02d})")
                last_log_time = now
                last_log_message = "before_start"
        elif current_total_minutes >= end_total_minutes:
            if last_log_time is None or (now - last_log_time).total_seconds() >= 3600:
                logger.info(f"[PROGRAMACION] Fuera de horario de publicación (límite: {END_HOUR}:{END_MINUTE:02d})")
                last_log_time = now
                last_log_message = "after_end"
        else:
            next_scheduled_time = get_next_scheduled_time(now, offers_today)
            if next_scheduled_time:
                if should_create_offer(now, last_offer_time, offers_today, last_scheduled_time):
                    offers_created = create_offer(existing_offers)
                    if offers_created > 0:
                        offers_today += offers_created
                        last_scheduled_time = next_scheduled_time
                        logger.info(f"[PROGRESO] Ofertas creadas hoy: {offers_today}/{DESIRED_OFFERS_PER_DAY}")
                        last_log_time = now
                        last_log_message = "offer_created"
                        save_state(last_date, offers_today, last_scheduled_time)

        # Esperar antes de la próxima verificación
        time_module.sleep(CHECK_INTERVAL_SECONDS)

def run_with_restart():
    """Ejecuta main con reinicio en caso de fallo."""
    max_attempts = 5
    retry_delay = 300  # 5 minutos
    attempt = 1

    while attempt <= max_attempts:
        try:
            logger.info(f"[SISTEMA] Iniciando ejecución (intento {attempt}/{max_attempts})")
            main(test_mode="--test" in sys.argv, test_5min="--test-5min" in sys.argv, test_force="--test-force" in sys.argv)
            logger.info("[SISTEMA] Ejecución completada exitosamente")
            break
        except Exception as e:
            logger.error(f"[ERROR] Error fatal: {e}. Reintentando en {retry_delay} segundos...")
            attempt += 1
            if attempt > max_attempts:
                logger.error(f"[ERROR] Se alcanzaron los {max_attempts} intentos. Deteniendo el script.")
                break
            time_module.sleep(retry_delay)

if __name__ == "__main__":
    run_with_restart()