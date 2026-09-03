"""
history_detail_view.py
-----------------------
Mostra i dettagli completi di una sessione di allenamento passata
e permette di eliminarla dallo storico.
"""

import flet as ft
import theme


def build_history_detail_view(app, sessione: dict) -> ft.Control:
    """Costruisce la schermata del dettaglio di un allenamento completato."""
    data = sessione.get("data", "-")
    giorno_nome = sessione.get("giorno_nome", "Allenamento")
    esercizi = sessione.get("esercizi", [])

    def elimina_allenamento(e):
        """Rimuove la sessione corrente dallo storico e salva i dati."""
        if sessione in app.data.get("storico", []):
            app.data["storico"].remove(sessione)
            app.save()
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
            # Pulsante per eliminare questo allenamento specifico
            ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                icon_color=ft.Colors.RED_400,
                tooltip="Elimina allenamento",
                on_click=elimina_allenamento,
            ),
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