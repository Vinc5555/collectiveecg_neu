# HRV-Auswertung für collectiveECG-Messungen (Polar H10) mit NeuroKit2
# Spezifikation: doc/lab_internal/SPEC_hrv_auswertung.md
#
# Start (aus dem Projektordner, venv aktiv):
#     python scripts/hrv_auswertung.py
#
# Das Skript fragt nacheinander: Messdatei (Pfeiltasten), Namen der Marker, Intervall.
# Verarbeitung (Resampling, Filtern, R-Zacken, Artefakte) wie in der
# bisherigen auswertung.py (Stand 13.11.2026).
import os
import sys
import glob
import warnings
import numpy as np
import pandas as pd
import neurokit2 as nk
import matplotlib
matplotlib.use("Agg")  # Grafiken nur speichern, kein Fenster öffnen
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline
import questionary  # Auswahl mit Pfeiltasten (Windows und Mac)
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# =====================================================================
# EINSTELLUNGEN – nur bei Bedarf ändern
# =====================================================================
GRENZE_ARTEFAKTE = 5.0      # Hinweis ab diesem Anteil korrigierter Schläge (%)
VALIDIERT_AB_S = 60         # RMSSD erst ab dieser Fensterlänge validiert (Esco & Flatt 2014)
MIN_DAUER_S = 10            # kürzere Fenster -> keine Werte (kürzestes für RMSSD
                            # untersuchte Fenster: 10 s, Muñoz et al. 2015)
MIN_RR = 5                  # technische Absicherung: weniger RR-Intervalle -> keine Werte
MIN_INTERVALL_S = 10        # kleinstes wählbares Intervall (= MIN_DAUER_S)
AUSSCHNITT_S = None         # Start (s) des 10-s-EKG-Ausschnitts; None = Mitte der Messung
STAB_S = 60                 # Stabilisierung nach Marker bzw. Gewöhnungsphase ab Messbeginn (s)
# =====================================================================

FS = 130
PROJEKT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJEKT, "data", "lab_internal", "raw")
OUTPUT_DIR = os.path.join(PROJEKT, "output")  # je Messung ein eigener Unterordner
warnings.filterwarnings("ignore")  # NeuroKit2-Warnungen bei kurzen Fenstern ausblenden


def komma(x):
    """Zahl mit einer Nachkommastelle und deutschem Komma, z. B. 24,7"""
    return f"{x:.1f}".replace(".", ",")


def ja(frage):
    """Enter = ja, n = nein."""
    return input(f"{frage} (Enter = ja, n = nein): ").strip().lower() not in ("n", "nein")


def speichern(schreibe, pfad):
    """Speichert eine Datei. Ist sie gesperrt (z. B. in Excel geöffnet),
    wird gewartet, bis sie geschlossen ist, und erneut versucht."""
    while True:
        try:
            schreibe(pfad)
            return
        except OSError:
            if not sys.stdin.isatty():
                raise
            input(f"\n  {os.path.basename(pfad)} ist geöffnet (z. B. in Excel) – "
                  "bitte schließen und Enter drücken: ")


def frage_zahl(text, minimum, maximum=None):
    """Fragt so lange nach, bis eine gültige ganze Zahl eingegeben wurde."""
    while True:
        eingabe = input(text).strip()
        if eingabe.isdigit():
            zahl = int(eingabe)
            if zahl >= minimum and (maximum is None or zahl <= maximum):
                return zahl
        print("  Ungültige Eingabe, bitte erneut.")


# --- 1. Messdatei auswählen ---
dateien = sorted(glob.glob(os.path.join(RAW_DIR, "*_ecg_*.csv")))
if not dateien:
    raise SystemExit(f"Keine EKG-Dateien in {RAW_DIR} gefunden.")
namen_dateien = [os.path.basename(d) for d in dateien]
DATEI = None
while DATEI is None:
    if sys.stdin.isatty():
        # Pfeiltasten hoch/runter, Enter = auswählen
        wahl = questionary.select("Messung auswählen (↑/↓, Enter):",
                                  choices=namen_dateien).ask()
        if wahl is None:  # Strg+C
            raise SystemExit("Abgebrochen.")
    else:
        # Ersatz ohne Pfeiltasten (z. B. wenn die Eingabe umgeleitet ist)
        print("\nGefundene Messungen:")
        for i, d in enumerate(namen_dateien, start=1):
            print(f"  {i}: {d}")
        wahl = namen_dateien[frage_zahl("Nummer der Messung: ", 1, len(dateien)) - 1]
    if ja(f"Ausgewählt: {wahl} – auswerten?"):
        DATEI = os.path.join(RAW_DIR, wahl)
