# app.py - Proyecciones de Poblacion Chile (Censo 2024)
# Dashboard de estimacion de demanda poblacional por region y comuna

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -- URLs de datos (GitHub, repo de Bastian Olea) ----------------------------

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

# -- Configuracion de pagina -------------------------------------------------

st.set_page_config(
    page_title="Proyecciones de Poblacion Chile",
    page_icon="\U0001f4ca",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .stApp { background-color: #111111; color: #e0e0e0; }
        [data-testid="stSidebar"] { background-color: #1a1a1a; }
        h1 { color: #cc44aa !important; }
        h2, h3 { color: #e0e0e0; }
        .stMetric label { color: #aaaaaa !important; }
        .stMetric [data-testid="stMetricValue"] { color: #e0e0e0 !important; }
        .stMetric [data-testid="stMetricDelta"] { font-size: 0.9rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -- Carga de datos -----------------------------------------------------------


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

# -- Sidebar ------------------------------------------------------------------

with st.sidebar:
    st.title("Proyecciones\nde Poblacion")
    st.markdown(
        "Estimaciones y proyecciones de poblacion 2002-2035 "
        "por region y comuna de Chile.\n\n"
        "Fuente: [INE Chile](https://www.ine.gob.cl/estadisticas/sociales/"
        "demografia-y-vitales/proyecciones-de-poblacion)"
    )

    regiones = sorted(df["region"].unique())
    regiones_sel = st.multiselect(
        "Regiones",
        regiones,
        default=["Metropolitana de Santiago"],
    )

    if regiones_sel:
        comunas_disponibles = sorted(
            df[df["region"].isin(regiones_sel)]["comuna"].unique()
        )
    else:
        comunas_disponibles = sorted(df["comuna"].unique())

    comunas_sel = st.multiselect(
        "Comunas (opcional, para detalle)",
        comunas_disponibles,
    )

    st.divider()

    años = sorted(df["año"].unique())
    col1, col2 = st.columns(2)
    año_base = col1.selectbox("Año base", años, index=años.index(2024))
    año_comp = col2.selectbox("Año comparar", años, index=años.index(2035))

# -- Filtros ------------------------------------------------------------------

if not regiones_sel:
    st.info("Selecciona al menos una region en el panel izquierdo.")
    st.stop()

df_reg = df[df["region"].isin(regiones_sel)]

# -- KPIs principales --------------------------------------------------------

st.header("Resumen de Poblacion")

pob_base = df_reg[df_reg["año"] == año_base].groupby("region")["poblacion"].sum()
pob_comp = df_reg[df_reg["año"] == año_comp].groupby("region")["poblacion"].sum()

cols = st.columns(len(regiones_sel))
for i, reg in enumerate(regiones_sel):
    base = pob_base.get(reg, 0)
    comp = pob_comp.get(reg, 0)
    delta = comp - base
    pct = (delta / base * 100) if base > 0 else 0
    cols[i].metric(
        reg,
        f"{comp:,.0f}",
        f"{delta:+,.0f} ({pct:+.1f}%) vs {año_base}",
    )

# -- Grafico: Evolucion regional ----------------------------------------------

st.header("Evolucion Poblacional por Region")

df_reg_año = (
    df_reg.groupby(["region", "año"])["poblacion"]
    .sum()
    .reset_index()
)

fig_reg = px.line(
    df_reg_año,
    x="año",
    y="poblacion",
    color="region",
    markers=True,
    color_discrete_sequence=px.colors.sequential.RdPu[2:],
)
fig_reg.update_layout(
    paper_bgcolor="#111111",
    plot_bgcolor="#1a1a1a",
    font_color="#e0e0e0",
    legend_title_text="Region",
    xaxis_title="Año",
    yaxis_title="Poblacion",
    height=450,
    xaxis=dict(gridcolor="#333333"),
    yaxis=dict(gridcolor="#333333"),
)
fig_reg.add_vline(x=2024, line_dash="dash", line_color="#cc44aa", opacity=0.5,
                  annotation_text="Censo 2024", annotation_font_color="#cc44aa")
st.plotly_chart(fig_reg, use_container_width=True)

# -- Tabla comparativa regional -----------------------------------------------

st.header(f"Comparacion Regional: {año_base} vs {año_comp}")

df_tabla_reg = pd.DataFrame({
    "Region": pob_base.index,
    f"Poblacion {año_base}": pob_base.values,
    f"Poblacion {año_comp}": pob_comp.values,
})
df_tabla_reg["Cambio"] = df_tabla_reg[f"Poblacion {año_comp}"] - df_tabla_reg[f"Poblacion {año_base}"]
df_tabla_reg["Cambio %"] = (
    df_tabla_reg["Cambio"] / df_tabla_reg[f"Poblacion {año_base}"] * 100
).round(1)
df_tabla_reg = df_tabla_reg.sort_values("Cambio %", ascending=False)

st.dataframe(
    df_tabla_reg.style.format({
        f"Poblacion {año_base}": "{:,.0f}",
        f"Poblacion {año_comp}": "{:,.0f}",
        "Cambio": "{:+,.0f}",
        "Cambio %": "{:+.1f}%",
    }),
    use_container_width=True,
    hide_index=True,
)

# -- Seccion comunal ----------------------------------------------------------

st.header("Detalle Comunal")

if not comunas_sel:
    # Mostrar top 10 comunas con mayor crecimiento en las regiones seleccionadas
    st.caption(
        "Selecciona comunas en el panel izquierdo para ver detalle. "
        "Mostrando las 10 comunas con mayor crecimiento proyectado."
    )
    df_com_base = df_reg[df_reg["año"] == año_base][["comuna", "poblacion"]].rename(
        columns={"poblacion": "pob_base"}
    )
    df_com_comp = df_reg[df_reg["año"] == año_comp][["comuna", "poblacion"]].rename(
        columns={"poblacion": "pob_comp"}
    )
    df_com_top = df_com_base.merge(df_com_comp, on="comuna")
    df_com_top["cambio_pct"] = (
        (df_com_top["pob_comp"] - df_com_top["pob_base"]) / df_com_top["pob_base"] * 100
    )
    df_com_top = df_com_top.nlargest(10, "cambio_pct")
    comunas_mostrar = df_com_top["comuna"].tolist()
else:
    comunas_mostrar = comunas_sel

df_com = df_reg[df_reg["comuna"].isin(comunas_mostrar)]

# Grafico comunal
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
    color_discrete_sequence=px.colors.qualitative.Set2,
)
fig_com.update_layout(
    paper_bgcolor="#111111",
    plot_bgcolor="#1a1a1a",
    font_color="#e0e0e0",
    legend_title_text="Comuna",
    xaxis_title="Año",
    yaxis_title="Poblacion",
    height=450,
    xaxis=dict(gridcolor="#333333"),
    yaxis=dict(gridcolor="#333333"),
)
fig_com.add_vline(x=2024, line_dash="dash", line_color="#cc44aa", opacity=0.5)
st.plotly_chart(fig_com, use_container_width=True)

# Tabla comunal
st.subheader(f"Tabla Comunal: {año_base} vs {año_comp}")

df_tc_base = df_com[df_com["año"] == año_base][["region", "comuna", "poblacion"]].rename(
    columns={"poblacion": f"Poblacion {año_base}"}
)
df_tc_comp = df_com[df_com["año"] == año_comp][["comuna", "poblacion"]].rename(
    columns={"poblacion": f"Poblacion {año_comp}"}
)
df_tabla_com = df_tc_base.merge(df_tc_comp, on="comuna")
df_tabla_com["Cambio"] = df_tabla_com[f"Poblacion {año_comp}"] - df_tabla_com[f"Poblacion {año_base}"]
df_tabla_com["Cambio %"] = (
    df_tabla_com["Cambio"] / df_tabla_com[f"Poblacion {año_base}"] * 100
).round(1)
df_tabla_com = df_tabla_com.rename(columns={"region": "Region", "comuna": "Comuna"})
df_tabla_com = df_tabla_com.sort_values("Cambio %", ascending=False)

st.dataframe(
    df_tabla_com.style.format({
        f"Poblacion {año_base}": "{:,.0f}",
        f"Poblacion {año_comp}": "{:,.0f}",
        "Cambio": "{:+,.0f}",
        "Cambio %": "{:+.1f}%",
    }),
    use_container_width=True,
    hide_index=True,
)

# -- Piramide poblacional -----------------------------------------------------

st.header("Piramide Poblacional")

try:
    with st.spinner("Cargando datos por edad y genero..."):
        df_pir = cargar_piramide()

    col_pir1, col_pir2 = st.columns(2)
    año_piramide = col_pir1.selectbox(
        "Año para piramide", años, index=años.index(2024), key="pir_año"
    )

    if comunas_sel:
        nivel_pir = col_pir2.selectbox("Nivel", ["Region", "Comuna"])
    else:
        nivel_pir = "Region"
        col_pir2.info("Selecciona comunas para ver piramides comunales")

    if nivel_pir == "Region" or not comunas_sel:
        df_pir_filtro = df_pir[
            (df_pir["region"].isin(regiones_sel)) & (df_pir["año"] == año_piramide)
        ]
        titulo_pir = ", ".join(regiones_sel)
    else:
        df_pir_filtro = df_pir[
            (df_pir["comuna"].isin(comunas_sel)) & (df_pir["año"] == año_piramide)
        ]
        titulo_pir = ", ".join(comunas_sel)

    if not df_pir_filtro.empty and "genero" in df_pir_filtro.columns and "edad" in df_pir_filtro.columns:
        df_pir_agg = (
            df_pir_filtro.groupby(["edad", "genero"])["poblacion"]
            .sum()
            .reset_index()
        )

        hombres = df_pir_agg[df_pir_agg["genero"].str.lower().str.contains("hombre|masculino|male")]
        mujeres = df_pir_agg[df_pir_agg["genero"].str.lower().str.contains("mujer|femenino|female")]

        fig_pir = go.Figure()
        fig_pir.add_trace(go.Bar(
            y=hombres["edad"],
            x=-hombres["poblacion"],
            orientation="h",
            name="Hombres",
            marker_color="#4a90d9",
        ))
        fig_pir.add_trace(go.Bar(
            y=mujeres["edad"],
            x=mujeres["poblacion"],
            orientation="h",
            name="Mujeres",
            marker_color="#cc44aa",
        ))
        fig_pir.update_layout(
            title=f"{titulo_pir} - {año_piramide}",
            barmode="overlay",
            bargap=0.1,
            paper_bgcolor="#111111",
            plot_bgcolor="#1a1a1a",
            font_color="#e0e0e0",
            xaxis=dict(
                title="Poblacion",
                gridcolor="#333333",
                tickvals=[-50000, -25000, 0, 25000, 50000],
                ticktext=["50k", "25k", "0", "25k", "50k"],
            ),
            yaxis=dict(title="Edad", gridcolor="#333333"),
            height=500,
        )
        st.plotly_chart(fig_pir, use_container_width=True)
    else:
        st.warning("No hay datos de piramide disponibles para esta seleccion.")

except Exception as e:
    st.warning(f"No se pudieron cargar los datos de piramide poblacional: {e}")

# -- Footer -------------------------------------------------------------------

st.divider()
st.caption(
    "Datos: [INE Chile - Proyecciones de Poblacion]"
    "(https://www.ine.gob.cl/estadisticas/sociales/demografia-y-vitales/"
    "proyecciones-de-poblacion) | "
    "Procesados por [Bastian Olea]"
    "(https://github.com/bastianolea/censo_proyecciones_poblacion)"
)
