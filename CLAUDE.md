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
- Wenn etwas schiefgeht: ruhig benennen, was los ist, und den nächsten Schritt vorschlagen. Bei
  Zugangsproblemen, Hosting oder Unklarheit: „Das klären wir mit Simon“ (office@digi-up.at).

## Die Befehle

| Befehl | Wofür |
|---|---|
| `/einrichten` | Startassistent beim allerersten Mal (Zugang, Prüfung, index.html übernehmen) |
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

1. **Nichts wird ohne Sabines ausdrückliches Ja öffentlich.** Standard ist die passwortgeschützte
   Vorschau (`push`). `live`, `startseite` und `push --ja-live` nur nach klarer Zustimmung im Chat.
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
7. **Keine Google Fonts, keine Einbettungen ohne Einwilligung** (YouTube, Google Maps, Facebook-Pixel).
   Schriften über `fonts.bunny.net`. Einbettungen nur nach Rücksprache mit Simon (Cookie-Einwilligung).
8. **Bestehende Seiten nicht anfassen.** Was schon in WordPress steht und nicht aus diesem Repo
   kommt (alte Seiten, Beiträge, Plugins, Menüs), bleibt unverändert, bis der Umstieg gemeinsam mit
   Simon live geht. Nichts in WordPress löschen. Plugins, Updates, Hosting: Sache von Simon.

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
