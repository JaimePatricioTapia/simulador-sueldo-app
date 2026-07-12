"""
📊 Mi Historial — Registro de cálculos anteriores

Muestra los sueldos calculados durante la sesión con gráfico de evolución.
"""

import streamlit as st
from modules.calculos import formato_clp

# ═══════════════════════════════════════════════════════════════════════════════
# Configuración
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Mi Historial — Simulador de Sueldo",
    page_icon="📊",
    layout="centered"
)

MESES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

# ═══════════════════════════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════════════════════════
st.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="st-"] { font-family: 'Inter', -apple-system, sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }

.hist-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    margin: 0.6rem 0;
    box-shadow: 0 1px 6px rgba(0,0,0,0.04);
    border: 1px solid #E5E5EA;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.hist-periodo {
    font-size: 0.88rem;
    font-weight: 600;
    color: #1D1D1F;
}

.hist-detalle {
    font-size: 0.75rem;
    color: #86868B;
    margin-top: 0.2rem;
}

.hist-monto {
    font-size: 1.3rem;
    font-weight: 800;
    color: #007AFF;
}

.empty-state {
    text-align: center;
    padding: 3rem 2rem;
    color: #86868B;
}

.empty-state .icon {
    font-size: 3rem;
    margin-bottom: 0.8rem;
}
</style>
""")

# ═══════════════════════════════════════════════════════════════════════════════
# Header
# ═══════════════════════════════════════════════════════════════════════════════
st.html("""
<div style="text-align:center; margin-bottom:1.5rem;">
    <h1 style="font-size:1.6rem; font-weight:700; color:#1D1D1F; letter-spacing:-0.02em;">
        📊 Mi Historial
    </h1>
    <p style="font-size:0.85rem; color:#86868B;">
        Tus cálculos guardados durante esta sesión
    </p>
</div>
""")

# ═══════════════════════════════════════════════════════════════════════════════
# Contenido
# ═══════════════════════════════════════════════════════════════════════════════

historial = st.session_state.get("historial", [])

if not historial:
    st.html("""
    <div class="empty-state">
        <div class="icon">📭</div>
        <p style="font-size: 1rem; font-weight: 500; margin-bottom: 0.3rem;">
            Aún no hay cálculos guardados
        </p>
        <p style="font-size: 0.82rem;">
            Ve al Simulador, calcula tu sueldo y toca "Guardar en historial"
        </p>
    </div>
    """)
else:
    # ─── Gráfico de evolución ────────────────────────────────────────────
    if len(historial) >= 2:
        import pandas as pd

        df = pd.DataFrame(historial)
        df["periodo"] = df.apply(
            lambda r: f"{MESES[r['mes']]} {r['anio']}", axis=1
        )
        df = df.set_index("periodo")

        st.markdown("##### 📈 Evolución de sueldo líquido")
        st.area_chart(df["sueldo_liquido"], color="#007AFF", height=200)

    # ─── Tarjetas ────────────────────────────────────────────────────────
    for i, entry in enumerate(reversed(historial)):
        mes_nombre = MESES[entry["mes"]] if 1 <= entry["mes"] <= 12 else "?"
        recau_fmt = formato_clp(entry["recaudacion"])
        sueldo_fmt = formato_clp(entry["sueldo_liquido"])

        st.html(f"""
        <div class="hist-card">
            <div>
                <div class="hist-periodo">{mes_nombre} {entry['anio']}</div>
                <div class="hist-detalle">
                    Recaudación: {recau_fmt} · {entry.get('tramo', '')}
                </div>
            </div>
            <div class="hist-monto">{sueldo_fmt}</div>
        </div>
        """)

    # ─── Limpiar historial ───────────────────────────────────────────────
    st.markdown("---")
    if st.button("🗑️ Limpiar historial", key="limpiar_hist"):
        st.session_state.historial = []
        st.rerun()
