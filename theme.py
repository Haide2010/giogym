"""
theme.py
--------
Costanti di stile centralizzate per GioGym: colori, dimensioni, font.
Tema scuro in stile "palestra": nero/grigio scuro + accento arancio/rosso.
Tenere tutti i colori qui rende semplice cambiare la palette in futuro.
"""

import flet as ft

# --- Palette colori ---
BG = ft.Colors.GREY_900              # sfondo principale (quasi nero)
BG_CARD = ft.Colors.GREY_800          # sfondo delle card/superfici
BG_CARD_LIGHT = ft.Colors.GREY_700    # sfondo elementi secondari (es. serie)
PRIMARY = ft.Colors.DEEP_ORANGE_600   # colore primario (bottoni, accenti)
PRIMARY_DARK = ft.Colors.DEEP_ORANGE_800
SUCCESS = ft.Colors.GREEN_500         # serie completata / allenamento salvato
WARNING = ft.Colors.AMBER_600         # timer in scadenza
DANGER = ft.Colors.RED_400            # eliminazione / errori
TEXT = ft.Colors.WHITE
TEXT_MUTED = ft.Colors.GREY_400
BORDER = ft.Colors.GREY_700
CARD_BG = BG_CARD                     # alias usato in alcune viste (storico/calendario)
GOLD = ft.Colors.AMBER_400            # colore badge Record Personale (PR)
INFO = ft.Colors.LIGHT_BLUE_400       # colore info/accento secondario

# --- Dimensioni / raggi ---
RADIUS = 14
PADDING = 16
SPACING = 12

# --- Font ---
TITLE_SIZE = 26
SUBTITLE_SIZE = 16
BODY_SIZE = 14


def page_theme(seed_color: str = None) -> ft.Theme:
    """Ritorna il tema Material scuro personalizzato per la Page di Flet.
    Se seed_color è indicato, usa quello al posto di PRIMARY (utile per
    rigenerare il tema quando l'utente cambia colore nelle Impostazioni)."""
    return ft.Theme(
        color_scheme_seed=seed_color or PRIMARY,
        font_family="Roboto",
    )


def section_title(text: str) -> ft.Text:
    """Titolo di sezione standard, riusato in tutte le schermate."""
    return ft.Text(text, size=TITLE_SIZE, weight=ft.FontWeight.BOLD, color=TEXT)


def card_container(content: ft.Control, **kwargs) -> ft.Container:
    """Container standard "a card" con sfondo, bordo arrotondato e padding."""
    return ft.Container(
        content=content,
        bgcolor=kwargs.pop("bgcolor", BG_CARD),
        border_radius=RADIUS,
        padding=kwargs.pop("padding", PADDING),
        **kwargs,
    )
