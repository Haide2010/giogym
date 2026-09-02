"""
workout_summary_view.py
-----------------------
Riepilogo a fine allenamento (o in modifica di un allenamento passato):
- mostra tutte le statistiche della sessione appena completata
- permette di allegare opzionalmente una foto dell'allenamento
- permette di dare una valutazione da 1 a 5 "manubri" (opzionale)
- permette di scrivere una nota generale della sessione

Alla conferma la sessione viene registrata (nuova) o sovrascritta
(quando si sta modificando un allenamento passato).
"""

import os
import shutil
from datetime import datetime

import flet as ft
import theme
import data_manager as dm


def _compute_stats(sessione: dict) -> dict:
    """Calcola le statistiche riassuntive della sessione."""
    esercizi = sessione.get("esercizi", [])
    n_esercizi = len(esercizi)
    n_serie = 0
    n_serie_completate = 0
    n_reps = 0
    volume = 0.0

    for ex in esercizi:
        for s in ex.get("serie_svolte", []):
            n_serie += 1
            peso = float(s.get("peso", 0) or 0)
            reps = int(s.get("reps", 0) or 0)
            n_reps += reps
            volume += peso * reps
            if s.get("completata"):
                n_serie_completate += 1

    return {
        "n_esercizi": n_esercizi,
        "n_serie": n_serie,
        "n_serie_completate": n_serie_completate,
        "n_reps": n_reps,
        "volume": round(volume, 1),
        "durata": sessione.get("durata", "-"),
        "giorno_nome": sessione.get("giorno_nome", "Allenamento"),
        "data": sessione.get("data", dm.today_str()),
    }


