"""
diet_view.py
------------
Vista "Dieta & Calorie": calcola metabolismo basale (BMR), dispendio
energetico (TDEE), calorie giornaliere per obiettivo e ripartizione macro.
"""

import flet as ft
import theme


LIVELLI = [
    ("sedentario", "Sedentario (poco o niente sport)", 1.2),
    ("leggero", "Leggero (1-3 allenamenti/settimana)", 1.375),
    ("moderato", "Moderato (3-5 allenamenti/settimana)", 1.55),
    ("attivo", "Attivo (6-7 allenamenti/settimana)", 1.725),
    ("molto", "Molto attivo (lavoro fisico + sport)", 1.9),
]


class DietView:
    def __init__(self, app):
        self.app = app
        self.page = app.page
        self.livello_dd = None
        self.bmr_text = ft.Text(color=theme.TEXT, weight=ft.FontWeight.BOLD, size=28)
        self.tdee_text = ft.Text(color=theme.TEXT_MUTED, size=14)
        self.goal_text = ft.Text(color=theme.TEXT, weight=ft.FontWeight.BOLD, size=28)
        self.goal_info = ""
        self.macro_pro_text = ft.Text(weight=ft.FontWeight.BOLD, color=theme.TEXT, size=15)
        self.macro_car_text = ft.Text(weight=ft.FontWeight.BOLD, color=theme.TEXT, size=15)
        self.macro_gra_text = ft.Text(weight=ft.FontWeight.BOLD, color=theme.TEXT, size=15)
        self.status = ft.Text("", size=12, color=theme.TEXT_MUTED)

    # ------------------------------------------------------------------
    def build(self) -> ft.Control:
        header = ft.Row(
            [
                theme.back_button(lambda e: self.app.show_home()),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.RESTAURANT, color=theme.SUCCESS, size=24),
                        ft.Text("Dieta & Calorie", size=theme.TITLE_SIZE,
                                weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ],
                    spacing=8,
                ),
            ],
        )

        profilo = self.app.data.get("profilo", {})
        peso = profilo.get("peso_attuale_kg")
        altezza = profilo.get("altezza_cm")
        eta = profilo.get("eta")

        dati_completi = all(
            x is not None for x in (peso, altezza, eta)
        ) and float(peso) > 0 and float(altezza) > 0 and float(eta) > 0

        self.livello_dd = ft.Dropdown(
            label="Livello di attività",
            options=[ft.dropdown.Option(key, testo) for key, testo, _ in LIVELLI],
            value=str(profilo.get("livello_attivita", "moderato")),
            on_change=self._cambia_livello,
            dense=True,
        )

        numeri_card = theme.card_container(
            ft.Column(
                [
                    self._numero("Metabolismo basale (BMR)", self.bmr_text,
                                "Calorie che bruci a riposo", theme.INFO),
                    ft.Divider(color=theme.BORDER, height=12),
                    self._numero("Dispendio totale (TDEE)", self.tdee_text,
                                "BMR × fattore attività", theme.PRIMARY),
                    ft.Divider(color=theme.BORDER, height=12),
                    self._numero("Calorie giornaliere per obiettivo", self.goal_text,
                                self.goal_info, theme.SUCCESS),
                    ft.Divider(color=theme.BORDER, height=12),
                    ft.Row(
                        [
                            ft.Column([
                                ft.Icon(ft.Icons.ROUNDED_CORNER, color=theme.INFO, size=18),
                                self.macro_pro_text,
                                ft.Text("Proteine", size=11, color=theme.TEXT_MUTED),
                            ], spacing=2),
                            ft.Column([
                                ft.Icon(ft.Icons.GRAIN, color=theme.PRIMARY, size=18),
                                self.macro_car_text,
                                ft.Text("Carboidrati", size=11, color=theme.TEXT_MUTED),
                            ], spacing=2),
                            ft.Column([
                                ft.Icon(ft.Icons.WATER_DROP, color=theme.WARNING, size=18),
                                self.macro_gra_text,
                                ft.Text("Grassi", size=11, color=theme.TEXT_MUTED),
                            ], spacing=2),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        expand=True,
                    ),
                ],
                spacing=8,
                visible=dati_completi,
            ),
        )

        manca_card = theme.card_container(
            ft.Column(
                [
                    ft.Icon(ft.Icons.HELP_OUTLINE, color=theme.WARNING, size=28),
                    ft.Text("Compila i dati del Profilo",
                            weight=ft.FontWeight.BOLD, color=theme.TEXT, size=15),
                    ft.Text("Manca peso, altezza o età: il calcolo delle calorie "
                            "ha bisogno di questi dati.", size=12, color=theme.TEXT_MUTED),
                    theme.primary_button("Apri il Profilo", lambda e: self.app.show_profile(),
                                         expand=True, icon=ft.Icons.PERSON),
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                visible=not dati_completi,
            ),
        )

        consigli_card = theme.card_container(
            ft.Column(
                [
                    ft.Row([
                        ft.Icon(ft.Icons.TIPS_AND_UPDATES, color=theme.PRIMARY, size=20),
                        ft.Text("Consigli", size=theme.SUBTITLE_SIZE,
                                weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ], spacing=8),
                    *[
                        ft.Row(
                            [ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=theme.SUCCESS, size=16),
                             ft.Text(t, size=13, color=theme.TEXT)],
                            spacing=8,
                        )
                        for t in (
                            "Bevi 2-3 litri di acqua al giorno.",
                            "Dormi 7-9 ore: il recupero vale quanto l'allenamento.",
                            "Distribuisci le proteine in 3-4 pasti.",
                            "Registra il peso a cadenza regolare per vedere i progressi.",
                        )
                    ],
                ],
                spacing=8,
                visible=dati_completi,
            ),
        )

        if dati_completi:
            self._ricalcola()

        return ft.Column(
            [
                header,
                ft.Divider(color=theme.BORDER, height=15),
                self.livello_dd,
                ft.Divider(color=theme.BORDER, height=12),
                numeri_card,
                ft.Divider(color=theme.BORDER, height=12),
                consigli_card,
                ft.Divider(color=theme.BORDER, height=12),
                self.status,
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

    # ------------------------------------------------------------------
    def _numero(self, label, valore, sotto, colore) -> ft.Control:
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        width=10, height=44,
                        bgcolor=ft.Colors.with_opacity(0.25, colore),
                        border_radius=6,
                    ),
                    ft.Column(
                        [
                            ft.Text(label, size=12, color=theme.TEXT_MUTED),
                            ft.Row(
                                [valore,
                                 ft.Text("kcal", size=13, color=theme.TEXT_MUTED)],
                                spacing=6,
                            ),
                            ft.Text(sotto, size=11, color=theme.TEXT_MUTED),
                        ],
                        spacing=0,
                    ),
                ],
                spacing=12,
            ),
            padding=10,
            bgcolor=theme.BG_CARD_LIGHT,
            border_radius=12,
        )

    # ------------------------------------------------------------------
    def _cambia_livello(self, e):
        self.app.data.setdefault("profilo", {})["livello_attivita"] = e.control.value
        self.app.save()
        self._ricalcola()
        self.status.value = "Livello aggiornato: obiettivi ricalcolati."
        self.status.color = theme.SUCCESS
        self.page.update()

    def _ricalcola(self):
        profilo = self.app.data.get("profilo", {})
        peso = float(profilo.get("peso_attuale_kg") or 0)
        altezza = float(profilo.get("altezza_cm") or 0)
        eta = float(profilo.get("eta") or 0)
        sesso = str(profilo.get("sesso", "M")).upper()

        bmr = 10 * peso + 6.25 * altezza - 5 * eta
        bmr += 5 if sesso != "F" else -161
        fattore = dict((k, v) for k, _, v in LIVELLI).get(
            str(profilo.get("livello_attivita", "moderato")), 1.55)
        tdee = bmr * fattore

        obiettivo = str(profilo.get("obiettivo", "")).lower()
        if obiettivo == "massa":
            goal = tdee * 1.15
            info = "Surplus calorico (+15%): per mettere massa"
        elif obiettivo == "definizione":
            goal = tdee * 0.85
            info = "Deficit calorico (-15%): per perdere grasso"
        elif obiettivo == "salute":
            goal = tdee * 0.95
            info = "Leggero deficit (-5%): benessere generale"
        else:
            goal = tdee
            info = "Mantenimento: bilanciato"

        proteine = peso * 2.0
        grassi = (goal * 0.25) / 9
        carboidrati = (goal - proteine * 4 - grassi * 9) / 4

        self.bmr_text.value = f"{int(round(bmr))}"
        self.tdee_text.value = f"{int(round(tdee))}"
        self.goal_text.value = f"{int(round(goal))}"
        self.goal_info = info
        self.macro_pro_text.value = f"{round(proteine)} g · ~{int(round(proteine * 4))} kcal"
        self.macro_car_text.value = f"{round(carboidrati)} g · ~{int(round(max(0, carboidrati * 4)))} kcal"
        self.macro_gra_text.value = f"{round(grassi)} g · ~{int(round(grassi * 9))} kcal"


def build_diet_view(app) -> ft.Control:
    return DietView(app).build()