import pandas as pd

class SignalProcessor():
    @staticmethod
    def signal_processor(file_path):
        """Procesa el archivo CSV de señales ECG, limpia, normaliza y detecta picos R. Retorna una lista de diccionarios con los resultados para cada latido"""  
        try:
            # Intenta cargar el archivo CSV sin encabezado
            data = pd.read_csv(file_path, header=None)
            
            # Verifica que tenga al menos 2 columnas
            if data.shape[1] < 2:
                return "Error: El archivo debe tener senal y etiqueta"
            
            # Selecciona todas las filas y excluyo la etiqueta
            signals = data.iloc[:, :-1]
            
            try:
                # Intenta convertir a numerico, forzando errores a NaN
                signals = signals.apply(pd.to_numeric, errors='raise')
            except (ValueError, TypeError):
                return "Error: El archivo contiene valores no numéricos o formato incorrecto"

            # Suma los nulos de toda la matriz
            detected_nulls = signals.isna().sum().sum()

            # Debido a la migracion a Pandas 3.0+, se refactorizo el procesamiento horizontal utilizando matrices transpuestas (.T)
            if detected_nulls > 0:
                # Transpone (.T), interpola y volvo a transponer (.T)
                nan_process = signals.T.interpolate(method='linear', limit_direction='both').T
            else:
                nan_process = signals

            # Transpone (.T), aplica rolling y vuelve a transponer (.T)
            trend = nan_process.T.rolling(window=50, center=True, min_periods=1).mean().T
            
            clean_signals = nan_process - trend 

            # Funciones .max() y .min()
            max_value = clean_signals.max(axis=1)
            min_value = clean_signals.min(axis=1)

            signal_range = max_value - min_value

            protected_range = signal_range.replace(0, 1)

            # sub() y div() con axis=0 para normalizar cada latido de forma independiente
            normalized_signals = clean_signals.sub(min_value, axis=0).div(protected_range, axis=0)
            results = []
            
            # Convierte el DataFrame a una matriz plana de NumPy
            norm_matrix = normalized_signals.to_numpy() 
            
            # Define umbral y distancia minima entre picos para deteccion de outliers
            umbral = 0.85
            min_distance = 50

            # Itera sobre cada latido en la matriz procesada
            for row_idx in range(len(norm_matrix)):
                row_signal = norm_matrix[row_idx]
                outliers = []
                last_peak = -min_distance

                # Busca maximos en este latido especifico
                for i in range(1, len(row_signal) - 1):
                    if row_signal[i] > umbral:
                        if row_signal[i] > row_signal[i-1] and row_signal[i] > row_signal[i+1]:
                            if (i - last_peak) > min_distance:
                                outliers.append(i)
                                last_peak = i
                
                # Agrega el diccionario de este latido a la lista principal
                results.append({
                    "signal": row_signal.tolist(),
                    "outliers": outliers,
                    "detected_outlier": len(outliers) != 1
                })

            # Retorna la lista de diccionarios con la señal procesada y los picos detectados
            return results

        except Exception as e:
            return f"Error critico al procesar el archivo: {repr(e)}"
        
    @staticmethod
    def process_individual_hbeat(lista_voltajes):
        """Recibe una lista con los voltajes de un solo latido y procesa esa señal de forma individual, aplicando los mismos pasos de limpieza, normalización y detección de picos R"""
        try:
            # Convierte la lista a una series de Pandas para usar los filtros
            signal = pd.Series(lista_voltajes)
            
            # Maneja NaN (interpolacion lineal si existen nulos)
            if signal.isna().sum() > 0:
                nan_process = signal.interpolate(method='linear', limit_direction='both')
            else:
                nan_process = signal

            # Normaliza la señal (elimina tendencia con un filtro de media movil)
            trend = nan_process.rolling(window=50, center=True, min_periods=1).mean()
            clean_signal = nan_process - trend

            # Normalizacion (Llevar los valores al rango 0 a 1)
            max_value = clean_signal.max()
            min_value = clean_signal.min()
            
            # Evita division por cero si la señal es completamente plana
            if max_value - min_value == 0:
                normalized_signal = clean_signal
            else:
                normalized_signal = (clean_signal - min_value) / (max_value - min_value)

            # 5. Deteccion de picos R
            outliers = []
            min_distancia = 50
            ultimo_pico = -min_distancia
            umbral = 0.85

            # Converte a arreglo de NumPy para optimizacion en ejecucion
            signal_array = normalized_signal.to_numpy()

            # Busca maximos en esta señal individual
            for i in range(1, len(signal_array) - 1):
                if signal_array[i] > umbral:
                    if signal_array[i] > signal_array[i-1] and signal_array[i] > signal_array[i+1]:
                        if (i - ultimo_pico) > min_distancia:
                            outliers.append(i)
                            ultimo_pico = i

            # Retornar el diccionario con el formato exacto que espera update_canvas
            return {
                "signal": signal_array.tolist(),
                "outliers": outliers,
                "detected_outlier": len(outliers) != 1
            }

        except Exception as e:
            print(f"Error en procesar_latido_individual: {e}")
            # Retorno de emergencia en caso de falla para que la app no crashee, aunque sin deteccion de picos
            return {"signal": lista_voltajes, "outliers": [], "detected_outlier": False}    