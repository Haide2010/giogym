"""
main.py
-------
Punto di ingresso principale dell'applicazione GioGym.
Gestisce lo stato globale e la navigazione tra le viste.
"""

import flet as ft
import data_manager
import theme

# Import delle viste
from views.home_view import build_home_view
from views.selection_view import build_selection_view
from views.schema_view import build_schema_view
from views.training_view import build_training_view
from views.history_detail_view import build_history_detail_view
from views.pr_view import build_pr_view
from views.progress_view import build_progress_view
from views.backup_view import build_backup_view
from views.settings_view import build_settings_view
from views.workout_summary_view import build_workout_summary_view


class GioGymApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "GioGym"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.theme = theme.page_theme() if hasattr(theme, "page_theme") else None
        self.page.padding = 16

        # Caricamento dati
        self.data = data_manager.load_data()

        # Ripristino del colore tema salvato in precedenza (se esiste)
        primary_color = self.data.get("primary_color")
        if primary_color:
            theme.PRIMARY = primary_color

        # Schermata iniziale
        self.show_home()

    def _set_content(self, view_control: ft.Control):
        """Pulisce la pagina e imposta la nuova vista."""
        self.page.clean()
        self.page.add(view_control)
        self.page.update()

    def show_home(self):
        view = build_home_view(self)
        self._set_content(view)

    def show_selection(self):
        view = build_selection_view(self)
        self._set_content(view)

    def show_schema_editor(self):
        view = build_schema_view(self)
        self._set_content(view)

    def show_training(self, giorno_selezionato: dict):
        view = build_training_view(self, giorno_selezionato)
        self._set_content(view)

    def show_training_edit(self, sessione: dict):
        """Apre la schermata di allenamento in modalità MODIFICA per
        sovrascrivere una sessione passata, ricaricandone lo stato."""
        storico = self.data.get("storico", [])
        edit_index = None
        for idx, s in enumerate(storico):
            if s is sessione or (s.get("data") == sessione.get("data")
                                 and s.get("giorno_nome") == sessione.get("giorno_nome")):
                edit_index = idx
                break
        view = build_training_view(self, None, edit_session=sessione, edit_index=edit_index)
        self._set_content(view)

    def show_history_detail(self, sessione: dict):
        view = build_history_detail_view(self, sessione)
        self._set_content(view)

    def show_workout_summary(self, sessione: dict, nuovi_pr: list, modify_index: int = None):
        """Riepilogo a fine allenamento (foto, manubri, note) prima di salvare."""
        view = build_workout_summary_view(self, sessione, nuovi_pr, modify_index=modify_index)
        self._set_content(view)

    def show_pr(self):
        """Schermata Record Personali (PR)."""
        view = build_pr_view(self)
        self._set_content(view)

    def show_progress(self):
        """Schermata Grafici dei Progressi."""
        view = build_progress_view(self)
        self._set_content(view)

    def show_backup(self):
        """Schermata Backup (export/import dati)."""
        view = build_backup_view(self)
        self._set_content(view)

    def show_settings(self):
        """Schermata Impostazioni."""
        view = build_settings_view(self)
        self._set_content(view)

    def show_plates(self):
        """Schermata Calcolatore Piastre."""
        try:
            from views.plates_view import build_plates_view
            view = build_plates_view(self)
            self._set_content(view)
        except ImportError:
            # Fallback temporaneo se il file plates_view.py non è stato ancora creato
            self.page.snack_bar = ft.SnackBar(ft.Text("Sezione Calcolatore Piastre in arrivo!"))
            self.page.snack_bar.open = True
            self.page.update()

    def save(self):
        """Salva i dati tramite il data_manager."""
        if hasattr(data_manager, "save_data"):
            data_manager.save_data(self.data)

    def salva_dati(self):
        """Alias di compatibilità per il salvataggio."""
        self.save()


def main(page: ft.Page):
    GioGymApp(page)


if __name__ == "__main__":
    ft.app(target=main)