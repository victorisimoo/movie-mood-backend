# movie-mood-backend

## Requisitos

- Python 3.x
- Bibliotecas: (Listar todas las bibliotecas y frameworks utilizados, por ejemplo, Flask, PyMongo, etc.)

## Configuración y Instalación

1. Clona el repositorio:
    ```bash
    git clone url_del_repositorio
    cd nombre_del_directorio
    ```

2. Crea un entorno virtual (opcional pero recomendado):
    ```bash
    python3 -m venv env
    source env/bin/activate  # En Windows, usa `env\Scripts\activate`
    ```

3. Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```

## Uso

### Indexación

Para construir el índice a partir de los documentos en un directorio específico, ejecuta:

```bash
python script_de_indexacion.py --directory_path ruta/del/directorio
