"""
history_detail_view.py
-----------------------
Mostra i dettagli completi di una sessione di allenamento passata,
permette di eliminarla o di riprenderla ricaricando esattamente lo stato
di completamento, pesi e ripetizioni nella schermata di allenamento attivo.
"""

import flet as ft
import theme


def build_history_detail_view(app, sessione: dict) -> ft.Control:
    """Costruisce la schermata del dettaglio di un allenamento completato con ripristino esatto dello stato."""
    data = sessione.get("data", "-")
    giorno_nome = sessione.get("giorno_nome", "Allenamento")
    esercizi = sessione.get("esercizi", [])

    def conferma_eliminazione(e):
        """Apre un dialogo di conferma prima di rimuovere la sessione."""
        def esegui_eliminazione(ev):
            if sessione in app.data.get("storico", []):
                app.data["storico"].remove(sessione)
                app.save()
            app.page.close(dlg_conferma)
            app.show_home()

        dlg_conferma = ft.AlertDialog(
            modal=True,
            bgcolor=theme.CARD_BG if hasattr(theme, "CARD_BG") else "#1a1a1a",
            title=ft.Text("Conferma eliminazione", color=theme.TEXT, weight=ft.FontWeight.BOLD),
            content=ft.Text(
                f"Vuoi davvero eliminare l'allenamento di {giorno_nome} ({data})?\nL'azione è irreversibile.",
                color=theme.TEXT_MUTED,
                size=13
            ),
            actions=[
                ft.TextButton("Annulla", on_click=lambda ev: app.page.close(dlg_conferma)),
                ft.ElevatedButton(
                    "Elimina",
                    bgcolor=ft.Colors.RED_400,
                    color="white",
                    on_click=esegui_eliminazione
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        app.page.open(dlg_conferma)

    def riprendi_allenamento(e):
        """Riprende l'allenamento ricaricando lo stato esatto (pesi, reps,
        spunte e note) della sessione, tramite show_training_edit."""
        if hasattr(app, "show_training_edit"):
            app.show_training_edit(sessione)
        else:
            app.show_home()

    def modifica_allenamento(e):
        """Apre l'allenamento in modalità modifica, con tutto lo stato
        già selezionato (pesi, reps, spunte, note), per poi sovrascriverlo."""
        if hasattr(app, "show_training_edit"):
            app.show_training_edit(sessione)
        else:
            app.show_home()

    header = ft.Row(
        [
            ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color=theme.TEXT,
                        on_click=lambda e: app.show_home(),
                    ),
                    ft.Text(
                        f"{giorno_nome}",
                        size=theme.TITLE_SIZE,
                        weight=ft.FontWeight.BOLD,
                        color=theme.TEXT,
                    ),
                ],
                spacing=5,
            ),
            ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.EDIT_OUTLINED,
                        icon_color=theme.INFO,
                        tooltip="Modifica allenamento",
                        on_click=modifica_allenamento,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.PLAY_ARROW_ROUNDED,
                        icon_color=theme.PRIMARY,
                        tooltip="Riprendi allenamento con spunte e carichi",
                        on_click=riprendi_allenamento,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=ft.Colors.RED_400,
                        tooltip="Elimina allenamento",
                        on_click=conferma_eliminazione,
                    ),
                ],
                spacing=0,
            )
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    sub_header = ft.Text(
        f"Completato il: {data}",
        size=theme.BODY_SIZE,
        color=theme.TEXT_MUTED,
    )

    esercizio_controls = []
    for ex in esercizi:
        ex_nome = ex.get("nome", "Esercizio")
        serie_svolte = ex.get("serie_svolte", [])

        serie_rows = []
        for i, serie in enumerate(serie_svolte, 1):
            peso = serie.get("peso", 0.0)
            reps = serie.get("reps", 0)
            completata = serie.get("completata", False)

            status_icon = (
                ft.Icon(ft.Icons.CHECK_CIRCLE, color=theme.SUCCESS, size=18)
                if completata
                else ft.Icon(ft.Icons.CANCEL, color=ft.Colors.RED_400, size=18)
            )

            serie_rows.append(
                ft.Row(
                    [
                        ft.Text(f"Serie {i}", size=12, color=theme.TEXT_MUTED, width=60),
                        ft.Text(f"{peso} kg", size=12, weight=ft.FontWeight.BOLD, color=theme.TEXT, width=60),
                        ft.Text(f"{reps} reps", size=12, color=theme.TEXT, width=60),
                        status_icon,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )

        ex_card = theme.card_container(
            ft.Column(
                [
                    ft.Text(ex_nome, size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                    ft.Divider(color=theme.BORDER, height=10),
                    ft.Column(serie_rows, spacing=6),
                ],
                spacing=4,
            ),
            margin=ft.margin.only(bottom=10),
        )
        esercizio_controls.append(ex_card)

    if not esercizio_controls:
        esercizio_controls.append(
            ft.Text("Nessun esercizio registrato per questa sessione.", color=theme.TEXT_MUTED)
        )

    # --- Sezione extra: foto, valutazione a manubri, nota generale ---
    extra_controls = []

    foto_path = sessione.get("foto", "")
    if foto_path:
        try:
            extra_controls.append(
                ft.Container(
                    content=ft.Image(src=foto_path, fit=ft.ImageFit.COVER, height=200, border_radius=theme.RADIUS),
                    margin=ft.margin.only(bottom=10),
                )
            )
        except Exception:
            pass

    valutazione = sessione.get("valutazione", 0) or 0
    if valutazione:
        manubri = ft.Row(
            [
                ft.Icon(
                    ft.Icons.FITNESS_CENTER,
                    color=theme.PRIMARY if i <= int(valutazione) else theme.TEXT_MUTED,
                    size=22,
                )
                for i in range(1, 6)
            ],
            spacing=2,
        )
        extra_controls.append(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.STAR, color=theme.GOLD, size=18),
                                ft.Text("Valutazione:", size=13, color=theme.TEXT, weight=ft.FontWeight.BOLD),
                            ],
                            spacing=6,
                        ),
                        manubri,
                        ft.Text(f"{int(valutazione)}/5", size=12, color=theme.TEXT_MUTED),
                    ],
                    spacing=10,
                ),
                margin=ft.margin.only(bottom=10),
            )
        )

    nota_generale = sessione.get("note_generali", "")
    if nota_generale:
        extra_controls.append(
            theme.card_container(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.NOTES, color=theme.INFO, size=18),
                                ft.Text("Nota della sessione", size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                            ],
                            spacing=6,
                        ),
                        ft.Text(nota_generale, size=13, color=theme.TEXT),
                    ],
                    spacing=8,
                ),
                margin=ft.margin.only(bottom=10),
            )
        )

    content_list = ft.ListView(
        controls=extra_controls + esercizio_controls,
        expand=True,
        spacing=0,
    )

    return ft.Column(
        [
            header,
            sub_header,
            ft.Divider(color=theme.BORDER, height=20),
            ft.Container(content=content_list, expand=True),
        ],
        expand=True,
        spacing=10,
    )