"""
training_view.py
------------------
Schermata C + D - Training Attivo, Rest Timer e nuove funzioni avanzate.
"""

import asyncio
import re
import time

import flet as ft
import theme
import data_manager as dm
import pr_manager
import fitness_calc

REST_MAX_SECONDS = 180
REST_STEP_SECONDS = 30
REST_DEFAULT_SECONDS = 90
REST_WARNING_THRESHOLD = 10

TIPO_RISCALDAMENTO = [
    "Cardio leggero",
    "Cyclette",
    "Rowing machine",
    "Corda",
    "Mobilità articolare",
    "Stretching dinamico",
    "Tecnica a vuoto",
    "Attivazione muscolare",
]

TIPO_DEFATICAMENTO = [
    "Stretching statico",
    "Cardio leggero",
    "Deambulazione",
    "Respirazione",
    "Foam roller / massaggio",
    "Riposo",
]


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
        # Basato su time.time() (orologio di parete): il tempo trascorso
        # viene ricalcolato dal timestamp a ogni aggiornamento, quindi resta
        # corretto anche se l'app va in background o lo schermo si spegne:
        # l'orologio di parete continua a scorrere durante la sospensione,
        # a differenza di time.monotonic() che su Android/iOS si ferma.
        self.session_start_wall = time.time()
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
            # Copia il giorno della scheda: gli esercizi aggiunti durante la
            # sessione (feature "Aggiungi esercizio") non devono alterare la
            # scheda originale salvata.
            giorno_sorgente = app.data["scheda"]["giorni"][giorno_index]
            self.giorno = {
                "nome": giorno_sorgente.get("nome", "Allenamento"),
                "esercizi": [dict(e) for e in giorno_sorgente.get("esercizi", [])],
            }
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
        self.rest_running = False
        self.timer_dialog_open = False
        # Timestamp assoluto (epoch) in cui il recupero deve terminare. Il
        # countdown viene sempre ricalcolato da questo istante, così anche se
        # l'app va in background / lo schermo si spegne, al rientro il tempo
        # residuo è quello reale (o è già scaduto).
        self.rest_end_time = None

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

        # --- Fasi opzionali: Riscaldamento (prima) e Defaticamento (dopo) ---
        # Ogni voce ha {tipo, minuti, note}. Vengono salvate nella sessione.
        self.risc_data = [dict(x) for x in ((edit_session or {}).get("riscaldamento") or [])]
        self.defat_data = [dict(x) for x in ((edit_session or {}).get("defaticamento") or [])]
        self.risc_items_col = ft.Column(spacing=6)
        self.defat_items_col = ft.Column(spacing=6)
        self.risc_body = None
        self.defat_body = None
        self.risc_switch = ft.Switch(
            label="Riscaldamento",
            value=bool(self.risc_data),
            on_change=lambda e: self._toggle_fase("risc"),
        )
        self.defat_switch = ft.Switch(
            label="Defaticamento",
            value=bool(self.defat_data),
            on_change=lambda e: self._toggle_fase("defat"),
        )

    # ------------------------------------------------------------------
    # Costruzione UI principale
    # ------------------------------------------------------------------
    def build(self) -> ft.Control:
        header = ft.Row(
            [
                theme.back_button(self._on_back),
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

        self._rebuild_fase("risc")
        self._rebuild_fase("defat")

        self.esercizi_list = ft.ListView(
            controls=self._build_list_controls(),
            expand=True,
            spacing=14,
        )

        add_ex_btn = ft.OutlinedButton(
            "Aggiungi esercizio",
            icon=ft.Icons.ADD_CIRCLE_OUTLINE,
            icon_color=theme.PRIMARY,
            style=ft.ButtonStyle(color=theme.PRIMARY),
            on_click=lambda e: self._open_add_exercise_dialog(),
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
                self.esercizi_list,
                add_ex_btn,
                finish_btn,
            ],
            expand=True,
            spacing=8,
        )

    def _build_list_controls(self) -> list:
        """Ricostruisce tutti i controlli della ListView degli esercizi."""
        esercizi_controls = [
            self._build_esercizio_card(idx, esercizio)
            for idx, esercizio in enumerate(self.giorno["esercizi"])
        ]
        return (
            [self._build_fase_card("risc")]
            + self._build_injury_controls()
            + [self.general_notes_field]
            + esercizi_controls
            + [self._build_fase_card("defat")]
        )

    def _open_add_exercise_dialog(self):
        """Dialog per aggiungere a caldo un esercizio (nuovo o da uno già
        esistente in scheda/storico) alla sessione in corso, senza toccare
        la scheda salvata."""

        def _existing_options() -> list:
            nomi = []
            visti = set()
            for g in self.app.data.get("scheda", {}).get("giorni", []):
                for ex in g.get("esercizi", []):
                    nome = (ex.get("nome") or "").strip()
                    key = nome.lower()
                    if nome and key not in visti:
                        visti.add(key)
                        nomi.append(nome)
            for sess in self.app.data.get("storico", []):
                for ex in sess.get("esercizi", []):
                    nome = (ex.get("nome") or "").strip()
                    key = nome.lower()
                    if nome and key not in visti:
                        visti.add(key)
                        nomi.append(nome)
            return sorted(nomi, key=str.lower)

        nome_field = ft.TextField(
            label="Nome nuovo esercizio",
            dense=True,
            border_color=theme.BORDER,
            focused_border_color=theme.PRIMARY,
        )
        serie_field = ft.TextField(
            label="Serie", dense=True, width=70,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=theme.BORDER, focused_border_color=theme.PRIMARY,
        )
        reps_field = ft.TextField(
            label="Ripetizioni", dense=True, width=90,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=theme.BORDER, focused_border_color=theme.PRIMARY,
        )
        peso_field = ft.TextField(
            label="Peso rif. (kg)", dense=True, width=100,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=theme.BORDER, focused_border_color=theme.PRIMARY,
        )

        options = _existing_options()
        es_dd = ft.Dropdown(
            label="Oppure scegli uno esistente",
            options=[ft.dropdown.Option(n, n) for n in options] if options else [],
            dense=True,
            border_color=theme.BORDER,
            focused_border_color=theme.PRIMARY,
            on_change=lambda e: self._fill_exercise_from_dropdown(
                e.control.value, nome_field, serie_field, reps_field, peso_field),
        )

        def _parse_int(tf, fallback):
            v = (tf.value or "").strip().replace(",", ".")
            if not v:
                return fallback
            try:
                return max(1, int(float(v)))
            except ValueError:
                return fallback

        def _parse_float(tf):
            v = (tf.value or "").strip().replace(",", ".")
            if not v:
                return 0
            try:
                return float(v)
            except ValueError:
                return 0

        def conferma(ev):
            self.page.close(dlg)
            nome = (nome_field.value or "").strip()
            if not nome:
                self.page.open(ft.SnackBar(content=ft.Text("Inserisci un nome per l'esercizio."), bgcolor=theme.WARNING))
                self.page.update()
                return
            serie = _parse_int(serie_field, 3)
            reps = (reps_field.value or "").strip()
            peso = _parse_float(peso_field)

            self.giorno["esercizi"].append({
                "nome": nome,
                "serie": serie,
                "peso_riferimento": peso,
                "ripetizioni": reps,
            })
            self.session.append([
                {"peso": peso, "reps": _parse_target_reps(reps), "completata": False}
                for _ in range(serie)
            ])
            self._rebuild_exercise_list()
            self.page.open(ft.SnackBar(content=ft.Text("Esercizio aggiunto alla sessione!"), bgcolor=theme.SUCCESS))
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            bgcolor=theme.BG_CARD,
            title=ft.Text("Aggiungi esercizio", color=theme.TEXT, weight=ft.FontWeight.BOLD),
            content=ft.Column(
                [
                    nome_field,
                    es_dd,
                    ft.Row([serie_field, reps_field, peso_field], spacing=8),
                    ft.Text("Scegli un nome oppure seleziona uno già esistente; serie, ripetizioni e peso restano modificabili durante l'allenamento.",
                            size=12, color=theme.TEXT_MUTED, italic=True),
                ],
                tight=True,
                spacing=10,
            ),
            actions=[
                ft.TextButton("Annulla", on_click=lambda e: self.page.close(dlg)),
                ft.FilledButton("Aggiungi", on_click=conferma),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.open(dlg)
        self.page.update()

    def _fill_exercise_from_dropdown(self, nome, nome_field, serie_field, reps_field, peso_field):
        """Precompila i campi con l'ultima prestazione nota dell'esercizio
        scelto (default dalla scheda, altrimenti dall'ultimo storico)."""
        nome = (nome or "").strip()
        if not nome:
            return
        ex_rif = None
        for g in self.app.data.get("scheda", {}).get("giorni", []):
            for ex in g.get("esercizi", []):
                if (ex.get("nome") or "").strip().lower() == nome.lower():
                    ex_rif = ex
                    break
            if ex_rif:
                break
        if ex_rif is None:
            for sess in reversed(self.app.data.get("storico", [])):
                for ex in sess.get("esercizi", []):
                    if (ex.get("nome") or "").strip().lower() == nome.lower() and ex.get("serie_svolte"):
                        ultima = ex["serie_svolte"][-1]
                        ex_rif = {
                            "serie": len(ex["serie_svolte"]),
                            "ripetizioni": ultima.get("reps", ""),
                            "peso_riferimento": ultima.get("peso", 0),
                        }
                        break
                if ex_rif:
                    break

        nome_field.value = nome
        serie_field.value = str(ex_rif.get("serie", 3) or 3) if ex_rif else ""
        reps_field.value = str(ex_rif.get("ripetizioni", "") or "") if ex_rif else ""
        peso_field.value = str(ex_rif.get("peso_riferimento", 0) or 0) if ex_rif else ""
        if self.page:
            self.page.update()

    def _rebuild_exercise_list(self):
        """Rigenera i controlli della lista esercizi dopo l'aggiunta."""
        self._check_buttons.clear()
        self._note_fields.clear()
        self._rm_labels.clear()
        self.esercizi_list.controls = self._build_list_controls()
        self.page.update()

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
    # Fasi opzionali: Riscaldamento (prima degli esercizi) e Defaticamento
    # ------------------------------------------------------------------
    def _fase_dati(self, which) -> list:
        return self.risc_data if which == "risc" else self.defat_data

    def _fase_col(self, which) -> ft.Column:
        return self.risc_items_col if which == "risc" else self.defat_items_col

    def _fase_tipi(self, which) -> list:
        return TIPO_RISCALDAMENTO if which == "risc" else TIPO_DEFATICAMENTO

    def _fase_switch(self, which) -> ft.Switch:
        return self.risc_switch if which == "risc" else self.defat_switch

    def _fase_body(self, which):
        return self.risc_body if which == "risc" else self.defat_body

    def _toggle_fase(self, which):
        switch = self._fase_switch(which)
        body = self._fase_body(which)
        if body is not None:
            body.visible = switch.value
        if switch.value and not self._fase_dati(which):
            self._add_fase_item(which)
        else:
            self.page.update()

    def _add_fase_item(self, which):
        self._fase_dati(which).append(
            {"tipo": self._fase_tipi(which)[0], "minuti": None, "note": ""})
        self._rebuild_fase(which)
        self.page.update()

    def _remove_fase_item(self, which, idx):
        dati = self._fase_dati(which)
        if 0 <= idx < len(dati):
            dati.pop(idx)
            self._rebuild_fase(which)
            self.page.update()

    def _rebuild_fase(self, which):
        col = self._fase_col(which)
        dati = self._fase_dati(which)
        col.controls.clear()
        if not dati:
            col.controls.append(
                ft.Text("Nessuna voce: aggiungine una.", size=12, color=theme.TEXT_MUTED))
            return
        for idx, data in enumerate(dati):
            col.controls.append(self._build_fase_row(which, idx, data))

    @staticmethod
    def _set_fase_minuti(data: dict, value: str):
        v = (value or "").strip().replace(",", ".")
        if not v:
            data["minuti"] = None
            return
        try:
            data["minuti"] = max(1, int(float(v)))
        except ValueError:
            data["minuti"] = None

    def _build_fase_row(self, which: str, idx: int, data: dict) -> ft.Control:
        tipi = self._fase_tipi(which)
        tipo_value = data.get("tipo") or tipi[0]
        if tipo_value not in tipi:
            tipo_value = tipi[0]
        tipo = ft.Dropdown(
            label="Tipo",
            options=[ft.dropdown.Option(t, t) for t in tipi],
            value=tipo_value,
            dense=True,
            expand=True,
            on_change=lambda e, d=data: d.__setitem__("tipo", e.control.value),
        )
        minuti = ft.TextField(
            label="Minuti",
            dense=True,
            width=88,
            keyboard_type=ft.KeyboardType.NUMBER,
            value=str(data.get("minuti") or ""),
            on_change=lambda e, d=data: self._set_fase_minuti(d, e.control.value),
        )
        nota = ft.TextField(
            label="Descrizione (opzionale)",
            dense=True,
            expand=True,
            text_size=12,
            value=data.get("note") or "",
            on_change=lambda e, d=data: d.__setitem__("note", e.control.value),
        )
        elimina = ft.IconButton(
            ft.Icons.DELETE_OUTLINE,
            icon_color=theme.DANGER,
            icon_size=18,
            tooltip="Rimuovi voce",
            on_click=lambda e, w=which, i=idx: self._remove_fase_item(w, i),
        )
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row([tipo, minuti], spacing=6),
                    ft.Row([nota, elimina], spacing=6),
                ],
                spacing=6,
            ),
            padding=10,
            bgcolor=theme.BG_CARD_LIGHT,
            border_radius=theme.RADIUS_SMALL,
        )

    def _build_fase_card(self, which: str) -> ft.Control:
        switch = self._fase_switch(which)
        body = ft.Container(
            content=ft.Column(
                [
                    self._fase_col(which),
                    ft.OutlinedButton(
                        "Aggiungi voce",
                        icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                        on_click=lambda e, w=which: self._add_fase_item(w),
                    ),
                ],
                spacing=8,
            ),
            visible=switch.value,
        )
        if which == "risc":
            self.risc_body = body
            icona = ft.Icons.LOCAL_FIRE_DEPARTMENT
            colore = theme.WARNING
            sottotitolo = "Prima degli esercizi: cardio leggero, mobilità, stretching dinamico... (opzionale)"
        else:
            self.defat_body = body
            icona = ft.Icons.AC_UNIT
            colore = theme.INFO
            sottotitolo = "A fine allenamento: stretching statico, defaticamento... (opzionale)"
        return theme.card_container(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(icona, color=colore, size=20),
                            switch,
                            ft.Container(expand=True),
                            ft.Text("Opzionale", size=11, color=theme.TEXT_MUTED, italic=True),
                        ],
                        spacing=8,
                    ),
                    ft.Text(sottotitolo, size=11, color=theme.TEXT_MUTED),
                    body,
                ],
                spacing=6,
            )
        )

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

    def _elapsed_now(self) -> int:
        """Secondi trascorsi dall'inizio della sessione, calcolati con
        l'orologio di parete (avanza anche a schermo spento/in background)."""
        return max(0, int(time.time() - self.session_start_wall))

    async def _global_timer_loop(self):
        """Aggiorna ogni secondo il cronometro globale della sessione."""
        while self.global_timer_running:
            # Ricalcola sempre dal timestamp di inizio: così il totale è
            # corretto anche dopo un periodo con l'app in background o lo
            # schermo spento (l'orologio di parete avanza comunque).
            self.elapsed_seconds = self._elapsed_now()
            mins, secs = divmod(self.elapsed_seconds, 60)
            hrs, mins = divmod(mins, 60)
            if hrs > 0:
                self.global_timer_text.value = f"{hrs:02d}:{mins:02d}:{secs:02d}"
            else:
                self.global_timer_text.value = f"{mins:02d}:{secs:02d}"
            if self.page:
                self.page.update()
            await asyncio.sleep(1)

    def _update_serie(self, ex_idx, s_idx, campo, value):
        if campo == "peso":
            try:
                value = round(float(value.replace(",", ".")), 2) if value else 0
            except ValueError:
                value = self.session[ex_idx][s_idx]["peso"]
        elif campo == "reps":
            try:
                value = int(float(str(value).replace(",", "."))) if value else 0
            except ValueError:
                value = self.session[ex_idx][s_idx]["reps"]
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
        self.rest_end_time = time.time() + self.rest_default_seconds
        self.rest_running = True
        self.timer_status.value = "Recupero in corso..."
        self.timer_status.color = theme.TEXT_MUTED
        self._refresh_timer_ui()
        self.timer_dialog_open = True
        self.page.open(self.timer_dialog)
        self.page.run_task(self._countdown_loop)

    def _adjust_timer(self, delta_seconds: int):
        # Se il timer è attivo, sposta il timestamp di fine; altrimenti usa il
        # valore corrente come base (utile se fermo o appena scaduto).
        remaining = self._remaining_seconds()
        if remaining <= 0:
            base = self.rest_default_seconds
        else:
            base = remaining
        new_remaining = max(0, min(REST_MAX_SECONDS, base + delta_seconds))
        if new_remaining > 0:
            # Riconverte il residuo in un nuovo timestamp assoluto.
            self.rest_end_time = time.time() + new_remaining
            self.rest_running = True
            self.timer_status.value = "Recupero in corso..."
            self.timer_status.color = theme.TEXT_MUTED
        else:
            self.rest_end_time = None
            self.rest_running = False
            self.timer_status.value = "Tempo scaduto"
        self._refresh_timer_ui()

    def _remaining_seconds(self) -> int:
        """Secondi residui reali calcolati dal timestamp di scadenza."""
        if self.rest_end_time is None:
            return 0
        return max(0, int(self.rest_end_time - time.time()))

    async def _countdown_loop(self):
        while self.rest_running:
            remaining = self._remaining_seconds()
            if remaining <= 0:
                self._on_timer_finished()
                break
            self._refresh_timer_ui()
            await asyncio.sleep(1)
        # Un ultimo refresh quando il loop termina (es. timer scaduto).
        self._refresh_timer_ui()

    def _on_timer_finished(self):
        self.rest_running = False
        self.timer_status.value = "TEMPO SCADUTO! Torna a lavorare 🔥"
        self.timer_status.color = theme.WARNING
        self.page.open(self.timer_end_snack)
        self._refresh_timer_ui()

    def _refresh_timer_ui(self):
        remaining = self._remaining_seconds()
        mins, secs = divmod(max(0, remaining), 60)
        self.timer_text.value = f"{mins:02d}:{secs:02d}"
        total = max(1, self.rest_default_seconds)
        self.timer_progress.value = max(0.0, remaining / total)

        if 0 < remaining <= REST_WARNING_THRESHOLD:
            self.timer_text.color = theme.WARNING
            self.timer_progress.color = theme.WARNING
        elif remaining <= 0 and self.rest_running:
            self.timer_text.color = theme.DANGER
            self.timer_progress.color = theme.DANGER
        else:
            self.timer_text.color = theme.TEXT
            self.timer_progress.color = theme.PRIMARY

        if self.page:
            self.page.update()

    def _close_timer(self):
        self.rest_running = False
        self.rest_end_time = None
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
        # Il calcolo usa l'orologio di parete: la durata è corretta anche se
        # lo schermo è rimasto spento o l'app in background durante la sessione.
        m, s = divmod(self._elapsed_now(), 60)
        h, m = divmod(m, 60)
        durata_str = f"{h}h {m}m" if h > 0 else f"{m}m {s}s"

        risc = self._fase_da_salvare(self.risc_switch, self.risc_data)
        defa = self._fase_da_salvare(self.defat_switch, self.defat_data)

        sessione = {
            "data": dm.today_str(),
            "giorno_nome": self.giorno.get("nome", ""),
            "durata": durata_str,
            "note_generali": self.general_notes_field.value if self.general_notes_field.value else "",
            "esercizi": esercizi_storico,
        }
        if risc is not None:
            sessione["riscaldamento"] = risc
        if defa is not None:
            sessione["defaticamento"] = defa

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

    @staticmethod
    def _fase_da_salvare(switch, items):
        """Ritorna la lista di voci {tipo,minuti,note} da salvare, oppure
        None se la fase è disattivata o completamente vuota."""
        if not switch.value:
            return None
        lista = []
        for it in items:
            tipo = (it.get("tipo") or "").strip()
            minuti = it.get("minuti")
            note = (it.get("note") or "").strip()
            if tipo or minuti or note:
                lista.append({"tipo": tipo, "minuti": minuti, "note": note})
        return lista or None


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