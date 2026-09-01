"""
schema_view.py
---------------
Editor della scheda di allenamento.
Non è una delle schermate esplicitamente elencate nelle specifiche, ma è
indispensabile: senza un modo per configurare giorni/esercizi l'app non
avrebbe dati su cui lavorare. Si raggiunge dall'icona ingranaggio in Home.

Permette di:
- aggiungere/rimuovere giorni (da 1 a 7)
- rinominare ogni giorno
- aggiungere/rimuovere esercizi per ogni giorno
- impostare nome, serie, ripetizioni target e peso di riferimento iniziale
"""

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
        import copy
        self.giorni = copy.deepcopy(app.data["scheda"]["giorni"])
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
            on_change=lambda e, i=g_idx: self._set_giorno_nome(i, e.control.value),
        )

        esercizi_rows = ft.Column(spacing=8)
        for e_idx, esercizio in enumerate(giorno.get("esercizi", [])):
            esercizi_rows.controls.append(self._build_esercizio_row(g_idx, e_idx, esercizio))

        add_ex_btn = ft.TextButton(
            "Aggiungi esercizio",
            icon=ft.Icons.ADD_CIRCLE_OUTLINE,
            on_click=lambda e, i=g_idx: self._add_esercizio(i),
        )

        delete_day_btn = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_color=theme.DANGER,
            tooltip="Elimina giorno",
            on_click=lambda e, i=g_idx: self._remove_giorno(i),
        )

        return theme.card_container(
            ft.Column(
                [
                    ft.Row([nome_field, delete_day_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    esercizi_rows,
                    add_ex_btn,
                ],
                spacing=10,
            ),
            bgcolor=theme.BG_CARD,
        )

    def _build_esercizio_row(self, g_idx: int, e_idx: int, esercizio: dict) -> ft.Control:
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
        delete_btn = ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_color=theme.TEXT_MUTED,
            icon_size=18,
            tooltip="Rimuovi esercizio",
            on_click=lambda e, gi=g_idx, ei=e_idx: self._remove_esercizio(gi, ei),
        )

        return ft.Row(
            [nome, serie, ripetizioni, peso, delete_btn],
            spacing=6,
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

    def _remove_giorno(self, g_idx):
        if len(self.giorni) <= 0:
            return
        del self.giorni[g_idx]
        self._refresh_giorni_column()

    def _add_esercizio(self, g_idx):
        self.giorni[g_idx]["esercizi"].append(dm.new_esercizio())
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
        self.app.save()
        self.app.show_home()
        
def build_schema_view(app) -> ft.Control:
    """Funzione helper per compatibilità con il router principale."""
    editor = SchemaEditorView(app)
    return editor.build()
