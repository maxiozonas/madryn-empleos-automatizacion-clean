from dotenv import load_dotenv
import os
from zoneinfo import ZoneInfo

# Cargar variables de entorno
load_dotenv("config/.env")

# Constantes de configuración
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
SPRING_BOOT_API = os.getenv("SPRING_BOOT_API") + "/automated"
BASE_API_URL = os.getenv("SPRING_BOOT_API")
USER_ID = os.getenv("USER_ID")
EMAIL_DEFAULT = os.getenv("EMAIL_DEFAULT")
DESIRED_OFFERS_PER_DAY = 5
START_HOUR = int(os.getenv("START_HOUR", 9))
START_MINUTE = int(os.getenv("START_MINUTE", 0))
END_HOUR = int(os.getenv("END_HOUR", 18))
END_MINUTE = int(os.getenv("END_MINUTE", 0))
HOURS_IN_RANGE = (END_HOUR * 60 + END_MINUTE - START_HOUR * 60 - START_MINUTE) / 60
INTERVAL_BETWEEN_OFFERS = HOURS_IN_RANGE / DESIRED_OFFERS_PER_DAY  
MAX_PAGES = 10  
DEFAULT_LOGO_URL = "https://example.com/default-logo.png"
ARGENTINA_TZ = ZoneInfo("America/Argentina/Buenos_Aires")
CHECK_INTERVAL_SECONDS = 60  
