---
name: wordpress
description: Fachwissen, um selbstgebaute Seiten (eigenes HTML/CSS/JS) sicher in WordPress (selbst gehostet oder WordPress.com Business, mit oder ohne Elementor) zu bringen und live zu prüfen. IMMER lesen, bevor etwas mit python3 tools/wp.py push/live/startseite nach WordPress geht, wenn eine Seite live anders aussieht als lokal, wenn JavaScript live nicht läuft, bei Bildern in der Mediathek, Cookie-Banner, Schriften oder wenn eine Seite "kaputt", "weiß", "verrutscht" oder "anders" aussieht.
---

# WordPress: bauen, schicken, live prüfen

Das System, mit dem DigiUp (Simon Bassani) seine eigene Website digi-up.at betreibt, hier für
Sabines WordPress: eigene Seiten als ein Custom-HTML-Block, gebaut und geprüft mit `tools/wp.py`.
Wie neue Seiten aussehen sollen: [`references/gestaltung.md`](references/gestaltung.md).

Welches WordPress Sabine hat (Theme, Page-Builder, SEO-, Cache-, Cookie-Plugin, Vorlagen), steht nach
`python3 tools/wp.py check` in `site/wordpress-info.json`. Vor der Arbeit dort nachsehen.

## Der eine Grundsatz

**Lokal grün heißt nicht live grün.** WordPress verändert Inhalte beim Ausliefern, nicht beim
Speichern. Eine Seite kann lokal fehlerfrei sein, byte-genau gespeichert werden und trotzdem live
kaputt sein. Auch die REST-Antwort (`content.rendered`) ist kein Beweis: Auf digi-up.at kam ein
`&&` dort unverändert zurück und hat live trotzdem schon ein Skript zerstört.
→ **Nach jedem Push die echte Adresse im Browser laden und messen** (Protokoll unten).

## Wie eine Seite in WordPress liegt

`tools/wp.py` baut je Seite genau **einen** `wp:group` (volle Breite) mit genau **einem** `wp:html`:
Schrift-Links, `<style>` (Grundkorrektur + gekapseltes `design.css` + `seite.css`), `<div class="srw">`
mit Kopf, Inhalt, Fuß, danach die Skripte. Seitenvorlage ist bevorzugt eine **leere Vorlage** ohne
Theme-Kopf und -Fuß (`elementor_canvas` bei Elementor, sonst z. B. `blank`), `check` wählt sie aus.
Gibt es keine, blendet `theme_ausblenden` in `site/config.json` den Theme-Kopf und -Fuß nur auf
unseren Seiten aus (Selektoren, z. B. `header.wp-block-template-part`, `#masthead`, `#colophon`).

Folgen davon:
- Das Menü ist `site/kopf.html`, nicht das WordPress-Menü. Neue Seite = Link dort ergänzen.
- Die Seiten lassen sich im WordPress-Editor nicht sinnvoll bearbeiten (ein großer HTML-Block).
  Änderungen immer hier im Repo, sonst überschreibt der nächste Push sie.
- Bestehende Seiten, die mit einem Page-Builder (Elementor, Divi …) gebaut sind, ignorieren den normalen
  Seiteninhalt. Deshalb werden alte Seiten **nicht** überschrieben, sondern durch neue Seiten ersetzt
  (siehe `/veroeffentlichen`).
- Auf **WordPress.com** braucht das System den Business-Tarif oder höher (Plugins, Anwendungspasswörter,
  eigenes JavaScript). Einfachere Tarife entfernen Skripte; `check` und `testseite` zeigen das.

## Die Fallen

### 1. `&` in JavaScript, der teuerste Fehler

WordPress wandelt beim Ausliefern ein rohes `&` in `&#038;` um. In einem `<script>` wird aus
`a&&b` dann `a&#038;&#038;b`: Syntaxfehler, das ganze Skript ist tot (Menü, Animationen, Formulare).

```js
// NIE:                    // STATT DESSEN:
if(a&&b){ … }              if(a)if(b){ … }
if(a&&!b){ … }             if(a)if(!b){ … }
var x = a&&b ? p : q;      var x = a ? (b ? p : q) : q;
url + '?x=1&y=2'           zwei Aufrufe oder nur ein Parameter
```

`tools/wp.py bauen/push` bricht bei jedem `&` in einem Skript ab, auch in Kommentaren. Nie umgehen.

### 2. Recht `unfiltered_html`

Ohne dieses Recht entfernt WordPress `<style>` und `<script>` **still**. Haben nur Administratoren
einer Einzel-Website (nicht Multisite, kein `DISALLOW_UNFILTERED_HTML`). `check` zeigt es,
`testseite` beweist es mit einem Wegwerf-Entwurf.

