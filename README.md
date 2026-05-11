# Sistema de Análisis de ECG

Este proyecto permite la adquisición y procesamiento de señales cardiacas. Siga estos pasos para configurar el entorno de ejecución en su equipo.

## 1. Requisitos Previos
* Python 3.12 o superior instalado.
* Visual Studio Code (Recomendado).

## 2. Configuración del Entorno Virtual
Es altamente recomendable usar un entorno virtual para evitar conflictos entre versiones de librerías.

1. Abra una terminal en la carpeta raíz del proyecto.
2. Cree el entorno virtual:
   ```bash
   python -m venv .venv

## 2. Configuración del Entorno Virtual
Dependiendo de su sistema operativo, use el comando correspondiente:

1. Windows (PowerShell):
* Si recibe un error de ejecución de scripts, use este comando para permitir la sesión actual:
    ```bash
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\.venv\Scripts\Activate.ps1

2. Windows (Símbolo del sistema / CMD):
    ```bash
    .venv\Scripts\activate.bat

3. Linux / macOS:
    ```bash
    source .venv/bin/activate

## 3. Instalación de Dependencias
Una vez activado el entorno (verá el prefijo (.venv) en la terminal), instale las librerías necesarias:
    ```bash
    pip install -r requirements.txt

## 4. Ejecución
Para iniciar la aplicación, ejecute:
    ```bash
    python MainApp.py
