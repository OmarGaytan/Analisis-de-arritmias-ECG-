import json
import os

class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_path = config_file

    def load_config(self):
        """Lee el archivo JSON y devuelve los datos guardados"""
        defaults = {"last_patient": "Paciente_Anonimo", "last_path": ""}
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Valida que existan las claves
                    return {
                        "last_patient": data.get("last_patient", defaults["last_patient"]),
                        "last_path": data.get("last_path", defaults["last_path"])
                    }
            except Exception:
                return defaults
        return defaults

    def save_config(self, patient, path):
        """Actualiza el archivo JSON con los nuevos datos si es que se cambian"""
        try:
            if os.path.isfile(path):
                path = os.path.dirname(path)
                
            datos = {
                "last_patient": patient,
                "last_path": path
            }
            
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error interno al guardar configuración: {repr(e)}")