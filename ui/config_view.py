import subprocess
import threading
from pathlib import Path

import flet as ft

from core.config_manager import (
    get_clients_path,
    get_secret,
    save_clients_path,
    save_secret,
)

_DEFAULT_PATH = str(Path.home() / "Documents" / "Clientes")


class ConfigView:
    def __init__(self, page: ft.Page):
        self.page = page
        self._build_controls()

    # ── Controls ─────────────────────────────────────────────────────────────

    def _build_controls(self):
        # ── Secret key ──────────────────────────────────────────────────────
        has_key = bool(get_secret())

        self._status_icon = ft.Icon(
            "lock" if has_key else "lock_open",
            color=ft.Colors.GREEN_600 if has_key else ft.Colors.ORANGE_600,
            size=20,
        )
        self._status_text = ft.Text(
            "Clave configurada" if has_key else "Sin clave configurada",
            size=12,
            color=ft.Colors.GREEN_700 if has_key else ft.Colors.ORANGE_700,
            weight=ft.FontWeight.BOLD,
        )

        self._secret_field = ft.TextField(
            label="Nueva clave secreta",
            prefix_icon="key",
            password=True,
            can_reveal_password=True,
            border_radius=8,
            on_change=self._clear_key_feedback,
        )

        self._save_key_btn = ft.ElevatedButton(
            "Guardar en Keychain",
            icon="save",
            style=ft.ButtonStyle(
                color={ft.ControlState.DEFAULT: ft.Colors.WHITE},
                bgcolor={ft.ControlState.DEFAULT: ft.Colors.BLUE_700},
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=24, vertical=14),
            ),
            on_click=self._save_key,
        )

        self._key_feedback = ft.Text("", size=12, visible=False)

        # ── Clients path ─────────────────────────────────────────────────────
        self._path_display = ft.Text(
            self._fmt_path(get_clients_path()),
            size=11,
            color=ft.Colors.BLUE_GREY_700,
            selectable=True,
        )

        self._pick_folder_btn = ft.ElevatedButton(
            "Elegir carpeta",
            icon="folder_open",
            style=ft.ButtonStyle(
                color={ft.ControlState.DEFAULT: ft.Colors.WHITE},
                bgcolor={ft.ControlState.DEFAULT: ft.Colors.BLUE_700},
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=20, vertical=12),
            ),
            on_click=self._pick_folder,
        )

        self._reset_path_btn = ft.TextButton(
            "Restaurar por defecto",
            icon="restart_alt",
            on_click=self._reset_path,
        )

        self._path_feedback = ft.Text("", size=12, visible=False)

    # ── Key handlers ──────────────────────────────────────────────────────────

    def _clear_key_feedback(self, e=None):
        if self._key_feedback.visible:
            self._key_feedback.visible = False
            self.page.update()

    def _save_key(self, e):
        value = self._secret_field.value.strip() if self._secret_field.value else ""
        if not value:
            self._key_feedback.value = "La clave no puede estar vacía."
            self._key_feedback.color = ft.Colors.RED_700
            self._key_feedback.visible = True
            self.page.update()
            return

        try:
            save_secret(value)
            self._secret_field.value = ""
            self._status_icon.name = "lock"
            self._status_icon.color = ft.Colors.GREEN_600
            self._status_text.value = "Clave configurada"
            self._status_text.color = ft.Colors.GREEN_700
            self._key_feedback.value = "Clave guardada correctamente en el Keychain de macOS."
            self._key_feedback.color = ft.Colors.GREEN_700
        except Exception as ex:
            self._key_feedback.value = f"Error al guardar: {ex}"
            self._key_feedback.color = ft.Colors.RED_700

        self._key_feedback.visible = True
        self.page.update()

    # ── Path handlers ─────────────────────────────────────────────────────────

    def _fmt_path(self, path: str) -> str:
        home = str(Path.home())
        return ("~" + path[len(home):]) if path.startswith(home) else path

    def _pick_folder(self, e):
        threading.Thread(target=self._run_folder_picker, daemon=True).start()

    def _run_folder_picker(self):
        self._pick_folder_btn.disabled = True
        self._path_feedback.visible = False
        self.page.update()

        try:
            proc = subprocess.run(
                ["osascript", "-e",
                 'POSIX path of (choose folder with prompt "Seleccionar carpeta para los clientes")'],
                capture_output=True,
                text=True,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                path = proc.stdout.strip().rstrip("/")
                save_clients_path(path)
                self._path_display.value = self._fmt_path(path)
                self._set_path_feedback("Carpeta guardada correctamente.", success=True)
        except Exception as ex:
            self._set_path_feedback(f"Error: {ex}", success=False)
        finally:
            self._pick_folder_btn.disabled = False
            self.page.update()

    def _reset_path(self, e):
        save_clients_path("")
        self._path_display.value = self._fmt_path(_DEFAULT_PATH)
        self._set_path_feedback("Restaurado a la carpeta por defecto.", success=True)
        self.page.update()

    def _set_path_feedback(self, msg: str, *, success: bool):
        self._path_feedback.value = msg
        self._path_feedback.color = ft.Colors.GREEN_700 if success else ft.Colors.RED_700
        self._path_feedback.visible = True

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self) -> ft.Control:
        return ft.Column(
            controls=[
                ft.Row([
                    ft.Icon("settings", size=26, color=ft.Colors.BLUE_700),
                    ft.Text("Configuración", size=20, weight=ft.FontWeight.BOLD),
                ], spacing=8),
                ft.Divider(height=4),

                # Key status
                ft.Card(content=ft.Container(
                    content=ft.Column([
                        ft.Text("ESTADO DE LA CLAVE", size=11,
                                weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                        ft.Row([self._status_icon, self._status_text], spacing=8),
                    ], spacing=8),
                    padding=16,
                ), elevation=1),

                # Key input
                ft.Card(content=ft.Container(
                    content=ft.Column([
                        ft.Text("CONFIGURAR CLAVE SECRETA", size=11,
                                weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                        self._secret_field,
                        self._save_key_btn,
                        self._key_feedback,
                    ], spacing=10),
                    padding=16,
                ), elevation=1),

                # Clients folder
                ft.Card(content=ft.Container(
                    content=ft.Column([
                        ft.Text("CARPETA DE CLIENTES", size=11,
                                weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                        ft.Row([
                            ft.Icon("folder", color=ft.Colors.BLUE_GREY_400, size=16),
                            self._path_display,
                        ], spacing=6),
                        ft.Row([
                            self._pick_folder_btn,
                            self._reset_path_btn,
                        ], spacing=8),
                        self._path_feedback,
                    ], spacing=10),
                    padding=16,
                ), elevation=1),

                # Warning
                ft.Card(content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon("warning_amber", color=ft.Colors.ORANGE_700, size=20),
                            ft.Text("ADVERTENCIA", size=11,
                                    weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_700),
                        ], spacing=8),
                        ft.Text(
                            "La clave secreta se usa para firmar criptográficamente cada comprobante. "
                            "Si perdés o cambiás la clave, los comprobantes anteriores ya no podrán "
                            "ser verificados correctamente. Guardá una copia segura de tu clave.",
                            size=12,
                            color=ft.Colors.ORANGE_900,
                        ),
                    ], spacing=6),
                    padding=16,
                    bgcolor=ft.Colors.ORANGE_50,
                    border_radius=8,
                ), elevation=0),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=12,
            expand=True,
        )
