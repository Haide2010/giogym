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
        """Crea una copia esatta della sessione passata forzando lo stato completato su ogni serie."""
        esercizi_ripristinati = []
        for ex in esercizi:
            serie_ripristinate = []
            for s in ex.get("serie_svolte", []):
                # Forziamo explicitamente 'completata' a True se salvata come True o se comunque aveva dei dati validi
                is_completed = s.get("completata", True)
                serie_ripristinate.append({
                    "peso": s.get("peso", 0.0),
                    "reps": s.get("reps", 0),
                    "completata": True if is_completed else False
                })
            esercizi_ripristinati.append({
                "nome": ex.get("nome"),
                "serie_svolte": serie_ripristinate
            })

        app.allenamento_attivo = {
            "giorno_nome": f"Ripresa: {giorno_nome}",
            "esercizi": esercizi_ripristinati
        }

        if hasattr(app, "show_training"):
            app.show_training(app.allenamento_attivo)
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

    content_list = ft.ListView(
        controls=esercizio_controls,
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