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

# Gradiente della card "hero" della Home (personalizzato per tema)
HERO_GRADIENT = ["#1E222D", "#26212A"]

# --- Palette tema CHIARO (per chi preferisce la luce) ---
# Applicata tramite applica_tema(): le costanti di sfondo/testo sovrascritte.
_PALETTE_CHIARO = {
    "BG": "#F4F6FB",
    "BG_CARD": "#FFFFFF",
    "BG_CARD_LIGHT": "#ECEFF6",
    "BORDER": "#E1E5EF",
    "TEXT": "#151A26",
    "TEXT_MUTED": "#5D6575",
    "HERO_GRADIENT": ["#FFFFFF", "#FFE3C7"],
}


def applica_tema(tema: str = "scuro") -> None:
    """Applica la palette scura (default) o chiara alle costanti globali.
    I colori di accento (PRIMARY, SUCCESS, DANGER, INFO, GOLD) restano
    invariati perché funzionano su entrambi i fondi."""
    global BG, BG_CARD, BG_CARD_LIGHT, TEXT, TEXT_MUTED, BORDER, CARD_BG, HERO_GRADIENT
    if tema == "chiaro":
        pal = _PALETTE_CHIARO
        BG = pal["BG"]
        BG_CARD = pal["BG_CARD"]
        BG_CARD_LIGHT = pal["BG_CARD_LIGHT"]
        TEXT = pal["TEXT"]
        TEXT_MUTED = pal["TEXT_MUTED"]
        BORDER = pal["BORDER"]
        HERO_GRADIENT = pal["HERO_GRADIENT"]
    else:
        BG = "#0B0F19"
        BG_CARD = "#1E222D"
        BG_CARD_LIGHT = "#2A3040"
        TEXT = "#FFFFFF"
        TEXT_MUTED = "#8E8E93"
        BORDER = "#2C313D"
        HERO_GRADIENT = ["#1E222D", "#26212A"]
    CARD_BG = BG_CARD

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

# Ombra più leggera per elementi piccoli (pillole, chip, icone)
CARD_SHADOW_SOFT = ft.BoxShadow(
    spread_radius=0,
    blur_radius=10,
    color="#00000033",
    offset=ft.Offset(0, 3),
)

# Bagliore neon per le azioni principali / stato attivo
GLOW_SHADOW = ft.BoxShadow(
    spread_radius=2,
    blur_radius=26,
    color="#FF6B0055",
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


def back_button(on_click=None) -> ft.Container:
    """Pulsante indietro coerente in tutte le schermate (tondo, con ombra)."""
    return ft.Container(
        content=ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            icon_color=TEXT,
            icon_size=22,
            on_click=on_click,
            tooltip="Indietro",
        ),
        bgcolor=BG_CARD_LIGHT,
        border_radius=22,
        shadow=CARD_SHADOW_SOFT,
        ink=True,
    )


def card_container(content: ft.Control, **kwargs) -> ft.Container:
    """Container standard "a card" con sfondo, angoli arrotondati, bordo
    sottile, shadow morbida e padding."""
    return ft.Container(
        content=content,
        bgcolor=kwargs.pop("bgcolor", BG_CARD),
        border_radius=kwargs.pop("border_radius", RADIUS),
        padding=kwargs.pop("padding", PADDING),
        shadow=kwargs.pop("shadow", CARD_SHADOW),
        border=kwargs.pop("border", ft.border.all(1, BORDER)),
        **kwargs,
    )


def primary_button(text: str, on_click=None, expand=False, icon=None) -> ft.Container:
    """Pulsante primario "glow" con gradiente neon: usato per le azioni
    principali (avvio workout, salvataggi). Ritorna un Container cliccabile."""
    content_row = ft.Row(
        [
            ft.Icon(icon, size=18, color="#FFFFFF") if icon else ft.Container(),
            ft.Text(text, weight=ft.FontWeight.BOLD, color="#FFFFFF", size=14),
        ],
        spacing=8,
        alignment=ft.MainAxisAlignment.CENTER,
    )
    return ft.Container(
        content=content_row,
        alignment=ft.alignment.center,
        padding=ft.padding.symmetric(horizontal=20, vertical=14),
        gradient=ft.LinearGradient(
            begin=ft.alignment.center_left,
            end=ft.alignment.center_right,
            colors=[GRADIENT_START, GRADIENT_END],
        ),
        border_radius=28,
        shadow=GLOW_SHADOW,
        expand=expand,
        ink=True,
        animate_scale=ft.Animation(140, ft.AnimationCurve.EASE_OUT),
        on_click=on_click,
    )
