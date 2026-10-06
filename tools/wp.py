#!/usr/bin/env python3
"""Werkzeug für die Website von Sabine Hoeppner-Plischke: bauen, prüfen, nach WordPress schieben.

Braucht nur Python 3.9+ (Standardbibliothek). Node.js ist optional und wird für die
Syntaxprüfung der Skripte genutzt, wenn vorhanden.

Befehle (Details: python3 tools/wp.py <befehl> -h):
  check                  Verbindung, Rechte und Plugins prüfen, Vorschau-Passwort anlegen
  testseite              Wegwerf-Entwurf anlegen: übersteht <style>/<script> das Speichern?
  importieren DATEI      eine fertige index.html in die Bausteine dieses Repos zerlegen
  neu SLUG --titel T     neue Seite aus der Vorlage anlegen
  bauen [SLUG …]         Seiten bauen und prüfen (dist/), ohne WordPress zu berühren
  server                 lokaler Vorschau-Server auf 127.0.0.1:8765 (sperrt .env und .git)
  push SLUG … | --alle   bauen, Bilder hochladen, als Entwurf oder Vorschau nach WordPress
  live SLUG … --ja       Seite öffentlich schalten (ohne Passwort)
  startseite SLUG --ja   Seite als Startseite der Website festlegen
  seiten                 Seiten in WordPress und hier im Repo auflisten

Grundsatz: lokal grün heißt nicht live grün. WordPress verändert Inhalte beim Ausliefern.
Nach jedem Push die echte Seite im Browser prüfen (siehe .claude/skills/wordpress/SKILL.md).
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
SEITEN = ROOT / "seiten"
BILDER = ROOT / "bilder"
DIST = ROOT / "dist"
ENV = ROOT / ".env"
CONFIG = SITE / "config.json"
MEDIEN = BILDER / "medien.json"
WP_INFO = SITE / "wordpress-info.json"

# Manche Hoster-Firewalls blocken unbekannte User-Agents, daher ein Browser-ähnlicher.
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) sabine-website-werkzeug/1.0"
MARKER = "<!-- sr-werkzeug:{slug} -->"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
BILD_RE = re.compile(
    r"(?<![\w/.:-])(?:\.\./|\./)*bilder/([^\"'()\s<>]+?\.(?:jpe?g|png|webp|gif|avif|svg|mp4|webm|pdf|ico))",
    re.I,
)
SEITE_LINK_RE = re.compile(r"(href=[\"'])seite:([a-z0-9-]+)(#[^\"']*)?([\"'])")
SCRIPT_RE = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.S | re.I)

GRUNDKORREKTUR = """/* WordPress-Grundkorrektur: Ränder und Abstände von Theme und Block-Layout neutralisieren */
.wp-site-blocks:has(.{w}){{padding-top:0!important}}
.entry-content:has(.{w}),.wp-block-post-content:has(.{w}){{margin:0!important;padding:0!important;max-width:none!important}}
.wp-block-group:has(>.{w}){{margin:0!important;padding:0!important;max-width:none!important;width:100%}}
.wp-block-group:has(>.{w})>*{{margin-block:0!important}}
body:has(.{w}){{margin:0}}
/* Theme und Page-Builder (z. B. Elementor-Kit) färben Überschriften, Links und Knöpfe direkt ein. Im Original erben sie.
   Diese Rückstellung (Spezifität 0,1,1, steht nach dem Theme-CSS) holt den Browser-Standard zurück;
   Regeln aus design.css stehen danach und gewinnen. Abstände bleiben unberührt. */
.{w} :is(h1,h2,h3,h4,h5,h6,p,a,span,li,blockquote,figcaption,label,strong,em,small,button,input,textarea,select){{color:revert;font-family:revert;font-size:revert;font-weight:revert;font-style:revert;line-height:revert;letter-spacing:revert;text-transform:revert;text-decoration:revert}}
"""


# ---------------------------------------------------------------- Hilfen

class Abbruch(Exception):
    pass


def fail(msg: str):
    raise Abbruch(msg)


def lies_json(p: Path, default=None):
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def schreib_json(p: Path, daten):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def lies(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def env() -> dict:
    if not ENV.exists():
        fail("Keine .env gefunden. Bitte zuerst den Startassistenten ausführen (/einrichten).")
    d = {}
    for zeile in ENV.read_text(encoding="utf-8").splitlines():
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#") or "=" not in zeile:
            continue
        k, v = zeile.split("=", 1)
        d[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("WP_URL", "WP_BENUTZER", "WP_APP_PASSWORT"):
        if not d.get(k):
            fail(f"{k} fehlt in .env (Vorlage: .env.beispiel).")
    d["WP_URL"] = d["WP_URL"].rstrip("/")
    if not d["WP_URL"].startswith("https://"):
        fail("WP_URL muss mit https:// beginnen. Anwendungspasswörter funktionieren nur über HTTPS.")
    return d


def env_setzen(schluessel: str, wert: str):
    zeilen = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    neu, gefunden = [], False
    for z in zeilen:
        if z.split("=", 1)[0].strip() == schluessel:
            neu.append(f"{schluessel}={wert}")
            gefunden = True
        else:
            neu.append(z)
    if not gefunden:
        neu.append(f"{schluessel}={wert}")
    ENV.write_text("\n".join(neu) + "\n", encoding="utf-8")
    try:
        ENV.chmod(0o600)
    except OSError:
        pass


def config() -> dict:
    c = lies_json(CONFIG, {}) or {}
    c.setdefault("wrapper", "srw")
    c.setdefault("template", "")
    c.setdefault("schriften", [])
    c.setdefault("css_extern", [])
    c.setdefault("skripte_extern", [])
    c.setdefault("body_klassen", [])
    c.setdefault("html_klassen", [])
    c.setdefault("theme_ausblenden", [])
    return c


def seite_pfad(slug: str) -> Path:
    return SEITEN / slug / "seite.json"


def seite_laden(slug: str) -> dict:
    p = seite_pfad(slug)
    if not p.exists():
        fail(f"Seite '{slug}' gibt es nicht (erwartet: {p.relative_to(ROOT)}).")
    s = lies_json(p)
    s.setdefault("wp_slug", slug)
    s.setdefault("kopf", True)
    s.setdefault("fuss", True)
    return s


def alle_slugs() -> list:
    if not SEITEN.exists():
        return []
    return sorted(
        d.name for d in SEITEN.iterdir()
        if d.is_dir() and not d.name.startswith("_") and (d / "seite.json").exists()
    )


def nach_tiefe(slugs: list) -> list:
    """Eltern vor Kindern, damit die Eltern-ID beim Push schon existiert."""
    def tiefe(slug, gesehen=()):
        s = lies_json(seite_pfad(slug), {}) or {}
        e = s.get("eltern")
        if not e or e in gesehen or not seite_pfad(e).exists():
            return 0
        return 1 + tiefe(e, gesehen + (slug,))
    return sorted(slugs, key=lambda x: (tiefe(x), x))


def node_da() -> bool:
    return shutil.which("node") is not None


# ---------------------------------------------------------------- WordPress-REST

class _KeineWeiterleitung(urllib.request.HTTPRedirectHandler):
    """urllib schickt den Authorization-Header bei Weiterleitungen mit, auch an fremde Hosts oder
    über http://. Deshalb jede Weiterleitung ablehnen und die richtige Adresse melden."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        alt = urllib.parse.urlparse(req.full_url)
        neu = urllib.parse.urlparse(newurl)
        ziel = f"{neu.scheme}://{neu.netloc}"
        fail(f"WordPress leitet weiter ({code}) von {alt.scheme}://{alt.netloc} nach {ziel}. "
             f"Bitte in .env WP_URL={ziel} eintragen (muss mit https:// beginnen).")


_OPENER = urllib.request.build_opener(_KeineWeiterleitung)


class WPFehler(Exception):
    def __init__(self, status, code, msg):
        super().__init__(f"HTTP {status} {code}: {msg}")
        self.status, self.code, self.msg = status, code, msg


