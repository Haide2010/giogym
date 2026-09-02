"""
home_view.py
------------
Schermata A - Home / Dashboard.
Mostra storico e calendario nella parte superiore, e un comodo box "Accesso rapido" 
insieme al tasto "INIZIA ALLENAMENTO" in basso.
"""

import calendar
from datetime import datetime, date
import flet as ft
import theme


def _build_year_calendar(app) -> ft.Control:
    """Genera la vista a calendario annuale 2026 con mesi cliccabili."""
    
    allenati_map = {}
    for s in app.data.get("storico", []):
        d_str = s.get("data")
        if d_str:
            try:
                dt = datetime.strptime(d_str, "%d/%m/%Y").date()
                allenati_map[dt] = s
            except ValueError:
                pass

    mesi_nomi = [
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
    ]
    giorni_settimana = ["L", "M", "M", "G", "V", "S", "D"]

    def apri_mese_ingrandito(m_idx: int):
        cal = calendar.monthcalendar(2026, m_idx)
        
        m_title = ft.Text(mesi_nomi[m_idx-1], size=18, weight=ft.FontWeight.BOLD, color=theme.TEXT)
        
        days_header = ft.Row(
            [ft.Text(g, size=12, color=theme.TEXT_MUTED, text_align=ft.TextAlign.CENTER, width=32) for g in giorni_settimana],
            spacing=4,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        weeks_col = [days_header]
        for week in cal:
            week_row = []
            for day in week:
                if day == 0:
                    week_row.append(ft.Container(width=32, height=32))
                else:
                    d_obj = date(2026, m_idx, day)
                    is_trained = d_obj in allenati_map
                    
                    bg_color = theme.PRIMARY if is_trained else (theme.BG_CARD_LIGHT if hasattr(theme, "BG_CARD_LIGHT") else "#2a2a2a")
                    text_color = "white" if is_trained else theme.TEXT_MUTED
                    
                    day_container = ft.Container(
                        content=ft.Text(str(day), size=13, weight=ft.FontWeight.BOLD if is_trained else ft.FontWeight.NORMAL, color=text_color, text_align=ft.TextAlign.CENTER),
                        alignment=ft.alignment.center,
                        width=32,
                        height=32,
                        bgcolor=bg_color,
                        border_radius=6,
                    )
                    
                    if is_trained:
                        sessione_rif = allenati_map[d_obj]
                        day_container.ink = True
                        day_container.on_click = lambda e, sess=sessione_rif: _vai_a_storico(sess)
                    
                    week_row.append(day_container)
            
            weeks_col.append(ft.Row(week_row, spacing=4, alignment=ft.MainAxisAlignment.CENTER))

        dialog_content = ft.Column(
            [
                m_title,
                ft.Divider(color=theme.BORDER, height=10),
                ft.Column(weeks_col, spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Text("Tocca un giorno evidenziato per aprire lo storico.", size=11, color=theme.TEXT_MUTED, italic=True, text_align=ft.TextAlign.CENTER)
            ],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True,
        )

        dlg = ft.AlertDialog(
            modal=True,
            bgcolor=theme.CARD_BG if hasattr(theme, "CARD_BG") else "#1a1a1a",
            content=dialog_content,
            actions=[
                ft.TextButton("Chiudi", on_click=lambda e: app.page.close(dlg)),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )
        app.page.open(dlg)

    def _vai_a_storico(sessione):
        app.page.close_dialogs() if hasattr(app.page, "close_dialogs") else None
        app.show_history_detail(sessione)

    month_cards = []
    for m_idx in range(1, 13):
        cal = calendar.monthcalendar(2026, m_idx)
        
        m_title = ft.Text(mesi_nomi[m_idx-1], size=11, weight=ft.FontWeight.BOLD, color=theme.TEXT)
        
        days_header = ft.Row(
            [ft.Text(g, size=8, color=theme.TEXT_MUTED, text_align=ft.TextAlign.CENTER, width=16) for g in giorni_settimana],
            spacing=1,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        weeks_col = [days_header]
        for week in cal:
            week_row = []
            for day in week:
                if day == 0:
                    week_row.append(ft.Container(width=16, height=16))
                else:
                    d_obj = date(2026, m_idx, day)
                    is_trained = d_obj in allenati_map
                    
                    bg_color = theme.PRIMARY if is_trained else "transparent"
                    text_color = "white" if is_trained else theme.TEXT_MUTED
                    
                    week_row.append(
                        ft.Container(
                            content=ft.Text(str(day), size=8, color=text_color, text_align=ft.TextAlign.CENTER),
                            alignment=ft.alignment.center,
                            width=16,
                            height=16,
                            bgcolor=bg_color,
                            border_radius=3,
                        )
                    )
            weeks_col.append(ft.Row(week_row, spacing=1, alignment=ft.MainAxisAlignment.CENTER))

        month_container = ft.Container(
            content=ft.Column([m_title, ft.Column(weeks_col, spacing=1)], spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=6,
            bgcolor=theme.CARD_BG if hasattr(theme, "CARD_BG") else "#1a1a1a",
            border_radius=8,
            border=ft.border.all(1, theme.BORDER),
            width=135,
            ink=True,
            on_click=lambda e, idx=m_idx: apri_mese_ingrandito(idx),
            tooltip="Tocca per ingrandire il mese",
        )
        month_cards.append(month_container)

    return ft.Column(
        [
            ft.Row(
                [
                    ft.Text("Calendario 2026", size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ft.Text("(Tocca un mese)", size=11, color=theme.TEXT_MUTED, italic=True),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Row(
                month_cards,
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
            ),
        ],
        spacing=6,
    )


def _history_card(app, sessione: dict) -> ft.Control:
    """Costruisce la card riassuntiva di un allenamento passato e la rende cliccabile."""
    n_esercizi = len(sessione.get("esercizi", []))
    n_serie = sum(len(e.get("serie_svolte", [])) for e in sessione.get("esercizi", []))

    return ft.Container(
        content=ft.Row(
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
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=theme.PRIMARY),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=14,
        margin=ft.margin.only(bottom=8),
        bgcolor=theme.CARD_BG if hasattr(theme, "CARD_BG") else "#1a1a1a",
        border_radius=12,
        border=ft.border.all(1, theme.BORDER),
        ink=True,
        on_click=lambda e, s=sessione: app.show_history_detail(s),
    )


def build_home_view(app) -> ft.Control:
    """Costruisce la schermata Home con statistiche, avviso scadenza, storico, calendario, box Accesso rapido e tasto Inizia."""

    # 1. Intestazione con titolo a sinistra e tasto impostazioni a destra
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
                icon=ft.Icons.SETTINGS_ROUNDED,
                icon_color=theme.TEXT,
                icon_size=24,
                on_click=lambda e: app.show_settings(),
                tooltip="Impostazioni",
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # --- Blocco Statistiche e Avviso Scadenza ---
    storico_list = app.data.get("storico", [])
    tot_allenamenti = len(storico_list)
    
    # Calcolo approssimativo delle ore di ferro (assumendo una media di 50 minuti o basandosi sulla durata se salvata)
    minuti_totali = 0
    for s in storico_list:
        durata_str = s.get("durata", "")
        # Parsing semplice se presente es. "1h 12m" o "45m"
        try:
            h = 0
            m = 0
            if "h" in durata_str:
                parts = durata_str.split("h")
                h = int(parts[0].strip())
                rest = parts[1].replace("m", "").strip()
                if rest:
                    m = int(rest)
            elif "m" in durata_str:
                m = int(durata_str.replace("m", "").replace("s", "").split()[0])
            minuti_totali += (h * 60) + m
        except Exception:
            minuti_totali += 55 # stima di fallback se il formato varia

    ore_ferro = round(minuti_totali / 60, 1)

    # Calcolo media settimanale approssimativa (basata sulle settimane dall'inizio dell'anno o storico)
    media_settimanale = round(tot_allenamenti / max(1, (datetime.now().date() - date(2026, 1, 1)).days // 7), 1)

    stat_card = ft.Container(
        content=ft.Row(
            [
                ft.Column([
                    ft.Text(str(tot_allenamenti), size=18, weight=ft.FontWeight.BOLD, color=theme.PRIMARY),
                    ft.Text("Workout", size=10, color=theme.TEXT_MUTED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, expand=True),
                ft.VerticalDivider(width=1, color=theme.BORDER),
                ft.Column([
                    
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, expand=True),
                ft.VerticalDivider(width=1, color=theme.BORDER),
                ft.Column([
                    ft.Text(str(media_settimanale), size=18, weight=ft.FontWeight.BOLD, color=theme.PRIMARY),
                    ft.Text("Media/sett.", size=10, color=theme.TEXT_MUTED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, expand=True),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        ),
        padding=10,
        bgcolor=theme.CARD_BG if hasattr(theme, "CARD_BG") else "#1a1a1a",
        border_radius=12,
        border=ft.border.all(1, theme.BORDER),
    )

    # Avviso Scadenza Scheda (simulato o basato su una data di scadenza configurabile, es. 30 giorni dall'ultima modifica o fissa)
    # Mostriamo un avviso dinamico se l'ultimo allenamento risale a un po' o come promemoria generale della scheda attiva
    avviso_scadenza = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=theme.WARNING, size=20),
                ft.Text("La scheda attiva è in corso di validità. Monitora i carichi!", size=12, color=theme.TEXT, expand=True),
            ],
            spacing=8,
        ),
        padding=10,
        bgcolor=theme.BG_CARD_LIGHT if hasattr(theme, "BG_CARD_LIGHT") else "#2a2a2a",
        border_radius=10,
        border=ft.border.all(1, theme.WARNING),
    )

    stats_and_warning_section = ft.Column(
        [
            stat_card,
            avviso_scadenza,
        ],
        spacing=8,
    )

    # 2. Storico
    storico = list(reversed(app.data.get("storico", [])))
    if storico:
        history_controls = [_history_card(app, s) for s in storico]
    else:
        history_controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.HISTORY, size=32, color=theme.TEXT_MUTED),
                        ft.Text(
                            "Nessun allenamento registrato.",
                            color=theme.TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER,
                            size=12,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                ),
                alignment=ft.alignment.center,
                padding=12,
            )
        ]

    # 3. Calendario annuale
    calendar_section = _build_year_calendar(app)

    # 4. Griglia di azioni rapide: Scheda, PR, Grafici, Backup.
    def _quick_action(icona, titolo, sottotitolo, colore, on_click):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Icon(icona, color=colore, size=22),
                        padding=8,
                        bgcolor=theme.BG_CARD_LIGHT if hasattr(theme, "BG_CARD_LIGHT") else "#2a2a2a",
                        border_radius=10,
                    ),
                    ft.Text(titolo, size=13, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ft.Text(sottotitolo, size=10, color=theme.TEXT_MUTED),
                ],
                spacing=4,
            ),
            padding=12,
            bgcolor=theme.CARD_BG if hasattr(theme, "CARD_BG") else "#1a1a1a",
            border_radius=14,
            border=ft.border.all(1, theme.BORDER),
            ink=True,
            on_click=on_click,
            width=155,
        )

    quick_actions_grid = ft.Row(
        [
            _quick_action(ft.Icons.VIEW_LIST, "Scheda", "Modifica giorni/esercizi", theme.PRIMARY,
                        lambda e: app.show_schema_editor()),
            _quick_action(ft.Icons.EMOJI_EVENTS, "Record (PR)", "I tuoi massimali", getattr(theme, "GOLD", "#FFD700"),
                        lambda e: app.show_pr()),
            _quick_action(ft.Icons.SHOW_CHART, "Grafici", "Andamento progressi", getattr(theme, "INFO", "#2196F3"),
                        lambda e: app.show_progress()),
            _quick_action(ft.Icons.BACKUP, "Backup", "Esporta/importa dati", getattr(theme, "SUCCESS", "#4CAF50"),
                        lambda e: app.show_backup()),
        ],
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
    )

    scheda_box = ft.Column(
        [
            ft.Text("Accesso rapido", size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
            quick_actions_grid,
        ],
        spacing=8,
    )

    # 5. Tasto gigante "INIZIA ALLENAMENTO"
    start_button = ft.Container(
        content=ft.ElevatedButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, size=32, color="white"),
                    ft.Text("INIZIA ALLENAMENTO", size=18, weight=ft.FontWeight.BOLD),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6,
            ),
            bgcolor=theme.PRIMARY,
            color="white",
            height=64,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=18)),
            on_click=lambda e: app.show_selection(),
        ),
        padding=ft.padding.symmetric(vertical=4),
    )

    # Assemblaggio finale della lista a scorrimento
    main_content = ft.ListView(
        [
            header,
            ft.Divider(color=theme.BORDER, height=15),
            stats_and_warning_section,
            ft.Divider(color=theme.BORDER, height=15),
            ft.Text("Storico allenamenti", size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
            *history_controls,
            ft.Divider(color=theme.BORDER, height=15),
            calendar_section,
            ft.Divider(color=theme.BORDER, height=15),
            scheda_box,
            start_button,
        ],
        expand=True,
        spacing=10,
    )

    return ft.Column(
        [
            main_content,
        ],
        expand=True,
    )