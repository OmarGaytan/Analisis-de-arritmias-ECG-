import os
from datetime import datetime

class DataHandler:
    @staticmethod
    def export_results(patient_name, hbeat_history, port, path):
        """Genera el reporte clínico con los resultados del análisis de los latidos y lo guarda en un archivo de texto con formato"""
        try:
            # Valida que el nombre no tenga caracteres invalidos para archivos
            clean_name = "".join(c for c in patient_name if c.isalnum() or c in (' ', '_', '-')).strip()
            if not clean_name:
                clean_name = "Paciente_Anonimo"

            # Calculo de metricas para el reporte
            total_hbeats = len(hbeat_history)
            anomalous_hbeats = sum(1 for l in hbeat_history if l.get("detected_outlier"))
            
            # Calculo estimado de BPM global basado en la frecuencia de la simulacion
            total_outliers = sum(len(l.get("outliers", [])) for l in hbeat_history)
            duration = total_hbeats * 0.6
            
            if duration > 0:
                average = (total_outliers / duration) * 60
            else:
                average = 0

            # Estructura del reporte clinico con formato
            with open(path, "w", encoding="utf-8") as file:
                file.write("==================================================\n")
                file.write("        SISTEMA DE ANÁLISIS DE SEÑALES ECG       \n")
                file.write("                REPORTE CLÍNICO                  \n")
                file.write("==================================================\n\n")
                
                file.write(f"Fecha de Emisión:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                file.write(f"Paciente:          {patient_name}\n")
                file.write(f"Origen de Datos:   {port}\n")
                file.write("--------------------------------------------------\n\n")
                
                file.write("RESUMEN DEL ANÁLISIS:\n")
                file.write(f" - Total de latidos analizados:   {total_hbeats}\n")
                file.write(f" - Ritmo Cardíaco Promedio:       {average:.1f} BPM\n")
                file.write(f" - Latidos con anomalías (picos): {anomalous_hbeats}\n")
                file.write(f" - Estado del Paciente:           ")

                # Evalua el estado del paciente basado en las metricas calculadas (diagnostico preliminar)
                if average < 10.0 or total_outliers == 0:
                    file.write("INCONCLUSO - Lectura fuera de rango funcional (Posible pérdida de señal o ausencia de picos R)\n")
                    file.write("   **Nota: Los datos procesados no presentan la morfología mínima requerida para sugerir un diagnóstico.\n")

                elif anomalous_hbeats > (total_hbeats * 0.15):
                    file.write("ALERTA - Alta presencia de picos R (Posible Arritmia)\n")

                else:
                    file.write("NORMAL - Ritmo dentro de los parámetros estables\n")
                
                file.write("\n--------------------------------------------------\n")
                file.write("DETALLE HISTÓRICO POR LATIDO:\n")
                file.write("--------------------------------------------------\n")
                file.write(f"{'Índice':<10}{'Picos R Detectados':<25}{'Estado':<15}\n")
                
                for idx, hbeat in enumerate(hbeat_history):
                    num_picos = len(hbeat.get("outliers", []))
                    estado = "Anómalo" if hbeat.get("detected_outlier") else "Normal"
                    file.write(f"{idx:<10}{num_picos:<25}{estado:<15}\n")
                
                file.write("\n==================================================\n")
                file.write("                    FIN DEL REPORTE               \n")
                file.write("==================================================\n")

            # Retorna un mensaje de exito con el nombre del archivo generado
            return f"Reporte guardado exitosamente como: {os.path.basename(path)}"

        except Exception as e:
            return f"Error crítico al guardar el reporte: {repr(e)}"