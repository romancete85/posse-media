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
    from posse.auth import oauth
    from posse.auth.token_store import get_token_store

    bundle = oauth.run_authorization_code_flow()
    get_token_store().save(bundle)
    typer.echo(f"OK. person_urn={bundle.person_urn} | access expira: {bundle.access_expires_at}")


@app.command()
def refresh() -> None:
    """Refresca el access token guardado (lo usa el workflow programado)."""
    from posse.auth import oauth
    from posse.auth.token_store import get_token_store

    store = get_token_store()
    bundle = store.load()
    if bundle is None:
        raise RuntimeError("no hay tokens guardados; corre `posse auth` primero")
    nuevo = oauth.refresh(bundle)
    store.save(nuevo)
    typer.echo(f"OK. access renovado, expira: {nuevo.access_expires_at}")


@app.command()
def validate(pieza: str) -> None:
    """Valida el schema de una pieza YAML."""
    from posse import content_store

    content_store.validate(pieza)
    typer.echo(f"OK: {pieza} valida el schema.")


@app.command()
def preview(pieza: str) -> None:
    """Muestra exactamente que se publicaria. No publica nada."""
    from posse import preview as preview_mod

    typer.echo(preview_mod.render(pieza))


@app.command()
def publish(pieza: str) -> None:
    """Publica una pieza approved (idempotente)."""
    from posse import logging_conf, publisher

    logging_conf.setup()
    publisher.publish(pieza)
    typer.echo(f"OK: publish de {pieza} finalizado.")


if __name__ == "__main__":
    app()
