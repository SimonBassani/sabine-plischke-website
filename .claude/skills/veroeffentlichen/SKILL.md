---
name: veroeffentlichen
description: Schaltet Seiten der Website von Sabine Hoeppner-Plischke öffentlich (Vorschau → live) ändert Seiten, die schon live sind, und führt durch den Umstieg, wenn die neue Website eine bestehende ersetzt. IMMER nutzen bei "/veroeffentlichen", "live schalten", "Änderung online stellen", "auf der echten Seite ändern", "online stellen", "freigeben", "Relaunch", "neue Website aktivieren", "alte Seite ersetzen", "Startseite umstellen".
---

# Veröffentlichen

Öffentlich ist öffentlich: Jeder Schritt hier braucht **Sabines ausdrückliches Ja im Chat**, vorher
in einem Satz erklärt, was danach für Besucher anders ist. Lies vorher den Skill `wordpress`.

Zuerst klären, welcher Fall vorliegt:

## Alltag: Änderung an einer Seite, die schon live ist

Text, Bild, neuer Menüpunkt auf einer öffentlichen Seite. Ablauf:
1. Im Repo ändern, `python3 tools/wp.py bauen <slug>`, lokal zeigen (`dist/<slug>.vorschau.html` über
   `python3 tools/wp.py server`), Sabine sagt „passt“.
2. Sabine fragen: „Soll das jetzt für alle sichtbar werden?“ Bei Ja:
   `python3 tools/wp.py push <slug> --ja-live` (Kopf/Fuß/Design geändert: `push --alle --ja-live`).
3. Verifikationsprotokoll (Skill `wordpress`) auf der Live-Seite, ausgeloggt. Bei Fehlern sofort
   zurück: `git checkout HEAD~1 -- <geänderte Dateien>`, erneut `push … --ja-live`, dann reparieren.
4. `git add -A && git commit -m "<was sich geändert hat>" && git push`

## Fall A: einzelne neue Seite, die alte Website bleibt (z. B. eine Landingpage)

1. Verifikationsprotokoll (Skill `wordpress`) auf der Vorschau, alles grün.
2. Impressum und Datenschutz sind von der Seite aus erreichbar (Pflicht für jede öffentliche Seite).
   Fehlen sie in unserem Fuß: auf die bestehenden Seiten der alten Website verlinken (normale URL).
3. Hat die Seite ein Formular: einmal mit Sabines eigener Adresse testen (Bestätigungsmail kommt an?).
4. Sabine fragen. Bei Ja:
   ```bash
   python3 tools/wp.py live <slug> --ja
   ```
5. Ausgeloggt (privates Fenster bzw. frisches Playwright) prüfen: Seite ohne Passwort erreichbar,
   Konsole fehlerfrei, Handy ok. Link an Sabine.
6. `git add -A && git commit -m "<Titel> ist live" && git push`

## Fall B: Umstieg, die neue Website ersetzt eine bestehende (oder geht erstmals online)

**Nur gemeinsam mit Simon** (office@digi-up.at). Diese Liste ist der Fahrplan für den Termin; nichts
davon alleine ausführen. Haken für Haken mit Sabine durchgehen.

Vorher:
- [ ] **Sicherung** der kompletten alten Website beim Hoster oder per Plugin (z. B. UpdraftPlus).
      Ohne Sicherung kein Relaunch.
- [ ] Alle neuen Seiten als Vorschau fertig, geprüft (Protokoll), von Sabine abgenommen.
- [ ] **Impressum und Datenschutz** neu und vollständig (Datenschutz nennt Bunny Fonts, Hoster,
      Newsletter-Tool, Cookie-Plugin, alles Eingebundene).
- [ ] Cookie-Einwilligung: nötig, sobald Tracking oder Einbettungen drin sind. Mit Simon entscheiden.
- [ ] Liste der **alten Adressen** (`python3 tools/wp.py seiten`) und wohin jede künftig führen soll.
      Alte Links bei Google und in Sabines Profilen sollen nicht ins Leere laufen.

Der Wechsel (kurzes Zeitfenster, möglichst abends; gibt es noch keine alten Seiten, entfallen 1 und 6):
1. Alte Seiten, deren Adresse die neue braucht (z. B. `/ueber-mich/`), im WP-Admin auf **Entwurf**
   setzen und ihre Adresse in `alt-ueber-mich` ändern. Nicht löschen.
2. In `seiten/<slug>/seite.json` steht `wp_slug` bereits richtig; `python3 tools/wp.py push --alle`
   holt jetzt die freien Adressen (statt `-2`). Kontrolle: `python3 tools/wp.py seiten`.
3. `python3 tools/wp.py live <alle slugs> --ja`
4. `python3 tools/wp.py startseite start --ja` (gibt die bisherige Einstellung zum Zurückstellen aus,
   notieren).
5. `python3 tools/wp.py push --alle --ja-live`, damit alle Links die endgültigen Adressen tragen.
6. Weiterleitungen alter Adressen auf neue (Plugin „Redirection“ oder Yoast Premium), für jede Zeile
   der Liste von oben.
7. Cache leeren.

Danach prüfen (ausgeloggt, Desktop und Handy): Startseite, jede Seite, Menü, Fuß-Links, Formulare,
eine alte Adresse leitet richtig um, Konsole fehlerfrei. Im SEO-Plugin bei keiner neuen Seite
„noindex“. Sitemap neu bei der Google Search Console einreichen (falls eingerichtet).

Zurück, falls etwas schiefgeht: Startseite mit den notierten Werten zurückstellen
(WP-Admin → Einstellungen → Lesen), neue Seiten auf Entwurf, alte Seiten wieder veröffentlichen.

Zum Schluss: `git add -A && git commit -m "Relaunch: neue Website live" && git push`.
