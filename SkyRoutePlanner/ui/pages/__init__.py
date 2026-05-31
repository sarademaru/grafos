"""Page module for SkyRoute Planner UI."""
from .pagina_inicio import PaginaInicio
from .pagina_planificador import PaginaPlanificador
from .pagina_viaje_dinamico import PaginaViajeDinamico
from .pagina_reportes import PaginaReportes
from .pagina_configuracion import PaginaConfiguracion

__all__ = [
    "PaginaInicio",
    "PaginaPlanificador",
    "PaginaViajeDinamico",
    "PaginaReportes",
    "PaginaConfiguracion",
]
