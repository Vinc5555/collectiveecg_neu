# collectiveECG – aufgeräumte Version

EKG- und Beschleunigungsdaten vom Polar H10 per Bluetooth aufnehmen und Marker setzen.
Funktion unverändert gegenüber dem Original `collectiveecg`; nur die Ordner sind neu sortiert.

## Ordner

```
collectiveecg_neu/
├── scripts/                 # alles, was gestartet wird
│   ├── heart_sync/          #   Aufnahme (heart_sync.py) + Hilfsskripte
│   ├── trigger_sender.py    #   Marker setzen / Aufnahme stoppen
│   ├── ecg_visualiser.py    #   Live-Anzeige (optional)
│   ├── start_experiment.py  #   Logs vor neuem Versuchstag zurücksetzen (optional)
│   └── hrv_auswertung.py    #   HRV-Auswertung (HR, RMSSD, lnRMSSD)
├── materials/lab_internal/config/
│   ├── polar_config.csv     # aktive Config (Gurt P01)
│   └── alt/                 # Original-Configs der Forschungsgruppe
├── data/lab_internal/
│   ├── raw/                 # hier landen die Messungen (_ecg_ und _acc_)
│   └── logs/                # experiment.log, streaming.csv
├── output/
│   └── <Messung>/           # je Messung: CSV + Excel, Unterordner plots/ mit Grafiken
├── doc/
│   ├── public/              # Original-Doku collectiveECG
│   └── lab_internal/        # eigene Notizen
└── extras/                  # unter Windows nicht genutzt: Linux-Shellskripte, Android
```

## Einmalig: Umgebung einrichten (PowerShell)

```powershell
cd <Pfad zu>\collectiveecg_neu
py -3.12 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Messung (immer aus diesem Ordner, venv aktiv)

Fenster 1 – Aufnahme starten (bleibt während der ganzen Messung offen):

```powershell
python scripts/heart_sync/heart_sync.py -c materials/lab_internal/config/polar_config.csv -p P01
```

Fenster 2 – Marker setzen:

```powershell
python scripts/trigger_sender.py -c materials/lab_internal/config/polar_config.csv -p P01
```

Fenster 2 – Aufnahme stoppen:

```powershell
python scripts/trigger_sender.py -c materials/lab_internal/config/polar_config.csv -p P01 -q
```

Ergebnis: `data/lab_internal/raw/<Unixzeit>_ecg_<OUTPUT_FILE>` und `..._acc_...`.
Dateiname (`OUTPUT_FILE`) und Gurt-Seriennummer stehen in `polar_config.csv`.

## Auswertung (HRV)

```powershell
python scripts/hrv_auswertung.py
```

Das Skript fragt nacheinander:
1. Messung (Liste aus `data/lab_internal/raw/`, mit ↑/↓ wählen, Enter, dann Enter zum Bestätigen)
2. Namen der Marker, einzeln nacheinander (leer = `Marker_1`, `Marker_2`, ...), danach Kontrolle
3. Intervall in Sekunden (z. B. 10, 30, 60, 300)

Ergebnis im Ordner `output/<Messung>/`:
- `<Messung>_hrv_<Intervall>s.csv` – eine Zeile pro Wert, für Statistik und Zusammenführen
- `<Messung>_hrv_<Intervall>s.xlsx` – formatierte Übersicht: Infoblock + Tabelle je Abschnitt mit Intervallen und Zeile `gesamt`
- `plots/<Messung>_rzacken.png` – Kontrolle der R-Zacken
- `plots/<Messung>_verlauf_<Intervall>s.png` – HR und lnRMSSD über die Zeit

Spalte `Hinweis`: `RMSSD < 60 s nicht validiert`, `Artefakte > 5 %`, `Paketlücke` (Werte leer),
`zu wenige Schläge` (Werte leer), `unvollständig (x s)`. Für Aussagen den Wert `gesamt` bzw.
Intervalle ≥ 60 s verwenden. Details: `doc/lab_internal/SPEC_hrv_auswertung.md`.

## Änderungen gegenüber dem Original

| Datei | Änderung |
| --- | --- |
| `heart_sync.py` | Messungen nach `data/lab_internal/raw/`, Logs nach `data/lab_internal/logs/`; Uhrzeit im Log 24-h statt 12-h; Timer-Anzeige im Terminal (Aufnahmedauer, Anzahl Marker, letzter Marker); Meldung beim Marker korrigiert (Original: „received message - stopping stream“) |
| `trigger_sender.py` | Log nach `data/lab_internal/logs/`; vertauschte Log-Texte korrigiert (Marker = „trigger“, Stopp = „quit trigger“); 24-h-Uhrzeit |
| `ecg_visualiser.py` | liest `streaming.csv` aus `data/lab_internal/logs/` |
| `start_experiment.py` | gleiche Pfade; Datumsformat korrigiert (`%m` = Monat statt `%M` = Minute) |
| `new_config.csv` | umbenannt in `polar_config.csv` |

Datenformat, Messablauf und Befehlsoptionen sind unverändert.

## Hinweise

- Zeitstempel: Das Original-README empfiehlt, in bleakheart einen Zeit-Offset zu entfernen. Das ist in der genutzten venv nicht geschehen. Der Offset ist konstant; Abstände zwischen Schlägen (und damit HRV) stimmen.
- `pyproject.toml`/`setup.py` sind unverändert übernommen. `pip install .` wird nicht benötigt, die Skripte werden direkt gestartet.
- `extras/linux_shell/runner.py` verweist auf nicht vorhandene Dateien (`collectiveHeart.py`, `parameters.csv`) und ist nur archiviert.
- Lizenz: Mozilla Public License 2.0 (`LICENSE`), Autoren in `AUTHORS`.