class WP:
    def __init__(self, e: dict):
        self.base = e["WP_URL"]
        tok = base64.b64encode(f'{e["WP_BENUTZER"]}:{e["WP_APP_PASSWORT"]}'.encode()).decode()
        self.auth = "Basic " + tok
        self.rest_route = False

    def url(self, pfad: str, query: dict | None = None) -> str:
        q = {k: v for k, v in (query or {}).items() if v is not None}
        if self.rest_route:
            q = {"rest_route": pfad, **q}
            return self.base + "/?" + urllib.parse.urlencode(q)
        u = self.base + "/wp-json" + pfad
        return u + ("?" + urllib.parse.urlencode(q) if q else "")

    def req(self, methode, pfad, json_daten=None, roh=None, header=None, query=None, auth=True):
        h = {"User-Agent": UA, "Accept": "application/json"}
        if auth:
            h["Authorization"] = self.auth
        daten = None
        if json_daten is not None:
            daten = json.dumps(json_daten).encode()
            h["Content-Type"] = "application/json"
        elif roh is not None:
            daten = roh
        h.update(header or {})
        r = urllib.request.Request(self.url(pfad, query), data=daten, headers=h, method=methode)
        try:
            with _OPENER.open(r, timeout=90) as resp:
                text = resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as ex:
            text = ex.read().decode("utf-8", "replace")
            try:
                j = json.loads(text)
                raise WPFehler(ex.code, j.get("code", "?"), j.get("message", text[:200]))
            except ValueError:
                raise WPFehler(ex.code, "kein_json", text[:200].strip())
        except urllib.error.URLError as ex:
            fail(f"WordPress nicht erreichbar ({self.base}): {ex.reason}")
        try:
            return json.loads(text)
        except ValueError:
            raise WPFehler(200, "kein_json",
                           "Antwort ist kein JSON (Firewall, Wartungsmodus oder REST-API gesperrt?): "
                           + text[:160].strip())

    def get(self, pfad, **query):
        return self.req("GET", pfad, query=query)

    def post(self, pfad, daten, **query):
        return self.req("POST", pfad, json_daten=daten, query=query)

    def delete(self, pfad, **query):
        return self.req("DELETE", pfad, query=query)

    def verbinden(self):
        """Prüft /wp-json; fällt auf ?rest_route= zurück, wenn Permalinks fehlen."""
        try:
            return self.req("GET", "/")
        except WPFehler as ex:
            if ex.status in (404, 200):
                self.rest_route = True
                return self.req("GET", "/")
            raise


def wp_verbinden() -> WP:
    wp = WP(env())
    wp.verbinden()
    return wp


# ---------------------------------------------------------------- CSS-Schutzschicht

def _teile_selektoren(s: str) -> list:
    teile, tiefe, akt = [], 0, ""
    for c in s:
        if c in "([":
            tiefe += 1
        elif c in ")]":
            tiefe -= 1
        if c == "," and tiefe == 0:
            teile.append(akt)
            akt = ""
        else:
            akt += c
    teile.append(akt)
    return [t.strip() for t in teile if t.strip()]


def _scope_selektor(sel: str, w: str) -> str:
    wc = "." + w
    if sel.startswith(wc) and (len(sel) == len(wc) or not re.match(r"[\w-]", sel[len(wc)])):
        return sel
    m = re.match(r"^(html|body|:root)(?![\w-])((?:[.#\[:][^\s>+~]*)?)(.*)$", sel, re.S | re.I)
    if m:
        basis, zusatz, rest = m.group(1).lower(), m.group(2), m.group(3)
        kopf = basis + zusatz
        rest_s = rest.strip()
        if basis in ("html", ":root"):
            if not rest_s:
                return sel  # Variablen, Schriftgröße, scroll-behavior bleiben am Dokument
            return kopf + " " + _scope_selektor(rest_s, w)
        # body
        if not rest_s:
            # Reines "body" wird zum Wrapper: Page-Builder (Elementor) setzen Schrift und Farbe per Klasse am
            # body und gewinnt sonst. Hintergründe kopiert scope_css zusätzlich auf den body.
            # "body.klasse" (per JS gesetzt) wirkt auf body und Wrapper.
            return f"{sel}, {sel} {wc}" if zusatz else wc
        if rest_s.startswith(">"):
            return f"{wc} {rest_s}" if not zusatz else f"{kopf} {wc} {rest_s}"
        return f"{kopf} {wc} {rest_s}"
    if sel == "*":
        return f"{wc}, {wc} *"
    return f"{wc} {sel}"


SCOPE_REKURSIV = {"media", "supports", "container", "layer", "document", "scope"}


def scope_css(css: str, w: str) -> str:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    aus, i, n = [], 0, len(css)
    while i < n:
        j = css.find("{", i)
        schluss = css.find("}", i)
        if j == -1 or (schluss != -1 and schluss < j):
            # Rest ohne Block (z. B. @import am Ende) oder verirrte Klammer
            if j == -1:
                aus.append(css[i:])
                break
            aus.append(css[i:schluss + 1])
            i = schluss + 1
            continue
        tiefe, k = 0, j
        while k < n:
            if css[k] == "{":
                tiefe += 1
            elif css[k] == "}":
                tiefe -= 1
                if tiefe == 0:
                    break
            k += 1
        prelude = css[i:j]
        koerper = css[j + 1:k]
        teile = prelude.split(";")
        anweisungen, kopf = teile[:-1], teile[-1].strip()
        vorspann = "".join(a.strip() + ";\n" for a in anweisungen if a.strip())
        if kopf.startswith("@"):
            name = re.match(r"@([\w-]+)", kopf)
            name = name.group(1).lower() if name else ""
            if name in SCOPE_REKURSIV:
                koerper = scope_css(koerper, w)
            neu = kopf
        else:
            selektoren = _teile_selektoren(kopf)
            neu = ", ".join(_scope_selektor(s, w) for s in selektoren)
            if any(x.lower() == "body" for x in selektoren):
                hg = re.findall(r"background(?:-color|-image)?\s*:[^;}]+", koerper)
                if hg:
                    vorspann += f"body:has(.{w}){{{';'.join(hg)}}}\n"
        aus.append(f"{vorspann}{neu}{{{koerper}}}\n")
        i = k + 1
    return "".join(aus)


# ---------------------------------------------------------------- Prüfungen

UMLAUT_RE = re.compile(r"\b[\wäöüÄÖÜß]*(?:ae|oe|ue|Ae|Oe|Ue)[\wäöüÄÖÜß]*\b")
UMLAUT_OK = re.compile(
    r"(?i)(?:[eaq]ue|uell|uen[zc]|poe|oue|ael|aero|duett|suez|blue|true|value|queue|venue|"
    r"issue|aloe|shoe|joel|noel)"
)


def umlaut_verdacht(html: str) -> list:
    text = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    funde = []
    for m in UMLAUT_RE.finditer(text):
        wort = m.group(0)
        if UMLAUT_OK.search(wort):
            continue
        funde.append(wort)
    return sorted(set(funde))


