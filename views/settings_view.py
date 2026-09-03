"""
settings_view.py
----------------
Schermata Impostazioni per personalizzare colori, tema e stile dell'app.
"""

import json
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
        # Aggiorna il colore primario nel modulo theme o nelle impostazioni salvate
        theme.PRIMARY = hex_code
        app.data["primary_color"] = hex_code
        app.salva_dati()
        
        # Mostra un messaggio di conferma e ricarica l'app
        app.page.snack_bar = ft.SnackBar(ft.Text(f"Colore tema aggiornato con successo!"), bgcolor=hex_code)
        app.page.snack_bar.open = True
        app.show_home()

    def esporta_scheda_json(e):
        """Copia la scheda negli appunti in formato JSON, epurata dallo storico."""
        # Estrae solo la parte della scheda dall'oggetto dati dell'app
        scheda_dati = app.data.get("scheda", {})
        
        # Serializza in formato JSON formattato
        json_str = json.dumps(scheda_dati, ensure_ascii=False, indent=2)
        
        # Copia negli appunti tramite la proprietà set_clipboard della pagina
        app.page.set_clipboard(json_str)
        
        # Mostra conferma visiva
        app.page.snack_bar = ft.SnackBar(
            ft.Text("Scheda copiata negli appunti in formato JSON! (Senza storico)"), 
            bgcolor=theme.SUCCESS
        )
        app.page.snack_bar.open = True
        app.page.update()

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

    # Sezione Condivisione/Export Scheda
    export_section = ft.Container(
        content=ft.Column(
            [
                ft.Text("Esportazione Scheda", size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                ft.Text("Copia la tua scheda di allenamento attuale negli appunti (escludendo lo storico) per condividerla facilmente.", size=12, color=theme.TEXT_MUTED),
                ft.ElevatedButton(
                    text="Copia Scheda JSON",
                    icon=ft.Icons.CONTENT_COPY,
                    color=ft.Colors.WHITE,
                    bgcolor=theme.PRIMARY,
                    on_click=esporta_scheda_json,
                ),
            ],
            spacing=8,
        ),
        padding=14,
        bgcolor=theme.CARD_BG if hasattr(theme, "CARD_BG") else "#1a1a1a",
        border_radius=12,
        border=ft.border.all(1, theme.BORDER),
    )

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
            export_section,
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