"""
progress_view.py
------------------
Schermata Grafici dei Progressi: per l'esercizio scelto dall'utente,
mostra l'andamento nel tempo del peso massimo per sessione e del volume
totale di allenamento (peso x reps), per monitorare il sovraccarico
progressivo.
"""

import flet as ft
import theme


def _estrai_esercizi_disponibili(storico: list) -> list:
    """Ritorna la lista ordinata (alfabetica) dei nomi esercizio che
    compaiono almeno una volta nello storico con serie completate."""
    nomi = set()
    for sessione in storico:
        for esercizio in sessione.get("esercizi", []):
            if any(s.get("completata") for s in esercizio.get("serie_svolte", [])):
                nome = esercizio.get("nome", "").strip()
                if nome:
                    nomi.add(nome)
    return sorted(nomi)


def _serie_temporale_esercizio(storico: list, nome_esercizio: str):
    """Ritorna due liste parallele (etichette_data, punti) dove ogni
    punto è (peso_massimo_sessione, volume_sessione), una entry per
    ogni sessione (in ordine cronologico di storico) in cui l'esercizio
    è stato svolto con almeno una serie completata."""
    etichette = []
    pesi_max = []
    volumi = []

    for sessione in storico:
        for esercizio in sessione.get("esercizi", []):
            if esercizio.get("nome", "").strip() != nome_esercizio:
                continue
            serie_completate = [s for s in esercizio.get("serie_svolte", []) if s.get("completata")]
            if not serie_completate:
                continue
            peso_max = max(float(s.get("peso", 0) or 0) for s in serie_completate)
            volume = sum(float(s.get("peso", 0) or 0) * int(s.get("reps", 0) or 0) for s in serie_completate)
            etichette.append(sessione.get("data", "-"))
            pesi_max.append(peso_max)
            volumi.append(round(volume, 1))

    return etichette, pesi_max, volumi


def _build_line_chart(valori: list, colore: str, unita: str) -> ft.Control:
    if len(valori) < 1:
        return ft.Text("Dati insufficienti per il grafico.", color=theme.TEXT_MUTED, size=12)

    punti = [ft.LineChartDataPoint(i, v) for i, v in enumerate(valori)]

    max_y = max(valori) if valori else 1
    min_y = min(valori) if valori else 0
    padding_y = max((max_y - min_y) * 0.15, 1)

    chart = ft.LineChart(
        data_series=[
            ft.LineChartData(
                data_points=punti,
                stroke_width=3,
                color=colore,
                curved=True,
                stroke_cap_round=True,
                below_line_bgcolor=ft.Colors.with_opacity(0.15, colore),
                point=True,
            )
        ],
        border=ft.border.all(1, theme.BORDER),
        horizontal_grid_lines=ft.ChartGridLines(interval=max(1, round(padding_y)), color=theme.BORDER, width=1),
        left_axis=ft.ChartAxis(labels_size=40, title=ft.Text(unita, size=10, color=theme.TEXT_MUTED)),
        bottom_axis=ft.ChartAxis(labels_size=24, title=ft.Text("Sessioni", size=10, color=theme.TEXT_MUTED)),
        min_y=max(0, min_y - padding_y),
        max_y=max_y + padding_y,
        min_x=0,
        max_x=max(1, len(valori) - 1),
        tooltip_bgcolor=theme.BG_CARD_LIGHT,
        expand=True,
    )
    return ft.Container(content=chart, height=220)