def pruefe(inner: str, modus: str) -> tuple:
    fehler, warn = [], []
    for nr, m in enumerate(SCRIPT_RE.finditer(inner), 1):
        attrs, code = m.group(1), m.group(2)
        if re.search(r"\bsrc\s*=", attrs, re.I):
            continue
        typ = re.search(r"type\s*=\s*[\"']([^\"']+)", attrs, re.I)
        typ = typ.group(1).lower() if typ else ""
        if "ld+json" in typ:
            if "&" in code:
                warn.append(f"Skript {nr} (JSON-LD) enthält '&': WordPress macht daraus &#038;.")
            continue
        if typ and typ not in ("text/javascript", "module", "application/javascript"):
            continue
        if "&" in code:
            stellen = []
            for zm in re.finditer("&", code):
                zeile = code.count("\n", 0, zm.start()) + 1
                ausschnitt = code[max(0, zm.start() - 25):zm.start() + 10].replace("\n", " ")
                stellen.append(f"      Zeile {zeile}: …{ausschnitt}…")
            fehler.append(
                f"Skript {nr}: {code.count('&')}x '&'. WordPress macht daraus '&#038;' und das Skript "
                "stirbt live. Umschreiben: if(a&&b) wird if(a)if(b), a&&b?x:y wird a?(b?x:y):y. "
                "Auch Kommentare im Skript dürfen kein '&' enthalten.\n" + "\n".join(stellen[:8]))
        if node_da():
            endung = ".mjs" if typ == "module" else ".js"
            with tempfile.NamedTemporaryFile("w", suffix=endung, delete=False, encoding="utf-8") as f:
                f.write(code)
                tmp = f.name
            r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
            Path(tmp).unlink(missing_ok=True)
            if r.returncode != 0:
                zeilen = [z for z in r.stderr.splitlines() if z.strip()]
                fehler.append(f"Skript {nr}: Syntaxfehler: {' | '.join(zeilen[:3])}")
    if not node_da():
        warn.append("Node.js fehlt: Skripte wurden nicht auf Syntaxfehler geprüft.")
    if re.search(r"fonts\.(googleapis|gstatic)\.com", inner):
        fehler.append("Google Fonts werden geladen (DSGVO-Problem). Im Link 'fonts.googleapis.com' "
                      "durch 'fonts.bunny.net' ersetzen, sonst nichts ändern.")
    for m in re.finditer(r"<iframe\b[^>]*src=[\"']([^\"']+)", inner, re.I):
        if re.search(r"youtube|youtu\.be|vimeo|google\.[a-z.]+/maps|maps\.google", m.group(1)):
            warn.append(f"Eingebettetes Video/Karte ({m.group(1)[:60]}): lädt ohne Einwilligung "
                        "Daten von Dritten. Vorschaubild mit Link oder Einwilligung über das Cookie-Plugin.")
    for m in re.finditer(r"<script\b[^>]*src=[\"']([^\"']+)", inner, re.I):
        if m.group(1).startswith("http"):
            warn.append(f"Externes Skript: {m.group(1)[:80]} (in der Datenschutzerklärung nennen).")
    h1 = len(re.findall(r"<h1\b", inner, re.I))
    if h1 == 0:
        warn.append("Keine <h1> auf der Seite (wichtig für Google und Screenreader).")
    elif h1 > 1:
        warn.append(f"{h1}x <h1> auf der Seite. Besser genau eine.")
    for m in re.finditer(r"href=[\"'](?!https?:|mailto:|tel:|#|/|seite:)([^\"']+\.html?)(#[^\"']*)?[\"']",
                         inner, re.I):
        warn.append(f"Link auf '{m.group(1)}': in WordPress gibt es keine .html-Dateien. "
                    "Stattdessen href=\"seite:<slug>\" verwenden.")
    for m in re.finditer(r"data:image/[a-z+]+;base64,([A-Za-z0-9+/=]{40000,})", inner):
        warn.append(f"Eingebettetes Bild mit {len(m.group(1)) // 1365} KB: besser als Datei nach bilder/.")
    if re.search(r"<form\b", inner, re.I):
        warn.append("Formular gefunden: ein HTML-Formular verschickt in WordPress nichts von selbst. "
                    "Ziel klären (Newsletter-Tool, Kontaktformular-Plugin).")
    if re.search(r"<(?:!doctype|html|head|body)\b", inner, re.I):
        fehler.append("<!doctype>, <html>, <head> oder <body> im Seiteninhalt: gehört nicht in WordPress.")
    ohne_code = re.sub(r"<(script|style)\b.*?</\1>", "", inner, flags=re.S | re.I)
    for m in re.finditer(r"\[([a-z_][\w-]*)(?:\s[^\]]*)?\]", ohne_code):
        if m.group(1) in ("gallery", "caption", "embed", "audio", "video", "playlist") or "_" in m.group(1):
            warn.append(f"'[{m.group(1)}…]' sieht aus wie ein WordPress-Shortcode und wird ersetzt.")
    funde = umlaut_verdacht(inner)
    if funde:
        warn.append("Mögliche Umschreibungen statt Umlaut (ae/oe/ue): " + ", ".join(funde[:15])
                    + (" …" if len(funde) > 15 else ""))
    groesse = len(inner.encode()) // 1024
    if groesse > 400:
        warn.append(f"Seite ist {groesse} KB groß. Eingebettete Bilder oder Schriften auslagern.")
    return fehler, warn


# ---------------------------------------------------------------- Bauen

def seiten_link(slug: str, modus: str, fallbacks: list) -> str:
    if modus == "vorschau":
        return f"{slug}.vorschau.html"
    p = seite_pfad(slug)
    if not p.exists():
        return ""
    s = lies_json(p)
    if s.get("link"):
        pfad = urllib.parse.urlparse(s["link"]).path or "/"
        q = urllib.parse.urlparse(s["link"]).query
        return pfad + ("?" + q if q else "")
    teile = [s.get("wp_slug") or slug]
    e = s.get("eltern")
    while e and seite_pfad(e).exists():
        es = lies_json(seite_pfad(e))
        teile.insert(0, es.get("wp_slug") or e)
        e = es.get("eltern")
    fallbacks.append(slug)
    return "/" + "/".join(teile) + "/"


def bilder_im(text: str) -> list:
    return sorted({"bilder/" + m.group(1) for m in BILD_RE.finditer(text)})


def bauen(slug: str, modus: str = "wp", medien: dict | None = None) -> dict:
    """modus 'wp' = Inhalt für WordPress, 'vorschau' = eigenständige Datei zum lokalen Ansehen."""
    cfg = config()
    w = cfg["wrapper"]
    s = seite_laden(slug)
    ordner = SEITEN / slug
    inhalt = lies(ordner / "inhalt.html").strip()
    if not inhalt:
        fail(f"seiten/{slug}/inhalt.html ist leer.")
    kopf = lies(SITE / "kopf.html").strip() if s.get("kopf", True) else ""
    fuss = lies(SITE / "fuss.html").strip() if s.get("fuss", True) else ""
    # Kein automatisches <main>: importierte Seiten bleiben 1:1 (CSS wie "body > section" muss greifen).
    # Neue Seiten bringen <main> über seiten/_vorlage/inhalt.html mit.
    koerper = "\n".join(x for x in (kopf, inhalt, fuss) if x)

    fehler, fallbacks = [], []

    def link_ersetzen(m):
        ziel = m.group(2)
        if not seite_pfad(ziel).exists():
            fehler.append(f"Link auf seite:{ziel}, aber seiten/{ziel}/ gibt es nicht.")
            return m.group(0)
        return m.group(1) + seiten_link(ziel, modus, fallbacks) + (m.group(3) or "") + m.group(4)

    koerper = SEITE_LINK_RE.sub(link_ersetzen, koerper)

    css_roh = lies(SITE / "design.css") + "\n" + lies(ordner / "seite.css")
    # Grundkorrektur auch in der lokalen Vorschau, damit sie zeigt, was WordPress zeigt
    css = GRUNDKORREKTUR.format(w=w) + scope_css(css_roh, w)
    if cfg["theme_ausblenden"] and s.get("kopf", True):
        # Ohne leere Seitenvorlage: Theme-Kopf/-Fuß ausblenden, unsere Teile ersetzen sie
        css = ", ".join(cfg["theme_ausblenden"]) + "{display:none!important}\n" + css

    starter = "document.documentElement.classList.add('js');"
    if cfg["html_klassen"]:
        starter += "document.documentElement.classList.add(" + ",".join(
            json.dumps(k) for k in cfg["html_klassen"]) + ");"
    if cfg["body_klassen"]:
        starter += "document.body.classList.add(" + ",".join(json.dumps(k) for k in cfg["body_klassen"]) + ");"
    skripte = [f"<script>{starter}</script>"]
    for sk in cfg["skripte_extern"]:
        attrs = " ".join(f'{k}="{v}"' for k, v in sk.get("attribute", {}).items())
        skripte.append(f'<script src="{sk["src"]}"{" " + attrs if attrs else ""}></script>')
    for datei in (SITE / "basis.js", ordner / "seite.js"):
        js = lies(datei).strip()
        if js:
            skripte.append(f"<script>\n{js}\n</script>")

    links = [f'<link rel="stylesheet" href="{u}">' for u in cfg["schriften"] + cfg["css_extern"]]
    inner = "\n".join([
        MARKER.format(slug=slug),
        *links,
        f"<style>\n{css.strip()}\n</style>",
        f'<div class="{w}">',
        koerper,
        "</div>",
        *skripte,
    ])

    benoetigt = bilder_im(inner)
    for b in benoetigt:
        if not (ROOT / b).exists():
            fehler.append(f"Bild fehlt: {b}")
    if modus == "vorschau":
        inner = BILD_RE.sub(lambda m: "../bilder/" + m.group(1), inner)
    elif medien is not None:
        def bild_url(m):
            e = medien.get("bilder/" + m.group(1))
            if not e:
                fehler.append(f"Bild noch nicht in der Mediathek: bilder/{m.group(1)}")
                return m.group(0)
            return e["url"]
        inner = BILD_RE.sub(bild_url, inner)

    f2, warn = pruefe(inner, modus)
    fehler += f2
    if fallbacks and modus == "wp":
        warn.append("Noch nicht in WordPress, Link vorläufig geraten: "
                    + ", ".join(sorted(set(fallbacks))) + ". Nach dem ersten Push erneut pushen.")
    return {"inner": inner, "fehler": fehler, "warn": warn, "bilder": benoetigt,
            "fallbacks": fallbacks, "seite": s}


def wp_block(inner: str) -> str:
    return ('<!-- wp:group {"align":"full","layout":{"type":"default"}} -->\n'
            '<div class="wp-block-group alignfull">\n<!-- wp:html -->\n'
            + inner + '\n<!-- /wp:html -->\n</div>\n<!-- /wp:group -->')


