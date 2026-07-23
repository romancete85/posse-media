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
def draft(tema: str, pilar: str = "A") -> None:
    """Genera una pieza draft con IA a partir de un tema/nota (no publica)."""
    from posse import logging_conf
    from posse.generators import draft as draft_mod

    logging_conf.setup()
    path = draft_mod.draft_to_file(tema, pilar)
    typer.echo(f"OK: pieza draft creada en {path}")


@app.command()
def repurpose(fuente: str, n: int = 3, pilar: str = "A") -> None:
    """Genera N piezas draft desde una fuente larga (archivo de texto). No publica."""
    from pathlib import Path

    from posse import logging_conf
    from posse.generators import repurpose as rep

    logging_conf.setup()
    texto = Path(fuente).read_text(encoding="utf-8")
    paths = rep.repurpose_to_files(texto, pilar, n)
    typer.echo(f"OK: {len(paths)} piezas draft creadas:\n  " + "\n  ".join(str(p) for p in paths))


@app.command("gen-image")
def gen_image(pieza: str, prompt: str = typer.Option(None, "--prompt", help="Prompt de la imagen")) -> None:
    """Genera una imagen (Google Imagen) para una pieza y la agrega con alt text. No publica."""
    from posse import logging_conf
    from posse.generators import images

    logging_conf.setup()
    path = images.gen_image(pieza, prompt=prompt)
    typer.echo(f"OK: imagen en {path}, agregada a {pieza}")


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


@app.command("publish-approved")
def publish_approved() -> None:
    """Publica todas las piezas 'approved' del content_dir (lo usa el workflow del label)."""
    from posse import logging_conf, publisher

    logging_conf.setup()
    ids = publisher.publish_approved()
    typer.echo(f"OK: publicadas {len(ids)} pieza(s): {', '.join(ids) or '(ninguna)'}")


if __name__ == "__main__":
    app()
