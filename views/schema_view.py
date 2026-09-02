"""
schema_view.py
---------------
Editor della scheda di allenamento.
Permette di:
- aggiungere, rimuovere e riordinare i giorni
- inserire note giornaliere e duplicare un giorno
- aggiungere, rimuovere e riordinare gli esercizi
- impostare nome, serie, ripetizioni, peso di riferimento e link foto/tutorial
"""

import copy
from datetime import datetime
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
        self.giorni = copy.deepcopy(app.data["scheda"].get("giorni", []))
        self.giorni_column = ft.Column(spacing=14)
        self.info_text = ft.Text("", color=theme.DANGER, size=12)

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
            on_change=lambda e, i=g_idx: self._set_giorno_campo(i, "nome", e.control.value),
        )
        
        nota_field = ft.TextField(
            value=giorno.get("nota_giorno", ""),
            label="Note giorno (es. scarico, focus...)",
            dense=True,
            text_size=12,
            border_color=theme.BORDER,
            focused_border_color=theme.PRIMARY,
            on_change=lambda e, i=g_idx: self._set_giorno_campo(i, "nota_giorno", e.control.value),
        )

        controlli_giorno = ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.ARROW_UPWARD,
                    icon_size=18,
                    tooltip="Sposta su",
                    on_click=lambda e, i=g_idx: self._sposta_giorno(i, -1),
                    disabled=g_idx == 0,
                ),
                ft.IconButton(
                    icon=ft.Icons.ARROW_DOWNWARD,
                    icon_size=18,
                    tooltip="Sposta giù",
                    on_click=lambda e, i=g_idx: self._sposta_giorno(i, 1),
                    disabled=g_idx == len(self.giorni) - 1,
                ),
                ft.IconButton(
                    icon=ft.Icons.COPY,
                    icon_size=18,
                    tooltip="Duplica giorno",
                    on_click=lambda e, i=g_idx: self._duplica_giorno(i),
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=theme.DANGER,
                    tooltip="Elimina giorno",
                    on_click=lambda e, i=g_idx: self._remove_giorno(i),
                ),
            ],
            spacing=0,
        )

        esercizi_rows = ft.Column(spacing=8)
        tot_es = len(giorno.get("esercizi", []))
        for e_idx, esercizio in enumerate(giorno.get("esercizi", [])):
            esercizi_rows.controls.append(self._build_esercizio_row(g_idx, e_idx, esercizio, tot_es))

        add_ex_btn = ft.TextButton(
            "Aggiungi esercizio",
            icon=ft.Icons.ADD_CIRCLE_OUTLINE,
            on_click=lambda e, i=g_idx: self._add_esercizio(i),
        )

        return theme.card_container(
            ft.Column(
                [
                    ft.Row([nome_field, controlli_giorno], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    nota_field,
                    ft.Divider(color=theme.BORDER, height=4),
                    esercizi_rows,
                    add_ex_btn,
                ],
                spacing=10,
            ),
            bgcolor=theme.BG_CARD,
        )

    def _build_esercizio_row(self, g_idx: int, e_idx: int, esercizio: dict, tot_esercizi: int) -> ft.Control:
        nome = ft.TextField(
            value=esercizio.get("nome", ""),
            label="Esercizio",
            dense=True,
            expand=2,
            on_change=lambda e: self._set_esercizio_campo(g_idx, e_idx, "nome", e.control.value),
        )
        serie = ft.TextField(
            value=str(esercizio.get("serie", 3)),
            label="Serie",
            dense=True,
            width=60,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: self._set_esercizio_campo(g_idx, e_idx, "serie", self._to_int(e.control.value, 3)),
        )
        ripetizioni = ft.TextField(
            value=str(esercizio.get("ripetizioni", "8-12")),
            label="Reps",
            dense=True,
            width=75,
            on_change=lambda e: self._set_esercizio_campo(g_idx, e_idx, "ripetizioni", e.control.value),
        )
        peso = ft.TextField(
            value=str(esercizio.get("peso_riferimento", 0)),
            label="Kg",
            dense=True,
            width=65,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda e: self._set_esercizio_campo(g_idx, e_idx, "peso_riferimento", self._to_float(e.control.value, 0)),
        )
        foto = ft.TextField(
            value=esercizio.get("url_foto", ""),
            label="Link Foto/Video (opzionale)",
            dense=True,
            text_size=11,
            expand=1,
            on_change=lambda e: self._set_esercizio_campo(g_idx, e_idx, "url_foto", e.control.value),
        )

        controlli = ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.ARROW_UPWARD,
                    icon_color=theme.TEXT_MUTED,
                    icon_size=16,
                    tooltip="Sposta esercizio su",
                    on_click=lambda e: self._sposta_esercizio(g_idx, e_idx, -1),
                    disabled=e_idx == 0,
                ),
                ft.IconButton(
                    icon=ft.Icons.ARROW_DOWNWARD,
                    icon_color=theme.TEXT_MUTED,
                    icon_size=16,
                    tooltip="Sposta esercizio giù",
                    on_click=lambda e: self._sposta_esercizio(g_idx, e_idx, 1),
                    disabled=e_idx == tot_esercizi - 1,
                ),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_color=theme.DANGER,
                    icon_size=18,
                    tooltip="Rimuovi esercizio",
                    on_click=lambda e: self._remove_esercizio(g_idx, e_idx),
                ),
            ],
            spacing=0,
        )

        return ft.Column(
            [
                ft.Row([nome, serie, ripetizioni, peso], spacing=6),
                ft.Row([foto, controlli], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=6),
            ],
            spacing=4,
        )

    @staticmethod
    def _to_int(value, default):
        try:
            return max(1, int(float(value)))
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _to_float(value, default):
        try:
            return round(float(str(value).replace(",", ".")), 2)
        except (ValueError, TypeError):
            return default

    def _set_giorno_campo(self, g_idx, campo, value):
        self.giorni[g_idx][campo] = value

    def _set_esercizio_campo(self, g_idx, e_idx, campo, value):
        self.giorni[g_idx]["esercizi"][e_idx][campo] = value

    def _add_giorno(self, e):
        if len(self.giorni) >= MAX_GIORNI:
            self.info_text.value = f"Puoi configurare al massimo {MAX_GIORNI} giorni."
            self.page.update()
            return
        self.info_text.value = ""
        self.giorni.append({
            "nome": f"Giorno {len(self.giorni) + 1}",
            "nota_giorno": "",
            "esercizi": []
        })
        self._refresh_giorni_column()

    def _remove_giorno(self, g_idx):
        if len(self.giorni) <= 1:
            self.info_text.value = "Devi mantenere almeno un giorno nella scheda."
            self.page.update()
            return
        del self.giorni[g_idx]
        self.info_text.value = ""
        self._refresh_giorni_column()

    def _sposta_giorno(self, g_idx, direzione):
        if 0 <= g_idx + direzione < len(self.giorni):
            self.giorni.insert(g_idx + direzione, self.giorni.pop(g_idx))
            self._refresh_giorni_column()

    def _duplica_giorno(self, g_idx):
        if len(self.giorni) >= MAX_GIORNI:
            self.info_text.value = f"Puoi configurare al massimo {MAX_GIORNI} giorni."
            self.page.update()
            return
        giorno_clonato = copy.deepcopy(self.giorni[g_idx])
        giorno_clonato["nome"] += " (Copia)"
        self.giorni.insert(g_idx + 1, giorno_clonato)
        self.info_text.value = ""
        self._refresh_giorni_column()

    def _add_esercizio(self, g_idx):
        self.giorni[g_idx]["esercizi"].append({
            "nome": "",
            "serie": 3,
            "ripetizioni": "8-12",
            "peso_riferimento": 0,
            "url_foto": ""
        })
        self._refresh_giorni_column()

    def _remove_esercizio(self, g_idx, e_idx):
        del self.giorni[g_idx]["esercizi"][e_idx]
        self._refresh_giorni_column()

    def _sposta_esercizio(self, g_idx, e_idx, direzione):
        lista_ex = self.giorni[g_idx]["esercizi"]
        if 0 <= e_idx + direzione < len(lista_ex):
            lista_ex.insert(e_idx + direzione, lista_ex.pop(e_idx))
            self._refresh_giorni_column()

    def _salva(self, e):
        if len(self.giorni) < MIN_GIORNI:
            self.info_text.value = "Devi configurare almeno 1 giorno."
            self.page.update()
            return
        
        for giorno in self.giorni:
            giorno["esercizi"] = [ex for ex in giorno["esercizi"] if ex.get("nome", "").strip()]

        self.app.data["scheda"]["giorni"] = self.giorni
        self.app.data["scheda"]["data_modifica"] = datetime.now().strftime("%Y-%m-%d")
        self.app.save()
        self.app.show_home()


def build_schema_view(app) -> ft.Control:
    """Funzione helper per compatibilità con il router principale."""
    editor = SchemaEditorView(app)
    return editor.build()