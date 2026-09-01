"""
selection_view.py
-----------------
Schermata di selezione del giorno di allenamento da avviare.
"""

import flet as ft
import theme


def build_selection_view(app) -> ft.Control:
    """Costruisce la vista per selezionare quale giorno della scheda allenare."""

    giorni_scheda = app.data.get("scheda", {}).get("giorni", [])

    header = ft.Row(
        [
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_color=theme.TEXT,
                on_click=lambda e: app.show_home(),
            ),
            ft.Text("Seleziona Giorno", size=theme.TITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
        ],
        alignment=ft.MainAxisAlignment.START,
    )

    cards = []
    if giorni_scheda:
        for giorno in giorni_scheda:
            nome_giorno = giorno.get("nome", "Giorno")
            num_es = len(giorno.get("esercizi", []))
            
            card = ft.Container(
                content=ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Icon(ft.Icons.FITNESS_CENTER, size=22, color=theme.PRIMARY),
                                    padding=10,
                                    bgcolor=theme.BG_CARD_LIGHT if hasattr(theme, "BG_CARD_LIGHT") else "#2a2a2a",
                                    border_radius=10,
                                ),
                                ft.Column(
                                    [
                                        ft.Text(nome_giorno, size=16, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                                        ft.Text(f"{num_es} esercizi programmati", size=12, color=theme.TEXT_MUTED),
                                    ],
                                    spacing=2,
                                ),
                            ],
                            spacing=12,
                        ),
                        ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, color=theme.PRIMARY, size=26),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=16,
                bgcolor=theme.CARD_BG if hasattr(theme, "CARD_BG") else "#1a1a1a",
                border_radius=14,
                border=ft.border.all(1, theme.BORDER),
                ink=True,
                # CORRETTO: Passiamo direttamente l'intero oggetto 'giorno' invece dell'indice numerico
                on_click=lambda e, g=giorno: app.show_training(g),
                tooltip=f"Avvia {nome_giorno}",
            )
            cards.append(card)
    else:
        cards.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=36, color=theme.TEXT_MUTED),
                        ft.Text(
                            "Nessun giorno trovato nella scheda.\nVai alla home e crea o modifica la scheda.",
                            color=theme.TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER,
                            size=13,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                alignment=ft.alignment.center,
                padding=24,
            )
        )

    content_list = ft.ListView(
        [
            header,
            ft.Divider(color=theme.BORDER, height=15),
            ft.Text("Scegli quale sessione vuoi affrontare oggi:", size=13, color=theme.TEXT_MUTED),
            *cards,
        ],
        expand=True,
        spacing=10,
    )

    return ft.Column(
        [
            content_list,
        ],
        expand=True,
    )
