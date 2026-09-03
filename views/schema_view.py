"""
schema_view.py
---------------
Editor della scheda di allenamento.
Non è una delle schermate esplicitamente elencate nelle specifiche, ma è
indispensabile: senza un modo per configurare giorni/esercizi l'app non
avrebbe dati su cui lavorare. Si raggiunge dall'icona ingranaggio in Home.

Permette di:
- aggiungere/rimuovere/riordinare giorni (da 1 a 7), duplicarli
- rinominare ogni giorno e aggiungere una nota libera (es. "scarico")
- aggiungere/rimuovere/riordinare esercizi per ogni giorno
- impostare nome, serie, ripetizioni target, peso di riferimento e
  tempo di recupero specifico per ciascun esercizio
"""

import copy

import flet as ft
import theme
import data_manager as dm

MAX_GIORNI = 7
MIN_GIORNI = 1


class SchemaEditorView:
    """Vista stateful per l'editing della scheda. Lavora su una copia
    profonda dei dati e salva solo al click su "Salva scheda"."""

    def __init__(self, app):
        self.app = app
        self.page = app.page
        # Copia di lavoro (evita di modificare app.data finché non si salva)
        self.giorni = copy.deepcopy(app.data["scheda"]["giorni"])
        # Compatibilità: garantisce che ogni giorno/esercizio abbia i
        # nuovi campi anche se la scheda è stata creata con una
        # versione precedente dell'app.
        for g in self.giorni:
            g.setdefault("note", "")
            for ex in g.get("esercizi", []):
                ex.setdefault("rest_seconds", 90)

        self.giorni_column = ft.Column(spacing=14)
        self.info_text = ft.Text("", color=theme.DANGER, size=12)

    # ------------------------------------------------------------------
    # Costruzione UI
    # ------------------------------------------------------------------
    def build(self) -> ft.Control:
        header = ft.Row(
            [
                ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: self.app.show_home()),
                ft.Text("Configura scheda", size=theme.TITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
            ]
        )

        add_day_btn = ft.OutlinedButton(
            "Aggiungi giorno",
            icon=ft.Icons.ADD,
            on_click=self._add_giorno,
        )

        save_btn = ft.ElevatedButton(
            "Salva scheda",
            icon=ft.Icons.SAVE,
            bgcolor=theme.PRIMARY,
            color=ft.Colors.WHITE,
            height=50,
            on_click=self._salva,
        )

        self._refresh_giorni_column()

        return ft.Column(
            [
                header,
                ft.Divider(color=theme.BORDER, height=16),
                ft.Container(content=self.giorni_column, expand=True),
                add_day_btn,
                self.info_text,
                save_btn,
            ],
            expand=True,
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

    # ------------------------------------------------------------------
    # Rendering dinamico dei giorni/esercizi
    # ------------------------------------------------------------------
    def _refresh_giorni_column(self):
        self.giorni_column.controls.clear()
        for g_idx, giorno in enumerate(self.giorni):
            self.giorni_column.controls.append(self._build_giorno_card(g_idx, giorno))
        if self.page:
            self.page.update()

    def _build_giorno_card(self, g_idx: int, giorno: dict) -> ft.Control:
        nome_field = ft.TextField(
            value=giorno.get("nome", f"Giorno {g_idx + 1}"),
            label="Nome giorno",
            dense=True,
            expand=True,
            on_change=lambda e, i=g_idx: self._set_giorno_nome(i, e.control.value),
        )

        note_field = ft.TextField(
            value=giorno.get("note", ""),
            label="Nota (facoltativa, es. \"scarico -20%\")",
            dense=True,
            text_size=12,
            on_change=lambda e, i=g_idx: self._set_giorno_nota(i, e.control.value),
        )

        esercizi_rows = ft.Column(spacing=8)
        n_esercizi = len(giorno.get("esercizi", []))
        for e_idx, esercizio in enumerate(giorno.get("esercizi", [])):
            esercizi_rows.controls.append(self._build_esercizio_row(g_idx, e_idx, esercizio, n_esercizi))

        add_ex_btn = ft.TextButton(
            "Aggiungi esercizio",
            icon=ft.Icons.ADD_CIRCLE_OUTLINE,
            on_click=lambda e, i=g_idx: self._add_esercizio(i),
        )

        n_giorni = len(self.giorni)
        sposta_su_btn = ft.IconButton(
            icon=ft.Icons.ARROW_UPWARD,
            icon_size=18,
            icon_color=theme.TEXT_MUTED if g_idx > 0 else theme.BORDER,
            tooltip="Sposta su",
            disabled=(g_idx == 0),
            on_click=lambda e, i=g_idx: self._sposta_giorno(i, -1),
        )
        sposta_giu_btn = ft.IconButton(
            icon=ft.Icons.ARROW_DOWNWARD,
            icon_size=18,
            icon_color=theme.TEXT_MUTED if g_idx < n_giorni - 1 else theme.BORDER,
            tooltip="Sposta giù",
            disabled=(g_idx == n_giorni - 1),
            on_click=lambda e, i=g_idx: self._sposta_giorno(i, 1),
        )
        duplica_btn = ft.IconButton(
            icon=ft.Icons.CONTENT_COPY,
            icon_size=18,
            icon_color=theme.INFO if hasattr(theme, "INFO") else theme.PRIMARY,
            tooltip="Duplica giorno",
            on_click=lambda e, i=g_idx: self._duplica_giorno(i),
        )
        delete_day_btn = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_size=18,
            icon_color=theme.DANGER,
            tooltip="Elimina giorno",
            on_click=lambda e, i=g_idx: self._remove_giorno(i),
        )

        toolbar = ft.Row(
            [sposta_su_btn, sposta_giu_btn, duplica_btn, ft.Container(expand=True), delete_day_btn],
            spacing=0,
        )

        return theme.card_container(
            ft.Column(
                [
                    toolbar,
                    nome_field,
                    note_field,
                    ft.Divider(color=theme.BORDER, height=6),
                    esercizi_rows,
                    add_ex_btn,
                ],
                spacing=10,
            ),
            bgcolor=theme.BG_CARD,
        )

    def _build_esercizio_row(self, g_idx: int, e_idx: int, esercizio: dict, n_esercizi: int) -> ft.Control:
        nome = ft.TextField(
            value=esercizio.get("nome", ""),
            label="Esercizio",
            dense=True,
            expand=2,
            on_change=lambda e, gi=g_idx, ei=e_idx: self._set_esercizio_campo(gi, ei, "nome", e.control.value),
        )
        serie = ft.TextField(
            value=str(esercizio.get("serie", 3)),
            label="Serie",
            dense=True,
            expand=1,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e, gi=g_idx, ei=e_idx: self._set_esercizio_campo(
                gi, ei, "serie", self._to_int(e.control.value, 3)
            ),
        )
        ripetizioni = ft.TextField(
            value=str(esercizio.get("ripetizioni", "8-12")),
            label="Reps",
            dense=True,
            expand=1,
            on_change=lambda e, gi=g_idx, ei=e_idx: self._set_esercizio_campo(gi, ei, "ripetizioni", e.control.value),
        )
        peso = ft.TextField(
            value=str(esercizio.get("peso_riferimento", 0)),
            label="Kg",
            dense=True,
            expand=1,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e, gi=g_idx, ei=e_idx: self._set_esercizio_campo(
                gi, ei, "peso_riferimento", self._to_float(e.control.value, 0)
            ),
        )
        recupero = ft.TextField(
            value=str(esercizio.get("rest_seconds", 90)),
            label="Recupero (s)",
            dense=True,
            expand=1,
            tooltip="Tempo di recupero specifico per questo esercizio, usato dal Rest Timer",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e, gi=g_idx, ei=e_idx: self._set_esercizio_campo(
                gi, ei, "rest_seconds", self._to_int(e.control.value, 90)
            ),
        )

        su_btn = ft.IconButton(
            icon=ft.Icons.ARROW_UPWARD,
            icon_size=14,
            icon_color=theme.TEXT_MUTED if e_idx > 0 else theme.BORDER,
            tooltip="Sposta su",
            disabled=(e_idx == 0),
            on_click=lambda e, gi=g_idx, ei=e_idx: self._sposta_esercizio(gi, ei, -1),
        )
        giu_btn = ft.IconButton(
            icon=ft.Icons.ARROW_DOWNWARD,
            icon_size=14,
            icon_color=theme.TEXT_MUTED if e_idx < n_esercizi - 1 else theme.BORDER,
            tooltip="Sposta giù",
            disabled=(e_idx == n_esercizi - 1),
            on_click=lambda e, gi=g_idx, ei=e_idx: self._sposta_esercizio(gi, ei, 1),
        )
        delete_btn = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_color=theme.TEXT_MUTED,
            icon_size=16,
            tooltip="Rimuovi esercizio",
            on_click=lambda e, gi=g_idx, ei=e_idx: self._remove_esercizio(gi, ei),
        )

        return ft.Column(
            [
                ft.Row([nome, serie, ripetizioni], spacing=6),
                ft.Row([peso, recupero, su_btn, giu_btn, delete_btn], spacing=2),
            ],
            spacing=4,
        )

    # ------------------------------------------------------------------
    # Utility di conversione sicura
    # ------------------------------------------------------------------
    @staticmethod
    def _to_int(value, default):
        try:
            return max(1, int(float(value)))
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _to_float(value, default):
        try:
            return round(float(value), 2)
        except (ValueError, TypeError):
            return default

    # ------------------------------------------------------------------
    # Handler di modifica dati (in memoria, sulla copia locale)
    # ------------------------------------------------------------------
    def _set_giorno_nome(self, g_idx, value):
        self.giorni[g_idx]["nome"] = value

    def _set_giorno_nota(self, g_idx, value):
        self.giorni[g_idx]["note"] = value

    def _set_esercizio_campo(self, g_idx, e_idx, campo, value):
        self.giorni[g_idx]["esercizi"][e_idx][campo] = value

    def _add_giorno(self, e):
        if len(self.giorni) >= MAX_GIORNI:
            self.info_text.value = f"Puoi configurare al massimo {MAX_GIORNI} giorni."
            self.page.update()
            return
        self.info_text.value = ""
        self.giorni.append(dm.new_giorno(f"Giorno {len(self.giorni) + 1}"))
        self._refresh_giorni_column()

    def _duplica_giorno(self, g_idx):
        if len(self.giorni) >= MAX_GIORNI:
            self.info_text.value = f"Puoi configurare al massimo {MAX_GIORNI} giorni."
            self.page.update()
            return
        copia = copy.deepcopy(self.giorni[g_idx])
        copia["nome"] = f'{copia.get("nome", "Giorno")} (copia)'
        self.giorni.insert(g_idx + 1, copia)
        self._refresh_giorni_column()

    def _sposta_giorno(self, g_idx, delta):
        nuovo_idx = g_idx + delta
        if 0 <= nuovo_idx < len(self.giorni):
            self.giorni[g_idx], self.giorni[nuovo_idx] = self.giorni[nuovo_idx], self.giorni[g_idx]
            self._refresh_giorni_column()

    def _remove_giorno(self, g_idx):
        if len(self.giorni) <= 0:
            return
        del self.giorni[g_idx]
        self._refresh_giorni_column()

    def _add_esercizio(self, g_idx):
        self.giorni[g_idx]["esercizi"].append(dm.new_esercizio())
        self._refresh_giorni_column()

    def _sposta_esercizio(self, g_idx, e_idx, delta):
        esercizi = self.giorni[g_idx]["esercizi"]
        nuovo_idx = e_idx + delta
        if 0 <= nuovo_idx < len(esercizi):
            esercizi[e_idx], esercizi[nuovo_idx] = esercizi[nuovo_idx], esercizi[e_idx]
            self._refresh_giorni_column()

    def _remove_esercizio(self, g_idx, e_idx):
        del self.giorni[g_idx]["esercizi"][e_idx]
        self._refresh_giorni_column()

    # ------------------------------------------------------------------
    # Salvataggio
    # ------------------------------------------------------------------
    def _salva(self, e):
        if len(self.giorni) < MIN_GIORNI:
            self.info_text.value = "Devi configurare almeno 1 giorno."
            self.page.update()
            return
        # Validazione minima: nomi esercizi non vuoti
        for giorno in self.giorni:
            giorno["esercizi"] = [ex for ex in giorno["esercizi"] if ex.get("nome", "").strip()]

        self.app.data["scheda"]["giorni"] = self.giorni
        # Traccia la data di ultimo aggiornamento scheda, usata dall'avviso
        # "scheda da rivedere" in Home.
        self.app.data["scheda"]["aggiornata_il"] = dm.today_str()
        self.app.save()
        self.app.show_home()


def build_schema_view(app) -> ft.Control:
    """Funzione helper per compatibilità con il router principale."""
    editor = SchemaEditorView(app)
    return editor.build()
