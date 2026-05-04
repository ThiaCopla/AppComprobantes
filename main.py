import flet as ft
from flet.core.control import Control as _FletControl
from pathlib import Path

# ── Flet 0.28 / Python 3.9 compatibility patch ──────────────────────────────
# Tab.before_update() calls isinstance(icon, IconValue) where IconValue is
# Union[str, Icons, CupertinoIcons] — raises TypeError on Python 3.9.
import flet.core.tabs as _tabs_mod


def _tab_before_update_patched(self):
    super(_tabs_mod.Tab, self).before_update()
    self._set_attr_json("iconMargin", self._Tab__icon_margin)
    if self._Tab__icon is not None and not isinstance(self._Tab__icon, _FletControl):
        self._set_enum_attr("icon", self._Tab__icon, _tabs_mod.IconEnums)


_tabs_mod.Tab.before_update = _tab_before_update_patched
# ────────────────────────────────────────────────────────────────────────────

from ui.generator_view import GeneratorView
from ui.validator_view import ValidatorView
from ui.config_view import ConfigView


ICON_PATH = str(Path(__file__).parent / "assets" / "icon.jpg")


def main(page: ft.Page):
    page.title = "AppComprobantes"
    page.window.icon = ICON_PATH
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 520
    page.window.height = 780
    page.window.resizable = True
    page.padding = 20

    generator = GeneratorView(page)
    validator = ValidatorView(page)
    config = ConfigView(page)

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=200,
        tabs=[
            ft.Tab(
                text="Generador",
                content=ft.Container(generator.build(), padding=ft.padding.only(top=16)),
            ),
            ft.Tab(
                text="Validador",
                content=ft.Container(validator.build(), padding=ft.padding.only(top=16)),
            ),
            ft.Tab(
                text="Configuración",
                content=ft.Container(config.build(), padding=ft.padding.only(top=16)),
            ),
        ],
        expand=True,
    )

    page.add(tabs)


ft.app(target=main, assets_dir="assets")
