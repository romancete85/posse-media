"""posse-pipeline — capa de ingenieria de un pipeline de contenido POSSE.

Motor hosting-agnostico: los modulos de dominio (models, content_store, platforms)
no saben quien los invoca. Los entrypoints (cli, workflows de Actions, futuro webhook
n8n) son finos y delegan en este paquete.
"""

__version__ = "0.1.0"
