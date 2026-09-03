"""
home_view.py
------------
Schermata A - Home / Dashboard.
Nuovo layout "plancia di comando" in stile mobile app:
- Header con nome grande e icona profilo/impostazioni tonda.
- Card hero "Workout Streak & Status" con palina di progresso settimanale.
- Vista della settimana corrente (Lun-Dom) con cerchi per i giorni completati.
- Statistiche chiave (Workout, Volume, Media) con numeri grandi.
- Storico allenamenti.
- Accesso rapido a "pillole" scorrevoli.
- Floating Action Button centrale con gradiente: "INIZIA WORKOUT".
"""

from datetime import datetime, date, timedelta
import asyncio
import flet as ft
import theme
import fitness_calc


def _history_card(app, sessione: dict) -> ft.Control:
    """Costruisce la card riassuntiva di un allenamento passato e la rende cliccabile."""
    n_esercizi = len(sessione.get("esercizi", []))
    n_serie = sum(len(e.get("serie_svolte", [])) for e in sessione.get("esercizi", []))
    vol = fitness_calc.volume_sessione(sessione) if hasattr(fitness_calc, "volume_sessione") else None

    meta = f"{n_esercizi} esercizi · {n_serie} serie"
    if vol:
        meta += f" · {vol:g} kg"

    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.FITNESS_CENTER, color=theme.PRIMARY, size=22),
                    padding=10,
                    bgcolor=theme.BG_CARD_LIGHT,
                    border_radius=theme.RADIUS_SMALL,
                ),
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
                        ft.Text(meta, size=12, color=theme.TEXT_MUTED),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=theme.PRIMARY),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            spacing=12,
        ),
        padding=12,
        margin=ft.margin.only(bottom=8),
        bgcolor=theme.CARD_BG if hasattr(theme, "CARD_BG") else "#1E222D",
        border_radius=theme.RADIUS,
        shadow=theme.CARD_SHADOW,
        ink=True,
        on_click=lambda e, s=sessione: app.show_history_detail(s),
    )


def _settimana_corrente(storico_list) -> list:
    """Restituisce la lista (data, allenamento_o_None) dei 7 giorni Lun-Dom della settimana corrente."""
    oggi = date.today()
    lunedi = oggi - timedelta(days=oggi.weekday())
    allenati_map = {}
    for s in storico_list:
        d_str = s.get("data")
        if d_str:
            try:
                dt = datetime.strptime(d_str, "%d/%m/%Y").date()
                allenati_map[dt] = s
            except ValueError:
                pass
    giorni = []
    nomi = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
    for i in range(7):
        d = lunedi + timedelta(days=i)
        giorni.append((nomi[i], d, allenati_map.get(d)))
    return giorni


async def _fade_in(control, delay: float = 0.0):
    """Entra gradualmente (fade + leggera salita, con easing) quando la Home carica."""
    try:
        await asyncio.sleep(delay)
        control.opacity = 1
        control.offset = ft.Offset(0, 0)
        control.update()
    except Exception:
        pass


