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


def _settings_con_modelo(model: str | None):
    from posse.config import get_settings

    s = get_settings()
    return s.model_copy(update={"ollama_model": model, "claude_model": model}) if model else s


context_app = typer.Typer(help="Contexto de grounding (perfil, proyectos, fuentes).")
app.add_typer(context_app, name="context")


@context_app.command("github")
def context_github(
    user: str = typer.Option(None, "--user", help="Usuario GitHub (default: el autenticado en gh)"),
    visibility: str = typer.Option("public", "--visibility", help="public | private | all"),
) -> None:
    """Arma context/proyectos.md desde GitHub (default solo repos públicos)."""
    from posse import context

    path = context.build_github(user, visibility)
    typer.echo(f"OK: {path} (visibility={visibility})")
    if visibility != "public":
        typer.echo("⚠️  Incluiste repos no-públicos: revisá que no haya contenido de clientes.")


@app.command("list")
def list_piezas() -> None:
    """Muestra el backlog de piezas por estado (approved/draft/published)."""
    from posse import backlog
    from posse.config import get_settings

    typer.echo(backlog.render(get_settings().content_dir))


@app.command()
def draft(
    tema: str = typer.Argument(None, help="Tema o nota (o usá --from)"),
    from_file: str = typer.Option(None, "--from", help="Archivo de texto como fuente del tema"),
    pilar: str = typer.Option("A", "--pilar"),
    model: str = typer.Option(None, "--model", help="Override del modelo (ollama/claude)"),
    context_on: bool = typer.Option(True, "--context/--no-context", help="Usar context/ como grounding"),
) -> None:
    """Genera una pieza draft con IA a partir de un tema/nota (no publica)."""
    from pathlib import Path

    from posse import logging_conf
    from posse.generators import draft as draft_mod

    logging_conf.setup()
    if from_file:
        tema = Path(from_file).read_text(encoding="utf-8")
    if not tema:
        raise typer.BadParameter("pasá un tema como argumento o un archivo con --from")
    path = draft_mod.draft_to_file(tema, pilar, usar_contexto=context_on, settings=_settings_con_modelo(model))
    typer.echo(f"OK: pieza draft creada en {path}")


@app.command()
def repurpose(
    fuente: str,
    n: int = 3,
    pilar: str = typer.Option("A", "--pilar"),
    model: str = typer.Option(None, "--model", help="Override del modelo"),
    context_on: bool = typer.Option(True, "--context/--no-context", help="Usar context/ como grounding"),
) -> None:
    """Genera N piezas draft desde una fuente larga (archivo de texto). No publica."""
    from pathlib import Path

    from posse import logging_conf
    from posse.generators import repurpose as rep

    logging_conf.setup()
    texto = Path(fuente).read_text(encoding="utf-8")
    paths = rep.repurpose_to_files(texto, pilar, n, usar_contexto=context_on, settings=_settings_con_modelo(model))
    typer.echo(f"OK: {len(paths)} piezas draft creadas:\n  " + "\n  ".join(str(p) for p in paths))


@app.command()
def ideas(
    tema: str,
    n: int = 5,
    pilar: str = typer.Option("A", "--pilar"),
    model: str = typer.Option(None, "--model", help="Override del modelo"),
    context_on: bool = typer.Option(True, "--context/--no-context", help="Usar context/ como grounding"),
) -> None:
    """Genera N ideas de posts draft a partir de un tema (no publica)."""
    from posse import logging_conf
    from posse.generators import repurpose as rep

    logging_conf.setup()
    paths = rep.ideas_to_files(tema, pilar, n, usar_contexto=context_on, settings=_settings_con_modelo(model))
    typer.echo(f"OK: {len(paths)} ideas draft creadas:\n  " + "\n  ".join(str(p) for p in paths))


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
def publish(
    pieza: str,
    destino: list[str] = typer.Option(None, "--destino", help="Publicar solo en estos destinos (ej. --destino mastodon)"),
) -> None:
    """Publica una pieza approved en sus destinos (idempotente). --destino filtra."""
    from posse import logging_conf, publisher

    logging_conf.setup()
    publisher.publish(pieza, destinos_filtro=destino or None)
    typer.echo(f"OK: publish de {pieza} finalizado.")


