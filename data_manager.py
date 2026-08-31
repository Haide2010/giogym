"""
data_manager.py
----------------
Gestisce la persistenza dei dati di GioGym in un file JSON locale.

Struttura del file (giogym_data.json):
{
    "scheda": {
        "giorni": [
            {
                "nome": "Giorno 1",
                "esercizi": [
                    {
                        "nome": "Panca piana",
                        "serie": 4,
                        "ripetizioni": "8-10",
                        "peso_riferimento": 40.0
                    },
                    ...
                ]
            },
            ...
        ]
    },
    "storico": [
        {
            "data": "31/08/2026",
            "giorno_nome": "Giorno 1",
            "esercizi": [
                {
                    "nome": "Panca piana",
                    "serie_svolte": [
                        {"peso": 40.0, "reps": 10, "completata": true},
                        ...
                    ]
                },
                ...
            ]
        },
        ...
    ]
}

Nota sul percorso del file:
Su dispositivo mobile (APK compilato con Flet) la cartella corrente
dell'app non è garantita scrivibile: Flet mette a disposizione la
variabile d'ambiente FLET_APP_STORAGE_DATA che punta a una cartella
dati persistente e specifica per l'app, valida su Android/iOS/desktop.
In fase di sviluppo (flet run) questa variabile non è impostata, quindi
si ricade sulla cartella corrente del progetto.
"""

import json
import os
from datetime import datetime

DATA_FILENAME = "giogym_data.json"

DEFAULT_DATA = {
    "scheda": {"giorni": []},
    "storico": [],
}


def get_data_path() -> str:
    """Ritorna il percorso completo del file JSON dati, scegliendo la
    cartella corretta in base all'ambiente di esecuzione (mobile o dev)."""
    base_dir = os.getenv("FLET_APP_STORAGE_DATA", os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, DATA_FILENAME)


def load_data() -> dict:
    """Carica i dati dal file JSON. Se il file non esiste o è corrotto,
    crea/ripristina una struttura dati vuota valida."""
    path = get_data_path()
    if not os.path.exists(path):
        save_data(DEFAULT_DATA)
        return json.loads(json.dumps(DEFAULT_DATA))

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Garantisce che le chiavi principali esistano sempre
        data.setdefault("scheda", {"giorni": []})
        data["scheda"].setdefault("giorni", [])
        data.setdefault("storico", [])
        return data
    except (json.JSONDecodeError, OSError):
        # File corrotto: non lo sovrascriviamo subito (evitiamo perdita
        # dati), ma torniamo una struttura vuota funzionante in memoria.
        return json.loads(json.dumps(DEFAULT_DATA))


def save_data(data: dict) -> None:
    """Salva l'intero dizionario dati su file JSON (indentato e leggibile)."""
    path = get_data_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def today_str() -> str:
    """Data odierna nel formato gg/mm/aaaa usato in tutta l'app."""
    return datetime.now().strftime("%d/%m/%Y")


def new_esercizio(nome: str = "", serie: int = 3, ripetizioni: str = "8-12",
                   peso_riferimento: float = 0.0) -> dict:
    """Factory per un esercizio vuoto/precompilato, usata dall'editor scheda."""
    return {
        "nome": nome,
        "serie": serie,
        "ripetizioni": ripetizioni,
        "peso_riferimento": peso_riferimento,
    }


def new_giorno(nome: str = "Giorno") -> dict:
    """Factory per un giorno vuoto della scheda."""
    return {"nome": nome, "esercizi": []}
