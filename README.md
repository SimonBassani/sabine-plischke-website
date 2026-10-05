# Website Sabine Hoeppner-Plischke

Deine Website, so aufgesetzt, wie Simon (DigiUp) seine eigene betreibt. Hier liegen alle Seiten als
Dateien, und Claude Code schickt sie in dein WordPress. Du sagst Claude in normalen Sätzen, was du willst („mach die
Überschrift größer“, „neue Seite für mein Angebot“), Claude baut es, prüft es und zeigt dir eine
geschützte Vorschau. Öffentlich wird erst etwas, wenn du ausdrücklich Ja sagst.

Eingerichtet von Simon Bassani, DigiUp Consulting (office@digi-up.at).

## Loslegen (einmalig)

**1. Terminal öffnen** (Mac: ⌘ + Leertaste, „Terminal“ tippen, Enter), diese Zeile hineinkopieren, Enter:

```bash
cd ~/Documents && git clone https://github.com/SimonBassani/sabine-plischke-website.git && cd sabine-plischke-website && claude
```

Claude startet im richtigen Ordner. Fragt es, ob es dem Ordner vertrauen und den Browser-Helfer
„playwright“ nutzen darf: beides mit Ja bestätigen.

**2. Diesen Text in Claude einfügen**, deine Adresse eintragen und deine `index.html` mit ins
Fenster ziehen (Bilder, die nicht in der Datei stecken, gleich mit):

```
/erster-durchgang
Hier ist meine Website-Datei (index.html, siehe Anhang).
Meine WordPress-Adresse: https://
Übernimm meine index.html genau so, wie sie ist, mit allen Effekten, und veröffentliche sie auf
meiner WordPress-Seite. Ändere nichts an Texten, Design oder Effekten. Wenn technisch etwas nicht
klappt, such selbst nach einer Lösung. Deine Fragen und Vorschläge bitte erst, wenn die Seite online ist.
```

Claude richtet alles ein. Einmal brauchst du deinen WordPress-Login: Claude zeigt dir Schritt für
Schritt, wie du einen Zugangsschlüssel („Anwendungspasswort“) anlegst. Danach läuft es von allein,
bis die Seite online ist, und dann kommen Claudes Fragen.

**Später** einfach im Terminal `cd ~/Documents/sabine-plischke-website && claude` und schreiben, was
du möchtest.

## Die Befehle

| Tippe | Was passiert |
|---|---|
| `/erster-durchgang` | Start: deine index.html 1:1 übernehmen und veröffentlichen, danach Fragen |
| `/einrichten` | nur die Einrichtung, z. B. auf einem neuen Rechner |
| `/importieren` | Deine index.html wird zur WordPress-Seite und als geschützte Vorschau hochgeladen |
| `/neue-seite` | Neue Unterseite im gleichen Design, mit Menüeintrag |
| `/veroeffentlichen` | Seiten öffentlich schalten; Relaunch der ganzen Website (mit Simon) |

Du kannst aber auch einfach schreiben, was du möchtest:

- „Zeig mir die Vorschau der Startseite.“
- „Tausch auf der Startseite das Foto gegen dieses hier aus.“ (Bild ins Fenster ziehen)
- „Der zweite Absatz unter ‚Über mich‘ soll so lauten: …“
- „Leg eine Seite für mein neues Angebot an, die Texte schicke ich dir gleich.“
- „Was hat Simon zuletzt geändert?“

## So ist es abgesichert

- **Vorschau zuerst:** Neue und geänderte Seiten sind mit einem Vorschau-Passwort geschützt. Das
  steht in deiner Datei `.env` (Eintrag `VORSCHAU_PASSWORT`), Claude sagt dir, wo.
- **Deine alte Website bleibt**, bis wir gemeinsam umstellen.
- **Zugangsdaten bleiben auf deinem Rechner** (Datei `.env`). Sie werden nie zu GitHub hochgeladen.
  Den WordPress-Schlüssel kannst du jederzeit unter Benutzer → Profil → Anwendungspasswörter löschen.
- **Jeder Stand ist gespeichert:** Jede Änderung landet mit einer kurzen Beschreibung auf GitHub.
  Simon und du arbeitet so am selben Stand, und jede frühere Fassung lässt sich zurückholen.

## Für Claude und für Simon

Arbeitsregeln: [`CLAUDE.md`](CLAUDE.md). Fachwissen und Prüfprotokoll:
[`.claude/skills/wordpress/SKILL.md`](.claude/skills/wordpress/SKILL.md). Werkzeug:
`python3 tools/wp.py -h` (nur Python-Standardbibliothek; Node.js optional für die Skript-Prüfung).