def _annual_dots_card(app, storico_list: list) -> ft.Control:
    """Mappa a pallini dell'intero anno: un pallino per ogni giorno; quelli in
    cui ti sei allenato sono colorati. Cliccando un giorno colorato si apre
    lo storico di quell'allenamento (sessione)."""
    anno = date.today().year
    oggi = date.today()

    # Mappa data -> sessione allo storico
    allenati_map = {}
    for s in storico_list:
        d_str = s.get("data")
        if d_str:
            try:
                allenati_map[datetime.strptime(d_str, "%d/%m/%Y").date()] = s
            except ValueError:
                pass
    giorni_anno = [date(anno, 1, 1) + timedelta(days=i)
                   for i in range(0, 366)]
    giorni_anno = [d for d in giorni_anno if d.year == anno]

    mesi_nomi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu",
                 "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]

    def _pallino(d: date) -> ft.Control:
        sess = allenati_map.get(d)
        allenato = sess is not None
        futuro = d > oggi
        is_oggi = d == oggi

        if futuro:
            fill = ft.Colors.with_opacity(0.0, theme.BG_CARD)   # trasparente
            colore_testo = None
        elif allenato:
            fill = theme.PRIMARY
            colore_testo = "white"
        else:
            fill = theme.BG_CARD_LIGHT
            colore_testo = theme.TEXT_MUTED

        pallino = ft.Container(
            content=ft.Text(str(d.day), size=9,
                            color=colore_testo if not futuro else ft.Colors.with_opacity(0.0, theme.BG_CARD),
                            text_align=ft.TextAlign.CENTER),
            alignment=ft.alignment.center,
            width=22, height=22,
            bgcolor=fill,
            border_radius=7,
            border=ft.border.all(2, theme.PRIMARY) if is_oggi else None,
            shadow=ft.BoxShadow(blur_radius=10, color="#FF6B0088") if allenato else None,
            ink=True,
            tooltip=f"{d.day:02d}/{d.month:02d}/{d.year} · {'Allenato' if allenato else 'Riposo'}"
                    + (f" · {sess.get('giorno_nome', '')}" if allenato else ""),
            on_click=(lambda e, s=sess: app.show_history_detail(s)) if allenato else None,
        )
        return pallino

    # Raggruppa per mese
    month_cols = []
    for m in range(1, 13):
        giorni_mese = [d for d in giorni_anno if d.month == m]
        if not giorni_mese:
            continue
        n_allenati = sum(1 for d in giorni_mese if d in allenati_map)
        month_cols.append(
            ft.Column(
                [
                    ft.Divider(color=theme.BORDER, height=6),
                    ft.Row(
                        [
                            ft.Text(mesi_nomi[m - 1], size=11, weight=ft.FontWeight.BOLD, color=theme.PRIMARY),
                            ft.Text(f"({n_allenati})", size=10, color=theme.TEXT_MUTED),
                        ],
                        spacing=4,
                    ),
                    ft.Row(
                        [_pallino(d) for d in giorni_mese],
                        spacing=4,
                        wrap=True,
                    ),
                ],
                spacing=2,
            )
        )

    tot_allenati = sum(1 for d in giorni_anno if d in allenati_map)

    return theme.card_container(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CALENDAR_MONTH, color=theme.PRIMARY, size=20),
                        ft.Column(
                            [
                                ft.Text("L'intero anno", size=theme.SUBTITLE_SIZE,
                                        weight=ft.FontWeight.BOLD, color=theme.TEXT),
                                ft.Text(f"{anno} · {tot_allenati} giorni allenati",
                                        size=12, color=theme.TEXT_MUTED),
                            ],
                            spacing=0,
                        ),
                    ],
                    spacing=8,
                ),
                *month_cols,
                ft.Divider(color=theme.BORDER, height=8),
                ft.Row(
                    [
                        ft.Container(width=12, height=12, bgcolor=theme.PRIMARY, border_radius=4),
                        ft.Text("Allenato", size=10, color=theme.TEXT_MUTED),
                        ft.Container(width=12, height=12, bgcolor=theme.BG_CARD_LIGHT, border_radius=4),
                        ft.Text("Riposo", size=10, color=theme.TEXT_MUTED),
                        ft.Container(width=12, height=12, border=ft.border.all(2, theme.PRIMARY), border_radius=4),
                        ft.Text("Oggi", size=10, color=theme.TEXT_MUTED),
                    ],
                    spacing=6,
                ),
            ],
            spacing=2,
        ),
    )


