import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Tótem IoT EAFIT",
    page_icon="💓",
    layout="wide",
)

CSV_FILE = "proyecto_integrador_eafit_max30102.csv"

REQUIRED_COLUMNS = {
    "timestamp",
    "student_id",
    "nfc_id",
    "device_id",
    "heart_rate_bpm",
    "spo2_percent",
    "signal_quality",
    "measurement_status",
}

# ---------- Estilo ----------
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.7rem; padding-bottom: 3rem;}
      [data-testid="stMetric"] {
        background: rgba(127,127,127,.08);
        border: 1px solid rgba(127,127,127,.18);
        padding: 14px;
        border-radius: 14px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Carga y preparación ----------
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(
            "Faltan columnas obligatorias: " + ", ".join(sorted(missing))
        )

    for col in ["student_id", "nfc_id", "device_id", "measurement_status"]:
        df[col] = df[col].astype(str).str.strip()

    df["measurement_status"] = df["measurement_status"].str.lower()

    for col in ["heart_rate_bpm", "spo2_percent", "signal_quality"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # El enunciado indica que timestamp viene en UTC.
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp"]).copy()

    # Conversión a hora local de Colombia.
    df["timestamp_local"] = df["timestamp"].dt.tz_convert("America/Bogota")
    df["fecha"] = df["timestamp_local"].dt.date
    df["hora"] = df["timestamp_local"].dt.hour
    df["dia_semana"] = df["timestamp_local"].dt.day_name()

    return df.sort_values("timestamp_local").reset_index(drop=True)


def fmt(value, decimals=1, suffix=""):
    if pd.isna(value):
        return "N/D"
    return f"{value:.{decimals}f}{suffix}"


def iqr_summary(series: pd.Series):
    s = series.dropna()
    if len(s) < 4:
        return 0, None, None
    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    count = int(((s < lower) | (s > upper)).sum())
    return count, lower, upper


try:
    df = load_data(CSV_FILE)
except FileNotFoundError:
    st.error(
        f"No encuentro `{CSV_FILE}`. Súbelo al repositorio junto a `app.py`."
    )
    st.stop()
except Exception as exc:
    st.error(f"No fue posible cargar los datos: {exc}")
    st.stop()

if df.empty:
    st.error("El archivo no contiene registros utilizables.")
    st.stop()

# ---------- Encabezado ----------
st.title("💓 Tótem IoT de monitoreo fisiológico — EAFIT")
st.write(
    "Exploración interactiva de mediciones sintéticas de frecuencia cardíaca, "
    "SpO₂, calidad de señal y patrones de utilización del tótem."
)
st.warning(
    "Todos los datos son simulados y se usan únicamente con fines académicos. "
    "Este dashboard no realiza diagnósticos médicos ni reemplaza una evaluación clínica."
)

# ---------- Filtros ----------
st.sidebar.header("🎛️ Filtros")

min_date = df["fecha"].min()
max_date = df["fecha"].max()

date_range = st.sidebar.date_input(
    "Rango de fechas",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range

student_options = sorted(df["student_id"].dropna().unique().tolist())
student_filter = st.sidebar.selectbox(
    "Estudiante",
    ["Todos"] + student_options,
)

status_options = sorted(df["measurement_status"].dropna().unique().tolist())
status_filter = st.sidebar.selectbox(
    "Estado de la medición",
    ["Todos"] + status_options,
)

# Base filtrada por período
period_df = df[
    (df["fecha"] >= start_date) & (df["fecha"] <= end_date)
].copy()

filtered = period_df.copy()

if student_filter != "Todos":
    filtered = filtered[filtered["student_id"] == student_filter]

if status_filter != "Todos":
    filtered = filtered[filtered["measurement_status"] == status_filter]

st.sidebar.caption(f"Registros visibles: {len(filtered):,} de {len(df):,}")

if filtered.empty:
    st.warning("No hay datos que coincidan con los filtros seleccionados.")
    st.stop()

# ---------- KPIs ----------
st.header("📌 Indicadores generales")

valid_filtered = filtered[
    filtered["measurement_status"] == "valid"
].copy()

total_measurements = len(filtered)
unique_students = filtered["student_id"].nunique()
avg_bpm = valid_filtered["heart_rate_bpm"].mean()
avg_spo2 = valid_filtered["spo2_percent"].mean()
invalid_count = int((filtered["measurement_status"] == "invalid").sum())
invalid_pct = (
    100 * invalid_count / total_measurements if total_measurements else 0
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Mediciones", f"{total_measurements:,}")
c2.metric("Estudiantes", f"{unique_students:,}")
c3.metric("BPM promedio válido", fmt(avg_bpm, 1, " bpm"))
c4.metric("SpO₂ promedio válido", fmt(avg_spo2, 1, " %"))
c5.metric("Mediciones inválidas", f"{invalid_pct:.1f} %")

st.caption(
    "Los promedios de BPM y SpO₂ se calculan únicamente con registros marcados como `valid`."
)

# ---------- Visualizaciones ----------
st.header("📊 Análisis visual")

# 1. Mediciones por día
daily = (
    filtered.groupby("fecha")
    .size()
    .reset_index(name="mediciones")
)

fig_daily = px.bar(
    daily,
    x="fecha",
    y="mediciones",
    title="1. Cantidad de mediciones por día",
    labels={"fecha": "Fecha", "mediciones": "Número de mediciones"},
)
fig_daily.update_layout(hovermode="x unified")
st.plotly_chart(fig_daily, use_container_width=True)

# 2. Horarios de uso
hourly = (
    filtered.groupby("hora")
    .size()
    .reindex(range(24), fill_value=0)
    .rename("mediciones")
    .reset_index()
)

fig_hourly = px.bar(
    hourly,
    x="hora",
    y="mediciones",
    title="2. Horarios de mayor utilización del tótem",
    labels={"hora": "Hora del día (Colombia)", "mediciones": "Mediciones"},
)
fig_hourly.update_xaxes(dtick=1)
st.plotly_chart(fig_hourly, use_container_width=True)

# 3-4. Distribuciones fisiológicas
st.subheader("Distribuciones de las mediciones válidas")
if valid_filtered.empty:
    st.info(
        "Con los filtros actuales no hay mediciones válidas para mostrar "
        "las distribuciones de BPM y SpO₂."
    )
else:
    left, right = st.columns(2)

    with left:
        fig_bpm = px.histogram(
            valid_filtered,
            x="heart_rate_bpm",
            nbins=30,
            title="3. Distribución de frecuencia cardíaca",
            labels={
                "heart_rate_bpm": "Frecuencia cardíaca (bpm)",
                "count": "Registros",
            },
        )
        st.plotly_chart(fig_bpm, use_container_width=True)

    with right:
        fig_spo2 = px.histogram(
            valid_filtered,
            x="spo2_percent",
            nbins=30,
            title="4. Distribución de SpO₂",
            labels={
                "spo2_percent": "SpO₂ estimada (%)",
                "count": "Registros",
            },
        )
        st.plotly_chart(fig_spo2, use_container_width=True)

# 5. Calidad del registro
status_counts = (
    filtered["measurement_status"]
    .value_counts()
    .rename_axis("estado")
    .reset_index(name="cantidad")
)

fig_status = px.pie(
    status_counts,
    names="estado",
    values="cantidad",
    hole=0.52,
    title="5. Distribución de mediciones válidas e inválidas",
)
st.plotly_chart(fig_status, use_container_width=True)

# 6. Relación BPM / SpO2 / señal
if not valid_filtered.empty:
    fig_scatter = px.scatter(
        valid_filtered,
        x="heart_rate_bpm",
        y="spo2_percent",
        color="signal_quality",
        hover_data=["student_id", "timestamp_local"],
        title="6. Relación entre BPM, SpO₂ y calidad de señal",
        labels={
            "heart_rate_bpm": "Frecuencia cardíaca (bpm)",
            "spo2_percent": "SpO₂ estimada (%)",
            "signal_quality": "Calidad señal",
        },
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# 7. Estudiantes con más mediciones
top_users = (
    filtered["student_id"]
    .value_counts()
    .head(10)
    .rename_axis("student_id")
    .reset_index(name="mediciones")
)

fig_users = px.bar(
    top_users,
    x="student_id",
    y="mediciones",
    title="7. Diez estudiantes con mayor número de mediciones",
    labels={"student_id": "Estudiante", "mediciones": "Mediciones"},
)
st.plotly_chart(fig_users, use_container_width=True)

# ---------- Hallazgos ----------
st.header("🔎 Hallazgos del período filtrado")

busiest_day_row = daily.loc[daily["mediciones"].idxmax()]
busiest_day = busiest_day_row["fecha"]
busiest_day_n = int(busiest_day_row["mediciones"])

busiest_hour_row = hourly.loc[hourly["mediciones"].idxmax()]
busiest_hour = int(busiest_hour_row["hora"])
busiest_hour_n = int(busiest_hour_row["mediciones"])

student_counts = filtered["student_id"].value_counts()
top_student = str(student_counts.index[0])
top_student_n = int(student_counts.iloc[0])

bpm_outliers, bpm_low, bpm_high = iqr_summary(
    valid_filtered["heart_rate_bpm"]
)
spo2_outliers, spo2_low, spo2_high = iqr_summary(
    valid_filtered["spo2_percent"]
)

h1, h2 = st.columns(2)

with h1:
    st.info(
        f"**Mayor uso diario:** el **{busiest_day}** se registraron "
        f"**{busiest_day_n} mediciones**, el máximo del período filtrado."
    )
    st.info(
        f"**Hora pico:** alrededor de las **{busiest_hour:02d}:00** "
        f"se concentraron **{busiest_hour_n} mediciones**."
    )

with h2:
    st.info(
        f"**Participación:** **{top_student}** es el estudiante con más "
        f"registros en el período, con **{top_student_n} mediciones**."
    )

    if valid_filtered.empty:
        st.info(
            f"**Calidad:** {invalid_pct:.1f}% de los registros filtrados "
            "están marcados como inválidos."
        )
    else:
        st.info(
            f"**Calidad y atípicos:** {invalid_pct:.1f}% de los registros "
            f"filtrados son inválidos. Con el criterio IQR aparecen "
            f"**{bpm_outliers} posibles atípicos en BPM** y "
            f"**{spo2_outliers} en SpO₂** entre las mediciones válidas."
        )

st.caption(
    "Los hallazgos son descriptivos y dependen de los filtros. "
    "Los valores atípicos sirven para revisar calidad de datos; "
    "no constituyen diagnósticos ni clasificaciones clínicas."
)

# ---------- Seguimiento individual ----------
st.header("👤 Seguimiento individual")

students_period = sorted(period_df["student_id"].dropna().unique().tolist())
selected_student = st.selectbox(
    "Selecciona un estudiante para consultar su histórico",
    students_period,
    key="individual_student",
)

student_df = period_df[
    period_df["student_id"] == selected_student
].copy()
student_valid = student_df[
    student_df["measurement_status"] == "valid"
].copy()

first_ts = student_df["timestamp_local"].min()
last_ts = student_df["timestamp_local"].max()

m1, m2, m3 = st.columns(3)
m1.metric("Identificador", selected_student)
m2.metric("Mediciones registradas", f"{len(student_df):,}")
m3.metric(
    "Período observado",
    f"{first_ts.strftime('%d/%m')} → {last_ts.strftime('%d/%m')}"
)

st.write(
    f"**Primera medición:** {first_ts.strftime('%d/%m/%Y %H:%M')}  |  "
    f"**Última medición:** {last_ts.strftime('%d/%m/%Y %H:%M')}"
)

if student_valid.empty:
    st.warning(
        "Este estudiante no tiene mediciones válidas en el período seleccionado."
    )
else:
    fig_student_bpm = px.line(
        student_valid,
        x="timestamp_local",
        y="heart_rate_bpm",
        markers=True,
        title=f"Evolución de frecuencia cardíaca — {selected_student}",
        labels={
            "timestamp_local": "Fecha y hora",
            "heart_rate_bpm": "BPM",
        },
    )
    st.plotly_chart(fig_student_bpm, use_container_width=True)

    fig_student_spo2 = px.line(
        student_valid,
        x="timestamp_local",
        y="spo2_percent",
        markers=True,
        title=f"Evolución de SpO₂ — {selected_student}",
        labels={
            "timestamp_local": "Fecha y hora",
            "spo2_percent": "SpO₂ estimada (%)",
        },
    )
    st.plotly_chart(fig_student_spo2, use_container_width=True)

# ---------- Calidad de datos ----------
st.header("🧹 Calidad de datos")

q1, q2, q3, q4 = st.columns(4)
q1.metric("Nulos BPM", int(filtered["heart_rate_bpm"].isna().sum()))
q2.metric("Nulos SpO₂", int(filtered["spo2_percent"].isna().sum()))
q3.metric(
    "Nulos calidad señal",
    int(filtered["signal_quality"].isna().sum())
)
q4.metric(
    "Calidad señal promedio",
    fmt(filtered["signal_quality"].mean(), 3)
)

with st.expander("Ver registros filtrados"):
    cols = [
        "timestamp_local",
        "student_id",
        "nfc_id",
        "device_id",
        "heart_rate_bpm",
        "spo2_percent",
        "signal_quality",
        "measurement_status",
    ]
    st.dataframe(
        filtered[cols],
        use_container_width=True,
        hide_index=True,
    )

with st.expander("ℹ️ Metodología y alcance"):
    st.markdown(
        """
        - El CSV se carga y procesa con **Pandas**.
        - Los timestamps originales están en UTC y se convierten a
          **America/Bogota** para analizar horarios locales.
        - Los promedios de BPM y SpO₂ se calculan únicamente con registros
          cuyo estado es `valid`.
        - Los filtros de fecha, estudiante y estado actualizan dinámicamente
          indicadores, gráficos y hallazgos.
        - Los posibles valores atípicos se cuentan con el criterio del rango
          intercuartílico (**IQR**) como herramienta exploratoria de calidad.
        - Los datos son sintéticos y el dashboard es académico; no debe
          utilizarse para realizar diagnósticos médicos.
        """
    )