@app.command("publish-due")
def publish_due(
    dry_run: bool = typer.Option(False, "--dry-run", help="Listar qué se publicaría, sin publicar"),
) -> None:
    """Publica las piezas 'approved' cuya fecha `programado` ya llegó (auto-publish; lo corre n8n/cron)."""
    from posse import logging_conf, publisher

    logging_conf.setup()
    ids = publisher.publish_due(dry_run=dry_run)
    prefijo = "[dry-run] " if dry_run else ""
    typer.echo(f"OK: {prefijo}{len(ids)} pieza(s): {', '.join(ids) or '(ninguna)'}")


@app.command("token-status")
def token_status() -> None:
    """Muestra si el token de LinkedIn sigue vigente y cuántos días le quedan (para el cron)."""
    import datetime as dt

    from posse.auth.token_store import get_token_store

    bundle = get_token_store().load()
    if bundle is None:
        typer.echo("⚠️  no hay tokens guardados; corré `posse auth`.")
        raise typer.Exit(code=1)
    expira = dt.datetime.fromisoformat(bundle.access_expires_at)
    ahora = dt.datetime.now(dt.timezone.utc)
    dias = (expira - ahora).days
    if dias < 0:
        typer.echo(f"❌ token VENCIDO ({bundle.access_expires_at}); corré `posse auth` de nuevo.")
        raise typer.Exit(code=1)
    icono = "✅" if dias > 7 else "⚠️"
    typer.echo(f"{icono} token válido, {dias} día(s) restantes (expira {bundle.access_expires_at}).")


@app.command()
def adapt(
    pieza: str,
    destino: str = typer.Argument(..., help="mastodon | twitter"),
    model: str = typer.Option(None, "--model", help="Override del modelo"),
) -> None:
    """Genera con IA la variante corta del post para otra red (Mastodon/X) y la guarda como draft."""
    from posse import logging_conf
    from posse.generators import adapt as adapt_mod

    logging_conf.setup()
    out = adapt_mod.adapt_to_file(pieza, destino, settings=_settings_con_modelo(model))
    typer.echo(f"OK: variante '{destino}' ({len(out.cuerpo)} chars) guardada en {pieza}:\n\n{out.cuerpo}")


@app.command()
def comment(pieza: str, texto: str) -> None:
    """Postea un comentario en una pieza ya publicada (ej. el link del diagrama interactivo)."""
    from posse import logging_conf, publisher

    logging_conf.setup()
    urn = publisher.comment(pieza, texto)
    typer.echo(f"OK: comentario publicado ({urn})")


@app.command()
def metrics(
    pieza: str,
    plataforma: str = typer.Argument("linkedin", help="linkedin | mastodon | twitter"),
    impresiones: int = typer.Option(None, "--impresiones"),
    reacciones: int = typer.Option(None, "--reacciones"),
    comentarios: int = typer.Option(None, "--comentarios"),
    clics: int = typer.Option(None, "--clics"),
    seguidores: int = typer.Option(None, "--seguidores"),
    fecha: str = typer.Option(None, "--fecha", help="YYYY-MM-DD del registro (default: hoy)"),
) -> None:
    """Registra a mano las métricas de una pieza (copiás los números de 'Ver analíticas')."""
    import datetime as dt

    from posse import content_store

    valores = {
        "impresiones": impresiones, "reacciones": reacciones,
        "comentarios": comentarios, "clics": clics, "seguidores": seguidores,
    }
    valores = {k: v for k, v in valores.items() if v is not None}
    if not valores:
        raise typer.BadParameter("pasá al menos una métrica (ej. --impresiones 1200 --comentarios 3)")
    content_store.set_metricas(
        pieza, plataforma, fecha=fecha or dt.date.today().isoformat(), valores=valores
    )
    typer.echo(f"OK: métricas de {plataforma} guardadas en {pieza}: {valores}")


@app.command()
def report(
    plataforma: str = typer.Argument("linkedin", help="linkedin | mastodon | twitter"),
) -> None:
    """Muestra qué piezas/pilares rinden, a partir de las métricas cargadas con `posse metrics`."""
    from posse import report as report_mod
    from posse.config import get_settings

    typer.echo(report_mod.render(get_settings().content_dir, plataforma))


@app.command("publish-approved")
def publish_approved() -> None:
    """Publica todas las piezas 'approved' del content_dir (lo usa el workflow del label)."""
    from posse import logging_conf, publisher

    logging_conf.setup()
    ids = publisher.publish_approved()
    typer.echo(f"OK: publicadas {len(ids)} pieza(s): {', '.join(ids) or '(ninguna)'}")


if __name__ == "__main__":
    app()
