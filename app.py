"""
app.py — Simulador de Sueldo ✦ Pantalla Principal

Filosofía Apple:
- Una pantalla, una pregunta a la vez
- Hero number gigante con el sueldo estimado
- Recálculo en vivo, sin botón "Calcular"
- Progressive disclosure: detalles ocultos hasta que se pidan
"""

import streamlit as st
from datetime import date
from modules import calculos, tramos, indicadores
from modules.calculos import formato_clp, formato_uf, ResultadoCalculo
from modules.pdf_generator import generar_pdf_resumen

# ═══════════════════════════════════════════════════════════════════════════════
# Configuración de Página
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Simulador de Sueldo",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ═══════════════════════════════════════════════════════════════════════════════
# CSS Custom — Estética Apple
# ═══════════════════════════════════════════════════════════════════════════════
st.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Reset global ────────────────────────────────────────────── */
html, body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
p, h1, h2, h3, h4, h5, h6, span, div, input, button, select, option, label {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ── Ocultar el hamburger menu y footer ──────────────────────── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ── Sidebar mínimo ──────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #FFFFFF;
}

/* ── Tarjeta Hero del resultado ──────────────────────────────── */
.hero-card {
    background: linear-gradient(135deg, #FFFFFF 0%, #F8F9FF 100%);
    border-radius: 24px;
    padding: 2.5rem 2rem;
    text-align: center;
    box-shadow: 0 2px 20px rgba(0, 122, 255, 0.08),
                0 1px 4px rgba(0, 0, 0, 0.04);
    border: 1px solid rgba(0, 122, 255, 0.08);
    margin: 1.5rem 0;
    animation: fadeInUp 0.4s ease-out;
}

.hero-label {
    font-size: 0.85rem;
    font-weight: 500;
    color: #86868B;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 0.25rem;
}

.hero-number {
    font-size: 3.2rem;
    font-weight: 800;
    color: #007AFF;
    letter-spacing: -0.02em;
    line-height: 1.1;
    margin: 0.25rem 0;
}

.hero-subtitle {
    font-size: 0.8rem;
    color: #86868B;
    margin-top: 0.5rem;
}

/* ── Tarjetas de escenario (lado a lado) ─────────────────────── */
.scenario-card {
    background: #FFFFFF;
    border-radius: 20px;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 1px 8px rgba(0,0,0,0.04);
    border: 1px solid #E5E5EA;
    margin: 0.5rem 0;
}

.scenario-card.confirmed {
    border-color: rgba(52, 199, 89, 0.3);
}

.scenario-card.projected {
    border-color: rgba(255, 149, 0, 0.3);
}

.scenario-label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 0.25rem;
}

.scenario-number {
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1.2;
}

/* ── Tarjeta de info (UF, período) ───────────────────────────── */
.info-pill {
    display: inline-block;
    background: #FFFFFF;
    border-radius: 12px;
    padding: 0.4rem 0.9rem;
    font-size: 0.78rem;
    font-weight: 500;
    color: #1D1D1F;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    border: 1px solid #E5E5EA;
    margin: 0.15rem 0.2rem;
}

.info-pill .value {
    color: #007AFF;
    font-weight: 600;
}

/* ── Barra de Indicadores ────────────────────────────────────── */
.indicators-bar {
    background: #F5F5F7;
    border-radius: 12px;
    padding: 0.8rem 1rem;
    display: flex;
    justify-content: space-around;
    align-items: center;
    margin: 0.5rem 0 1rem 0;
    font-size: 0.82rem;
}

.indicator-item {
    text-align: center;
}

.indicator-label {
    color: #86868B;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.02em;
    margin-bottom: 0.1rem;
}

.indicator-value {
    font-weight: 700;
    color: #1D1D1F;
}

.uf-warning {
    background: #FFF9E6;
    border: 1px solid rgba(255, 149, 0, 0.2);
    border-radius: 12px;
    padding: 0.6rem 1rem;
    font-size: 0.78rem;
    color: #8A6D00;
    margin: 0.5rem 0;
}

/* ── Detalle del cálculo ─────────────────────────────────────── */
.detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.55rem 0;
    border-bottom: 1px solid #F2F2F7;
    font-size: 0.88rem;
}

