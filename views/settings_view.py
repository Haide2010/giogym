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
            theme.back_button(lambda e: app.show_home()),
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

    def esporta_scheda_html(e):
        """Copia la scheda formattata in HTML (per PDF o condivisione).
        Dall'app hai già esportabile a file; qui generiamo testo ordinato."""
        scheda = app.data.get("scheda", {})
        giorni = scheda.get("giorni", [])

        def esc(s):
            return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        sezioni = []
        for giorno in giorni:
            esercizi = giorno.get("esercizi", [])
            righe = "".join(
                f"<tr><td>{esc(ex.get('nome'))}</td>"
                f"<td>{esc(str(ex.get('serie', '')))}</td>"
                f"<td>{esc(ex.get('ripetizioni', ''))}</td>"
                f"<td>{esc(str(ex.get('peso_riferimento', '')))}</td></tr>"
                for ex in esercizi
            )
            sezioni.append(
                f"<h3>{esc(giorno.get('nome', 'Giorno'))}</h3>"
                + (f"<p><em>{esc(giorno.get('nota_giorno'))}</em></p>" if giorno.get("nota_giorno") else "")
                + "<table border='1' cellpadding='6' style='border-collapse:collapse;width:100%'>"
                "<tr><th>Esercizio</th><th>Serie</th><th>Ripetizioni</th><th>Peso (kg)</th></tr>"
                + righe + "</table>"
            )
        if not sezioni:
            sezioni = ["<p>Nessun giorno programmato.</p>"]
        html = (
            f"<html><head><meta charset='utf-8'><title>GioGym - Scheda</title></head>"
            f"<body style='font-family:Segoe UI,Arial,sans-serif;color:#222;max-width:700px;margin:auto'>"
            f"<h1 style='color:#FF6B00'>GioGym</h1>"
            f"<h2 style='color:#444'>Scheda di allenamento</h2>" + "".join(sezioni) + "</body></html>"
        )
        app.page.set_clipboard(html)
        app.page.snack_bar = ft.SnackBar(
            ft.Text("Scheda HTML copiata! Incollala in un documento o mail per condividerla / stamparla in PDF."),
            bgcolor=theme.SUCCESS)
        app.page.snack_bar.open = True
        app.page.update()

    def cambia_tema(attivo):
        # attivo = True -> chiaro
        nuovo = "chiaro" if attivo else "scuro"
        app.data["tema"] = nuovo
        app.salva_dati()
        theme.applica_tema(nuovo)
        app.page.theme_mode = ft.ThemeMode.LIGHT if attivo else ft.ThemeMode.DARK
        app.page.bgcolor = theme.BG
        app.page.update()
        app.show_home()

    tema_chiaro = (app.data.get("tema") or "scuro").lower() == "chiaro"

    appearance_section = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [ft.Icon(ft.Icons.DARK_MODE_OUTLINED, color=theme.PRIMARY, size=20),
                     ft.Text("Aspetto", size=theme.SUBTITLE_SIZE,
                             weight=ft.FontWeight.BOLD, color=theme.TEXT)],
                    spacing=8,
                ),
                ft.Text("Scegli il tema dell'app:", size=12, color=theme.TEXT_MUTED),
                ft.Row(
                    [
                        ft.Text("Tema chiaro", size=14, color=theme.TEXT),
                        ft.Switch(
                            value=tema_chiaro,
                            active_color=theme.PRIMARY,
                            on_change=lambda e: cambia_tema(e.control.value),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=8,
        ),
        padding=14,
        bgcolor=theme.CARD_BG if hasattr(theme, "CARD_BG") else "#1a1a1a",
        border_radius=12,
        border=ft.border.all(1, theme.BORDER),
    )

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

    # Sezione Profilo: modifica nome, peso, obiettivi e frequenza
    profile_section = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [ft.Icon(ft.Icons.PERSON, color=theme.PRIMARY, size=20),
                     ft.Text("Profilo & Obiettivi", size=theme.SUBTITLE_SIZE,
                             weight=ft.FontWeight.BOLD, color=theme.TEXT)],
                    spacing=8,
                ),
                ft.Text("Modifica il nome, l'età, il peso attuale e obiettivo, la frequenza settimanale e gli obiettivi personali.",
                        size=12, color=theme.TEXT_MUTED),
                ft.ElevatedButton(
                    text="Apri il Profilo",
                    icon=ft.Icons.EDIT,
                    color=ft.Colors.WHITE,
                    bgcolor=theme.PRIMARY,
                    on_click=lambda e: app.show_profile(),
                ),
            ],
            spacing=8,
        ),
        padding=14,
        bgcolor=theme.CARD_BG if hasattr(theme, "CARD_BG") else "#1a1a1a",
        border_radius=12,
        border=ft.border.all(1, theme.BORDER),
    )

    # Sezione Condivisione/Export Scheda
    export_section = ft.Container(
        content=ft.Column(
            [
                ft.Text("Esportazione Scheda", size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                ft.Text("Copia la tua scheda di allenamento attuale negli appunti, in JSON (veloce) o in HTML (per PDF/stampa/condivisione col coach).", size=12, color=theme.TEXT_MUTED),
                ft.ElevatedButton(
                    text="Copia Scheda JSON",
                    icon=ft.Icons.CONTENT_COPY,
                    color=ft.Colors.WHITE,
                    bgcolor=theme.PRIMARY,
                    on_click=esporta_scheda_json,
                ),
                ft.ElevatedButton(
                    text="Copia Scheda HTML (PDF / Condividi)",
                    icon=ft.Icons.PICTURE_AS_PDF,
                    color=ft.Colors.WHITE,
                    bgcolor=theme.PRIMARY,
                    on_click=esporta_scheda_html,
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
            appearance_section,
            ft.Divider(color=theme.BORDER, height=15),
            profile_section,
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