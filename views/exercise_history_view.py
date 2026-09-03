"""
exercise_history_view.py
--------------------------
Mostra la cronologia dettagliata (riga per riga) di un singolo
esercizio: ogni sessione in cui è stato svolto, con data, peso/reps di
ogni serie e se è stata completata. Raggiungibile da PR e Grafici,
utile quando il trend del grafico non basta e servono i numeri esatti.
"""

import flet as ft
import theme


def build_exercise_history_view(app, nome_esercizio: str, origine: str = "pr") -> ft.Control:
    """Costruisce la schermata di cronologia per l'esercizio indicato.
    origine determina dove torna il pulsante "indietro" ('pr' o 'progress')."""
    storico = app.data.get("storico", [])
    torna_indietro = app.show_progress if origine == "progress" else app.show_pr

    # Raccoglie tutte le occorrenze dell'esercizio, dalla più recente
    sessioni_esercizio = []
    for sessione in reversed(storico):
        for ex in sessione.get("esercizi", []):
            if ex.get("nome", "").strip() == nome_esercizio.strip():
                sessioni_esercizio.append((sessione.get("data", "-"), ex))

    def _sessione_card(data: str, ex: dict) -> ft.Control:
        note = ex.get("note", "").strip()
        righe = []
        for i, serie in enumerate(ex.get("serie_svolte", []), 1):
            peso = serie.get("peso", 0)
            reps = serie.get("reps", 0)
            completata = serie.get("completata", False)
            icona = ft.Icon(
                ft.Icons.CHECK_CIRCLE if completata else ft.Icons.CANCEL,
                size=15,
                color=theme.SUCCESS if completata else theme.DANGER,
            )
            righe.append(
                ft.Row(
                    [
                        ft.Text(f"Serie {i}", size=12, color=theme.TEXT_MUTED, width=55),
                        ft.Text(f"{peso} kg", size=13, weight=ft.FontWeight.BOLD, color=theme.TEXT, width=60),
                        ft.Text(f"{reps} reps", size=12, color=theme.TEXT, width=60),
                        icona,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                )
            )

        contenuto = [
            ft.Row(
                [
                    ft.Text(data, size=14, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                ],
            ),
            ft.Divider(color=theme.BORDER, height=8),
            ft.Column(righe, spacing=4),
        ]
        if note:
            contenuto.append(
                ft.Text(f'📝 {note}', size=11, color=theme.TEXT_MUTED, italic=True)
            )

        return theme.card_container(
            ft.Column(contenuto, spacing=4),
            margin=ft.margin.only(bottom=8),
        )

    header = ft.Row(
        [
            ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=theme.TEXT, on_click=lambda e: torna_indietro()),
            ft.Row(
                [
                    ft.Icon(ft.Icons.HISTORY, color=theme.INFO if hasattr(theme, "INFO") else theme.PRIMARY, size=22),
                    ft.Text(nome_esercizio, size=theme.TITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                ],
                spacing=8,
            ),
        ],
    )

    if not sessioni_esercizio:
        body = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.HISTORY_TOGGLE_OFF, size=36, color=theme.TEXT_MUTED),
                    ft.Text("Nessuna sessione registrata per questo esercizio.", color=theme.TEXT_MUTED, size=13),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            alignment=ft.alignment.center,
            padding=30,
        )
        content_list = ft.ListView([header, ft.Divider(color=theme.BORDER, height=15), body], expand=True, spacing=10)
    else:
        cards = [_sessione_card(data, ex) for data, ex in sessioni_esercizio]
        content_list = ft.ListView(
            [
                header,
                ft.Divider(color=theme.BORDER, height=15),
                ft.Text(f"{len(sessioni_esercizio)} sessioni registrate, dalla più recente", size=12, color=theme.TEXT_MUTED),
                *cards,
            ],
            expand=True,
            spacing=10,
        )

    return ft.Column([content_list], expand=True)
