---
name: einrichten
description: Startassistent für die Website von Sabine Hoeppner-Plischke. Führt beim allerersten Mal (oder auf einem neuen Rechner) Schritt für Schritt durch Werkzeuge, WordPress-Zugang, Prüfung und das Übernehmen der index.html. IMMER nutzen bei "/einrichten", "einrichten", "Start", "wie fange ich an", "Setup", "neuer Rechner", "Zugang einrichten", oder wenn noch keine .env existiert.
---

# Startassistent

Ziel: In etwa 15 Minuten ist Sabines Rechner mit ihrem WordPress verbunden, die Verbindung ist
geprüft und ihre `index.html` liegt im Repo. Danach geht es mit `/importieren` weiter.

Sprich in Alltagssprache (siehe `CLAUDE.md`, „Mit wem du sprichst“). Zeig am Anfang kurz den Plan:

> Wir machen fünf Schritte: 1. kurz prüfen, ob dein Rechner alles hat, 2. einen Zugangsschlüssel für
> WordPress anlegen, 3. die Verbindung testen, 4. deine index.html übernehmen, 5. alles speichern.
> Danach bauen wir daraus die neue Seite.

Arbeite die Schritte der Reihe nach ab. Was schon erledigt ist (z. B. `.env` existiert, `check` ist
grün), überspringst du mit einem Satz.

## Schritt 1: Werkzeuge auf dem Rechner

Prüfen (still, ohne Erklärung, nur Ergebnis melden):

```bash
git --version; python3 --version; node --version; git config user.name; git config user.email
```

- **git oder python3 fehlt (Mac):** `xcode-select --install` ausführen lassen. Es öffnet sich ein
  Fenster „Installieren“, ca. 5 bis 10 Minuten. Danach weiter.
- **Windows:** Python von python.org (Haken „Add to PATH“) bzw. Git von git-scm.com. Dort heißt der
  Befehl evtl. `python` statt `python3`: dann in allen Befehlen entsprechend ersetzen.
- **node fehlt:** empfohlen, nicht zwingend. Node.js LTS von nodejs.org installieren (Doppelklick,
  Weiter, Fertig). Braucht es für die Skript-Prüfung und den Browser-Test (Playwright). Danach muss
  Claude Code einmal neu gestartet werden.
- **git user.name/email leer:** Sabine nach Name und E-Mail fragen, dann nur für dieses Repo setzen:
  `git config user.name "…"` und `git config user.email "…"`.
- `git pull` ausführen, damit der neueste Stand da ist. Fragt git nach einem GitHub-Login: Sabine
  braucht ein GitHub-Konto mit Zugriff auf dieses Repo. Am einfachsten: `gh auth login` (GitHub CLI,
  Download cli.github.com), Anmeldung im Browser. Klappt das nicht, Simon Bescheid geben und
  trotzdem weitermachen (lokal arbeiten geht, hochladen später).

## Schritt 2: Zugangsschlüssel für WordPress (Anwendungspasswort)

Erklären: Ein Anwendungspasswort ist ein eigener Schlüssel nur für dieses Werkzeug. Ihr normales
Passwort bleibt geheim, und den Schlüssel kann sie jederzeit in WordPress wieder löschen.

Anleitung für Sabine (genau so ausgeben):

1. Im Browser einloggen: `<deine Website>/wp-admin` (bei WordPress.com: Meine Website → WP-Admin)
2. Links **Benutzer** → **Profil** (bzw. oben rechts auf deinen Namen → „Profil bearbeiten“).
3. Ganz nach unten scrollen zu **Anwendungspasswörter**.
4. Bei „Name des neuen Anwendungspassworts“ eintragen: `Claude Code`
5. Auf **Neues Anwendungspasswort hinzufügen** klicken.
6. Das angezeigte Passwort (vier Blöcke, z. B. `abcd efgh ijkl mnop qrst uvwx`) kopieren.
   Es wird nur einmal angezeigt.

Fehlt der Bereich „Anwendungspasswörter“:
- Ein Sicherheits-Plugin blockt ihn (häufig **Wordfence**: Wordfence → Login Security → Settings →
  Haken bei „Disable WordPress application passwords“ entfernen; bei Solid Security / iThemes ähnlich).
- Der Benutzer ist kein Administrator → mit Admin-Konto einloggen oder Simon fragen.
- Ist es unklar: Simon kontaktieren, das ist ein Fall für ihn.

Dann die Datei anlegen, **ohne dass das Passwort durch den Chat geht**:

```bash
cp -n .env.beispiel .env && chmod 600 .env && open -e .env      # Mac (TextEdit)
# Windows: copy .env.beispiel .env  und  notepad .env
```

Sabine trägt in TextEdit ein: `WP_BENUTZER=` ihren WordPress-Benutzernamen (oder die E-Mail-Adresse,
mit der sie sich einloggt) und `WP_APP_PASSWORT=` das kopierte Passwort (Leerzeichen dürfen bleiben).
`WP_URL` steht schon richtig. Speichern (⌘S), Fenster schließen, im Chat „fertig“ schreiben.

