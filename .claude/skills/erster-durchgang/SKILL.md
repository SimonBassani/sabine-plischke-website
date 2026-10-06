---
name: erster-durchgang
description: Der komplette erste Durchgang für Sabines Website, in einem Rutsch. Ihre fertige index.html (mit allen Effekten) wird 1:1 übernommen, nach WordPress gebracht, gegen das Original geprüft und VERÖFFENTLICHT. Erst danach gibt es Fragen und Vorschläge. IMMER nutzen bei "/erster-durchgang", "erster Durchgang", "übernimm meine Datei und veröffentliche sie", "meine index.html online stellen", "Website hochschalten", oder wenn Sabine zum ersten Mal ihre index.html bringt.
---

# Erster Durchgang: index.html 1:1 online

Sabine hat ihre Website als fertige `index.html` gebaut, mit allen Effekten. **Diese Datei ist die
Ausgangsbasis.** Mit dem Startprompt hat sie den Auftrag zum Veröffentlichen erteilt. Ziel:
Die Seite ist am Ende öffentlich erreichbar und sieht aus und verhält sich wie ihr Original.

## Die drei Regeln dieses Durchgangs

1. **Nichts ändern.** Kein Text, keine Farbe, kein Abstand, kein Effekt, keine Reihenfolge, auch keine
   Tippfehler, keine Umlaut-Korrektur, keine „Verbesserung“. Alles, was dir auffällt, kommt auf die
   **Fragenliste** für danach.
   Erlaubt sind nur technisch nötige Eingriffe, die man nicht sieht:
   - `&` in Skripten umschreiben, mit identischem Verhalten (`if(a&&b)` → `if(a)if(b)`).
   - Google Fonts → Bunny Fonts (dieselben Schriften, macht der Import).
   - Bilder in die Mediathek, Pfade auf die Mediathek-Adressen (macht `push`).
   - Kapselung des CSS und Aufteilen in Kopf/Inhalt/Fuß (Markup bleibt unverändert, macht der Import).
   - Was nötig ist, damit WordPress die Seite **genauso** anzeigt wie das Original (Falle 3 im Skill
     `wordpress`, Theme ausblenden). Maßstab ist immer das Original.
2. **Durchziehen, nicht fragen.** Fragen nur, wenn es ohne Sabine nicht weitergeht: Anwendungspasswort
   anlegen (nur sie hat den Login), Datei nicht auffindbar. Alles andere selbst lösen
   (`references/fehlerbehebung.md` im Skill `wordpress`, Websuche, Doku der Plugins und des Hosters).
3. **Erst prüfen, dann veröffentlichen.** Live geht die Seite erst, wenn die Vorschau den Vergleich mit
   dem Original besteht. Kann ein Problem nicht gelöst werden, nicht halbfertig live schalten,
   sondern ehrlich sagen, woran es hängt und was du versucht hast.

## Ablauf

Zwischendurch nur kurze Statuszeilen für Sabine („Verbindung steht.“, „Seite liegt in WordPress,
ich prüfe sie jetzt.“). Kein Technik-Vortrag.

### 1. Einrichten (Skill `einrichten`, Schritte 1 bis 4)

Werkzeuge prüfen, Anwendungspasswort anlegen lassen, `check`, `testseite`. Die WordPress-Adresse aus
Sabines Prompt in `.env` als `WP_URL` eintragen (die Datei legst du an, das Passwort trägt sie selbst
ein, siehe Skill). Warnt `check` vor Menüs mit „automatisch neue Seiten hinzufügen“: Sabine kurz
bitten, den Haken zu entfernen, oder es mit ihrem Einverständnis selbst über den WP-Admin erledigen.

### 2. Datei übernehmen

Sabine gibt die index.html **direkt im Chatfenster**. Das kommt auf zwei Arten an:

- **Als Dateipfad** (Datei ins Terminal gezogen, z. B. `/Users/…/index.html`): die Datei mit `cp`
  nach `original/index.html` kopieren. Liegt daneben ein Bilderordner, den mitkopieren (Pfade wie
  im Original). Den Ordner der Datei merken, er ist der Suchort für Bilder.
- **Als angehängter Inhalt** (Claude-App, kein Pfad sichtbar): den Inhalt **unverändert, Zeichen für
  Zeichen** mit dem Write-Werkzeug nach `original/index.html` schreiben. Nichts kürzen, nichts
  umformatieren. Danach prüfen, dass die Datei vollständig ist (`tail -c 200 original/index.html`
  endet mit `</html>`; Größe plausibel). Wirkt der Inhalt abgeschnitten: die Datei auf dem Rechner
  suchen (`mdfind -name index.html`, neueste zuerst, `ls -lt`) und von dort kopieren, sonst Sabine
  bitten, die Datei ins Terminal-Fenster zu ziehen (dann kommt der Pfad).

Danach die **Bilder** klären: `grep -oE '(src|href|url\()=?["'\'']?[^"'\''()<>]+\.(jpe?g|png|webp|gif|svg|avif|mp4)' original/index.html`
zeigt, welche lokalen Dateien die Seite braucht (Adressen mit `http` und `data:` sind schon drin).
Fehlen welche: erst selbst suchen (Ordner der Datei, Schreibtisch, Downloads, Dokumente:
`mdfind -name "<dateiname>"`), gefundene Dateien relativ zu `original/` so ablegen, wie die Seite
sie erwartet. Nur was dann noch fehlt, bei Sabine erfragen („Zieh bitte den Ordner mit deinen
Bildern hier ins Fenster“). Ohne alle Bilder nicht veröffentlichen.

