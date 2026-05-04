import os
import subprocess
import threading

import flet as ft

from core.config_manager import get_counter, get_secret, save_counter
from core.crypto import compute_hmac
from core.file_manager import find_existing_pdf, get_pdf_path
from core.pdf_generator import build_pdf
from core.qr_handler import build_qr_content, make_qr_image


class GeneratorView:
    def __init__(self, page: ft.Page):
        self.page = page
        self._build_controls()

    # ── Controls ─────────────────────────────────────────────────────────────

    def _build_controls(self):
        counter = get_counter()

        self._nombre = ft.TextField(
            label="Nombre del cliente",
            prefix_icon="person",
            border_radius=8,
            on_change=self._clear_result,
        )
        self._precio = ft.TextField(
            label="Precio",
            prefix_icon="attach_money",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=8,
            on_change=self._clear_result,
        )
        self._numero = ft.TextField(
            label="Número de comprobante",
            prefix_icon="tag",
            keyboard_type=ft.KeyboardType.NUMBER,
            value=str(counter),
            border_radius=8,
            on_change=self._clear_result,
        )

        self._spinner = ft.ProgressRing(width=22, height=22, stroke_width=2.5, visible=False)
        self._gen_btn = ft.ElevatedButton(
            "Generar Comprobante",
            icon="receipt_long",
            style=ft.ButtonStyle(
                color={ft.ControlState.DEFAULT: ft.Colors.WHITE},
                bgcolor={ft.ControlState.DEFAULT: ft.Colors.BLUE_700},
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=24, vertical=14),
            ),
            on_click=self._generate,
        )

        # Result panel (hidden until generation completes)
        self._result_icon = ft.Icon("check_circle", color=ft.Colors.GREEN_600, size=32)
        self._result_title = ft.Text(
            "¡Comprobante generado!", size=16,
            weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700,
        )
        self._result_path = ft.Text("", size=11, color=ft.Colors.BLUE_GREY_700, selectable=True)
        self._open_btn = ft.TextButton(
            "Abrir carpeta",
            icon="folder_open",
            on_click=self._open_folder,
        )
        self._result_panel = ft.Container(
            content=ft.Column([
                ft.Row([self._result_icon, self._result_title], spacing=10),
                self._result_path,
                self._open_btn,
            ], spacing=6),
            padding=16,
            border_radius=8,
            bgcolor=ft.Colors.GREEN_50,
            border=ft.border.all(1, ft.Colors.GREEN_300),
            visible=False,
        )

        self._error_text = ft.Text("", color=ft.Colors.RED_700, size=12, visible=False)
        self._last_folder = ""

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _clear_result(self, e=None):
        if self._result_panel.visible or self._error_text.visible:
            self._result_panel.visible = False
            self._error_text.visible = False
            self.page.update()

    def _validate_inputs(self):
        nombre = self._nombre.value.strip() if self._nombre.value else ""
        precio = self._precio.value.strip() if self._precio.value else ""
        numero_s = self._numero.value.strip() if self._numero.value else ""

        if not nombre:
            return None, "El nombre del cliente es obligatorio."
        if not precio:
            return None, "El precio es obligatorio."
        try:
            float(precio.replace(",", "."))
        except ValueError:
            return None, "El precio debe ser un número válido."
        if not numero_s:
            return None, "El número de comprobante es obligatorio."
        try:
            numero = int(numero_s)
            if numero <= 0:
                raise ValueError
        except ValueError:
            return None, "El número de comprobante debe ser un entero positivo."

        secret = get_secret()
        if not secret:
            return None, "No hay clave secreta configurada. Andá a la pestaña Configuración."

        return (nombre, precio, numero, secret), None

    def _generate(self, e):
        self._clear_result()
        data, err = self._validate_inputs()
        if err:
            self._show_error(err)
            return

        self._gen_btn.disabled = True
        self._spinner.visible = True
        self.page.update()

        threading.Thread(target=self._run_generation, args=(data,), daemon=True).start()

    def _run_generation(self, data):
        nombre, precio, numero, secret = data
        try:
            existing = find_existing_pdf(nombre, numero)
            if existing:
                self._show_error(
                    f"Ya existe el comprobante N° {numero:04d} para este cliente.\n{existing}"
                )
                return

            hmac_hash = compute_hmac(secret, nombre, precio, str(numero))
            content = build_qr_content(nombre, precio, str(numero), hmac_hash)
            qr_img = make_qr_image(content)
            pdf_path = get_pdf_path(nombre, numero)
            build_pdf(pdf_path, nombre, precio, numero, hmac_hash, qr_img)

            # Increment counter: next = numero + 1
            save_counter(numero + 1)
            self._numero.value = str(numero + 1)

            self._last_folder = os.path.dirname(pdf_path)
            self._result_path.value = pdf_path
            self._result_panel.visible = True
            self._error_text.visible = False

        except Exception as ex:
            self._show_error(f"Error al generar: {ex}")

        finally:
            self._gen_btn.disabled = False
            self._spinner.visible = False
            self.page.update()

    def _open_folder(self, e):
        if self._last_folder and os.path.exists(self._last_folder):
            subprocess.Popen(["open", self._last_folder])

    def _show_error(self, msg: str):
        self._error_text.value = msg
        self._error_text.visible = True
        self._result_panel.visible = False
        self.page.update()

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self) -> ft.Control:
        return ft.Column(
            controls=[
                ft.Row([
                    ft.Icon("receipt_long", size=26, color=ft.Colors.BLUE_700),
                    ft.Text("Generador de Comprobantes", size=20, weight=ft.FontWeight.BOLD),
                ], spacing=8),
                ft.Divider(height=4),

                ft.Card(content=ft.Container(
                    content=ft.Column([
                        ft.Text("DATOS DEL COMPROBANTE", size=11,
                                weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                        self._nombre,
                        self._precio,
                        self._numero,
                    ], spacing=10),
                    padding=16,
                ), elevation=1),

                self._error_text,

                ft.Row([
                    self._gen_btn,
                    self._spinner,
                ], spacing=12, alignment=ft.MainAxisAlignment.CENTER),

                self._result_panel,
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=12,
            expand=True,
        )
