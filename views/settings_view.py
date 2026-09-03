"""
settings_view.py
----------------
Schermata Impostazioni per personalizzare colori, tema e stile dell'app.
"""

import flet as ft
import theme


def build_settings_view(app) -> ft.Control:
    """Costruisce la vista delle impostazioni."""

    header = ft.Row(
        [
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_color=theme.TEXT,
                on_click=lambda e: app.show_home(),
            ),
            ft.Text("Impostazioni", size=theme.TITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
        ],
        alignment=ft.MainAxisAlignment.START,
    )

    # Definizione dei colori di tema disponibili
    colori_disponibili = [
        {"nome": "Verde Smeraldo (Default)", "hex": "#4CAF50"},
        {"nome": "Blu Elettrico", "hex": "#2196F3"},
        {"nome": "Viola", "hex": "#9C27B0"},
        {"nome": "Arancione", "hex": "#FF9800"},
        {"nome": "Rosso Carismatico", "hex": "#F44336"},
    ]

    def cambia_colore(hex_code):
        # Salva la scelta e applica il nuovo tema in modo coerente a
        # tutta l'app (sia le viste che il tema Material della pagina).
        app.data["primary_color"] = hex_code
        app.salva_dati()
        app.refresh_theme_and_reload()

    color_cards = []
    current_color = getattr(theme, "PRIMARY", "#4CAF50")

    for c in colori_disponibili:
        is_selected = (c["hex"].lower() == current_color.lower())
        
        btn = ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Container(
                                width=24,
                                height=24,
                                bgcolor=c["hex"],
                                border_radius=12,
                                border=ft.border.all(2, "white" if is_selected else "transparent"),
                            ),
                            ft.Text(c["nome"], size=14, weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL, color=theme.TEXT),
                        ],
                        spacing=12,
                    ),
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=theme.PRIMARY, size=20) if is_selected else ft.Container(),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=14,
            bgcolor=theme.CARD_BG if hasattr(theme, "CARD_BG") else "#1a1a1a",
            border_radius=12,
            border=ft.border.all(2, theme.PRIMARY if is_selected else theme.BORDER),
            ink=True,
            on_click=lambda e, hex_val=c["hex"]: cambia_colore(hex_val),
        )
        color_cards.append(btn)

    # Sezione Informazioni / Crediti app
    info_section = ft.Container(
        content=ft.Column(
            [
                ft.Text("Info su GioGym", size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                ft.Text("Versione 1.0.0\nGestisci i tuoi allenamenti in modo semplice e veloce.", size=12, color=theme.TEXT_MUTED),
            ],
            spacing=4,
        ),
        padding=14,
        bgcolor=theme.CARD_BG if hasattr(theme, "CARD_BG") else "#1a1a1a",
        border_radius=12,
        border=ft.border.all(1, theme.BORDER),
    )

    content_list = ft.ListView(
        [
            header,
            ft.Divider(color=theme.BORDER, height=15),
            ft.Text("Personalizzazione Colore Tema", size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
            ft.Text("Scegli il colore principale che preferisci per i tasti e gli elementi attivi dell'app:", size=12, color=theme.TEXT_MUTED),
            *color_cards,
            ft.Divider(color=theme.BORDER, height=15),
            info_section,
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