### 3. Theme- und Page-Builder-CSS färben mit

Auch auf einer leeren Vorlage lädt WordPress das Theme-CSS und z. B. das **Elementor-Kit**
(`.elementor-kit-N h1 {color:…}`) oder die globalen Stile eines Block-Themes. Im Original erben
Überschriften und Links ihre Farbe; hier setzt das Theme sie direkt und gewinnt. Gemessen am
05.10.2026 in einer Simulation: H1 wurde rot.

Dagegen hat das Werkzeug zwei Schichten, die du nicht ausbauen sollst:
- **Kapselung:** Jede Regel aus `design.css` bekommt `.srw` davor (`h1` → `.srw h1`). `body` wird zum
  Wrapper `.srw`, Hintergründe gehen zusätzlich auf den echten `body`. `html`, `:root`,
  `@keyframes`, `@font-face` bleiben. `body.klasse …` (per JS gesetzt) wirkt auf body und Wrapper.
- **Rückstellung:** `.srw :is(h1,…,a,button,…)` setzt Schrift, Größe, Farbe auf Browser-Standard
  zurück. Regeln aus `design.css` stehen danach und gewinnen.

Wenn trotzdem etwas falsch aussieht: **messen statt raten.** `getComputedStyle` auf dem Element und
die gewinnende Regel suchen (Chrome DevTools oder `browser_evaluate`). Gegen Theme-Regeln mit hoher
Spezifität gezielt mit `html .srw …` überbieten, nicht mit `!important`.

### 4. Beitragsbild-Phantom

Nach dem Anlegen und nach Statuswechseln setzt WordPress (bzw. Plugins) teils ein `featured_media`.
Das bestimmt das Vorschaubild beim Teilen des Links (`og:image`). `push` setzt es auf `0` zurück oder
auf `beitragsbild_id` aus `seite.json` (ein Bild 1200 × 630 aus der Mediathek, ID aus `bilder/medien.json`).

### 5. Gleiche Adresse schon belegt

Die alte Website hat vermutlich schon `/ueber-mich/`, `/kontakt/` usw. Eine neue Seite mit derselben
Adresse bekommt von WordPress `-2` angehängt. Das ist während des Aufbaus gewollt (alte Seiten laufen
weiter). Links bleiben richtig, weil `seite:<slug>` die echte Adresse einsetzt. Getauscht wird beim
Livegang (`/veroeffentlichen`).

### 6. Fixierter Kopf und Admin-Leiste

Eingeloggt zeigt WordPress oben die schwarze Admin-Leiste (32 px, mobil 46 px) und schiebt die Seite
nach unten. Ein `position:fixed` Kopf überdeckt sie dann. Für Besucher irrelevant; wenn es stört:
`.admin-bar .srw header{top:32px}` (mobil 46 px) in `design.css`.

### 7. Cache- und Optimierungs-Plugins

Zeigt die Seite nach dem Push den alten Stand: Cache leeren (Plugin-Knopf in der Admin-Leiste) oder
mit `?cb=<zahl>` laden. **Nie `?m=`** (ist eine WordPress-Datumsabfrage, liefert „nicht gefunden“).
Plugins, die JavaScript „verzögern“, „zusammenfassen“ oder „minifizieren“, können Seiten-Skripte
brechen: dann die Seite dort ausschließen.

### 8. Was sonst live zuschlägt

- **Shortcodes:** `[gallery]`, `[irgendwas_mit_unterstrich]` im Text ersetzt WordPress. Das Werkzeug warnt.
- **SVG-Dateien** lässt WordPress nicht hochladen. SVG-Code direkt ins HTML oder als PNG/WebP.
- **Formulare** verschicken nichts von selbst. Ziel klären (Newsletter-Tool, Kontaktformular-Plugin)
  und einbauen. Ist ein Formular-Plugin aktiv (`check`, z. B. WPForms), dessen Formular nutzen.
- **Google Fonts, YouTube, Google Maps, Pixel** übertragen ohne Einwilligung Daten (DSGVO).
  Schriften über `fonts.bunny.net` (macht der Import automatisch), Einbettungen nur mit Simon.
- **Bilder** unter 300 KB halten (WebP oder JPG, 1920 px breit reicht). Große Fotos bremsen am Handy.
- **Reveal-Animationen:** Wenn Elemente per CSS unsichtbar starten (`opacity:0`) und JavaScript sie
  einblendet, bleibt die Seite bei einem JS-Fehler leer. Besser `.js .reveal{opacity:0}`: das
  Werkzeug setzt die Klasse `js` am `<html>` als allererstes Skript.