def build_home_view(app) -> ft.Control:
    """Costruisce la nuova Home in stile 'plancia di comando'."""

    storico_list = app.data.get("storico", [])
    profilo = app.data.get("profilo", {})
    target_settimanale = int(profilo.get("frequenza_settimanale", 0) or 0)
    fatta_settimana = fitness_calc.frequenza_settimana_corrente(storico_list)
    streak = fitness_calc.streak_settimane_consecutive(storico_list, target_settimanale)

    # Statistiche
    tot_allenamenti = len(storico_list)
    media_settimanale = round(tot_allenamenti / max(1, (datetime.now().date() - date(2026, 1, 1)).days // 7), 1)
    vol_settimana = fitness_calc.volume_settimanale(storico_list, mode="kg")
    volume_corrente = round(vol_settimana[0][1], 0) if vol_settimana else 0
    if volume_corrente == int(volume_corrente):
        volume_corrente = int(volume_corrente)

    # ---------- 1. Header ----------
    header = ft.Row(
        [
            ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(ft.Icons.FITNESS_CENTER, color=theme.PRIMARY, size=28),
                        padding=8,
                        bgcolor=theme.BG_CARD_LIGHT,
                        border_radius=14,
                        shadow=theme.CARD_SHADOW,
                    ),
                    ft.Column(
                        [
                            ft.Text("GioGym", size=28, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                            ft.Text("La tua plancia di comando", size=12, color=theme.TEXT_MUTED),
                        ],
                        spacing=0,
                    ),
                ],
                spacing=10,
            ),
            ft.Container(
                content=ft.IconButton(
                    icon=ft.Icons.SETTINGS_ROUNDED,
                    icon_color=theme.TEXT,
                    icon_size=22,
                    on_click=lambda e: app.show_settings(),
                    tooltip="Impostazioni",
                ),
                bgcolor=theme.BG_CARD_LIGHT,
                border_radius=20,
                padding=ft.padding.all(2),
                shadow=theme.CARD_SHADOW,
                ink=True,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # ---------- 2. Card hero Streak & Status ----------
    def _bar_scale(tipo="serie"):
        """Barrette di progresso colorate per la settimana rispetto al target."""
        target = max(target_settimanale, 1)
        riga = []
        for i in range(1, target + 1):
            pieno = i <= fatta_settimana
            riga.append(
                ft.Container(
                    width=10,
                    expand=True,
                    height=10,
                    bgcolor=theme.PRIMARY if pieno else theme.BG_CARD_LIGHT,
                    border_radius=5,
                )
            )
        return riga

    hero_card = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("QUESTA SETTIMANA", size=11, color=theme.TEXT_MUTED, weight=ft.FontWeight.BOLD),
                                ft.Row(
                                    [
                                        ft.Text(
                                            str(fatta_settimana),
                                            size=theme.BIG_NUMBER_SIZE,
                                            weight=ft.FontWeight.BOLD,
                                            color=theme.TEXT,
                                        ),
                                        ft.Text(
                                            f"/ {target_settimanale if target_settimanale else '–'}",
                                            size=18,
                                            weight=ft.FontWeight.BOLD,
                                            color=theme.TEXT_MUTED,
                                        ),
                                    ],
                                    spacing=2,
                                ),
                            ],
                            spacing=0,
                        ),
                        ft.Row(
                            [ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, color=theme.PRIMARY, size=18),
                             ft.Text(f"{streak} sett.", size=16, weight=ft.FontWeight.BOLD, color=theme.PRIMARY)],
                            spacing=4,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row(_bar_scale(), spacing=6),
                ft.Text(
                    f"Streak: {streak} settimana{'e' if streak != 1 else ''} consecutive al target. Continua così!",
                    size=12, color=theme.TEXT_MUTED,
                ),
            ],
            spacing=10,
        ),
        padding=16,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#1E222D", "#26212A"],
        ),
        border_radius=theme.RADIUS + 4,
        border=ft.border.all(1, theme.BORDER),
        shadow=theme.CARD_SHADOW,
        opacity=0,
        offset=ft.Offset(0, 20),
        animate_opacity=ft.Animation(450, ft.AnimationCurve.EASE_OUT),
        animate_offset=ft.Animation(450, ft.AnimationCurve.EASE_OUT),
    )

    # ---------- 3. Vista settimana corrente (Lun-Dom) ----------
    settimana = _settimana_corrente(storico_list)
    giorni_row = []
    for nome, d, sess in settimana:
        allenato = sess is not None
        is_oggi = d == date.today()
        giorno_circ = ft.Container(
            content=ft.Icon(ft.Icons.RADIO_BUTTON_CHECKED, size=16, color="white")
            if allenato else ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, size=16, color=theme.TEXT_MUTED),
            alignment=ft.alignment.center,
            width=36,
            height=36,
            bgcolor=theme.PRIMARY if allenato else theme.BG_CARD_LIGHT,
            border_radius=18,
            border=ft.border.all(2, theme.PRIMARY) if is_oggi else None,
        )
        giorni_row.append(
            ft.Column(
                [
                    giorno_circ,
                    ft.Text(nome, size=10, weight=ft.FontWeight.BOLD if is_oggi else ft.FontWeight.NORMAL,
                            color=theme.TEXT if is_oggi else theme.TEXT_MUTED),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            )
        )

    week_card = theme.card_container(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CALENDAR_TODAY, color=theme.PRIMARY, size=18),
                        ft.Text("Settimana corrente", size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ],
                    spacing=6,
                ),
                ft.Row(giorni_row, alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=4),
            ],
            spacing=10,
        ),
        opacity=0,
        offset=ft.Offset(0, 20),
        animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
        animate_offset=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
    )

    # ---------- 4. Statistiche chiave ----------
    stat_card = theme.card_container(
        ft.Row(
            [
                ft.Column([
                    ft.Text(str(tot_allenamenti), size=theme.BIG_NUMBER_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ft.Text("Workout", size=11, color=theme.TEXT_MUTED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, expand=True),
                ft.VerticalDivider(width=1, color=theme.BORDER),
                ft.Column([
                    ft.Text(str(volume_corrente), size=theme.BIG_NUMBER_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ft.Text("Volume (kg)", size=11, color=theme.TEXT_MUTED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, expand=True),
                ft.VerticalDivider(width=1, color=theme.BORDER),
                ft.Column([
                    ft.Text(str(media_settimanale), size=theme.BIG_NUMBER_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ft.Text("Media/sett.", size=11, color=theme.TEXT_MUTED),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0, expand=True),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        ),
        opacity=0,
        offset=ft.Offset(0, 20),
        animate_opacity=ft.Animation(550, ft.AnimationCurve.EASE_OUT),
        animate_offset=ft.Animation(550, ft.AnimationCurve.EASE_OUT),
    )

    # ---------- 5. Storico ----------
    storico = list(reversed(storico_list))
    if storico:
        history_controls = [_history_card(app, s) for s in storico[:5]]
    else:
        history_controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.HISTORY, size=32, color=theme.TEXT_MUTED),
                        ft.Text("Nessun allenamento registrato.", color=theme.TEXT_MUTED,
                                text_align=ft.TextAlign.CENTER, size=12),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4,
                ),
                alignment=ft.alignment.center,
                padding=12,
            )
        ]

    # ---------- 6. Accesso rapido a "pillole" ----------
    pills = [
        (ft.Icons.VIEW_LIST, "Scheda", lambda e: app.show_schema_editor()),
        (ft.Icons.EMOJI_EVENTS, "Record", lambda e: app.show_pr()),
        (ft.Icons.SHOW_CHART, "Grafici", lambda e: app.show_progress()),
        (ft.Icons.PERSON, "Profilo", lambda e: app.show_profile()),
        (ft.Icons.HEALING, "Infortuni", lambda e: app.show_injuries()),
        (ft.Icons.BACKUP, "Backup", lambda e: app.show_backup()),
    ]

    pill_row = []
    for icona, titolo, on_click in pills:
        pill_row.append(
            ft.Container(
                content=ft.Row(
                    [ft.Icon(icona, color=theme.PRIMARY, size=16), ft.Text(titolo, size=13, weight=ft.FontWeight.BOLD, color=theme.TEXT)],
                    spacing=6,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=ft.padding.symmetric(horizontal=14, vertical=10),
                bgcolor=theme.BG_CARD_LIGHT,
                border_radius=24,
                shadow=theme.CARD_SHADOW,
                ink=True,
                on_click=on_click,
            )
        )

    quick_access = ft.Column(
        [
            ft.Row(
                [ft.Icon(ft.Icons.APP_SHORTCUT, color=theme.PRIMARY, size=18),
                 ft.Text("Accesso rapido", size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT)],
                spacing=6,
            ),
            ft.Row(pill_row, spacing=8, scroll=ft.ScrollMode.AUTO),
        ],
        spacing=10,
    )

    # ---------- 7. Contenuto scorrevole ----------
    annual_card = _annual_dots_card(app, storico_list)

    main_content = ft.ListView(
        [
            header,
            ft.Divider(color=theme.BORDER, height=16),
            hero_card,
            ft.Divider(color=theme.BORDER, height=10),
            week_card,
            ft.Divider(color=theme.BORDER, height=10),
            stat_card,
            ft.Divider(color=theme.BORDER, height=16),
            ft.Text("Storico allenamenti", size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
            *history_controls,
            ft.Divider(color=theme.BORDER, height=16),
            quick_access,
            ft.Divider(color=theme.BORDER, height=16),
            annual_card,
        ],
        expand=True,
        spacing=8,
        padding=ft.padding.only(bottom=90),
    )

    # ---------- 8. FAB "INIZIA WORKOUT" ----------
    def _avvia_workout(e):
        # feedback "a pressione" sull'FAB
        fab.scale = 0.93
        fab.update()
        try:
            e.page.run_task(_unpress_fab, fab)
        except Exception:
            pass
        app.show_selection()

    async def _unpress_fab(control):
        await asyncio.sleep(0.1)
        try:
            control.scale = 1.0
            control.update()
        except Exception:
            pass

    fab = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, size=28, color="white"),
                ft.Text("INIZIA WORKOUT", size=16, weight=ft.FontWeight.BOLD, color="white"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
        ),
        padding=ft.padding.symmetric(horizontal=28, vertical=18),
        gradient=ft.LinearGradient(
            begin=ft.alignment.center_left,
            end=ft.alignment.center_right,
            colors=[theme.GRADIENT_START, theme.GRADIENT_END],
        ),
        border_radius=32,
        shadow=ft.BoxShadow(spread_radius=2, blur_radius=24, color="#FF6B0088", offset=ft.Offset(0, 6)),
        ink=True,
        opacity=0,
        offset=ft.Offset(0, 30),
        animate_opacity=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
        animate_offset=ft.Animation(500, ft.AnimationCurve.EASE_OUT),
        animate_scale=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
        on_click=_avvia_workout,
    )

    # Programma l'ingresso animato (fade + salita) a scaglioni
    if hasattr(app.page, "run_task"):
        try:
            app.page.run_task(_fade_in, hero_card, 0.05)
            app.page.run_task(_fade_in, week_card, 0.18)
            app.page.run_task(_fade_in, stat_card, 0.30)
            app.page.run_task(_fade_in, fab, 0.42)
        except Exception:
            pass

    return ft.Stack(
        [
            main_content,
            ft.Container(
                content=fab,
                alignment=ft.alignment.center,
                bgcolor=ft.Colors.with_opacity(0.0, theme.BG),
                left=0,
                right=0,
                bottom=16,
            ),
        ],
        expand=True,
    )


# Manteniamo l'annuale disponibile ma non più mostrato di default (sostituito dalla vista settimanale).
def _build_year_calendar(app) -> ft.Control:
    import calendar
    return ft.Text("", visible=False)