def vorschau_dokument(titel: str, inner: str) -> str:
    return ('<!doctype html>\n<html lang="de">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{titel} (lokale Vorschau)</title>\n</head>\n<body style="margin:0">\n'
            + inner + '\n</body>\n</html>\n')


def bericht(slug: str, erg: dict) -> bool:
    print(f"\n== {slug} ==")
    for f in erg["fehler"]:
        print(f"  FEHLER  {f}")
    for w in erg["warn"]:
        print(f"  Hinweis {w}")
    if not erg["fehler"] and not erg["warn"]:
        print("  alles sauber")
    return not erg["fehler"]


def cmd_bauen(a):
    slugs = a.slugs or alle_slugs()
    if not slugs:
        fail("Noch keine Seiten. Erst importieren oder mit 'neu' anlegen.")
    DIST.mkdir(exist_ok=True)
    ok = True
    for slug in slugs:
        wp_erg = bauen(slug, "wp")
        (DIST / f"{slug}.html").write_text(wp_block(wp_erg["inner"]), encoding="utf-8")
        v = bauen(slug, "vorschau")
        (DIST / f"{slug}.vorschau.html").write_text(
            vorschau_dokument(wp_erg["seite"].get("titel", slug), v["inner"]), encoding="utf-8")
        ok = bericht(slug, wp_erg) and ok
        print(f"  lokal ansehen: dist/{slug}.vorschau.html")
    if not ok:
        sys.exit(1)


# ---------------------------------------------------------------- Bilder

def bilder_hochladen(wp: WP, pfade: list) -> dict:
    medien = lies_json(MEDIEN, {}) or {}
    for rel in pfade:
        datei = ROOT / rel
        if not datei.exists():
            fail(f"Bild fehlt: {rel}")
        daten = datei.read_bytes()
        sha = hashlib.sha1(daten).hexdigest()
        e = medien.get(rel)
        if e and e.get("sha1") == sha:
            continue
        if datei.suffix.lower() == ".svg":
            fail(f"{rel}: SVG-Dateien lässt WordPress ohne Zusatz-Plugin nicht hochladen. "
                 "Als PNG/WebP exportieren oder den SVG-Code direkt ins HTML setzen.")
        kb = len(daten) // 1024
        if kb > 800:
            print(f"  Hinweis {rel} ist {kb} KB groß. Für schnelle Seiten unter 300 KB bleiben "
                  "(z. B. als WebP oder JPG mit 1920 px Breite).")
        typ = mimetypes.guess_type(datei.name)[0] or "application/octet-stream"
        name = re.sub(r"[^A-Za-z0-9._-]", "-", datei.name)
        res = wp.req("POST", "/wp/v2/media", roh=daten, header={
            "Content-Type": typ,
            "Content-Disposition": f'attachment; filename="{name}"',
        })
        medien[rel] = {"id": res["id"], "url": res["source_url"], "sha1": sha}
        schreib_json(MEDIEN, medien)
        print(f"  hochgeladen: {rel} -> {res['source_url']}")
    return medien


# ---------------------------------------------------------------- Push

def namespaces(wp: WP) -> list:
    info = lies_json(WP_INFO, {}) or {}
    if info.get("namespaces"):
        return info["namespaces"]
    return wp.get("/").get("namespaces", [])


def gerenderte_skripte_kaputt(rendered: str) -> list:
    kaputt = []
    for nr, m in enumerate(SCRIPT_RE.finditer(rendered), 1):
        if "src=" in m.group(1):
            continue
        if "&#038;" in m.group(2) or "&amp;" in m.group(2) or "&#8211;" in m.group(2):
            kaputt.append(nr)
    return kaputt


def push_eine(wp: WP, slug: str, a, e: dict, cfg: dict, medien: dict) -> dict:
    erg = bauen(slug, "wp", medien)
    if not bericht(slug, erg):
        fail(f"{slug}: nicht gepusht, erst die Fehler beheben.")
    s = erg["seite"]
    link_vorher = s.get("link")
    raw = wp_block(erg["inner"])
    daten = {"title": s.get("titel") or slug, "content": raw, "slug": s.get("wp_slug") or slug}
    vorlage = s.get("template") or cfg.get("template")
    if vorlage:
        daten["template"] = vorlage
    if s.get("eltern"):
        es = lies_json(seite_pfad(s["eltern"]), {}) or {}
        if not es.get("wp_id"):
            fail(f"{slug}: Elternseite '{s['eltern']}' ist noch nicht in WordPress. Zuerst diese pushen.")
        daten["parent"] = es["wp_id"]
    daten["featured_media"] = int(s.get("beitragsbild_id") or 0)

    remote = None
    if s.get("wp_id"):
        try:
            remote = wp.get(f"/wp/v2/pages/{s['wp_id']}", context="edit")
            if remote.get("status") == "trash":
                remote = None
        except WPFehler as ex:
            if ex.status != 404:
                raise
            print(f"  Hinweis Seite {s['wp_id']} gibt es in WordPress nicht mehr, lege neu an.")
    else:
        try:
            gleich = wp.get("/wp/v2/pages", slug=daten["slug"], status="any", context="edit")
        except WPFehler:
            gleich = []
        for g in gleich:
            if MARKER.format(slug=slug) in g.get("content", {}).get("raw", ""):
                remote = g
                print(f"  Hinweis Seite gab es schon (ID {g['id']}, von einem anderen Rechner gepusht), "
                      "übernehme sie.")
                break
        else:
            if gleich:
                print(f"  Hinweis In WordPress gibt es schon eine Seite mit der Adresse "
                      f"'/{daten['slug']}/' (ID {gleich[0]['id']}, alte Seite?). WordPress hängt "
                      "deshalb '-2' an. Beim Livegang tauschen (siehe /veroeffentlichen).")

    ist_live = bool(remote) and remote.get("status") == "publish" and not remote.get("password")
    if remote and s.get("wp_modified") and remote.get("modified_gmt") != s["wp_modified"] and not a.trotzdem:
        fail(f"{slug}: Die Seite wurde in WordPress seit dem letzten Push verändert "
             f"(dort {remote.get('modified_gmt')}, hier {s['wp_modified']}). Vielleicht hat jemand im "
             "WP-Admin bearbeitet oder von einem anderen Rechner gepusht (dann zuerst 'git pull'). "
             "Nur mit --trotzdem überschreiben.")
    if ist_live and not a.ja_live:
        fail(f"{slug}: Diese Seite ist öffentlich. Änderungen wären sofort für alle sichtbar. "
             "Erst bestätigen lassen, dann mit --ja-live pushen.")

    if ist_live:
        pass  # Status unverändert lassen
    elif a.entwurf:
        daten["status"] = "draft"
        daten["password"] = ""
    else:
        daten["status"] = "publish"
        daten["password"] = e.get("VORSCHAU_PASSWORT") or fail(
            "VORSCHAU_PASSWORT fehlt in .env (python3 tools/wp.py check legt eines an).")

    try:
        if remote:
            res = wp.post(f"/wp/v2/pages/{remote['id']}", daten)
        else:
            res = wp.post("/wp/v2/pages", daten)
    except WPFehler as ex:
        if "template" in ex.msg.lower() and vorlage:
            fail(f"WordPress kennt die Vorlage '{vorlage}' nicht. 'python3 tools/wp.py check' zeigt die "
                 "verfügbaren; in site/config.json bei \"template\" eintragen.")
        raise

    pid = res["id"]
    pruef = wp.get(f"/wp/v2/pages/{pid}", context="edit")
    probleme = []
    if pruef["content"]["raw"].strip() != raw.strip():
        if "<script" not in pruef["content"]["raw"] or "<style" not in pruef["content"]["raw"]:
            probleme.append("WordPress hat <style> oder <script> entfernt (Benutzer ohne Recht "
                            "'unfiltered_html'?). Mit 'python3 tools/wp.py testseite' prüfen.")
        else:
            probleme.append("Gespeicherter Inhalt weicht vom gesendeten ab (Plugin verändert Inhalte?).")
    kaputt = gerenderte_skripte_kaputt(pruef["content"].get("rendered", ""))
    if kaputt:
        probleme.append(f"Skript(e) {kaputt} werden beim Ausliefern verändert (&/– umgewandelt). "
                        "Live prüfen, ob JavaScript-Fehler auftreten.")
    if vorlage and pruef.get("template") != vorlage:
        probleme.append(f"Vorlage ist '{pruef.get('template')}' statt '{vorlage}'.")
    if pruef.get("featured_media") != daten["featured_media"]:
        wp.post(f"/wp/v2/pages/{pid}", {"featured_media": daten["featured_media"]})
        pruef = wp.get(f"/wp/v2/pages/{pid}", context="edit")
        probleme.append("WordPress hatte ein Beitragsbild gesetzt, zurückgesetzt.")

    if s.get("beschreibung") and "yoast/v1" in namespaces(wp):
        try:
            item = {"id": pid, "meta_description": s["beschreibung"]}
            if s.get("seo_titel"):
                item["seo_title"] = s["seo_titel"]
            wp.post("/yoast/v1/bulk_editor/update_search", {"items": [item]})
        except WPFehler as ex:
            probleme.append(f"Yoast-Beschreibung nicht gesetzt ({ex}). Im WP-Admin von Hand eintragen.")

    pruef = wp.get(f"/wp/v2/pages/{pid}", context="edit")
    s.update({
        "wp_id": pid,
        "link": pruef.get("link"),
        "status": ("live" if pruef["status"] == "publish" and not pruef.get("password")
                   else "vorschau" if pruef["status"] == "publish" else "entwurf"),
        "wp_modified": pruef.get("modified_gmt"),
    })
    schreib_json(seite_pfad(slug), s)
    for p in probleme:
        print(f"  ACHTUNG {p}")
    print(f"  gepusht: ID {pid}, Status {s['status']}, {s['link']}")
    if s["status"] == "vorschau":
        print("  Die Seite ist mit dem Vorschau-Passwort geschützt (steht in .env).")
    elif s["status"] == "entwurf":
        print(f"  Entwurf ansehen (eingeloggt): {wp.base}/?page_id={pid}&preview=true")
    return {"fallbacks": erg["fallbacks"], "probleme": probleme,
            "link_geaendert": link_vorher != s["link"]}


