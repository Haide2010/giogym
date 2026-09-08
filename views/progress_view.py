"""
progress_view.py
-----------------
Schermata Grafici dei Progressi: mostra tutti gli esercizi (della scheda
e già allenati) in un elenco ordinato e ricercabile. Ogni card, una volta
aperta, mostra l'andamento nel tempo del peso massimo per sessione e del
volume totale (peso x reps), per monitorare il sovraccarico progressivo.
"""

import flet as ft
import theme


def _tutti_esercizi(app) -> list:
    """Ritorna l'elenco ordinato (alfabetico) di TUTTI gli esercizi:
    quelli presenti nella scheda e quelli svolti in passato nello storico."""
    nomi = set()
    for giorno in app.data.get("scheda", {}).get("giorni", []):
        for esercizio in giorno.get("esercizi", []):
            nome = esercizio.get("nome", "").strip()
            if nome:
                nomi.add(nome)
    for sessione in app.data.get("storico", []):
        for esercizio in sessione.get("esercizi", []):
            nome = esercizio.get("nome", "").strip()
            if nome:
                nomi.add(nome)
    return sorted(nomi)


def _serie_temporale_esercizio(storico: list, nome_esercizio: str):
    """Ritorna tre liste parallele (date, pesi_max, volumi): una entry per
    ogni sessione (in ordine cronologico di storico) in cui l'esercizio è
    stato svolto con almeno una serie completata."""
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
                below_line_gradient=ft.LinearGradient(
                    begin=ft.alignment.top_center,
                    end=ft.alignment.bottom_center,
                    colors=[
                        ft.Colors.with_opacity(0.30, colore),
                        ft.Colors.with_opacity(0.0, colore),
                    ],
                ),
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


def _build_esercizio_card(storico: list, nome_esercizio: str) -> ft.Control:
    """Card espandibile con il riepilogo e i grafici di un singolo esercizio."""
    etichette, pesi_max, volumi = _serie_temporale_esercizio(storico, nome_esercizio)

    if not etichette:
        body = ft.Column(
            [
                ft.Text("Nessun allenamento registrato per questo esercizio. "
                        "Completa la prima sessione e comparirà qui il grafico.",
                        color=theme.TEXT_MUTED, size=12),
            ],
            spacing=8,
        )
    else:
        ultimo_peso = pesi_max[-1]
        primo_peso = pesi_max[0]
        delta_peso = round(ultimo_peso - primo_peso, 1)
        delta_str = f"+{delta_peso} kg" if delta_peso >= 0 else f"{delta_peso} kg"
        delta_color = theme.SUCCESS if delta_peso >= 0 else theme.DANGER

        body = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(f"{len(etichette)} sessioni", size=12, color=theme.TEXT_MUTED),
                        ft.Text("Ultimo peso: ", size=12, color=theme.TEXT_MUTED),
                        ft.Text(f"{ultimo_peso} kg", size=13, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.TRENDING_UP if delta_peso >= 0 else ft.Icons.TRENDING_DOWN,
                                        size=16, color=delta_color),
                                ft.Text(delta_str, size=13, weight=ft.FontWeight.BOLD, color=delta_color),
                            ],
                            spacing=4,
                        ),
                    ],
                    spacing=8,
                    wrap=True,
                ),
                theme.card_container(
                    ft.Column(
                        [
                            ft.Text("Peso massimo per sessione", size=theme.SUBTITLE_SIZE,
                                    weight=ft.FontWeight.BOLD, color=theme.TEXT),
                            _build_line_chart(pesi_max, theme.PRIMARY, "kg"),
                        ],
                        spacing=8,
                    )
                ),
                theme.card_container(
                    ft.Column(
                        [
                            ft.Text("Volume totale per sessione (peso × reps)", size=theme.SUBTITLE_SIZE,
                                    weight=ft.FontWeight.BOLD, color=theme.TEXT),
                            _build_line_chart(volumi, theme.INFO, "kg tot."),
                        ],
                        spacing=8,
                    )
                ),
            ],
            spacing=12,
        )

    return ft.Container(
        content=ft.ExpansionTile(
            leading=ft.Container(
                content=ft.Icon(ft.Icons.FITNESS_CENTER, size=18, color=theme.PRIMARY),
                alignment=ft.alignment.center,
                width=40, height=40,
                bgcolor=theme.BG_CARD_LIGHT,
                border_radius=20,
            ),
            title=ft.Text(nome_esercizio, size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
            subtitle=ft.Text(
                f"{len(etichette)} sessioni" if etichette else "Mai allenato",
                size=12,
                color=theme.TEXT_MUTED,
            ),
            controls=[body],
            controls_padding=ft.padding.only(top=10),
            maintain_state=True,
            collapsed_bgcolor=ft.Colors.with_opacity(0.0, theme.BG_CARD),
            bgcolor=ft.Colors.with_opacity(0.0, theme.BG_CARD),
            shape=ft.RoundedRectangleBorder(radius=theme.RADIUS),
            collapsed_shape=ft.RoundedRectangleBorder(radius=theme.RADIUS),
            tile_padding=ft.padding.symmetric(horizontal=10, vertical=6),
        ),
        padding=4,
    )


def build_progress_view(app) -> ft.Control:
    """Costruisce la schermata dei grafici dei progressi."""
    storico = app.data.get("storico", [])
    esercizi_disponibili = _tutti_esercizi(app)

    lista_column = ft.Column(spacing=10)

    ricerca_field = ft.TextField(
        label="Cerca esercizio",
        prefix_icon=ft.Icons.SEARCH,
        dense=True,
        border_color=theme.BORDER,
        focused_border_color=theme.PRIMARY,
        text_size=13,
        on_change=lambda e: _filtra(e.control.value or ""),
    )

    def _filtra(testo: str):
        testo_pulito = testo.strip().lower()
        lista_column.controls.clear()
        for nome in esercizi_disponibili:
            if testo_pulito and testo_pulito not in nome.lower():
                continue
            lista_column.controls.append(_build_esercizio_card(storico, nome))
        app.page.update()

    header = ft.Row(
        [
            theme.back_button(lambda e: app.show_home()),
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
                                "Nessun esercizio ancora disponibile.\nAggiungi una scheda o "
                                "completa un allenamento per\nvedere qui i tuoi grafici.",
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

    # Pre-carica l'elenco completo
    _filtra("")

    content_list = ft.ListView(
        [
            header,
            ft.Divider(color=theme.BORDER, height=15),
            ricerca_field,
            ft.Text(
                f"{len(esercizi_disponibili)} esercizi",
                size=12,
                color=theme.TEXT_MUTED,
            ),
            lista_column,
        ],
        expand=True,
        spacing=14,
    )

    return ft.Column([content_list], expand=True)