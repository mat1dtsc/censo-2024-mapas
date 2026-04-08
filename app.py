# app.py - Censo de poblacion: proyecciones
# Replica de https://bastianoleah.shinyapps.io/censo_proyecciones/

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# -- Colores (mismos que el original) -----------------------------------------

COLOR_PRINCIPAL = "#365c8d"
COLOR_DESTACADO = "#3a87c8"
COLOR_FONDO = "#FFFFFF"
COLOR_NEGATIVO = "#e5084b"
COLOR_MASCULINO = "#964191"
COLOR_FEMENINO = "#5B4898"

# -- URLs de datos ------------------------------------------------------------

URL_PROYECCIONES = (
    "https://raw.githubusercontent.com/bastianolea/"
    "censo_proyecciones_poblacion/main/datos/datos_procesados/"
    "censo_proyecciones_a%C3%B1o.csv"
)
URL_PIRAMIDE = (
    "https://raw.githubusercontent.com/bastianolea/"
    "censo_proyecciones_poblacion/main/datos/datos_procesados/"
    "censo_proyecciones_a%C3%B1o_edad_genero.parquet"
)

# -- Configuracion de pagina --------------------------------------------------

st.set_page_config(
    page_title="Proyecciones Censo",
    page_icon="\U0001f4ca",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    f"""
    <style>
        .stApp {{ background-color: {COLOR_FONDO}; color: {COLOR_PRINCIPAL}; }}
        [data-testid="stSidebar"] {{ background-color: #f8f9fa; }}
        h1 {{ color: {COLOR_DESTACADO} !important; font-weight: bold !important; }}
        h2 {{ color: {COLOR_PRINCIPAL} !important; }}
        h3, h4 {{ color: {COLOR_PRINCIPAL} !important; }}
        p, li, span {{ color: {COLOR_PRINCIPAL}; }}
        .explicacion {{ font-size: 80%; line-height: 1.3; }}
        .stMetric label {{ color: {COLOR_PRINCIPAL} !important; }}
        .stMetric [data-testid="stMetricValue"] {{ color: {COLOR_PRINCIPAL} !important; }}
        hr {{ border-color: #e0e0e0 !important; }}
        [data-testid="stDataFrame"] {{ color: {COLOR_PRINCIPAL}; }}
        .stSelectbox label, .stMultiSelect label {{ color: {COLOR_DESTACADO} !important; font-size: 1.1rem !important; font-weight: 600 !important; }}
        .stSlider label {{ color: {COLOR_DESTACADO} !important; font-size: 1.1rem !important; font-weight: 600 !important; }}
        .footer-text {{ font-size: 80%; color: {COLOR_PRINCIPAL}; }}
        .footer-text a {{ color: {COLOR_DESTACADO}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -- Carga de datos ------------------------------------------------------------


@st.cache_data(ttl=3600)
def cargar_proyecciones():
    df = pd.read_csv(URL_PROYECCIONES, sep=";", index_col=0)
    df.columns = [
        "cut_region", "region", "cut_provincia", "provincia",
        "cut_comuna", "comuna", "año", "poblacion",
    ]
    return df


@st.cache_data(ttl=3600)
def cargar_piramide():
    df = pd.read_parquet(URL_PIRAMIDE)
    return df


with st.spinner("Descargando datos de proyecciones del INE..."):
    df = cargar_proyecciones()

años = sorted(df["año"].unique())
regiones_todas = sorted(df["region"].unique())

# -- Encabezado ----------------------------------------------------------------

st.title("Censo de poblacion: proyecciones")

st.markdown(
    'Visualizador de datos oficiales de proyecciones poblacionales realizadas por el '
    '[Instituto Nacional de Estadisticas](https://www.ine.gob.cl) de Chile'
)
st.markdown("*Bastian Olea Herrera*", unsafe_allow_html=True)

st.markdown(
    "Aplicacion web que visualiza los datos oficiales del "
    "[Instituto Nacional de Estadisticas](https://www.ine.gob.cl) de Chile sobre "
    "[proyecciones de poblacion](https://www.ine.gob.cl/estadisticas/sociales/"
    "demografia-y-vitales/proyecciones-de-poblacion); es decir, estimaciones del "
    "crecimiento poblacional hacia el futuro, a partir de los datos obtenidos en "
    "los censos oficiales."
)

st.divider()

# ==============================================================================
# SECCION 1: Evolucion regional
# ==============================================================================

col_graf_reg, col_tabla_reg = st.columns([7, 5])

with col_graf_reg:
    st.header("Evolucion de la poblacion regional")
    st.markdown(
        "En este grafico puedes analizar los cambios poblacionales proyectados "
        "para las regiones de Chile que elijas. Los puntos indican mediciones de "
        "poblacion realizadas por censos nacionales de poblacion y vivienda, "
        "mientras que el resto de las lineas representan proyecciones de dichas "
        "mediciones."
    )
    st.markdown(
        '<p class="explicacion">Selecciona una o mas regiones para incluirlas en el grafico.</p>',
        unsafe_allow_html=True,
    )

    regiones_sel = st.multiselect(
        "Regiones",
        regiones_todas,
        default=["Metropolitana de Santiago", "Valparaiso", "Biobio", "Maule"],
    )

if not regiones_sel:
    st.info("Selecciona al menos una region.")
    st.stop()

df_reg = df[df["region"].isin(regiones_sel)]

# Grafico regional
with col_graf_reg:
    df_reg_año = (
        df_reg.groupby(["region", "año"])["poblacion"]
        .sum()
        .reset_index()
    )
    df_reg_año["tipo"] = df_reg_año["año"].apply(
        lambda x: "censo" if x in [2002, 2017] else "proyeccion"
    )
    df_reg_año["opacidad"] = df_reg_año["año"].apply(
        lambda x: 1.0 if x <= 2017 else 0.4
    )

    fig_reg = px.line(
        df_reg_año,
        x="año",
        y="poblacion",
        color="region",
        markers=True,
    )

    fig_reg.add_vline(
        x=2024, line_width=2, line_color=COLOR_DESTACADO, opacity=0.4,
    )

    fig_reg.update_layout(
        paper_bgcolor=COLOR_FONDO,
        plot_bgcolor=COLOR_FONDO,
        font_color=COLOR_PRINCIPAL,
        legend_title_text="Regiones",
        legend_title_font_color=COLOR_DESTACADO,
        xaxis=dict(
            title="",
            gridcolor="#e8eaed",
            tickvals=[2002] + list(range(2005, 2036, 5)) + [2017],
            tickangle=-90,
            tickfont=dict(size=10),
        ),
        yaxis=dict(
            title="Poblacion residente proyectada",
            title_font_color=COLOR_DESTACADO,
            gridcolor="#e8eaed",
            tickfont=dict(size=10),
        ),
        height=450,
        margin=dict(l=60, r=20, t=20, b=60),
    )

    # Resaltar puntos censales
    for trace in fig_reg.data:
        region_name = trace.name
        df_trace = df_reg_año[df_reg_año["region"] == region_name]
        censo_mask = df_trace["año"].isin([2002, 2017])
        sizes = [10 if c else 5 for c in censo_mask]
        trace.marker.size = sizes

    st.plotly_chart(fig_reg, use_container_width=True)

# Tabla comparativa regional
with col_tabla_reg:
    st.header("Cambios en la poblacion regional")
    st.markdown(
        "Esta tabla detalla una lista de las regiones seleccionadas, con su "
        "poblacion correspondiente para los años que elijas, junto a el cambio "
        "porcentual entre ambas fechas."
    )
    st.markdown(
        '<p class="explicacion">Selecciona dos años para ajustar la comparacion entre poblaciones regionales.</p>',
        unsafe_allow_html=True,
    )

    año_range_reg = st.slider(
        "Seleccione dos años a comparar",
        min_value=int(min(años)),
        max_value=int(max(años)),
        value=(2002, 2023),
        key="slider_reg",
    )

    año_1_reg, año_2_reg = año_range_reg

    pob_1 = df_reg[df_reg["año"] == año_1_reg].groupby("region")["poblacion"].sum()
    pob_2 = df_reg[df_reg["año"] == año_2_reg].groupby("region")["poblacion"].sum()

    df_comp_reg = pd.DataFrame({
        "Region": pob_1.index,
        str(año_1_reg): pob_1.values,
        str(año_2_reg): pob_2.values,
    })
    df_comp_reg["% de cambio"] = (
        (df_comp_reg[str(año_2_reg)] - df_comp_reg[str(año_1_reg)])
        / df_comp_reg[str(año_2_reg)] * 100
    ).round(1)
    df_comp_reg = df_comp_reg.sort_values(str(año_2_reg), ascending=False)

    st.dataframe(
        df_comp_reg.style.format({
            str(año_1_reg): "{:,.0f}",
            str(año_2_reg): "{:,.0f}",
            "% de cambio": "{:+.1f}%",
        }),
        use_container_width=True,
        hide_index=True,
        height=400,
    )

st.divider()

# ==============================================================================
# SECCION 2: Evolucion comunal
# ==============================================================================

# Comunas disponibles segun regiones seleccionadas
comunas_disponibles = sorted(
    df[df["region"].isin(regiones_sel)]["comuna"].unique()
)

col_graf_com, col_tabla_com = st.columns([7, 5])

with col_graf_com:
    st.header("Evolucion de la poblacion comunal")
    st.markdown(
        "Visualizacion de los cambios poblacionales proyectados para las comunas del pais."
    )
    st.markdown(
        '<p class="explicacion">A partir de las regiones seleccionadas mas arriba, '
        "elige una o varias comunas que seran incluidas en el grafico.</p>",
        unsafe_allow_html=True,
    )

    comunas_default = [c for c in ["La Pintana", "Puente Alto", "Santiago", "Vitacura", "Independencia", "La Florida"]
                       if c in comunas_disponibles]

    comunas_sel = st.multiselect(
        "Comunas",
        comunas_disponibles,
        default=comunas_default[:6],
    )

if comunas_sel:
    df_com = df[df["comuna"].isin(comunas_sel)]

    with col_graf_com:
        df_com_año = (
            df_com.groupby(["comuna", "año"])["poblacion"]
            .sum()
            .reset_index()
        )

        fig_com = px.line(
            df_com_año,
            x="año",
            y="poblacion",
            color="comuna",
            markers=True,
        )

        fig_com.add_vline(
            x=2024, line_width=2, line_color=COLOR_DESTACADO, opacity=0.4,
        )

        fig_com.update_layout(
            paper_bgcolor=COLOR_FONDO,
            plot_bgcolor=COLOR_FONDO,
            font_color=COLOR_PRINCIPAL,
            legend_title_text="Comunas",
            legend_title_font_color=COLOR_DESTACADO,
            xaxis=dict(
                title="",
                gridcolor="#e8eaed",
                tickvals=[2002] + list(range(2005, 2036, 5)) + [2017],
                tickangle=-90,
                tickfont=dict(size=10),
            ),
            yaxis=dict(
                title="Poblacion residente proyectada",
                title_font_color=COLOR_DESTACADO,
                gridcolor="#e8eaed",
                tickfont=dict(size=10),
            ),
            height=450,
            margin=dict(l=60, r=20, t=20, b=60),
        )

        for trace in fig_com.data:
            comuna_name = trace.name
            df_trace = df_com_año[df_com_año["comuna"] == comuna_name]
            censo_mask = df_trace["año"].isin([2002, 2017])
            sizes = [10 if c else 5 for c in censo_mask]
            trace.marker.size = sizes

        st.plotly_chart(fig_com, use_container_width=True)

    with col_tabla_com:
        st.header("Cambios en la poblacion comunal")
        st.markdown(
            "Esta tabla detalla una lista de las comunas seleccionadas, con su "
            "poblacion correspondiente para los años que elijas, junto a el cambio "
            "porcentual entre ambas fechas."
        )
        st.markdown(
            '<p class="explicacion">Selecciona dos años para ajustar la comparacion entre poblaciones.</p>',
            unsafe_allow_html=True,
        )

        año_range_com = st.slider(
            "Seleccione dos años a comparar",
            min_value=int(min(años)),
            max_value=int(max(años)),
            value=(2002, 2023),
            key="slider_com",
        )

        año_1_com, año_2_com = año_range_com

        pob_1c = df_com[df_com["año"] == año_1_com].groupby("comuna")["poblacion"].sum()
        pob_2c = df_com[df_com["año"] == año_2_com].groupby("comuna")["poblacion"].sum()

        df_comp_com = pd.DataFrame({
            "Comuna": pob_1c.index,
            str(año_1_com): pob_1c.values,
            str(año_2_com): pob_2c.values,
        })
        df_comp_com["% de cambio"] = (
            (df_comp_com[str(año_2_com)] - df_comp_com[str(año_1_com)])
            / df_comp_com[str(año_2_com)] * 100
        ).round(1)
        df_comp_com = df_comp_com.sort_values(str(año_2_com), ascending=False)

        st.dataframe(
            df_comp_com.style.format({
                str(año_1_com): "{:,.0f}",
                str(año_2_com): "{:,.0f}",
                "% de cambio": "{:+.1f}%",
            }),
            use_container_width=True,
            hide_index=True,
            height=400,
        )

    st.divider()

else:
    with col_graf_com:
        st.info("Selecciona al menos una comuna para ver el grafico.")
    with col_tabla_com:
        st.header("Cambios en la poblacion comunal")
        st.info("Selecciona comunas para ver la tabla comparativa.")
    st.divider()

# ==============================================================================
# SECCION 3: Piramides poblacionales
# ==============================================================================

st.header("Piramides poblacionales")
st.markdown(
    "Vuelve a elegir una region y una comuna para poder visualizar su piramide "
    "poblacional, que corresponde a la distribucion de la poblacion de dicha "
    "comuna, pero separada en grupos de edad y genero."
)
st.markdown(
    '<p class="explicacion">Elige una region, luego una comuna de dicha region, '
    "y ajusta el año para ver las diferencias en las piramides poblacionales.</p>",
    unsafe_allow_html=True,
)

año_piramide = st.slider(
    "Año",
    min_value=int(min(años)),
    max_value=int(max(años)),
    value=2023,
    key="slider_piramide",
)

col_pir_reg, col_pir_com = st.columns(2)

with col_pir_reg:
    region_piramide = st.selectbox(
        "Region",
        regiones_todas,
        index=regiones_todas.index("Metropolitana de Santiago")
        if "Metropolitana de Santiago" in regiones_todas else 0,
        key="pir_region",
    )

comunas_piramide = sorted(
    df[df["region"] == region_piramide]["comuna"].unique()
)

with col_pir_com:
    comuna_default_idx = (
        comunas_piramide.index("Puente Alto")
        if "Puente Alto" in comunas_piramide else 0
    )
    comuna_piramide = st.selectbox(
        "Comuna",
        comunas_piramide,
        index=comuna_default_idx,
        key="pir_comuna",
    )

# Cargar datos de piramide
try:
    with st.spinner("Cargando datos por edad y genero..."):
        df_pir = cargar_piramide()

    # Grupos de edad
    bins = [-1, 5, 14, 19, 24, 29, 39, 49, 59, 69, 200]
    labels = ["0 a 5 años", "6 a 14 años", "15 a 19 años", "20 a 24 años",
              "25 a 29 años", "30 a 39 años", "40 a 49 años", "50 a 59 años",
              "60 a 69 años", "70 o mas años"]

    def hacer_piramide(df_filtro, titulo):
        if df_filtro.empty or "genero" not in df_filtro.columns or "edad" not in df_filtro.columns:
            st.warning("No hay datos disponibles para esta seleccion.")
            return

        df_filtro = df_filtro.copy()
        df_filtro["grupo_edad"] = pd.cut(
            df_filtro["edad"], bins=bins, labels=labels, ordered=True
        )

        df_agg = (
            df_filtro.groupby(["grupo_edad", "genero"], observed=True)["poblacion"]
            .sum()
            .reset_index()
        )

        masc = df_agg[df_agg["genero"].str.lower().str.contains("masculino|hombre|male")].copy()
        fem = df_agg[df_agg["genero"].str.lower().str.contains("femenino|mujer|female")].copy()

        if masc.empty or fem.empty:
            st.warning("No hay datos de genero disponibles.")
            return

        fig = go.Figure()

        fig.add_trace(go.Bar(
            y=masc["grupo_edad"].astype(str),
            x=masc["poblacion"],
            orientation="h",
            name="Masculino",
            marker_color=COLOR_MASCULINO,
            text=masc["poblacion"].apply(lambda x: f"{x:,.0f}"),
            textposition="outside",
            textfont=dict(size=9, color=COLOR_MASCULINO),
        ))

        fig.add_trace(go.Bar(
            y=fem["grupo_edad"].astype(str),
            x=-fem["poblacion"],
            orientation="h",
            name="Femenino",
            marker_color=COLOR_FEMENINO,
            text=fem["poblacion"].apply(lambda x: f"{x:,.0f}"),
            textposition="outside",
            textfont=dict(size=9, color=COLOR_FEMENINO),
        ))

        max_val = max(masc["poblacion"].max(), fem["poblacion"].max()) * 1.3

        fig.update_layout(
            title=dict(text=titulo, font=dict(color=COLOR_PRINCIPAL, size=14)),
            barmode="overlay",
            bargap=0.3,
            paper_bgcolor=COLOR_FONDO,
            plot_bgcolor=COLOR_FONDO,
            font_color=COLOR_PRINCIPAL,
            xaxis=dict(
                title="Poblacion por grupo de edad y genero",
                title_font_color=COLOR_DESTACADO,
                gridcolor="#e8eaed",
                range=[-max_val, max_val],
                tickvals=np.linspace(-max_val, max_val, 5),
                ticktext=[f"{abs(v):,.0f}" for v in np.linspace(-max_val, max_val, 5)],
            ),
            yaxis=dict(
                title="Categorias de edad",
                title_font_color=COLOR_DESTACADO,
                categoryorder="array",
                categoryarray=labels,
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.25,
                xanchor="center",
                x=0.5,
                title_text="Genero",
                title_font_color=COLOR_DESTACADO,
            ),
            height=450,
            margin=dict(l=20, r=80, t=40, b=80),
        )

        st.plotly_chart(fig, use_container_width=True)

    # Piramide regional
    with col_pir_reg:
        df_pir_reg = df_pir[
            (df_pir["region"] == region_piramide) & (df_pir["año"] == año_piramide)
        ]
        hacer_piramide(df_pir_reg, region_piramide)

    # Piramide comunal
    with col_pir_com:
        df_pir_com = df_pir[
            (df_pir["comuna"] == comuna_piramide) & (df_pir["año"] == año_piramide)
        ]
        hacer_piramide(df_pir_com, comuna_piramide)

except Exception as e:
    st.warning(f"No se pudieron cargar los datos de piramide poblacional: {e}")

# -- Footer --------------------------------------------------------------------

st.divider()

st.markdown(
    '<div class="footer-text">'
    "<p>Diseñado y programado por Bastian Olea Herrera.</p>"
    '<p>Puedes explorar sus otras <a href="https://bastianolea.github.io/shiny_apps/" target="_blank">'
    "aplicaciones interactivas sobre datos sociales en su portafolio.</a></p>"
    '<p>Fuente de los datos: <a href="https://www.ine.gob.cl/estadisticas/sociales/'
    'demografia-y-vitales/proyecciones-de-poblacion" target="_blank">'
    "Instituto Nacional de Estadisticas, Chile</a></p>"
    '<p>Codigo de fuente de esta app y de la obtencion de los datos '
    '<a href="https://github.com/bastianolea/censo_proyecciones_poblacion" target="_blank">'
    "disponibles en GitHub.</a></p>"
    "</div>",
    unsafe_allow_html=True,
)
