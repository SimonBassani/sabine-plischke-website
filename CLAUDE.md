# Website Sabine Hoeppner-Plischke: Arbeitsanweisungen für Claude

Hier entsteht und lebt die Website von **Sabine Hoeppner-Plischke**. Die Seiten werden als eigenes
HTML/CSS/JS gebaut und über die REST-API in ihr **WordPress** geschoben (Adresse steht in `.env`
unter `WP_URL`, Theme und Plugins in `site/wordpress-info.json` nach `python3 tools/wp.py check`).
Eingerichtet von DigiUp Consulting (Simon Bassani), nach demselben System, mit dem DigiUp seine
eigene Website betreibt. Sabine und Simon arbeiten beide mit Claude Code in diesem Repo, jede Person
auf ihrem eigenen Rechner.

Über Sabines Angebot und Zielgruppe steht hier bewusst nichts: Das kommt aus ihren Texten und ihrer
index.html. Nichts dazuerfinden.

## Mit wem du sprichst

Meist mit **Sabine**. Sie ist stark im Inhalt und will verstehen, was passiert, aber keine Technik
lernen. Deshalb:

- Alltagssprache, du-Form, kurze Sätze. Erkläre, **was sie tut und was die Besucher sehen**, nicht
  wie es technisch funktioniert. Kein „REST“, „Slug“, „Commit“, „Push“ ohne Übersetzung
  (Adresse der Seite, Stand speichern, nach WordPress schicken).
- Pro Schritt eine Sache. Am Ende jedes Schritts sagen, was als Nächstes kommt.
- Wenn etwas schiefgeht: **selbst eine Lösung suchen**, nicht Sabine fragen, was zu tun ist.
  Vorgehen und bekannte Probleme: `.claude/skills/wordpress/references/fehlerbehebung.md`, gelöste
  Fälle in `docs/lehren.md`, sonst Websuche und Doku. Sabine nur einbeziehen, wenn ein Klick in ihrem
  Konto nötig ist (dann genaue Anleitung). Simon (office@digi-up.at) nur, wenn es außerhalb von
  WordPress liegt (Hosting-Vertrag, Domain, E-Mail, Kosten) oder nach Recherche und zwei Versuchen kein Weg da ist.

## Die Befehle

| Befehl | Wofür |
|---|---|
| `/erster-durchgang` | **Start:** Einrichtung, index.html 1:1 übernehmen, prüfen, veröffentlichen, danach Fragen |
| `/einrichten` | nur die Einrichtung (Zugang, Prüfung), z. B. auf einem neuen Rechner |
| `/importieren` | eine fertige `index.html` in WordPress-taugliche Bausteine zerlegen und als Vorschau hochladen |
| `/neue-seite` | Unterseite anlegen (z. B. Über mich, Angebot, Kontakt) |
| `/veroeffentlichen` | Seiten öffentlich schalten, Relaunch-Checkliste |

Das Fachwissen dahinter (Fallen, Prüfprotokoll) steht im Skill **`wordpress`**. Lies ihn, bevor du
etwas nach WordPress schickst. Alle WordPress-Vorgänge laufen über `python3 tools/wp.py`
(Befehle: `python3 tools/wp.py -h`), nie über selbstgebaute curl-Aufrufe.

## Aufbau

```
original/          Sabines Ausgangsdateien (index.html, Bilder), bleiben unverändert
site/design.css    gemeinsames Design aller Seiten (Farben, Schriften, Bausteine)
site/kopf.html     Menü oben, erscheint auf jeder Seite
site/fuss.html     Fußbereich, erscheint auf jeder Seite
site/basis.js      gemeinsames JavaScript
site/config.json   Schriften, WordPress-Vorlage, Wrapper-Klasse
seiten/<slug>/     je Seite: inhalt.html, seite.json, optional seite.css und seite.js
bilder/            alle Bilder; medien.json merkt sich, was schon in der Mediathek liegt
tools/wp.py        das Werkzeug (bauen, prüfen, hochladen)
dist/              gebaute Dateien (wird erzeugt, nicht bearbeiten)
```

Konventionen:
- **Interne Links** immer als `href="seite:<slug>"` (z. B. `seite:ueber-mich`, `seite:start#kontakt`).
  Das Werkzeug setzt die echte WordPress-Adresse ein.
- **Bilder** als `bilder/<datei>` einbinden. Dateinamen klein, ohne Leerzeichen und Umlaute.
- Das CSS wird beim Bauen automatisch unter `.srw` gekapselt. Normal schreiben wie im Original.

## Harte Regeln

0. **Verbindung zu WordPress nur über das Anwendungspasswort in `.env` und `python3 tools/wp.py`.**
   Nie beim Hoster einloggen (united-domains, IONOS, Strato …), nie Dateimanager, FTP oder Browser-Login
   zum Hochladen nutzen, keine index.html auf den Webspace legen. Der Hoster ist für dieses System egal.
   Gibt Sabine im Chat ein Passwort aus sechs Viererblöcken (`abcd efgh ijkl mnop qrst uvwx`), ist es
   das Anwendungspasswort: in `.env` als `WP_APP_PASSWORT` eintragen, nie wieder anzeigen, weitermachen.
   Ihr Login-Passwort für WordPress oder den Hoster wird nie gebraucht.

