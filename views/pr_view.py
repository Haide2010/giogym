"""
pr_view.py
-----------
Schermata Record Personali (PR): mostra per ogni esercizio allenato
almeno una volta il massimale di peso, ripetizioni, volume e la stima
del massimale (1RM), calcolati da pr_manager.
"""

import flet as ft
import theme
import pr_manager


def _pr_card(app, nome_esercizio: str, record: dict) -> ft.Control:
    def _riga(icona, etichetta, valore, data, colore):
        if not data:
            return ft.Container()
        return ft.Row(
            [
                ft.Row(
                    [
                        ft.Icon(icona, size=16, color=colore),
                        ft.Text(etichetta, size=12, color=theme.TEXT_MUTED),
                    ],
                    spacing=6,
                ),
                ft.Row(
                    [
                        ft.Text(valore, size=14, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                        ft.Text(f"({data})", size=10, color=theme.TEXT_MUTED),
                    ],
                    spacing=6,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    righe = [
        _riga(ft.Icons.FITNESS_CENTER, "Peso massimo", f"{record['max_peso']} kg", record["max_peso_data"], theme.GOLD),
        _riga(ft.Icons.REPEAT, "Ripetizioni massime", f"{record['max_reps']} reps", record["max_reps_data"], theme.PRIMARY),
        _riga(ft.Icons.TRENDING_UP, "Massimale stimato (1RM)", f"{record['stima_1rm']} kg", record["stima_1rm_data"], theme.SUCCESS),
        _riga(ft.Icons.STACKED_BAR_CHART, "Volume in una sessione", f"{record['max_volume']} kg", record["max_volume_data"], theme.INFO),
    ]

    cronologia_btn = ft.TextButton(
        content=ft.Row(
            [ft.Icon(ft.Icons.HISTORY, size=15, color=theme.INFO), ft.Text("Vedi cronologia completa", size=12, color=theme.INFO)],
            spacing=6,
        ),
        on_click=lambda e, nome=nome_esercizio: app.show_exercise_history(nome, "pr"),
    )

    return theme.card_container(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.EMOJI_EVENTS, color=theme.GOLD, size=22),
                        ft.Text(nome_esercizio, size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ],
                    spacing=8,
                ),
                ft.Divider(color=theme.BORDER, height=10),
                ft.Column(righe, spacing=8),
                cronologia_btn,
            ],
            spacing=6,
        ),
        margin=ft.margin.only(bottom=10),
    )


def build_pr_view(app) -> ft.Control:
    """Costruisce la schermata dei Record Personali."""
    header = ft.Row(
        [
            ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=theme.TEXT, on_click=lambda e: app.show_home()),
            ft.Row(
                [
                    ft.Icon(ft.Icons.EMOJI_EVENTS, color=theme.GOLD, size=24),
                    ft.Text("Record Personali", size=theme.TITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                ],
                spacing=8,
            ),
        ],
    )

    prs = pr_manager.compute_all_prs(app.data.get("storico", []))

    if not prs:
        body = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.EMOJI_EVENTS_OUTLINED, size=40, color=theme.TEXT_MUTED),
                    ft.Text(
                        "Nessun record ancora disponibile.\nCompleta un allenamento per iniziare a\ntracciare i tuoi PR.",
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
        )
        content_list = ft.ListView([header, ft.Divider(color=theme.BORDER, height=15), body], expand=True, spacing=10)
    else:
        cards = [_pr_card(app, nome, record) for nome, record in sorted(prs.items())]
        content_list = ft.ListView(
            [
                header,
                ft.Divider(color=theme.BORDER, height=15),
                ft.Text(
                    f"{len(prs)} esercizi tracciati · continua così! 💪",
                    size=12,
                    color=theme.TEXT_MUTED,
                ),
                *cards,
            ],
            expand=True,
            spacing=10,
        )

    return ft.Column([content_list], expand=True)