MESSUNG = os.path.splitext(os.path.basename(DATEI))[0]

# --- 2. Einlesen ---
roh = pd.read_csv(DATEI, header=None)
sensor_ns = roh[0].to_numpy()
marker = roh[2].to_numpy()
ekg_pakete = roh.iloc[:, 3:].to_numpy()

# --- 3. Resampling auf 130 Hz (Sensor-Zeitstempel, Spline) ---
n = ekg_pakete.shape[1]
t_paket = (sensor_ns - sensor_ns[0]) / 1e9
dauer = np.diff(t_paket, prepend=t_paket[0] - (t_paket[1] - t_paket[0]))
t_werte = (t_paket[:, None] - dauer[:, None]
           + dauer[:, None] * np.arange(1, n + 1) / n).ravel()
t_neu = np.arange(t_werte[0], t_werte[-1], 1 / FS)
ekg_130 = CubicSpline(t_werte, ekg_pakete.ravel())(t_neu)
marker_s = t_paket[marker == 1]
# Paketlücke: Abstand zum nächsten Paket > 1,5 x üblicher Abstand
luecke = dauer > 1.5 * np.median(dauer)
luecke[0] = False
luecken_von = t_paket[np.where(luecke)[0] - 1]
luecken_bis = t_paket[luecke]

print(f"\nMessung: {MESSUNG}")
print(f"  Dauer: {komma(t_neu[-1] - t_neu[0])} s ({komma((t_neu[-1] - t_neu[0]) / 60)} min)")
print(f"  Abtastrate geschätzt: {73 / np.mean(np.diff(sensor_ns) / 1e9):.2f} Hz".replace(".", ","))
print(f"  Paketlücken: {int(luecke.sum())}", np.round(luecken_bis, 1) if luecke.any() else "")

# --- 4. Marker benennen (einzeln, danach Kontrolle) ---
marker_namen = []
while len(marker_s):
    print(f"\n{len(marker_s)} Marker gefunden – jetzt einzeln benennen "
          "(Enter = weiter, leer = Marker_1 …)")
    marker_namen = []
    for i, m in enumerate(marker_s, start=1):
        while True:
            name = input(f"  Marker {i} ({komma(m)} s): ").strip()
            if "," in name or ";" in name:
                print("    Bitte ohne , oder ;")
                continue
            marker_namen.append(name if name else f"Marker_{i}")
            break
    for i, name in enumerate(marker_namen, start=1):
        print(f"    Marker {i} = {name}")
    if ja("Passt?"):
        break
if len(marker_s) == 0:
    print("\nKeine Marker gefunden – die ganze Messung ist ein Abschnitt.")

# --- 5. Intervall wählen ---
print(f"\nIntervall in Sekunden (mindestens {MIN_INTERVALL_S}, z. B. 10, 30, 60, 300).")
INTERVALL = frage_zahl("Intervall (s): ", MIN_INTERVALL_S)
if INTERVALL < VALIDIERT_AB_S:
    print(f"  Hinweis: RMSSD unter {VALIDIERT_AB_S} s ist nicht validiert – "
          "die Werte werden in der Spalte 'Hinweis' gekennzeichnet.")

# --- 5b. Stabilisierung nach Markern ---
# j: die ersten STAB_S Sekunden nach Messbeginn und jedem Marker werden eine
#    eigene, rot markierte Zeile; die Intervalle beginnen danach in voller Länge;
#    zusätzlich je Abschnitt "gesamt ab 60 s" (Stabilisierung herausgerechnet).
# n: Intervalle wie bisher; nur die Gewöhnungsphase (erste STAB_S s der Messung)
#    wird immer markiert.
antwort = input(f"\nStabilisierung: die ersten {STAB_S} s nach jedem Marker kennzeichnen? "
                "(j = ja, Empfehlung / n = nein) [j]: ").strip().lower()
STABILISIERUNG = antwort not in ("n", "nein")

