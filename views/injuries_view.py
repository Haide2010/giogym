"""
injuries_view.py
----------------
Registro "Infortuni o Fastidi" collegato al muscolo/giorno di allenamento.
Permette di:
- registrare un fastidio (muscolo, descrizione, giorno ed eventuale esercizio)
- vedere gli infortuni attivi/risolti
- risolvere o eliminare una voce

Il promemoria relativo viene mostrato nell'allenamento attivo del giorno
corrispondente (vedi training_view).
"""

import flet as ft
import theme
import data_manager as dm


def _giorni_scheda(app) -> list:
    return [g.get("nome", "") for g in app.data.get("scheda", {}).get("giorni", [])]


class InjuriesView:
    def __init__(self, app):
        self.app = app
        self.page = app.page

    def build(self) -> ft.Control:
        header = ft.Row(
            [
                ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=theme.TEXT,
                              on_click=lambda e: self.app.show_home()),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.HEALING, color=theme.WARNING, size=24),
                        ft.Text("Infortuni & Fastidi", size=theme.TITLE_SIZE,
                                weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ],
                    spacing=8,
                ),
            ],
        )

        # --- Form per aggiungere un nuovo infortunio ---
        muscolo_field = ft.TextField(
            label="Zona / muscolo (es. spalla destra)",
            dense=True,
            border_color=theme.BORDER,
            focused_border_color=theme.PRIMARY,
        )
        descrizione_field = ft.TextField(
            label="Descrizione (es. leggero fastidio sulla panca)",
            dense=True,
            multiline=True,
            min_lines=2,
            max_lines=4,
            border_color=theme.BORDER,
            focused_border_color=theme.PRIMARY,
        )

        giorni_options = _giorni_scheda(self.app)
        giorno_dropdown = ft.Dropdown(
            label="Giorno di allenamento legato (opzionale)",
            options=[ft.dropdown.Option(g) for g in giorni_options],
            border_color=theme.BORDER,
            focused_border_color=theme.PRIMARY,
        )

        esercizio_field = ft.TextField(
            label="Esercizio specifico (opzionale, es. Panca piana)",
            dense=True,
            border_color=theme.BORDER,
            focused_border_color=theme.PRIMARY,
        )

        status_text = ft.Text("", size=12)

        def _salva(e):
            muscolo = muscolo_field.value.strip()
            if not muscolo:
                status_text.value = "Inserisci almeno la zona/muscolo."
                status_text.color = theme.DANGER
                self.page.update()
                return

            infortuni = self.app.data.setdefault("infortuni", [])
            infortuni.append({
                "data": dm.today_str(),
                "muscolo": muscolo,
                "descrizione": descrizione_field.value.strip(),
                "giorno": giorno_dropdown.value,
                "giorni": [giorno_dropdown.value] if giorno_dropdown.value else [],
                "esercizio": esercizio_field.value.strip(),
                "stato": "attivo",
            })
            self.app.save()

            muscolo_field.value = ""
            descrizione_field.value = ""
            esercizio_field.value = ""
            giorno_dropdown.value = None
            status_text.value = "Fastidio registrato. Riceverai un promemoria quando alleni quel giorno."
            status_text.color = theme.SUCCESS
            self._refresh_list(self.lista_infortuni)
            self.page.update()

        salva_btn = ft.ElevatedButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.ADD, color="white"), ft.Text("Registra fastidio", weight=ft.FontWeight.BOLD)],
                spacing=8,
            ),
            bgcolor=theme.PRIMARY,
            color="white",
            on_click=_salva,
        )

        form_card = theme.card_container(
            ft.Column(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.HEALING, color=theme.WARNING, size=20),
                        ft.Text("Registra un nuovo fastidio", size=theme.SUBTITLE_SIZE,
                                weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ], spacing=8),
                    muscolo_field,
                    descrizione_field,
                    giorno_dropdown,
                    esercizio_field,
                    salva_btn,
                    status_text,
                ],
                spacing=8,
            ),
        )

        # --- Lista infortuni ---
        self.lista_infortuni = ft.Column(spacing=8)
        self._refresh_list(self.lista_infortuni)

        content_list = ft.ListView(
            [
                header,
                ft.Divider(color=theme.BORDER, height=15),
                form_card,
                ft.Divider(color=theme.BORDER, height=15),
                ft.Text("Registro", size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                self.lista_infortuni,
            ],
            expand=True,
            spacing=10,
        )

        return ft.Column([content_list], expand=True)

    def _refresh_list(self, container: ft.Column):
        container.controls.clear()
        infortuni = self.app.data.get("infortuni", [])
        if not infortuni:
            container.controls.append(
                ft.Text("Nessun fastidio registrato.", color=theme.TEXT_MUTED, size=12)
            )
            return

        for i in range(len(infortuni) - 1, -1, -1):
            container.controls.append(self._build_cards(jidx=i, inj=infortuni[i]))

    def _build_cards(self, jidx: int, inj: dict) -> ft.Control:
        stato = inj.get("stato", "attivo")
        attivo = stato != "risolto"

        badge_color = theme.WARNING if attivo else (theme.SUCCESS if hasattr(theme, "SUCCESS") else "#4CAF50")
        badge_text = "Attivo" if attivo else "Risolto"

        detallex = [
            ft.Text(inj.get("muscolo", "Zona"), size=theme.SUBTITLE_SIZE,
                    weight=ft.FontWeight.BOLD, color=theme.TEXT),
        ]
        if inj.get("descrizione"):
            detallex.append(ft.Text(inj.get("descrizione"), size=12, color=theme.TEXT_MUTED))
        meta = f'Registrato il: {inj.get("data", "-")}'
        if inj.get("giorno"):
            meta += f" · Giorno: {inj['giorno']}"
        if inj.get("esercizio"):
            meta += f" · Esercizio: {inj['esercizio']}"
        detallex.append(ft.Text(meta, size=11, color=theme.TEXT_MUTED))

        def _aggiorna_stato(new_stato, e):
            infortuni = self.app.data.get("infortuni", [])
            if 0 <= jidx < len(infortuni):
                infortuni[jidx]["stato"] = new_stato
                self.app.save()
                self._refresh_list(self.lista_infortuni)
                self.page.update()

        def _rimuovi(e):
            infortuni = self.app.data.get("infortuni", [])
            if 0 <= jidx < len(infortuni):
                del infortuni[jidx]
                self.app.save()
                self._refresh_list(self.lista_infortuni)
                self.page.update()

        azioni = ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.DONE,
                    icon_color=theme.SUCCESS if hasattr(theme, "SUCCESS") else "#4CAF50",
                    tooltip="Segna come risolto",
                    on_click=lambda e, i=jidx: _aggiorna_stato("risolto", e),
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=theme.DANGER if hasattr(theme, "DANGER") else "#EF5350",
                    tooltip="Elimina",
                    on_click=_rimuovi,
                ),
            ],
            spacing=0,
        )

        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(detallex, spacing=2, expand=True),
                    azioni,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=12,
            bgcolor=theme.CARD_BG if hasattr(theme, "CARD_BG") else "#1a1a1a",
            border_radius=12,
            border=ft.border.all(2, badge_color if attivo else theme.BORDER),
        )


def build_injuries_view(app) -> ft.Control:
    """Funzione helper per compatibilità con il router principale."""
    return InjuriesView(app).build()
