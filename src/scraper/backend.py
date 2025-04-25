import json
import requests
from typing import List, Dict
from src.config.settings import BASE_API_URL, SPRING_BOOT_API
from src.utils.logging import setup_logging
from src.models.oferta_empleo import map_to_oferta_empleo
from src.utils.helpers import is_duplicate

logger = setup_logging()

def fetch_existing_offers() -> List[Dict]:
    """Consulta las ofertas existentes en el backend."""
    try:
        response = requests.get(f"{BASE_API_URL}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"Error HTTP al consultar ofertas existentes: {e}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de red al consultar ofertas existentes: {e}")
        return []

def send_to_backend(oferta: Dict) -> bool:
    """Envía una oferta al backend."""
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(SPRING_BOOT_API, headers=headers, json={"oferta": json.dumps(oferta)}, timeout=10)
        response.raise_for_status()
        logger.info(f"Oferta creada: {oferta['titulo']}")
        return True
    except requests.exceptions.HTTPError as e:
        logger.error(f"Error HTTP al enviar oferta '{oferta['titulo']}': {response.status_code} - {response.text}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de red al enviar oferta '{oferta['titulo']}': {e}")
        return False

def create_offer(existing_offers: List[Dict], desired_offers: int = 1) -> int:
    """Crea una oferta y la envía al backend. Devuelve el número de ofertas creadas."""
    from src.scraper.serpapi import scrape_google_jobs
    from src.config.settings import MAX_PAGES

    offers_created = 0
    page_count = 0
    next_token = None

    while offers_created < desired_offers and page_count < MAX_PAGES:
        jobs, next_token = scrape_google_jobs(next_page_token=next_token)
        if not jobs:
            logger.info(f"No hay más empleos disponibles (página {page_count}). Terminando.")
            break

        logger.info(f"Encontrados {len(jobs)} empleos en la página {page_count}")

        for job in jobs:
            if offers_created >= desired_offers:
                break

            if is_duplicate(job, existing_offers):
                logger.info(f"Oferta duplicada encontrada, omitiendo: {job.get('title')} - {job.get('company_name')}")
                continue

            oferta = map_to_oferta_empleo(job)
            logger.info(f"Enviando oferta '{oferta['titulo']}': Categoría ID = {oferta['categoria']['id']}")
            
            if send_to_backend(oferta):
                offers_created += 1
                existing_offers.append({
                    "titulo": oferta["titulo"],
                    "empresaConsultora": oferta["empresaConsultora"],
                    "fechaPublicacion": oferta["fechaPublicacion"]
                })
                logger.info(f"Ofertas creadas en esta ejecución: {offers_created}/{desired_offers}")

        page_count += 1

        if not next_token:
            logger.info("No hay más páginas de resultados disponibles.")
            break

    if offers_created < desired_offers:
        logger.warning(f"No se pudieron crear {desired_offers} ofertas nuevas. Solo se crearon {offers_created}.")
    return offers_created