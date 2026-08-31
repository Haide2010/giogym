# GioGym 🏋️

App mobile per tracciare gli allenamenti in palestra, scritta interamente
in Python con **Flet** (UI Material Design moderna, basata su Flutter,
compilabile in vero APK Android).

## Perché Flet e non Kivy/BeeWare

Per questo progetto ho scelto **Flet** perché:
- il motore di rendering è **Flutter**, quindi la UI risulta moderna e
  fluida "di serie" (Material 3), senza dover disegnare da zero temi,
  ombre, animazioni come si farebbe in Kivy;
- il codice resta **100% Python puro**, senza linguaggi di markup
  aggiuntivi (a differenza del `.kv` di Kivy);
- la compilazione Android è **integrata**: `flet build apk` fa tutto
  (genera il progetto Flutter, lo builda, produce l'APK), senza dover
  configurare manualmente `buildozer.spec` come con Kivy.

## Struttura del progetto

```
giogym/
├── main.py                 # Entry point + controller di navigazione (GioGymApp)
├── data_manager.py         # Persistenza JSON locale (load/save)
├── theme.py                 # Colori, stili, costanti UI condivise
├── requirements.txt
├── views/
│   ├── home_view.py         # A) Home / Dashboard + storico
│   ├── selection_view.py    # B) Selezione giorno allenamento
│   ├── schema_view.py       # Editor scheda (1-7 giorni, esercizi)
│   └── training_view.py     # C+D) Training attivo + Rest Timer
```

I dati (scheda + storico allenamenti) vengono salvati in un file
`giogym_data.json`. Su desktop/dev viene creato nella cartella del
progetto; su dispositivo mobile Flet lo colloca automaticamente nella
cartella dati persistente dell'app (variabile `FLET_APP_STORAGE_DATA`),
gestita già in `data_manager.py` — non serve configurare nulla.

---

## 1. Installazione delle dipendenze (test locale)

Consigliato un ambiente virtuale:

```bash
python3 -m venv venv
source venv/bin/activate        # Su Windows: venv\Scripts\activate

pip install -r requirements.txt
```

> Il progetto è stato scritto e testato contro **flet==0.28.3**, versione
> pinnata in `requirements.txt`. Flet cambia API abbastanza spesso tra
> major version: se aggiorni, verifica che i metodi `page.open()` /
> `page.close()` per dialog/snackbar esistano ancora (nella versione
> testata sì).

## 2. Avvio e test dell'app (senza compilare nulla)

**Come finestra desktop nativa** (il modo più rapido per testare tutto
il flusso — scheda, allenamento, timer):

```bash
flet run main.py
```

**Nel browser** (utile per test rapidi o ambienti senza GUI):

```bash
flet run --web main.py
```

**Su smartphone reale, senza compilare**, tramite l'app "Flet" (disponibile
su Play Store/App Store): avvia `flet run main.py`, poi inquadra il QR
code mostrato in console con l'app Flet sul telefono. Utilissimo per
testare il tocco/timer su dispositivo vero prima di fare la build APK.

Con `flet run` (non `--web`) è attivo anche l'**hot reload**: salvando un
file `.py` la UI si aggiorna subito.

---

## 3. Compilazione dell'APK Android

### Prerequisiti sulla macchina di build

`flet build apk` orchestra una build Flutter/Android "vera", quindi
servono gli stessi strumenti richiesti da Flutter:

1. **Flutter SDK** installato e nel `PATH`
   (https://docs.flutter.dev/get-started/install)
2. **Java JDK 17+**
3. **Android SDK + Android NDK** (si possono installare anche solo con
   Android Studio, oppure con `sdkmanager` da riga di comando)
4. Verifica che tutto sia a posto con:
   ```bash
   flutter doctor
   ```
   Risolvi eventuali ✗ prima di procedere (licenze Android accettate con
   `flutter doctor --android-licenses`).

> Su una macchina "pulita" questa è la parte più lunga (installazione
> Flutter + Android SDK/NDK può richiedere diversi GB e mezz'ora buona).
> Se non vuoi installare nulla in locale, in alternativa puoi usare una
> **GitHub Action** che esegue `flet build apk` in CI (Anthropic/Flet
> pubblicano workflow di esempio nella documentazione ufficiale
> flet.dev → "Publishing an app").

### Comando di build

Dalla cartella del progetto (dove si trova `main.py`):

```bash
pip install flet[all]==0.28.3   # se non già fatto, include gli strumenti CLI di build
flet build apk
```

Al termine (può richiedere diversi minuti la prima volta, perché Flutter
scarica dipendenze Gradle), l'APK compilato si trova in:

```
build/apk/app-release.apk
```

Puoi installarlo su un dispositivo collegato via USB (debug abilitato)
con:

```bash
adb install build/apk/app-release.apk
```

### Personalizzare nome app, icona, package id

Prima della build puoi creare/editare un file `pyproject.toml` nella
root del progetto per personalizzare metadata (nome visualizzato, id
pacchetto Android, versione, icona):

```toml
[project]
name = "giogym"
version = "1.0.0"

[tool.flet.app]
product = "GioGym"

[tool.flet.android]
package = "com.tuonome.giogym"
```

Per l'icona: metti un file `icon.png` (1024x1024) in una cartella
`assets/` nella root del progetto — Flet la userà automaticamente come
icona dell'app se referenziata nella configurazione, oppure puoi
passarla via `flet build apk --icon assets/icon.png`. Consulta
`flet build apk --help` per l'elenco completo delle opzioni (versione,
build number, splash screen, ecc.).

---

## 4. Note su suono/vibrazione del Rest Timer

Per semplicità e portabilità, l'avviso di fine recupero implementato è
**visivo** (colore che cambia + SnackBar). Se vuoi aggiungere:

- **Suono**: metti un file audio (es. `beep.mp3`) in una cartella
  `assets/`, aggiungi un controllo `ft.Audio(src="beep.mp3")`
  all'overlay della pagina e chiama `.play()` quando il timer arriva a
  zero (in `training_view.py`, metodo `_on_timer_finished`).
- **Vibrazione**: richiede un plugin nativo aggiuntivo (es.
  `flet-permission-handler` o un pacchetto Flutter dedicato) e i
  permessi Android corrispondenti in `pyproject.toml`. Non incluso di
  default per mantenere la build più semplice e senza permessi extra.

---

## 5. Cosa fa già l'app (riepilogo funzionalità)

- **Editor scheda** (icona ⚙️ in Home): configura da 1 a 7 giorni, ogni
  giorno con esercizi (nome, serie, reps target, peso di riferimento).
- **Home**: storico allenamenti completati (data + giorno + riepilogo
  serie), pulsante grande "INIZIA ALLENAMENTO".
- **Selezione**: scelta del giorno tra quelli configurati.
- **Training attivo**: per ogni esercizio, serie con peso/reps
  precompilati e modificabili in tempo reale; tap sul cerchio di spunta
  segna la serie completata e avvia il timer di recupero.
- **Rest Timer**: dialog modale con countdown, barra di progresso,
  pulsanti -30s/+30s, slider per la durata di default (max 3 minuti),
  avviso visivo a scadenza.
- **Fine allenamento**: salva la sessione nello storico con data
  esatta e aggiorna i pesi di riferimento della scheda con l'ultimo
  peso usato in ciascun esercizio.

Tutto il codice è stato verificato con: compilazione sintattica di ogni
modulo, uno smoke test che percorre l'intero flusso applicativo
(creazione scheda → selezione → allenamento → timer → salvataggio →
verifica del JSON su disco) e un avvio reale del server Flet in
modalità web per controllare che non ci siano eccezioni a runtime.