def build_progress_view(app) -> ft.Control:
    """Costruisce la schermata dei grafici dei progressi."""
    storico = app.data.get("storico", [])
    esercizi_disponibili = _estrai_esercizi_disponibili(storico)

    body_container = ft.Column(spacing=14)

    def _aggiorna_grafico(nome_esercizio: str):
        body_container.controls.clear()
        if not nome_esercizio:
            body_container.controls.append(
                ft.Text("Seleziona un esercizio per vedere i progressi.", color=theme.TEXT_MUTED)
            )
            app.page.update()
            return

        etichette, pesi_max, volumi = _serie_temporale_esercizio(storico, nome_esercizio)

        if not etichette:
            body_container.controls.append(
                ft.Text("Nessun dato registrato per questo esercizio.", color=theme.TEXT_MUTED)
            )
            app.page.update()
            return

        ultimo_peso = pesi_max[-1]
        primo_peso = pesi_max[0]
        delta_peso = round(ultimo_peso - primo_peso, 1)
        delta_str = f"+{delta_peso} kg" if delta_peso >= 0 else f"{delta_peso} kg"
        delta_color = theme.SUCCESS if delta_peso >= 0 else theme.DANGER

        summary = ft.Row(
            [
                ft.Text(f"{len(etichette)} sessioni registrate", size=12, color=theme.TEXT_MUTED),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.TRENDING_UP if delta_peso >= 0 else ft.Icons.TRENDING_DOWN,
                                 size=16, color=delta_color),
                        ft.Text(delta_str, size=13, weight=ft.FontWeight.BOLD, color=delta_color),
                    ],
                    spacing=4,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        body_container.controls.extend(
            [
                summary,
                theme.card_container(
                    ft.Column(
                        [
                            ft.Text("Peso massimo per sessione", size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                            _build_line_chart(pesi_max, theme.PRIMARY, "kg"),
                        ],
                        spacing=8,
                    )
                ),
                theme.card_container(
                    ft.Column(
                        [
                            ft.Text("Volume totale per sessione (peso × reps)", size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                            _build_line_chart(volumi, theme.INFO, "kg tot."),
                        ],
                        spacing=8,
                    )
                ),
                ft.TextButton(
                    content=ft.Row(
                        [ft.Icon(ft.Icons.HISTORY, size=15, color=theme.INFO), ft.Text("Vedi cronologia completa", size=12, color=theme.INFO)],
                        spacing=6,
                    ),
                    on_click=lambda e, nome=nome_esercizio: app.show_exercise_history(nome, "progress"),
                ),
            ]
        )
        app.page.update()

    dropdown = ft.Dropdown(
        label="Scegli esercizio",
        options=[ft.dropdown.Option(nome) for nome in esercizi_disponibili],
        value=esercizi_disponibili[0] if esercizi_disponibili else None,
        on_change=lambda e: _aggiorna_grafico(e.control.value),
        border_color=theme.BORDER,
        focused_border_color=theme.PRIMARY,
    )

    header = ft.Row(
        [
            ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=theme.TEXT, on_click=lambda e: app.show_home()),
            ft.Row(
                [
                    ft.Icon(ft.Icons.SHOW_CHART, color=theme.INFO, size=24),
                    ft.Text("Grafici dei Progressi", size=theme.TITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                ],
                spacing=8,
            ),
        ],
    )

    if not esercizi_disponibili:
        content_list = ft.ListView(
            [
                header,
                ft.Divider(color=theme.BORDER, height=15),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.Icons.SHOW_CHART, size=40, color=theme.TEXT_MUTED),
                            ft.Text(
                                "Nessun dato ancora disponibile.\nCompleta almeno un allenamento per\nvedere qui i tuoi grafici.",
                                color=theme.TEXT_MUTED,
                                text_align=ft.TextAlign.CENTER,
                                size=13,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    alignment=ft.alignment.center,
                    padding=30,
                ),
            ],
            expand=True,
            spacing=10,
        )
        return ft.Column([content_list], expand=True)

    # Pre-carica il grafico per il primo esercizio della lista
    _aggiorna_grafico(dropdown.value)

    content_list = ft.ListView(
        [
            header,
            ft.Divider(color=theme.BORDER, height=15),
            dropdown,
            body_container,
        ],
        expand=True,
        spacing=14,
    )

    return ft.Column([content_list], expand=True)
