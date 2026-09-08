"""
onboarding_view.py
------------------
Prima accensione dell'app: un brece benvenuto a passi che raccoglie i dati
base del profilo (nome, età, sesso, peso, altezza, obiettivo e frequenza
settimanale). Viene mostrato automaticamente finché il profilo non è stato
compilato (basta che manchi il nome) e i dati salvati finiscono proprio
nella sezione "profilo" usata dal resto dell'app.
"""

import flet as ft
import theme
import data_manager as dm

OBIETTIVI = [
    ("massa", "Massa muscolare"),
    ("definizione", "Definizione / dimagrimento"),
    ("forza", "Forza"),
    ("mantenimento", "Mantenimento"),
    ("salute", "Salute / benessere"),
]


def build_onboarding_view(app) -> ft.Control:
    profilo = app.data.setdefault("profilo", {})

    nome = ft.TextField(label="Il tuo nome", dense=True,
                        value=str(profilo.get("nome", "") or ""), autofocus=True)
    eta = ft.TextField(label="La tua età (anni)", dense=True,
                       keyboard_type=ft.KeyboardType.NUMBER,
                       value=str(profilo.get("eta", "") or ""))
    sesso = ft.Dropdown(label="Sesso",
                        options=[ft.dropdown.Option("M", "Maschio"),
                                 ft.dropdown.Option("F", "Femmina")],
                        value=str(profilo.get("sesso", "") or ""))
    peso = ft.TextField(label="Peso attuale (kg)", dense=True,
                        keyboard_type=ft.KeyboardType.NUMBER,
                        value=str(profilo.get("peso_attuale_kg", "") or ""))
    altezza = ft.TextField(label="Altezza (cm)", dense=True,
                           keyboard_type=ft.KeyboardType.NUMBER,
                           value=str(profilo.get("altezza_cm", "") or ""))
    obiettivo = ft.Dropdown(label="Qual è il tuo obiettivo?",
                            options=[ft.dropdown.Option(k, v) for k, v in OBIETTIVI],
                            value=str(profilo.get("obiettivo", "") or ""))
    peso_obiettivo = ft.TextField(label="Peso obiettivo (kg) - facoltativo", dense=True,
                                  keyboard_type=ft.KeyboardType.NUMBER,
                                  value=str(profilo.get("peso_obiettivo_kg", "") or ""))
    freq = ft.Dropdown(
        label="Quante volte vuoi allenarti a settimana?",
        options=[ft.dropdown.Option(str(i), f"{i} volta{'e' if i > 1 else ''}/settimana") for i in range(1, 8)],
        value=str(profilo.get("frequenza_settimanale", "") or "") or "3",
    )

    title = ft.Text("GioGym", size=30, weight=ft.FontWeight.BOLD, color=theme.TEXT)
    subtitle = ft.Text("Conosciamoci: rispondi a poche domande e iniziamo!",
                       size=13, color=theme.TEXT_MUTED)

    body = ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    error_text = ft.Text("", size=12, color=theme.DANGER)

    def _valido() -> bool:
        if step_meta["key"] == "nome" and not nome.value.strip():
            error_text.value = "Scrivi il tuo nome per iniziare."
            app.page.update()
            return False
        if step_meta["key"] == "eta":
            for f in (eta,):
                if f.value.strip():
                    try:
                        float(f.value)
                    except ValueError:
                        error_text.value = f"Valore non valido: {f.label}."
                        app.page.update()
                        return False
        if step_meta["key"] == "fisico":
            for f in (peso, altezza):
                if f.value.strip():
                    try:
                        float(f.value)
                    except ValueError:
                        error_text.value = f"Valore non valido: {f.label}."
                        app.page.update()
                        return False
        error_text.value = ""
        return True

    def _avanti(e):
        if step_meta["cur"] < len(STEPS) - 1 and _valido():
            step_meta["cur"] += 1
            _mostra()

    def _indietro(e):
        if step_meta["cur"] > 0:
            step_meta["cur"] -= 1
            _mostra()

    def _inizia(e):
        if not _valido():
            return
        profilo["nome"] = nome.value.strip()
        try:
            profilo["eta"] = int(float(eta.value)) if eta.value.strip() else profilo.get("eta", 25)
        except (ValueError, TypeError):
            profilo["eta"] = 25
        profilo["sesso"] = sesso.value or "M"
        try:
            profilo["peso_attuale_kg"] = float(peso.value) if peso.value.strip() else profilo.get("peso_attuale_kg", 68.5)
        except (ValueError, TypeError):
            profilo["peso_attuale_kg"] = 68.5
        try:
            profilo["altezza_cm"] = float(altezza.value) if altezza.value.strip() else profilo.get("altezza_cm", 175)
        except (ValueError, TypeError):
            profilo["altezza_cm"] = 175
        profilo["obiettivo"] = obiettivo.value or "massa"
        try:
            profilo["peso_obiettivo_kg"] = float(peso_obiettivo.value) if peso_obiettivo.value.strip() else profilo.get("peso_obiettivo_kg", 0.0)
        except (ValueError, TypeError):
            profilo["peso_obiettivo_kg"] = 0.0
        profilo["frequenza_settimanale"] = int(freq.value) if freq.value.strip() else 3
        app.save()
        app.show_home()

    STEPS = [
        ("nome", "Ciao! Come ti chiami?",
         "Useremo il tuo nome per salutarti nella schermata principale.", [nome]),
        ("eta", "Quanti anni hai?",
         "L'età serve per stimare i massimali e i consumi.", [eta, sesso]),
        ("fisico", "Partiamo dalla base: peso e altezza.",
         "Potrai sempre modificarli dal Profilo.", [peso, altezza]),
        ("obiettivo", "Qual è il tuo obiettivo?",
         "Imposteremo record e grafici di conseguenza.", [obiettivo, peso_obiettivo]),
        ("freq", "Quanto spesso vuoi allenarti?",
         "È il numero di allenamenti 'target' a settimana delle tue streak.", [freq]),
    ]
    step_meta = {"cur": 0, "key": STEPS[0][0]}

    indicator = ft.Row(spacing=4)

    def _mostra():
        step_meta["key"], titolo, desc, campi = STEPS[step_meta["cur"]]
        body.controls = [
            ft.Text(titolo, size=18, weight=ft.FontWeight.BOLD, color=theme.TEXT,
                    text_align=ft.TextAlign.CENTER),
            ft.Text(desc, size=12, color=theme.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
            ft.Container(height=6),
            *campi,
        ]
        indicator.controls = [
            ft.Container(width=18 if i == step_meta["cur"] else 8, height=8,
                         border_radius=4,
                         bgcolor=theme.PRIMARY if i == step_meta["cur"] else theme.BG_CARD_LIGHT)
            for i in range(len(STEPS))
        ]
        avanti.visible = step_meta["cur"] < len(STEPS) - 1
        indietro.visible = step_meta["cur"] > 0
        inizia.visible = step_meta["cur"] == len(STEPS) - 1
        app.page.update()

    avanti = theme.primary_button("Avanti", _avanti, icon=ft.Icons.ARROW_FORWARD_IOS_ROUNDED)
    indietro = ft.TextButton("Indietro", icon=ft.Icons.ARROW_BACK_IOS_ROUNDED, on_click=_indietro)
    inizia = theme.primary_button("Inizia!", _inizia, icon=ft.Icons.CHECK_CIRCLE)

    def _skippa(e):
        # Consente di proseguire senza compilare tutto (i default restano sensati).
        profilo["nome"] = nome.value.strip() or "Atleta"
        app.save()
        app.show_home()

    skippa = ft.TextButton("Salta per ora", on_click=_skippa)

    step_meta["cur"] = 0
    _mostra()

    return ft.Container(
        content=ft.Column(
            [
                ft.Row([ft.Icon(ft.Icons.FITNESS_CENTER, color=theme.PRIMARY, size=30),
                        title], spacing=8),
                subtitle,
                ft.Divider(color=theme.BORDER, height=16),
                body,
                error_text,
                ft.Divider(color=theme.BORDER, height=10),
                indicator,
                ft.Row([indietro, avanti, inizia], spacing=8,
                       alignment=ft.MainAxisAlignment.CENTER),
                skippa,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
            expand=True,
        ),
        padding=20,
        alignment=ft.alignment.center,
    )