---
name: importieren
description: Macht aus einer fertigen index.html (z. B. mit ChatGPT oder Claude gebaut) eine funktionierende WordPress-Seite in diesem Repo, lädt sie als passwortgeschützte Vorschau hoch und prüft sie live gegen das Original. IMMER nutzen bei "/importieren", "index.html übernehmen", "meine Seite hochladen", "aus der HTML eine WordPress-Seite machen", "neue Version der index.html", oder wenn in original/ eine neue HTML-Datei liegt.
---

# index.html → WordPress

Voraussetzung: `/einrichten` ist durch (`.env` da, `check` grün), die Datei liegt in
`original/index.html`. Lies vorher den Skill `wordpress` (Fallen und Prüfprotokoll).

Maßstab: **Die WordPress-Seite sieht aus und verhält sich wie das Original.** Nicht verschönern,
nicht umtexten, ohne dass Sabine es will. Verbesserungen schlägst du am Ende vor.

## 1. Zerlegen

```bash
python3 tools/wp.py importieren original/index.html
```

Das Werkzeug verteilt das Original auf die Bausteine: CSS → `site/design.css`, Skripte →
`site/basis.js`, `<header>`/`<nav>` oben → `site/kopf.html`, `<footer>` → `site/fuss.html`, Rest →
`seiten/start/inhalt.html`. Es stellt Google Fonts auf Bunny Fonts um, holt eingebettete Bilder
(base64) und lokale Bilder nach `bilder/` und schreibt Titel und Beschreibung in `seiten/start/seite.json`.

Gibt es schon einen Import und Sabine bringt eine **neue Fassung** ihrer index.html: erst fragen, ob
seitdem hier Änderungen gemacht wurden (`git log --oneline -- site seiten`). Wenn ja, die
Unterschiede gezielt übernehmen statt mit `--ueberschreiben` alles zu ersetzen.

## 2. Hinweise abarbeiten

Die Ausgabe listet, was noch Handarbeit braucht. Typisch:

| Hinweis | Was tun |
|---|---|
| `FEHLER Skript … '&'` | Stelle in `site/basis.js` umschreiben: `if(a&&b)` → `if(a)if(b)`, `a&&b?x:y` → `a?(b?x:y):y`, `a&&f()` → `if(a)f()`. `a||b` ist erlaubt. Auch Kommentare. |
| `Syntaxfehler` | in `site/basis.js` beheben (oft durch das Zerlegen getrennte Teile) |
| `Link auf 'xyz.html'` | Gibt es die Seite schon? Dann `href="seite:<slug>"`. Sonst Sabine fragen, ob sie angelegt werden soll (`/neue-seite`), bis dahin `href="#"` mit Kommentar. |
| Menü springt zu `#abschnitt` | so lassen, solange es nur eine Seite gibt. Mit Unterseiten: `seite:start#abschnitt` |
| kein Seitenkopf/-fuß gefunden | Kopf- und Fußbereich von Hand aus `inhalt.html` nach `site/kopf.html` bzw. `site/fuss.html` verschieben |
| Lokales Stylesheet/Skript | Inhalt der Datei nach `site/design.css` bzw. `site/basis.js` kopieren |
| Bild nicht gefunden | Sabine nach dem Bild fragen; Datei nach `bilder/`, Pfad `bilder/<name>` |
| Bilder von fremden Servern | herunterladen nach `bilder/` (Lizenz klären, z. B. Unsplash ok, Google-Bildersuche nicht) |
| Umschreibungen ae/oe/ue | Treffer prüfen und echte Umlaute setzen (Sabines Text sonst unverändert lassen) |
| Formular | Ziel mit Sabine/Simon klären, bis dahin sichtbar lassen und nicht abschicken |
| `<h1>` fehlt / mehrfach | genau eine Hauptüberschrift; nur nach Rückfrage ändern |
| Eingebettetes Video/Karte | mit Simon klären (Einwilligung). Bis dahin Vorschaubild mit Link |

Prüfen, bis keine `FEHLER` mehr kommen:

```bash
python3 tools/wp.py bauen start
```

## 3. Lokal vergleichen

```bash
python3 tools/wp.py server    # im Hintergrund starten. Nie python3 -m http.server: der liefert .env aus
```

Mit Playwright beide Fassungen bei 1440 × 900 und 390 × 844 öffnen:
`http://127.0.0.1:8765/original/index.html` und `http://127.0.0.1:8765/dist/start.vorschau.html`.
Die Messung aus dem Skill `wordpress` (Verifikationsprotokoll, Schritt 3) auf beiden laufen lassen:
Schrift, Größe, Farbe von Überschrift, Text, Link, Knopf müssen gleich sein, `ueberlauf` 0,
Konsole ohne Fehler, Skripte gelaufen (Menü am Handy öffnen, Animationen eingeblendet).
Die Vorschau enthält schon die WordPress-Schutzschicht, zeigt also ziemlich genau das spätere Bild.

Abweichungen beheben, bevor etwas hochgeht.

## 4. Als Vorschau hochladen

```bash
python3 tools/wp.py push start
```

Lädt die Bilder in die Mediathek, legt die Seite passwortgeschützt an (leere Seitenvorlage aus `site/config.json`)
und prüft, was WordPress gespeichert hat. Jede Zeile mit `ACHTUNG` ernst nehmen.

## 5. Live prüfen

Verifikationsprotokoll aus dem Skill `wordpress` komplett gegen den Link aus der Push-Ausgabe,
**und** dieselben Messwerte wie in Schritt 3 vergleichen. Besonders: Farben der Überschriften
(Theme oder Elementor-Kit färben mit?), Schriften geladen, alle Bilder da, Konsole fehlerfrei, Handy ohne Überlauf.

## 6. Sabine zeigen und speichern

Sabine bekommt: den Link, den Hinweis aufs Vorschau-Passwort (steht in ihrer `.env`), und in
zwei, drei Sätzen, was gleich geblieben ist und was offen ist (Links ohne Ziel, Formular, Bilder).

```bash
git add -A && git commit -m "Startseite aus Sabines index.html als Vorschau in WordPress" && git push
```

Dann fragen, wie es weitergeht: Änderungen an der Startseite, weitere Seiten (`/neue-seite`, z. B.
Impressum und Datenschutz, die für den Livegang Pflicht sind) oder später `/veroeffentlichen`.
