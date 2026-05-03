import flet as ft
import os
import shutil

def main(page: ft.Page):
    page.title = "Generador de Comprobantes Pro"
    page.window_width = 600
    page.window_height = 700
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # --- VARIABLES DE ESTADO ---
    ruta_seleccionada = ft.Text("No se ha seleccionado una carpeta de destino", color="grey")
    archivo_a_procesar = ft.Text("No hay archivo seleccionado", color="grey")
    
    # --- LÓGICA DE ARCHIVOS ---
    def result_folder(e: ft.FilePickerResultEvent):
        if e.path:
            ruta_seleccionada.value = e.path
            ruta_seleccionada.color = "blue"
        else:
            ruta_seleccionada.value = "Selección cancelada"
            ruta_seleccionada.color = "red"
        page.update()

    folder_picker = ft.FilePicker(on_result=result_folder)
    
    def result_file(e: ft.FilePickerResultEvent):
        if e.files:
            archivo_a_procesar.value = e.files[0].name
            archivo_a_procesar.data = e.files[0].path
            archivo_a_procesar.color = "blue"
        else:
            archivo_a_procesar.value = "Selección cancelada"
            archivo_a_procesar.color = "red"
        page.update()

    file_picker = ft.FilePicker(on_result=result_file)
    
    # Es clave agregar los pickers al overlay ANTES de usarlos y forzar el update
    page.overlay.extend([folder_picker, file_picker])
    page.update()

    # --- FUNCIONES DE BOTONES (Con prints para depurar en la consola) ---
    def click_carpeta(e):
        print("🟢 Clic detectado: Abriendo selector de carpeta...")
        folder_picker.get_directory_path()

    def click_archivo(e):
        print("🟢 Clic detectado: Abriendo selector de archivo...")
        file_picker.pick_files(allow_multiple=False)

    def procesar_comprobante(e):
        print("🟢 Clic detectado: Procesando y guardando...")
        if not input_cliente.value or ruta_seleccionada.value.startswith("No") or ruta_seleccionada.value.startswith("Selección"):
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ Falta el cliente o la ruta de destino"))
            page.snack_bar.open = True
            page.update()
            return

        ruta_final = os.path.join(ruta_seleccionada.value, "Clientes", input_cliente.value)
        os.makedirs(ruta_final, exist_ok=True)

        if archivo_a_procesar.data:
            nombre_final = f"Comprobante_{input_cliente.value}_{archivo_a_procesar.value}"
            destino = os.path.join(ruta_final, nombre_final)
            shutil.copy(archivo_a_procesar.data, destino)
            
            page.snack_bar = ft.SnackBar(ft.Text(f"✅ ¡Guardado en {input_cliente.value}!"))
            page.snack_bar.open = True
        
        page.update()

    # --- DISEÑO DE LA INTERFAZ ---
    input_cliente = ft.TextField(label="Nombre del Cliente", prefix_icon="person")

    page.add(
        ft.Text("Configuración de Proyecto", size=20, weight="bold"),
        ft.ElevatedButton("1. Elegir Carpeta de Destino", 
                          icon="folder_open", 
                          on_click=click_carpeta),
        ruta_seleccionada,
        
        ft.Divider(),
        
        ft.Text("Entrada de Datos", size=20, weight="bold"),
        input_cliente,
        ft.ElevatedButton("2. Cargar Comprobante (PDF/Foto)", 
                          icon="upload_file", 
                          on_click=click_archivo),
        archivo_a_procesar,
        
        ft.Divider(),
        
        ft.FloatingActionButton(text="Procesar y Guardar", 
                                 icon="play_arrow", 
                                 on_click=procesar_comprobante),
    )

ft.app(target=main)