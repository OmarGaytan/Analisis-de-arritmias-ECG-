from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import serial
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from DataValidation.SignalProcessor import SignalProcessor as sp
from DataValidation.DataHandler import DataHandler as dh
from DataValidation.ConfigManager import ConfigManager 

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Análisis de ECG")
        self.geometry("900x700")
        self.configure(bg="#f0f0f0")
        
        # CONFIGURACIÓN
        self.config_manager = ConfigManager()
        config_data = self.config_manager.load_config()
        self.current_patient_name = config_data.get("last_patient", "Paciente_Anonimo")
        self.last_path = config_data.get("last_path", os.path.expanduser("~"))

        # VARIABLES DE ESTADO
        self.index = 0  
        self.data = []
        self.serial_port = None
        self.is_connected = False
        self.is_processing_csv = False
        self.hbeat_history = [] 

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # CONFIGURACION DE INTERFAZ GRAFICA
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.ax.set_title("Monitoreo de Señal ECG")
        self.ax.set_ylim(-0.05, 1.05) 

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.graph_widget = self.canvas.get_tk_widget()
        self.graph_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # CREACION DE PANEL DE CONTROL Y CONSOLA DE ESTADO
        self.create_control_panel()
        self.create_status_console()    

    # PANEL DE CONTROL: BOTONES Y ESTADO
    def create_control_panel(self):
        control_frame = ttk.LabelFrame(self, text=" Adquisición de Datos ")
        control_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.btn_csv = ttk.Button(control_frame, text="Cargar Archivo CSV", command=self.load_csv)
        self.btn_csv.pack(side="left", padx=10, pady=10)

        self.btn_serial = ttk.Button(control_frame, text="Conectar Hardware (Serial)", command=self.connect_serial)
        self.btn_serial.pack(side="left", padx=10, pady=10)

        self.lbl_status = ttk.Label(control_frame, text="Estado: Desconectado", foreground="red")
        self.lbl_status.pack(side="right", padx=10)

        self.btn_export = ttk.Button(control_frame, state="disabled", text="Finalizar y exportar", command=self.stop_and_export)
        self.btn_export.pack(side="right", padx=30, pady=10) 

    # CONSOLA DE ESTADO: LOGS DE EVENTOS Y ERRORES
    def create_status_console(self):
        console_frame = ttk.LabelFrame(self, text=" Consola de Estado ")
        console_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.console_text = tk.Text(console_frame, height=8, state="disabled", bg="black", fg="#00ff00")
        self.console_text.pack(fill="both", padx=5, pady=5)

    def log_event(self, message, type_msg="info"):
        self.console_text.config(state="normal")
        prefix = ">> ERROR:" if type_msg == "error" else ">>"
        self.console_text.insert("end", f"{prefix} {message}\n")
        self.console_text.see("end")
        self.console_text.config(state="disabled")

    # FUNCIONES PRINCIPALES: CARGA DE CSV, CONEXION SERIAL, ACTUALIZACION DINAMICA Y EXPORTACION DE RESULTADOS
    def load_csv(self):
        """Permite cargar un archivo CSV con datos históricos, llama al procesador de latidos y a la actualización de la gráfica y consola de estado en tiempo real"""
        if self.is_connected:
            messagebox.showwarning("Conflicto", "Desconecte el hardware antes de iniciar un análisis histórico")
            return

        try:
            self.btn_serial.config(state="disabled")
            self.btn_csv.config(state="disabled")     
            
            # Llenado del campo usando el JSON
            name_input = simpledialog.askstring(
                title="Registro de Paciente",
                prompt="Por favor, ingrese el nombre completo del paciente:",
                initialvalue=self.current_patient_name 
            )
            
            # Validacion de entrada de nombre
            if not name_input or not name_input.strip():
                self.log_event("Nombre no proporcionado, conexión cancelada", "info")
                self.btn_serial.config(state="normal")
                self.btn_csv.config(state="normal")
                return
            
            self.current_patient_name = name_input.strip()

            # Abre dialogo de seleccion de archivo con la ultima ruta conocida
            path = filedialog.askopenfilename(initialdir=self.last_path, filetypes=[("Archivos CSV", "*.csv")])
            if path:
                self.log_event(f"Archivo cargado: {path}", "info")
                
                # Actualiza la ruta persistente al cargar un nuevo archivo
                self.last_path = os.path.dirname(path)
                self.config_manager.save_config(self.current_patient_name, self.last_path)

                resultado = sp.signal_processor(path)
                
                if not resultado or isinstance(resultado, str):
                    error_msg = resultado if isinstance(resultado, str) else "El procesador no devolvió datos"
                    self.log_event(error_msg, "error")
                    messagebox.showerror("Error de Procesamiento", error_msg)
                    self.btn_serial.config(state="normal")
                    self.btn_csv.config(state="normal")
                    return
                
                self.data = [resultado] if isinstance(resultado, dict) else resultado
                                   
                self.log_event(f"Archivo cargado con éxito. Total de registros: {len(self.data):,}", "info")

                # Reinicio de estado para nuevo analisis
                self.index = 0
                self.is_processing_csv = True
                self.btn_export.config(state="normal")
                self.dynamic_update()
            else:
                self.log_event("Carga de archivo cancelada por el usuario", "info")
                self.btn_serial.config(state="normal")
                self.btn_csv.config(state="normal")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el archivo: {repr(e)}")
            self.log_event("Error crítico al procesar el archivo", "error")
            self.btn_serial.config(state="normal")
            self.btn_csv.config(state="normal")

    def dynamic_update(self):
        """Llama a la actualización la gráfica y consola de estado con cada nuevo latido procesado del CSV"""
        # Verificacion de estado para evitar conflictos entre procesos
        if not self.is_processing_csv:
            return

        try:              
            # Verifica el indice para evitar errores de rango
            if self.index < len(self.data):
                current_beat = self.data[self.index]
                self.update_canvas(current_beat)
                self.hbeat_history.append(current_beat)
                
                if current_beat.get("outliers"):
                    self.log_event(f"Latido {self.index}: {len(current_beat['outliers'])} pico(s) detectado(s)", "info")
                
                self.index += 1
                self.after(500, self.dynamic_update)
            else:
                self.log_event("Procesamiento del archivo histórico completo", "info")
                self.stop_and_export()
                
        except Exception as e:
            messagebox.showerror("Error", f"Fallo en actualización dinámica: {repr(e)}")
            self.log_event("Error en la lectura del array de datos", "error")

    def update_canvas(self, processed_data):
        """Redibuja la gráfica con la señal procesada y los picos R detectados"""
        signal = processed_data["signal"]
        outliers = processed_data["outliers"]

        # Limpia y actualiza la grafica con la nueva señal y los picos R detectados
        self.ax.clear()
        self.ax.plot(signal, color="blue", label="Señal ECG")

        if outliers:
            outliers_values = [signal[i] for i in outliers]
            self.ax.scatter(outliers, outliers_values, color="red", marker="o", s=40, label="Picos R")

        # Configuracion visual de la grafica
        self.ax.set_ylim(-0.05, 1.05)
        self.ax.set_xlim(0, len(signal))
        self.ax.set_title("Visualización de Latido en Tiempo Real")
        self.ax.legend(loc="upper right")
        self.ax.grid(True, linestyle="--", alpha=0.5)
        self.canvas.draw()

    def connect_serial(self):
        """Inicia la conexión serial con el hardware, solicita el nombre del paciente y comienza a escuchar el flujo de datos"""
        if self.is_processing_csv:
            messagebox.showwarning("Conflicto", "Detenga el análisis histórico antes de conectar hardware")
            return

        self.btn_csv.config(state="disabled")
        self.log_event("Iniciando búsqueda de puerto serial...", "info")
        self.index = 0
        
        if not self.is_connected:
            try:          
                # Solicita el nombre del paciente al iniciar conexion serial, con valor inicial desde el JSON
                name_input = simpledialog.askstring(
                    title="Registro de Paciente",
                    prompt="Por favor, ingrese el nombre completo del paciente:",
                    initialvalue=self.current_patient_name
                )
                
                if not name_input or not name_input.strip():
                    self.log_event("Nombre no proporcionado, conexión cancelada", "info")
                    self.btn_csv.config(state="normal")
                    return
                
                self.current_patient_name = name_input.strip()
                self.config_manager.save_config(self.current_patient_name, self.last_path)
                self.log_event(f"Iniciando análisis para el paciente: {self.current_patient_name}", "info")

                # Intenta conexion al puerto serial (NOTA IMPORTANTE PARA USTED MAESTRO: Se debe ajustar segun el sistema operativo y configuracion)
                # Use vSPD para crear puertos seriales virtuales en Windows y use COM1 para pruebas, en el reporte le doy mas informacion al respecto
                self.serial_port = serial.Serial("COM1", 9600, timeout=0)
                self.is_connected = True
                
                self.lbl_status.config(text="Estado: Conectado", foreground="green")
                self.log_event("Conexión al hardware establecida exitosamente", "info")
                self.btn_serial.config(text="Desconectar Hardware", command=self.disconnect_hardware)
                self.btn_export.config(state="normal")
                
                self.listen_serial()
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el puerto COM1: {e}")
                self.log_event("Fallo al conectar con el hardware", "error")
                self.lbl_status.config(text="Estado: Desconectado", foreground="red")
                self.btn_csv.config(state="normal")

    def listen_serial(self):
        """Escucha el flujo de datos del hardware, procesa cada latido en tiempo real y actualiza la gráfica y la consola de estado"""
        # Verificacion de estado para evitar conflictos entre procesos
        if self.is_connected and self.serial_port and self.serial_port.is_open:
            try:
                bytes_row = self.serial_port.readline()
                if bytes_row:
                    text_row = bytes_row.decode('utf-8').strip()
                    if text_row:
                        try:
                            values = [float(x) for x in text_row.split(',')]
                        except ValueError:
                            self.after(20, self.listen_serial)
                            return
                        
                        # Validacion de longitud minima para evitar errores de procesamiento
                        if len(values) < 2:
                            self.after(20, self.listen_serial)
                            return
                        
                        hbeat_signal = values[:-1]
                        processed_result = sp.process_individual_hbeat(hbeat_signal)
                        self.hbeat_history.append(processed_result)
                        self.update_canvas(processed_result)
                        
                        if processed_result.get("outliers"):
                            self.log_event(f"Latido {self.index}: {len(processed_result['outliers'])} pico(s) detectado(s)", "info")

                        self.index += 1
                
                # Continua escuchando el puerto serial, asi, uso un ciclo de eventos para evitar bloqueos en la interfaz grafica
                self.after(20, self.listen_serial)
                
            except Exception as e:
                self.log_event(f"Error leyendo el flujo de hardware: {repr(e)}", "error")
                self.disconnect_hardware()

    def stop_and_export(self):
        """Detiene análisis y genera el reporte"""
        try:
            self.btn_export.config(state="disabled")
            
            # Frena ciclos
            if self.is_processing_csv:
                self.log_event("Deteniendo reproducción de datos históricos (CSV)...", "info")
                self.is_processing_csv = False
                
            if self.is_connected:
                self.log_event("Deteniendo captura de datos seriales...", "info")
                self.disconnect_hardware()

            if not self.hbeat_history:
                self.log_event("No hay datos acumulados para exportar", "info")
                messagebox.showinfo("Sin Datos", "El análisis finalizó sin acumular latidos válidos")
                self.btn_csv.config(state="normal")
                self.btn_serial.config(state="normal")
                return
            
            self.lbl_status.config(text="Estado: Finalizado", foreground="blue")

            clean_name = "".join(c for c in self.current_patient_name if c.isalnum() or c in (' ', '_', '-')).strip()
            date = datetime.now().strftime("%Y%m%d_%H%M%S")
            suggested_name = f"Reporte_{clean_name}_{date}.txt"

            initial_dir = os.path.normpath(self.last_path) if self.last_path else os.path.expanduser("~")

            if self.last_path:
                os.makedirs(initial_dir, exist_ok=True)

            # Dialogo de guardado con la ultima ruta conocida y nombre sugerido
            chosen_path = filedialog.asksaveasfilename(
                title="Seleccionar ubicación para guardar el reporte",
                initialdir=initial_dir, 
                initialfile=suggested_name,
                defaultextension=".txt",
                filetypes=[("Archivos de Texto", "*.txt")]
            )

            if not chosen_path:
                self.log_event("Exportación cancelada por el usuario, los datos permanecen en memoria y se pueden exportar", "info")
                self.btn_csv.config(state="normal")
                self.btn_serial.config(state="normal")
                self.btn_export.config(state="normal")
                return
                
            # Se hace configuracion nueva, asi, se actualiza la ruta cada vez que se exporta un reporte
            self.last_path = os.path.dirname(chosen_path)
            self.config_manager.save_config(self.current_patient_name, self.last_path)
            
            # Al ser simulacion, hardcodeo el origen como "Simulador de Hardware (COM2)", pero en un caso de uso real se podria detectar dinamicamente
            origin = "Simulador de Hardware (COM2)" if hasattr(self, 'serial_port') and self.serial_port else "Archivo Histórico CSV"

            result_msg = dh.export_results(
                patient_name=self.current_patient_name,
                hbeat_history=self.hbeat_history,
                port=origin,
                path=chosen_path
            )

            self.log_event(result_msg, "info")
            messagebox.showinfo("Reporte Exportado", result_msg)
            
            # Reset de estado despues de la exportacion
            self.hbeat_history = []
            self.btn_csv.config(state="normal")
            self.btn_serial.config(state="normal")
            
        except Exception as e:
            self.log_event(f"Error al finalizar y exportar: {repr(e)}", "error")
            messagebox.showerror("Error", "Ocurrió un error en la exportación")
            self.btn_csv.config(state="normal")
            self.btn_serial.config(state="normal")

    def disconnect_hardware(self):
        """Desconecta el hardware, cierra el puerto serial y actualiza la interfaz de estado"""
        try:
            self.is_connected = False
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
            self.log_event("Hardware desconectado", "info")
            self.lbl_status.config(text="Estado: Desconectado", foreground="red")
            self.btn_serial.config(text="Conectar Hardware (Serial)", command=self.connect_serial)
        except Exception as e:
            self.log_event(f"Error al desconectar: {repr(e)}", "error")

if __name__ == "__main__":
    app = MainApp()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.destroy()