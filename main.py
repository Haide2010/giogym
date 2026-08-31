"""
main.py
-------
GioGym - Entry point dell'applicazione.

Avvio in sviluppo (finestra desktop / hot reload):
    flet run main.py

Avvio in sviluppo (nel browser):
    flet run --web main.py

Compilazione APK Android:
    flet build apk
(vedi README.md per la procedura completa passo-passo)
"""

import flet as ft

import theme
import data_manager as dm
from views.home_view import build_home_view
from views.selection_view import build_selection_view
from views.schema_view import SchemaEditorView
from views.training_view import TrainingView


class GioGymApp:
    """Controller centrale dell'app: tiene i dati in memoria e gestisce
    la navigazione tra le schermate sostituendo il contenuto della Page.
    Un approccio a singolo container (invece delle ft.View/routing) è
    stato scelto per semplicità e per mantenere facilmente lo stato
    condiviso (es. i dati caricati una sola volta all'avvio).
    """

    def __init__(self, page: ft.Page):
        self.page = page
        self.data = dm.load_data()

        self._setup_page()
        self.show_home()

    # ------------------------------------------------------------------
    # Setup generale della pagina (tema scuro, stile "palestra")
    # ------------------------------------------------------------------
    def _setup_page(self):
        self.page.title = "GioGym"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.theme = theme.page_theme()
        self.page.bgcolor = theme.BG
        self.page.padding = 0
        self.page.window_width = 420
        self.page.window_height = 860
        self.page.scroll = ft.ScrollMode.HIDDEN

    # ------------------------------------------------------------------
    # Persistenza
    # ------------------------------------------------------------------
    def save(self):
        dm.save_data(self.data)

    # ------------------------------------------------------------------
    # Navigazione: ogni show_* sostituisce il contenuto della pagina
    # ------------------------------------------------------------------
def _set_content(self, control: ft.Control):
        self.page.controls.clear()
        self.page.controls.append(
            ft.Container(
                content=control,
                padding=ft.padding.only(top=25, left=theme.PADDING, right=theme.PADDING, bottom=theme.PADDING),
                expand=True,
                bgcolor=theme.BG,
            )
        )
        self.page.update()

    def show_home(self):
        # Ricarico i dati da disco per riflettere eventuali modifiche
        # (es. dopo aver salvato una scheda o un allenamento).
        self.data = dm.load_data()
        self._set_content(build_home_view(self))

    def show_schema_editor(self):
        editor = SchemaEditorView(self)
        self._set_content(editor.build())

    def show_selection(self):
        self._set_content(build_selection_view(self))

    def show_training(self, giorno_index: int):
        training = TrainingView(self, giorno_index)
        self._set_content(training.build())


def main(page: ft.Page):
    GioGymApp(page)


if __name__ == "__main__":
    ft.app(target=main)
