import pandas as pd
import matplotlib.pyplot as plt

class SignalProcessor():
    @staticmethod
    def signal_processor(file_path):    
        try:
            # Intentar cargar el archivo CSV sin encabezado
            data = pd.read_csv(file_path, header=None)
            
            # Verificar que tenga al menos 2 columnas
            if data.shape[1] < 2:
                # TODO: Agregar un mensaje de error en la consola
                return "Error: El archivo debe tener senal y etiqueta"

            print(f"Filas a procesar: {data.shape[0]}, Columnas: {data.shape[1]}")
            
            # Selecciono todas las filas y excluyo la etiqueta
            signals = data.iloc[:, :-1]
            
            # Sumo los nulos de toda la matriz
            detected_nulls = signals.isna().sum().sum()

            #TODO: DOCUMENTAR ESTA CORRECCION: Debido a la migración a Pandas 3.0+, se refactorizo el procesamiento horizontal utilizando matrices transpuestas (.T) para mantener la eficiencia vectorizada ante la depreciacion del parametro axis=1
            if detected_nulls > 0:
                print(f"Se detectaron {detected_nulls} valores nulos. Iniciando correccion...")
                # Transpogo (.T), interpolo y volvo a transponer (.T)
                nan_process = signals.T.interpolate(method='linear', limit_direction='both').T
            else:
                print("No se detectaron valores nulos. Procede...")
                nan_process = signals

            # Transponer (.T), aplico rolling y volvo a transponer (.T)
            trend = nan_process.T.rolling(window=50, center=True, min_periods=1).mean().T
            
            clean_signals = nan_process - trend 

            # Funciones .max() y .min()
            max_value = clean_signals.max(axis=1)
            min_value = clean_signals.min(axis=1)

            # sub() y div() con axis=0 para normalizar cada latido de forma independiente
            normalized_signals = clean_signals.sub(min_value, axis=0).div(max_value - min_value, axis=0)
            results = []
            
            # Converto el DataFrame a una matriz plana de NumPy
            norm_matrix = normalized_signals.to_numpy() 
            
            # Defino umbral y distancia minima entre picos para deteccion de outliers
            umbral = 0.85
            min_distance = 50

            # Iteramos sobre cada latido en la matriz procesada
            for row_idx in range(len(norm_matrix)):
                row_signal = norm_matrix[row_idx]
                outliers = []
                last_peak = -min_distance

                # Busco maximos en este latido especifico
                for i in range(1, len(row_signal) - 1):
                    if row_signal[i] > umbral:
                        if row_signal[i] > row_signal[i-1] and row_signal[i] > row_signal[i+1]:
                            if (i - last_peak) > min_distance:
                                outliers.append(i)
                                last_peak = i
                
                # Agrego el diccionario de este latido a la lista principal
                results.append({
                    "signal": row_signal.tolist(),
                    "outliers": outliers,
                    "detected_outlier": len(outliers) > 0
                })

            # Retorno la lista de diccionarios con la señal procesada y los picos detectados
            return results

        # TODO: Enviar esto a la consola de MainApp y mostrar un mensaje de error al usuario, sin que se caiga la app
        except Exception as e:
            return f"Error critico al procesar el archivo: {repr(e)}"