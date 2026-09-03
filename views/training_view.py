"""
training_view.py
------------------
Schermata C + D - Training Attivo, Rest Timer e nuove funzioni avanzate.
"""

import asyncio
import re
from datetime import datetime

import flet as ft
import theme
import data_manager as dm
import pr_manager
import fitness_calc

REST_MAX_SECONDS = 180
REST_STEP_SECONDS = 30
REST_DEFAULT_SECONDS = 90
REST_WARNING_THRESHOLD = 10


def _parse_target_reps(ripetizioni_str: str) -> str:
    match = re.search(r"\d+", str(ripetizioni_str))
    return match.group(0) if match else ""


class TrainingView:
    def __init__(self, app, giorno_index: int, edit_session: dict = None, edit_index: int = None):
        self.app = app
        self.page = app.page
        self.giorno_index = giorno_index
        self.edit_session = edit_session
        self.edit_index = edit_index

        # --- Cronometro Globale Sessione ---
        self.session_start_time = datetime.now()
        self.elapsed_seconds = 0
        self.global_timer_running = True
        self.global_timer_text = ft.Text("00:00", size=14, weight=ft.FontWeight.BOLD, color=theme.PRIMARY)

        self._check_buttons = {}
        self._note_fields = {}
        self._rm_labels = {}

        # Modalità MODIFICA: carica uno stato già esistente da una sessione passata
        if edit_session is not None:
            self.giorno = {
                "nome": edit_session.get("giorno_nome", "Allenamento"),
                "esercizi": [
                    {
                        "nome": ex.get("nome", ""),
                        "serie": len(ex.get("serie_svolte", [])),
                        "peso_riferimento": ex.get("serie_svolte", [])[-1].get("peso", 0) if ex.get("serie_svolte") else 0,
                        "ripetizioni": "",
                    }
                    for ex in edit_session.get("esercizi", [])
                ],
            }
            # Preserva esattamente peso/reps/completata di ogni serie salvata
            self.session = [
                [dict(s) for s in ex.get("serie_svolte", [])]
                for ex in edit_session.get("esercizi", [])
            ]
            # Note per esercizio salvate in precedenza (se presenti)
            self._session_notes = {
                i: ex.get("note", "")
                for i, ex in enumerate(edit_session.get("esercizi", []))
            }
        else:
            self.giorno = app.data["scheda"]["giorni"][giorno_index]
            self._session_notes = {}
            # Stato di sessione nuovo (da zero)
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

        # Campo note generali della sessione (precaricato se in modifica)
        self.general_notes_field = ft.TextField(
            label="Note generali della sessione (es. riscaldamento, energie...)",
            value=(edit_session or {}).get("note_generali", ""),
            text_size=13,
            dense=True,
            border_color=theme.BORDER,
            focused_border_color=theme.PRIMARY,
        )

        # --- Stato Rest Timer ---
        self.rest_default_seconds = REST_DEFAULT_SECONDS
        self.rest_seconds_remaining = self.rest_default_seconds
        self.rest_running = False
        self.timer_dialog_open = False

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
                ft.Column(
                    [
                        ft.Text(
                            self.giorno.get("nome", "Allenamento"),
                            size=theme.TITLE_SIZE,
                            weight=ft.FontWeight.BOLD,
                            color=theme.TEXT,
                        ),
                        ft.Row([
                            ft.Icon(ft.Icons.TIMER, size=14, color=theme.PRIMARY),
                            ft.Text("Tempo totale: ", size=12, color=theme.TEXT_MUTED),
                            self.global_timer_text,
                        ], spacing=4)
                    ],
                    spacing=0,
                    expand=True,
                )
            ]
        )

        esercizi_controls = [
            self._build_esercizio_card(idx, esercizio)
            for idx, esercizio in enumerate(self.giorno["esercizi"])
        ]

        esercizi_list = ft.ListView(
            controls=self._build_injury_controls() + [self.general_notes_field] + esercizi_controls, 
            expand=True, 
            spacing=14
        )

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

        # Avvia il task asincrono per il cronometro globale della sessione
        if self.page:
            self.page.run_task(self._global_timer_loop)

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

    def _get_last_performance(self, ex_name: str) -> str:
        """Cerca nello storico l'ultima prestazione registrata per questo esercizio."""
        for sessione in reversed(self.app.data.get("storico", [])):
            for ex in sessione.get("esercizi", []):
                if ex.get("nome", "").strip().lower() == ex_name.strip().lower():
                    serie_svolte = ex.get("serie_svolte", [])
                    if serie_svolte:
                        ultima = serie_svolte[-1]
                        return f"Ultima volta: {ultima.get('peso', 0)} kg × {ultima.get('reps', '-')} reps"
        return "Nessuno storico precedente"

    # ------------------------------------------------------------------
    # Registro "Infortuni o Fastidi" collegato al muscolo
    # ------------------------------------------------------------------
    def _get_active_injuries(self):
        """Ritorna gli infortuni ancora attivi (stato != 'risolto')."""
        attivi = []
        for inj in self.app.data.get("infortuni", []):
            if inj.get("stato") != "risolto":
                attivi.append(inj)
        return attivi

    def _injury_matches_day(self, inj: dict) -> bool:
        """Vero se l'infortunio è legato al giorno che stiamo allenando."""
        giorno_nome = self.giorno.get("nome", "")
        for g in inj.get("giorni", []):
            if g == giorno_nome:
                return True
        return False

    def _build_injury_controls(self) -> list:
        """Banner di promemoria in cima all'allenamento se ci sono
        infortuni attivi legati a questo giorno."""
        attivi = [i for i in self._get_active_injuries() if self._injury_matches_day(i)]
        if not attivi:
            return []

        controlli = []
        for inj in attivi:
            muscolo = inj.get("muscolo", "").strip() or "zona"
            desc = inj.get("descrizione", "").strip()
            testo = f"⚠️ Attenzione: fastidio registrato a {muscolo}"
            if desc:
                testo += f" — {desc}"
            testo += "\nRiscalda bene e considera di modulare i carichi."
            controlli.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.HEALING, color=theme.WARNING, size=18),
                                    ft.Text("Promemoria infortunio", size=13,
                                            weight=ft.FontWeight.BOLD, color=theme.WARNING),
                                ],
                                spacing=6,
                            ),
                            ft.Text(testo, size=12, color=theme.TEXT),
                        ],
                        spacing=4,
                    ),
                    padding=12,
                    bgcolor=theme.BG_CARD_LIGHT,
                    border_radius=theme.RADIUS,
                    border=ft.border.all(1, theme.WARNING),
                )
            )
        return controlli

    def _esercizio_injury(self, ex_name: str):
        """Ritorna il testo di promemoria se l'esercizio corrisponde (per
        nome) a un infortunio attivo, altrimenti None."""
        nome = (ex_name or "").strip().lower()
        for inj in self._get_active_injuries():
            ex_rif = (inj.get("esercizio", "") or "").strip().lower()
            if ex_rif and ex_rif == nome:
                desc = inj.get("descrizione", "").strip()
                return f"⚠️ Fastidio registrato su questo esercizio" + (f": {desc}" if desc else "")
        return None

    def _build_esercizio_card(self, ex_idx: int, esercizio: dict) -> ft.Control:
        ex_name = esercizio.get("nome", "Esercizio")
        target = f'{esercizio.get("ripetizioni", "-")} reps · rif. {esercizio.get("peso_riferimento", 0)} kg'
        last_perf = self._get_last_performance(ex_name)

        serie_rows = ft.Column(spacing=6)
        for s_idx, serie in enumerate(self.session[ex_idx]):
            serie_rows.controls.append(self._build_serie_row(ex_idx, s_idx, serie))

        note_field = ft.TextField(
            label="Note esercizio (es. pump, aumentare carico...)",
            value=self._session_notes.get(ex_idx, ""),
            text_size=12,
            dense=True,
            border_color=theme.BORDER,
            focused_border_color=theme.PRIMARY,
            content_padding=10,
        )
        self._note_fields[ex_idx] = note_field

        card_body = [
            ft.Text(ex_name, size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
            ft.Text(target, size=12, color=theme.TEXT_MUTED),
            ft.Text(last_perf, size=11, color=theme.PRIMARY, italic=True),
        ]

        # Promemoria specifico per esercizio (se matcha un infortunio attivo)
        injury_msg = self._esercizio_injury(ex_name)
        if injury_msg:
            card_body.append(
                ft.Text(injury_msg, size=11, color=theme.DANGER if hasattr(theme, "DANGER") else "#EF5350",
                        weight=ft.FontWeight.BOLD)
            )

        card_body += [
            ft.Divider(color=theme.BORDER, height=8),
            serie_rows,
            ft.Divider(color=theme.BORDER, height=4),
            note_field,
        ]

        return theme.card_container(
            ft.Column(card_body, spacing=6),
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

        # Stima del massimale teorico in tempo reale (Epley/Brzycki)
        rm_label = ft.Text(
            "1RM ≈ --",
            size=11,
            color=theme.GOLD if hasattr(theme, "GOLD") else "#FFD700",
            italic=True,
        )
        self._update_rm_label(ex_idx, s_idx, rm_label)
        self._rm_labels[(ex_idx, s_idx)] = rm_label

        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(f"Serie {s_idx + 1}", size=13, color=theme.TEXT_MUTED, width=60),
                        peso_field,
                        reps_field,
                        ft.Container(expand=True),
                        check_btn,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Row(
                    [ft.Container(width=60), rm_label],
                    spacing=4,
                ),
            ],
            spacing=0,
        )

    def _update_rm_label(self, ex_idx, s_idx, label: ft.Text):
        """Aggiorna il testo del massimale stimato per una data serie."""
        peso = self.session[ex_idx][s_idx].get("peso", 0)
        reps = self.session[ex_idx][s_idx].get("reps", 0)
        try:
            rm = fitness_calc.stima_1rm(float(peso), int(reps))
            if rm and rm > 0:
                label.value = f"1RM ≈ {rm} kg"
            else:
                label.value = "1RM ≈ --"
        except (TypeError, ValueError):
            label.value = "1RM ≈ --"

    async def _global_timer_loop(self):
        """Aggiorna ogni secondo il cronometro globale della sessione."""
        while self.global_timer_running:
            await asyncio.sleep(1)
            self.elapsed_seconds += 1
            mins, secs = divmod(self.elapsed_seconds, 60)
            hrs, mins = divmod(mins, 60)
            if hrs > 0:
                self.global_timer_text.value = f"{hrs:02d}:{mins:02d}:{secs:02d}"
            else:
                self.global_timer_text.value = f"{mins:02d}:{secs:02d}"
            if self.page:
                self.page.update()

    def _update_serie(self, ex_idx, s_idx, campo, value):
        if campo == "peso":
            try:
                value = round(float(value.replace(",", ".")), 2) if value else 0
            except ValueError:
                value = self.session[ex_idx][s_idx]["peso"]
        self.session[ex_idx][s_idx][campo] = value

        # Aggiorna in tempo reale l'etichetta del massimale stimato
        label = self._rm_labels.get((ex_idx, s_idx))
        if label is not None:
            self._update_rm_label(ex_idx, s_idx, label)
            if self.page:
                self.page.update()

    def _toggle_serie_completata(self, ex_idx, s_idx):
        serie = self.session[ex_idx][s_idx]
        serie["completata"] = not serie["completata"]

        btn = self._check_buttons[(ex_idx, s_idx)]
        btn.icon = ft.Icons.CHECK_CIRCLE if serie["completata"] else ft.Icons.RADIO_BUTTON_UNCHECKED
        btn.icon_color = theme.SUCCESS if serie["completata"] else theme.TEXT_MUTED
        self.page.update()

        if serie["completata"]:
            self._start_rest_timer()

    def _on_default_duration_change(self, e):
        self.rest_default_seconds = int(self.rest_slider.value)

    def _start_rest_timer(self):
        self.rest_seconds_remaining = self.rest_default_seconds
        self.rest_running = True
        self.timer_status.value = "Recupero in corso..."
        self.timer_status.color = theme.TEXT_MUTED
        self._refresh_timer_ui()
        self.timer_dialog_open = True
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
        if self.timer_dialog_open:
            self.timer_dialog_open = False
            try:
                self.page.close(self.timer_dialog)
            except Exception:
                pass

    def _on_back(self, e):
        self.rest_running = False
        # Ferma il cronometro globale per evitare continui aggiornamenti
        # della pagina (che rendono lento/laggy il dialog di conferma).
        self.global_timer_running = False
        # Chiudi subito l'eventuale dialog del rest timer ancora aperto,
        # altrimenti il nuovo dialog di conferma potrebbe non rispondere.
        self._close_timer()

        def conferma(ev):
            self.page.close(confirm_dialog)
            self.app.show_selection()

        def annulla(ev):
            self.page.close(confirm_dialog)
            # L'utente resta in allenamento: riavvia il cronometro globale
            self.global_timer_running = True
            if self.page:
                self.page.run_task(self._global_timer_loop)

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Uscire dall'allenamento?"),
            content=ft.Text("I progressi di questa sessione non salvata andranno persi."),
            actions=[
                ft.TextButton("Annulla", on_click=annulla),
                ft.TextButton("Esci", on_click=conferma),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(confirm_dialog)
        self.page.update()

    def _on_finish(self, e):
        self.rest_running = False
        self.global_timer_running = False
        # Chiudi subito l'eventuale dialog del rest timer ancora aperto.
        self._close_timer()

        def conferma(ev):
            self.page.close(confirm_dialog)
            self._salva_sessione()

        def annulla(ev):
            self.page.close(confirm_dialog)
            self.global_timer_running = True
            if self.page:
                self.page.run_task(self._global_timer_loop)

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Terminare l'allenamento?"),
            content=ft.Text("Vedrai il riepilogo finale con statistiche, foto, manubri e nota, poi l'allenamento verrà salvato."),
            actions=[
                ft.TextButton("Annulla", on_click=annulla),
                ft.TextButton("Termina", on_click=conferma),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(confirm_dialog)
        self.page.update()

    def _salva_sessione(self):
        self.global_timer_running = False
        esercizi_storico = []
        for ex_idx, esercizio in enumerate(self.giorno["esercizi"]):
            serie_svolte = [dict(s) for s in self.session[ex_idx]]
            note_text = self._note_fields[ex_idx].value if ex_idx in self._note_fields and self._note_fields[ex_idx].value else ""

            esercizi_storico.append({
                "nome": esercizio.get("nome", ""), 
                "serie_svolte": serie_svolte,
                "note": note_text
            })

        # Formatta la durata totale trascorsa in una stringa leggibile (es. "1h 12m" o "45m")
        m, s = divmod(self.elapsed_seconds, 60)
        h, m = divmod(m, 60)
        durata_str = f"{h}h {m}m" if h > 0 else f"{m}m {s}s"

        sessione = {
            "data": dm.today_str(),
            "giorno_nome": self.giorno.get("nome", ""),
            "durata": durata_str,
            "note_generali": self.general_notes_field.value if self.general_notes_field.value else "",
            "esercizi": esercizi_storico,
        }

        # Rileva eventuali nuovi Record Personali confrontando lo storico
        # PRIMA e DOPO l'inserimento di questa sessione, per poterli
        # celebrare con un badge a fine allenamento. In modalità modifica
        # di un allenamento passato i record non vengono ricalcolati.
        if self.edit_session is not None:
            nuovi_pr = []
        else:
            nuovi_pr = pr_manager.detect_new_prs(self.app.data.get("storico", []), sessione)

        # Apre il riepilogo finale (statistiche, foto, manubri, note): la
        # sessione viene registrata/sovrascritta SOLO alla conferma.
        self.app.show_workout_summary(
            sessione,
            nuovi_pr,
            modify_index=self.edit_index,
        )


def build_training_view(app, giorno_selezionato: dict, edit_session: dict = None, edit_index: int = None) -> ft.Control:
    """Funzione helper per compatibilità con il router principale.

    - Se `edit_session` è fornito apre la schermata in modalità MODIFICA,
      ricaricando esattamente lo stato (pesi, reps, spunte, note) della
      sessione passata. Al salvataggio l'allenamento viene sovrascritto.
    - Altrimenti avvia un allenamento nuovo per il giorno selezionato.
    """
    if edit_session is not None:
        view_instance = TrainingView(app, -1, edit_session=edit_session, edit_index=edit_index)
        return view_instance.build()

    # Trova l'indice del giorno selezionato all'interno della scheda
    giorni = app.data["scheda"]["giorni"]
    g_idx = 0
    for idx, g in enumerate(giorni):
        if g.get("nome") == giorno_selezionato.get("nome"):
            g_idx = idx
            break

    view_instance = TrainingView(app, g_idx)
    return view_instance.build()