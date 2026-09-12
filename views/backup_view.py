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

import os

import flet as ft
import theme
import data_manager as dm


def build_backup_view(app) -> ft.Control:
    """Costruisce la schermata di backup (export/import)."""

    status_text = ft.Text("", size=12)

    # ------------------------------------------------------------------
    # Sezione ESPORTAZIONE
    # ------------------------------------------------------------------
    include_fotos_cb = ft.Checkbox(
        label="Includi le foto degli allenamenti (il file diventa molto grande)",
        value=False,
        on_change=lambda e: _ricarica_anteprima(),
    )

    json_preview_field = ft.TextField(
        label="Anteprima struttura del backup",
        value="",
        multiline=True,
        min_lines=4,
        max_lines=7,
        read_only=True,
        border_color=theme.BORDER,
        text_size=11,
    )

    def _json_backup() -> str:
        return dm.export_data_to_json(app.data, include_fotos=bool(include_fotos_cb.value))

    def _ricarica_anteprima():
        contenuto = _json_backup()
        if len(contenuto) > 3500:
            json_preview_field.value = contenuto[:3500] + "\n… (anteprima troncata al limite, il backup completo è più grande)"
        else:
            json_preview_field.value = contenuto
        app.page.update()

    _ricarica_anteprima()

    def _mostra_stato(msg: str, colore):
        status_text.value = msg
        status_text.color = colore
        app.page.update()

    def _save_result(e: ft.FilePickerResultEvent):
        if e.error:
            _mostra_stato(
                "Il dialogo di salvataggio non è disponibile su questo dispositivo: "
                "usa 'Salva nella cartella' o 'Copia testo'.",
                theme.DANGER,
            )
            return
        if not e.path:
            _mostra_stato("Salvataggio annullato.", theme.TEXT_MUTED)
            return
        try:
            path = e.path if e.path.lower().endswith(".json") else e.path + ".json"
            with open(path, "w", encoding="utf-8") as f:
                f.write(_json_backup())
            _mostra_stato(f"Backup salvato in: {path}", theme.SUCCESS)
        except OSError as exc:
            _mostra_stato(
                f"Errore durante il salvataggio: {exc}. Usa 'Salva nella cartella' o 'Copia testo'.",
                theme.DANGER,
            )

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

    if app.page and (save_picker not in app.page.overlay):
        app.page.overlay.extend([save_picker, open_picker])

    def _esporta_su_file(e):
        save_picker.save_file(
            dialog_title="Salva backup GioGym",
            file_name="giogym_backup.json",
            allowed_extensions=["json"],
        )

    def _salva_nella_cartella(e):
        """Salva senza chiedere il percorso: scrive nella cartella dati
        dell'app e mostra/copia il percorso. Funziona ovunque, anche dove
        il dialogo nativo non è disponibile."""
        try:
            directory = os.path.dirname(dm.get_data_path())
            path = dm.export_backup_file(
                app.data, directory, include_fotos=bool(include_fotos_cb.value))
            app.page.set_clipboard(path)
            _mostra_stato(f"Backup salvato in:\n{path}\n(Percorso copiato negli appunti)", theme.SUCCESS)
        except OSError as exc:
            _mostra_stato(f"Errore durante il salvataggio: {exc}", theme.DANGER)

    def _copia_negli_appunti(e):
        app.page.set_clipboard(_json_backup())
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
            ft.OutlinedButton(
                content=ft.Row(
                    [ft.Icon(ft.Icons.FOLDER_OPEN, color=theme.TEXT), ft.Text("Salva nella cartella")],
                    spacing=8,
                ),
                on_click=_salva_nella_cartella,
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
            if importato.get("profilo"):
                app.data["profilo"] = importato["profilo"]
            if importato.get("peso_corporeo"):
                app.data["peso_corporeo"] = importato["peso_corporeo"]
            if importato.get("infortuni"):
                app.data["infortuni"] = importato["infortuni"]
            if importato.get("primary_color"):
                app.data["primary_color"] = importato["primary_color"]
            app.save()
            _mostra_stato("Dati importati (sostituiti) con successo. Torna alla Home per vederli.", theme.SUCCESS)

        def _conferma_unisci(ev):
            app.page.close(dlg)
            app.data.update(dm.merge_imported_data(app.data, importato))
            app.save()
            _mostra_stato("Dati uniti allo storico esistente con successo.", theme.SUCCESS)

        n_giorni = len(importato["scheda"].get("giorni", []))
        n_sessioni = len(importato["storico"])
        dettagli_extra = []
        if importato.get("profilo") and importato["profilo"].get("nome"):
            dettagli_extra.append("profilo")
        if importato.get("peso_corporeo"):
            dettagli_extra.append(f'{len(importato["peso_corporeo"])} registrazioni peso')
        if importato.get("infortuni"):
            dettagli_extra.append(f'{len(importato["infortuni"])} infortuni')
        if importato.get("primary_color"):
            dettagli_extra.append("colore tema")
        extra_str = f" · " + ", ".join(dettagli_extra) if dettagli_extra else ""
        n_foto = sum(1 for s in importato["storico"] if s.get("foto"))

        dlg = ft.AlertDialog(
            modal=True,
            bgcolor=theme.BG_CARD,
            title=ft.Text("Importare i dati?", color=theme.TEXT),
            content=ft.Text(
                f"Il backup contiene {n_giorni} giorni di scheda, {n_sessioni} sessioni "
                f"nello storico{n_foto and f' (di cui {n_foto} con foto)' or ''} "
                f"e anche: {extra_str.strip(' · ')}.\n\nVuoi SOSTITUIRE i dati attuali "
                "oppure UNIRLI (lo storico viene combinato, la scheda viene sostituita)?",
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
            theme.back_button(lambda e: app.show_home()),
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
                "sicurezza o per trasferire i dati su un altro dispositivo. "
                "Le foto NON sono incluse di default per tenere il file leggero.",
                size=12,
                color=theme.TEXT_MUTED,
            ),
            export_actions,
            include_fotos_cb,
            json_preview_field,
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
