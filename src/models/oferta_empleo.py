from datetime import datetime, timedelta
from typing import Dict
from src.config.settings import USER_ID, EMAIL_DEFAULT
from src.utils.helpers import map_category, get_logo_url, generate_link_postulacion, text_to_html

def map_to_oferta_empleo(job: Dict) -> Dict:
    """Mapea los datos de un empleo a una oferta para el backend."""
    apply_options = job.get("apply_options", [])
    via = job.get("via", "").lower()
    known_platforms = ["linkedin", "indeed", "glassdoor", "computrabajo", "bumeran", "zonajobs", "jooble", "jobted"]

    if apply_options and len(apply_options) > 0:
        forma_postulacion = "LINK"
        link_postulacion = apply_options[0].get("link")
        if link_postulacion and len(link_postulacion) > 250:
            link_postulacion = link_postulacion[:250]  # Limitar a 250 caracteres para dejar margen
        email_contacto = None
    else:
        forma_postulacion = "LINK" if any(platform in via for platform in known_platforms) else "MAIL"
        email_contacto = EMAIL_DEFAULT if forma_postulacion == "MAIL" else None
        if forma_postulacion == "LINK":
            link_postulacion = generate_link_postulacion(job)
            if link_postulacion and len(link_postulacion) > 250:
                link_postulacion = link_postulacion[:250]  # Limitar a 250 caracteres
        else:
            link_postulacion = None

    # Convertir la descripción de texto plano a HTML para el editor TipTap
    descripcion = text_to_html(job.get("description", "Sin descripción"))
    
    
    # Asegurarse de que fechaCierre sea explícitamente None para que el backend no aplique una fecha por defecto
    return {
        "titulo": job.get("title", "Sin título")[:150],
        "descripcion": descripcion,
        "usuario": {"id": USER_ID},
        "empresaConsultora": job.get("company_name", "Desconocida")[:150],
        "fechaPublicacion": datetime.now().isoformat(),
        "fechaCierre": None,  # Explícitamente None para que el backend no aplique fecha por defecto
        "formaPostulacion": forma_postulacion,
        "emailContacto": email_contacto,
        "linkPostulacion": link_postulacion,
        "categoria": {"id": map_category(job.get("title", ""), job.get("description", ""))},
        "logoUrl": get_logo_url(job),
        "habilitado": True
    }