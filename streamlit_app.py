import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import unicodedata
import numpy as np
import os
import threading
import http.server
import socketserver
import io
import tempfile


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
        background: linear-gradient(160deg, #1a0a0a 0%, #140d0d 50%, #1a0a08 100%);
        color: #f0e6e6; 
    }
    .block-container { padding: 2rem 2.5rem; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: #221414;
        border-radius: 12px;
        padding: 6px;
        gap: 6px;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: #b08080;
        font-weight: 600;
        font-size: 1rem;
        padding: 10px 28px;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #d63031, #922b21) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(214,48,49,0.4);
    }

    /* ── Metricas ── */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #221414, #2a1010);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 20px 16px;
        text-align: center;
        transition: all 0.3s;
    }
    [data-testid="stMetric"]:hover {
        border-color: rgba(225,112,85,0.4);
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(225,112,85,0.15);
    }
    [data-testid="stMetricLabel"] {
        color: #b08080 !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    [data-testid="stMetricValue"] {
        color: #e17055 !important;
        font-size: 1.9rem !important;
        font-weight: 800 !important;
    }

    /* ── Titulos de seccion ── */
    .seccion-titulo {
        font-size: 1.4rem;
        font-weight: 700;
        color: white;
        background: linear-gradient(135deg, #3d1515, #221414);
        border-left: 5px solid #e17055;
        border-radius: 0 10px 10px 0;
        padding: 14px 20px;
        margin: 2rem 0 1.2rem 0;
        box-shadow: 0 4px 15px rgba(225,112,85,0.1);
    }

    /* ── Separador ── */
    .separador {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, 
            transparent, #e1705544, #e1705588, #e1705544, transparent);
        margin: 2.5rem 0;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #140d0d; }
    ::-webkit-scrollbar-thumb { 
        background: #e1705555; 
        border-radius: 3px; 
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
# Servidor local para mapas completos
STATIC_PORT = 8502
STATIC_DIR  = tempfile.gettempdir()

def iniciar_servidor_estatico():
    os.chdir(STATIC_DIR)
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *args: None
    try:
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", STATIC_PORT), handler) as httpd:
            httpd.serve_forever()
    except OSError:
        pass  # Puerto ya en uso, servidor ya corriendo

if 'servidor_iniciado' not in st.session_state:
    t = threading.Thread(target=iniciar_servidor_estatico, daemon=True)
    t.start()
    st.session_state['servidor_iniciado'] = True

SHP      = os.path.join(BASE, 'data', 'mexico_simple.gpkg')
XLS      = os.path.join(BASE, 'data', 'Base de datos principal defunciones.xlsx')
CSV_2224 = os.path.join(BASE, 'data', 'datos_2022_2024.parquet')
CSV_2024 = os.path.join(BASE, 'data', 'datos_2020_2024.parquet')
CSV_2025 = os.path.join(BASE, 'data', 'datos_2025.parquet')

TEMPLATE  = "plotly_dark"
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
    """Carga defunciones desde el Excel segun las hojas del periodo."""
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
    """Carga defunciones desde el Parquet (para 2025)."""
    df = pd.read_parquet(ruta) if ruta.endswith('.parquet') else pd.read_csv(ruta)
    # Asegurar que todos los 32 estados aparezcan aunque tengan 0
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

# ==========================
# Defunciones por periodo
# ==========================
# 2020-2024: Hoja1 a Hoja5
def_2024 = cargar_defunciones_excel(['Hoja1','Hoja2','Hoja3','Hoja4','Hoja5'])
# 2022-2024: Hoja3 a Hoja5
def_2224 = cargar_defunciones_excel(['Hoja3','Hoja4','Hoja5'])
# 2025: desde CSV
def_2025 = cargar_defunciones_csv(CSV_2025)

# ==========================
# Funcion: mapa Folium
# ==========================
def hacer_mapa(gdf, col_valor, titulo, paleta, tooltip_alias, key_suffix):
    _, bins = pd.qcut(gdf[col_valor].dropna(), q=4, retbins=True, duplicates='drop')

    es_entero = gdf[col_valor].dropna().apply(lambda x: float(x) == int(x)).all()
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
    """Mapa con rangos fijos para 2025"""

    CAT_BAJO   = "Bajo (0)"
    CAT_MEDIO  = "Medio (1 - 5)"
    CAT_ALTO   = "Alto (6 - 10)"
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

    # Metricas
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Casos de Dengue",    f"{total_casos:,}")
    c2.metric("Defunciones",        f"{total_def:,}")
    c3.metric("IRM Promedio",       f"{irm_nacional:.3f}")
    c4.metric("Tasa Mortalidad",    f"{tasa_mortalidad:.2f}%")
    c5.metric("Estados Analizados", "32")
    c6.metric("Variables",          "16")

    st.markdown('<hr class="separador">', unsafe_allow_html=True)

    resumen_irm = df.groupby(['ENTIDAD_RES','ESTADO']).agg(
        irm_prom=('Indice_Riesgo','mean'),
    ).reset_index().sort_values('irm_prom', ascending=False)

    def_sexo = (df[df['DEFUNCION']==1]
                .groupby(['ESTADO','SEXO_LABEL'])
                .size().reset_index(name='muertes'))

    lista_estados = sorted(df['ESTADO'].dropna().unique().tolist())

# ==========================
    # SECCION DESCARGA
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
        import io
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

    # Filtros IRM
    fi1, fi2 = st.columns([3, 1])
    with fi1:
        estados_sel_irm = st.multiselect(
            "Filtrar estados:",
            options=lista_estados,
            default=[],
            placeholder="Todos los estados (sin filtro)",
            key=f"filtro_irm_{periodo}"
        )
    with fi2:
        años_disponibles = sorted(df['ANIO'].dropna().unique().astype(int).tolist())
        año_sel_irm = st.selectbox(
            "Año:",
            options=["Todos"] + años_disponibles,
            key=f"año_irm_{periodo}"
        )

    # Aplicar filtros al dataframe
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

    col1, col2 = st.columns(2)
    with col1:
        # Boton pantalla completa IRM
        # Guardar mapa IRM como HTML y abrir en nueva pestaña
        ruta_irm_full = os.path.join(STATIC_DIR, f'mapa_irm_full_{periodo}.html') 
        if not os.path.exists(ruta_irm_full):
            mapa_irm_temp = hacer_mapa(
                gdf_irm, 'irm_prom', 'IRM por Estado',
                COLOR_IRM, 'IRM Promedio:', f"irm_full_{periodo}")
            mapa_irm_temp.save(ruta_irm_full)
        st.markdown(
            f'<a href="http://localhost:8502/mapa_irm_full_{periodo}.html" '
            f'target="_blank" style="display:inline-block;background:linear-gradient'
            f'(135deg,#1a6fff,#0d4bcc);color:white;font-weight:700;padding:10px 22px;'
            f'border-radius:8px;text-decoration:none;font-size:0.9rem;margin-bottom:10px;'
            f'box-shadow:0 4px 15px rgba(26,111,255,0.3);">'
            f'&#x26F6; Ver Mapa IRM Completo</a>',
            unsafe_allow_html=True
        )

        mapa_irm = hacer_mapa(
            gdf_irm, 'irm_prom', 'IRM por Estado',
            COLOR_IRM, 'IRM Promedio:', f"irm_{periodo}")
        st_folium(mapa_irm, width=680, height=430,
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
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#0d1117',
            font_color='#e6edf3', font_family='Arial',
            margin=dict(l=10,r=10,t=40,b=10), bargap=0.15,
            title_font=dict(size=14, color='#58a6ff'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)',
                       zerolinecolor='rgba(255,255,255,0.1)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
        )
        st.plotly_chart(fig_irm, width='stretch',
                        key=f"graf_irm_{periodo}")

    st.markdown('<hr class="separador">', unsafe_allow_html=True)

    # ==========================
    # SECCION DEFUNCIONES
    # ==========================
    st.markdown('<div class="seccion-titulo">Defunciones Reales por Dengue</div>',
                unsafe_allow_html=True)

    # Filtros Defunciones
    fd1, fd2 = st.columns([3, 1])
    with fd1:
        estados_sel_def = st.multiselect(
            "Filtrar estados:",
            options=lista_estados,
            default=[],
            placeholder="Todos los estados (sin filtro)",
            key=f"filtro_def_{periodo}"
        )

    if estados_sel_def:
        df_def_graf = df_def[df_def['ESTADO'].isin(estados_sel_def)]
    else:
        df_def_graf = df_def

    gdf_def = gdf_base.merge(
        df_def[['ENTIDAD_RES','defunciones']], on='ENTIDAD_RES', how='left')

    col3, col4 = st.columns(2)
    with col3:
        # Boton pantalla completa Defunciones
        # Guardar mapa defunciones como HTML y abrir en nueva pestaña
        ruta_def_full = os.path.join(STATIC_DIR, f'mapa_def_full_{periodo}.html')
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
        st.markdown(
            f'<a href="http://localhost:8502/mapa_def_full_{periodo}.html" '
            f'target="_blank" style="display:inline-block;background:linear-gradient'
            f'(135deg,#c0392b,#922b21);color:white;font-weight:700;padding:10px 22px;'
            f'border-radius:8px;text-decoration:none;font-size:0.9rem;margin-bottom:10px;'
            f'box-shadow:0 4px 15px rgba(192,57,43,0.3);">'
            f'&#x26F6; Ver Mapa Defunciones Completo</a>',
            unsafe_allow_html=True
        )
        if periodo == "2025":
            mapa_def = hacer_mapa_rangos_fijos(
                gdf_def, 'defunciones', 'Defunciones por Estado',
                'Defunciones:', f"def_{periodo}")
        else:
            mapa_def = hacer_mapa(
                gdf_def, 'defunciones', 'Defunciones por Estado',
                COLOR_DEF, 'Defunciones:', f"def_{periodo}")
        st_folium(mapa_def, width=680, height=430,
                  returned_objects=[], key=f"mapa_def_{periodo}")

    with col4:
        altura_def = max(750, len(df_def_graf) * 25)
        fig_def = px.bar(
            df_def_graf.sort_values('defunciones', ascending=True),
            x='defunciones', y='ESTADO', orientation='h',
            color='defunciones', color_continuous_scale=COLOR_DEF,
            labels={'defunciones':'Defunciones','ESTADO':''},
            title=f'Defunciones Acumuladas por Estado ({periodo})',
            template=TEMPLATE
        )
        fig_def.update_layout(
            height=altura_def, coloraxis_showscale=False,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#0d1117',
            font_color='#e6edf3', font_family='Arial',
            margin=dict(l=10,r=10,t=40,b=10), bargap=0.15,
            title_font=dict(size=14, color='#58a6ff'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)',
                       zerolinecolor='rgba(255,255,255,0.1)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
        )
        st.plotly_chart(fig_def, width='stretch',
                        key=f"graf_def_{periodo}")

    st.markdown('<hr class="separador">', unsafe_allow_html=True)

    # ==========================
    # SECCION SEXO
    # ==========================
    st.markdown('<div class="seccion-titulo">Defunciones por Sexo y Estado</div>',
                unsafe_allow_html=True)

    # Filtro sexo
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
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#0d1117',
        font_color='#e6edf3', font_family='Arial',
        margin=dict(l=10,r=10,t=40,b=10), bargap=0.2,
        title_font=dict(size=14, color='#58a6ff'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)',
                   zerolinecolor='rgba(255,255,255,0.1)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        legend=dict(bgcolor='rgba(22,27,34,0.8)',
                    bordercolor='rgba(255,255,255,0.1)', borderwidth=1)
    )
    st.plotly_chart(fig_sexo, width='stretch',
                    key=f"graf_sexo_{periodo}")

# ==========================
# HERO
# ==========================
st.markdown("""
<div style="padding: 70px 0 5px 0; margin-bottom: 5px;">
    <div style="
        display: inline-block;
        background: linear-gradient(135deg, rgba(225,112,85,0.15), rgba(214,48,49,0.05));
        border: 1px solid rgba(225,112,85,0.3);
        color: #e17055;
        padding: 5px 16px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 12px;
        font-family: Arial, sans-serif;
    ">
        Salud Publica · Mexico · Dengue
    </div>
    <h1 style="
        font-size: 2.6rem;
        font-weight: 900;
        margin: 0;
        font-family: Arial, sans-serif;
        line-height: 1.2;
        background: linear-gradient(135deg, #ffffff 0%, #e17055 50%, #d63031 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    ">Indice de Riesgo de Mortalidad por Dengue</h1>
    <p style="
        color: #b08080;
        font-size: 1rem;
        margin-top: 8px;
        font-family: Arial, sans-serif;
    ">
        Analisis espacial · Variables climaticas, ambientales y sociodemograficas · México
    </p>
</div>
""", unsafe_allow_html=True)

# ==========================
# TABS POR PERIODO
# ==========================
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