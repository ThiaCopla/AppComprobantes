import os
import subprocess
import threading

import flet as ft

from core.config_manager import get_secret
from core.crypto import verify_hmac
from core.qr_handler import decode_qr, parse_qr_content

_ALLOWED_EXT = {".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


class ValidatorView:
    def __init__(self, page: ft.Page):
        self.page = page
        self._build_controls()

    # ── Controls ─────────────────────────────────────────────────────────────

    def _build_controls(self):
        self._pick_btn = ft.ElevatedButton(
            "Seleccionar archivo",
            icon="upload_file",
            style=ft.ButtonStyle(
                color={ft.ControlState.DEFAULT: ft.Colors.WHITE},
                bgcolor={ft.ControlState.DEFAULT: ft.Colors.BLUE_700},
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=24, vertical=14),
            ),
            on_click=self._pick_file,
        )

        self._spinner = ft.ProgressRing(width=22, height=22, stroke_width=2.5, visible=False)

        self._selected_path = ft.Text(
            "Ningún archivo seleccionado",
            size=11,
            color=ft.Colors.BLUE_GREY_400,
            italic=True,
        )

        self._valid_rows = ft.Column([], spacing=4)
        self._valid_panel = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon("check_circle", color=ft.Colors.GREEN_600, size=32),
                    ft.Text(
                        "COMPROBANTE VÁLIDO",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREEN_700,
                    ),
                ], spacing=10),
                ft.Divider(height=6, color=ft.Colors.GREEN_200),
                self._valid_rows,
            ], spacing=6),
            padding=16,
            border_radius=8,
            bgcolor=ft.Colors.GREEN_50,
            border=ft.border.all(1, ft.Colors.GREEN_300),
            visible=False,
        )

        self._invalid_detail = ft.Text("", size=12, color=ft.Colors.RED_800)
        self._invalid_panel = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon("cancel", color=ft.Colors.RED_600, size=32),
                    ft.Text(
                        "COMPROBANTE INVÁLIDO",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_700,
                    ),
                ], spacing=10),
                self._invalid_detail,
            ], spacing=6),
            padding=16,
            border_radius=8,
            bgcolor=ft.Colors.RED_50,
            border=ft.border.all(1, ft.Colors.RED_300),
            visible=False,
        )

        self._error_text = ft.Text("", color=ft.Colors.RED_700, size=12, visible=False)

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _pick_file(self, e):
        threading.Thread(target=self._run_pick_and_validate, daemon=True).start()

    def _run_pick_and_validate(self):
        self._pick_btn.disabled = True
        self._spinner.visible = True
        self._reset_panels()
        self.page.update()

        try:
            proc = subprocess.run(
                ["osascript", "-e",
                 'POSIX path of (choose file with prompt "Seleccionar comprobante")'],
                capture_output=True,
                text=True,
            )

            if proc.returncode != 0 or not proc.stdout.strip():
                self._selected_path.value = "Ningún archivo seleccionado"
                return

            path = proc.stdout.strip()
            if os.path.splitext(path)[1].lower() not in _ALLOWED_EXT:
                self._show_error("Formato no soportado. Usá PDF, JPG o PNG.")
                return

            self._selected_path.value = path
            self._selected_path.italic = False
            self._selected_path.color = ft.Colors.BLUE_GREY_700
            self.page.update()

            raw = decode_qr(path)
            if not raw:
                self._show_error("No se encontró ningún QR en el archivo.")
                return

            data = parse_qr_content(raw)
            if not data:
                self._show_error("El QR no tiene el formato esperado.")
                return

            secret = get_secret()
            if not secret:
                self._show_error(
                    "No hay clave secreta configurada. Configurala en la pestaña Configuración."
                )
                return

            if verify_hmac(secret, data["nombre"], data["precio"], data["numero"], data["hash"]):
                self._show_valid(data)
            else:
                self._show_invalid(
                    "La firma digital no coincide. El comprobante puede haber sido alterado."
                )

        except Exception as ex:
            self._show_error(f"Error al validar: {ex}")
        finally:
            self._pick_btn.disabled = False
            self._spinner.visible = False
            self.page.update()

    def _reset_panels(self):
        self._valid_panel.visible = False
        self._invalid_panel.visible = False
        self._error_text.visible = False

    def _show_valid(self, data: dict):
        rows = [
            ("Cliente",        data["nombre"]),
            ("Precio",         f"${data['precio']}"),
            ("N° Comprobante", data["numero"]),
            ("Firma (HMAC)",   data["hash"]),
        ]
        self._valid_rows.controls = [
            ft.Row([
                ft.Text(label + ":", size=11, weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREEN_800, width=120),
                ft.Text(value, size=12, selectable=True, color=ft.Colors.GREEN_900),
            ], spacing=6)
            for label, value in rows
        ]
        self._valid_panel.visible = True
        self._invalid_panel.visible = False
        self._error_text.visible = False

    def _show_invalid(self, reason: str):
        self._invalid_detail.value = reason
        self._invalid_panel.visible = True
        self._valid_panel.visible = False
        self._error_text.visible = False

    def _show_error(self, msg: str):
        self._error_text.value = msg
        self._error_text.visible = True
        self._valid_panel.visible = False
        self._invalid_panel.visible = False

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self) -> ft.Control:
        return ft.Column(
            controls=[
                ft.Row([
                    ft.Icon("verified", size=26, color=ft.Colors.BLUE_700),
                    ft.Text("Validador de Comprobantes", size=20, weight=ft.FontWeight.BOLD),
                ], spacing=8),
                ft.Divider(height=4),

                ft.Card(content=ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "Seleccioná una imagen (JPG/PNG) o PDF que contenga el código QR del comprobante.",
                            size=12,
                            color=ft.Colors.BLUE_GREY_600,
                        ),
                        ft.Row([
                            self._pick_btn,
                            self._spinner,
                        ], spacing=12),
                        self._selected_path,
                    ], spacing=10),
                    padding=16,
                ), elevation=1),

                self._error_text,
                self._valid_panel,
                self._invalid_panel,
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=12,
            expand=True,
        )