# --- 6. Filtern, R-Zacken, Artefaktkorrektur ---
print("\nBerechne ...")
ekg_sauber = nk.ecg_clean(ekg_130, sampling_rate=FS, method="neurokit")
ekg_sauber, invertiert = nk.ecg_invert(ekg_sauber, sampling_rate=FS)
_, info = nk.ecg_peaks(ekg_sauber, sampling_rate=FS, method="neurokit")
peaks_roh = info["ECG_R_Peaks"]
_, peaks = nk.signal_fixpeaks(peaks_roh, sampling_rate=FS, iterative=True, method="Kubios")
peaks = np.asarray(peaks, dtype=int)


def ohne_partner(a, b):
    """Zacken aus a, die in b keinen Partner (Abstand <= 1 Messwert) haben."""
    return np.array([x for x in a if np.min(np.abs(b - x)) > 1], dtype=int)


# Korrigierte Schläge = entfernt, eingefügt oder verschoben; Entfernen und
# Neusetzen desselben Schlags (Abstand < 0,25 s) zählt als ein Schlag.
t_geaendert = np.sort(np.concatenate([t_neu[ohne_partner(peaks_roh, peaks)],
                                      t_neu[ohne_partner(peaks, peaks_roh)]]))
if len(t_geaendert):
    t_art = t_geaendert[np.insert(np.diff(t_geaendert) >= 0.25, 0, True)]
else:
    t_art = t_geaendert
t_peaks = t_neu[peaks]
rr = np.diff(peaks) / FS * 1000
t_rr = t_peaks[1:]


# --- 7. Kennwerte für ein Zeitfenster ---
def kennwerte(start, ende):
    """HR, RMSSD, lnRMSSD und Qualitätsangaben für Schläge in [start, ende)."""
    p = peaks[(t_peaks >= start) & (t_peaks < ende)]
    fdauer = ende - start
    zeile = {"Start_s": round(start, 1), "Ende_s": round(ende, 1),
             "Dauer_s": round(fdauer, 1), "Schlaege": len(p),
             "Artefakte_Prozent": np.nan, "Paketluecke": False,
             "HR_bpm": np.nan, "RMSSD_ms": np.nan, "lnRMSSD": np.nan}
    hinweise = []
    if fdauer < VALIDIERT_AB_S:
        hinweise.append(f"RMSSD < {VALIDIERT_AB_S} s nicht validiert")
    if len(p):
        anteil = 100 * np.sum((t_art >= start) & (t_art < ende)) / len(p)
        zeile["Artefakte_Prozent"] = round(anteil, 1)
        if anteil > GRENZE_ARTEFAKTE:
            hinweise.append(f"Artefakte > {GRENZE_ARTEFAKTE:g} %")
    if fdauer < MIN_DAUER_S - 1e-9:
        hinweise.append(f"zu kurz (< {MIN_DAUER_S} s)")
    elif np.any((luecken_von < ende) & (luecken_bis > start)):
        zeile["Paketluecke"] = True
        hinweise.append("Paketlücke")
    elif len(p) - 1 < MIN_RR:
        hinweise.append("zu wenige Schläge")
    else:
        zeit = nk.hrv_time(p, sampling_rate=FS)
        rmssd = zeit["HRV_RMSSD"].iloc[0]
        zeile["HR_bpm"] = round(60000 / zeit["HRV_MeanNN"].iloc[0], 1)
        zeile["RMSSD_ms"] = round(rmssd, 2)
        zeile["lnRMSSD"] = round(np.log(rmssd), 3)
    return zeile, hinweise


