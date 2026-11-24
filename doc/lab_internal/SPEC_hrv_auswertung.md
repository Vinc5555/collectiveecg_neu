# Spezifikation: HRV-Auswertung in collectiveecg_neu

Stand: 23.11.2026 · Status: freigegeben 23.11.2026, umgesetzt

## 1. Ziel
Ein Skript wertet eine Rohmessung aus `data/lab_internal/raw/` aus und gibt die Hauptkennwerte
der HRV (HR, RMSSD, lnRMSSD) pro Abschnitt zwischen benannten Markern aus - in einem beim Start
frei gewählten Intervall und als Gesamtwert pro Abschnitt. Test mit `1795193269_ecg_test_ecg.csv`.

## 2. Umfang
- **v1 (Muss):** Dateiauswahl, Markerbenennung, Intervallwahl im Terminal; Verarbeitung wie
  bisherige `auswertung.py`; eine CSV; zwei Grafiken; Kennzeichnung nicht validierter Werte.
- **Später:** weitere Kennwerte (SDNN, HF), ACC-Auswertung (Bewegung), Stapelauswertung
  mehrerer Personen, Vergleich mit Kubios.

## 3. Ablauf beim Start (Terminal)
1. Liste aller `*_ecg_*.csv` in `data/lab_internal/raw/` -> Auswahl mit Pfeiltasten (`questionary`,
   Windows und Mac), Enter; danach Bestätigung (Enter = ja, n = zurück zur Liste).
   Ohne Terminal (umgeleitete Eingabe) Ersatz: Auswahl per Nummer.
2. Anzeige: Dauer, Abtastrate, Paketlücken, Anzahl Marker mit Zeitpunkt (s).
3. Hinweis "N Marker gefunden – jetzt einzeln benennen (Enter = weiter, leer = Marker_1 …)",
   dann je Marker eine Eingabe; `,` und `;` werden abgelehnt; Zusammenfassung + "Passt?" (n = neu).
4. Abfrage Intervall in Sekunden (ganze Zahl >= 5; Vorschläge 10, 30, 60, 300).
   Bei < 60 s Hinweis: "RMSSD unter 60 s nicht validiert - Werte werden gekennzeichnet".
5. Verarbeitung, Kurzübersicht der Gesamtwerte im Terminal, Ausgabe der Dateipfade.

## 4. Abschnitte und Intervalle
- Abschnitte: `Messbeginn -> Marker 1`, `Marker 1 -> Marker 2`, ..., `letzter Marker -> Messende`.
  Name z. B. `start_baseline -> ende_baseline`.
- Intervalle beginnen in jedem Abschnitt neu (Marker + 0, + Intervall, ...); kein Intervall
  überschreitet einen Marker.
- Letztes Intervall eines Abschnitts kürzer als gewählt: wird berechnet, Hinweis `unvollständig (x s)`.
- Pro Abschnitt zusätzlich eine Zeile `gesamt` über den ganzen Abschnitt.
- Ein Schlag gehört zu dem Intervall, in dem seine R-Zacke liegt; RR-Intervalle nur innerhalb
  des Intervalls (wie bisher).

## 5. Verarbeitung (unverändert aus auswertung.py, Stand 13.11.2026)
Resampling auf 130 Hz per Spline über Sensor-Zeitstempel (Chung et al. 2026) · Paketlücken-
erkennung (> 1,5 x Median) · `nk.ecg_clean` (neurokit) · `nk.ecg_invert` · `nk.ecg_peaks` ·
`nk.signal_fixpeaks` (Kubios, iterativ; Lipponen & Tarvainen 2019) · Artefaktzählung über
Unterschied erkannte/korrigierte Zacken.

## 6. Kennwerte und Kennzeichnung
- HR (bpm) = 60000 / MeanNN; RMSSD (ms) aus `nk.hrv_time`; lnRMSSD = ln(RMSSD).
- Werte werden immer berechnet, Spalte `Hinweis` markiert (mehrere möglich, mit ` | ` getrennt):
  - `RMSSD < 60 s nicht validiert` (Dauer < 60 s; Esco & Flatt 2014, Muñoz et al. 2015)
  - `Artefakte > 5 %`
  - `Paketlücke` -> HR und RMSSD leer (RR-Intervalle dort falsch)
  - `zu wenige Schläge` (< 5 RR-Intervalle) -> Werte leer
  - `unvollständig (x s)`

## 7. Ausgabe
- CSV `output/stats/<Messung>_hrv_<Intervall>s.csv` (Trennzeichen `;`, Dezimal `,`), Spalten:
  Messung · Abschnitt_Nr · Abschnitt · Zeile (Intervall-Nr oder `gesamt`) · Start_s · Ende_s ·
  Dauer_s · Schlaege · Artefakte_Prozent · Paketluecke · HR_bpm · RMSSD_ms · lnRMSSD · Hinweis ·
  Intervall_s · NeuroKit2_Version
- `output/plots/<Messung>_rzacken.png`: RR-Verlauf gesamt mit Markern + 10-s-EKG-Ausschnitt mit R-Zacken.
- `output/plots/<Messung>_verlauf_<Intervall>s.png`: HR und lnRMSSD je Intervall über die Zeit,
  Marker als beschriftete Linien, Intervalle < 60 s hell dargestellt.
- Bestehende Dateien mit gleichem Namen werden überschrieben (Hinweis im Terminal).

