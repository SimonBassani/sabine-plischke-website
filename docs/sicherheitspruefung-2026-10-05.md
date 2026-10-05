# Sicherheitsprüfung Erststand (05.10.2026)

Differential Review (Trail of Bits) auf den ersten Stand des Repos, Basis leer (Neucode).
Umfang: alle Dateien des Erststands, Schwerpunkt `tools/wp.py`, `.claude/settings.json`, `.mcp.json`,
Anleitungen in `.claude/skills/`. Strategie: SMALL, vollständig gelesen. Geprüft durch
Claude (Opus 5.5) für DigiUp. Keine automatisierten Tests im Repo; das Werkzeug wurde stattdessen
am 05.10.2026 gegen eine echte WordPress-Installation (digi-up.at, Testseiten danach gelöscht)
und in einer Browser-Simulation mit Elementor-Kit-CSS geprüft.

## Risikoeinstufung

| Bereich | Risiko | Grund |
|---|---|---|
| Anwendungspasswort aus `.env`, Basic-Auth (`tools/wp.py`, `env`, `WP`) | HOCH | Zugangsdaten mit Admin-Rechten auf die Live-Website |
| HTTP-Aufrufe, Weiterleitungen (`WP.req`) | HOCH | externer Aufruf mit Credentials |
| Import fremder HTML-Dateien (`cmd_importieren`) | MITTEL | Dateipfade aus Eingabedatei |
| Lokaler Vorschau-Server (`cmd_server`, Skill-Anleitungen) | MITTEL | liefert Repo-Dateien aus |
| Freigaben (`.claude/settings.json`), MCP (`.mcp.json`) | MITTEL | automatische Ausführung |
| Bauen, CSS-Kapselung, Prüfungen | NIEDRIG | lokale Textverarbeitung |

## Befunde (alle vor dem ersten Commit behoben)

| # | Schwere | Ort | Befund | Behebung |
|---|---|---|---|---|
| 1 | Hoch | `tools/wp.py:188-200`, `:236` | `urllib` leitet bei 30x-Weiterleitungen den `Authorization`-Header mit weiter, auch an fremde Hosts oder über `http://`. Ein falsch eingetragenes `WP_URL` (z. B. `www.` mit Umleitung) oder eine manipulierte Weiterleitung hätte das Anwendungspasswort offengelegt. | Eigener `HTTPRedirectHandler` lehnt jede Weiterleitung ab und nennt die richtige Adresse. Live geprüft mit `https://www.digi-up.at` → Abbruch mit Hinweis. |
| 2 | Mittel | Skill-Anleitungen (vorher `python3 -m http.server`) | Ohne `--bind` lauscht der Server im ganzen WLAN und liefert `.env` aus. Auch auf 127.0.0.1 kann jedes Skript der Vorschauseite (inkl. fremder CDN-Skripte) die `.env` per `fetch('/.env')` lesen (gleicher Ursprung). | `python3 tools/wp.py server` (`:1288`): nur 127.0.0.1, sperrt jeden Pfad mit Punkt-Segment (`.env`, `.git`) und `tools/`. Geprüft: `/.env.beispiel`, `/%2eenv.beispiel`, `/.git/config` → 404. Anleitungen umgestellt, `http.server` ausdrücklich verboten. |
| 3 | Niedrig | `tools/wp.py:1222` | Import kopierte Bildpfade wie `../../x.png` aus der HTML auch von außerhalb des Quellordners ins Repo (und damit potenziell zu GitHub/Mediathek). | Nur Dateien innerhalb des Ordners der index.html. Geprüft mit Gegenbeispiel. |
| 4 | Niedrig | `tools/wp.py` (base64-Import) | Kaputte base64-Bilder brachen den Import mit Traceback ab. | `ValueError` abgefangen, Hinweis statt Abbruch. |

## Geprüft und in Ordnung

- `.env` steht in `.gitignore` (inkl. `.env.*` außer `.env.beispiel`), `git check-ignore` bestätigt.
  `env_setzen` setzt `chmod 600` (`:131`). Anleitung zum Anlegen ohne Passwort im Chat (`open -e .env`).
- `WP_URL` muss `https://` sein (`:113`), sonst Abbruch.
- `subprocess.run(["node","--check",tmp])` (`:426`): Liste, keine Shell, `--check` führt nichts aus.
- Upload-Dateiname wird auf `[A-Za-z0-9._-]` reduziert (`:640`), keine Header-Injektion.
- Live-Schaltung (`live`, `startseite`, Änderung live geschalteter Seiten) nur mit ausdrücklichem
  Schalter (`--ja`, `--ja-live`). Seit dem Ablauf „erster Durchgang“ sind die Befehle in
  `.claude/settings.json` freigegeben, damit Sabines Veröffentlichungsauftrag ohne Klick-Rückfragen
  durchläuft. Schutz ist damit die Regel in `CLAUDE.md` (nur nach Sabines Ja), nicht die Rechteabfrage.
- Schutz gegen Überschreiben fremder Änderungen in WordPress (`modified_gmt`-Vergleich), live geprüft.
- Vorschau-Passwort: 48 Bit Zufall (`secrets`, `:990`), nur für die Vorschau, nicht wiederverwenden.
- `.mcp.json`: `@playwright/mcp@0.0.80` exakt gepinnt (gleiche Version wie bei DigiUp im Einsatz).

## Restrisiken (bewusst akzeptiert)

- **`Bash(cat .env)` ist nicht technisch gesperrt**, nur `Read(./.env)`. Die Anleitungen verbieten das
  Anzeigen; Claude liest nur `VORSCHAU_PASSWORT` per `grep`. Wer die Datei sehen will, sieht sie.
- **Transitive npm-Abhängigkeiten** des Playwright-MCP sind nicht gepinnt (`npx -y`). Akzeptiert wie
  im restlichen DigiUp-Setup; bei Versionswechsel bewusst anheben.
- **Eigenes HTML/JS mit Admin-Recht `unfiltered_html`** ist Absicht (sonst keine eigenen Seiten).
  Inhalte stammen von Sabine und DigiUp. Fremde Skripte (CDN) meldet das Werkzeug als Hinweis.
- **Preview per Passwortschutz** ist kein Zugriffsschutz für vertrauliche Inhalte, nur ein Sichtschutz
  vor der Veröffentlichung.
