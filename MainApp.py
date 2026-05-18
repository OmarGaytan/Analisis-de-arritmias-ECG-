import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from DataValidation.SignalProcessor import SignalProcessor as sp
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # Configuracion de la ventana principal
        self.title("Sistema de Análisis de ECG - Proyecto Final")
        self.geometry("900x700")
        self.configure(bg="#f0f0f0")
        self.index = 0  # Para seguimiento de filas procesadas en el archivo CSV
        self.data= {}

        # Configuracion de pesos para que la interfaz sea responsiva
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)  # El area del grafico se expande mas

        # Creo la figura base de Matplotlib y el eje de dibujo (ax)
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(1, 1, 1)
        
        # Estilo inicial del grafico
        self.ax.set_title("Monitoreo de Señal ECG")
        self.ax.set_ylim(-0.05, 1.05) # Rango fijo de 0 a 1

        # Crear el area de grafico
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.graph_widget = self.canvas.get_tk_widget()
        self.graph_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        #TODO: Todas estas funciones deben retornar un estado para la consola de estado, por ejemplo, si se carga un archivo correctamente o si hay un error, etc. 
        # Esto se hara en la siguiente iteracion del proyecto, por ahora solo se imprimen mensajes en la terminal para validar que las funciones se ejecutan correctamente.
        # Panel de Control
        self.create_control_panel()

        # Area de Grafico
        self.create_graph_area()

        # Consola de Estado
        self.create_status_console()    

    def create_control_panel(self):
        """Espacio con botones de fuente de datos"""
        control_frame = ttk.LabelFrame(self, text=" Adquisicion de Datos ")
        control_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

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
        self.graph_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Placeholder del grafico
        self.placeholder_label = ttk.Label(self.graph_frame, text="[ El grafico de la señal se mostrara aqui ]", font=("Arial", 12))
        self.placeholder_label.place(relx=0.5, rely=0.5, anchor="center")

    def create_status_console(self):
        """Espacio con cuadro de texto para eventos del sistema"""
        console_frame = ttk.LabelFrame(self, text=" Consola de Estado ")
        console_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.console_text = tk.Text(console_frame, height=8, state="disabled", bg="black", fg="#00ff00")
        self.console_text.pack(fill="both", padx=5, pady=5)

    # Placeholders para funciones de logica
    def log_event(self, message, type):
        """Escribe mensajes en la consola de estado"""
        if type == "error":
            self.console_text.config(state="normal")
            self.console_text.insert("end", f">> ERROR: {message}\n")
            self.console_text.see("end")
            self.console_text.config(state="disabled")
        elif type == "info":
            self.console_text.config(state="normal")
            self.console_text.insert("end", f">> {message}\n")
            self.console_text.see("end")
            self.console_text.config(state="disabled")

    def load_csv(self):
        try:
            # Abrir un dialogo para seleccionar el archivo CSV
            path = filedialog.askopenfilename(filetypes=[("Archivos CSV", "*.csv")])
            if path:
                self.log_event(f"Archivo cargado: {path}", "info")
                
                # Obtengo el resultado del procesador
                resultado = sp.signal_processor(path)
                
                if not resultado:
                    self.log_event("Error: El procesador no devolvio datos.", "error")
                    return
                
                # Si el resultado es un string, significa que es un mensaje de error (DEBUG)
                if isinstance(resultado, str):
                    self.log_event(resultado, "error")
                    messagebox.showerror("Error de Procesamiento", resultado)
                    return
                
                # Si pasa la validacion, formateo los datos para la visualizacion dinamica
                if isinstance(resultado, dict):
                    self.data = [resultado]
                else:
                    self.data = resultado
                                   
            self.index = 0
            self.dynamic_update()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el archivo: {repr(e)}")
            self.log_event("Error al procesar el archivo.", "error")

    def dynamic_update(self):
        """Revisa si quedan latidos por mostrar y programa la actualizacion del lienzo."""
        # Verifico si ya se procesaron todas las filas del archivo
        if self.index < len(self.data):
            current_beat = self.data[self.index]
            
            # Mando el diccionario del latido y dibuja el canvas
            self.update_canvas(current_beat)
            
            # Log por si detecta picos en este latido
            if current_beat.get("outliers"):
                self.log_event(f"Latido {self.index}: {len(current_beat['outliers'])} pico(s) detectado(s).", "info")
            
            # Incremento el indice para pasar a la siguiente fila en el proximo ciclo
            self.index += 1
            
            # 500 milisegundos entre actualizacion (medio segundo por latido). Posteriormente se vuelve a llamar a esta funcion para crear un loop de actualizacion dinamica.
            self.after(500, self.dynamic_update)
        else:
            self.log_event("Procesamiento del archivo completo de manera exitosa.", "info")
            
            # TODO: Aqui es el punto seguro para llamar a DataHandler para exportar el reporte final .txt

    def update_canvas(self, processed_data):
        """Recibe el diccionario del SignalProcessor"""
        # Extraer los datos del diccionario
        signal = processed_data["signal"]
        outliers = processed_data["outliers"]

        # Borro el latido anterior para que no se encimen las lineas
        self.ax.clear()

        # Linea continua de la senal (azul)
        self.ax.plot(signal, color="blue", label="Señal ECG")

        # Puntos rojos en los picos detectados
        if outliers:
            outliers_values = [signal[i] for i in outliers]
            self.ax.scatter(outliers, outliers_values, color="red", marker="o", s=40, label="Picos R")

        # Configuracion estetica fija para que la gráfica no se "mueva" o cambie de tamaño
        self.ax.set_ylim(-0.05, 1.05)
        self.ax.set_xlim(0, len(signal))
        self.ax.set_title("Visualizacion de Latido en Tiempo Real")
        self.ax.legend(loc="upper right")
        self.ax.grid(True, linestyle="--", alpha=0.5)

        # Redibujar los cambios inmediatamente
        self.canvas.draw()

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