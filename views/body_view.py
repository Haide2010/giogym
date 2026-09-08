"""
body_view.py
------------
Vista "Peso & Misure": registra peso corporeo e misure (vita, petto,
braccio, gamba) con grafico dell'andamento e storico eliminabile.
"""

import flet as ft
import theme
import data_manager as dm


class BodyView:
    def __init__(self, app):
        self.app = app
        self.page = app.page
        self.log = app.data.setdefault("peso_corporeo", [])
        self.peso_field = None
        self.vita_field = None
        self.petto_field = None
        self.braccio_field = None
        self.gamba_field = None
        self.data_field = None
        self.status_text = ft.Text("", size=12, color=theme.TEXT_MUTED)
        self.storico_col = ft.Column(spacing=4)
        self.grafico_col = ft.Column(spacing=4)

    # ------------------------------------------------------------------
    def build(self) -> ft.Control:
        header = ft.Row(
            [
                theme.back_button(lambda e: self.app.show_home()),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.MONITOR_WEIGHT, color=theme.SUCCESS, size=24),
                        ft.Text("Peso & Misure", size=theme.TITLE_SIZE,
                                weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ],
                    spacing=8,
                ),
            ],
        )

        self.peso_field = ft.TextField(
            label="Peso (kg)", dense=True,
            keyboard_type=ft.KeyboardType.NUMBER,
            expand=True,
            helper_text="Peso corporeo di oggi")
        self.vita_field = ft.TextField(label="Vita (cm)", dense=True,
                                       keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        self.petto_field = ft.TextField(label="Petto (cm)", dense=True,
                                        keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        self.braccio_field = ft.TextField(label="Braccio (cm)", dense=True,
                                          keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        self.gamba_field = ft.TextField(label="Gamba (cm)", dense=True,
                                        keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        self.data_field = ft.TextField(
            label="Data (gg/mm/aaaa)", dense=True, value=dm.today_str())

        form_card = theme.card_container(
            ft.Column(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.ADD_TASK, color=theme.PRIMARY, size=20),
                        ft.Text("Nuova registrazione", size=theme.SUBTITLE_SIZE,
                                weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ], spacing=8),
                    ft.Row([self.peso_field, self.data_field], spacing=8),
                    ft.Text("Misure (opzionali, cm)", size=12, color=theme.TEXT_MUTED),
                    ft.Row([self.vita_field, self.petto_field,
                            self.braccio_field, self.gamba_field], spacing=8),
                    theme.primary_button("Salva registrazione", self._salva,
                                         expand=True, icon=ft.Icons.CHECK_CIRCLE),
                    self.status_text,
                ],
                spacing=8,
            ),
        )

        grafico_card = theme.card_container(
            ft.Column(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.SHOW_CHART, color=theme.PRIMARY, size=20),
                        ft.Text("Andamento peso", size=theme.SUBTITLE_SIZE,
                                weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ], spacing=8),
                    self.grafico_col,
                ],
                spacing=8,
            ),
        )

        storico_card = theme.card_container(
            ft.Column(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.LIST_ALT, color=theme.INFO, size=20),
                        ft.Text("Storico Peso & Misure", size=theme.SUBTITLE_SIZE,
                                weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ], spacing=8),
                    self.storico_col,
                ],
                spacing=8,
            ),
        )

        self._refresh_grafico()
        self._refresh_storico()

        return ft.Column(
            [
                header,
                ft.Divider(color=theme.BORDER, height=15),
                form_card,
                ft.Divider(color=theme.BORDER, height=12),
                grafico_card,
                ft.Divider(color=theme.BORDER, height=12),
                storico_card,
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

    # ------------------------------------------------------------------
    def _salva(self, e):
        try:
            peso = float((self.peso_field.value or "").strip().replace(",", "."))
        except (TypeError, ValueError):
            self._status("Inserisci un peso valido.", theme.DANGER)
            return
        data = (self.data_field.value or "").strip() or dm.today_str()
        misure = {}
        for campo, chiave in (
            (self.vita_field, "vita"),
            (self.petto_field, "petto"),
            (self.braccio_field, "braccio"),
            (self.gamba_field, "gamba"),
        ):
            val = (campo.value or "").strip().replace(",", ".")
            if val:
                try:
                    misure[chiave] = round(float(val), 1)
                except ValueError:
                    self._status(f"Misura non valida: {chiave}", theme.DANGER)
                    return

        self.log.append({**{"data": data, "peso": peso}, **({"misure": misure} if misure else {})})
        # Aggiorna il peso attuale nel profilo con l'ultima registrazione
        self.app.data.setdefault("profilo", {})["peso_attuale_kg"] = peso
        self.app.save()
        self.peso_field.value = ""
        self.vita_field.value = ""
        self.petto_field.value = ""
        self.braccio_field.value = ""
        self.gamba_field.value = ""
        self.data_field.value = dm.today_str()
        self._status("Registrazione salvata!", theme.SUCCESS)
        self._refresh_grafico()
        self._refresh_storico()
        self.page.update()

    def _elimina(self, idx, e):
        if 0 <= idx < len(self.log):
            self.log.pop(idx)
            self.app.save()
            self._status("Registrazione eliminata.", theme.TEXT_MUTED)
            self._refresh_grafico()
            self._refresh_storico()
            self.page.update()

    def _status(self, msg, colore):
        self.status_text.value = msg
        self.status_text.color = colore

    # ------------------------------------------------------------------
    def _refresh_grafico(self):
        self.grafico_col.controls.clear()
        if not self.log:
            self.grafico_col.controls.append(
                ft.Text("Registra il peso per vedere l'andamento.", color=theme.TEXT_MUTED, size=12))
            return

        pesi = [e.get("peso", 0) for e in self.log]
        punti = [ft.LineChartDataPoint(i, p) for i, p in enumerate(pesi)]

        max_y = max(pesi)
        min_y = min(pesi)
        padding_y = max((max_y - min_y) * 0.15, 1)

        line = ft.LineChartData(
            data_points=punti,
            stroke_width=3,
            color=theme.PRIMARY,
            curved=True,
            stroke_cap_round=True,
            below_line_gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[
                    ft.Colors.with_opacity(0.30, theme.PRIMARY),
                    ft.Colors.with_opacity(0.0, theme.PRIMARY),
                ],
            ),
            point=True,
        )

        chart = ft.LineChart(
            data_series=[line],
            border=ft.border.all(1, theme.BORDER),
            horizontal_grid_lines=ft.ChartGridLines(
                interval=max(1, round(padding_y)), color=theme.BORDER, width=1),
            left_axis=ft.ChartAxis(labels_size=36, title=ft.Text("kg", size=10, color=theme.TEXT_MUTED)),
            bottom_axis=ft.ChartAxis(labels_size=24),
            min_y=max(0, min_y - padding_y),
            max_y=max_y + padding_y,
            expand=True,
        )
        self.grafico_col.controls.append(ft.Container(chart, height=210))

    # ------------------------------------------------------------------
    def _refresh_storico(self):
        self.storico_col.controls.clear()
        if not self.log:
            self.storico_col.controls.append(
                ft.Text("Nessuna registrazione.", color=theme.TEXT_MUTED, size=12))
            return
        for idx in range(len(self.log) - 1, -1, -1):
            entry = self.log[idx]
            misure = entry.get("misure", {}) or {}
            dettagli = []
            if misure.get("vita"):
                dettagli.append(f"Vita {misure['vita']}cm")
            if misure.get("petto"):
                dettagli.append(f"Petto {misure['petto']}cm")
            if misure.get("braccio"):
                dettagli.append(f"Braccio {misure['braccio']}cm")
            if misure.get("gamba"):
                dettagli.append(f"Gamba {misure['gamba']}cm")

            riga = ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(f"{entry.get('data', '-')}  ·  {entry.get('peso', 0)} kg",
                                    size=13, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                            ft.Text(", ".join(dettagli), size=11,
                                    color=theme.TEXT_MUTED, visible=bool(dettagli)),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=theme.DANGER,
                        icon_size=18,
                        tooltip="Elimina",
                        on_click=lambda e, i=idx: self._elimina(i, e),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
            self.storico_col.controls.append(
                ft.Container(
                    content=riga,
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    bgcolor=theme.BG_CARD_LIGHT,
                    border_radius=10,
                )
            )


def build_body_view(app) -> ft.Control:
    return BodyView(app).build()