Will sie das Passwort lieber in den Chat einfügen, ist das möglich (der Schlüssel ist jederzeit
widerrufbar). Dann schreibst du es selbst in `.env` und zeigst es danach nie wieder an.

**Nie** `.env` anzeigen oder auslesen. Zum Prüfen reicht `check`.

## Schritt 3: Verbindung prüfen

```bash
python3 tools/wp.py check
```

Ergebnis in zwei, drei Sätzen übersetzen. Wichtig sind:

| Ausgabe | Bedeutung, was tun |
|---|---|
| `Anmeldung abgelehnt` | Benutzername oder Passwort vertippt → `.env` nochmal öffnen. Bleibt es: Sicherheits-Plugin/Hoster blockt (Simon). |
| `NEIN Administrator` / `NEIN … unfiltered_html` | Mit diesem Konto geht es nicht. Admin-Konto nutzen oder Simon. |
| `nicht erreichbar` / `kein JSON` | Firewall, Wartungsmodus oder gesperrte REST-API beim Hoster → Simon. |
| `ACHTUNG Menü(s) … nehmen neue Seiten automatisch auf` | Vor dem ersten Hochladen: WP-Admin → Design → Menüs → Haken „Automatisch neue Seiten hinzufügen“ entfernen, speichern. Sonst erscheinen Vorschauseiten im Menü der jetzigen Website. |
| Vorlage `…` gewählt | gut: neue Seiten ohne Kopf und Fuß des Themes, wir bringen eigene mit. |
| keine leere Seitenvorlage gefunden | nach dem Probelauf lösen (Schritt 4, letzter Absatz). |
| `NEIN … unfiltered_html` auf **WordPress.com** | Tarif ohne eigenes JavaScript. Braucht Business oder höher → Simon. |
| `cache_plugins` / `sicherheit` | merken, steht im Skill `wordpress` (Falle 7). |

`check` legt außerdem das **Vorschau-Passwort** an. Damit sind neue Seiten für andere unsichtbar,
bis Sabine sie freigibt. Sag ihr, dass es in `.env` steht (`VORSCHAU_PASSWORT`) und sie es braucht,
um ihre Vorschau im Browser anzusehen.

## Schritt 4: Probelauf

```bash
python3 tools/wp.py testseite
```

Legt einen unsichtbaren Entwurf an, prüft, ob WordPress eigenes Design und Skripte stehen lässt,
und löscht ihn sofort wieder. Alles `OK` → weiter. `WEG` bei `<style>`/`<script>` → Simon (fehlendes
Recht, Sicherheits-Plugin). `ACHTUNG Skript wird verändert` ist bekannt und durch die `&`-Regel
abgefangen.

**Keine leere Seitenvorlage?** Dann zeigt WordPress den Kopf und Fuß des Themes über und unter
unseren Seiten. Zwei Wege, mit Sabine entscheiden:
- Theme-Kopf und -Fuß nur auf unseren Seiten ausblenden: Nach dem ersten Push (Schritt aus
  `/importieren`) die Vorschau mit Playwright öffnen, die Elemente von Theme-Kopf und -Fuß finden
  (`document.querySelectorAll('body > * , .wp-site-blocks > *')`, typisch
  `header.wp-block-template-part`, `footer.wp-block-template-part`, `#masthead`, `#colophon`) und als
  Liste in `site/config.json` bei `"theme_ausblenden"` eintragen. Neu pushen, nachmessen.
- Oder den Theme-Kopf behalten und `site/kopf.html` leer lassen (dann pflegt Sabine das Menü in
  WordPress unter Design → Menüs bzw. im Website-Editor).

## Schritt 5: index.html übernehmen

Sabine fragen, wo ihre Datei liegt. Am einfachsten: Datei aus dem Finder ins Claude-Fenster ziehen,
dann steht der Pfad im Chat. Gibt es Bilder dazu (Ordner neben der index.html), den ganzen Ordner.

```bash
cp "<pfad>/index.html" original/index.html
# mit Bilderordner (Ordnername wie im Original, damit die Pfade stimmen):
cp -R "<pfad>/<bilderordner>" original/
```

Kurz ansehen (nur Struktur, nicht die ganze Datei lesen):
`grep -c "<section" original/index.html`, `grep -o "<title>.*</title>" original/index.html`.

## Abschluss

```bash
git add -A && git commit -m "Einrichtung: Ausgangsdatei von Sabine übernommen" && git push
```

`.env` wird dabei nicht hochgeladen (steht in `.gitignore`); vorher mit `git status` prüfen, dass sie
nicht in der Liste auftaucht.

Dann zusammenfassen: verbunden mit ihrer Website, Probelauf gut, Datei übernommen. Nächster Schritt:

> Jetzt machen wir aus deiner index.html die WordPress-Seite. Dazu einfach `/importieren`.

Und direkt mit dem Skill `importieren` weitermachen, wenn sie zustimmt.
