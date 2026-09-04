"""
fitness_calc.py
---------------
Calcoli "matematici" di fitness/antropometria, centralizzati e riutilizzabili
da più schermate (Profilo & Nutrizione, allenamento attivo, statistiche).

Include:
- Stima del massimale (1RM): Epley e Brzycki
- BMI e classificazione
- Metabolismo basale (BMR) con Mifflin-St Jeor
- Dispendio energetico totale (TDEE) e calorie target per fase
- Fase di ricomposizione (Cut / Bulk / Maintenance)
- Frequenza settimanale e streak di settimane consecutive
- Volume settimanale di allenamento
- Rapporto forza / peso corporeo
"""

from datetime import date, datetime, timedelta

# ----------------------------------------------------------------------------
# Massimale teorico (1RM)
# ----------------------------------------------------------------------------

def epley_1rm(peso: float, reps: int) -> float:
    """Stima 1RM con la formula di Epley: peso * (1 + reps/30)."""
    try:
        reps = min(max(int(reps), 1), 30)
        return round(float(peso) * (1 + reps / 30), 1)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def brzycki_1rm(peso: float, reps: int) -> float:
    """Stima 1RM con la formula di Brzycki: peso * 36 / (37 - reps)."""
    try:
        reps = min(max(int(reps), 1), 35)
        return round(float(peso) * 36 / (37 - reps), 1)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def stima_1rm(peso: float, reps: int) -> float:
    """Stima 1RM media (Epley + Brzycki) per un risultato più stabile."""
    e = epley_1rm(peso, reps)
    b = brzycki_1rm(peso, reps)
    if e and b:
        return round((e + b) / 2, 1)
    return max(e, b)


# ----------------------------------------------------------------------------
# BMI e classificazione
# ----------------------------------------------------------------------------

def bmi(peso_kg: float, altezza_cm: float) -> float:
    """Indice di Massa Corporea: peso(kg) / altezza(m)^2."""
    try:
        h_m = float(altezza_cm) / 100.0
        if h_m <= 0:
            return 0.0
        return round(float(peso_kg) / (h_m * h_m), 1)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def bmi_category(bmi_value: float) -> str:
    """Classificazione automatica del BMI."""
    if bmi_value < 18.5:
        return "Sottopeso"
    if bmi_value < 25:
        return "Normopeso"
    if bmi_value < 30:
        return "Sovrappeso"
    return "Obesità"


def fase_ricomposizione(peso_attuale: float, peso_obiettivo: float) -> str:
    """Stabilisce la fase: CUT se target<attuale, BULK se >, MAINTENANCE se =."""
    try:
        if peso_obiettivo < peso_attuale:
            return "CUT"
        if peso_obiettivo > peso_attuale:
            return "BULK"
        return "MAINTENANCE"
    except TypeError:
        return "MAINTENANCE"


# ----------------------------------------------------------------------------
# Calorie (Mifflin-St Jeor)
# ----------------------------------------------------------------------------

def bmr_mifflin(peso_kg: float, altezza_cm: float, eta: int, sesso: str) -> float:
    """Metabolismo basale (BMR) con la formula di Mifflin-St Jeor."""
    try:
        base = (10 * float(peso_kg)) + (6.25 * float(altezza_cm)) - (5 * int(eta))
        if str(sesso).lower().startswith("f"):
            return round(base - 161, 0)
        return round(base + 5, 0)
    except (TypeError, ValueError):
        return 0.0


def attivita_multiplier(frequenza_settimanale: int) -> float:
    """Fattore di attività in base alla frequenza di allenamento settimanale."""
    f = int(frequenza_settimanale or 0)
    if f <= 0:
        return 1.2
    if f <= 2:
        return 1.375
    if f <= 4:
        return 1.55
    if f <= 6:
        return 1.725
    return 1.9


def tdee(bmr: float, frequenza_settimanale: int) -> float:
    """Dispendio energetico totale = BMR * fattore di attività."""
    return round(float(bmr) * attivita_multiplier(frequenza_settimanale), 0)


def calorie_target(tdee_value: float, fase: str) -> dict:
    """Calorie raccomandate in base alla fase di ricomposizione."""
    td = float(tdee_value)
    if fase == "CUT":
        return {
            "fase": fase,
            "min": round(td - 500, 0),
            "max": round(td - 300, 0),
            "nota": "Deficit calorico controllato (-300/-500 kcal)",
        }
    if fase == "BULK":
        return {
            "fase": fase,
            "min": round(td + 300, 0),
            "max": round(td + 500, 0),
            "nota": "Surplus calorico pulito (+300/+500 kcal)",
        }
    return {
        "fase": "MAINTENANCE",
        "min": round(td, 0),
        "max": round(td, 0),
        "nota": "Mantenimento: calorie pari al TDEE",
    }


