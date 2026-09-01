"""
pr_manager.py
--------------
Calcola e tiene traccia dei Record Personali (PR) per ogni esercizio,
analizzando lo storico degli allenamenti salvato in data_manager.

Per ogni esercizio vengono tracciati 3 tipi di record:
- max_peso: il peso più alto mai sollevato in una singola serie completata
- max_reps: il maggior numero di ripetizioni fatte in una singola serie
  completata (a parità di peso più alto, se possibile)
- max_volume: il volume più alto (somma peso*reps di tutte le serie
  completate) in una singola sessione, per quell'esercizio
- stima_1rm: la stima del massimale (1 ripetizione) più alta mai raggiunta,
  calcolata con la formula di Epley: peso * (1 + reps/30)

Questi record vengono anche usati per rilevare "nuovi PR" appena
conclusa una sessione di allenamento (badge celebrativo).
"""

from typing import Optional


def _epley_1rm(peso: float, reps: int) -> float:
    """Stima del massimale (1RM) con la formula di Epley."""
    try:
        return round(float(peso) * (1 + float(reps) / 30), 1)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


def compute_all_prs(storico: list) -> dict:
    """Analizza l'intero storico e ritorna un dizionario:
    { nome_esercizio: {
        "max_peso": float, "max_peso_data": str,
        "max_reps": int, "max_reps_data": str,
        "max_volume": float, "max_volume_data": str,
        "stima_1rm": float, "stima_1rm_data": str,
    } }
    Solo le serie marcate come "completata" vengono considerate.
    """
    prs: dict = {}

    for sessione in storico:
        data_sessione = sessione.get("data", "-")
        for esercizio in sessione.get("esercizi", []):
            nome = esercizio.get("nome", "").strip()
            if not nome:
                continue

            serie_svolte = [s for s in esercizio.get("serie_svolte", []) if s.get("completata")]
            if not serie_svolte:
                continue

            record = prs.setdefault(nome, {
                "max_peso": 0.0, "max_peso_data": None,
                "max_reps": 0, "max_reps_data": None,
                "max_volume": 0.0, "max_volume_data": None,
                "stima_1rm": 0.0, "stima_1rm_data": None,
            })

            volume_sessione = 0.0
            for serie in serie_svolte:
                peso = float(serie.get("peso", 0) or 0)
                reps = int(serie.get("reps", 0) or 0)
                volume_sessione += peso * reps

                if peso > record["max_peso"]:
                    record["max_peso"] = peso
                    record["max_peso_data"] = data_sessione

                if reps > record["max_reps"]:
                    record["max_reps"] = reps
                    record["max_reps_data"] = data_sessione

                stima = _epley_1rm(peso, reps)
                if stima > record["stima_1rm"]:
                    record["stima_1rm"] = stima
                    record["stima_1rm_data"] = data_sessione

            if volume_sessione > record["max_volume"]:
                record["max_volume"] = round(volume_sessione, 1)
                record["max_volume_data"] = data_sessione

    return prs


def detect_new_prs(storico_precedente: list, sessione_nuova: dict) -> list:
    """Confronta i PR calcolati PRIMA della nuova sessione con quelli
    ottenuti aggiungendola, e ritorna una lista di messaggi descrittivi
    per ogni nuovo record raggiunto in questa sessione (peso, reps, 1RM,
    o volume). Utile per mostrare un badge di celebrazione a fine
    allenamento."""
    prs_prima = compute_all_prs(storico_precedente)
    prs_dopo = compute_all_prs(storico_precedente + [sessione_nuova])

    nuovi_record = []
    for esercizio in sessione_nuova.get("esercizi", []):
        nome = esercizio.get("nome", "").strip()
        if not nome or nome not in prs_dopo:
            continue

        prima = prs_prima.get(nome, {"max_peso": 0.0, "max_reps": 0, "max_volume": 0.0, "stima_1rm": 0.0})
        dopo = prs_dopo[nome]

        if dopo["max_peso"] > prima.get("max_peso", 0.0):
            nuovi_record.append(f"🏆 Nuovo PR di peso in {nome}: {dopo['max_peso']} kg")
        if dopo["max_reps"] > prima.get("max_reps", 0):
            nuovi_record.append(f"🏆 Nuovo PR di ripetizioni in {nome}: {dopo['max_reps']} reps")
        if dopo["max_volume"] > prima.get("max_volume", 0.0):
            nuovi_record.append(f"🏆 Nuovo PR di volume in {nome}: {dopo['max_volume']} kg totali")
        if dopo["stima_1rm"] > prima.get("stima_1rm", 0.0):
            nuovi_record.append(f"🏆 Nuovo massimale stimato in {nome}: {dopo['stima_1rm']} kg")

    return nuovi_record


def get_pr_for_exercise(storico: list, nome_esercizio: str) -> Optional[dict]:
    """Ritorna il record del singolo esercizio, o None se non esistono
    dati sufficienti (nessuna serie completata registrata)."""
    prs = compute_all_prs(storico)
    return prs.get(nome_esercizio.strip())
