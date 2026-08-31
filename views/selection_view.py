"""
selection_view.py
------------------
Schermata B - Selezione Allenamento.
Mostra i giorni configurati nella scheda (da 1 a 7) e permette
all'utente di scegliere quale sessione svolgere oggi.
"""

import flet as ft
import theme


def build_selection_view(app) -> ft.Control:
    giorni = app.data["scheda"]["giorni"]

    header = ft.Row(
        [
            ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: app.show_home()),
            ft.Text("Scegli il giorno", size=theme.TITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
        ],
    )

    if not giorni:
        body = ft.Column(
            [
                ft.Icon(ft.Icons.LIST_ALT, size=48, color=theme.TEXT_MUTED),
                ft.Text(
                    "Non hai ancora configurato una scheda.",
                    color=theme.TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.ElevatedButton(
                    "Configura scheda",
                    icon=ft.Icons.SETTINGS,
                    bgcolor=theme.PRIMARY,
                    color=ft.Colors.WHITE,
                    on_click=lambda e: app.show_schema_editor(),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=14,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )
        return ft.Column([header, body], expand=True, spacing=10)

    cards = []
    for idx, giorno in enumerate(giorni):
        n_esercizi = len(giorno.get("esercizi", []))
        cards.append(
            ft.GestureDetector(
                on_tap=lambda e, i=idx: app.show_training(i),
                content=theme.card_container(
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(
                                        giorno.get("nome", f"Giorno {idx + 1}"),
                                        size=theme.SUBTITLE_SIZE,
                                        weight=ft.FontWeight.BOLD,
                                        color=theme.TEXT,
                                    ),
                                    ft.Text(f"{n_esercizi} esercizi", size=12, color=theme.TEXT_MUTED),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, color=theme.PRIMARY),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    margin=ft.margin.only(bottom=10),
                ),
            )
        )

    return ft.Column(
        [
            header,
            ft.Divider(color=theme.BORDER, height=20),
            ft.ListView(controls=cards, expand=True, spacing=0),
        ],
        expand=True,
        spacing=10,
    )
