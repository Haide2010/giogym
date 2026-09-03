"""
theme.py
--------
Costanti di stile centralizzate per GioGym: colori, dimensioni, font.
Nuovo stile visivo: "Dark Obsidian & Neon Orange Pro".
- Sfondo nero / blu notte profondissimo (ideale per display OLED).
- Accento Neon Orange / Sunset Amber vibrante con gradienti leggeri.
- Card con angoli molto arrotondati (border_radius 18-24) e shadow morbide
  per un effetto di profondità stile Neumorphism scuro / Glassmorphism.
Tenere tutti i colori qui rende semplice cambiare la palette in futuro.
Le costanti storiche (BG, BG_CARD, PRIMARY, card_container, ecc.) restano
invariate nei nomi e nelle firme, in modo che tutte le viste le ereditino.
"""

import flet as ft

# --- Palette colori: Dark Obsidian & Neon Orange Pro ---
BG = "#0B0F19"                  # sfondo principale (nero/blu notte, OLED)
BG_CARD = "#1E222D"             # sfondo delle card/superfici (più chiaro del fondo)
BG_CARD_LIGHT = "#2A3040"       # sfondo di elementi secondari (es. serie)
PRIMARY = "#FF6B00"             # Neon Orange / Sunset Amber (accento principale)
PRIMARY_DARK = "#FF8500"        # variazione più chiara del neon per gradienti
SUCCESS = "#3DDC97"             # serie completata / allenamento salvato (verde neon)
WARNING = "#FFB300"             # timer in scadenza (ambra)
DANGER = "#FF5C5C"              # eliminazione / errori (rosso)
TEXT = "#FFFFFF"                # testo principale
TEXT_MUTED = "#8E8E93"          # etichette descrittive (grigio chiaro)
BORDER = "#2C313D"              # bordo sottile e discreto
CARD_BG = BG_CARD               # alias usato in alcune viste (storico/calendario)
GOLD = "#FFC107"                # colore badge Record Personale (PR)
INFO = "#4DC3FF"                # colore info/accento secondario (ciano chiaro)
GRADIENT_START = "#FF6B00"      # per i gradienti arancioni
GRADIENT_END = "#FFB300"        # per i gradienti arancioni

# --- Dimensioni / raggi / ombre ---
RADIUS = 18
RADIUS_SMALL = 12
PADDING = 16
SPACING = 12

# Ombra morbida standard per le card (effetto profondità)
CARD_SHADOW = ft.BoxShadow(
    spread_radius=1,
    blur_radius=18,
    color="#00000055",
    offset=ft.Offset(0, 6),
)

# --- Font ---
TITLE_SIZE = 26
SUBTITLE_SIZE = 17
BODY_SIZE = 14
BIG_NUMBER_SIZE = 30   # numeri chiave (peso, calorie, serie, timer)


def page_theme() -> ft.Theme:
    """Ritorna il tema Material scuro personalizzato per la Page di Flet."""
    return ft.Theme(
        color_scheme_seed=PRIMARY,
        font_family="Roboto",
        page_transitions=ft.PageTransitionsTheme(
            android=ft.PageTransitionTheme.FADE_UPWARDS,
            ios=ft.PageTransitionTheme.CUPERTINO,
            windows=ft.PageTransitionTheme.FADE_UPWARDS,
            linux=ft.PageTransitionTheme.FADE_UPWARDS,
            macos=ft.PageTransitionTheme.FADE_UPWARDS,
        ),
    )


def section_title(text: str) -> ft.Text:
    """Titolo di sezione standard, riusato in tutte le schermate."""
    return ft.Text(text, size=TITLE_SIZE, weight=ft.FontWeight.BOLD, color=TEXT)


def card_container(content: ft.Control, **kwargs) -> ft.Container:
    """Container standard "a card" con sfondo, angoli arrotondati, shadow morbida e padding."""
    return ft.Container(
        content=content,
        bgcolor=kwargs.pop("bgcolor", BG_CARD),
        border_radius=kwargs.pop("border_radius", RADIUS),
        padding=kwargs.pop("padding", PADDING),
        shadow=kwargs.pop("shadow", CARD_SHADOW),
        **kwargs,
    )


def primary_button(text: str, on_click=None, expand=False) -> ft.ElevatedButton:
    """Pulsante primario con gradiente neon per le azioni principali."""
    return ft.ElevatedButton(
        content=ft.Text(text, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
        on_click=on_click,
        expand=expand,
        style=ft.ButtonStyle(
            bgcolor={
                ft.ControlState.DEFAULT: PRIMARY,
            },
            padding=ft.padding.symmetric(horizontal=18, vertical=14),
            shape=ft.RoundedRectangleBorder(radius=RADIUS_SMALL),
        ),
    )
