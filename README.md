# Website Sabine Hoeppner-Plischke

Deine Website, so aufgesetzt, wie Simon (DigiUp) seine eigene betreibt. Hier liegen alle Seiten als
Dateien, und Claude Code schickt sie in dein WordPress. Du sagst Claude in normalen Sätzen, was du willst („mach die
Überschrift größer“, „neue Seite für mein Angebot“), Claude baut es, prüft es und zeigt dir eine
geschützte Vorschau. Öffentlich wird erst etwas, wenn du ausdrücklich Ja sagst.

Eingerichtet von Simon Bassani, DigiUp Consulting (office@digi-up.at).

## Loslegen (einmalig, ca. 15 Minuten)

**1. GitHub-Einladung annehmen.** Du bekommst eine E-Mail von GitHub, „Accept invitation“ klicken.
Noch kein GitHub-Konto? Kostenlos auf github.com anlegen und Simon deinen Benutzernamen schicken.

**2. Claude Code öffnen.** Entweder im Terminal `claude` eintippen oder in der Claude-App den
Bereich „Code“ öffnen.

**3. Dieses Projekt holen.** Schreib Claude:

> Hol dir bitte https://github.com/SimonBassani/sabine-plischke-website in meinen Ordner
> Dokumente und sag mir, wie ich das Projekt dann öffne.

Oder selbst im Terminal:

```bash
cd ~/Documents
git clone https://github.com/SimonBassani/sabine-plischke-website.git
cd sabine-plischke-website
claude
```

Wichtig: Claude muss **im Ordner `sabine-plischke-website`** gestartet sein, sonst kennt es die
Befehle unten nicht. Beim ersten Start fragt Claude, ob es dem Ordner vertrauen und den
Browser-Helfer „playwright“ nutzen darf: beides mit Ja bestätigen.

**4. Startassistent.** Tippe:

```
/einrichten
```

Claude führt dich durch alles Weitere: Zugangsschlüssel für WordPress anlegen, Verbindung testen,
deine `index.html` übernehmen. Danach geht es mit `/importieren` weiter.

## Die Befehle

| Tippe | Was passiert |
|---|---|
| `/einrichten` | Startassistent (einmalig, oder auf einem neuen Rechner) |
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
