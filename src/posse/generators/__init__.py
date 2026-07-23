"""Generación de contenido con IA — SIEMPRE upstream del gate.

Todo lo que se genera sale en estado 'draft' a content/; nunca aprueba ni publica.
El humano revisa/edita/aprueba antes de publicar (gate intacto).

- llm       : cliente Claude (texto estructurado + alt text por visión).
- draft     : tema/nota -> 1 pieza draft.
- repurpose : fuente larga -> N piezas draft.
- images    : genera imagen (Google Imagen) + alt (Claude) -> agrega a la pieza.
"""
