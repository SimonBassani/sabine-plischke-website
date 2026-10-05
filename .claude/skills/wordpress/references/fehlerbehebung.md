# Fehlerbehebung: selbst lösen

Grundsatz: **Erst selbst lösen, dann eskalieren.** Sabine soll nicht mit Technik allein gelassen
werden, und Simon soll nur bei Dingen gerufen werden, die Claude wirklich nicht kann.

## Vorgehen bei jedem Problem

1. **Genau hinsehen:** die vollständige Fehlermeldung, HTTP-Status, betroffene Seite, Konsole im
   Browser. Nicht raten.
2. **Hier nachschlagen** (Tabelle unten) und in `docs/lehren.md` (was in diesem Repo schon gelöst wurde).
3. **Recherchieren:** WebSearch mit der exakten Fehlermeldung plus „WordPress“ und, falls bekannt, Name
   von Theme, Plugin oder Hoster (`site/wordpress-info.json`). Offizielle Doku bevorzugen
   (developer.wordpress.org, Plugin-Doku, Hilfe-Center des Hosters). Lösung erst verstehen, dann anwenden.
4. **Kleinsten umkehrbaren Schritt** ausprobieren, nachmessen. Nicht drei Dinge gleichzeitig ändern.
5. **Festhalten:** Problem, Ursache und Lösung als kurzer Eintrag in `docs/lehren.md`, mit Datum.
   Beim nächsten Mal steht es dann da.

Selbst erledigen darf Claude: alles im Repo, Seiten über `tools/wp.py`, Einstellungen im WP-Admin
**über Sabine** (genaue Klickanleitung geben) oder per REST, wenn umkehrbar und vorher notiert.

**Eskalieren an Simon (office@digi-up.at)** nur bei: Zugang, den Sabine nicht hat (Hosting, FTP,
DNS), Kosten (Tarif-Upgrade, kostenpflichtiges Plugin), Rechtsfragen (Impressum-Inhalt,
Datenschutz-Bewertung), oder wenn nach Recherche und zwei ernsthaften Versuchen kein Weg da ist.
Dann eine fertige Nachricht für Sabine formulieren: was passiert ist, was versucht wurde, was gebraucht wird.

## Bekannte Probleme

| Symptom | Ursache | Lösung |
|---|---|---|
| `check`: „Anmeldung abgelehnt“ (401), Daten stimmen aber | Hoster entfernt den `Authorization`-Header (Apache mit CGI/FastCGI) | Prüfen: `curl -s -o /dev/null -w "%{http_code}" -u "user:pw" <WP_URL>/wp-json/wp/v2/users/me`. Fix in `.htaccess`: `SetEnvIf Authorization "(.*)" HTTP_AUTHORIZATION=$1` (braucht Datei-Zugang über den Hoster → Simon). |
| 401 trotz richtiger Daten, Wordfence aktiv | Wordfence sperrt Anwendungspasswörter | Wordfence → Login Security → Settings → „Disable WordPress application passwords“ aus |
| Bereich „Anwendungspasswörter“ fehlt im Profil | Sicherheits-Plugin, kein HTTPS, oder WordPress.com-Tarif ohne Plugins | Plugin-Einstellung (Wordfence, Solid Security, All In One WP Security) suchen; bei WordPress.com Tarif prüfen |
| 403 beim `push`, aber `check` ok | Firewall des Hosters (ModSecurity) blockt Inhalte mit `<script>` | Hoster-Hilfe zu „ModSecurity“/„WAF“ suchen; oft im Kundenmenü abschaltbar oder Ausnahme für `/wp-json/` (Sabine anleiten); sonst Simon |
| 413 / „Request Entity Too Large“ | Seite zu groß (eingebettete Bilder/Schriften) | base64-Bilder nach `bilder/` (macht der Import), Schriften über Bunny |
| `rest_forbidden`, `rest_cannot_create` | Benutzer ist kein Administrator | Mit Admin-Konto ein Anwendungspasswort anlegen |
| „kein JSON“, HTML-Seite statt Antwort | Wartungsmodus, „Coming soon“-Plugin, REST-API per Plugin gesperrt | `check` zeigt Plugins; Wartungsmodus/„Disable REST API“ für angemeldete Nutzer erlauben |
| `<style>`/`<script>` verschwinden | kein `unfiltered_html` (kein Admin, Multisite, `DISALLOW_UNFILTERED_HTML`, WordPress.com ohne Business) | anderes Konto bzw. Tarif; sonst Simon |
| Skript läuft live nicht, lokal schon | `&` im Skript, oder Optimierungs-Plugin verzögert/bündelt JavaScript | `&` prüfen (Werkzeug), Plugin-Einstellung „JS verzögern/kombinieren“ für diese Seite ausschließen |
| Live alter Stand | Cache (Plugin, Hoster, Cloudflare) | Cache leeren, mit `?cb=<zahl>` laden (nie `?m=`) |
| Farben/Schriften anders als im Original | Theme-, Page-Builder- oder Block-Theme-Stile | messen (`getComputedStyle`), gewinnende Regel finden, mit `html .srw …` überbieten (Skill `wordpress`, Falle 3) |
| Theme-Kopf/-Fuß über der Seite | keine leere Seitenvorlage | `theme_ausblenden` in `site/config.json` (Skill `einrichten`, Schritt 4) |
| Abstand oben, eingeloggt | Admin-Leiste | für Besucher egal; ausgeloggt prüfen |
| Seite heißt `…-2` | Adresse schon von alter Seite belegt | bei Bedarf alte Seite umbenennen (Skill `veroeffentlichen`, Fall B) |
| Bild-Upload scheitert | Dateityp (SVG), Größe über Upload-Limit | SVG als Code ins HTML; Bild verkleinern (`sips -Z 1920 datei.jpg` auf dem Mac) |
| „WordPress leitet weiter von … nach …“ | `WP_URL` nicht die Endadresse (www/ohne www, http) | angezeigte Adresse in `.env` übernehmen |
| `git push` verlangt Anmeldung | kein GitHub-Zugang auf diesem Rechner | lokal weiterarbeiten; `gh auth login` (GitHub CLI) bzw. Simon |
| Playwright-Screenshot hängt | Zeitlimit beim Laden der Schriften | ohne `fullPage` wiederholen; Messungen per `browser_evaluate` reichen |