def cmd_push(a):
    e = env()
    wp = wp_verbinden()
    cfg = config()
    slugs = alle_slugs() if a.alle else a.slugs
    if not slugs:
        fail("Welche Seite? z. B. 'push start' oder 'push --alle'.")
    slugs = nach_tiefe(slugs)
    bilder = sorted({b for slug in slugs for b in bauen(slug, "wp")["bilder"]})
    medien = bilder_hochladen(wp, bilder)
    geraten, geaendert = False, []
    for slug in slugs:
        r = push_eine(wp, slug, a, e, cfg, medien)
        geraten = geraten or bool(r["fallbacks"])
        if r["link_geaendert"]:
            geaendert.append(slug)
    if geraten or geaendert:
        # Adressen stehen erst nach dem Push fest (Entwurf -> Vorschau, "-2" bei Doppelbelegung).
        print("\nZweiter Durchgang, damit alle Links auf die echten Adressen zeigen:")
        for slug in slugs:
            push_eine(wp, slug, a, e, cfg, medien)
    andere = [x for x in alle_slugs() if x not in slugs and lies_json(seite_pfad(x)).get("wp_id")]
    if geaendert and andere:
        print(f"\nAdresse geändert bei {', '.join(geaendert)}. Andere Seiten verlinken evtl. noch die alte: "
              "python3 tools/wp.py push --alle")
    info = lies_json(WP_INFO, {}) or {}
    if info.get("cache_plugins"):
        print(f"\nCache-Plugin aktiv ({', '.join(info['cache_plugins'])}): "
              "falls die Änderung nicht sichtbar ist, Cache leeren.")
    print("\nJetzt im Browser prüfen (Skill 'wordpress', Abschnitt Verifikation). "
          "Danach seiten/*/seite.json committen.")


def cmd_live(a):
    if not a.ja:
        fail("Live schalten nur mit --ja, nachdem Sabine ausdrücklich zugestimmt hat.")
    wp = wp_verbinden()
    for slug in a.slugs:
        s = seite_laden(slug)
        if not s.get("wp_id"):
            fail(f"{slug} ist noch nicht in WordPress.")
        res = wp.post(f"/wp/v2/pages/{s['wp_id']}", {"status": "publish", "password": ""})
        s.update({"status": "live", "link": res.get("link"), "wp_modified": res.get("modified_gmt")})
        schreib_json(seite_pfad(slug), s)
        print(f"{slug}: öffentlich unter {res.get('link')}")
    print("Links prüfen: python3 tools/wp.py push --alle --ja-live (baut alle Seiten mit den neuen Adressen)")


def cmd_startseite(a):
    if not a.ja:
        fail("Startseite nur mit --ja ändern, nachdem Sabine ausdrücklich zugestimmt hat.")
    wp = wp_verbinden()
    s = seite_laden(a.slug)
    if not s.get("wp_id"):
        fail(f"{a.slug} ist noch nicht in WordPress.")
    vorher = wp.get("/wp/v2/settings")
    print(f"Bisher: show_on_front={vorher.get('show_on_front')}, page_on_front={vorher.get('page_on_front')} "
          "(zum Zurückstellen notieren)")
    wp.post("/wp/v2/settings", {"show_on_front": "page", "page_on_front": s["wp_id"]})
    neu = wp.get(f"/wp/v2/pages/{s['wp_id']}", context="edit")
    s.update({"link": neu.get("link"), "wp_modified": neu.get("modified_gmt")})
    schreib_json(seite_pfad(a.slug), s)
    print(f"Startseite ist jetzt {a.slug} (ID {s['wp_id']}). Jetzt alle Seiten neu pushen, damit die Links "
          "stimmen: python3 tools/wp.py push --alle --ja-live")


# ---------------------------------------------------------------- Check und Testseite

# Seitenvorlagen ohne Theme-Kopf und -Fuß, in dieser Reihenfolge bevorzugt
LEER_VORLAGEN = ("elementor_canvas", "blank", "canvas", "template-canvas", "page-blank", "blank-page",
                 "template-blank", "page-template-blank", "no-header-footer", "page-no-header-footer")

KATEGORIEN = {
    "cache_plugins": ("cache", "rocket", "litespeed", "autoptimize", "w3-total", "sg-cachepress",
                      "breeze", "hummingbird", "wp-optimize", "swift", "nitropack", "perfmatters"),
    "sicherheit": ("wordfence", "sucuri", "ithemes", "better-wp-security", "solid", "all-in-one-wp-security",
                   "shield", "defender", "ninjafirewall"),
    "seo": ("wordpress-seo", "yoast", "seo-by-rank-math", "rank-math", "all-in-one-seo", "seopress",
            "the-seo-framework"),
    "cookie": ("complianz", "borlabs", "cookie-notice", "real-cookie-banner", "cookieyes", "wpconsent",
               "cookie-law-info", "gdpr-cookie", "usercentrics", "iubenda"),
    "baukasten": ("elementor", "divi", "beaver", "wpbakery", "js_composer", "oxygen", "bricks"),
}


