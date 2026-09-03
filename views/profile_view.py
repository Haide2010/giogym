"""
profile_view.py
---------------
Sezione "Profilo & Nutrizione".
Permette di inserire i dati antropometrici e calcola automaticamente:
- Fase di ricomposizione (CUT / BULK / MAINTENANCE)
- BMI e classificazione
- Metabolismo basale (BMR) con Mifflin-St Jeor
- Dispendio energetico totale (TDEE) e calorie target per fase

Inclusi anche:
- Registro del peso corporeo mattutino (storico)
- Rapporto forza / peso corporeo (es. 1.5x il peso corporeo su panca)
"""

import flet as ft
import theme
import fitness_calc
import data_manager as dm
import pr_manager


def _ultimo_peso_corporeo(app) -> float:
    """Ultimo peso corporeo registrato (o quello attuale del profilo)."""
    log = app.data.get("peso_corporeo", [])
    if log:
        return float(log[-1].get("peso", 0) or 0)
    return float(app.data.get("profilo", {}).get("peso_attuale_kg", 0) or 0)


class ProfileView:
    def __init__(self, app):
        self.app = app
        self.page = app.page
        self.profilo = app.data.setdefault("profilo", {})

    def build(self) -> ft.Control:
        header = ft.Row(
            [
                ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=theme.TEXT,
                              on_click=lambda e: self.app.show_home()),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.PERSON, color=theme.PRIMARY, size=24),
                        ft.Text("Profilo & Nutrizione", size=theme.TITLE_SIZE,
                                weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ],
                    spacing=8,
                ),
            ],
        )

        # --- Form dati profilo ---
        altezza = ft.TextField(label="Altezza (cm)", dense=True, keyboard_type=ft.KeyboardType.NUMBER,
                               value=str(self.profilo.get("altezza_cm", 175)),
                               helper_text="Es. 175")
        peso_att = ft.TextField(label="Peso attuale (kg)", dense=True, keyboard_type=ft.KeyboardType.NUMBER,
                                value=str(self.profilo.get("peso_attuale_kg", 68.5)),
                                helper_text="Es. 68.5")
        peso_ob = ft.TextField(label="Peso obiettivo (kg)", dense=True, keyboard_type=ft.KeyboardType.NUMBER,
                               value=str(self.profilo.get("peso_obiettivo_kg", 72.0)),
                               helper_text="Es. 72.0 per massa / 65 per definizione")
        freq = ft.TextField(label="Frequenza di allenamento (giorni/settimana)", dense=True,
                            keyboard_type=ft.KeyboardType.NUMBER,
                            value=str(self.profilo.get("frequenza_settimanale", 4)))
        eta = ft.TextField(label="Età", dense=True, keyboard_type=ft.KeyboardType.NUMBER,
                           value=str(self.profilo.get("eta", 25)))
        sesso = ft.Dropdown(
            label="Sesso",
            options=[ft.dropdown.Option("M", "Maschio"), ft.dropdown.Option("F", "Femmina")],
            value=self.profilo.get("sesso", "M"),
        )

        status_text = ft.Text("", size=12)

        def _salva(e):
            try:
                self.profilo["altezza_cm"] = float(altezza.value)
                self.profilo["peso_attuale_kg"] = float(peso_att.value)
                self.profilo["peso_obiettivo_kg"] = float(peso_ob.value)
                self.profilo["frequenza_settimanale"] = int(float(freq.value))
                self.profilo["eta"] = int(float(eta.value))
                self.profilo["sesso"] = sesso.value or "M"
            except (ValueError, TypeError):
                status_text.value = "Controlla i valori inseriti (numeri validi)."
                status_text.color = theme.DANGER
                self.page.update()
                return
            self.app.save()
            status_text.value = "Profilo salvato. I calcoli sono aggiornati."
            status_text.color = theme.SUCCESS
            self._refresh_risultati(self.risultati_column)
            self.page.update()

        form_card = theme.card_container(
            ft.Column(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.EDIT, color=theme.INFO, size=20),
                        ft.Text("Dati del profilo", size=theme.SUBTITLE_SIZE,
                                weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ], spacing=8),
                    ft.Row([altezza, peso_att], spacing=8),
                    peso_ob,
                    ft.Row([freq, eta, sesso], spacing=8, wrap=True),
                    ft.ElevatedButton(
                        content=ft.Row(
                            [ft.Icon(ft.Icons.SAVE, color="white"), ft.Text("Salva profilo", weight=ft.FontWeight.BOLD)],
                            spacing=8,
                        ),
                        bgcolor=theme.PRIMARY, color="white", on_click=_salva,
                    ),
                    status_text,
                ],
                spacing=8,
            ),
        )

        # --- Registro peso corporeo ---
        log_status = ft.Text("", size=12)
        pesoTxt = ft.TextField(label="Peso mattutino (kg)", dense=True, keyboard_type=ft.KeyboardType.NUMBER,
                               helper_text="Registra il tuo peso di oggi")

        def _salva_peso(e):
            try:
                p = float(pesoTxt.value)
            except (TypeError, ValueError):
                log_status.value = "Inserisci un peso valido."
                log_status.color = theme.DANGER
                self.page.update()
                return
            log = self.app.data.setdefault("peso_corporeo", [])
            log.append({"data": dm.today_str(), "peso": p})
            self.app.save()
            pesoTxt.value = ""
            log_status.value = "Peso registrato!"
            log_status.color = theme.SUCCESS
            self._refresh_peso_log(self.peso_log_column)
            self.page.update()

        self.peso_log_column = ft.Column(spacing=4)
        self._refresh_peso_log(self.peso_log_column)

        peso_card = theme.card_container(
            ft.Column(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.MONITOR_WEIGHT, color=theme.SUCCESS, size=20),
                        ft.Text("Registro peso corporeo", size=theme.SUBTITLE_SIZE,
                                weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ], spacing=8),
                    ft.Row([pesoTxt, ft.ElevatedButton("Registra", bgcolor=theme.SUCCESS, color="white",
                                                        on_click=_salva_peso)], spacing=8),
                    self.peso_log_column,
                    log_status,
                ],
                spacing=8,
            ),
        )

        # --- Card risultati (BMI, fase, calorie, forza/peso) ---
        self.risultati_column = ft.Column(spacing=8)
        self._refresh_risultati(self.risultati_column)

        content_list = ft.ListView(
            [
                header,
                ft.Divider(color=theme.BORDER, height=15),
                form_card,
                ft.Divider(color=theme.BORDER, height=15),
                peso_card,
                ft.Divider(color=theme.BORDER, height=15),
                self.risultati_column,
            ],
            expand=True,
            spacing=10,
        )

        return ft.Column([content_list], expand=True)

    def _refresh_risultati(self, container: ft.Column):
        container.controls.clear()
        p = self.profilo
        try:
            peso = float(p.get("peso_attuale_kg", 0) or 0)
            alt = float(p.get("altezza_cm", 0) or 0)
            ob = float(p.get("peso_obiettivo_kg", 0) or 0)
            freq = int(p.get("frequenza_settimanale", 0) or 0)
            eta = int(p.get("eta", 0) or 0)
            sesso = p.get("sesso", "M")
        except (TypeError, ValueError):
            peso = 0
            alt = 0
            ob = 0
            freq = 0
            eta = 0
            sesso = "M"

        if peso <= 0 or alt <= 0:
            container.controls.append(
                ft.Text("Compila e salva i dati del profilo per vedere i calcoli.",
                        color=theme.TEXT_MUTED, size=13)
            )
            return

        bmi_val = fitness_calc.bmi(peso, alt)
        cat = fitness_calc.bmi_category(bmi_val)
        fase = fitness_calc.fase_ricomposizione(peso, ob)
        bmr = fitness_calc.bmr_mifflin(peso, alt, eta, sesso)
        tdee_val = fitness_calc.tdee(bmr, freq)
        target = fitness_calc.calorie_target(tdee_val, fase)

        fase_colors = {
            "CUT": getattr(theme, "SUCCESS", "#4CAF50"),
            "BULK": getattr(theme, "INFO", "#2196F3"),
            "MAINTENANCE": getattr(theme, "GOLD", "#FFC107"),
        }
        bmi_colors = {
            "Sottopeso": getattr(theme, "INFO", "#4DC3FF"),
            "Normopeso": getattr(theme, "SUCCESS", "#3DDC97"),
            "Sovrappeso": getattr(theme, "WARNING", "#FFB300"),
            "Obesità": getattr(theme, "DANGER", "#FF5C5C"),
        }
        colore_fase = fase_colors.get(fase, theme.PRIMARY)
        colore_bmi = bmi_colors.get(cat, theme.PRIMARY)

        # Card riepilogo: tachimetro BMI (anello di progresso) + badge fase e categoria
        bmi_ring = ft.Stack(
            [
                ft.ProgressRing(
                    value=min(bmi_val / 40.0, 1.0),
                    stroke_width=8,
                    width=120,
                    height=120,
                    color=colore_bmi,
                    bgcolor=theme.BG_CARD_LIGHT,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(str(bmi_val), size=theme.BIG_NUMBER_SIZE,
                                    weight=ft.FontWeight.BOLD, color=theme.TEXT),
                            ft.Text("BMI", size=12, color=theme.TEXT_MUTED),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                    ),
                    alignment=ft.alignment.center,
                ),
            ],
            width=120,
            height=120,
        )

        riepilogo = theme.card_container(
            ft.Column(
                [
                    ft.Row(
                        [bmi_ring, ft.VerticalDivider(width=1, color=theme.BORDER)],
                        alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(
                        content=ft.Text(f"BMI · {cat}", size=13, weight=ft.FontWeight.BOLD, color="white"),
                        bgcolor=colore_bmi,
                        padding=ft.padding.symmetric(horizontal=16, vertical=7),
                        border_radius=20,
                        alignment=ft.alignment.center,
                    ),
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(fase, size=16, weight=ft.FontWeight.BOLD, color="white"),
                                        ft.Text("Fase attiva", size=11, color="#FFFFFFCC"),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=1,
                                ),
                                bgcolor=colore_fase,
                                padding=ft.padding.symmetric(horizontal=18, vertical=10),
                                border_radius=theme.RADIUS,
                                expand=True,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        container.controls.append(riepilogo)

        # Card calorie & obiettivi
        calorie_card = theme.card_container(
            ft.Column(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, color=theme.WARNING, size=20),
                        ft.Text("Calorie & Obiettivi", size=theme.SUBTITLE_SIZE,
                                weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ], spacing=8),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Obiettivo giornaliero",
                                        size=12, color=theme.TEXT_MUTED, weight=ft.FontWeight.BOLD),
                                ft.Row(
                                    [
                                ft.Text(
                                    str(int(target['max'])),
                                    size=theme.BIG_NUMBER_SIZE,
                                    weight=ft.FontWeight.BOLD,
                                    color=colore_fase,
                                ),
                                        ft.Text("kcal", size=14, color=theme.TEXT_MUTED,
                                                weight=ft.FontWeight.BOLD),
                                    ],
                                    spacing=4,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                ft.Text(f"intervallo {target['min']:.0f} – {target['max']:.0f} kcal",
                                        size=11, color=theme.TEXT_MUTED),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=-2,
                        ),
                        padding=14,
                        bgcolor=theme.BG_CARD_LIGHT,
                        border_radius=theme.RADIUS_SMALL,
                    ),
                    ft.Text(target["nota"], size=11, color=theme.TEXT_MUTED, italic=True),
                    ft.Divider(color=theme.BORDER, height=8),
                    self._kv("Metabolismo basale (BMR)", f"{bmr:.0f} kcal"),
                    self._kv("Dispendio totale (TDEE)", f"{tdee_val:.0f} kcal"),
                    self._kv("Fase", fase, colore=fase_colors.get(fase, theme.TEXT)),
                    self._kv("Target di peso", f"{ob} kg", colore=theme.TEXT),
                ],
                spacing=6,
            ),
        )
        container.controls.append(calorie_card)

        # Card rapporto forza / peso corporeo
        self._refresh_force_card(container)

    def _kv(self, label: str, valore: str, colore=None):
        return ft.Row(
            [
                ft.Text(label, size=13, color=theme.TEXT_MUTED, expand=True),
                ft.Text(valore, size=14, weight=ft.FontWeight.BOLD,
                        color=colore or theme.TEXT),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def _refresh_force_card(self, container: ft.Column):
        peso_bw = _ultimo_peso_corporeo(self.app)
        storico = self.app.data.get("storico", [])
        prs = pr_manager.compute_all_prs(storico)
        if not prs or peso_bw <= 0:
            container.controls.append(
                theme.card_container(
                    ft.Column(
                        [
                            ft.Row([
                                ft.Icon(ft.Icons.STRAIGHTEN, color=theme.GOLD if hasattr(theme, "GOLD") else "#FFD700", size=20),
                                ft.Text("Forza / Peso corporeo", size=theme.SUBTITLE_SIZE,
                                        weight=ft.FontWeight.BOLD, color=theme.TEXT),
                            ], spacing=8),
                            ft.Text("Completa allenamenti e registra il peso corporeo per vedere il rapporto forza/peso.",
                                    size=12, color=theme.TEXT_MUTED),
                        ],
                        spacing=6,
                    ),
                )
            )
            return

        # Top 3 esercizi per rapporto forza/peso (usando il PR di peso)
        righe = []
        for nome, rec in prs.items():
            if rec.get("max_peso", 0) <= 0:
                continue
            ratio = fitness_calc.forza_peso_ratio(rec["max_peso"], peso_bw)
            righe.append((nome, rec["max_peso"], ratio))
        righe.sort(key=lambda x: x[2], reverse=True)
        righe = righe[:3]

        cons = [ft.Row([
            ft.Icon(ft.Icons.STRAIGHTEN, color=theme.GOLD if hasattr(theme, "GOLD") else "#FFD700", size=20),
            ft.Text("Forza / Peso corporeo", size=theme.SUBTITLE_SIZE,
                    weight=ft.FontWeight.BOLD, color=theme.TEXT),
        ], spacing=8)]
        cons.append(ft.Text(f"Peso corporeo attuale: {peso_bw} kg", size=12, color=theme.TEXT_MUTED))

        for nome, peso_pr, ratio in righe:
            cons.append(ft.Row(
                [
                    ft.Text(nome, size=13, color=theme.TEXT, expand=True),
                    ft.Text(f"{ratio}x", size=15, weight=ft.FontWeight.BOLD, color=theme.PRIMARY),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ))
        container.controls.append(theme.card_container(ft.Column(cons, spacing=6)))

    def _refresh_peso_log(self, container: ft.Column):
        container.controls.clear()
        log = self.app.data.get("peso_corporeo", [])
        if not log:
            container.controls.append(
                ft.Text("Nessun peso registrato.", color=theme.TEXT_MUTED, size=12)
            )
            return
        # Ultime 5 voci
        for entry in log[-5:]:
            container.controls.append(
                ft.Row(
                    [
                        ft.Text(entry.get("data", "-"), size=12, color=theme.TEXT_MUTED),
                        ft.Text(f"{entry.get('peso', 0)} kg", size=13, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )


def build_profile_view(app) -> ft.Control:
    return ProfileView(app).build()