## Status einer Seite

| Status | Wer sieht sie | Befehl |
|---|---|---|
| entwurf | nur eingeloggt | `push <slug> --entwurf` |
| vorschau | alle mit Vorschau-Passwort (aus `.env`) | `push <slug>` (Standard) |
| live | alle | `live <slug> --ja` (Sabines Auftrag genügt) |

Eine Seite, die schon **live** ist, ändert `push` nur mit `--ja-live`, weil die Änderung dann sofort
für alle sichtbar ist. Hat Sabine die Änderung beauftragt, ist das ihr Ja: direkt mit `--ja-live`.

Achtung Menü: Hat ein WordPress-Menü „Automatisch neue Seiten hinzufügen“ aktiv, landen auch
Vorschauseiten im Live-Menü der alten Website. `check` warnt davor. Den Haken vor dem ersten Push
entfernen (WP-Admin → Design → Menüs).

## Verifikationsprotokoll (nach jedem Push, nicht optional)

Werkzeug: MCP-Server **`playwright`** (ist in `.mcp.json` eingetragen) gegen die **echte Adresse**.

1. `browser_resize` 1440 × 900, `browser_navigate` auf den Link aus der Push-Ausgabe (`?cb=<zahl>`
   anhängen gegen Cache).
2. Vorschau-Passwort eingeben, ohne es im Chat zu zeigen: `browser_evaluate` mit
   `input[name=post_password]` füllen und `form.submit()`. Das Passwort liest du per
   `grep VORSCHAU_PASSWORT .env | cut -d= -f2` (nur dieses Feld, nie die ganze `.env`).
3. Messen, nicht schauen:

```js
async () => {
  await new Promise(r => setTimeout(r, 1500));
  const s = e => { if (!e) return null; const c = getComputedStyle(e);
    return [c.fontFamily.split(',')[0], c.fontSize, c.color, c.backgroundColor].join(' | '); };
  window.scrollTo({ top: 99999, behavior: 'instant' });
  await new Promise(r => setTimeout(r, 1200));
  return {
    seite: !!document.querySelector('.srw'),
    h1: s(document.querySelector('.srw h1')), text: s(document.querySelector('.srw p')),
    link: s(document.querySelector('.srw main a')), knopf: s(document.querySelector('.srw .btn, .srw button')),
    js: document.documentElement.classList.contains('js'),
    bilder_kaputt: [...document.querySelectorAll('.srw img')].filter(i => !(i.complete && i.naturalWidth)).map(i => i.src),
    ueberlauf: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  };
}
```

4. Dieselbe Messung auf dem **Original** (`original/index.html` über `python3 tools/wp.py server` im Hintergrund,
   dann `http://127.0.0.1:8765/original/index.html`) bei gleicher Fensterbreite.
   Werte müssen übereinstimmen. Abweichung = Falle 3.
5. `browser_console_messages` Stufe `error`: 0 Fehler. Sonst Skript reparieren.
6. Wirkung der Skripte beweisen, nicht ihre Existenz: Menü-Knopf am Handy klicken, Animation
   eingeblendet (Klasse gesetzt?), Formular sichtbar. „Fehlerfrei geladen“ heißt nicht „gelaufen“.
7. `browser_resize` 390 × 844 und 768 × 1024: `ueberlauf` muss 0 sein, Menü bedienbar.
8. `browser_take_screenshot` Desktop und Handy **ansehen** (Kontrast, Überlagerungen). Hängt der
   Screenshot (Zeitlimit beim Font-Laden), ohne `fullPage` erneut versuchen.

Erst wenn alles grün ist, Sabine den Link zeigen: Adresse plus Hinweis, dass das Passwort in ihrer
`.env` steht (Simon hat es ebenfalls). Danach `git add -A && git commit && git push`.

## Cookie-Banner

Nie selbst bauen (Script-Blocking vor der Einwilligung, Protokoll, Widerruf: das gehört in ein
gepflegtes Plugin). Ein vorhandenes Plugin (Complianz, Borlabs, Real Cookie Banner) umstylen statt
ersetzen. Complianz nutzt CSS-Variablen `--cmplz_*` (Unterstriche). „Ablehnen“ gleich groß wie
„Akzeptieren“ lassen. Nach dem Umstylen die Mechanik testen (Ablehnen speichert, Widerruf-Reiter da).
Braucht die neue Seite gar keine Einbettungen und kein Tracking, reicht oft kein Banner. Mit Simon klären.
