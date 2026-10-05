# Gestaltung: wie neue Seiten aussehen sollen

Aus dem Design-Playbook der DigiUp-Website-Engine, zugeschnitten auf eine bestehende Marke.

## Grundhaltung

- **Sabines Design ist gesetzt.** Farben, Schriften, Abstände und Bausteine kommen aus
  `site/design.css` und der Startseite. Eine Unterseite soll aussehen, als wäre sie von Anfang an
  dabei gewesen. Keine neuen Schriften, keine neuen Farben ohne ihr Ja.
- **Ein starker Moment schlägt zehn kleine Effekte.** Ein gut gestaffelter Seitenaufbau und eine
  starke erste Bildschirmseite wirken mehr als überall verstreute Spielereien.
- **Nie generische KI-Optik:** keine lila Verläufe auf Weiß, keine austauschbaren Karten-Raster,
  keine Stockfoto-Händeschüttler. Lieber echte Fotos von Sabine und ihrer Arbeit.
- **Rhythmus beim Scrollen:** Abschnitte im Wechsel (hell/dunkel bzw. Fläche/Bild), nicht fünf
  gleiche Blöcke untereinander.
- **„Solide“ ist noch nicht fertig.** Die Seite soll den „will ich jemandem zeigen“-Test bestehen.

## Effekte (alle CSS-first, absturzsicher)

| Effekt | Wirkung | Technik |
|---|---|---|
| Scroll-Reveal | Elemente erscheinen gestaffelt | IntersectionObserver, Startzustand nur unter `.js` verstecken |
| Ken-Burns | langsamer Zoom im Titelbild | `@keyframes` scale 1.04 → 1.12 |
| Parallax | Bild bewegt sich langsamer als die Seite | `translate3d` per `requestAnimationFrame` |
| Zahlen-Zähler | Kennzahl zählt beim Sichtbarwerden hoch | IntersectionObserver + Easing, nur echte Zahlen |
| Hover-Zoom | Bild „atmet“ im Rahmen | `transform:scale` auf `:hover`, `overflow:hidden` |
| Laufband | Begriffe laufen endlos durch | Inhalt einmal klonen, `translateX(-50%)` |
| Text-Schimmer | edler Glanz auf einer Überschrift | `background-clip:text` + animierte Position |

**Immer dabei:** `@media (prefers-reduced-motion: reduce)` schaltet Bewegung ab, Inhalt bleibt sichtbar.
Kein `&` in den Skripten (siehe `SKILL.md`, Falle 1).

## Schriften

Nur über `fonts.bunny.net` (gleiche Syntax wie Google Fonts, ohne Datenübertragung an Google), nur
die Gewichte, die wirklich vorkommen. Neue Schrift nur, wenn Sabine eine neue Marke will.

## Qualitätsschwelle (nicht verhandelbar)

- **Kontrast WCAG AA:** Text ≥ 4,5 : 1, große Schrift ≥ 3 : 1. Messen, nicht schätzen. Markenfarben
  taugen oft nicht als Textfarbe auf hellem Grund: dann eine dunklere Textvariante ableiten.
- **Kein seitliches Überlaufen** bei 360, 390, 768, 1024, 1440, 1920 px.
- **Handy zuerst denken:** Knöpfe, Menü, Kennzahlen-Leisten dürfen nicht umbrechen oder drängeln.
- Genau eine `<h1>`, Überschriften ohne Sprünge, jedes Bild mit `alt`-Text.
- Fotos unter 300 KB (WebP oder JPG, 1920 px breit), als Datei in `bilder/`.

## Echtheit

Nur echte Angaben: Adresse, Telefon, Leistungen, Stimmen, Zahlen kommen von Sabine. Fehlt etwas,
sichtbarer Platzhalter `[TEXT FOLGT: …]`. Auf einer öffentlichen Seite steht nie etwas, das echt
aussieht, aber erfunden ist.
