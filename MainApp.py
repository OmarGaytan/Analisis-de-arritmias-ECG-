import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from DataValidation.SignalProcessor import SignalProcessor as sp

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # Configuracion de la ventana principal
        self.title("Sistema de Análisis de ECG - Proyecto Final")
        self.geometry("900x700")
        self.configure(bg="#f0f0f0")

        # Configuracion de pesos para que la interfaz sea responsiva
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)  # El area del grafico se expande mas

        #TODO: Todas estas funciones deben retornar un estado para la consola de estado, por ejemplo, si se carga un archivo correctamente o si hay un error, etc. 
        # Esto se hara en la siguiente iteracion del proyecto, por ahora solo se imprimen mensajes en la terminal para validar que las funciones se ejecutan correctamente.
        # Panel de Control
        self.create_control_panel()

        # Area de Grafico
        self.create_graph_area()

        # Consola de Estado
        self.create_status_console()

        # Prueba de validacion de la clase SignalProcessor
        #TODO: Verificar si los datos ya normalizados se visualizan correctamente
        sp.signal_processor("ecg_no_normalized.csv")

    def create_control_panel(self):
        """Espacio con botones de fuente de datos"""
        control_frame = ttk.LabelFrame(self, text=" Adquisicion de Datos ")
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.btn_csv = ttk.Button(control_frame, text="Cargar Archivo CSV", command=self.load_csv)
        self.btn_csv.pack(side="left", padx=10, pady=10)

        self.btn_serial = ttk.Button(control_frame, text="Conectar Hardware (Serial)", command=self.connect_serial)
        self.btn_serial.pack(side="left", padx=10, pady=10)

        # Indicador de conexion (placeholder)
        self.lbl_status = ttk.Label(control_frame, text="Estado: Desconectado", foreground="red")
        self.lbl_status.pack(side="right", padx=10)

    def create_graph_area(self):
        """Espacio para visualizacion de ECG"""
        # Espacio reservado para Matplotlib 
        self.graph_frame = ttk.LabelFrame(self, text=" Visualizador Dinamico de ECG ")
        self.graph_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        # Placeholder del grafico
        self.placeholder_label = ttk.Label(self.graph_frame, text="[ El grafico de la señal se mostrara aqui ]", font=("Arial", 12))
        self.placeholder_label.place(relx=0.5, rely=0.5, anchor="center")

    def create_status_console(self):
        """Espacio con cuadro de texto para eventos del sistema"""
        console_frame = ttk.LabelFrame(self, text=" Consola de Estado ")
        console_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        self.console_text = tk.Text(console_frame, height=8, state="disabled", bg="black", fg="#00ff00")
        self.console_text.pack(fill="both", padx=5, pady=5)

    # Placeholders para funciones de logica
    def log_event(self, message):
        """Escribe mensajes en la consola de estado"""
        self.console_text.config(state="normal")
        self.console_text.insert("end", f">> {message}\n")
        self.console_text.see("end")
        self.console_text.config(state="disabled")

    def load_csv(self):
        try:
            path = filedialog.askopenfilename(filetypes=[("Archivos CSV", "*.csv")])
            if path:
                self.log_event(f"Archivo cargado: {path}")
                # Aqui se llamara a DataHandler
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el archivo: {e}")

    def connect_serial(self):
        # Simulacion de conexion
        try:
            self.log_event("Iniciando busqueda de puerto serial...")
            self.lbl_status.config(text="Estado: Conectado (Simulado)", foreground="green")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar al hardware: {e}")
            self.lbl_status.config(text="Estado: Desconectado", foreground="red")

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()