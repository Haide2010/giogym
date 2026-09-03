"""
backup_view.py
----------------
Schermata Backup: permette di esportare tutti i dati (scheda + storico)
in un file JSON scaricabile, e di importarli di nuovo (utile per
trasferire i dati su un altro dispositivo o per un semplice backup di
sicurezza).

Vengono offerte due strade, per essere accessibile su qualunque
piattaforma (desktop, mobile, web):
1) Selezione file nativa (FilePicker) per salvare/aprire un file .json
2) Copia/incolla manuale del testo JSON, sempre disponibile come
   alternativa se il file picker non è utilizzabile sul dispositivo.
"""

import flet as ft
import theme
import data_manager as dm


def build_backup_view(app) -> ft.Control:
    """Costruisce la schermata di backup (export/import)."""

    status_text = ft.Text("", size=12)

    # ------------------------------------------------------------------
    # Sezione ESPORTAZIONE
    # ------------------------------------------------------------------
    json_preview_field = ft.TextField(
        label="Contenuto JSON del backup",
        value=dm.export_data_to_json(app.data),
        multiline=True,
        min_lines=6,
        max_lines=10,
        read_only=True,
        border_color=theme.BORDER,
        text_size=11,
    )

    def _mostra_stato(msg: str, colore):
        status_text.value = msg
        status_text.color = colore
        app.page.update()

    def _save_result(e: ft.FilePickerResultEvent):
        if not e.path:
            return
        try:
            path = e.path if e.path.lower().endswith(".json") else e.path + ".json"
            with open(path, "w", encoding="utf-8") as f:
                f.write(dm.export_data_to_json(app.data))
            _mostra_stato(f"Backup salvato in: {path}", theme.SUCCESS)
        except OSError as exc:
            _mostra_stato(f"Errore durante il salvataggio: {exc}", theme.DANGER)

    save_picker = ft.FilePicker(on_result=_save_result)

    def _open_result(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        file_info = e.files[0]
        try:
            with open(file_info.path, "r", encoding="utf-8") as f:
                contenuto = f.read()
            _importa_da_stringa(contenuto)
        except (OSError, UnicodeDecodeError) as exc:
            _mostra_stato(f"Impossibile leggere il file: {exc}", theme.DANGER)

    open_picker = ft.FilePicker(on_result=_open_result)

    def _save_solo_scheda_result(ev: ft.FilePickerResultEvent):
        if not ev.path:
            return
        try:
            path = ev.path if ev.path.lower().endswith(".json") else ev.path + ".json"
            with open(path, "w", encoding="utf-8") as f:
                f.write(dm.export_schema_to_json(app.data))
            _mostra_stato(f"Scheda (senza storico) salvata in: {path}", theme.SUCCESS)
        except OSError as exc:
            _mostra_stato(f"Errore durante il salvataggio: {exc}", theme.DANGER)

    solo_scheda_picker = ft.FilePicker(on_result=_save_solo_scheda_result)

    if app.page and (save_picker not in app.page.overlay):
        app.page.overlay.extend([save_picker, open_picker, solo_scheda_picker])

    def _esporta_su_file(e):
        save_picker.save_file(
            dialog_title="Salva backup GioGym",
            file_name="giogym_backup.json",
            allowed_extensions=["json"],
        )

    def _esporta_solo_scheda(e):
        solo_scheda_picker.save_file(
            dialog_title="Salva scheda GioGym (senza storico)",
            file_name="giogym_scheda.json",
            allowed_extensions=["json"],
        )

    def _copia_negli_appunti(e):
        app.page.set_clipboard(json_preview_field.value)
        _mostra_stato("Contenuto JSON copiato negli appunti.", theme.SUCCESS)

    export_actions = ft.Row(
        [
            ft.ElevatedButton(
                content=ft.Row(
                    [ft.Icon(ft.Icons.DOWNLOAD, color="white"), ft.Text("Salva su file", weight=ft.FontWeight.BOLD)],
                    spacing=8,
                ),
                bgcolor=theme.PRIMARY,
                color="white",
                on_click=_esporta_su_file,
            ),
            ft.OutlinedButton(
                content=ft.Row(
                    [ft.Icon(ft.Icons.COPY, color=theme.TEXT), ft.Text("Copia testo")],
                    spacing=8,
                ),
                on_click=_copia_negli_appunti,
            ),
        ],
        spacing=10,
        wrap=True,
    )

    condividi_scheda_row = ft.Row(
        [
            ft.OutlinedButton(
                content=ft.Row(
                    [ft.Icon(ft.Icons.SHARE_OUTLINED, color=theme.INFO if hasattr(theme, "INFO") else theme.TEXT),
                     ft.Text("Condividi solo la scheda (senza storico)")],
                    spacing=8,
                ),
                tooltip="Esporta solo il tuo programma di allenamento, senza i dati personali dello storico",
                on_click=_esporta_solo_scheda,
            ),
        ],
        spacing=10,
        wrap=True,
    )

    # ------------------------------------------------------------------
    # Sezione IMPORTAZIONE
    # ------------------------------------------------------------------
    import_text_field = ft.TextField(
        label="Incolla qui il JSON del backup da importare",
        multiline=True,
        min_lines=5,
        max_lines=8,
        border_color=theme.BORDER,
        focused_border_color=theme.PRIMARY,
        text_size=11,
    )

    def _importa_da_stringa(contenuto: str):
        try:
            importato = dm.import_data_from_json(contenuto)
        except dm.ImportError_ as exc:
            _mostra_stato(str(exc), theme.DANGER)
            return
        _apri_dialogo_conferma(importato)

    def _apri_dialogo_conferma(importato: dict):
        def _conferma_sovrascrivi(ev):
            app.page.close(dlg)
            app.data["scheda"] = importato["scheda"]
            app.data["storico"] = importato["storico"]
            app.save()
            _mostra_stato("Dati importati (sostituiti) con successo. Torna alla Home per vederli.", theme.SUCCESS)

        def _conferma_unisci(ev):
            app.page.close(dlg)
            app.data.update(dm.merge_imported_data(app.data, importato))
            app.save()
            _mostra_stato("Dati uniti allo storico esistente con successo.", theme.SUCCESS)

        n_giorni = len(importato["scheda"].get("giorni", []))
        n_sessioni = len(importato["storico"])

        dlg = ft.AlertDialog(
            modal=True,
            bgcolor=theme.BG_CARD,
            title=ft.Text("Importare i dati?", color=theme.TEXT),
            content=ft.Text(
                f"Il backup contiene {n_giorni} giorni di scheda e {n_sessioni} sessioni "
                "nello storico.\n\nVuoi SOSTITUIRE i dati attuali oppure UNIRLI (lo "
                "storico viene combinato, la scheda viene sostituita)?",
                color=theme.TEXT_MUTED,
                size=13,
            ),
            actions=[
                ft.TextButton("Annulla", on_click=lambda ev: app.page.close(dlg)),
                ft.TextButton("Unisci", on_click=_conferma_unisci),
                ft.TextButton("Sostituisci", on_click=_conferma_sovrascrivi, style=ft.ButtonStyle(color=theme.DANGER)),
            ],
        )
        app.page.open(dlg)

    def _importa_da_testo(e):
        if not import_text_field.value or not import_text_field.value.strip():
            _mostra_stato("Incolla prima il contenuto JSON del backup.", theme.DANGER)
            return
        _importa_da_stringa(import_text_field.value)

    def _importa_da_file(e):
        open_picker.pick_files(
            dialog_title="Seleziona il file di backup GioGym",
            allow_multiple=False,
            allowed_extensions=["json"],
        )

    import_actions = ft.Row(
        [
            ft.ElevatedButton(
                content=ft.Row(
                    [ft.Icon(ft.Icons.UPLOAD_FILE, color="white"), ft.Text("Importa da file", weight=ft.FontWeight.BOLD)],
                    spacing=8,
                ),
                bgcolor=theme.BG_CARD_LIGHT,
                color=theme.TEXT,
                on_click=_importa_da_file,
            ),
            ft.OutlinedButton(
                content=ft.Row(
                    [ft.Icon(ft.Icons.CONTENT_PASTE_GO, color=theme.TEXT), ft.Text("Importa da testo incollato")],
                    spacing=8,
                ),
                on_click=_importa_da_testo,
            ),
        ],
        spacing=10,
        wrap=True,
    )

    header = ft.Row(
        [
            ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=theme.TEXT, on_click=lambda e: app.show_home()),
            ft.Row(
                [
                    ft.Icon(ft.Icons.BACKUP, color=theme.PRIMARY, size=24),
                    ft.Text("Backup dati", size=theme.TITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
                ],
                spacing=8,
            ),
        ],
    )

    content_list = ft.ListView(
        [
            header,
            ft.Divider(color=theme.BORDER, height=15),
            ft.Text("Esporta i tuoi dati", size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
            ft.Text(
                "Salva scheda e storico in un file JSON: utile come backup di "
                "sicurezza o per trasferire i dati su un altro dispositivo.",
                size=12,
                color=theme.TEXT_MUTED,
            ),
            export_actions,
            json_preview_field,
            ft.Divider(color=theme.BORDER, height=12),
            ft.Text("Condividi solo il programma", size=13, weight=ft.FontWeight.BOLD, color=theme.TEXT),
            ft.Text(
                "Vuoi prestare la tua scheda a un amico senza mostrargli il tuo "
                "storico personale? Esporta solo la parte 'scheda'.",
                size=11,
                color=theme.TEXT_MUTED,
            ),
            condividi_scheda_row,
            ft.Divider(color=theme.BORDER, height=20),
            ft.Text("Importa dati da backup", size=theme.SUBTITLE_SIZE, weight=ft.FontWeight.BOLD, color=theme.TEXT),
            ft.Text(
                "Carica un file di backup esportato in precedenza, oppure incolla "
                "direttamente il testo JSON.",
                size=12,
                color=theme.TEXT_MUTED,
            ),
            import_actions,
            import_text_field,
            status_text,
        ],
        expand=True,
        spacing=10,
    )

    return ft.Column([content_list], expand=True)
