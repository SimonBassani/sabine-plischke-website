---
name: neue-seite
description: Legt eine neue Unterseite der Website von Sabine Hoeppner-Plischke an (z. B. Über mich, Angebot, Leistungen, Kontakt, Impressum, Datenschutz, Landingpage), im Design der Startseite, mit Menüeintrag, als passwortgeschützte Vorschau in WordPress. IMMER nutzen bei "/neue-seite", "neue Seite", "Unterseite", "Seite für mein Angebot", "Impressum anlegen", "Landingpage für …", "füg eine Seite hinzu".
---

# Neue Unterseite

Voraussetzung: Die Startseite ist importiert (`site/design.css` ist befüllt). Lies vorher
`.claude/skills/wordpress/references/gestaltung.md` (Maßstab für das Aussehen) und den
Skill `wordpress`.

## 1. Klären (kurz, im Gespräch)

- **Wofür ist die Seite?** Wer soll sie lesen, und was soll die Person danach tun (Termin buchen,
  Anfrage schicken, etwas herunterladen, nur informieren)?
- **Titel** und **Adresse** vorschlagen, Sabine bestätigt: Kleinbuchstaben, Bindestriche, ohne
  Umlaute (`ueber-mich`, `angebot`, `kontakt`). Unterseite einer anderen? (`--eltern`)
- **Texte:** Sabine liefert sie (Datei, Chat, Notiz). Fehlt etwas: Platzhalter `[TEXT FOLGT: …]`
  mit kurzer Angabe, was dort hingehört. Keine Texte, Zahlen, Stimmen oder Lebenslauf-Details erfinden.
  Bietet sie an, dass du einen Entwurf schreibst: als Entwurf kennzeichnen und von ihr freigeben lassen.
- **Bilder:** welche, und liegen sie vor? Nach `bilder/` (klein, ohne Leerzeichen), Fotos unter 300 KB.
- **Ins Menü?** Impressum und Datenschutz gehören in den Fuß, nicht ins Hauptmenü.

## 2. Anlegen

```bash
python3 tools/wp.py neu <slug> --titel "<Titel>"           # optional: --eltern angebot
```

Dann `seiten/<slug>/inhalt.html` schreiben:

- **Bausteine der Startseite wiederverwenden.** Erst `seiten/start/inhalt.html` und
  `site/design.css` ansehen (nur die Abschnitte, die du brauchst, große Dateien nicht ganz lesen):
  Welche Klassen gibt es für Abschnitte, Überschriften, Karten, Knöpfe, Zitate, Bild-Text-Wechsel?
  Genau diese Klassen nehmen. So sieht die Unterseite automatisch aus wie die Startseite.
- Neue Gestaltung nur, wenn kein vorhandener Baustein passt. Dann in `seiten/<slug>/seite.css`, mit
  den vorhandenen Farben und Schriften (CSS-Variablen aus `design.css`), keine neuen Schriften.
- Genau eine `<h1>`. Danach `<h2>`, `<h3>` ohne Sprünge.
- Interne Links `href="seite:<slug>"`, Bilder `src="bilder/<datei>"` mit sinnvollem `alt`-Text.
- JavaScript nur wenn nötig, in `seiten/<slug>/seite.js`, **ohne `&`**.
- In `seite.json` `beschreibung` setzen (120 bis 158 Zeichen, was Besucher hier finden; für Google).

**Impressum und Datenschutz:** keine Texte erfinden oder aus Vorlagen zusammenstellen. Sabine liefert
die Angaben (Name, Anschrift, Kontakt, USt-IdNr., ggf. Kammer und Berufsrecht) bzw. einen
Generator-Text (in Deutschland Impressum nach § 5 DDG, z. B. über e-recht24 oder die IT-Recht Kanzlei). Die Datenschutzerklärung muss Bunny Fonts und alle
eingebundenen Dienste nennen. Im Zweifel: Simon.

## 3. Menü

Link in `site/kopf.html` (und/oder `site/fuss.html`) ergänzen, im Stil der bestehenden Links:
`<a href="seite:<slug>">Titel</a>`. Gibt es ein Handy-Menü als eigenes Element, dort auch.
Springen bestehende Menüpunkte zu Abschnitten der Startseite (`#angebot`), jetzt auf
`seite:start#angebot` umstellen, damit sie auch von der neuen Seite aus funktionieren.

## 4. Bauen, ansehen, hochladen

```bash
python3 tools/wp.py bauen          # alle Seiten, weil sich Kopf/Fuß geändert haben
```

`dist/<slug>.vorschau.html` lokal mit Playwright ansehen (`python3 tools/wp.py server` im
Hintergrund), Desktop und Handy. Passt es zur Startseite? Dann:

```bash
python3 tools/wp.py push --alle    # Menü ist auf allen Seiten neu
```

Ist eine Seite schon live, verlangt `push` `--ja-live`. Will Sabine die neue Seite online haben,
ist das ihr Ja: `push --alle --ja-live`, neue Seite `live <slug> --ja`.

## 5. Prüfen, zeigen, speichern

Verifikationsprotokoll aus dem Skill `wordpress` auf der neuen Seite und stichprobenhaft auf der
Startseite (Menü!). Sabine Link und kurze Zusammenfassung geben, offene Platzhalter nennen.

```bash
git add -A && git commit -m "Neue Seite: <Titel>" && git push
```