## 7a. Änderung 24.11.2026: Ausgabe je Messung
- Ordner `output/<Messung>/` mit CSV und XLSX, Unterordner `plots/` mit beiden Grafiken.
- CSV unverändert (Spalten wie Abschnitt 7), Kodierung utf-8-sig (Umlaute in Excel korrekt).
- XLSX, ein Blatt "HRV": Infoblock Spalte A (Messung, Messbeginn, Dauer gesamt, Intervall,
  Marker mit Zeit, Artefakte gesamt, Paketlücken gesamt, NeuroKit2-Version, Ausgewertet am);
  Tabelle ab Spalte C: Abschnitt (Nr: Name, nur erste Zeile) · Intervall · Start_s · Ende_s ·
  Dauer_s · Schlaege · Artefakte_% · Paketluecke (ja/nein) · HR_bpm · RMSSD_ms · lnRMSSD · Hinweis.
  Abschnitte abwechselnd weiß/hellgrau, Zeilen "gesamt" hellgelb + fett, Kopfzeile fixiert,
  Zahlenformate 0,0 / RMSSD 0,00 / lnRMSSD 0,000. Paket openpyxl==3.1.5.

## 7b. Änderung 24.11.2026: Stabilisierung
- Abfrage nach dem Intervall: "Stabilisierung: die ersten 60 s nach jedem Marker kennzeichnen? (j/n) [j]".
- j: je Abschnitt zuerst Zeile `Stab.` (60 s ab Messbeginn bzw. Marker; Hinweis "Gewöhnungsphase"
  bzw. "Stabilisierung"), danach Intervalle in voller Länge; zusätzlich Zeile
  `gesamt ab 60 s` (ab +60 s). Abschnitt <= 60 s: Zeile leer, Hinweis
  "Abschnitt zu kurz für Stabilisierung".
- n: Intervalle wie bisher; Intervalle in den ersten 60 s der Messung erhalten Hinweis
  "enthält Gewöhnungsphase (0–60 s)" (immer markiert).
- Excel: Stab.-/Gewöhnungszeilen rot (F8CBAD); Infoblock-Eintrag "Stabilisierung".
- CSV: zusätzliche Spalte `Stabilisierung_s` (60 bzw. 0).
- Verlaufsgrafik: Gewöhnungsphase immer, Stabilisierung bei j grau hinterlegt; gestrichelt
  bei j "gesamt ab 60 s", sonst "gesamt".
- Begründung: Übergänge nach Haltungs-/Bedingungswechsel verfälschen Gesamtwerte (Testmessung
  23.11.: Bewegung lnRMSSD 3,13 mit vs. 2,36 ohne erste Minute); Vorgehen wie Bourdillon et al.
  2017, Blalock et al. 2026 (1 min Stabilisierung).

## 7c. Änderung 24.11.2026: Mindestdauer
- Fenster < 10 s erhalten keine Werte, Hinweis "zu kurz (< 10 s)". Begründung: 10 s ist das
  kürzeste für RMSSD untersuchte Fenster (Muñoz et al. 2015). Kleinstes wählbares Intervall 10 s.
- Zusätzlich technische Absicherung (eigene Annahme, keine Quelle): < 5 RR-Intervalle -> keine Werte.

## 8. Technik
| Bereich | Wahl | Begründung |
| --- | --- | --- |
| Skript | `scripts/hrv_auswertung.py`, eine Datei, Einstellungsblock oben | wie bisher, gut nachvollziehbar |
| Pakete | neue venv; requirements.txt ergänzt: neurokit2==0.3.0, pandas==3.1.1, scikit-learn==1.9.1, PyWavelets==1.10.0, requests==2.34.2 | gleiche Versionen wie alte venv |
| Start | `python scripts/hrv_auswertung.py` aus dem Projektordner | Pfade relativ zum Skript |

## 9. Prüfung (Validierung vor Einsatz)
1. Testmessung mit 10 s und 60 s auswerten, Plausibilität (HR 50-100 bpm in Ruhe, Schlagzahl ~ HR x Dauer).
2. Kontrollrechnung: `gesamt`-Zeilen gleich den Werten der alten `auswertung.py` bei denselben Fenstern.
3. Synthetisches EKG (`nk.ecg_simulate`, bekannte HR) -> HR muss getroffen werden.
4. Künstliche Paketlücke (wie `mach_luecken.py`) -> Intervall wird erkannt und leer gesetzt.

## 9a. Prüfergebnisse (23.11.2026)
- Testmessung 1795193269: 0 Paketlücken, 1 korrigierter Schlag (0,5 %), HR 59,7–66,3 bpm.
- Gegenrechnung alte auswertung.py, gleiche Fenster: HR, RMSSD, lnRMSSD und Schlagzahl identisch.
- Synthetisches EKG (HR 70): HR 70,1–70,2 bpm erkannt.
- Künstliche Paketlücke bei 84,8 s: erkannt, betroffene Zeilen leer + Hinweis.
- Zeit 0 = Zeitstempel des ersten Pakets; die < 0,6 s davor werden nicht ausgewertet.

- Änderung 23.11.2026: Pfeiltasten-Auswahl und klarere Markerbenennung, getestet (Pseudo-Terminal).

## 10. Annahmen
- Mindestintervall 10 s (Muñoz 2015), Empfehlung >= 60 s; MIN_RR = 5 als technische Absicherung (eigene Annahme).
- Grenze 5 % Artefakte wie bisher (mit Betreuung festlegen).
- README wird um Abschnitt "Auswertung" ergänzt.

## 11. Offene Punkte
- keine
