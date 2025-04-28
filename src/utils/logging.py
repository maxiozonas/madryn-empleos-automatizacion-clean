import logging
import sys
import os
from datetime import datetime

def setup_logging():
    """Configura el logging para el proyecto con un formato más legible."""
    # Formato personalizado: hora (sin fecha) - nivel - mensaje
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                                  datefmt='%H:%M:%S')
    
    # Configurar el logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Eliminar handlers existentes para evitar duplicados
    for handler in root_logger.handlers[:]: 
        root_logger.removeHandler(handler)
    
    # Handler para la consola con buffer line
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Añadir el handler de consola
    root_logger.addHandler(console_handler)
    
    # Desactivar propagación para evitar logs duplicados
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).propagate = False
        logging.getLogger(name).handlers = []
    
    # Forzar flush inmediato para evitar superposición
    sys.stdout.reconfigure(line_buffering=True)
    
    return root_logger