# --- 8. Abschnitte und Intervalle ---
# Zeit 0 = Zeitstempel des ersten Pakets (wie bisher); die wenigen Werte davor
# (< 0,6 s) werden nicht ausgewertet, damit keine negativen Zeiten entstehen.
grenzen = [max(t_neu[0], 0.0)] + list(marker_s) + [t_neu[-1]]
namen = ["Messbeginn"] + marker_namen + ["Messende"]
zeilen = []
for a in range(len(grenzen) - 1):
    a_start, a_ende = grenzen[a], grenzen[a + 1]
    if a_ende - a_start <= 0:
        continue
    abschnitt = f"{namen[a]} -> {namen[a + 1]}"
    basis = {"Messung": MESSUNG, "Abschnitt_Nr": a + 1, "Abschnitt": abschnitt}
    nr_int = 1
    start = a_start
    phase = "Gewöhnungsphase" if a == 0 else "Stabilisierung"
    if STABILISIERUNG:
        # eigene Zeile für die Stabilisierung, Intervalle beginnen danach
        ende = min(a_start + STAB_S, a_ende)
        zeile, hinweise = kennwerte(a_start, ende)
        zeilen.append({**basis, "Zeile": "Stab.", **zeile,
                       "Hinweis": " | ".join([phase] + hinweise)})
        start = ende
    while start < a_ende - 1e-9:
        ende = min(start + INTERVALL, a_ende)
        zeile, hinweise = kennwerte(start, ende)
        if ende - start < INTERVALL - 1e-9:
            hinweise.append(f"unvollständig ({ende - start:.1f} s)".replace(".", ","))
        if not STABILISIERUNG and a == 0 and start < STAB_S:
            hinweise.insert(0, f"enthält Gewöhnungsphase (0–{STAB_S} s)")
        zeilen.append({**basis, "Zeile": str(nr_int), **zeile,
                       "Hinweis": " | ".join(hinweise)})
        nr_int += 1
        start = ende
    zeile, hinweise = kennwerte(a_start, a_ende)
    zeilen.append({**basis, "Zeile": "gesamt", **zeile, "Hinweis": " | ".join(hinweise)})
    if STABILISIERUNG:
        if a_ende - a_start > STAB_S:
            zeile, hinweise = kennwerte(a_start + STAB_S, a_ende)
        else:
            zeile, _ = kennwerte(a_ende, a_ende)  # leere Werte
            zeile.update({"Start_s": round(a_ende, 1), "Dauer_s": 0.0})
            hinweise = ["Abschnitt zu kurz für Stabilisierung"]
            for k in ("HR_bpm", "RMSSD_ms", "lnRMSSD", "Artefakte_Prozent"):
                zeile[k] = np.nan
        zeilen.append({**basis, "Zeile": f"gesamt ab {STAB_S} s", **zeile,
                       "Hinweis": " | ".join(hinweise)})

ergebnis = pd.DataFrame(zeilen)
ergebnis["Intervall_s"] = INTERVALL
ergebnis["Stabilisierung_s"] = STAB_S if STABILISIERUNG else 0
ergebnis["NeuroKit2_Version"] = nk.__version__

