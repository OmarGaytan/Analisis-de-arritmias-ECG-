import pandas as pd
import matplotlib.pyplot as plt

#TODO: Falta el manejo de NaN y deteccion de outliers.
class SignalProcessor():
    @staticmethod
    def signal_processor(file_path):    
        try:
            # Intentar cargar el archivo CSV sin encabezado
            data = pd.read_csv(file_path, header=None)
            
            # Verificar que tenga al menos 2 columnas (una para la senal y otra para la etiqueta), si no, hago un early return con un mensaje de error
            if data.shape[1] < 2:
                #TODO: Agregar un mensaje de error en la consola de estado de la aplicacion en lugar de imprimirlo en la terminal
                return print("El archivo debe tener al menos 2 columnas (senal y etiqueta)")

            # Solo una visualizacion de un latido (fila 0) para validar el proceso de filtrado y normalizacion
            print(f"Filas: {data.shape[0]}, Columnas: {data.shape[1]}")
            signals = data.iloc[0, :-1]
            #labels  = data.iloc[0, -1]

            # Aplicar filtro de media movil (con un rango de 25 entre valores adyacentes) para eliminar el ruido de la senal original
            # min_periods=1 para que no haya NaN al inicio ni al final, center=True para que el filtro sea simetrico
            trend= pd.Series(signals).rolling(window=50, center=True, min_periods=1).mean()
            clean_signals = signals - trend  # Ahora si elimino el ruido de la senal original

            max_value = clean_signals.max()  # Excluyendo la ultima columna (etiqueta)
            min_value = clean_signals.min()  # Lo mismo que el anterior

            # Normalizar la senal filtrada
            normalized_signals = clean_signals.sub(min_value, axis=0).div(max_value - min_value, axis=0)

            plt.plot(normalized_signals)
            plt.title("Visualizacion de un solo latido")
            plt.show()
                    
        except Exception as e:
            #TODO: Agregar un mensaje de error en la consola de estado de la aplicacion en lugar de imprimirlo en la terminal
            return print(f"Error al procesar el archivo CSV: {e}")