### 3. Importieren und technisch anpassen

```bash
python3 tools/wp.py importieren original/index.html
python3 tools/wp.py bauen start
```

`FEHLER` beheben, nur mit erlaubten Eingriffen (Regel 1). `Hinweis`-Zeilen **nicht** abarbeiten,
sondern auf die Fragenliste setzen (Links auf .html-Dateien, ae/oe/ue, Formulare, fehlende h1 …).
Liegen lokale Skripte oder Stylesheets neben der index.html, deren Inhalt unverändert nach
`site/basis.js` bzw. `site/design.css` (Reihenfolge wie im Original).

### 4. Lokal gegen das Original prüfen

`python3 tools/wp.py server` im Hintergrund. Mit Playwright `http://127.0.0.1:8765/original/index.html`
und `http://127.0.0.1:8765/dist/start.vorschau.html` je bei 1440 × 900 und 390 × 844 öffnen und
messen (Skript im Skill `wordpress`, Verifikationsprotokoll Schritt 3). Zusätzlich die **Effekte**:
jeden Effekt des Originals einmal auslösen (scrollen bis zum Ende, hovern, Menü am Handy öffnen,
Zähler, Slider) und prüfen, dass er in der Vorschau genauso passiert. Konsole ohne Fehler.
Abweichung → Ursache messen, beheben, erneut vergleichen.

### 5. Nach WordPress, live prüfen

```bash
python3 tools/wp.py push start
```

Dann das komplette Verifikationsprotokoll aus dem Skill `wordpress` auf der Vorschau-Adresse (mit
Vorschau-Passwort) und dieselben Messwerte wie in Schritt 4 vergleichen. Sieht man Kopf oder Fuß des
Themes: `theme_ausblenden` (Skill `einrichten`, Schritt 4). Erst weiter, wenn alles übereinstimmt.

### 6. Veröffentlichen

```bash
python3 tools/wp.py live start --ja
```

Startseite: In `site/wordpress-info.json` nachsehen (`startseite`, `seiten`).
- WordPress zeigt als Startseite die Beitragsliste (`show_on_front: posts`), oder es gibt außer
  Musterseiten („Beispiel-Seite“, „Datenschutzerklärung“-Entwurf) keine veröffentlichten Seiten:
  `python3 tools/wp.py startseite start --ja`, dann `python3 tools/wp.py push --alle --ja-live`.
  Die ausgegebenen alten Werte in `docs/lehren.md` notieren (zum Zurückstellen).
- Steht im Prompt ausdrücklich **„Startseite ersetzen: JA“**: ebenso umstellen, auch wenn es schon eine
  Website mit eigener Startseite gibt (die alte Startseite bleibt als Seite erhalten, alte Werte notieren).
- Sonst, bei bestehender Website mit eigener Startseite: **nicht** ersetzen. Die neue Seite ist
  unter ihrer eigenen Adresse live; das Ersetzen der Startseite ist die erste Frage danach.

Cache leeren, falls ein Cache-Plugin aktiv ist (Falle 7). Dann **ausgeloggt** prüfen (frischer
Playwright-Aufruf ohne Passwort): Seite erreichbar, Konsole fehlerfrei, Effekte laufen, Handy ohne
Überlauf, ein Screenshot Desktop und Handy angesehen.

### 7. Speichern

```bash
git add -A && git commit -m "Erster Durchgang: Website aus Sabines index.html veröffentlicht" && git push
```

Scheitert `git push` an der Anmeldung: lokal ist alles gespeichert, Sabine kurz Bescheid geben, dass
Simon das Hochladen zu GitHub mit ihr einrichtet. Den Durchgang deshalb nicht abbrechen.

### 8. Ergebnis und Fragen

Kurz und in Alltagssprache:
1. **Die Adresse**, unter der die Seite jetzt öffentlich ist (anklickbar).
2. Was 1:1 übernommen wurde (ein Satz), und die unsichtbaren technischen Anpassungen in einer Zeile.
3. **Fragen, nummeriert, wichtigste zuerst**, je mit kurzer Begründung, warum es zählt. Typisch:
   - Soll diese Seite die Startseite werden (falls noch nicht)?
   - Links ins Leere (z. B. auf `kontakt.html`, `#`): wohin sollen sie führen? Eigene Unterseiten?
   - Impressum und Datenschutzerklärung: gibt es sie? (In Deutschland Pflicht, sonst abmahngefährdet.
     Steht ganz oben, wenn sie fehlen.)
   - Formulare: wohin sollen Anfragen gehen?
   - Auffälligkeiten im Text (Tippfehler, ae statt ä) mit Fundstelle, nur als Vorschlag.
   - Beschreibung für Google (Titel, Kurztext), Vorschaubild beim Teilen.
4. Ein Satz, wie es weitergeht: „Sag mir einfach, was du ändern möchtest, oder beantworte die Fragen
   der Reihe nach.“

Danach wartet Claude auf Sabine. Änderungen an der jetzt öffentlichen Seite laufen über den Alltag-Ablauf
im Skill `veroeffentlichen` (zeigen, Ja, live).