1. **Sabine hat freie Hand, ihr Auftrag im Chat ist das Ja.** Was sie sagt („stell das online“,
   „lösch die alte Seite“, „installier ein Plugin für …“, „ändere das Menü“), führt Claude direkt aus:
   in einem Satz ankündigen, was passiert, dann machen. Nicht um Erlaubnis fragen, nicht auf Simon
   verweisen, keine Vorschau-Schleife, wenn sie es direkt live will. Nachfragen nur, wenn unklar ist,
   **was** sie will. Ohne Auftrag ändert Claude nichts Sichtbares (dann Vorschau mit Passwort).
1a. **Ihre index.html ist die Vorlage, nicht der Entwurf.** Im ersten Durchgang nichts an Text,
   Design oder Effekten ändern, nur unsichtbare technische Anpassungen. Auffälligkeiten sammeln und
   nach dem Veröffentlichen als Fragen stellen. Später ändert sich nur, was Sabine will.
2. **Kein `&` in JavaScript.** WordPress macht beim Ausliefern `&#038;` daraus und das Skript ist
   tot. Das Werkzeug bricht dann ab. `if(a&&b)` wird `if(a)if(b)`. Auch in Kommentaren.
3. **Lokal grün heißt nicht live grün.** Nach jedem Push die echte Seite im Browser prüfen
   (Playwright, Protokoll im Skill `wordpress`). Erst dann „fertig“ sagen.
4. **Nichts erfinden.** Keine Texte, Zahlen, Kundenstimmen, Lebenslauf-Details oder Versprechen,
   die Sabine nicht geliefert hat. Fehlt Text: sichtbarer Platzhalter `[TEXT FOLGT]` und nachfragen.
   Über ihre eigene Geschichte entscheidet sie selbst, was öffentlich wird.
5. **Echte Umlaute** (ä, ö, ü, ß) in allen Texten, nie ae/oe/ue/ss.
6. **Keine Zugangsdaten ins Repo.** Sie stehen nur in `.env` (ist in `.gitignore`). `.env` nie
   anzeigen, nie in den Chat kopieren, nie committen.
7. **Datenschutz mitdenken, nicht blockieren:** Schriften über `fonts.bunny.net` statt Google Fonts.
   Will Sabine YouTube, Google Maps, Pixel o. Ä. einbinden: machen und dabei sagen, dass es im
   Cookie-Banner (WPConsent) eingetragen und in der Datenschutzerklärung genannt werden muss, und
   das gleich mit erledigen.
8. **Alles in WordPress ist erlaubt**: Seiten, Beiträge, Menüs, Medien, Plugins, Einstellungen.
   Werkzeuge: eigene Seiten über `push`/`live`/`startseite`, alte Seiten über `ablegen` (Entwurf +
   Adresse `alt-…`), alles andere über `python3 tools/wp.py api <METHODE> <pfad> …` (z. B.
   `api GET /wp/v2/plugins`, `api POST /wp/v2/plugins --daten '{"slug":"redirection","status":"active"}'`,
   `api POST /wp/v2/settings --daten '{"title":"…"}'`, `api GET /wp/v2/menu-items`).
   Sicherheitsnetz statt Verbot: Löschen landet im Papierkorb (30 Tage zurückholbar), endgültig nur
   mit `--endgueltig`, wenn Sabine das ausdrücklich will. `api` protokolliert jede Änderung in
   `docs/protokoll.md` und sichert den vorherigen Stand in `docs/sicherungen/`. Vor großen Umbauten
   (Theme wechseln, viele Seiten löschen) kurz an das Backup des Hosters erinnern, dann machen.
   Geht etwas nur im WP-Admin (z. B. Theme-Einstellungen per Klick): Sabine Klick für Klick anleiten.
   Simon nur, wenn es außerhalb von WordPress liegt (Hosting-Vertrag, Domain, E-Mail-Postfach, Kosten).

## Gemeinsam arbeiten (Sabine und Simon)

- **Zu Beginn jeder Sitzung:** `git pull`, damit du den Stand der anderen Person hast.
- **Nach jedem fertigen Schritt** (Seite geprüft): Änderungen speichern und hochladen,
  `git add -A && git commit -m "<was sich geändert hat>" && git push`. Die Nachricht auf Deutsch,
  in einem Satz, was Sabine sehen würde (z. B. „Über-mich-Seite mit neuem Foto“).
- Meldet `push` „in WordPress seit dem letzten Push verändert“: nicht mit `--trotzdem` drüberbügeln.
  Erst `git pull`; hat jemand im WP-Admin direkt geändert, Sabine fragen, welche Fassung gilt.
- Inhalte immer hier im Repo ändern, nicht im WordPress-Editor. Sonst überschreibt der nächste Push
  die Änderung (der Schutz oben warnt davor).

## Wenn Sabine etwas ändern will

Textänderung, neues Bild, anderer Knopf: in `seiten/<slug>/inhalt.html` bzw. `site/*.html` ändern,
`python3 tools/wp.py bauen <slug>`, lokal in `dist/<slug>.vorschau.html` zeigen, dann
`python3 tools/wp.py push <slug>` und live prüfen. Änderungen an Kopf, Fuß oder Design betreffen
alle Seiten: `push --alle`.
