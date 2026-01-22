import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from pyproj import Transformer
import pydeck as pdk

# ==================================================
# 1. CONFIGURACIÓN Y ESTILO VISUAL
# ==================================================
st.set_page_config(
    page_title="Madrid 2024: Movilidad y Género",
    layout="wide",
    initial_sidebar_state="expanded"
)

COLOR_MAP_LESIVIDAD = {
    "Sin asistencia sanitaria": "LightSeaGreen",
    "Asistencia sanitaria sólo en el lugar del accidente": "DarkSeaGreen",
    "Asistencia sanitaria ambulatoria con posterioridad": "GoldenRod",
    "Atención en urgencias sin posterior ingreso": "SandyBrown",
    "Ingreso inferior o igual a 24 horas": "Tomato",
    "Ingreso superior a 24 horas": "FireBrick",
    "Fallecido 24 horas": "Black",
    "Se desconoce": "Silver"
}

st.markdown("""
    <style>
    h1 { font-family: 'Helvetica Neue', sans-serif; color: Black; font-size: 2.5rem; }
    h2 { color: Crimson; border-bottom: 2px solid Crimson; padding-bottom: 10px; margin-top: 3rem; }
    .subtitle { font-size: 1.2rem; color: LightGray; margin-bottom: 2rem; font-style: italic; }

    .narrative-box {
        background-color: #262730;
        padding: 20px;
        border-radius: 8px;
        border-left: 5px solid Crimson;
        font-size: 1.1rem;
        line-height: 1.6;
        color: WhiteSmoke !important;
        margin-bottom: 20px;
        box-shadow: 0 2px 4px LightGray;
    }

    .gender-box {
        background-color: LavenderBlush;
        border-left: 5px solid MediumVioletRed;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
        color: Black !important;
    }

    .insight-text {
        font-size: 0.95rem;
        color: Black !important;
        background-color: White;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid LightGray;
        margin-top: 10px;
        box-shadow: 0 1px 3px LightGray;
    }

    .kpi-card {
        background-color: White;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 5px LightGray;
        border-top: 3px solid SteelBlue;
    }
    .kpi-num { font-size: 1.8rem; font-weight: bold; color: MidnightBlue; }
    .kpi-label { font-size: 0.9rem; color: #262730; text-transform: uppercase; letter-spacing: 1px;}

    .sidebar-text { font-size: 0.9rem; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# ==================================================
# 2. CARGA DE DATOS
# ==================================================
@st.cache_data
def load_data():
    base_dir = Path(__file__).resolve().parent
    data_path = base_dir / "2024_Accidentalidad.csv"
    if not data_path.exists():
        data_path = base_dir / "data" / "2024_Accidentalidad.csv"

    if not data_path.exists():
        st.error("No se encuentra el dataset. Verifica la ruta.")
        st.stop()

    df = pd.read_csv(data_path, sep=";", encoding="utf-8-sig", low_memory=False)

    df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True)
    df["hora_dt"] = pd.to_datetime(df["hora"], format="%H:%M:%S", errors="coerce")
    df["hora_num"] = df["hora_dt"].dt.hour

    dias_map = {"Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles", "Thursday": "Jueves",
                "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"}
    df["dia_semana"] = df["fecha"].dt.day_name().map(dias_map)

    orden = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    df["dia_semana"] = pd.Categorical(df["dia_semana"], categories=orden, ordered=True)

    transformer = Transformer.from_crs("EPSG:25830", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(df["coordenada_x_utm"].values, df["coordenada_y_utm"].values)
    df["lon"] = lon
    df["lat"] = lat

    df['alcohol'] = df['positiva_alcohol'] == 'S'
    df['rango_edad'] = df['rango_edad'].replace({'Más de 74 años': '> 74'})

    df['lesividad'] = df['lesividad'].fillna("Se desconoce")

    return df

df = load_data()

# ==================================================
# SIDEBAR COMPLETA (CONTEXTO Y DATOS)
# ==================================================
with st.sidebar:

    st.markdown("### Sobre este informe")

    st.info("""
    **Monitor de Movilidad Urbana**

    Vamos a repasar mediante esta web los tres ejes claves en la sinistralidad:

    * **Salud Pública:** Severidad y reincidencia.
    * **Urbanismo:** Puntos calientes y flujos.
    * **Impacto Social:** Brecha de género y vulnerabilidades.
    """)

    st.markdown("---")
    st.markdown("#### Origen de datos")
    st.markdown("""
    * **Fuente:** [Portal de datos abiertos del ayuntamiento de Madrid](https://datos.madrid.es/portal/site/egob)
    * **Alcance:** Totalidad del año 2024.
    * **Análisis:** Enero 2026.
    """)

    st.markdown("---")
    st.caption("Desarrollado por Alberto Fernández Gálvez")

# ==================================================
# INTRODUCCIÓN Y MOTIVACIÓN
# ==================================================

st.title("Radiografía del tráfico en Madrid")
st.markdown('<div class="subtitle">Patrones de riesgo y brecha de género.</div>', unsafe_allow_html=True)
st.markdown("""
<style>
.narrative-box {
    background-color: #262730;
    padding: 20px;
    border-radius: 8px;
    border-left: 5px solid Crimson;
    font-size: 1.1rem;
    line-height: 1.6;
    color: WhiteSmoke !important;
    margin-bottom: 20px;
    box-shadow: 0 4px 6px Black;
}
.narrative-box h3 {
    color: White !important;
    margin-top: 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="narrative-box">
    <h3>Motivación del proyecto</h3>
    <p>
        La seguridad vial es un desafío fundamental de salud pública y bienestar social. En una gran ciudad como Madrid,
        la convivencia entre vehículos, peatones y nuevas formas de movilidad genera una complejidad que requiere análisis detallados.
    </p>
    <p>
        En este relato visual vamos a explorar los datos de 2024 para entender el impacto social de los siniestros, desde la
        vulnerabilidad de los peatones hasta la influencia del ocio nocturno, buscando patrones que ayuden a comprender la realidad de nuestra movilidad urbana.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("### Cifras clave del año")

st.markdown("""
<style>
    .kpi-card {
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px LightGray;
        margin-bottom: 10px;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .kpi-num { font-size: 2rem; font-weight: 700; margin-bottom: 5px; }
    .kpi-label { font-size: 0.9rem; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; opacity: 0.8; }
</style>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

total_personas = len(df)
media_diaria = int(total_personas / 366)
distrito_top = df['distrito'].mode()[0]
graves_count = len(df[df['lesividad'].isin(['Ingreso superior a 24 horas', 'Fallecido 24 horas'])])

with col1:
    st.markdown(f"""
        <div class="kpi-card" style="background-color: AliceBlue; border-left: 5px solid SteelBlue; color: MidnightBlue;">
            <div class="kpi-num">{total_personas:,}</div>
            <div class="kpi-label">Personas implicadas</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="kpi-card" style="background-color: MintCream; border-left: 5px solid LightSeaGreen; color: DarkSlateGray;">
            <div class="kpi-num">{media_diaria}</div>
            <div class="kpi-label">Media diaria</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class="kpi-card" style="background-color: Cornsilk; border-left: 5px solid GoldenRod; color: SaddleBrown;">
            <div class="kpi-num" style="font-size: 1.4rem;">{distrito_top}</div>
            <div class="kpi-label">Distrito + Incidencia</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
        <div class="kpi-card" style="background-color: LavenderBlush; border-left: 5px solid FireBrick; color: DarkRed;">
            <div class="kpi-num">{graves_count}</div>
            <div class="kpi-label">Casos gravedad alta</div>
        </div>
    """, unsafe_allow_html=True)

st.write("")

# ==================================================
# 1. MAPA DE ACCIDENTES
# ==================================================
st.markdown("## 1. La huella urbana del riesgo")

c1_txt, c1_viz = st.columns([1, 3])

with c1_txt:
    st.write("")
    st.write("")
    st.markdown("""
    <div style="background-color: #262730; padding: 15px; border-radius: 8px; border-left: 5px solid Crimson; color: Gainsboro; box-shadow: 0 4px 6px Black;">
        <h4 style="margin: 0 0 10px 0; color: White; font-size: 1.1rem;">Dinámica urbana</h4>
        <p style="font-size: 0.95rem; line-height: 1.5; margin-bottom: 0;">
            El riesgo no es estático, el tráfico se mueve y durante las diferentes horas migra del centro a la periferia y viceversa.
            <br><br>
            Moviendo el slider podemos ver cómo se transforma el mapa de calor.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    escenario = st.radio(
        "Filtro por tipo de accidente:",
        ["Todo el tráfico", "Sólo graves o mortales", "Sólo atropellos"],
        index=0
    )

    hora_mapa = st.slider("Filtro por hora del día:", 0, 23, 19, format="%dh")

    if escenario == "Sólo graves o mortales":
        st.caption("Mostrando solo ingresos >24h o fallecidos.")
    elif escenario == "Sólo atropellos":
        st.caption("Mostrando zonas de conflicto vehículo-peatón.")

with c1_viz:
    st.write("")
    df_map = df[df["hora_num"] == hora_mapa].dropna(subset=["lat", "lon"])

    if escenario == "Sólo graves o mortales":
        graves = ['Ingreso superior a 24 horas', 'Fallecido 24 horas']
        df_map = df_map[df_map['lesividad'].isin(graves)]
    elif escenario == "Sólo atropellos":
        df_map = df_map[df_map['tipo_persona'] == 'Peatón']

    if df_map.empty:
        st.warning(f"No hay datos para esta hora con el filtro '{escenario}'. Prueba otra hora.")
    else:
        view_state = pdk.ViewState(latitude=40.4168, longitude=-3.7038, zoom=11, pitch=45)
        layer = pdk.Layer(
            "HexagonLayer",
            data=df_map,
            get_position="[lon, lat]",
            radius=120,
            elevation_scale=4,
            elevation_range=[0, 1000],
            extruded=True,
            pickable=True,
            opacity=0.8,
            color_range=[[255, 255, 178], [254, 204, 92], [253, 141, 60], [240, 59, 32], [189, 0, 38]]
        )
        st.pydeck_chart(pdk.Deck(
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
            initial_view_state=view_state,
            layers=[layer],
            tooltip={"html": f"<b>{escenario}</b><br/>En este hexágono: <b>{{elevationValue}}</b> afectados.", "style": {"color": "white"}}
        ))

st.markdown("""
<div style="background-color: #262730; padding: 15px; border-radius: 8px; border-left: 5px solid GoldenRod; color: Gainsboro;">
    <span style="color: GoldenRod; font-weight: bold; font-size: 1rem;">Lectura de datos</span>
    <p style="margin-top: 5px; font-size: 0.9rem; line-height: 1.4; color: LightGray;">
        La densidad de incidentes satura la almendra central, barrios como Chamberí, Centro, Salamanca se saturan de accidentes
        en horario comercial. Por otro lado, en los anillos que rodean la ciudad, los accidentes más graves destacan, por el aumento de
        la velocidad.
    </p>
</div>
""", unsafe_allow_html=True)

# ==================================================
# 2. ALCOHOL EN FIN DE SEMANA
# ==================================================
st.markdown("## 2. Factor de riesgo: Alcohol y ocio")

c_alc1, c_alc2 = st.columns([1, 2])

with c_alc1:
    st.write("")
    st.write("")

    st.markdown("""
    <div style="background-color: #262730; padding: 15px; border-radius: 8px; border-left: 5px solid Crimson; color: Gainsboro; box-shadow: 0 4px 6px Black;">
        <h4 style="margin: 0 0 10px 0; color: White; font-size: 1.1rem;">Alcohol y ocio nocturo</h4>
        <p style="font-size: 0.95rem; line-height: 1.5; margin-bottom: 0;">
            Existe una tendencia a la accidentalidad cuando la vida se vincula al alcohol. Si visualizamos sólo los fines de
            semana podemos evidenciar picos de actividad y con ello de accidentabilidad.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    dias_posibles = ["Viernes", "Sábado", "Domingo"]
    dias_sel = st.multiselect("Filtro por día de la semana (activar o desactivar días):", options=dias_posibles, default=dias_posibles)

with c_alc2:

    df_alc = df[(df["alcohol"] == True) & (df["dia_semana"].isin(dias_sel))].copy()
    df_alc["dia_semana"] = df_alc["dia_semana"].cat.remove_unused_categories()

    if not df_alc.empty:
        counts = df_alc.groupby(["hora_num", "dia_semana"], observed=True).size().reset_index(name="n")

        fig_alc = px.line(
            counts, x="hora_num", y="n", color="dia_semana",
            title="Evolución horaria de positivos en alcohol",
            markers=True,
            labels={"hora_num": "Hora del día", "n": "Nº Positivos", "dia_semana": "Día"},
            color_discrete_map={"Viernes": "MediumSlateBlue", "Sábado": "Orange", "Domingo": "MediumSeaGreen"}
        )
        fig_alc.update_layout(xaxis=dict(tickmode='linear', dtick=2))

        fig_alc.update_traces(
            hovertemplate="<b>Hora:</b> %{x}:00 h<br><b>Día:</b> %{fullData.name}<br><b>Detecciones:</b> %{y} conductores positivos<extra></extra>"
        )

        st.plotly_chart(fig_alc, use_container_width=True)
    else:
        st.info("Selecciona un día del fin de semana para visualizar los datos.")

st.markdown("""
<div style="background-color: #262730; padding: 15px; border-radius: 8px; border-left: 5px solid GoldenRod; color: Gainsboro;">
    <span style="color: GoldenRod; font-weight: bold; font-size: 1rem;">Lectura de datos</span>
    <p style="margin-top: 5px; font-size: 0.9rem; line-height: 1.4; color: LightGray;">
        Se puede apreciar cómo el pico de riesgo se desplaza hacia la madrugada, correlacionando el cierre de locales de ocio con la siniestralidad.
    </p>
</div>
""", unsafe_allow_html=True)
# ==================================================
# 3. VULNERABILIDAD (TODOS LOS VEHÍCULOS)
# ==================================================
st.markdown("## 3. Vulnerabilidad según vehículo")

col_v1, col_v2 = st.columns([1, 3])

with col_v1:
    st.write("")
    st.write("")

    st.markdown("""
    <div style="background-color: #262730; padding: 15px; border-radius: 8px; border-left: 5px solid Crimson; color: Gainsboro; box-shadow: 0 4px 6px Black;">
        <h4 style="margin: 0 0 10px 0; color: White; font-size: 1.1rem;">Fragilidad en la vía</h4>
        <p style="font-size: 0.95rem; line-height: 1.5; margin-bottom: 0;">
            ¿Quién se lleva la peor parte? Analizamos la severidad del impacto según el medio de transporte.
            <br><br>
            Leyenda: De tonos verdes (Leve) a rojos/negros (Grave/Mortal).
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    todos_los_vehiculos = sorted(df["tipo_vehiculo"].dropna().unique())
    seleccion_defecto = ["Turismo", "Motocicleta > 125cc", "Bicicleta", "Peatón", "VMU eléctrico"]

    vehiculos_sel = st.multiselect(
        "Selecciona vehículos:",
        options=todos_los_vehiculos,
        default=[v for v in seleccion_defecto if v in todos_los_vehiculos]
    )

with col_v2:
    if vehiculos_sel:
        df_vul = df[df["tipo_vehiculo"].isin(vehiculos_sel)]

        orden_lesividad = list(COLOR_MAP_LESIVIDAD.keys())

        fig_vul = px.histogram(
            df_vul,
            y="tipo_vehiculo",
            color="lesividad",
            barnorm="percent",
            orientation='h',
            title="Comparativa de gravedad de lesiones por vehículo",
            text_auto='.0f',
            color_discrete_map=COLOR_MAP_LESIVIDAD,
            category_orders={"lesividad": orden_lesividad},
            labels={"tipo_vehiculo": "", "count": "Porcentaje"}
        )
        fig_vul.update_layout(xaxis_title="Porcentaje (%)", legend_title="Grado de lesividad")

        fig_vul.update_traces(
            hovertemplate="<b>Vehículo:</b> %{y}<br><b>Consecuencia:</b> %{fullData.name}<br><b>Frecuencia:</b> %{x:.2f}% del total<extra></extra>"
        )

        st.plotly_chart(fig_vul, use_container_width=True)

st.markdown("""
<div style="background-color: #262730; padding: 15px; border-radius: 8px; border-left: 5px solid GoldenRod; color: Gainsboro;">
    <span style="color: GoldenRod; font-weight: bold; font-size: 1rem;">Lectura de datos</span>
    <p style="margin-top: 5px; font-size: 0.9rem; line-height: 1.4; color: LightGray;">
        El gráfico revela la "protección de la carrocería": el Turismo presenta mayoritariamente tonos verdes (ilesos/leves).
        En contraste, Motocicletas y VMU muestran franjas anaranjadas y rojas mucho más anchas, evidenciando que cuando no hay chasis, la probabilidad de hospitalización se dispara.
    </p>
</div>
""", unsafe_allow_html=True)

# ==================================================
# 4. GÉNERO Y EDAD
# ==================================================
st.markdown("## 4. Perspectiva de género y demografía")
st.write("")
st.write("")
st.markdown("""
<div style="background-color: #262730; padding: 15px; border-radius: 8px; border-left: 5px solid Crimson; color: Gainsboro; box-shadow: 0 4px 6px Black;">
    <h4 style="margin: 0 0 10px 0; color: White; font-size: 1.1rem;">Sociología de la movilidad</h4>
    <p style="font-size: 0.95rem; line-height: 1.5; margin-bottom: 0;">
        La movilidad urbana no es neutra. Los datos reflejan patrones culturales profundos:
        la <em>"movilidad del cuidado"</em> (trayectos cortos, a pie, mayormente mujeres)
        frente a la <em>"movilidad pendular"</em> (coche/moto, velocidad, mayormente hombres).
    </p>
</div>
""", unsafe_allow_html=True)

st.write("")

tab_gen1, tab_gen2 = st.tabs(["Brecha de géneros", "Pirámide demográfica"])

with tab_gen1:
    st.write("")
    c_g1, c_g2 = st.columns(2)
    df_sex = df[df["sexo"].isin(["Hombre", "Mujer"])]

    with c_g1:
        st.markdown("### Patrones de movilidad")

        fig_generos = px.histogram(
            df_sex, x="sexo", color="tipo_persona",
            barnorm="percent", text_auto='.0f',
            title="¿Quién conduce y quién camina?",
            color_discrete_map={"Conductor": "DarkSlateGray", "Peatón": "GoldenRod", "Pasajero": "Teal"},
            labels={"sexo": "Género", "tipo_persona": "Rol"}
        )

        fig_generos.update_layout(
            xaxis_title="Género",
            yaxis_title="Porcentaje (%)",
            legend_title="Rol en la vía"
        )

        fig_generos.update_traces(
            hovertemplate="<b>Género:</b> %{x}<br><b>Tipo:</b> %{fullData.name}<br><b>Proporción:</b> %{y:.2f}%<extra></extra>"
        )
        st.plotly_chart(fig_generos, use_container_width=True)

        st.write("")
        st.markdown("""
        <div style="background-color: #262730; padding: 15px; border-radius: 8px; border-left: 5px solid GoldenRod; color: Gainsboro;">
            <span style="color: GoldenRod; font-weight: bold; font-size: 0.95rem;">Insight:</span>
            <p style="margin-top: 5px; font-size: 0.9rem; line-height: 1.4; color: LightGray;">
                Observa la barra amarilla (Peatones). Proporcionalmente, las mujeres sufren más atropellos, indicando una mayor exposición en desplazamientos a pie.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with c_g2:
        st.markdown("### Severidad del accidente")

        graves = ['Ingreso superior a 24 horas', 'Ingreso inferior o igual a 24 horas', 'Fallecido 24 horas']
        df_graves = df_sex[df_sex['lesividad'].isin(graves)]

        fig_pie = px.pie(
            df_graves, names="sexo",
            title="Proporción en accidentes graves (hospitalización)",
            color="sexo",
            color_discrete_map={"Hombre": "SteelBlue", "Mujer": "Crimson"},
            hole=0.4
        )
        fig_pie.update_traces(
            hovertemplate="<b>Grupo:</b> %{label}<br><b>Impacto grave:</b> %{value} personas<br><b>Porcentaje:</b> %{percent:.2%}<extra></extra>"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        st.write("")
        st.markdown("""
        <div style="background-color: #262730; padding: 15px; border-radius: 8px; border-left: 5px solid GoldenRod; color: Gainsboro;">
            <span style="color: GoldenRod; font-weight: bold; font-size: 0.95rem;">Dato clínico:</span>
            <p style="margin-top: 5px; font-size: 0.9rem; line-height: 1.4; color: LightGray;">
                Los hombres representan la mayoría de los ingresos graves. Esto correlaciona con el uso de vehículos de riesgo (motos) y conductas de velocidad.
            </p>
        </div>
        """, unsafe_allow_html=True)

with tab_gen2:
    st.write("")
    st.markdown("### Perfil de edad de los afectados")

    y_age = sorted(df["rango_edad"].dropna().unique())
    df_m = df[df['sexo']=='Hombre'].groupby('rango_edad').size().reindex(y_age, fill_value=0)
    df_f = df[df['sexo']=='Mujer'].groupby('rango_edad').size().reindex(y_age, fill_value=0)

    fig_pyr = go.Figure()

    fig_pyr.add_trace(go.Bar(
        y=y_age, x=df_m*-1, name='Hombres', orientation='h',
        marker_color='SteelBlue', customdata=df_m,
        hovertemplate="<b>Rango:</b> %{y}<br><b>Hombres:</b> %{customdata}<extra></extra>"
    ))

    fig_pyr.add_trace(go.Bar(
        y=y_age, x=df_f, name='Mujeres', orientation='h',
        marker_color='Crimson',
        hovertemplate="<b>Rango:</b> %{y}<br><b>Mujeres:</b> %{x}<extra></extra>"
    ))

    fig_pyr.update_layout(
        title="Pirámide de edad (Izquierda: Hombres | Derecha: Mujeres)",
        barmode='overlay',
        xaxis=dict(tickmode='sync', title='Nº Personas'),
        yaxis=dict(title='Edad'),
        legend=dict(x=0, y=1.0),
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_pyr, use_container_width=True)

    st.markdown("---")

    st.markdown("""
    <div style="background-color: #262730; padding: 15px; border-radius: 8px; border-left: 5px solid GoldenRod; color: Gainsboro;">
        <h5 style="margin: 0 0 10px 0; color: GoldenRod; font-size: 1rem;">Interpretación demográfica</h5>
        <ul style="font-size: 0.9rem; line-height: 1.6; color: LightGray; margin-bottom: 0;">
            <li>Pico laboral (25-45 años): El grueso de la siniestralidad ocurre en edad activa probablemente en desplazamientos al trabajo.</li>
            <li>Los mayores (>65 años): Sufren una incidencia desproporcionada, casi siempre asociada a atropellos graves.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
# ==================================================
# FOOTER
# ==================================================
st.divider()
st.caption("Alberto Fernández Gálvez | 22.531 - Visualización de datos | Universitat Oberta de Catalunya (UOC) - 2026")
