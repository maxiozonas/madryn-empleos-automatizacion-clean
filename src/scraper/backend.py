import json
import requests
from typing import List, Dict
from datetime import datetime
from src.config.settings import BASE_API_URL, SPRING_BOOT_API, ARGENTINA_TZ, MAX_PAGES
from src.utils.logging import setup_logging
from src.models.oferta_empleo import map_to_oferta_empleo
from src.utils.helpers import is_duplicate, is_blacklisted_source
from src.scheduler.scheduler import get_next_scheduled_time
from src.scraper.serpapi import scrape_google_jobs

logger = setup_logging()

def fetch_existing_offers() -> List[Dict]:
    """Consulta las ofertas existentes en el backend."""
    try:
        response = requests.get(f"{BASE_API_URL}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"[API] Error HTTP al consultar ofertas existentes: {e}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"[API] Error de red al consultar ofertas existentes: {e}")
        return []

def send_to_backend(oferta: Dict) -> bool:
    """Envía una oferta al backend."""
    # Asegurarse de que fechaCierre sea null en el JSON
    if 'fechaCierre' in oferta and oferta['fechaCierre'] is None:
        # Asegurarse de que el campo fechaCierre sea explícitamente null
        pass  # Eliminado log redundante
    
    headers = {"Content-Type": "application/json"}
    try:
        # Convertir a JSON manualmente para asegurar que None se convierta a null
        oferta_json = json.dumps(oferta)
        response = requests.post(SPRING_BOOT_API, headers=headers, json={"oferta": oferta_json}, timeout=10)
        response.raise_for_status()
        logger.info(f"[API] Oferta creada: {oferta['titulo']}")
        return True
    except requests.exceptions.HTTPError as e:
        logger.error(f"[API] Error HTTP al enviar oferta '{oferta['titulo']}': {response.status_code} - {response.text}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"[API] Error de red al enviar oferta '{oferta['titulo']}': {e}")
        return False

def create_offer(existing_offers: List[Dict], desired_offers: int = 1) -> int:
    """Crea una oferta y la envía al backend. Devuelve el número de ofertas creadas."""
    offers_created = 0
    page_count = 0
    next_token = None
    # Contador para rastrear cuántas ofertas válidas encontramos en la página actual
    valid_offers_in_current_page = 0
    # Contador para rastrear cuántas páginas consecutivas sin ofertas válidas
    consecutive_pages_without_valid_offers = 0
    # Máximo de páginas consecutivas sin ofertas válidas antes de cambiar de filtro
    # Aumentado para explorar más páginas antes de cambiar de filtro
    max_consecutive_pages_without_valid_offers = 5
    
    # Lista de filtros de fecha en orden de prioridad (según las opciones reales de Google Jobs)
    # Priorizar primero "ayer" y luego "últimos 3 días" como solicitó el usuario
    date_filters = ["date_posted:yesterday", "date_posted:3days", "date_posted:week", None]
    current_filter_index = 0  # Comenzamos con "date_posted:yesterday"
    
    # Número de variantes de consulta disponibles (definido en serpapi.py)
    num_query_variants = 3  # "empleos puerto madryn", "trabajo puerto madryn", "ofertas laborales puerto madryn"

    while offers_created < desired_offers and page_count < MAX_PAGES:
        # Obtener el filtro actual
        current_filter = date_filters[current_filter_index]
        
        # Variable para rastrear la variante de consulta actual
        query_variant_attempts = 0
        current_query_variant = 0
        
        # Bucle para probar todas las variantes de consulta antes de cambiar de filtro
        while query_variant_attempts < num_query_variants:
            # Obtener empleos con el filtro actual y la variante de consulta actual
            jobs, next_token, current_query_variant = scrape_google_jobs(
                next_page_token=next_token, 
                date_filter=current_filter,
                query_variant=current_query_variant
            )
            
            # Si encontramos empleos, salir del bucle de variantes
            if jobs:
                break
                
            # Si no encontramos empleos, probar con la siguiente variante
            query_variant_attempts += 1
            current_query_variant = (current_query_variant + 1) % num_query_variants
            logger.info(f"[BUSQUEDA] Probando variante de consulta {current_query_variant+1}/{num_query_variants} para filtro '{current_filter}'")
            next_token = None  # Reiniciar token de página al cambiar de variante
        
        # Si después de probar todas las variantes no hay resultados, cambiar de filtro
        if not jobs:
            logger.info(f"[BUSQUEDA] No hay empleos con filtro '{current_filter}' en ninguna variante de consulta. Cambiando al siguiente filtro.")
            # Reiniciar el token de página y cambiar a un filtro menos restrictivo
            next_token = None
            page_count = 0
            current_filter_index = (current_filter_index + 1) % len(date_filters)
            consecutive_pages_without_valid_offers = 0
            continue

        logger.info(f"[BUSQUEDA] Encontrados {len(jobs)} empleos con filtro '{current_filter}' (página {page_count})")
        valid_offers_in_current_page = 0

        for job in jobs:
            if offers_created >= desired_offers:
                break

            # Verificar si la oferta es de una fuente no deseada
            if is_blacklisted_source(job):
                # El logging ahora se hace dentro de is_blacklisted_source
                continue

            # Verificar si la oferta ya existe
            if is_duplicate(job, existing_offers):
                logger.info(f"[FILTRO] Oferta duplicada: '{job.get('title', '')}' - {job.get('company_name', '')}")
                continue
                
            # Logging para ofertas válidas encontradas
            logger.info(f"[VÁLIDA] Oferta aceptada: '{job.get('title', '')}' - {job.get('company_name', '')}")
            
            # Mostrar el objeto completo de SerpAPI para depuración
            logger.info(f"[SERPAPI OBJETO] {json.dumps(job, indent=2, ensure_ascii=False)}")

            # Si llegamos aquí, la oferta es válida
            valid_offers_in_current_page += 1
            
            oferta = map_to_oferta_empleo(job)
            logger.info(f"[OFERTA] Procesando: '{oferta['titulo']}' (Categoría: {oferta['categoria']['id']})")
            
            if send_to_backend(oferta):
                offers_created += 1
                existing_offers.append({
                    "titulo": oferta["titulo"],
                    "empresaConsultora": oferta["empresaConsultora"],
                    "fechaPublicacion": oferta["fechaPublicacion"]
                })
                logger.info(f"[PROGRESO] Ofertas creadas: {offers_created}/{desired_offers}")
                
                # Calcular y mostrar la hora de la próxima publicación
                now = datetime.now(ARGENTINA_TZ)
                next_scheduled_time = get_next_scheduled_time(now, offers_created)
                if next_scheduled_time:
                    logger.info(f"[PROGRAMACION] Próxima publicación: {next_scheduled_time.strftime('%H:%M:%S')}")
                else:
                    logger.info("[PROGRAMACION] No hay más publicaciones programadas para hoy.")

        # Actualizar contadores para la lógica de cambio de filtro
        if valid_offers_in_current_page == 0:
            consecutive_pages_without_valid_offers += 1
        else:
            consecutive_pages_without_valid_offers = 0

        # Si hemos pasado demasiadas páginas sin ofertas válidas, cambiar de filtro
        if consecutive_pages_without_valid_offers >= max_consecutive_pages_without_valid_offers:
            logger.info(f"[BUSQUEDA] Sin ofertas válidas en {consecutive_pages_without_valid_offers} páginas con filtro '{current_filter}'. Cambiando filtro.")
            next_token = None
            page_count = 0
            current_filter_index = (current_filter_index + 1) % len(date_filters)
            consecutive_pages_without_valid_offers = 0
            continue

        page_count += 1

        # Si no hay más páginas disponibles con este filtro, cambiar al siguiente
        if not next_token:
            logger.info(f"[BUSQUEDA] Fin de resultados con filtro '{current_filter}'. Cambiando al siguiente filtro.")
            page_count = 0
            current_filter_index = (current_filter_index + 1) % len(date_filters)
            consecutive_pages_without_valid_offers = 0

    if offers_created < desired_offers:
        logger.warning(f"[RESUMEN] Se crearon {offers_created}/{desired_offers} ofertas solicitadas.")
    return offers_created