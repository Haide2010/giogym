"""
home_view.py
------------
Schermata A - Home / Dashboard.
Mostra la lista cronologica (storico) degli allenamenti completati e il
grande pulsante centrale per iniziare un nuovo allenamento.
"""

import flet as ft
import theme


def _history_card(sessione: dict) -> ft.Control:
    """Costruisce la card riassuntiva di un allenamento passato."""
    n_esercizi = len(sessione.get("esercizi", []))
    n_serie = sum(len(e.get("serie_svolte", [])) for e in sessione.get("esercizi", []))

    return theme.card_container(
        ft.Row(
            [
                ft.Column(
                    [
                        ft.Text(
                            f'{sessione.get("data", "-")}',
                            size=theme.SUBTITLE_SIZE,
                            weight=ft.FontWeight.BOLD,
                            color=theme.TEXT,
                        ),
                        ft.Text(
                            f'Completato: {sessione.get("giorno_nome", "-")}',
                            size=theme.BODY_SIZE,
                            color=theme.TEXT_MUTED,
                        ),
                        ft.Text(
                            f"{n_esercizi} esercizi · {n_serie} serie",
                            size=12,
                            color=theme.TEXT_MUTED,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=theme.SUCCESS, size=28),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        margin=ft.margin.only(bottom=10),
    )


def build_home_view(app) -> ft.Control:
    """Costruisce il contenuto della schermata Home."""

    storico = list(reversed(app.data.get("storico", [])))  # più recenti in alto

    if storico:
        history_list = ft.ListView(
            controls=[_history_card(s) for s in storico],
            spacing=0,
            expand=True,
        )
    else:
        history_list = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.FITNESS_CENTER, size=48, color=theme.TEXT_MUTED),
                    ft.Text(
                        "Nessun allenamento registrato.\nInizia il tuo primo workout!",
                        color=theme.TEXT_MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.alignment.center,
            expand=True,
            padding=30,
        )

    header = ft.Row(
        [
            ft.Column(
                [
                    ft.Text("GioGym", size=theme.TITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ft.Text("Il tuo allenamento, sempre con te", size=12, color=theme.TEXT_MUTED),
                ],
                spacing=0,
            ),
            ft.IconButton(
                icon=ft.Icons.SETTINGS,
                icon_color=theme.TEXT_MUTED,
                tooltip="Configura scheda",
                on_click=lambda e: app.show_schema_editor(),
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    start_button = ft.Container(
        content=ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, size=32, color=ft.Colors.WHITE),
                    ft.Text("INIZIA ALLENAMENTO", size=18, weight=ft.FontWeight.BOLD),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
            ),
            bgcolor=theme.PRIMARY,
            color=ft.Colors.WHITE,
            height=64,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=18)),
            on_click=lambda e: app.show_selection(),
        ),
        padding=ft.padding.symmetric(vertical=10),
    )

    return ft.Column(
        [
            header,
            ft.Divider(color=theme.BORDER, height=20),
            ft.Text("Storico allenamenti", size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
            ft.Container(content=history_list, expand=True),
            start_button,
        ],
        expand=True,
        spacing=10,
    )
