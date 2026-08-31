"""
training_view.py
------------------
Schermata C + D - Training Attivo e Rest Timer.

Il cuore dell'app: per il giorno scelto mostra tutti gli esercizi con le
relative serie (peso/reps precompilati dalla scheda), permette di
segnare ogni serie come completata e, a quel punto, avvia in automatico
un timer di recupero mostrato in un dialog modale con controlli rapidi
(+30s / -30s) e uno slider per impostare la durata di default.

Alla fine, "Termina e Salva Allenamento" scrive la sessione nello
storico e aggiorna i pesi di riferimento della scheda.
"""

import asyncio
import re

import flet as ft
import theme
import data_manager as dm

REST_MAX_SECONDS = 180   # 3 minuti, come da specifica
REST_STEP_SECONDS = 30
REST_DEFAULT_SECONDS = 90
REST_WARNING_THRESHOLD = 10  # secondi rimanenti sotto i quali il timer "avvisa"


def _parse_target_reps(ripetizioni_str: str) -> str:
    """Estrae un valore reps iniziale ragionevole dal target (es. '8-10' -> '8').
    Ritorna comunque una stringa: l'utente può modificarla liberamente."""
    match = re.search(r"\d+", str(ripetizioni_str))
    return match.group(0) if match else ""


class TrainingView:
    def __init__(self, app, giorno_index: int):
        self.app = app
        self.page = app.page
        self.giorno_index = giorno_index
        self.giorno = app.data["scheda"]["giorni"][giorno_index]

        # Stato di sessione: una lista di serie per ogni esercizio.
        # Non tocca ancora i dati salvati (self.app.data) finché non si
        # preme "Termina e Salva Allenamento".
        self.session = []
        for esercizio in self.giorno["esercizi"]:
            n_serie = max(1, int(esercizio.get("serie", 3)))
            serie_list = [
                {
                    "peso": esercizio.get("peso_riferimento", 0),
                    "reps": _parse_target_reps(esercizio.get("ripetizioni", "")),
                    "completata": False,
                }
                for _ in range(n_serie)
            ]
            self.session.append(serie_list)

        # Riferimenti ai controlli "check" per aggiornarne icona/colore
        self._check_buttons = {}  # (ex_idx, serie_idx) -> IconButton

        # --- Stato Rest Timer ---
        self.rest_default_seconds = REST_DEFAULT_SECONDS
        self.rest_seconds_remaining = self.rest_default_seconds
        self.rest_running = False

        self.timer_text = ft.Text("01:30", size=48, weight=ft.FontWeight.BOLD, color=theme.TEXT)
        self.timer_status = ft.Text("Recupero in corso...", size=13, color=theme.TEXT_MUTED)
        self.timer_progress = ft.ProgressBar(
            value=1.0, width=260, color=theme.PRIMARY, bgcolor=theme.BG_CARD_LIGHT
        )
        self.rest_slider = ft.Slider(
            min=30,
            max=REST_MAX_SECONDS,
            divisions=(REST_MAX_SECONDS - 30) // 15,
            value=self.rest_default_seconds,
            label="{value}s",
            on_change=self._on_default_duration_change,
        )

        self.timer_dialog = ft.AlertDialog(
            modal=True,
            bgcolor=theme.BG_CARD,
            title=ft.Text("Recupero", color=theme.TEXT, weight=ft.FontWeight.BOLD),
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.TIMER, size=40, color=theme.PRIMARY),
                    self.timer_text,
                    self.timer_progress,
                    self.timer_status,
                    ft.Row(
                        [
                            ft.OutlinedButton("-30s", on_click=lambda e: self._adjust_timer(-REST_STEP_SECONDS)),
                            ft.OutlinedButton("+30s", on_click=lambda e: self._adjust_timer(REST_STEP_SECONDS)),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=12,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                tight=True,
            ),
            actions=[
                ft.TextButton("Salta recupero", on_click=lambda e: self._close_timer()),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )

        # Snackbar riutilizzata per notificare fine recupero
        self.timer_end_snack = ft.SnackBar(
            content=ft.Text("Tempo di recupero terminato! 💪"),
            bgcolor=theme.SUCCESS,
        )

    # ------------------------------------------------------------------
    # Costruzione UI principale
    # ------------------------------------------------------------------
    def build(self) -> ft.Control:
        header = ft.Row(
            [
                ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self._on_back),
                ft.Text(
                    self.giorno.get("nome", "Allenamento"),
                    size=theme.TITLE_SIZE,
                    weight=ft.FontWeight.BOLD,
                    color=theme.TEXT,
                ),
            ]
        )

        esercizi_controls = [
            self._build_esercizio_card(idx, esercizio)
            for idx, esercizio in enumerate(self.giorno["esercizi"])
        ]

        esercizi_list = ft.ListView(controls=esercizi_controls, expand=True, spacing=14)

        finish_btn = ft.ElevatedButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.FLAG, color=ft.Colors.WHITE), ft.Text("TERMINA E SALVA ALLENAMENTO", weight=ft.FontWeight.BOLD)],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=theme.SUCCESS,
            color=ft.Colors.WHITE,
            height=54,
            on_click=self._on_finish,
        )

        return ft.Column(
            [
                header,
                ft.Row(
                    [
                        ft.Icon(ft.Icons.TIMER_OUTLINED, size=16, color=theme.TEXT_MUTED),
                        ft.Text("Durata recupero predefinita:", size=12, color=theme.TEXT_MUTED),
                        self.rest_slider,
                    ],
                ),
                ft.Divider(color=theme.BORDER, height=10),
                esercizi_list,
                finish_btn,
            ],
            expand=True,
            spacing=8,
        )

    def _build_esercizio_card(self, ex_idx: int, esercizio: dict) -> ft.Control:
        target = f'{esercizio.get("ripetizioni", "-")} reps · rif. {esercizio.get("peso_riferimento", 0)} kg'

        serie_rows = ft.Column(spacing=6)
        for s_idx, serie in enumerate(self.session[ex_idx]):
            serie_rows.controls.append(self._build_serie_row(ex_idx, s_idx, serie))

        return theme.card_container(
            ft.Column(
                [
                    ft.Text(esercizio.get("nome", "Esercizio"), size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ft.Text(target, size=12, color=theme.TEXT_MUTED),
                    ft.Divider(color=theme.BORDER, height=8),
                    serie_rows,
                ],
                spacing=6,
            ),
        )

    def _build_serie_row(self, ex_idx: int, s_idx: int, serie: dict) -> ft.Control:
        peso_field = ft.TextField(
            value=str(serie["peso"]),
            label="Kg",
            dense=True,
            width=80,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e, ei=ex_idx, si=s_idx: self._update_serie(ei, si, "peso", e.control.value),
        )
        reps_field = ft.TextField(
            value=str(serie["reps"]),
            label="Reps",
            dense=True,
            width=70,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e, ei=ex_idx, si=s_idx: self._update_serie(ei, si, "reps", e.control.value),
        )

        check_btn = ft.IconButton(
            icon=ft.Icons.CHECK_CIRCLE if serie["completata"] else ft.Icons.RADIO_BUTTON_UNCHECKED,
            icon_color=theme.SUCCESS if serie["completata"] else theme.TEXT_MUTED,
            tooltip="Fine serie",
            on_click=lambda e, ei=ex_idx, si=s_idx: self._toggle_serie_completata(ei, si),
        )
        self._check_buttons[(ex_idx, s_idx)] = check_btn

        return ft.Row(
            [
                ft.Text(f"Serie {s_idx + 1}", size=13, color=theme.TEXT_MUTED, width=60),
                peso_field,
                reps_field,
                ft.Container(expand=True),
                check_btn,
            ],
            alignment=ft.MainAxisAlignment.START,
        )

    # ------------------------------------------------------------------
    # Aggiornamento dati sessione
    # ------------------------------------------------------------------
    def _update_serie(self, ex_idx, s_idx, campo, value):
        if campo == "peso":
            try:
                value = round(float(value.replace(",", ".")), 2) if value else 0
            except ValueError:
                value = self.session[ex_idx][s_idx]["peso"]
        self.session[ex_idx][s_idx][campo] = value

    def _toggle_serie_completata(self, ex_idx, s_idx):
        serie = self.session[ex_idx][s_idx]
        serie["completata"] = not serie["completata"]

        btn = self._check_buttons[(ex_idx, s_idx)]
        btn.icon = ft.Icons.CHECK_CIRCLE if serie["completata"] else ft.Icons.RADIO_BUTTON_UNCHECKED
        btn.icon_color = theme.SUCCESS if serie["completata"] else theme.TEXT_MUTED
        self.page.update()

        if serie["completata"]:
            self._start_rest_timer()

    # ------------------------------------------------------------------
    # Rest Timer
    # ------------------------------------------------------------------
    def _on_default_duration_change(self, e):
        self.rest_default_seconds = int(self.rest_slider.value)

    def _start_rest_timer(self):
        self.rest_seconds_remaining = self.rest_default_seconds
        self.rest_running = True
        self.timer_status.value = "Recupero in corso..."
        self.timer_status.color = theme.TEXT_MUTED
        self._refresh_timer_ui()
        self.page.open(self.timer_dialog)
        self.page.run_task(self._countdown_loop)

    def _adjust_timer(self, delta_seconds: int):
        self.rest_seconds_remaining = max(0, min(REST_MAX_SECONDS, self.rest_seconds_remaining + delta_seconds))
        if self.rest_seconds_remaining > 0:
            self.rest_running = True
            self.timer_status.value = "Recupero in corso..."
            self.timer_status.color = theme.TEXT_MUTED
        self._refresh_timer_ui()

    async def _countdown_loop(self):
        # Ciclo asincrono non bloccante: aggiorna la UI ogni secondo.
        # Si interrompe se l'utente chiude/salta il timer (rest_running=False)
        # o se esce dalla schermata di training.
        while self.rest_seconds_remaining > 0 and self.rest_running:
            await asyncio.sleep(1)
            self.rest_seconds_remaining -= 1
            self._refresh_timer_ui()

        if self.rest_running and self.rest_seconds_remaining <= 0:
            self._on_timer_finished()

    def _on_timer_finished(self):
        self.rest_running = False
        self.timer_status.value = "TEMPO SCADUTO! Torna a lavorare 🔥"
        self.timer_status.color = theme.WARNING
        # Avviso visivo: barra e testo diventano evidenti.
        # NOTA: per un avviso sonoro/vibrazione reale su Android si può
        # aggiungere un ft.Audio con un file in /assets (vedi README) e/o
        # il pacchetto "flet-permission-handler" per l'haptic feedback;
        # qui, per portabilità, usiamo un forte segnale visivo + SnackBar.
        self.page.open(self.timer_end_snack)
        self._refresh_timer_ui()

    def _refresh_timer_ui(self):
        mins, secs = divmod(max(0, self.rest_seconds_remaining), 60)
        self.timer_text.value = f"{mins:02d}:{secs:02d}"
        total = max(1, self.rest_default_seconds)
        self.timer_progress.value = max(0.0, self.rest_seconds_remaining / total)

        if self.rest_seconds_remaining <= REST_WARNING_THRESHOLD and self.rest_seconds_remaining > 0:
            self.timer_text.color = theme.WARNING
            self.timer_progress.color = theme.WARNING
        elif self.rest_seconds_remaining <= 0:
            self.timer_text.color = theme.DANGER
            self.timer_progress.color = theme.DANGER
        else:
            self.timer_text.color = theme.TEXT
            self.timer_progress.color = theme.PRIMARY

        if self.page:
            self.page.update()

    def _close_timer(self):
        self.rest_running = False
        self.page.close(self.timer_dialog)

    # ------------------------------------------------------------------
    # Navigazione / Fine allenamento
    # ------------------------------------------------------------------
    def _on_back(self, e):
        self.rest_running = False  # ferma eventuale countdown attivo

        def conferma(ev):
            self.page.close(confirm_dialog)
            self.app.show_selection()

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Uscire dall'allenamento?"),
            content=ft.Text("I progressi di questa sessione non salvata andranno persi."),
            actions=[
                ft.TextButton("Annulla", on_click=lambda ev: self.page.close(confirm_dialog)),
                ft.TextButton("Esci", on_click=conferma),
            ],
        )
        self.page.open(confirm_dialog)

    def _on_finish(self, e):
        self.rest_running = False

        def conferma(ev):
            self.page.close(confirm_dialog)
            self._salva_sessione()

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Terminare l'allenamento?"),
            content=ft.Text("L'allenamento verrà salvato nello storico e i pesi di riferimento aggiornati."),
            actions=[
                ft.TextButton("Annulla", on_click=lambda ev: self.page.close(confirm_dialog)),
                ft.TextButton("Termina e salva", on_click=conferma),
            ],
        )
        self.page.open(confirm_dialog)

    def _salva_sessione(self):
        esercizi_storico = []
        for ex_idx, esercizio in enumerate(self.giorno["esercizi"]):
            serie_svolte = [dict(s) for s in self.session[ex_idx]]  # copia pulita
            esercizi_storico.append({"nome": esercizio.get("nome", ""), "serie_svolte": serie_svolte})

            # Aggiorna il peso di riferimento nella scheda con l'ultimo
            # peso utilizzato nell'ultima serie svolta (se presente).
            if serie_svolte:
                ultimo_peso = serie_svolte[-1]["peso"]
                try:
                    self.app.data["scheda"]["giorni"][self.giorno_index]["esercizi"][ex_idx]["peso_riferimento"] = float(ultimo_peso)
                except (ValueError, TypeError):
                    pass

        sessione = {
            "data": dm.today_str(),
            "giorno_nome": self.giorno.get("nome", ""),
            "esercizi": esercizi_storico,
        }
        self.app.data["storico"].append(sessione)
        self.app.save()
        self.app.show_home()
