"""CLI del pipeline (Typer). Entrypoint fino: delega en el motor.

Comandos objetivo:
    posse auth                      -> flujo OAuth de una vez; guarda tokens en el store
    posse validate <pieza.yaml>     -> valida el schema
    posse preview  <pieza.yaml>     -> muestra que se publicaria (no publica)
    posse publish  <pieza.yaml>     -> publica si esta approved (idempotente)

SCAFFOLD: comandos declarados, sin logica. Implementacion en Fase 1.
"""

from __future__ import annotations

import typer

app = typer.Typer(help="posse-pipeline — publicar contenido versionado en LinkedIn con gate humano.")


@app.command()
def auth() -> None:
    """Ejecuta el flujo OAuth (una vez) y persiste los tokens."""
    raise NotImplementedError("TODO(Fase 1): auth.oauth.run_authorization_code_flow -> token_store.save")


@app.command()
def validate(pieza: str) -> None:
    """Valida el schema de una pieza YAML."""
    raise NotImplementedError("TODO(Fase 1): content_store.validate")


@app.command()
def preview(pieza: str) -> None:
    """Muestra exactamente que se publicaria. No publica nada."""
    raise NotImplementedError("TODO(Fase 1): print(preview.render(pieza))")


@app.command()
def publish(pieza: str) -> None:
    """Publica una pieza approved (idempotente)."""
    raise NotImplementedError("TODO(Fase 1): publisher.publish(pieza)")


if __name__ == "__main__":
    app()