# ----------------------------------------------------------------------------
# Statistiche settimanali / streak
# ----------------------------------------------------------------------------

def _parse_data(d_str: str) -> date:
    """Converte una data 'gg/mm/aaaa' (o 'aaaa-mm-gg') in un oggetto date."""
    if not d_str:
        return datetime.min.date()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(d_str, fmt).date()
        except ValueError:
            continue
    return datetime.min.date()


def frequenza_settimana_corrente(storico: list) -> int:
    """Numero di allenamenti completati nella settimana ISO corrente."""
    oggi = date.today()
    # lunedì della settimana corrente
    lunedi = oggi - timedelta(days=oggi.weekday())
    dom = lunedi + timedelta(days=6)
    return sum(1 for s in storico if lunedi <= _parse_data(s.get("data")) <= dom)


def settimane_attive(storico: list) -> set:
    """Insieme di 'chiavi' della settimana ISO in cui c'è almeno un allenamento."""
    settimane = set()
    for s in storico:
        d = _parse_data(s.get("data"))
        if d == datetime.min.date():
            continue
        iso = d.isocalendar()
        settimane.add((iso[0], iso[1]))
    return settimane


def streak_settimane_consecutive(storico: list, target_settimanale: int) -> int:
    """Numero di settimane consecutive (fino alla più recente con allenamenti)
    in cui sono stati completati almeno `target_settimanale` allenamenti.

    Il conteggio parte dalla settimana più recente in cui c'è almeno un
    allenamento e procede a ritroso: se una settimana non raggiunge il target
    o manca del tutto (buco temporale), la streak si interrompe."""
    target = int(target_settimanale or 0)

    # Raggruppa per lunedì di ogni settimana con almeno un allenamento.
    per_lunedi = {}
    for s in storico:
        d = _parse_data(s.get("data"))
        if d == datetime.min.date():
            continue
        lunedi = d - timedelta(days=d.weekday())
        per_lunedi.setdefault(lunedi, 0)
        per_lunedi[lunedi] += 1

    if not per_lunedi:
        return 0

    # Parti dal lunedì più recente che ha allenamenti.
    cursore = max(per_lunedi)
    streak = 0
    for _ in range(len(per_lunedi) + 1):
        if cursore in per_lunedi and per_lunedi[cursore] >= target:
            streak += 1
        else:
            break
        cursore -= timedelta(days=7)
    return streak


def volume_settimanale(storico: list, mode: str = "kg") -> list:
    """Ritorna una lista di tuple (chiave_settimana, valore) per l'ultima
    parte dello storico, dove il valore è il volume in kg oppure il numero
    di serie totali, aggregato per settimana ISO.

    mode: 'kg' (volume totale) oppure 'serie' (numero serie totali).
    """
    aggregato = {}
    for s in storico:
        d = _parse_data(s.get("data"))
        if d == datetime.min.date():
            continue
        iso = d.isocalendar()
        key = (iso[0], iso[1])
        agg = aggregato.setdefault(key, {"kg": 0.0, "serie": 0})
        for ex in s.get("esercizi", []):
            for serie in ex.get("serie_svolte", []):
                if not serie.get("completata"):
                    continue
                agg["serie"] += 1
                peso = float(serie.get("peso", 0) or 0)
                reps = int(serie.get("reps", 0) or 0)
                agg["kg"] += peso * reps

    ordinate = sorted(aggregato.items())
    # Prendi solo le ultime 12 settimane per non affollare il grafico
    ordinate = ordinate[-12:]

    if mode == "serie":
        return [(k, v["serie"]) for k, v in ordinate]
    return [(k, round(v["kg"], 0)) for k, v in ordinate]


def volume_sessione(sessione: dict) -> float:
    """Ritorna il volume (in kg) di una singola sessione = somma di peso x reps."""
    tot = 0.0
    for ex in sessione.get("esercizi", []):
        for serie in ex.get("serie_svolte", []):
            if not serie.get("completata"):
                continue
            try:
                tot += float(serie.get("peso", 0) or 0) * int(serie.get("reps", 0) or 0)
            except (TypeError, ValueError):
                pass
    return round(tot, 0)


def settimana_label(iso_key) -> str:
    """Etichetta leggibile per una chiave settimana ISO, es. 'W32'."""
    anno, sett = iso_key
    return f"W{sett}"


def forza_peso_ratio(pr_peso: float, peso_corporeo: float) -> float:
    """Rapporto forza/peso corporeo (es. 1.5 = 1.5x il peso corporeo)."""
    try:
        if float(peso_corporeo) <= 0:
            return 0.0
        return round(float(pr_peso) / float(peso_corporeo), 2)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0