def cmd_check(a):
    e = env()
    wp = WP(e)
    print(f"WordPress: {wp.base}")
    root = wp.verbinden()
    if wp.rest_route:
        print("  Hinweis /wp-json/ ist nicht erreichbar, nutze ?rest_route= (Permalinks prüfen).")
    ns = root.get("namespaces", [])
    print(f"  Website: {root.get('name')}  |  REST-API erreichbar")
    try:
        me = wp.get("/wp/v2/users/me", context="edit")
    except WPFehler as ex:
        if ex.status == 401:
            fail("Anmeldung abgelehnt. Benutzername oder Anwendungspasswort stimmt nicht, oder ein "
                 "Sicherheits-Plugin bzw. der Hoster blockt Anwendungspasswörter.")
        raise
    caps = me.get("capabilities", {})
    rollen = me.get("roles", [])
    print(f"  Angemeldet als: {me.get('name')} ({', '.join(rollen)})")
    ok_admin = "administrator" in rollen
    ok_html = bool(caps.get("unfiltered_html"))
    print(f"  {'OK ' if ok_admin else 'NEIN'} Administrator")
    print(f"  {'OK ' if ok_html else 'NEIN'} darf eigenes HTML/CSS/JS speichern (unfiltered_html)")
    if not ok_html:
        print("     Ohne dieses Recht entfernt WordPress <style> und <script>. Ursache meist: kein Admin, "
              "Multisite oder DISALLOW_UNFILTERED_HTML in wp-config.php.")

    vorlagen = {}
    try:
        schema = wp.req("OPTIONS", "/wp/v2/pages")
        enum = schema.get("schema", {}).get("properties", {}).get("template", {}).get("enum", [])
        vorlagen = {v: v for v in enum if v}
    except WPFehler:
        pass
    print(f"  Seitenvorlagen: {', '.join(vorlagen) or 'nur Standard'}")

    plugins = []
    try:
        plugins = wp.get("/wp/v2/plugins")
    except WPFehler:
        print("  Hinweis Plugin-Liste nicht lesbar (fehlende Rechte).")
    aktiv = [p for p in plugins if p.get("status") == "active"]
    gefunden = {k: [] for k in KATEGORIEN}
    for p in aktiv:
        kennung = (p.get("plugin", "") + " " + p.get("name", "")).lower()
        for k, muster in KATEGORIEN.items():
            if any(m in kennung for m in muster):
                gefunden[k].append(p.get("name"))
    try:
        theme = wp.get("/wp/v2/themes", status="active")
        theme_name = theme[0]["name"]["rendered"] if isinstance(theme[0].get("name"), dict) else theme[0].get("name")
    except (WPFehler, IndexError, KeyError):
        theme_name = "?"
    print(f"  Theme: {theme_name}")
    for k, namen in gefunden.items():
        if namen:
            print(f"  {k}: {', '.join(namen)}")

    auto_menues = []
    try:
        for menue in wp.get("/wp/v2/menus", context="edit"):
            if menue.get("auto_add"):
                auto_menues.append(menue.get("name"))
    except WPFehler:
        pass
    if auto_menues:
        print(f"  ACHTUNG Menü(s) {', '.join(auto_menues)} nehmen neue Seiten automatisch auf. Dann landen "
              "auch Vorschauseiten im Live-Menü. Im WP-Admin unter Design > Menüs den Haken "
              "'Automatisch neue Seiten hinzufügen' entfernen, bevor gepusht wird.")
    try:
        settings = wp.get("/wp/v2/settings")
    except WPFehler:
        settings = {}
    seiten = []
    seite_nr = 1
    while True:
        try:
            teil = wp.get("/wp/v2/pages", status="any", per_page=100, page=seite_nr, context="edit",
                          _fields="id,slug,status,title,template,link,parent")
        except WPFehler:
            break
        seiten += teil
        if len(teil) < 100:
            break
        seite_nr += 1
    print(f"  Seiten in WordPress: {len(seiten)} (Liste: python3 tools/wp.py seiten)")
    if settings.get("show_on_front") == "page":
        print(f"  Startseite: Seite ID {settings.get('page_on_front')}")

    info = {
        "url": wp.base, "name": root.get("name"), "namespaces": ns, "rest_route": wp.rest_route,
        "benutzer": me.get("name"), "rollen": rollen, "unfiltered_html": ok_html,
        "vorlagen": list(vorlagen), "theme": theme_name, "menues_auto_add": auto_menues,
        "plugins_aktiv": [f"{p.get('name')} {p.get('version')}" for p in aktiv],
        **gefunden,
        "startseite": {"show_on_front": settings.get("show_on_front"),
                       "page_on_front": settings.get("page_on_front")},
        "seiten": [{"id": p["id"], "slug": p["slug"], "status": p["status"],
                    "titel": p["title"]["raw"] if isinstance(p.get("title"), dict) else p.get("title"),
                    "template": p.get("template")} for p in seiten],
    }
    schreib_json(WP_INFO, info)

    cfg = config()
    if not cfg.get("template"):
        wahl = next((v for v in LEER_VORLAGEN if v in vorlagen), None) or next(
            (v for v in vorlagen if "blank" in v.lower() or "canvas" in v.lower()), None)
        if not wahl and not vorlagen and gefunden["baukasten"] and any(
                "elementor" in n.lower() for n in gefunden["baukasten"]):
            # Neuere WordPress-Versionen nennen die Vorlagen nicht mehr im Schema.
            # Elementor bringt "elementor_canvas" immer mit; testseite prüft das echt.
            wahl = "elementor_canvas"
        if wahl:
            cfg["template"] = wahl
            print(f"  Vorlage '{wahl}' gewählt: leere Seite ohne Theme-Kopf und -Fuß, "
                  "Kopf und Fuß kommen aus site/kopf.html und site/fuss.html.")
        else:
            print("  Hinweis Keine leere Seitenvorlage gefunden. Dann zeigt das Theme seinen Kopf und Fuß "
                  "über unseren Seiten. Lösung im Skill 'einrichten' (Schritt 4): Theme-Kopf/-Fuß per "
                  "\"theme_ausblenden\" in site/config.json ausblenden oder eine passende Vorlage eintragen.")
        schreib_json(CONFIG, cfg)
    if not e.get("VORSCHAU_PASSWORT"):
        pw = "-".join(secrets.token_hex(2) for _ in range(3))
        env_setzen("VORSCHAU_PASSWORT", pw)
        print("  Vorschau-Passwort angelegt (steht in .env).")
    if gefunden["cache_plugins"]:
        print("  Hinweis Cache-Plugin aktiv: nach Änderungen ggf. Cache leeren. Plugins, die JavaScript "
              "zusammenfassen oder verzögern, können Seiten-Skripte stören.")
    if not (ok_admin and ok_html):
        sys.exit(2)
    print("\nAlles bereit. Nächster Schritt: python3 tools/wp.py testseite")


def cmd_testseite(a):
    wp = wp_verbinden()
    cfg = config()
    js = "var a=1,b=2,c=3;if(a&&b){window.srTest='ok'}c--;var s='x';"
    probe = ('<!-- wp:html -->\n<style>.srt{backdrop-filter:blur(4px)}@keyframes srt{from{opacity:0}'
             'to{opacity:1}}</style>\n<div class="srt" data-x="1">Test äöü</div>\n'
             f'<script>{js}</script>\n<!-- /wp:html -->')
    daten = {"title": "Claude-Test (wird sofort gelöscht)", "content": probe, "status": "draft"}
    if cfg.get("template"):
        daten["template"] = cfg["template"]
    try:
        p = wp.post("/wp/v2/pages", daten)
    except WPFehler as ex:
        if "template" not in ex.msg.lower() or not daten.get("template"):
            raise
        print(f"  WEG Vorlage '{daten['template']}' kennt WordPress nicht. Ohne Vorlage weiter; "
              "Theme-Kopf/-Fuß dann per theme_ausblenden (Skill einrichten, Schritt 4).")
        cfg["template"] = ""
        schreib_json(CONFIG, cfg)
        daten.pop("template")
        p = wp.post("/wp/v2/pages", daten)
    pid = p["id"]
    try:
        r = wp.get(f"/wp/v2/pages/{pid}", context="edit")
        raw, rendered = r["content"]["raw"], r["content"].get("rendered", "")
        print(f"Testseite ID {pid} angelegt (Entwurf).")
        for teil in ("<style>", "<script>", "backdrop-filter", "@keyframes"):
            print(f"  {'OK ' if teil in raw else 'WEG'} {teil} übersteht das Speichern")
        print(f"  {'OK ' if raw.strip() == probe.strip() else 'ANDERS'} gespeichert = gesendet")
        m = SCRIPT_RE.search(rendered)
        if m:
            ausgeliefert = m.group(2)
            if ausgeliefert == js:
                print("  OK  Skript wird unverändert ausgeliefert")
            else:
                print(f"  ACHTUNG Skript wird beim Ausliefern verändert: {ausgeliefert!r}")
                print("     Deshalb gilt: kein '&' in Skripten (das Werkzeug prüft das).")
        else:
            print("  WEG Skript fehlt in der ausgelieferten Fassung")
        if cfg.get("template"):
            ok = r.get("template") == cfg["template"]
            print(f"  {'OK ' if ok else 'ANDERS'} Vorlage: {r.get('template') or 'Standard'}")
    finally:
        wp.delete(f"/wp/v2/pages/{pid}", force="true")
        print(f"Testseite {pid} gelöscht.")


def cmd_seiten(a):
    wp = wp_verbinden()
    lokal = {}
    for slug in alle_slugs():
        s = lies_json(seite_pfad(slug))
        if s.get("wp_id"):
            lokal[s["wp_id"]] = slug
    nr, alle = 1, []
    while True:
        teil = wp.get("/wp/v2/pages", status="any", per_page=100, page=nr, context="edit",
                      _fields="id,slug,status,title,template,link,password")
        alle += teil
        if len(teil) < 100:
            break
        nr += 1
    print(f"{'ID':>6}  {'Status':10} {'Adresse':32} {'Vorlage':22} Repo")
    for p in sorted(alle, key=lambda x: x["slug"]):
        status = p["status"] + ("+pw" if p.get("password") else "")
        print(f"{p['id']:>6}  {status:10} /{p['slug'][:30]:31} {(p.get('template') or '-')[:22]:22} "
              f"{lokal.get(p['id'], '')}")
    ohne = [s for s in alle_slugs() if not lies_json(seite_pfad(s)).get("wp_id")]
    if ohne:
        print("\nNur im Repo, noch nicht in WordPress: " + ", ".join(ohne))