class WorkoutSummaryView:
    """Vista stateful: riepilogo a fine allenamento con foto/manubri/note."""

    def __init__(self, app, sessione: dict, nuovi_pr: list, modify_index=None):
        self.app = app
        self.page = app.page
        self.sessione = sessione
        self.nuovi_pr = nuovi_pr or []
        self.modify_index = modify_index  # indice in storico se in modifica

        self.stats = _compute_stats(sessione)

        # Stato foto
        self.foto_path = sessione.get("foto", "")

        # Stato valutazione (1-5 manubri, 0 = non data)
        try:
            self.valutazione = int(sessione.get("valutazione", 0) or 0)
        except (TypeError, ValueError):
            self.valutazione = 0
        self.valutazione = max(0, min(5, self.valutazione))

        # Nota generale (precaricata se sto modificando una sessione)
        self.nota_generale = sessione.get("note_generali", "")

        # Controllo per aggiornare dinamicamente la foto nella UI
        self.foto_preview = ft.Container()

        # Controlli valutazione (manubri cliccabili)
        self.dumbbells: list = []

    # ------------------------------------------------------------------
    # Helper foto
    # ------------------------------------------------------------------
    def _persisti_foto(self, src_path: str) -> str:
        """Copia la foto nella cartella dati persistente dell'app e ne
        ritorna il percorso salvato. Su desktop copia in locale."""
        try:
            estensione = os.path.splitext(src_path)[1] or ".jpg"
            nome = f"workout_{datetime.now().strftime('%Y%m%d_%H%M%S')}{estensione}"
            data_dir = os.path.dirname(dm.get_data_path())
            os.makedirs(data_dir, exist_ok=True)
            dest = os.path.join(data_dir, nome)
            shutil.copy2(src_path, dest)
            return dest
        except OSError:
            # Se non riusciamo a copiare, teniamo comunque il percorso originale
            return src_path

    def _on_pick_foto(self, e: ft.FilePickerResultEvent):
        if e.files and e.files[0].path:
            self.foto_path = e.files[0].path
            self._aggiorna_preview_foto()
            self.page.update()

    def _deseleziona_foto(self, e):
        self.foto_path = ""
        self._aggiorna_preview_foto()
        self.page.update()

    def _aggiorna_preview_foto(self):
        if self.foto_path:
            try:
                self.foto_preview.content = ft.Image(
                    src=self.foto_path,
                    fit=ft.ImageFit.COVER,
                    height=180,
                    border_radius=theme.RADIUS,
                )
            except Exception:
                self.foto_preview.content = ft.Text(
                    "Immagine non disponibile", color=theme.TEXT_MUTED, size=12
                )
        else:
            self.foto_preview.content = ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.ADD_A_PHOTO, color=theme.TEXT_MUTED, size=40),
                        ft.Text("Aggiungi una foto dell'allenamento (opzionale)",
                                color=theme.TEXT_MUTED, size=12),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                ),
                alignment=ft.alignment.center,
                height=120,
                bgcolor=theme.BG_CARD_LIGHT,
                border_radius=theme.RADIUS,
                border=ft.border.all(1, theme.BORDER),
                ink=True,
                on_click=lambda e: self._scegli_foto(),
            )

    # ------------------------------------------------------------------
    # Valutazione (manubri)
    # ------------------------------------------------------------------
    def _scegli_foto(self, ev=None):
        self.foto_picker.pick_files(
            dialog_title="Seleziona una foto dell'allenamento",
            allow_multiple=False,
            allowed_extensions=["jpg", "jpeg", "png", "gif", "bmp", "webp"],
        )

    def _set_valutazione(self, valore: int):
        self.valutazione = valore
        self._refresh_valutazione()
        self.page.update()

    def _refresh_valutazione(self):
        for i, btn in enumerate(self.dumbbells):
            pieno = (i + 1) <= self.valutazione
            btn.icon_color = theme.PRIMARY if pieno else theme.TEXT_MUTED

    def _build_valutazione_row(self) -> ft.Row:
        self.dumbbells = []
        for i in range(1, 6):
            btn = ft.IconButton(
                icon=ft.Icons.FITNESS_CENTER,
                icon_size=30,
                icon_color=theme.PRIMARY if i <= self.valutazione else theme.TEXT_MUTED,
                tooltip=f"{i} manubri",
                on_click=lambda e, v=i: self._set_valutazione(v),
            )
            self.dumbbells.append(btn)
        return ft.Row(self.dumbbells, spacing=4, alignment=ft.MainAxisAlignment.CENTER)

    # ------------------------------------------------------------------
    # Costruzione UI
    # ------------------------------------------------------------------
    def build(self) -> ft.Control:
        self.foto_picker = ft.FilePicker(on_result=self._on_pick_foto)
        if self.foto_picker not in self.page.overlay:
            self.page.overlay.append(self.foto_picker)

        self._aggiorna_preview_foto()

        header = ft.Row(
            [
                ft.Icon(ft.Icons.CELEBRATION, color=theme.PRIMARY, size=28),
                ft.Text("Riepilogo allenamento", size=theme.TITLE_SIZE,
                        weight=ft.FontWeight.BOLD, color=theme.TEXT),
            ],
            spacing=10,
        )

        # --- Card statistiche ---
        stats_grid = ft.Row(
            [
                self._stat_box(str(self.stats["n_esercizi"]), "Esercizi", theme.INFO),
                self._stat_box(str(self.stats["n_serie"]), "Serie", theme.PRIMARY),
                self._stat_box(str(self.stats["n_reps"]), "Reps totali", theme.SUCCESS),
                self._stat_box(f"{self.stats['volume']} kg", "Volume", theme.GOLD),
            ],
            spacing=8,
            wrap=True,
        )

        stats_card = theme.card_container(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.BAR_CHART, color=theme.PRIMARY, size=20),
                            ft.Text("Le tue statistiche", size=theme.SUBTITLE_SIZE,
                                    weight=ft.FontWeight.BOLD, color=theme.TEXT),
                        ],
                        spacing=8,
                    ),
                    stats_grid,
                    ft.Divider(color=theme.BORDER, height=10),
                    ft.Row(
                        [
                            ft.Row([
                                ft.Icon(ft.Icons.TIMER, color=theme.PRIMARY, size=18),
                                ft.Text(f"Durata: {self.stats['durata']}", color=theme.TEXT, size=13),
                            ], spacing=6),
                            ft.Row([
                                ft.Icon(ft.Icons.CHECK_CIRCLE, color=theme.SUCCESS, size=18),
                                ft.Text(f"{self.stats['n_serie_completate']}/{self.stats['n_serie']} serie completate",
                                        color=theme.TEXT, size=13),
                            ], spacing=6),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        wrap=True,
                    ),
                ],
                spacing=10,
            ),
        )

        # --- Badge nuovi PR ---
        controls = []
        if self.nuovi_pr:
            righe = [ft.Row([
                ft.Icon(ft.Icons.EMOJI_EVENTS, color=theme.GOLD, size=18),
                ft.Text(msg, color=theme.TEXT, size=13, weight=ft.FontWeight.BOLD),
            ], spacing=6) for msg in self.nuovi_pr]
            pr_card = theme.card_container(
                ft.Column(
                    [
                        ft.Row([
                            ft.Icon(ft.Icons.EMOJI_EVENTS, color=theme.GOLD, size=22),
                            ft.Text("Nuovi Record Personali!", size=theme.SUBTITLE_SIZE,
                                    weight=ft.FontWeight.BOLD, color=theme.GOLD),
                        ], spacing=8),
                        *righe,
                    ],
                    spacing=8,
                ),
                bgcolor=theme.BG_CARD,
            )
            controls.append(pr_card)

        # --- Fotografia ---
        foto_actions = ft.Row(
            [
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.ADD_A_PHOTO, color="white"),
                        ft.Text("Scegli foto" if not self.foto_path else "Cambia foto",
                                weight=ft.FontWeight.BOLD),
                    ], spacing=8),
                    bgcolor=theme.PRIMARY,
                    color="white",
                    on_click=lambda e: self._scegli_foto(),
                ),
                ft.OutlinedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.DELETE_OUTLINE, color=theme.TEXT),
                        ft.Text("Rimuovi"),
                    ], spacing=8),
                    visible=bool(self.foto_path),
                    on_click=self._deseleziona_foto,
                ),
            ],
            spacing=10,
            wrap=True,
        )

        foto_card = theme.card_container(
            ft.Column(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.PHOTO_CAMERA, color=theme.INFO, size=20),
                        ft.Text("Foto dell'allenamento (opzionale)", size=theme.SUBTITLE_SIZE,
                                weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ], spacing=8),
                    self.foto_preview,
                    foto_actions,
                ],
                spacing=10,
            ),
        )

        # --- Valutazione a manubri ---
        valutazione_card = theme.card_container(
            ft.Column(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.STAR, color=theme.GOLD, size=20),
                        ft.Text("Come valuti l'allenamento? (opzionale)", size=theme.SUBTITLE_SIZE,
                                weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ], spacing=8),
                    self._build_valutazione_row(),
                    ft.Text(
                        f"{self.valutazione}/5" if self.valutazione else "Tocca i manubri per assegnare la valutazione",
                        size=12, color=theme.TEXT_MUTED, text_align=ft.TextAlign.CENTER,
                    ),
                ],
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        # --- Nota generale ---
        nota_field = ft.TextField(
            label="Nota generale dell'allenamento (opzionale)",
            value=self.nota_generale,
            multiline=True,
            min_lines=3,
            max_lines=6,
            border_color=theme.BORDER,
            focused_border_color=theme.PRIMARY,
            text_size=13,
            on_change=lambda e: self._set_nota(e.control.value),
        )

        nota_card = theme.card_container(
            ft.Column(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.NOTES, color=theme.INFO, size=20),
                        ft.Text("Nota dell'allenamento", size=theme.SUBTITLE_SIZE,
                                weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ], spacing=8),
                    nota_field,
                ],
                spacing=10,
            ),
        )

        controls.extend([stats_card, foto_card, valutazione_card, nota_card])

        # --- Pulsante conferma ---
        confirm_btn = ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.DONE_ALL, color=ft.Colors.WHITE),
                    ft.Text("CONFERMA E SALVA", weight=ft.FontWeight.BOLD),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=theme.SUCCESS,
            color=ft.Colors.WHITE,
            height=56,
            on_click=self._on_confirm,
        )

        content_list = ft.ListView(
            [header, *controls, confirm_btn],
            expand=True,
            spacing=12,
        )

        return ft.Column([content_list], expand=True)

    def _stat_box(self, valore: str, etichetta: str, colore: str) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(valore, size=18, weight=ft.FontWeight.BOLD, color=colore),
                    ft.Text(etichetta, size=10, color=theme.TEXT_MUTED),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            padding=10,
            bgcolor=theme.BG_CARD_LIGHT,
            border_radius=10,
            expand=True,
        )

    def _set_nota(self, value):
        self.nota_generale = value

    def _on_confirm(self, e):
        # Applica foto (persistita), valutazione e nota alla sessione
        if self.foto_path:
            self.sessione["foto"] = self._persisti_foto(self.foto_path)
        self.sessione["valutazione"] = self.valutazione
        self.sessione["note_generali"] = self.nota_generale

        storico = self.app.data.get("storico", [])

        if self.modify_index is not None and 0 <= self.modify_index < len(storico):
            # Sovrascrive l'allenamento passato mantenendo data e nome giorno
            precedente = storico[self.modify_index]
            self.sessione["data"] = precedente.get("data", dm.today_str())
            self.sessione["giorno_nome"] = precedente.get("giorno_nome", self.sessione.get("giorno_nome", "Allenamento"))
            storico[self.modify_index] = self.sessione
        else:
            # Nuovo allenamento
            storico.append(self.sessione)
            # Aggiorna i pesi di riferimento della scheda con l'ultimo peso
            # usato in ciascun esercizio (ora che la sessione è nello storico).
            self._aggiorna_pesi_riferimento()

        self.app.save()

        if self.nuovi_pr:
            self._mostra_badge_pr()
        else:
            self.app.show_home()

    def _aggiorna_pesi_riferimento(self):
        """Aggiorna i pesi di riferimento della scheda con l'ultimo peso
        usato in ciascun esercizio (solo per allenamenti nuovi)."""
        giorni = self.app.data["scheda"].get("giorni", [])
        for g in giorni:
            for idx, ex in enumerate(g.get("esercizi", [])):
                nome = ex.get("nome", "").strip()
                ultimo = None
                for sessione in reversed(self.app.data.get("storico", [])):
                    trovata = False
                    for es in sessione.get("esercizi", []):
                        if es.get("nome", "").strip() == nome and es.get("serie_svolte"):
                            ultimo = es["serie_svolte"][-1].get("peso", ex.get("peso_riferimento", 0))
                            trovata = True
                            break
                    if trovata:
                        break
                if nome and ultimo is not None:
                    try:
                        ex["peso_riferimento"] = float(ultimo)
                    except (ValueError, TypeError):
                        pass

    def _mostra_badge_pr(self):
        def _chiudi(ev):
            self.page.close(dlg)
            self.app.show_home()

        righe = [
            ft.Row([
                ft.Icon(ft.Icons.EMOJI_EVENTS, color=theme.GOLD, size=18),
                ft.Text(msg, size=13, color=theme.TEXT, weight=ft.FontWeight.BOLD),
            ], spacing=6)
            for msg in self.nuovi_pr
        ]

        dlg = ft.AlertDialog(
            modal=True,
            bgcolor=theme.BG_CARD,
            title=ft.Row(
                [ft.Icon(ft.Icons.EMOJI_EVENTS, color=theme.GOLD, size=28),
                 ft.Text("Nuovi Record! 🎉", color=theme.TEXT, weight=ft.FontWeight.BOLD)],
                spacing=8,
            ),
            content=ft.Column(righe, spacing=8, tight=True),
            actions=[ft.ElevatedButton("Fantastico!", bgcolor=theme.PRIMARY, color="white", on_click=_chiudi)],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )
        self.page.open(dlg)


def build_workout_summary_view(app, sessione: dict, nuovi_pr: list, modify_index=None) -> ft.Control:
    """Funzione helper per compatibilità con il router principale."""
    view = WorkoutSummaryView(app, sessione, nuovi_pr, modify_index=modify_index)
    return view.build()
