"""Tests del upload de imagenes (Images API) + content.media/multiImage. HTTP mockeado."""

import datetime as dt
import json

import httpx

from posse.models import Pieza
from posse.platforms.linkedin import LinkedInPublisher

CLOCK = lambda: dt.datetime(2026, 7, 23, tzinfo=dt.timezone.utc)  # noqa: E731


def _pub(handler):
    return LinkedInPublisher(
        access_token="AT",
        person_urn="urn:li:person:abc",
        version="202606",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        clock=CLOCK,
    )


def _pieza(assets):
    return Pieza.model_validate(
        {
            "id": "i",
            "pilar": "A",
            "estado": "approved",
            "destinos": ["linkedin"],
            "titulo": "t",
            "cuerpo": "c",
            "assets": assets,
        }
    )


def _handler(events, n_images):
    """Devuelve un handler que rutea initialize -> PUT -> posts, con urns image-<k>."""
    counter = {"k": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "initializeUpload" in url:
            counter["k"] += 1
            k = counter["k"]
            events.append(("init", k))
            return httpx.Response(
                200,
                json={"value": {"uploadUrl": f"https://upload.li/{k}", "image": f"urn:li:image:{k}"}},
            )
        if url.startswith("https://upload.li/"):
            events.append(("put", request.content))
            return httpx.Response(201)
        events.append(("post", json.loads(request.content)))
        return httpx.Response(201, headers={"x-restli-id": "urn:li:share:1"})

    return handler


def test_publish_una_imagen(tmp_path):
    img = tmp_path / "x.png"
    img.write_bytes(b"\x89PNGfake")
    events = []
    res = _pub(_handler(events, 1)).publish(_pieza([{"path": str(img), "alt": "una imagen"}]))

    post = next(e[1] for e in events if e[0] == "post")
    assert post["content"]["media"] == {"id": "urn:li:image:1", "altText": "una imagen"}
    assert ("put", b"\x89PNGfake") in events
    assert res.post_id == "urn:li:share:1"


def test_publish_multi_imagen(tmp_path):
    a = tmp_path / "a.png"
    a.write_bytes(b"AAA")
    b = tmp_path / "b.png"
    b.write_bytes(b"BBB")
    events = []
    _pub(_handler(events, 2)).publish(
        _pieza([{"path": str(a), "alt": "a"}, {"path": str(b)}])
    )

    post = next(e[1] for e in events if e[0] == "post")
    imgs = post["content"]["multiImage"]["images"]
    assert [i["id"] for i in imgs] == ["urn:li:image:1", "urn:li:image:2"]
    assert imgs[1]["altText"] == ""  # sin alt -> string vacio


def test_publish_sin_assets_no_lleva_content(tmp_path):
    events = []
    _pub(_handler(events, 0)).publish(_pieza([]))
    post = next(e[1] for e in events if e[0] == "post")
    assert "content" not in post
    assert not any(e[0] == "init" for e in events)