# --- 9. Speichern ---
# Ordner je Messung: output/<Messung>/ (CSV, XLSX) und output/<Messung>/plots/ (Bilder)
MESS_DIR = os.path.join(OUTPUT_DIR, MESSUNG)
PLOTS_DIR = os.path.join(MESS_DIR, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

# CSV für Statistik (eine Zeile pro Wert); utf-8-sig, damit Excel Umlaute erkennt
csv_pfad = os.path.join(MESS_DIR, f"{MESSUNG}_hrv_{INTERVALL}s.csv")
if os.path.exists(csv_pfad):
    print(f"  Hinweis: Ergebnisse für {INTERVALL} s werden überschrieben.")
speichern(lambda pfad: ergebnis.to_csv(pfad, index=False, sep=";", decimal=",",
                                       encoding="utf-8-sig"), csv_pfad)

# Excel zum Anschauen: Infoblock links, Tabelle rechts
GRAU = PatternFill("solid", fgColor="D9D9D9")      # Überschriften
HELLGRAU = PatternFill("solid", fgColor="F2F2F2")  # jeder zweite Abschnitt
GELB = PatternFill("solid", fgColor="FFF2CC")      # Zeilen "gesamt"
ROT = PatternFill("solid", fgColor="F8CBAD")       # Stabilisierung / Gewöhnungsphase
FETT = Font(bold=True)
LINIE = Border(top=Side(style="thin", color="808080"))

wb = Workbook()
ws = wb.active
ws.title = "HRV"

# Infoblock (Spalte A): Bezeichnung grau, Wert darunter
start_pc = datetime.fromtimestamp(float(roh[1].iloc[0]))
gesamt_dauer = t_neu[-1] - max(t_neu[0], 0.0)
info = [("Messung", MESSUNG),
        ("Messbeginn", start_pc.strftime("%d.%m.%Y %H:%M:%S")),
        ("Dauer gesamt", f"{int(gesamt_dauer // 60)}:{int(gesamt_dauer % 60):02d} min "
                         f"({komma(gesamt_dauer)} s)"),
        ("Intervall", f"{INTERVALL} s"),
        ("Stabilisierung", f"ja – je {STAB_S} s nach Messbeginn und jedem Marker (rot)"
                           if STABILISIERUNG else
                           f"nein – nur Gewöhnungsphase 0–{STAB_S} s markiert (rot)"),
        ("Marker", [f"{i}: {n} ({komma(m)} s)" for i, (n, m)
                    in enumerate(zip(marker_namen, marker_s), start=1)] or ["keine"]),
        ("Artefakte gesamt", f"{komma(100 * len(t_art) / len(peaks))} % "
                             f"({len(t_art)} von {len(peaks)} Schlägen)"),
        ("Paketlücken gesamt", str(int(luecke.sum()))),
        ("NeuroKit2-Version", nk.__version__),
        ("Ausgewertet am", datetime.now().strftime("%d.%m.%Y %H:%M"))]
z = 1
for titel, wert in info:
    ws.cell(z, 1, titel).font = FETT
    ws.cell(z, 1).fill = GRAU
    z += 1
    for w in (wert if isinstance(wert, list) else [wert]):
        ws.cell(z, 1, w)
        z += 1
    z += 1
ws.column_dimensions["A"].width = 42
ws.column_dimensions["B"].width = 3

# Tabelle ab Spalte C
kopf = ["Abschnitt", "Intervall", "Start_s", "Ende_s", "Dauer_s", "Schlaege",
        "Artefakte_%", "Paketluecke", "HR_bpm", "RMSSD_ms", "lnRMSSD", "Hinweis"]
formate = {"Start_s": "0.0", "Ende_s": "0.0", "Dauer_s": "0.0", "Artefakte_%": "0.0",
           "HR_bpm": "0.0", "RMSSD_ms": "0.00", "lnRMSSD": "0.000"}
breiten = [42, 26, 10, 10, 10, 10, 13, 13, 10, 12, 10, 60]
S0 = 3  # Spalte C
for j, (k, b) in enumerate(zip(kopf, breiten)):
    zelle = ws.cell(1, S0 + j, k)
    zelle.font = FETT
    zelle.fill = GRAU
    ws.column_dimensions[zelle.column_letter].width = b
for i, r in enumerate(ergebnis.itertuples(index=False), start=2):
    erste = (i == 2) or (ergebnis["Abschnitt_Nr"].iloc[i - 3] != r.Abschnitt_Nr)
    werte = [f"{r.Abschnitt_Nr}: {r.Abschnitt}" if erste else None,
             int(r.Zeile) if str(r.Zeile).isdigit() else r.Zeile,
             r.Start_s, r.Ende_s, r.Dauer_s, r.Schlaege, r.Artefakte_Prozent,
             "ja" if r.Paketluecke else "nein", r.HR_bpm, r.RMSSD_ms, r.lnRMSSD, r.Hinweis]
    gesamtzeile = str(r.Zeile).startswith("gesamt")
    rot = r.Zeile == "Stab." or "Gewöhnungsphase" in str(r.Hinweis)
    fuell = (GELB if gesamtzeile else ROT if rot
             else HELLGRAU if r.Abschnitt_Nr % 2 == 0 else None)
    for j, w in enumerate(werte):
        if isinstance(w, float) and np.isnan(w):
            w = None
        zelle = ws.cell(i, S0 + j, w)
        if kopf[j] in formate:
            zelle.number_format = formate[kopf[j]]
        if fuell is not None:
            zelle.fill = fuell
        if gesamtzeile:
            zelle.font = FETT
        if erste:
            zelle.border = LINIE
        if kopf[j] == "Intervall":
            zelle.alignment = Alignment(horizontal="right")
        if kopf[j] == "Paketluecke":
            zelle.alignment = Alignment(horizontal="center")
ws.freeze_panes = "A2"
xlsx_pfad = os.path.join(MESS_DIR, f"{MESSUNG}_hrv_{INTERVALL}s.xlsx")
speichern(lambda pfad: wb.save(pfad), xlsx_pfad)

# Kontrollgrafik: RR-Verlauf gesamt + 10-s-EKG-Ausschnitt mit R-Zacken
aus_start = AUSSCHNITT_S if AUSSCHNITT_S is not None else (t_neu[0] + t_neu[-1]) / 2 - 5
von, bis = np.searchsorted(t_neu, [aus_start, aus_start + 10])
fig, ax = plt.subplots(2, 1, figsize=(11, 6))
ax[0].plot(t_rr, rr, lw=0.8)
for m, name in zip(marker_s, marker_namen):
    ax[0].axvline(m, color="red", ls="--", lw=0.8)
    ax[0].text(m, ax[0].get_ylim()[1], f" {name}", color="red", fontsize=8, va="top")
ax[0].set_title(f"RR-Intervalle – {MESSUNG} (rot = Marker)")
ax[0].set_xlabel("Zeit (s)")
ax[0].set_ylabel("RR (ms)")
sel = peaks[(peaks >= von) & (peaks < bis)]
ax[1].plot(t_neu[von:bis], ekg_sauber[von:bis])
ax[1].plot(t_neu[sel], ekg_sauber[sel], "o", color="red")
ax[1].set_title(f"Erkannte R-Zacken ({aus_start:.0f}–{aus_start + 10:.0f} s)")
ax[1].set_xlabel("Zeit (s)")
ax[1].set_ylabel("µV")
plt.tight_layout()
rz_pfad = os.path.join(PLOTS_DIR, f"{MESSUNG}_rzacken.png")
speichern(lambda pfad: plt.savefig(pfad, dpi=120), rz_pfad)
plt.close()

# Verlaufsgrafik: HR und lnRMSSD je Intervall, Gesamtwert je Abschnitt gestrichelt
iv = ergebnis[~ergebnis["Zeile"].astype(str).str.startswith("gesamt")]
# gestrichelt: Gesamtwert je Abschnitt (bei Stabilisierung: ohne Stabilisierung)
ges_text = f"gesamt ab {STAB_S} s" if STABILISIERUNG else "gesamt"
ges = ergebnis[ergebnis["Zeile"] == ges_text]
# grau hinterlegt: Gewöhnungsphase immer, Stabilisierung nach Markern nur bei j
grau_bereiche = [(max(t_neu[0], 0.0), STAB_S)]
if STABILISIERUNG:
    grau_bereiche += [(m, m + STAB_S) for m in marker_s]
mitte = (iv["Start_s"] + iv["Ende_s"]) / 2
validiert = iv["Dauer_s"] >= VALIDIERT_AB_S
fig, ax = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
for achse, spalte, titel in [(ax[0], "HR_bpm", "HR (bpm)"), (ax[1], "lnRMSSD", "lnRMSSD")]:
    achse.plot(mitte, iv[spalte], color="tab:blue", lw=0.8, alpha=0.6)
    achse.plot(mitte[validiert], iv[spalte][validiert], "o", color="tab:blue", ms=4)
    achse.plot(mitte[~validiert], iv[spalte][~validiert], "o", color="tab:blue",
               ms=4, alpha=0.35)
    for _, g in ges.iterrows():
        achse.hlines(g[spalte], g["Start_s"], g["Ende_s"], color="black", ls="--", lw=1)
    for m in marker_s:
        achse.axvline(m, color="red", ls="--", lw=0.8)
    for von_s, bis_s in grau_bereiche:
        achse.axvspan(von_s, min(bis_s, t_neu[-1]), color="grey", alpha=0.15, lw=0)
    achse.set_ylabel(titel)
for m, name in zip(marker_s, marker_namen):
    ax[0].text(m, ax[0].get_ylim()[1], f" {name}", color="red", fontsize=8, va="top")
hinweis = "" if INTERVALL >= VALIDIERT_AB_S else " – helle Punkte: < 60 s, RMSSD nicht validiert"
ax[0].set_title(f"Verlauf je {INTERVALL} s (gestrichelt = {ges_text.replace('gesamt', 'Gesamtwert')}, "
                f"grau = Gewöhnung/Stabilisierung){hinweis}",
                fontsize=10)
ax[1].set_xlabel("Zeit (s)")
plt.tight_layout()
vl_pfad = os.path.join(PLOTS_DIR, f"{MESSUNG}_verlauf_{INTERVALL}s.png")
speichern(lambda pfad: plt.savefig(pfad, dpi=120), vl_pfad)
plt.close()

# --- 10. Kurzübersicht ---
print(f"\nSignal invertiert (und umgedreht): {invertiert}")
print(f"R-Zacken: {len(peaks)} | korrigiert: {len(t_art)} "
      f"({100 * len(t_art) / len(peaks):.1f} %)")
print("\nGesamtwerte je Abschnitt:")
spalten = ["Abschnitt", "Dauer_s", "Schlaege", "Artefakte_Prozent",
           "HR_bpm", "RMSSD_ms", "lnRMSSD", "Hinweis"]
print(ergebnis[ergebnis["Zeile"].astype(str).str.startswith("gesamt")]
      [["Zeile"] + spalten].to_string(index=False))
print("\nGespeichert:")
for pfad in [csv_pfad, xlsx_pfad, rz_pfad, vl_pfad]:
    print("  " + os.path.relpath(pfad, PROJEKT))
