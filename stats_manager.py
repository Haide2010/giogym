"""
stats_manager.py
------------------
Calcola statistiche aggregate sullo storico allenamenti, da mostrare
come cruscotto rapido in Home: allenamenti di questo mese/settimana,
streak di settimane consecutive allenate, volume totale della settimana
corrente, e un controllo per avvisare se la scheda non viene rivista
da troppo tempo (utile per ricordare la periodizzazione).
"""

from datetime import datetime, date, timedelta

SETTIMANE_AVVISO_SCHEDA = 6  # dopo quante settimane senza modifiche avvisare


def _parse_date(d_str: str):
    try:
        return datetime.strptime(d_str, "%d/%m/%Y").date()
    except (ValueError, TypeError):
        return None


def _sessioni_con_data(storico: list):
    """Ritorna lista di tuple (date, sessione) per le sessioni con data valida."""
    risultato = []
    for s in storico:
        d = _parse_date(s.get("data", ""))
        if d:
            risultato.append((d, s))
    return risultato


def compute_home_stats(storico: list, oggi: date = None) -> dict:
    """Ritorna un dizionario con le statistiche da mostrare in Home:
    {
        "allenamenti_mese": int,
        "allenamenti_settimana": int,
        "streak_settimane": int,
        "volume_settimana": float,
    }
    """
    oggi = oggi or date.today()
    sessioni = _sessioni_con_data(storico)

    inizio_settimana = oggi - timedelta(days=oggi.weekday())  # lunedì corrente
    fine_settimana = inizio_settimana + timedelta(days=6)

    allenamenti_mese = sum(1 for d, _ in sessioni if d.year == oggi.year and d.month == oggi.month)
    sessioni_settimana = [(d, s) for d, s in sessioni if inizio_settimana <= d <= fine_settimana]
    allenamenti_settimana = len(sessioni_settimana)

    volume_settimana = 0.0
    for _, s in sessioni_settimana:
        for ex in s.get("esercizi", []):
            for serie in ex.get("serie_svolte", []):
                if serie.get("completata"):
                    peso = float(serie.get("peso", 0) or 0)
                    reps = int(serie.get("reps", 0) or 0)
                    volume_settimana += peso * reps

    streak = _compute_streak_settimane(sessioni, oggi)

    return {
        "allenamenti_mese": allenamenti_mese,
        "allenamenti_settimana": allenamenti_settimana,
        "streak_settimane": streak,
        "volume_settimana": round(volume_settimana, 1),
    }


def _compute_streak_settimane(sessioni: list, oggi: date) -> int:
    """Conta quante settimane consecutive (a partire da questa, andando
    indietro) contengono almeno un allenamento. Se questa settimana non
    ha ancora allenamenti ma quella scorsa sì, la streak riparte da
    quella scorsa (non penalizza chi non si è ancora allenato oggi)."""
    settimane_allenate = set()
    for d, _ in sessioni:
        lunedi = d - timedelta(days=d.weekday())
        settimane_allenate.add(lunedi)

    if not settimane_allenate:
        return 0

    lunedi_corrente = oggi - timedelta(days=oggi.weekday())

    # Se questa settimana non ha ancora allenamenti, si parte a
    # contare da quella precedente (altrimenti la streak sembrerebbe
    # sempre a zero il lunedì mattina).
    cursore = lunedi_corrente if lunedi_corrente in settimane_allenate else lunedi_corrente - timedelta(days=7)

    streak = 0
    while cursore in settimane_allenate:
        streak += 1
        cursore -= timedelta(days=7)

    return streak


def scheda_da_rivedere(scheda: dict, oggi: date = None) -> dict:
    """Controlla da quanto tempo la scheda non viene aggiornata.
    Ritorna { "avviso": bool, "settimane": int|None }."""
    oggi = oggi or date.today()
    aggiornata_il = scheda.get("aggiornata_il")
    if not aggiornata_il:
        return {"avviso": False, "settimane": None}

    d = _parse_date(aggiornata_il)
    if not d:
        return {"avviso": False, "settimane": None}

    settimane = (oggi - d).days // 7
    return {"avviso": settimane >= SETTIMANE_AVVISO_SCHEDA, "settimane": settimane}
