import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import unicodedata
import numpy as np
import os
import io
import tempfile
import streamlit.components.v1 as components

# ==========================
# Configuracion
# ==========================
st.set_page_config(
    page_title="Analisis IRM - Dengue Mexico",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* ── Fondo general ── */
    .stApp { 
        background: #f8f4f4;
        color: #2d1a1a; 
    }
    .block-container { padding: 2rem 2.5rem; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: white;
        border-radius: 12px;
        padding: 8px;
        gap: 8px;
        border: 2px solid #e17055;
        box-shadow: 0 4px 15px rgba(225,112,85,0.15);
    }
    .stTabs [data-baseweb="tab"] {
        background: #fff0ed;
        border-radius: 8px;
        color: #c0392b;
        font-weight: 700;
        font-size: 1rem;
        padding: 12px 32px;
        border: 2px solid transparent;
        transition: all 0.3s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: #ffe0d9;
        border-color: #e17055;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #d63031, #922b21) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(214,48,49,0.4);
        border-color: transparent !important;
    }

    /* ── Label de tabs ── */
    .stTabs [data-baseweb="tab-list"]::before {
        content: "Selecciona un periodo:";
        display: block;
        color: #c0392b;
        font-weight: 700;
        font-size: 0.8rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 6px;
        padding-left: 4px;
    }

    /* ── Metricas ── */
    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #f0d0c8;
        border-radius: 14px;
        padding: 20px 16px;
        text-align: center;
        transition: all 0.3s;
        box-shadow: 0 2px 8px rgba(225,112,85,0.08);
    }
    [data-testid="stMetric"]:hover {
        border-color: #e17055;
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(225,112,85,0.2);
    }
    [data-testid="stMetricLabel"] {
        color: #9e6050 !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    [data-testid="stMetricValue"] {
        color: #d63031 !important;
        font-size: 1.9rem !important;
        font-weight: 800 !important;
    }

    /* ── Titulos de seccion ── */
    .seccion-titulo {
        font-size: 1.4rem;
        font-weight: 700;
        color: white;
        background: linear-gradient(135deg, #d63031, #c0392b);
        border-left: 5px solid #922b21;
        border-radius: 0 10px 10px 0;
        padding: 14px 20px;
        margin: 2rem 0 1.2rem 0;
        box-shadow: 0 4px 15px rgba(214,48,49,0.2);
    }

    /* ── Separador ── */
    .separador {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, 
            transparent, #e1705566, #e17055, #e1705566, transparent);
        margin: 2.5rem 0;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #f8f4f4; }
    ::-webkit-scrollbar-thumb { 
        background: #e1705580; 
        border-radius: 3px; 
    }

    /* ── Inputs y selectbox ── */
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background: white !important;
        border-color: #f0d0c8 !important;
        color: #2d1a1a !important;
    }

    /* ── Botones ── */
    .stButton > button {
        background: linear-gradient(135deg, #d63031, #922b21);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        transition: all 0.3s;
        box-shadow: 0 4px 12px rgba(214,48,49,0.3);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(214,48,49,0.4);
    }

    /* ── Download buttons ── */
    .stDownloadButton > button {
        background: white;
        color: #d63031;
        border: 2px solid #d63031;
        border-radius: 8px;
        font-weight: 700;
        transition: all 0.3s;
    }
    .stDownloadButton > button:hover {
        background: #d63031;
        color: white;
    }

    /* ── Responsivo movil ── */
    @media (max-width: 768px) {
        .block-container { padding: 1rem 1rem !important; }
        h1 { font-size: 1.8rem !important; }
        .seccion-titulo { font-size: 1.1rem !important; }
        [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
        [data-testid="stMetricLabel"] { font-size: 0.75rem !important; }
        iframe { width: 100% !important; min-height: 300px; }
    }
            /* ── Radio buttons como botones ── */
    div[data-testid="stRadio"] > div {
        gap: 8px;
    }
    div[data-testid="stRadio"] label {
        background: white;
        border: 2px solid #f0d0c8;
        border-radius: 8px;
        padding: 6px 14px;
        color: #2d1a1a !important;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
    }
    div[data-testid="stRadio"] label span {
        color: #2d1a1a !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] span {
        color: white !important;
    }
    div[data-testid="stRadio"] label:hover {
        border-color: #d63031;
        background: #fff0ed;
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        background: #d63031;
        border-color: #d63031;
        color: white;
    }
            /* ── Multiselect mas pequeno ── */
    div[data-testid="stMultiSelect"] > div {
        min-height: 38px !important;
        font-size: 0.85rem !important;
    }
    div[data-testid="stMultiSelect"] > div > div {
        padding: 4px 8px !important;
        min-height: 38px !important;
    }
    /* ── Multiselect completo ── */
    div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
    div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div:hover {
        background-color: white !important;
        border-color: #d63031 !important;
        min-height: 36px !important;
        max-height: 36px !important;
        padding: 0 8px !important;
        font-size: 0.85rem !important;
        box-shadow: none !important;
    }
    div[data-testid="stMultiSelect"] * {
        color: #2d1a1a !important;
        font-size: 0.85rem !important;
    }
    div[data-testid="stMultiSelect"] input,
    div[data-testid="stMultiSelect"] input::placeholder {
        color: #2d1a1a !important;
        opacity: 1 !important;
        font-size: 0.85rem !important;
    }
    div[data-testid="stMultiSelect"] svg {
        fill: #d63031 !important;
    }
    div[data-baseweb="popover"] * {
        background: white !important;
        color: #2d1a1a !important;
    }
    div[data-baseweb="popover"] li:hover {
        background: #fff0ed !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================
# Utilidades
# ==========================
def normaliza(s):
    if pd.isna(s): return s
    s = str(s)
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")
    return s.strip().lower()

catalogo_ent = {
    1:"Aguascalientes", 2:"Baja California", 3:"Baja California Sur",
    4:"Campeche", 5:"Coahuila", 6:"Colima", 7:"Chiapas", 8:"Chihuahua",
    9:"Ciudad de Mexico", 10:"Durango", 11:"Guanajuato", 12:"Guerrero",
    13:"Hidalgo", 14:"Jalisco", 15:"Mexico", 16:"Michoacan", 17:"Morelos",
    18:"Nayarit", 19:"Nuevo Leon", 20:"Oaxaca", 21:"Puebla", 22:"Queretaro",
    23:"Quintana Roo", 24:"San Luis Potosi", 25:"Sinaloa", 26:"Sonora",
    27:"Tabasco", 28:"Tamaulipas", 29:"Tlaxcala", 30:"Veracruz",
    31:"Yucatan", 32:"Zacatecas"
}

sinos_shp = {
    normaliza("Coahuila de Zaragoza"):            normaliza("Coahuila"),
    normaliza("Michoacan de Ocampo"):             normaliza("Michoacan"),
    normaliza("Veracruz de Ignacio de la Llave"): normaliza("Veracruz"),
    normaliza("Estado de Mexico"):                normaliza("Mexico"),
}

BASE     = os.path.dirname(__file__)
SHP      = os.path.join(BASE, 'data', 'mexico_simple.gpkg')
XLS      = os.path.join(BASE, 'data', 'Base de datos principal defunciones.xlsx')
CSV_2224 = os.path.join(BASE, 'data', 'datos_2022_2024.parquet')
CSV_2024 = os.path.join(BASE, 'data', 'datos_2020_2024.parquet')
CSV_2025 = os.path.join(BASE, 'data', 'datos_2025.parquet')

TEMPLATE  = "plotly_white"
COLOR_IRM = ['#2ecc71','#f1c40f','#e67e22','#c0392b']
COLOR_DEF = ['#2ecc71','#f1c40f','#e67e22','#c0392b']

# ==========================
# Cargar datos
# ==========================
@st.cache_data
def cargar_csv(ruta):
    df = pd.read_parquet(ruta) if ruta.endswith('.parquet') else pd.read_csv(ruta)
    df['ESTADO'] = df['ENTIDAD_RES'].map(catalogo_ent)
    df['SEXO_LABEL'] = df['SEXO'].map({1:'Masculino', 2:'Femenino'})
    df['FECHA_SIGN_SINTOMAS'] = pd.to_datetime(
        df['FECHA_SIGN_SINTOMAS'], dayfirst=True, errors='coerce')
    df['ANIO'] = df['FECHA_SIGN_SINTOMAS'].dt.year.astype('Int64')
    return df

@st.cache_data
def cargar_defunciones_excel(hojas):
    conteo = {k: 0 for k in catalogo_ent}
    for hoja in hojas:
        df_a = pd.read_excel(XLS, sheet_name=hoja, engine='openpyxl')
        for cod, cant in df_a['ENTIDAD_RES'].value_counts().items():
            if cod in conteo:
                conteo[cod] += cant
    return pd.DataFrame([
        {'ENTIDAD_RES': k, 'ESTADO': catalogo_ent[k], 'defunciones': v}
        for k, v in conteo.items()
    ])

@st.cache_data
def cargar_defunciones_csv(ruta):
    df = pd.read_parquet(ruta) if ruta.endswith('.parquet') else pd.read_csv(ruta)
    conteo = {k: 0 for k in catalogo_ent}
    por_entidad = df[df['DEFUNCION'] == 1]['ENTIDAD_RES'].value_counts().to_dict()
    for cod, cant in por_entidad.items():
        if cod in conteo:
            conteo[cod] = cant
    return pd.DataFrame([
        {'ENTIDAD_RES': k, 'ESTADO': catalogo_ent[k], 'defunciones': v}
        for k, v in conteo.items()
    ])

@st.cache_data
def cargar_shp():
    gdf = gpd.read_file(SHP).to_crs(epsg=4326)
    gdf['name_norm'] = gdf['name'].apply(normaliza)
    for k, v in sinos_shp.items():
        gdf.loc[gdf['name_norm'] == k, 'name_norm'] = v
    codigo_to_norm = {k: normaliza(v) for k, v in catalogo_ent.items()}
    gdf['ENTIDAD_RES'] = np.nan
    for idx, row in gdf.iterrows():
        for cod, nom in codigo_to_norm.items():
            if nom == row['name_norm']:
                gdf.at[idx, 'ENTIDAD_RES'] = cod
                break
    return gdf

gdf_base = cargar_shp()

def_2024 = cargar_defunciones_excel(['Hoja1','Hoja2','Hoja3','Hoja4','Hoja5'])
def_2224 = cargar_defunciones_excel(['Hoja3','Hoja4','Hoja5'])
def_2025 = cargar_defunciones_csv(CSV_2025)

# ==========================
# Funciones: mapas Folium
# ==========================
def hacer_mapa(gdf, col_valor, titulo, paleta, tooltip_alias, key_suffix):
    valores = gdf[col_valor].dropna()

    # Calcular bins de forma segura
    try:
        _, bins = pd.qcut(valores, q=4, retbins=True, duplicates='drop')
        # Asegurar que siempre tengamos exactamente 5 puntos
        if len(bins) < 5:
            raise ValueError("Pocos valores unicos")
    except Exception:
        vmin = float(valores.min()) if len(valores) > 0 else 0.0
        vmax = float(valores.max()) if len(valores) > 0 else 1.0
        if vmin == vmax:
            vmax = vmin + 1
        bins = np.linspace(vmin, vmax, 5)

    es_entero = valores.apply(lambda x: float(x) == int(x)).all()
    if es_entero:
        cats = [
            f"Bajo ({int(bins[0])} - {int(bins[1])})",
            f"Medio ({int(bins[1])} - {int(bins[2])})",
            f"Alto ({int(bins[2])} - {int(bins[3])})",
            f"Critico ({int(bins[3])} - {int(bins[4])})"
        ]
    else:
        cats = [
            f"Bajo ({bins[0]:.3f} - {bins[1]:.3f})",
            f"Medio ({bins[1]:.3f} - {bins[2]:.3f})",
            f"Alto ({bins[2]:.3f} - {bins[3]:.3f})",
            f"Critico ({bins[3]:.3f} - {bins[4]:.3f})"
        ]

    colores_cat = dict(zip(cats, paleta))

    def categorizar(v):
        if pd.isna(v): return 'Sin datos'
        if v <= bins[1]: return cats[0]
        if v <= bins[2]: return cats[1]
        if v <= bins[3]: return cats[2]
        return cats[3]

    gdf = gdf.copy()
    gdf['categoria'] = gdf[col_valor].apply(categorizar)
    m = folium.Map(location=[23.5,-102.5], zoom_start=4,
                   tiles='CartoDB positron', scrollWheelZoom=False)
    folium.GeoJson(
        gdf,
        style_function=lambda f: {
            'fillColor': colores_cat.get(f['properties'].get('categoria','Sin datos'),'#bdc3c7'),
            'color': '#2c3e50', 'weight': 1.0, 'fillOpacity': 0.78
        },
        highlight_function=lambda f: {'fillOpacity':0.95,'weight':2.5},
        tooltip=folium.GeoJsonTooltip(
            fields=['name', col_valor, 'categoria'],
            aliases=['Estado:', tooltip_alias, 'Categoria:'],
            localize=True, sticky=True,
            style="background:#1a1a2e;color:white;font-size:13px;padding:8px;border-radius:6px;"
        )
    ).add_to(m)
    leyenda_items = "".join([
        f'<div style="margin:4px 0"><span style="display:inline-block;width:14px;height:14px;'
        f'background:{c};border-radius:3px;margin-right:6px;vertical-align:middle;"></span>{cat}</div>'
        for cat, c in colores_cat.items()
    ])
    m.get_root().html.add_child(folium.Element(f"""
    <div style="position:fixed;bottom:30px;left:20px;z-index:1000;
        background:rgba(13,17,23,0.92);padding:14px 18px;border-radius:10px;
        color:white;font-family:Arial;font-size:12px;
        border:1px solid rgba(255,255,255,0.1);">
        <b style="font-size:13px;">{titulo}</b><br><br>{leyenda_items}
    </div>"""))
    return m

def hacer_mapa_rangos_fijos(gdf, col_valor, titulo, tooltip_alias, key_suffix):
    CAT_BAJO    = "Bajo (0)"
    CAT_MEDIO   = "Medio (1 - 5)"
    CAT_ALTO    = "Alto (6 - 10)"
    CAT_CRITICO = "Critico (mas de 10)"
    colores_cat = {
        CAT_BAJO:    "#2ecc71",
        CAT_MEDIO:   "#f1c40f",
        CAT_ALTO:    "#e67e22",
        CAT_CRITICO: "#c0392b"
    }

    def categorizar(v):
        if pd.isna(v) or v <= 0: return CAT_BAJO
        if v <= 5:  return CAT_MEDIO
        if v <= 10: return CAT_ALTO
        return CAT_CRITICO

    gdf = gdf.copy()
    gdf['categoria'] = gdf[col_valor].apply(categorizar)
    m = folium.Map(location=[23.5,-102.5], zoom_start=4,
                   tiles='CartoDB positron', scrollWheelZoom=False)
    folium.GeoJson(
        gdf,
        style_function=lambda f: {
            'fillColor': colores_cat.get(
                f['properties'].get('categoria', CAT_BAJO), '#bdc3c7'),
            'color': '#2c3e50', 'weight': 1.0, 'fillOpacity': 0.78
        },
        highlight_function=lambda f: {'fillOpacity':0.95, 'weight':2.5},
        tooltip=folium.GeoJsonTooltip(
            fields=['name', col_valor, 'categoria'],
            aliases=['Estado:', tooltip_alias, 'Categoria:'],
            localize=True, sticky=True,
            style="background:#1a1a2e;color:white;font-size:13px;padding:8px;border-radius:6px;"
        )
    ).add_to(m)
    leyenda_items = "".join([
        f'<div style="margin:4px 0"><span style="display:inline-block;width:14px;height:14px;'
        f'background:{c};border-radius:3px;margin-right:6px;vertical-align:middle;"></span>{cat}</div>'
        for cat, c in colores_cat.items()
    ])
    m.get_root().html.add_child(folium.Element(
        '<div style="position:fixed;bottom:30px;left:20px;z-index:1000;'
        'background:rgba(13,17,23,0.92);padding:14px 18px;border-radius:10px;'
        'color:white;font-family:Arial;font-size:12px;'
        'border:1px solid rgba(255,255,255,0.1);">'
        f'<b style="font-size:13px;">{titulo}</b><br><br>{leyenda_items}'
        '</div>'
    ))
    return m

# ==========================
# Funcion: renderizar periodo
# ==========================
def render_periodo(periodo, df, df_def):

    total_casos     = len(df)
    total_def       = int((df['DEFUNCION']==1).sum())
    irm_nacional    = df['Indice_Riesgo'].mean()
    tasa_mortalidad = total_def / total_casos * 100

    # Metricas — 2 columnas en movil, 6 en escritorio
    c1, c2, c3 = st.columns(3)
    c1.metric("Casos de Dengue",    f"{total_casos:,}")
    c2.metric("Defunciones",        f"{total_def:,}")
    c3.metric("IRM Promedio",       f"{irm_nacional:.3f}")
    c4, c5, c6 = st.columns(3)
    c4.metric("Tasa Mortalidad",    f"{tasa_mortalidad:.2f}%")
    c5.metric("Estados Analizados", "32")
    c6.metric("Variables",          "16")

    st.markdown('<hr class="separador">', unsafe_allow_html=True)

    # Descripcion del IRM
    st.markdown("""
    <div style="
        background: white;
        border: 1px solid #f0d0c8;
        border-left: 5px solid #d63031;
        border-radius: 0 12px 12px 0;
        padding: 24px 28px;
        margin: 0 0 1rem 0;
        box-shadow: 0 2px 10px rgba(214,48,49,0.08);
        font-family: Arial, sans-serif;
    ">
        <h3 style="
            color: #d63031;
            font-size: 1.2rem;
            font-weight: 800;
            margin: 0 0 12px 0;
        ">IRM — Índice de Riesgo de Mortalidad por Dengue</h3>
        <p style="
            color: #4a2020;
            font-size: 0.95rem;
            line-height: 1.7;
            margin: 0 0 10px 0;
        ">
            El IRM es un índice compuesto que mide el riesgo relativo de mortalidad por dengue en México, integrando variables clínicas, ambientales y sociodemográficas.
        </p>
        <p style="
            color: #4a2020;
            font-size: 0.95rem;
            line-height: 1.7;
            margin: 0;
        ">
            Se construyó mediante un análisis multivariable utilizando machine learning, donde las variables fueron seleccionadas y ponderadas según su importancia (criterio de Gini en árboles de decisión El índice final permite identificar territorios con mayor riesgo y analizar patrones espaciales de la enfermedad.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="separador">', unsafe_allow_html=True)

    resumen_irm = df.groupby(['ENTIDAD_RES','ESTADO']).agg(
        irm_prom=('Indice_Riesgo','mean'),
    ).reset_index().sort_values('irm_prom', ascending=False)

    def_sexo = (df[df['DEFUNCION']==1]
                .groupby(['ESTADO','SEXO_LABEL'])
                .size().reset_index(name='muertes'))

    lista_estados = sorted(df['ESTADO'].dropna().unique().tolist())

    # ==========================
    # DESCARGA
    # ==========================
    st.markdown('<hr class="separador">', unsafe_allow_html=True)
    st.markdown('<div class="seccion-titulo">Descargar Datos</div>',
                unsafe_allow_html=True)
    st.markdown("Descarga el dataset completo de este periodo en formato CSV o Parquet.")
    col_d1, col_d2, col_d3 = st.columns([1, 1, 4])
    with col_d1:
        csv_bytes = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar CSV",
            data=csv_bytes,
            file_name=f"dataset_dengue_{periodo}.csv",
            mime="text/csv",
            key=f"btn_csv_{periodo}"
        )
    with col_d2:
        parquet_buffer = io.BytesIO()
        df.to_parquet(parquet_buffer, index=False)
        st.download_button(
            label="Descargar Parquet",
            data=parquet_buffer.getvalue(),
            file_name=f"dataset_dengue_{periodo}.parquet",
            mime="application/octet-stream",
            key=f"btn_parquet_{periodo}"
        )

    # ==========================
    # SECCION IRM
    # ==========================
    st.markdown('<div class="seccion-titulo">Indice de Riesgo de Mortalidad (IRM)</div>',
                unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#fff5f5;border:1px solid #f0d0c8;border-radius:10px;
        padding:12px 16px;margin-bottom:12px;font-family:Arial,sans-serif;">
        <span style="color:#d63031;font-weight:700;font-size:0.85rem;">
            Filtros — Selecciona estados o años para actualizar el mapa y la gráfica
        </span>
    </div>
    """, unsafe_allow_html=True)

    fi1, fi2 = st.columns([3, 1])
    with fi1:
        estados_sel_irm = st.multiselect(
            "Filtrar por estado (el mapa resaltará los estados seleccionados en la gráfica):",
            options=lista_estados,
            default=[],
            placeholder="Todos los estados (sin filtro)",
            key=f"filtro_irm_{periodo}"
        )
    with fi2:
        años_disponibles = sorted(df['ANIO'].dropna().unique().astype(int).tolist())
        st.markdown("""
        <style>
        div[data-testid="stRadio"] p {
            color: #2d1a1a !important;
            font-weight: 600 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        año_sel_irm = st.radio(
            "Filtrar por año:",
            options=["Todos"] + años_disponibles,
            horizontal=True,
            key=f"año_irm_{periodo}"
        )

    df_irm_filtrado = df.copy()
    if año_sel_irm != "Todos":
        df_irm_filtrado = df_irm_filtrado[
            df_irm_filtrado['ANIO'] == int(año_sel_irm)]

    resumen_irm_filtrado = df_irm_filtrado.groupby(['ENTIDAD_RES','ESTADO']).agg(
        irm_prom=('Indice_Riesgo','mean'),
    ).reset_index().sort_values('irm_prom', ascending=False)

    if estados_sel_irm:
        resumen_irm_graf = resumen_irm_filtrado[
            resumen_irm_filtrado['ESTADO'].isin(estados_sel_irm)]
    else:
        resumen_irm_graf = resumen_irm_filtrado

    gdf_irm = gdf_base.merge(
        resumen_irm_filtrado[['ENTIDAD_RES','irm_prom']], on='ENTIDAD_RES', how='left')

    col1, col2 = st.columns([1, 1])
    with col1:
        ruta_irm_full = os.path.join(tempfile.gettempdir(), f'mapa_irm_full_{periodo}.html')
        if not os.path.exists(ruta_irm_full):
            mapa_irm_temp = hacer_mapa(
                gdf_irm, 'irm_prom', 'IRM por Estado',
                COLOR_IRM, 'IRM Promedio:', f"irm_full_{periodo}")
            mapa_irm_temp.save(ruta_irm_full)

        if st.button("⛶ Ver Mapa IRM Completo", key=f"btn_irm_{periodo}"):
            st.session_state[f'modal_irm_{periodo}'] = True

        if st.session_state.get(f'modal_irm_{periodo}', False):
            @st.dialog("Mapa IRM - Vista Completa", width="large")
            def modal_irm():
                with open(ruta_irm_full, 'r', encoding='utf-8') as f:
                    mapa_html = f.read()
                components.html(mapa_html, height=650, scrolling=False)
                if st.button("Cerrar", key=f"cerrar_irm_{periodo}"):
                    st.session_state[f'modal_irm_{periodo}'] = False
                    st.rerun()
            modal_irm()

        mapa_irm = hacer_mapa(
            gdf_irm, 'irm_prom', 'IRM por Estado',
            COLOR_IRM, 'IRM Promedio:', f"irm_{periodo}")
        st_folium(mapa_irm, width="100%", height=430,
                  returned_objects=[], key=f"mapa_irm_{periodo}")

    with col2:
        altura_irm = max(750, len(resumen_irm_graf) * 25)
        fig_irm = px.bar(
            resumen_irm_graf.sort_values('irm_prom', ascending=True),
            x='irm_prom', y='ESTADO', orientation='h',
            color='irm_prom', color_continuous_scale=COLOR_IRM,
            labels={'irm_prom':'IRM Promedio','ESTADO':''},
            title=f'IRM Promedio por Estado ({periodo})',
            template=TEMPLATE
        )
        fig_irm.update_layout(
            height=altura_irm, coloraxis_showscale=False,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#faf5f5',
            font_color='#2d1a1a', font_family='Arial',
            margin=dict(l=10,r=10,t=40,b=10), bargap=0.15,
            title_font=dict(size=14, color='#d63031'),
            xaxis=dict(gridcolor='rgba(214,48,49,0.1)',
                       zerolinecolor='rgba(214,48,49,0.2)',
                       tickfont=dict(color='#2d1a1a'),
                       title_font=dict(color='#2d1a1a'),
                       linecolor='#2d1a1a'),
            yaxis=dict(gridcolor='rgba(214,48,49,0.1)',
                       tickfont=dict(color='#2d1a1a'),
                       title_font=dict(color='#2d1a1a'),
                       linecolor='#2d1a1a')
        )
        st.plotly_chart(fig_irm, width='stretch', key=f"graf_irm_{periodo}")

    st.markdown('<hr class="separador">', unsafe_allow_html=True)

    # ==========================
    # SECCION DEFUNCIONES
    # ==========================
    st.markdown('<div class="seccion-titulo">Defunciones Reales por Dengue</div>',
                unsafe_allow_html=True)

    st.markdown("""
    <style>
    div[data-testid="stRadio"] p {
        color: #2d1a1a !important;
        font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    fd1, fd2 = st.columns([3, 1])
    with fd1:
        estados_sel_def = st.multiselect(
            "Filtrar por estado:",
            options=lista_estados,
            default=[],
            placeholder="Todos los estados (sin filtro)",
            key=f"filtro_def_{periodo}"
        )
    with fd2:
        años_def = sorted(df['ANIO'].dropna().unique().astype(int).tolist())
        año_sel_def = st.radio(
            "Filtrar por año:",
            options=["Todos"] + años_def,
            horizontal=True,
            key=f"año_def_{periodo}"
        )

    # Calcular defunciones filtradas por año desde el CSV
    df_def_filtrado = df.copy()
    if año_sel_def != "Todos":
        df_def_filtrado = df_def_filtrado[
            df_def_filtrado['ANIO'] == int(año_sel_def)]

    # Recalcular defunciones por estado con el año filtrado
    conteo_def = {k: 0 for k in catalogo_ent}
    por_entidad = df_def_filtrado[df_def_filtrado['DEFUNCION'] == 1][
        'ENTIDAD_RES'].value_counts().to_dict()
    for cod, cant in por_entidad.items():
        if cod in conteo_def:
            conteo_def[cod] = cant

    df_def_periodo = pd.DataFrame([
        {'ENTIDAD_RES': k, 'ESTADO': catalogo_ent[k], 'defunciones': v}
        for k, v in conteo_def.items()
    ])

    if estados_sel_def:
        df_def_graf = df_def_periodo[df_def_periodo['ESTADO'].isin(estados_sel_def)]
    else:
        df_def_graf = df_def_periodo

    gdf_def = gdf_base.merge(
        df_def_periodo[['ENTIDAD_RES','defunciones']], on='ENTIDAD_RES', how='left')

    col3, col4 = st.columns([1, 1])
    with col3:
        ruta_def_full = os.path.join(tempfile.gettempdir(), f'mapa_def_full_{periodo}.html')
        if not os.path.exists(ruta_def_full):
            if periodo == "2025":
                mapa_def_temp = hacer_mapa_rangos_fijos(
                    gdf_def, 'defunciones', 'Defunciones por Estado',
                    'Defunciones:', f"def_full_{periodo}")
            else:
                mapa_def_temp = hacer_mapa(
                    gdf_def, 'defunciones', 'Defunciones por Estado',
                    COLOR_DEF, 'Defunciones:', f"def_full_{periodo}")
            mapa_def_temp.save(ruta_def_full)

        if st.button("Ver Mapa Defunciones Completo", key=f"btn_def_{periodo}"):
            st.session_state[f'modal_def_{periodo}'] = True

        if st.session_state.get(f'modal_def_{periodo}', False):
            @st.dialog("Mapa Defunciones - Vista Completa", width="large")
            def modal_def():
                with open(ruta_def_full, 'r', encoding='utf-8') as f:
                    mapa_html = f.read()
                components.html(mapa_html, height=650, scrolling=False)
                if st.button("Cerrar", key=f"cerrar_def_{periodo}"):
                    st.session_state[f'modal_def_{periodo}'] = False
                    st.rerun()
            modal_def()

        if periodo == "2025" and año_sel_def == "Todos":
            mapa_def = hacer_mapa_rangos_fijos(
                gdf_def, 'defunciones', 'Defunciones por Estado',
                'Defunciones:', f"def_{periodo}")
        else:
            mapa_def = hacer_mapa(
                gdf_def, 'defunciones', 'Defunciones por Estado',
                COLOR_DEF, 'Defunciones:', f"def_{periodo}")
        st_folium(mapa_def, width="100%", height=430,
                  returned_objects=[], key=f"mapa_def_{periodo}")

    with col4:
        altura_def = max(750, len(df_def_graf) * 25)
        fig_def = px.bar(
            df_def_graf.sort_values('defunciones', ascending=True),
            x='defunciones', y='ESTADO', orientation='h',
            color='defunciones', color_continuous_scale=COLOR_DEF,
            labels={'defunciones':'Defunciones','ESTADO':''},
            title=f'Defunciones por Estado ({periodo}'
                  + (f' - {año_sel_def}' if año_sel_def != "Todos" else '') + ')',
            template=TEMPLATE
        )
        fig_def.update_layout(
            height=altura_def, coloraxis_showscale=False,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#faf5f5',
            font_color='#2d1a1a', font_family='Arial',
            margin=dict(l=10,r=10,t=40,b=10), bargap=0.15,
            title_font=dict(size=14, color='#d63031'),
            xaxis=dict(gridcolor='rgba(214,48,49,0.1)',
                       zerolinecolor='rgba(214,48,49,0.2)',
                       tickfont=dict(color='#2d1a1a'),
                       title_font=dict(color='#2d1a1a'),
                       linecolor='#2d1a1a'),
            yaxis=dict(gridcolor='rgba(214,48,49,0.1)',
                       tickfont=dict(color='#2d1a1a'),
                       title_font=dict(color='#2d1a1a'),
                       linecolor='#2d1a1a')
        )
        st.plotly_chart(fig_def, width='stretch', key=f"graf_def_{periodo}")

    st.markdown('<hr class="separador">', unsafe_allow_html=True)

    # ==========================
    # SECCION SEXO
    # ==========================
    st.markdown('<div class="seccion-titulo">Defunciones por Sexo y Estado</div>',
                unsafe_allow_html=True)

    estados_sel_sexo = st.multiselect(
        "Filtrar estados:",
        options=lista_estados,
        default=[],
        placeholder="Todos los estados (sin filtro)",
        key=f"filtro_sexo_{periodo}"
    )

    if estados_sel_sexo:
        def_sexo_graf = def_sexo[def_sexo['ESTADO'].isin(estados_sel_sexo)]
    else:
        def_sexo_graf = def_sexo

    orden_estados = (def_sexo_graf.groupby('ESTADO')['muertes']
                     .sum().sort_values(ascending=True).index.tolist())

    fig_sexo = px.bar(
        def_sexo_graf,
        x='muertes', y='ESTADO', color='SEXO_LABEL',
        orientation='h', barmode='group',
        color_discrete_map={'Masculino':'#58a6ff','Femenino':'#e91e8c'},
        labels={'muertes':'Defunciones','ESTADO':'','SEXO_LABEL':'Sexo'},
        title=f'Defunciones por Sexo ({periodo})',
        category_orders={'ESTADO': orden_estados},
        template=TEMPLATE
    )
    altura_sexo = max(900, len(orden_estados) * 35)
    fig_sexo.update_layout(
        height=altura_sexo,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#faf5f5',
        font_color='#2d1a1a', font_family='Arial',
        margin=dict(l=10,r=10,t=40,b=10), bargap=0.2,
        title_font=dict(size=14, color='#d63031'),
        xaxis=dict(gridcolor='rgba(214,48,49,0.1)',
                   zerolinecolor='rgba(214,48,49,0.2)',
                   tickfont=dict(color='#2d1a1a'),
                   title_font=dict(color='#2d1a1a'),
                   linecolor='#2d1a1a'),
        yaxis=dict(gridcolor='rgba(214,48,49,0.1)',
                   tickfont=dict(color='#2d1a1a'),
                   title_font=dict(color='#2d1a1a'),
                   linecolor='#2d1a1a'),
        legend=dict(bgcolor='rgba(255,255,255,0.9)',
                    bordercolor='rgba(214,48,49,0.2)',
                    borderwidth=1,
                    font=dict(color='#2d1a1a'))
    )
    st.plotly_chart(fig_sexo, width='stretch', key=f"graf_sexo_{periodo}")

# ==========================
# HERO
# ==========================
st.markdown("""
<div style="padding: 70px 0 5px 0; margin-bottom: 5px;">
    <div style="
        display: inline-block;
        background: linear-gradient(135deg, rgba(214,48,49,0.1), rgba(225,112,85,0.05));
        border: 1px solid rgba(214,48,49,0.3);
        color: #d63031;
        padding: 5px 16px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 12px;
        font-family: Arial, sans-serif;
    ">
        Sistema de Análisis Espacial del Riesgo de Mortalidad por Dengue en México
    </div>
    <h1 style="
        font-size: 2.6rem;
        font-weight: 900;
        margin: 0;
        font-family: Arial, sans-serif;
        line-height: 1.2;
        background: linear-gradient(135deg, #2d1a1a 0%, #d63031 50%, #e17055 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    ">Índice de Riesgo de Mortalidad por Dengue</h1>
    <p style="
        color: #9e6050;
        font-size: 1rem;
        margin-top: 8px;
        font-family: Arial, sans-serif;
    ">
        Plataforma web para el monitoreo epidemiológico del dengue en México, que integra datos clínicos, ambientales y sociodemográficos para generar visualizaciones y análisis espaciales del riesgo de mortalidad. El sistema utiliza técnicas de análisis multivariable y machine learning para construir un índice de riesgo territorial que facilita la interpretación de patrones epidemiológicos y apoya la toma de decisiones en salud pública.
    </p>
</div>
""", unsafe_allow_html=True)

# TABS POR PERIODO
tab1, tab2, tab3 = st.tabs(["2020-2024", "2022-2024", "2025"])

with tab1:
    df_20_24 = cargar_csv(CSV_2024)
    render_periodo("2020-2024", df_20_24, def_2024)

with tab2:
    df_22_24 = cargar_csv(CSV_2224)
    render_periodo("2022-2024", df_22_24, def_2224)

with tab3:
    df_25 = cargar_csv(CSV_2025)
    render_periodo("2025", df_25, def_2025)