.detail-row.indent {
    padding-left: 1rem;
    font-size: 0.82rem;
    color: #6E6E73;
}

.detail-row:last-child {
    border-bottom: none;
}

.detail-label {
    color: #3C3C43;
    font-weight: 400;
}

.detail-value {
    color: #1D1D1F;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
}

.detail-total {
    color: #007AFF;
    font-weight: 700;
    font-size: 1.05rem;
}

.detail-section-title {
    font-size: 0.72rem;
    font-weight: 600;
    color: #86868B;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-top: 1rem;
    margin-bottom: 0.3rem;
}

/* ── Tramo badge ─────────────────────────────────────────────── */
.tramo-badge {
    display: inline-block;
    background: linear-gradient(135deg, #007AFF 0%, #0051D5 100%);
    color: white;
    border-radius: 10px;
    padding: 0.4rem 0.8rem;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}

/* ── Animaciones ─────────────────────────────────────────────── */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(12px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* ── Inputs más grandes y amigables ──────────────────────────── */
[data-testid="stNumberInput"] input {
    font-size: 1.3rem !important;
    font-weight: 600 !important;
    padding: 0.7rem 1rem !important;
    border-radius: 14px !important;
    text-align: center !important;
}

[data-testid="stSelectbox"] > div > div {
    border-radius: 14px !important;
}

/* ── Slider más suave ────────────────────────────────────────── */
[data-testid="stSlider"] > div > div > div > div {
    background-color: #007AFF !important;
}

/* ── Título principal ────────────────────────────────────────── */
.app-title {
    text-align: center;
    margin-bottom: 0.2rem;
}

.app-title h1 {
    font-size: 1.8rem;
    font-weight: 700;
    color: #1D1D1F;
    margin: 0;
    letter-spacing: -0.02em;
}

.app-subtitle {
    text-align: center;
    font-size: 0.88rem;
    color: #86868B;
    margin-bottom: 1.5rem;
}

/* ── Expander styling ────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid #E5E5EA !important;
    border-radius: 16px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
}

[data-testid="stExpander"] summary {
    font-weight: 500 !important;
    color: #007AFF !important;
}
</style>
""")

# ═══════════════════════════════════════════════════════════════════════════════
# Constantes
# ═══════════════════════════════════════════════════════════════════════════════
MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

# ═══════════════════════════════════════════════════════════════════════════════
# Inicialización de Session State y Callbacks
# ═══════════════════════════════════════════════════════════════════════════════
if "historial" not in st.session_state:
    st.session_state.historial = []

if "monto_final" not in st.session_state:
    st.session_state.monto_final = 0
if "recaudacion_input" not in st.session_state:
    st.session_state.recaudacion_input = 0
if "slider_recaudacion" not in st.session_state:
    st.session_state.slider_recaudacion = 0

def sync_from_input():
    val = st.session_state.recaudacion_input
    st.session_state.monto_final = val
    st.session_state.slider_recaudacion = min(val, 80_000_000)

def sync_from_slider():
    val = st.session_state.slider_recaudacion
    st.session_state.monto_final = val
    st.session_state.recaudacion_input = val


# ═══════════════════════════════════════════════════════════════════════════════
# Header
# ═══════════════════════════════════════════════════════════════════════════════
st.html("""
<div class="app-title">
    <h1>💰 Simulador de Sueldo</h1>
</div>
<div class="app-subtitle">
    Descubre cuánto ganarás según tu recaudación
</div>
""")

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 1 — Selección de Período
# ═══════════════════════════════════════════════════════════════════════════════

hoy = date.today()

col_mes, col_anio = st.columns(2)
with col_mes:
    mes_seleccionado = st.selectbox(
        "Mes de recaudación",
        range(1, 13),
        index=hoy.month - 1,
        format_func=lambda x: MESES[x - 1],
        key="mes"
    )
with col_anio:
    anio_actual = hoy.year
    anios_disponibles = list(range(anio_actual - 5, anio_actual + 2))
    anio_seleccionado = st.selectbox(
        "Año",
        anios_disponibles,
        index=anios_disponibles.index(anio_actual),
        key="anio"
    )

# ─── Obtener Indicadores (UF, IMM, UTM) ───────────────────────────────────────
valor_uf, fuente_uf, es_cache = indicadores.obtener_uf_con_fallback(
    anio_seleccionado, mes_seleccionado
)

imm = indicadores.obtener_imm(anio_seleccionado, mes_seleccionado)
if imm is None:
    imm = 553553  # Fallback a IMM 2026 vigente si no hay datos

utm, fuente_utm, utm_es_cache = indicadores.obtener_utm_con_fallback(anio_seleccionado, mes_seleccionado)
if utm is None:
    utm = 0  # To handle later with the manual fallback

if valor_uf > 0 and utm > 0:
    uf_display = f"$ {valor_uf:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    imm_display = formato_clp(imm)
    utm_display = formato_clp(utm)
    
    st.html(f"""
    <div class="indicators-bar">
        <div class="indicator-item" title="Fuente UF: {fuente_uf}">
            <div class="indicator-label">UF</div>
            <div class="indicator-value" style="color: #007AFF;">{uf_display}</div>
        </div>
        <div class="indicator-item">
            <div class="indicator-label">IMM</div>
            <div class="indicator-value">{imm_display}</div>
        </div>
        <div class="indicator-item" title="Fuente UTM: {fuente_utm}">
            <div class="indicator-label">UTM</div>
            <div class="indicator-value">{utm_display}</div>
        </div>
    </div>
    """)
    if (es_cache and not indicadores.es_mes_pasado(anio_seleccionado, mes_seleccionado)) or (utm_es_cache and not indicadores.es_mes_pasado(anio_seleccionado, mes_seleccionado)):
        st.html(f"""
        <div class="uf-warning" style="text-align:center; padding:0.4rem; margin-top:-0.5rem; margin-bottom:1rem; border-radius:0 0 12px 12px; border-top:none;">
            ⚠️ Sin conexión. Usando último valor conocido de UF/UTM.
        </div>
        """)
else:
    if valor_uf == 0:
        st.warning(f"No tengo el valor UF de {MESES[mes_seleccionado-1]} {anio_seleccionado} todavía.")
        nuevo_uf = st.number_input(
            "Ingresa el valor UF de ese mes",
            min_value=1000.0,
            max_value=100000.0,
            value=38000.0,
            step=100.0,
            format="%.2f",
            key="nuevo_uf_input"
        )
        if st.button("Guardar este valor UF", key="guardar_uf"):
            indicadores.agregar_uf(anio_seleccionado, mes_seleccionado, nuevo_uf)
            st.success("¡Valor UF guardado!")
            st.rerun()
        valor_uf = nuevo_uf
    
    if utm == 0:
        st.warning(f"No tengo el valor UTM de {MESES[mes_seleccionado-1]} {anio_seleccionado} todavía.")
        nuevo_utm = st.number_input(
            "Ingresa el valor UTM de ese mes",
            min_value=10000,
            max_value=100000,
            value=68000,
            step=100,
            key="nuevo_utm_input"
        )
        if st.button("Guardar este valor UTM", key="guardar_utm"):
            indicadores.agregar_utm(anio_seleccionado, mes_seleccionado, nuevo_utm)
            st.success("¡Valor UTM guardado!")
            st.rerun()
        utm = nuevo_utm


# ═══════════════════════════════════════════════════════════════════════════════
# PASO 2 — Selección de Tabla de Comisión (solo si hay más de una)
# ═══════════════════════════════════════════════════════════════════════════════
tablas_disponibles = tramos.listar_tablas()
if len(tablas_disponibles) > 1:
    tabla_id = st.selectbox(
        "Tabla de comisión",
        tablas_disponibles,
        format_func=lambda x: tramos.obtener_tabla(x).get("nombre_display", x),
        key="tabla_comision"
    )
else:
    tabla_id = tablas_disponibles[0] if tablas_disponibles else "DNP"

tabla_datos = tramos.obtener_tabla(tabla_id)
lista_tramos = tramos.obtener_tramos(tabla_id)


# ═══════════════════════════════════════════════════════════════════════════════
# PASO 3 — Semana Corrida
# ═══════════════════════════════════════════════════════════════════════════════
with st.expander("📅 Días trabajados (Semana Corrida)"):
    st.markdown("<p style='font-size:0.85rem; color:#6E6E73;'>Ajusta los días del mes para el cálculo de tu semana corrida.</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        dias_trabajables = st.number_input("Días trabajables", min_value=1, max_value=27, value=20, help="Lunes a viernes/sábado")
    with c2:
        domingos_festivos = st.number_input("Domingos y festivos", min_value=0, max_value=10, value=4, help="Días de descanso irrenunciable")
    with c3:
        dias_licencia = st.number_input("Días de licencia", min_value=0, max_value=31, value=0, help="Restan a los días trabajables")


# ═══════════════════════════════════════════════════════════════════════════════
# PASO 4 — Ingreso de Recaudación
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("#### ¿Cuánto recaudaste este mes?")

recaudacion = st.number_input(
    "Monto total en pesos ($)",
    min_value=0,
    max_value=500_000_000,
    step=100_000,
    format="%d",
    key="recaudacion_input",
    on_change=sync_from_input,
    help="Ingresa el monto total de recaudación en pesos chilenos"
)

monto_final = st.session_state.monto_final

# Mostrar formato CLP del monto ingresado
if monto_final > 0:
    st.html(f"""
    <div style="text-align: center; margin: -0.5rem 0 0.5rem 0;">
        <span class="info-pill">Recaudación: <span class="value">{formato_clp(monto_final)}</span></span>
    </div>
    """)

# ─── Slider de simulación "¿Y si...?" ────────────────────────────────────────
st.markdown("##### 🎛️ Simula distintos montos")
max_slider = 80_000_000
recaudacion_slider = st.slider(
    "Desliza para explorar escenarios",
    min_value=0,
    max_value=max_slider,
    step=500_000,
    format="$%d",
    key="slider_recaudacion",
    on_change=sync_from_slider
)

# Validación amigable
if monto_final > 100_000_000:
    st.html("""
    <div class="uf-warning">
        🤔 Ese monto parece muy alto. ¿Lo revisamos? Si es correcto, adelante.
    </div>
    """)

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 5 — Resultado Instantáneo
# ═══════════════════════════════════════════════════════════════════════════════

if monto_final > 0 and valor_uf > 0 and lista_tramos:
    try:
        resultado = calculos.calcular_sueldo(
            recaudacion_pesos=monto_final,
            valor_uf=valor_uf,
            valor_utm=utm,
            imm=imm,
            tramos=lista_tramos,
            tabla_nombre=tabla_datos.get("nombre_display", tabla_id) if tabla_datos else tabla_id,
            mes=mes_seleccionado,
            anio=anio_seleccionado,
            dias_trabajables=dias_trabajables,
            domingos_festivos=domingos_festivos,
            dias_licencia=dias_licencia
        )

        # ─── ¿Hay escenario dual? (tramos no confirmados) ────────────────
        if resultado.escenario_alternativo is not None:
            # Modo 2 tarjetas lado a lado
            col_conf, col_proy = st.columns(2)

            with col_conf:
                st.html(f"""
                <div class="scenario-card confirmed">
                    <div class="scenario-label" style="color: #34C759;">✅ Tasa confirmada</div>
                    <div class="scenario-number" style="color: #34C759;">
                        {formato_clp(resultado.escenario_alternativo.sueldo_liquido)}
                    </div>
                    <div class="hero-subtitle">
                        Tramo: {resultado.escenario_alternativo.tramo.descripcion}
                    </div>
                </div>
                """)

            with col_proy:
                st.html(f"""
                <div class="scenario-card projected">
                    <div class="scenario-label" style="color: #FF9500;">⚠️ Tasa proyectada</div>
                    <div class="scenario-number" style="color: #FF9500;">
                        {formato_clp(resultado.sueldo_liquido)}
                    </div>
                    <div class="hero-subtitle">
                        Tramo: {resultado.tramo.descripcion}
                    </div>
                </div>
                """)
        else:
            # Modo normal — 1 tarjeta hero
            recaudacion_uf_display = f"{resultado.recaudacion_uf:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            st.html(f"""
            <div class="hero-card">
                <div class="hero-label">Tu sueldo líquido estimado</div>
                <div class="hero-number">{formato_clp(resultado.sueldo_liquido)}</div>
                <div class="hero-subtitle">
                    Recaudación: {formato_clp(monto_final)} → {recaudacion_uf_display} UF
                </div>
                <div style="margin-top: 0.8rem;">
                    <span class="tramo-badge">{resultado.tramo.descripcion}</span>
                </div>
            </div>
            """)

        # ─── Detalle del cálculo (Progressive Disclosure) ────────────────
        with st.expander("📋 Ver el detalle del cálculo"):
            d = resultado.descuentos

            st.html(f"""
            <div style="padding: 0.5rem 0;">
                <div class="detail-section-title">Haberes</div>
                <div class="detail-row">
                    <span class="detail-label">Ingreso Mínimo Mensual (IMM)</span>
                    <span class="detail-value">{formato_clp(resultado.imm)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Comisión por recaudación ({resultado.tramo.comision_pct}%)</span>
                    <span class="detail-value">{formato_clp(resultado.comision_recaudacion)}</span>
                </div>
                {"<div class='detail-row'><span class='detail-label'>Premio del tramo</span><span class='detail-value'>" + formato_clp(resultado.premio) + "</span></div>" if resultado.premio > 0 else ""}
                <div class="detail-row">
                    <span class="detail-label">Semana Corrida</span>
                    <span class="detail-value">{formato_clp(resultado.semana_corrida_monto)}</span>
                </div>
                <div class="detail-row indent">
                    <span>(Comisión ÷ {resultado.dias_efectivos_trabajables} días) × {resultado.domingos_festivos} festivos</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Asignación Internet (no imponible)</span>
                    <span class="detail-value">{formato_clp(resultado.asignacion_internet)}</span>
                </div>
                <div class="detail-row" style="background:#F5F5F7; border-radius:8px; padding:0.5rem; margin-top:0.3rem;">
                    <span class="detail-label" style="font-weight:600;">Total Haberes</span>
                    <span class="detail-total">{formato_clp(resultado.total_haberes)}</span>
                </div>

                <div class="detail-section-title" style="margin-top: 1.2rem;">Descuentos Legales e Impuestos</div>
                <div class="detail-row">
                    <span class="detail-label">{d.afp_nombre} ({d.afp_tasa}%)</span>
                    <span class="detail-value">-{formato_clp(d.afp_monto)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Salud {d.salud_sistema} ({d.salud_tasa}%)</span>
                    <span class="detail-value">-{formato_clp(d.salud_monto)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Seguro Cesantía ({d.cesantia_tasa}%)</span>
                    <span class="detail-value">-{formato_clp(d.cesantia_monto)}</span>
                </div>
                {"<div class='detail-row'><span class='detail-label'>APV Individual</span><span class='detail-value'>-" + formato_clp(d.apv_monto) + "</span></div>" if d.apv_monto > 0 else ""}
                <div class="detail-row" style="margin-top:0.3rem;">
                    <span class="detail-label">Impuesto Único de 2da Categoría</span>
                    <span class="detail-value" style="color: #FF3B30;">-{formato_clp(d.impuesto_unico_monto)}</span>
                </div>
                <div class="detail-row indent">
                    <span>Base tributable: {formato_clp(d.base_tributable)} ({round(d.base_tributable/resultado.valor_utm, 2)} UTM)</span>
                </div>
                <div class="detail-row" style="background:#FFF0F0; border-radius:8px; padding:0.5rem; margin-top:0.3rem;">
                    <span class="detail-label" style="font-weight:600;">Total Descuentos</span>
                    <span class="detail-value" style="color: #FF3B30; font-weight:700;">-{formato_clp(d.total_descuentos)}</span>
                </div>
            </div>
            """)

        # ─── Tabla de tramos referencial ─────────────────────────────────
        with st.expander("📊 Ver tabla de tramos vigente"):
            tramos_enriquecidos = tramos.tramos_con_pesos(lista_tramos, valor_uf)

            filas_html = ""
            for i, t in enumerate(tramos_enriquecidos):
                es_actual = (t["desde_uf"] <= resultado.recaudacion_uf and
                            (t["hasta_uf"] is None or resultado.recaudacion_uf <= t["hasta_uf"]))
                bg = "background: rgba(0, 122, 255, 0.06);" if es_actual else ""
                peso_desde = formato_clp(t["recuperacion_desde_pesos"])
                peso_hasta = formato_clp(t["recuperacion_hasta_pesos"]) if t["recuperacion_hasta_pesos"] else "Sin tope"
                indicator = "👉 " if es_actual else ""

                filas_html += f"""
                <tr style="{bg}">
                    <td style="padding:0.5rem 0.7rem; font-weight:{'700' if es_actual else '400'};">
                        {indicator}{t['desde_uf']:,.0f} – {f"{t['hasta_uf']:,.0f}" if t['hasta_uf'] else '∞'} UF
                    </td>
                    <td style="padding:0.5rem 0.7rem; text-align:right;">{peso_desde} – {peso_hasta}</td>
                    <td style="padding:0.5rem 0.7rem; text-align:center; font-weight:600;">{t['comision_pct']}%</td>
                    <td style="padding:0.5rem 0.7rem; text-align:right;">{formato_clp(t['premio']) if t['premio'] > 0 else '—'}</td>
                </tr>
                """

            st.html(f"""
            <div style="overflow-x:auto; border-radius:12px; border:1px solid #E5E5EA;">
                <table style="width:100%; border-collapse:collapse; font-size:0.82rem;">
                    <thead>
                        <tr style="background:#F5F5F7; border-bottom:2px solid #E5E5EA;">
                            <th style="padding:0.6rem 0.7rem; text-align:left; font-weight:600; color:#86868B;">Tramo UF</th>
                            <th style="padding:0.6rem 0.7rem; text-align:right; font-weight:600; color:#86868B;">Rango en $</th>
                            <th style="padding:0.6rem 0.7rem; text-align:center; font-weight:600; color:#86868B;">Comisión</th>
                            <th style="padding:0.6rem 0.7rem; text-align:right; font-weight:600; color:#86868B;">Premio</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filas_html}
                    </tbody>
                </table>
            </div>
            <p style="font-size:0.72rem; color:#86868B; margin-top:0.4rem; text-align:center;">
                Los rangos en pesos se calculan dinámicamente con la UF vigente
            </p>
            """)

        # ─── Acciones ────────────────────────────────────────────────────
        col_guardar, col_pdf = st.columns(2)

        with col_guardar:
            if st.button("💾 Guardar en historial", use_container_width=True, key="guardar_hist"):
                entry = {
                    "mes": mes_seleccionado,
                    "anio": anio_seleccionado,
                    "recaudacion": monto_final,
                    "sueldo_liquido": resultado.sueldo_liquido,
                    "tramo": resultado.tramo.descripcion,
                    "valor_uf": valor_uf,
                    "comision": resultado.comision_recaudacion,
                    "premio": resultado.premio,
                    "imm": resultado.imm,
                }
                st.session_state.historial.append(entry)
                st.success("✅ Guardado en tu historial")

        with col_pdf:
            try:
                pdf_bytes = generar_pdf_resumen(resultado)
                mes_nombre = MESES[mes_seleccionado - 1]
                st.download_button(
                    "📄 Descargar PDF",
                    data=pdf_bytes,
                    file_name=f"Sueldo_{mes_nombre}_{anio_seleccionado}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="descargar_pdf"
                )
            except Exception:
                st.button("📄 Descargar PDF", disabled=True, use_container_width=True,
                          help="Instala fpdf2 para habilitar la exportación PDF")

    except Exception as e:
        st.error(f"Hubo un problema con el cálculo. Revisa los datos ingresados.")
        with st.expander("Detalle técnico"):
            st.code(str(e))

elif monto_final == 0:
    # Estado vacío — invitar al usuario
    st.html("""
    <div class="hero-card" style="opacity: 0.6;">
        <div class="hero-label">Tu sueldo líquido estimado</div>
        <div class="hero-number" style="color: #C7C7CC;">$ —</div>
        <div class="hero-subtitle">
            Ingresa tu recaudación arriba o desliza el simulador
        </div>
    </div>
    """)
