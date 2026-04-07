# Censo 2024 por Manzana

Visualizacion interactiva de datos del Censo 2024 de Chile a nivel de manzana censal.
Replica en Python/Streamlit de la app original en R/Shiny.

## Datos

El archivo Parquet con las cartografias lo publica el INE de Chile.
Puedes obtenerlo desde el repositorio de Bastian Olea:

https://github.com/bastianolea/censo_2024_mapas

Descarga el archivo `Cartografia_censo2024_Pais_Manzanas.parquet` y colocalo
en la misma carpeta que `app.py`.

## Instalacion

```bash
pip install -r requirements.txt
```

## Ejecucion

```bash
streamlit run app.py
```

## Stack

- **Streamlit** - interfaz web
- **DuckDB** - lectura lazy del Parquet sin cargar todo en memoria
- **GeoPandas** - manejo de geometrias
- **Plotly** - mapa interactivo con zoom

## Fuente de datos

Instituto Nacional de Estadisticas (INE) de Chile, Censo 2024.