# ---------------------------------------------------------------- Neu und Import

def cmd_neu(a):
    if not SLUG_RE.match(a.slug):
        fail("Adresse nur aus Kleinbuchstaben, Ziffern und Bindestrichen, z. B. 'ueber-mich'.")
    ziel = SEITEN / a.slug
    if ziel.exists():
        fail(f"seiten/{a.slug}/ gibt es schon.")
    shutil.copytree(SEITEN / "_vorlage", ziel)
    s = lies_json(ziel / "seite.json")
    s["titel"] = a.titel
    s["wp_slug"] = a.slug
    if a.eltern:
        if not seite_pfad(a.eltern).exists():
            fail(f"Elternseite '{a.eltern}' gibt es nicht.")
        s["eltern"] = a.eltern
    schreib_json(ziel / "seite.json", s)
    print(f"Angelegt: seiten/{a.slug}/ (inhalt.html befüllen, Link im Menü: href=\"seite:{a.slug}\")")


FONT_HOSTS = ("fonts.googleapis.com", "fonts.bunny.net", "use.typekit.net", "fonts.cdnfonts.com")


def _attr(tag: str, name: str) -> str:
    m = re.search(rf"\b{name}\s*=\s*([\"'])(.*?)\1", tag, re.S | re.I)
    return m.group(2) if m else ""


def _datei_name(name: str) -> str:
    stamm, punkt, endung = name.rpartition(".")
    stamm = stamm.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        stamm = stamm.replace(a, b)
    stamm = re.sub(r"[^a-z0-9]+", "-", stamm).strip("-") or "bild"
    return f"{stamm}.{endung.lower()}"


def cmd_importieren(a):
    quelle = Path(a.datei).expanduser().resolve()
    if not quelle.exists():
        fail(f"{a.datei} nicht gefunden.")
    slug = a.slug
    if not SLUG_RE.match(slug):
        fail("Ungültige Adresse für die Seite.")
    ziel = SEITEN / slug
    belegt = [p for p in (SITE / "design.css", SITE / "kopf.html", ziel / "inhalt.html") if lies(p).strip()]
    if belegt and not a.ueberschreiben:
        fail("Es gibt schon importierte Inhalte (" + ", ".join(str(p.relative_to(ROOT)) for p in belegt)
             + "). Nur mit --ueberschreiben erneut importieren.")
    html = quelle.read_text(encoding="utf-8", errors="replace")
    notizen = []

    titel = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    titel = re.sub(r"\s+", " ", titel.group(1)).strip() if titel else "Startseite"
    beschr = ""
    for m in re.finditer(r"<meta\b[^>]*>", html, re.I):
        if _attr(m.group(0), "name").lower() == "description":
            beschr = _attr(m.group(0), "content")

    cfg = config()
    cfg["schriften"], cfg["css_extern"], cfg["skripte_extern"] = [], [], []
    for m in re.finditer(r"<link\b[^>]*>", html, re.I):
        tag = m.group(0)
        rel, href = _attr(tag, "rel").lower(), _attr(tag, "href")
        if "stylesheet" not in rel or not href:
            continue
        if any(h in href for h in FONT_HOSTS):
            neu = href.replace("fonts.googleapis.com", "fonts.bunny.net")
            if neu != href:
                notizen.append("Google Fonts auf Bunny Fonts umgestellt (gleiche Schriften, DSGVO-freundlich, "
                               "in der Datenschutzerklärung nennen).")
            cfg["schriften"].append(neu.replace("&amp;", "&"))
        elif href.startswith("http"):
            cfg["css_extern"].append(href)
            notizen.append(f"Externes Stylesheet übernommen: {href}")
        else:
            notizen.append(f"Lokales Stylesheet '{href}' verlinkt: Inhalt von Hand nach site/design.css kopieren.")

    css_teile = [m.group(1) for m in re.finditer(r"<style\b[^>]*>(.*?)</style>", html, re.S | re.I)]
    css = "\n\n".join(t.strip() for t in css_teile)

    def font_import(m):
        url = m.group(2)
        if any(h in url for h in FONT_HOSTS):
            cfg["schriften"].append(url.replace("fonts.googleapis.com", "fonts.bunny.net"))
            notizen.append("@import für Schriften aus dem CSS in site/config.json verschoben.")
            return ""
        return m.group(0)
    css = re.sub(r"@import\s+url\(\s*([\"']?)([^\"')]+)\1\s*\)\s*;?", font_import, css)

    js_teile = []
    for m in SCRIPT_RE.finditer(html):
        attrs, code = m.group(1), m.group(2)
        src = _attr("<x " + attrs + ">", "src")
        typ = _attr("<x " + attrs + ">", "type").lower()
        if src:
            if src.startswith("http") or src.startswith("//"):
                weitere = {}
                for k in ("defer", "async"):
                    if re.search(rf"\b{k}\b", attrs):
                        weitere[k] = k
                cfg["skripte_extern"].append({"src": src, "attribute": weitere})
                notizen.append(f"Externes Skript übernommen: {src}")
            else:
                notizen.append(f"Lokales Skript '{src}' verlinkt: Inhalt von Hand nach site/basis.js kopieren.")
        elif "ld+json" in typ:
            notizen.append("Strukturierte Daten (JSON-LD) gefunden: übernimmt in WordPress das SEO-Plugin.")
        elif code.strip():
            js_teile.append(code.strip())
    js = "\n\n".join(js_teile)

    body_m = re.search(r"<body\b([^>]*)>(.*?)(?:</body>|$)", html, re.S | re.I)
    if body_m:
        body_attrs, body = body_m.group(1), body_m.group(2)
    else:
        body_attrs, body = "", re.sub(r"<head\b.*?</head>", "", html, flags=re.S | re.I)
    klassen = _attr("<x " + body_attrs + ">", "class").split()
    cfg["body_klassen"] = klassen
    html_tag = re.search(r"<html\b[^>]*>", html, re.I)
    html_klassen = [k for k in _attr(html_tag.group(0), "class").split() if k != "no-js"] if html_tag else []
    cfg["html_klassen"] = html_klassen
    if html_tag and re.search(r"\bno-js\b", html_tag.group(0)):
        notizen.append("<html class=\"no-js\">: das Startskript setzt stattdessen die Klasse 'js'.")
    if html_tag and re.search(r"\bdata-[\w-]+=", html_tag.group(0)):
        notizen.append("Attribute am <html>-Tag (data-…) gefunden: prüfen, ob Skripte oder CSS sie brauchen.")
    if klassen:
        notizen.append(f"Klassen am <body> ({' '.join(klassen)}) setzt künftig ein Startskript.")
    if _attr("<x " + body_attrs + ">", "style"):
        notizen.append("Inline-Stil am <body> gefunden: von Hand nach site/design.css übernehmen.")
    body = SCRIPT_RE.sub("", body)
    body = re.sub(r"<style\b[^>]*>.*?</style>", "", body, flags=re.S | re.I)
    body = re.sub(r"<link\b[^>]*>", "", body, flags=re.I)
    body = re.sub(r"</?(?:html|head|body)\b[^>]*>", "", body, flags=re.I).strip()

    BILDER.mkdir(exist_ok=True)
    zaehler = [0]

    def base64_raus(m):
        art, daten = m.group(1).lower(), m.group(2)
        if art.startswith("svg"):
            return m.group(0)
        endung = {"jpeg": "jpg"}.get(art, art)
        zaehler[0] += 1
        name = f"import-{zaehler[0]}.{endung}"
        try:
            (BILDER / name).write_bytes(base64.b64decode(re.sub(r"\s", "", daten)))
        except ValueError:
            notizen.append("Ein eingebettetes Bild ist beschädigt und wurde nicht übernommen.")
            return m.group(0)
        return f"bilder/{name}"
    muster64 = re.compile(r"data:image/([a-z+]+);base64,([A-Za-z0-9+/=\s]+)", re.I)
    body = muster64.sub(base64_raus, body)
    css = muster64.sub(base64_raus, css)
    if zaehler[0]:
        notizen.append(f"{zaehler[0]} eingebettete Bilder als Dateien nach bilder/ ausgelagert (import-N).")

    def lokale_bilder(text, ist_css=False):
        muster = (r"url\(\s*([\"']?)([^\"')]+)\1\s*\)" if ist_css
                  else r"((?:src|href|poster)=)([\"'])([^\"']+)\2")

        def ersetzen(m):
            pfad = m.group(2) if ist_css else m.group(3)
            if re.match(r"^(?:https?:|//|data:|#|mailto:|tel:|bilder/)", pfad):
                return m.group(0)
            if not re.search(r"\.(?:jpe?g|png|webp|gif|avif|svg|mp4|webm|pdf|ico)$", pfad, re.I):
                return m.group(0)
            datei = (quelle.parent / urllib.parse.unquote(pfad)).resolve()
            if quelle.parent not in datei.parents:
                notizen.append(f"Bild '{pfad}' liegt außerhalb des Ordners der index.html: nicht übernommen.")
                return m.group(0)
            if not datei.exists():
                notizen.append(f"Bild '{pfad}' nicht gefunden: Datei nach bilder/ legen und Pfad anpassen.")
                return m.group(0)
            name = _datei_name(datei.name)
            shutil.copy2(datei, BILDER / name)
            neu = f"bilder/{name}"
            return f"url({neu})" if ist_css else f"{m.group(1)}{m.group(2)}{neu}{m.group(2)}"
        return re.sub(muster, ersetzen, text, flags=re.I)
    body = lokale_bilder(body)
    css = lokale_bilder(css, ist_css=True)
    extern = sorted({m.group(1) for m in re.finditer(r"(?:src|url\()\s*=?[\"']?(https?://[^\"')\s]+"
                                                     r"\.(?:jpe?g|png|webp|gif|avif))", body + css, re.I)})
    if extern:
        notizen.append(f"{len(extern)} Bilder kommen von fremden Servern (z. B. {extern[0][:70]}). "
                       "Herunterladen und nach bilder/ legen (Lizenz klären).")

    kopf = fuss = ""
    oben = re.match(r"\s*(?:<!--.*?-->\s*)*(?:<a\b[^>]*>[^<]*</a>\s*)?(<(header|nav)\b.*?</\2>)",
                    body, re.S | re.I)
    if oben and len(re.findall(rf"<{oben.group(2)}\b", oben.group(1), re.I)) == 1:
        kopf = oben.group(1)
        body = body[:oben.start(1)] + body[oben.end(1):]
        notizen.append(f"<{oben.group(2)}> als gemeinsamer Seitenkopf nach site/kopf.html verschoben.")
    unten = re.search(r"(<footer\b.*?</footer>)\s*(?:<!--.*?-->\s*)*$", body, re.S | re.I)
    if unten and len(re.findall(r"<footer\b", unten.group(1), re.I)) == 1:
        fuss = unten.group(1)
        body = body[:unten.start(1)].rstrip()
        notizen.append("<footer> als gemeinsamer Seitenfuß nach site/fuss.html verschoben.")
    if not kopf:
        notizen.append("Kein eindeutiger Seitenkopf gefunden: Navigation von Hand nach site/kopf.html.")
    if not fuss:
        notizen.append("Kein eindeutiger Seitenfuß gefunden: Fußbereich von Hand nach site/fuss.html.")
    if re.search(r"href=[\"']#[a-z]", kopf, re.I):
        notizen.append("Menü springt zu Abschnitten (#…). Sobald es Unterseiten gibt: href=\"seite:start#…\".")

    ziel.mkdir(parents=True, exist_ok=True)
    (SITE / "design.css").write_text(f"/* übernommen aus {quelle.name} */\n{css.strip()}\n", encoding="utf-8")
    (SITE / "basis.js").write_text(js + "\n" if js else "", encoding="utf-8")
    (SITE / "kopf.html").write_text(kopf + "\n" if kopf else "", encoding="utf-8")
    (SITE / "fuss.html").write_text(fuss + "\n" if fuss else "", encoding="utf-8")
    (ziel / "inhalt.html").write_text(body.strip() + "\n", encoding="utf-8")
    s = lies_json(ziel / "seite.json") or lies_json(SEITEN / "_vorlage" / "seite.json")
    s.update({"titel": titel if slug != "start" else "Startseite", "wp_slug": s.get("wp_slug") or slug,
              "beschreibung": beschr or s.get("beschreibung", ""), "seo_titel": titel})
    schreib_json(ziel / "seite.json", s)
    schreib_json(CONFIG, cfg)

    print(f"Importiert aus {quelle.name}:")
    print(f"  site/design.css   {len(css) // 1024} KB CSS")
    print(f"  site/basis.js     {len(js_teile)} Skript-Block(e)")
    print(f"  site/kopf.html    {'ja' if kopf else 'leer'}")
    print(f"  site/fuss.html    {'ja' if fuss else 'leer'}")
    print(f"  seiten/{slug}/inhalt.html")
    for n in dict.fromkeys(notizen):
        print(f"  - {n}")
    erg = bauen(slug, "wp")
    bericht(slug, erg)
    print("\nWeiter: python3 tools/wp.py bauen " + slug + "  (dann dist/" + slug
          + ".vorschau.html mit original/ vergleichen)")


