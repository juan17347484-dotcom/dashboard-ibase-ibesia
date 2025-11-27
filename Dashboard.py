import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ======== PALETA DE COLORES GLOBAL PARA PLOTLY ========
px.defaults.template = "simple_white"
px.defaults.color_discrete_sequence = [
    "#1F6FB2",  # azul principal
    "#20A5AA",  # turquesa / verde agua
    "#F5A623",  # naranja suave
    "#4A4A4A",  # gris oscuro
    "#9B9B9B"   # gris claro
]

# ======== CONFIGURACIÓN DE LA PÁGINA ========
st.set_page_config(
    page_title="Base Ibesia - Dashboard",
    layout="wide"
)

# ======== ESTILOS GLOBALES (FONDO, TIPOGRAFÍA, ETC.) ========
st.markdown(
    """
    <style>
    .main {
        background-color: #20A5AA;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    section[data-testid="stSidebar"] {
        background-color: #F5F7FB;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ======== ENCABEZADO CON UN SOLO LOGO + TÍTULO (VERTICAL) ========
with st.container():
    st.markdown(
        """
        <div style="
            background-color:#1F6FB2;
            padding:0.8rem 1rem;
            border-radius:10px;
            margin-bottom:1rem;
            text-align:center;
        ">
        """,
        unsafe_allow_html=True
    )

    # Logo centrado (asegúrate que el archivo exista en la carpeta)
    st.image("logo_principal.png", width=420)

    # Título y subtítulo debajo del logo
    st.markdown(
        """
        <h2 style='color:#1F6FB2;margin-bottom:0;font-size:32px;'>Dashboard - base de datos Ibesia</h2>
        <p style='color:#1F6FB2;margin-top:0;font-size:16px;'>
            Dashboard de seguimientos y pacientes
        </p>
        """,
        unsafe_allow_html=True
    )

    st.markdown("</div>", unsafe_allow_html=True)

# --------------------------
# Carga y limpieza de datos
# --------------------------

# Ruta del archivo Excel
DATA_FILE = "Datos prueba.xlsx"

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path)

    # limpiar nombres de columnas
    df.columns = df.columns.str.strip()

    # eliminar columna basura si existe
    if "Unnamed: 0" in df.columns:
        df = df.drop(columns=["Unnamed: 0"])

    # limpiar espacios y valores raros en columnas de texto
    for col in df.select_dtypes(include="object").columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .replace(
                {
                    "[NULL]": "No registrado",
                    "": "No registrado",
                }
            )
        )

    return df


path = Path(DATA_FILE)

if not path.exists():
    st.error(
        f"No encuentro el archivo **{DATA_FILE}**.\n\n"
        "Revisa la ruta en la variable DATA_FILE."
    )
    st.stop()

df = load_data(str(path))

# nombres de columnas que vamos a usar
COL_ESTADO = "Estado Real  1"
COL_TIPO_ESTADO = "Estado Real  2"
COL_PRESCRIPTOR = "prescriptor  HMLG"
COL_REGIONAL = "regional_ips"
COL_GENERO = "gender"
COL_EPS = "EPS1"

# --------------------------
# Filtros en la barra lateral
# --------------------------
st.sidebar.title("Filtros")

prescriptores = ["Todos"] + sorted(df[COL_PRESCRIPTOR].unique())
f_prescriptor = st.sidebar.selectbox("Prescriptor", prescriptores)

estados = ["Todos"] + sorted(df[COL_ESTADO].unique())
f_estado = st.sidebar.selectbox("Estado", estados)

tipos_estado = ["Todos"] + sorted(df[COL_TIPO_ESTADO].unique())
f_tipo_estado = st.sidebar.selectbox("Tipo de estado", tipos_estado)

generos = ["Todos"] + sorted(df[COL_GENERO].unique())
f_genero = st.sidebar.selectbox("Género", generos)

eps_list = ["Todos"] + sorted(df[COL_EPS].unique())
f_eps = st.sidebar.selectbox("EPS", eps_list)

regionales = ["Todos"] + sorted(df[COL_REGIONAL].unique())
f_regional = st.sidebar.selectbox("Regional de atención", regionales)

# Aplicar filtros
df_filtered = df.copy()

if f_prescriptor != "Todos":
    df_filtered = df_filtered[df_filtered[COL_PRESCRIPTOR] == f_prescriptor]
if f_estado != "Todos":
    df_filtered = df_filtered[df_filtered[COL_ESTADO] == f_estado]
if f_tipo_estado != "Todos":
    df_filtered = df_filtered[df_filtered[COL_TIPO_ESTADO] == f_tipo_estado]
if f_genero != "Todos":
    df_filtered = df_filtered[df_filtered[COL_GENERO] == f_genero]
if f_eps != "Todos":
    df_filtered = df_filtered[df_filtered[COL_EPS] == f_eps]
if f_regional != "Todos":
    df_filtered = df_filtered[df_filtered[COL_REGIONAL] == f_regional]

if df_filtered.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

# --------------------------
# KPIs (más ejecutivos)
# --------------------------
total_seguimientos = len(df_filtered)
total_pacientes = df_filtered.drop_duplicates().shape[0]

pct_activo = (
    (df_filtered[COL_ESTADO] == "Activo").mean() * 100
    if not df_filtered.empty
    else 0
)
pct_con_barrera = (
    (df_filtered[COL_TIPO_ESTADO] == "Con Barrera").mean() * 100
    if not df_filtered.empty
    else 0
)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Seguimientos", f"{total_seguimientos:,}".replace(",", "."))
kpi2.metric("Pacientes (aprox.)", f"{total_pacientes:,}".replace(",", "."))
kpi3.metric("% Activo", f"{pct_activo:.1f} %")
kpi4.metric("% Con barrera", f"{pct_con_barrera:.1f} %")

st.caption("Datos calculados sobre el subconjunto filtrado en la barra lateral.")
st.markdown("---")

# --------------------------
# Función de utilidad: Top N + 'Otros'
# --------------------------
def top_n_with_others(grouped_df, label_col, value_col, n=10):
    if len(grouped_df) <= n:
        return grouped_df
    top = grouped_df.nlargest(n, value_col).copy()
    others_val = grouped_df.iloc[n:][value_col].sum()
    others_row = {label_col: "Otros", value_col: others_val}
    top = pd.concat([top, pd.DataFrame([others_row])], ignore_index=True)
    return top

# --------------------------
# Tabs del dashboard
# --------------------------
tab_inicio, tab_info = st.tabs(["🏠 Inicio", "📊 Información"])

# --------------------------
# TAB 1 - INICIO
# --------------------------
with tab_inicio:
    st.subheader("Visión general por prescriptor y estado")

    col_left, col_right = st.columns([2, 1])

    # --- Gráfico: Registros por prescriptor (Top 10) ---
    with col_left:
        st.markdown("**Registros por prescriptor (Top 10)**")
        grup_prescriptor = (
            df_filtered.groupby(COL_PRESCRIPTOR)
            .size()
            .reset_index(name="Registros")
            .sort_values("Registros", ascending=False)
        )
        grup_prescriptor = top_n_with_others(
            grup_prescriptor, COL_PRESCRIPTOR, "Registros", n=10
        )

        fig_prescriptor = px.bar(
            grup_prescriptor,
            x="Registros",
            y=COL_PRESCRIPTOR,
            orientation="h",
            title=None,
            text_auto=True,
        )
        fig_prescriptor.update_layout(
            xaxis_title="Registros",
            yaxis_title="Prescriptor",
            height=500,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        fig_prescriptor.update_traces(
            marker_color="#1F6FB2",
            textposition="outside"
        )
        st.plotly_chart(fig_prescriptor, use_container_width=True)

    # --- Gráfico: Pacientes por estado ---
    with col_right:
        st.markdown("**Pacientes por estado**")
        grup_estado = (
            df_filtered.groupby(COL_ESTADO)
            .size()
            .reset_index(name="Registros")
            .sort_values("Registros", ascending=False)
        )

        color_estado_map = {
            "Activo": "#20A5AA",
            "Inactivo": "#4A4A4A",
            "No registrado": "#9B9B9B",
        }

        fig_estado = px.bar(
            grup_estado,
            x=COL_ESTADO,
            y="Registros",
            color=COL_ESTADO,
            color_discrete_map=color_estado_map,
            title=None,
            text_auto=True,
        )
        fig_estado.update_layout(
            xaxis_title="Estado",
            yaxis_title="Registros",
            showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        fig_estado.update_traces(textposition="outside")
        st.plotly_chart(fig_estado, use_container_width=True)

    # --- Gráfico: Tipo de estado (pie) ---
    st.markdown("### Distribución por tipo de estado")
    grup_tipo_estado = (
        df_filtered.groupby(COL_TIPO_ESTADO)
        .size()
        .reset_index(name="Registros")
        .sort_values("Registros", ascending=False)
    )

    color_tipo_estado_map = {
        "Con Barrera": "#F5A623",
        "Sin Barrera": "#1F6FB2",
        "Activo": "#20A5AA",
        "Inactivo": "#4A4A4A",
        "No registrado": "#9B9B9B",
    }

    fig_tipo_estado = px.pie(
        grup_tipo_estado,
        names=COL_TIPO_ESTADO,
        values="Registros",
        color=COL_TIPO_ESTADO,
        color_discrete_map=color_tipo_estado_map,
        hole=0.6,
        title=None,
    )
    fig_tipo_estado.update_traces(
        textposition="inside",
        textinfo="percent+label"
    )
    fig_tipo_estado.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig_tipo_estado, use_container_width=True)

# --------------------------
# TAB 2 - INFORMACIÓN
# --------------------------
with tab_info:
    st.subheader("Información por EPS, género y regional")

    col_eps, col_genero = st.columns(2)

    # --- Gráfico: Pacientes por EPS (Top 10) ---
    with col_eps:
        st.markdown("**Pacientes por EPS (Top 10)**")
        grup_eps = (
            df_filtered.groupby(COL_EPS)
            .size()
            .reset_index(name="Registros")
            .sort_values("Registros", ascending=False)
        )
        grup_eps = top_n_with_others(grup_eps, COL_EPS, "Registros", n=10)

        fig_eps = px.bar(
            grup_eps,
            x="Registros",
            y=COL_EPS,
            orientation="h",
            title=None,
            text_auto=True,
        )
        fig_eps.update_layout(
            xaxis_title="Registros",
            yaxis_title="EPS",
            height=500,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        fig_eps.update_traces(
            marker_color="#1F6FB2",
            textposition="outside"
        )
        st.plotly_chart(fig_eps, use_container_width=True)

    # --- Gráfico: Registros por género ---
    with col_genero:
        st.markdown("**Registros por género**")
        grup_genero = (
            df_filtered.groupby(COL_GENERO)
            .size()
            .reset_index(name="Registros")
            .sort_values("Registros", ascending=False)
        )

        color_genero_map = {
            "Femenino": "#1F6FB2",
            "Masculino": "#20A5AA",
            "Otro": "#F5A623",
            "No registrado": "#9B9B9B",
        }

        fig_genero = px.bar(
            grup_genero,
            x=COL_GENERO,
            y="Registros",
            color=COL_GENERO,
            color_discrete_map=color_genero_map,
            title=None,
            text_auto=True,
        )
        fig_genero.update_layout(
            xaxis_title="Género",
            yaxis_title="Registros",
            showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        fig_genero.update_traces(textposition="outside")
        st.plotly_chart(fig_genero, use_container_width=True)

    # --- Gráfico: Regional de atención (pie) ---
    st.markdown("### Registros por regional de atención")
    grup_regional = (
        df_filtered.groupby(COL_REGIONAL)
        .size()
        .reset_index(name="Registros")
        .sort_values("Registros", ascending=False)
    )

    fig_regional = px.pie(
        grup_regional,
        names=COL_REGIONAL,
        values="Registros",
        hole=0.6,
        title=None,
    )
    fig_regional.update_traces(
        textposition="inside",
        textinfo="percent+label"
    )
    fig_regional.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig_regional, use_container_width=True)

    st.markdown("### Detalle de registros filtrados")
    st.dataframe(df_filtered)