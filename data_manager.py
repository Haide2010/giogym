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
    "profilo": {
        "altezza_cm": 175,
        "peso_attuale_kg": 68.5,
        "peso_obiettivo_kg": 72.0,
        "frequenza_settimanale": 4,
        "eta": 25,
        "sesso": "M",
    },
    "peso_corporeo": [],
    "infortuni": [],
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
        data.setdefault("profilo", DEFAULT_DATA["profilo"])
        data.setdefault("peso_corporeo", [])
        data.setdefault("infortuni", [])
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


# ----------------------------------------------------------------------
# Backup: esportazione / importazione dati (JSON)
# ----------------------------------------------------------------------

def export_data_to_json(data: dict) -> str:
    """Serializza l'intero dizionario dati in una stringa JSON leggibile,
    pronta per essere scritta su file e condivisa/trasferita."""
    payload = {
        "app": "GioGym",
        "versione_backup": 1,
        "esportato_il": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "scheda": data.get("scheda", {"giorni": []}),
        "storico": data.get("storico", []),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def export_backup_file(data: dict, directory: str) -> str:
    """Scrive un file di backup timestampato nella cartella indicata e
    ne ritorna il percorso completo."""
    os.makedirs(directory, exist_ok=True)
    filename = f"giogym_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(export_data_to_json(data))
    return path


class ImportError_(Exception):
    """Errore sollevato quando un file/stringa di backup non è valido."""
    pass


def validate_backup_dict(parsed: dict) -> dict:
    """Verifica che il dizionario importato abbia la struttura minima
    attesa e ritorna un dizionario dati pulito e pronto all'uso.
    Solleva ImportError_ se la struttura non è valida."""
    if not isinstance(parsed, dict):
        raise ImportError_("Il file non contiene un oggetto JSON valido.")

    scheda = parsed.get("scheda")
    storico = parsed.get("storico")

    if scheda is None or storico is None:
        raise ImportError_("Il file non sembra un backup di GioGym (chiavi 'scheda'/'storico' mancanti).")

    if not isinstance(scheda, dict) or "giorni" not in scheda or not isinstance(scheda["giorni"], list):
        raise ImportError_("La sezione 'scheda' del backup non è valida.")

    if not isinstance(storico, list):
        raise ImportError_("La sezione 'storico' del backup non è valida.")

    return {"scheda": scheda, "storico": storico}


def import_data_from_json(json_str: str) -> dict:
    """Importa i dati da una stringa JSON di backup, validandone la
    struttura. Ritorna un dizionario dati pronto per sostituire quello
    corrente. Solleva ImportError_ in caso di file non valido."""
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ImportError_(f"File JSON non leggibile: {exc}") from exc
    return validate_backup_dict(parsed)


def merge_imported_data(current: dict, imported: dict) -> dict:
    """Unisce i dati importati con quelli correnti: la scheda importata
    sostituisce quella attuale, mentre lo storico viene unito evitando
    duplicati esatti (stessa data + stesso giorno + stessi esercizi)."""
    merged_storico = list(current.get("storico", []))
    esistenti = {json.dumps(s, sort_keys=True, ensure_ascii=False) for s in merged_storico}

    for sessione in imported.get("storico", []):
        chiave = json.dumps(sessione, sort_keys=True, ensure_ascii=False)
        if chiave not in esistenti:
            merged_storico.append(sessione)
            esistenti.add(chiave)

    # Ordina lo storico unito per data (gg/mm/aaaa) quando possibile
    def _key(s):
        try:
            return datetime.strptime(s.get("data", ""), "%d/%m/%Y")
        except ValueError:
            return datetime.min

    merged_storico.sort(key=_key)

    return {
        "scheda": imported.get("scheda", current.get("scheda", {"giorni": []})),
        "storico": merged_storico,
    }
