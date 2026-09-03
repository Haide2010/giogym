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
from views.exercise_history_view import build_exercise_history_view


class GioGymApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "GioGym"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 16

        # Caricamento dati
        self.data = data_manager.load_data()

        # Ripristino del colore tema salvato in precedenza (se esiste) e
        # applicazione coerente sia alla palette (theme.PRIMARY) sia al
        # tema Material della pagina (page.theme), così l'intera UI
        # (non solo i singoli controlli) riflette il colore scelto.
        primary_color = self.data.get("primary_color")
        self.apply_theme(primary_color or theme.PRIMARY)

        # Schermata iniziale
        self.show_home()

    def apply_theme(self, color: str):
        """Applica un colore primario in modo coerente a tutta l'app:
        aggiorna la costante usata dalle viste (theme.PRIMARY) e
        rigenera il tema Material della pagina (color_scheme_seed)."""
        theme.PRIMARY = color
        self.page.theme = theme.page_theme(color)

    def refresh_theme_and_reload(self):
        """Da chiamare dopo un cambio colore nelle Impostazioni: applica
        il nuovo tema e ricostruisce la Home per mostrare subito il
        risultato ovunque."""
        self.apply_theme(self.data.get("primary_color", theme.PRIMARY))
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

    def show_history_detail(self, sessione: dict):
        view = build_history_detail_view(self, sessione)
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

    def show_exercise_history(self, nome_esercizio: str, origine: str = "pr"):
        """Schermata di cronologia dettagliata (riga per riga) per un
        singolo esercizio, raggiungibile da PR e Grafici."""
        view = build_exercise_history_view(self, nome_esercizio, origine)
        self._set_content(view)

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