# ---------------------------------------------------------------- Lokaler Vorschau-Server

def cmd_server(a):
    """Liefert das Repo nur an diesen Rechner aus und sperrt Punktdateien (.env, .git):
    Skripte in der Vorschau (auch fremde CDN-Skripte) könnten sie sonst per fetch lesen."""
    import functools
    import http.server

    class Handler(http.server.SimpleHTTPRequestHandler):
        def send_head(self):
            pfad = urllib.parse.unquote(urllib.parse.urlparse(self.path).path)
            if any(t.startswith(".") for t in pfad.split("/") if t) or pfad.startswith("/tools"):
                self.send_error(404)
                return None
            return super().send_head()

        def log_message(self, *args):
            pass

    h = functools.partial(Handler, directory=str(ROOT))
    with http.server.ThreadingHTTPServer(("127.0.0.1", a.port), h) as srv:
        print(f"Vorschau-Server: http://127.0.0.1:{a.port}/  (Original: /original/index.html, "
              f"gebaut: /dist/<slug>.vorschau.html). Beenden mit Strg+C.")
        srv.serve_forever()


# ---------------------------------------------------------------- Einstieg

def main(argv=None):
    p = argparse.ArgumentParser(prog="wp.py", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="befehl", required=True)
    sub.add_parser("check", help="Verbindung, Rechte, Plugins prüfen").set_defaults(f=cmd_check)
    sub.add_parser("testseite", help="Wegwerf-Entwurf: übersteht eigenes HTML?").set_defaults(f=cmd_testseite)
    sub.add_parser("seiten", help="Seiten in WordPress auflisten").set_defaults(f=cmd_seiten)

    x = sub.add_parser("importieren", help="index.html zerlegen")
    x.add_argument("datei")
    x.add_argument("--slug", default="start")
    x.add_argument("--ueberschreiben", action="store_true")
    x.set_defaults(f=cmd_importieren)

    x = sub.add_parser("neu", help="neue Seite anlegen")
    x.add_argument("slug")
    x.add_argument("--titel", required=True)
    x.add_argument("--eltern")
    x.set_defaults(f=cmd_neu)

    x = sub.add_parser("server", help="lokaler Vorschau-Server (nur dieser Rechner, ohne .env)")
    x.add_argument("--port", type=int, default=8765)
    x.set_defaults(f=cmd_server)

    x = sub.add_parser("bauen", help="Seiten bauen und prüfen")
    x.add_argument("slugs", nargs="*")
    x.set_defaults(f=cmd_bauen)

    x = sub.add_parser("push", help="nach WordPress schieben (Standard: passwortgeschützte Vorschau)")
    x.add_argument("slugs", nargs="*")
    x.add_argument("--alle", action="store_true")
    x.add_argument("--entwurf", action="store_true", help="nur als Entwurf (nur eingeloggt sichtbar)")
    x.add_argument("--trotzdem", action="store_true", help="Änderungen in WordPress überschreiben")
    x.add_argument("--ja-live", action="store_true", help="öffentliche Seite direkt ändern")
    x.set_defaults(f=cmd_push)

    x = sub.add_parser("live", help="öffentlich schalten")
    x.add_argument("slugs", nargs="+")
    x.add_argument("--ja", action="store_true")
    x.set_defaults(f=cmd_live)

    x = sub.add_parser("startseite", help="als Startseite festlegen")
    x.add_argument("slug")
    x.add_argument("--ja", action="store_true")
    x.set_defaults(f=cmd_startseite)

    a = p.parse_args(argv)
    try:
        a.f(a)
    except Abbruch as ex:
        print(f"\nABBRUCH: {ex}", file=sys.stderr)
        sys.exit(1)
    except WPFehler as ex:
        print(f"\nWordPress meldet einen Fehler: {ex}", file=sys.stderr)
        if ex.status in (401, 403):
            print("Rechte oder Anmeldung prüfen (python3 tools/wp.py check).", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
