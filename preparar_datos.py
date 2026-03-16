import pandas as pd
import os
import geopandas as gpd


BASE = os.path.dirname(__file__)

archivos = {
    'dataset_con_irm.csv':      'datos_2022_2024.parquet',
    'dataset_con_irm20_24.csv': 'datos_2020_2024.parquet',
    'dataset_con_irm20_25.csv': 'datos_2025.parquet',
}

for csv, parquet in archivos.items():
    ruta_csv = os.path.join(BASE, 'data', csv)
    ruta_parquet = os.path.join(BASE, 'data', parquet)
    print(f'Convirtiendo {csv}...')
    df = pd.read_csv(ruta_csv)
    df.to_parquet(ruta_parquet, index=False)
    size_csv     = os.path.getsize(ruta_csv) / 1024 / 1024
    size_parquet = os.path.getsize(ruta_parquet) / 1024 / 1024
    print(f'  CSV: {size_csv:.1f} MB  →  Parquet: {size_parquet:.1f} MB')

print('\nListo!')


print('Simplificando shapefile...')
shp = os.path.join(BASE, 'data', 'mexican-states-master', 'mexican-states.shp')
gdf = gpd.read_file(shp).to_crs(epsg=4326)
gdf_simple = gdf.copy()
gdf_simple['geometry'] = gdf_simple['geometry'].simplify(
    tolerance=0.01, preserve_topology=True)
salida = os.path.join(BASE, 'data', 'mexico_simple.gpkg')
gdf_simple.to_file(salida, driver='GPKG')
size_shp = os.path.getsize(shp) / 1024 / 1024
size_gpkg = os.path.getsize(salida) / 1024 / 1024
print(f'  SHP: {size_shp:.1f} MB  →  GPKG: {size_gpkg:.1f} MB')
print('Listo!')