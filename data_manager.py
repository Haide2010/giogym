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

import base64
import json
import os
import shutil
from datetime import datetime

DATA_FILENAME = "giogym_data.json"

DEFAULT_DATA = {
    "scheda": {"giorni": []},
    "storico": [],
    "profilo": {
        "nome": "",
        "obiettivo": "",
        "altezza_cm": 175,
        "peso_attuale_kg": 68.5,
        "peso_obiettivo_kg": 72.0,
        "frequenza_settimanale": 4,
        "eta": 25,
        "sesso": "M",
    },
    "peso_corporeo": [],
    "infortuni": [],
    "tema": "scuro",
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
        data.setdefault("tema", "scuro")
        return data
    except (json.JSONDecodeError, OSError):
        # File corrotto: non lo sovrascriviamo subito (evitiamo perdita
        # dati), ma torniamo una struttura vuota funzionante in memoria.
        return json.loads(json.dumps(DEFAULT_DATA))


def save_data(data: dict) -> None:
    """Salva l'intero dizionario dati su file JSON (indentato e leggibile)
    e crea automaticamente una copia di backup datata nella cartella
    'backups' accanto al file dati (rotazione: si tiene l'ultima copia per
    giorno, massimo MAX_BACKUP_DAYS; le più vecchie vengono eliminate)."""
    path = get_data_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    try:
        bdir = backup_dir()
        nome_bk = f"giogym_data_{datetime.now().strftime('%Y%m%d')}.json"
        destino = os.path.join(bdir, nome_bk)
        if not os.path.exists(destino):
            shutil.copy2(path, destino)
        _ruota_backup(bdir)
    except OSError:
        # Se la copia di backup fallisce non blocchiamo il salvataggio
        # principale (es. permessi limitati su alcune piattaforme mobili).
        pass


def backup_dir() -> str:
    """Cartella dei backup automatici, accanto al file dati principale."""
    bdir = os.path.join(os.path.dirname(get_data_path()), "backups")
    os.makedirs(bdir, exist_ok=True)
    return bdir


MAX_BACKUP_DAYS = 30


def _ruota_backup(bdir: str) -> None:
    """Elimina i backup giornalieri più vecchi (tiene solo gli ultimi
    MAX_BACKUP_DAYS file)."""
    file_data = [
        os.path.join(bdir, n)
        for n in os.listdir(bdir)
        if n.startswith("giogym_data_") and n.endswith(".json")
    ]
    if len(file_data) <= MAX_BACKUP_DAYS:
        return
    # Ordiniamo per data nel nome (YYYYMMDD) e rimuoviamo i più vecchi.
    file_data.sort(key=lambda p: os.path.basename(p))
    for vecchio in file_data[:-MAX_BACKUP_DAYS]:
        try:
            os.remove(vecchio)
        except OSError:
            pass


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

def _storico_con_foto_b64(storico: list) -> list:
    """Copia dello storico in cui ogni sessione con una foto su disco
    viene arricchita con 'foto_b64' (contenuto binario codificato in
    base64) così la foto fa parte del file di backup."""
    output = []
    for sessione in storico:
        copia = dict(sessione)
        foto = sessione.get("foto", "")
        if foto and os.path.exists(foto):
            try:
                with open(foto, "rb") as f:
                    copia["foto_b64"] = base64.b64encode(f.read()).decode("ascii")
            except OSError:
                pass
        output.append(copia)
    return output


def export_data_to_json(data: dict, include_fotos: bool = False) -> str:
    """Serializza l'intero dizionario dati in una stringa JSON leggibile,
    pronta per essere scritta su file e condivisa/trasferita. Il backup
    include scheda, storico, profilo, peso corporeo, infortuni e colore
    del tema scelto.

    Di default le FOTO dell'allenamento NON vengono incluse: sono dati
    binari codificati in base64 che gonfiano il file rendendolo enorme e
    difficile da copiare/condividere. Imposta `include_fotos=True` solo
    per esportazioni complete."""
    def _storico_export():
        if include_fotos:
            return _storico_con_foto_b64(data.get("storico", []))
        output = []
        for sessione in data.get("storico", []):
            copia = dict(sessione)
            copia.pop("foto", None)
            copia.pop("foto_b64", None)
            output.append(copia)
        return output

    payload = {
        "app": "GioGym",
        "versione_backup": 2,
        "esportato_il": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "scheda": data.get("scheda", {"giorni": []}),
        "storico": _storico_export(),
        "profilo": data.get("profilo", {}),
        "peso_corporeo": data.get("peso_corporeo", []),
        "infortuni": data.get("infortuni", []),
        "primary_color": data.get("primary_color"),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def export_backup_file(data: dict, directory: str, include_fotos: bool = False) -> str:
    """Scrive un file di backup timestampato nella cartella indicata e
    ne ritorna il percorso completo."""
    os.makedirs(directory, exist_ok=True)
    filename = f"giogym_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(export_data_to_json(data, include_fotos=include_fotos))
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

    return {
        "scheda": scheda,
        "storico": storico,
        "profilo": parsed.get("profilo") if isinstance(parsed.get("profilo"), dict) else {},
        "peso_corporeo": parsed.get("peso_corporeo") if isinstance(parsed.get("peso_corporeo"), list) else [],
        "infortuni": parsed.get("infortuni") if isinstance(parsed.get("infortuni"), list) else [],
        "primary_color": parsed.get("primary_color") if isinstance(parsed.get("primary_color"), str) else None,
    }


def _ripristina_foto(storico: list) -> None:
    """Per ogni sessione con 'foto_b64' scrive il file immagine nella
    cartella dati dell'app e aggiorna il campo 'foto' col nuovo percorso
    (eliminando la voce base64)."""
    data_dir = os.path.dirname(get_data_path())
    os.makedirs(data_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    contatore = 0
    for sessione in storico:
        b64 = sessione.pop("foto_b64", None)
        if not b64:
            continue
        try:
            payload = base64.b64decode(b64)
        except Exception:
            continue
        if not payload:
            continue
        contatore += 1
        estensione = os.path.splitext(str(sessione.get("foto", "")))[1] or ".jpg"
        nome = f"workout_{timestamp}_{contatore}{estensione}"
        try:
            with open(os.path.join(data_dir, nome), "wb") as f:
                f.write(payload)
            sessione["foto"] = os.path.join(data_dir, nome)
        except OSError:
            pass


def import_data_from_json(json_str: str) -> dict:
    """Importa i dati da una stringa JSON di backup, validandone la
    struttura. Ritorna un dizionario dati pronto per sostituire quello
    corrente (include scheda, storico con foto ripristinate, profilo,
    peso corporeo, infortuni e colore tema). Solleva ImportError_ in
    caso di file non valido."""
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ImportError_(f"File JSON non leggibile: {exc}") from exc
    dati = validate_backup_dict(parsed)
    _ripristina_foto(dati["storico"])
    return dati


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
        "profilo": imported.get("profilo") or current.get("profilo", {}),
        "peso_corporeo": imported.get("peso_corporeo") or current.get("peso_corporeo", []),
        "infortuni": imported.get("infortuni") or current.get("infortuni", []),
        "primary_color": imported.get("primary_color") or current.get("primary_color"),
    }
