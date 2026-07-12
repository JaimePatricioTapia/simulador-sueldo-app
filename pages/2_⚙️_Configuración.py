"""
⚙️ Configuración — Modo Avanzado

Gestión de tablas de tramos, valores UF históricos, IMM y descuentos.
Solo para usuarios que necesitan ajustar los datos técnicos.
"""

import streamlit as st
import pandas as pd
import json
from modules import tramos, indicadores, calculos
from modules.calculos import formato_clp

# ═══════════════════════════════════════════════════════════════════════════════
# Configuración de Página
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Configuración — Simulador de Sueldo",
    page_icon="⚙️",
    layout="centered"
)

# ═══════════════════════════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════════════════════════
st.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="st-"] { font-family: 'Inter', -apple-system, sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }

.config-header {
    text-align: center;
    margin-bottom: 1.5rem;
}

.config-header h1 {
    font-size: 1.6rem;
    font-weight: 700;
    color: #1D1D1F;
    letter-spacing: -0.02em;
}

.config-header p {
    font-size: 0.85rem;
    color: #86868B;
}
</style>
""")

st.html("""
<div class="config-header">
    <h1>⚙️ Configuración</h1>
    <p>Ajusta las tablas de comisión, indicadores económicos y descuentos</p>
</div>
""")

# ═══════════════════════════════════════════════════════════════════════════════
# Tabs de Configuración
# ═══════════════════════════════════════════════════════════════════════════════

tab_tramos, tab_uf, tab_imm, tab_descuentos = st.tabs([
    "📋 Tablas de Comisión",
    "📈 Valores UF",
    "💰 Valores IMM",
    "🏛️ Descuentos"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Tablas de Comisión
# ═══════════════════════════════════════════════════════════════════════════════
with tab_tramos:
    tablas_ids = tramos.listar_tablas()

    if not tablas_ids:
        st.info("No hay tablas de comisión configuradas.")
    else:
        tabla_sel = st.selectbox(
            "Selecciona una tabla",
            tablas_ids,
            format_func=lambda x: tramos.obtener_tabla(x).get("nombre_display", x),
            key="config_tabla_sel"
        )

        tabla_info = tramos.obtener_tabla(tabla_sel)
        lista = tramos.obtener_tramos(tabla_sel)

        if lista:
            # Convertir a DataFrame para edición
            df = pd.DataFrame(lista)

            # Renombrar para legibilidad
            display_cols = {
                "desde_uf": "Desde (UF)",
                "hasta_uf": "Hasta (UF)",
                "comision_pct": "Comisión (%)",
                "premio": "Premio ($)",
                "estado": "Estado"
            }

            df_display = df.rename(columns=display_cols)

            st.markdown(f"##### {tabla_info.get('nombre_display', tabla_sel)}")

            edited_df = st.data_editor(
                df_display,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "Desde (UF)": st.column_config.NumberColumn(format="%.0f", min_value=0),
                    "Hasta (UF)": st.column_config.NumberColumn(format="%.0f", min_value=0),
                    "Comisión (%)": st.column_config.NumberColumn(format="%.2f", min_value=0, max_value=100),
                    "Premio ($)": st.column_config.NumberColumn(format="$%d", min_value=0),
                    "Estado": st.column_config.SelectboxColumn(
                        options=["confirmado", "proyectado"],
                        default="confirmado"
                    )
                },
                key=f"editor_tramos_{tabla_sel}"
            )

            if st.button("💾 Guardar cambios en tramos", key="guardar_tramos"):
                # Convertir de vuelta
                inv_cols = {v: k for k, v in display_cols.items()}
                df_save = edited_df.rename(columns=inv_cols)
                nuevos_tramos = df_save.to_dict(orient="records")

                # Limpiar NaN → None para hasta_uf
                for t in nuevos_tramos:
                    if pd.isna(t.get("hasta_uf")):
                        t["hasta_uf"] = None
                    if "premio" not in t:
                        t["premio"] = 0
                    if "estado" not in t:
                        t["estado"] = "confirmado"

                # Validar
                errores = tramos.validar_tramos(nuevos_tramos)
                if errores:
                    for e in errores:
                        st.error(f"⚠️ {e}")
                else:
                    tramos.actualizar_tramos(tabla_sel, nuevos_tramos)
                    st.success("✅ Tramos actualizados correctamente")

    # ─── Crear nueva tabla ───────────────────────────────────────────────
    with st.expander("➕ Crear nueva tabla de comisión"):
        nuevo_id = st.text_input("ID de la tabla (sin espacios)", key="nueva_tabla_id")
        nuevo_nombre = st.text_input("Nombre para mostrar", key="nueva_tabla_nombre")

        if st.button("Crear tabla", key="crear_tabla"):
            if nuevo_id and nuevo_nombre:
                if nuevo_id in tablas_ids:
                    st.error("Ya existe una tabla con ese ID")
                else:
                    tramos.crear_tabla(nuevo_id, nuevo_nombre)
                    st.success(f"✅ Tabla '{nuevo_nombre}' creada")
                    st.rerun()
            else:
                st.warning("Completa ambos campos")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Valores UF
# ═══════════════════════════════════════════════════════════════════════════════
with tab_uf:
    st.markdown("##### Valores UF por Mes")
    st.caption("Los últimos 30 días se actualizan automáticamente desde la API de findic.cl")

    uf_data = indicadores.cargar_uf_historica()

    if uf_data:
        df_uf = pd.DataFrame(
            [{"Período": k, "Valor UF ($)": v} for k, v in sorted(uf_data.items(), reverse=True)]
        )

        edited_uf = st.data_editor(
            df_uf,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Período": st.column_config.TextColumn(help="Formato: AAAA-MM"),
                "Valor UF ($)": st.column_config.NumberColumn(format="$%.2f", min_value=1000)
            },
            key="editor_uf"
        )

        if st.button("💾 Guardar cambios UF", key="guardar_uf_config"):
            new_uf = {}
            for _, row in edited_uf.iterrows():
                periodo = str(row["Período"]).strip()
                valor = row["Valor UF ($)"]
                if periodo and not pd.isna(valor):
                    new_uf[periodo] = round(float(valor), 2)
            indicadores.guardar_uf_historica(new_uf)
            st.success("✅ Valores UF actualizados")
    else:
        st.info("No hay valores UF cargados. Agrega el primero:")

    # ─── Agregar UF manual ───────────────────────────────────────────────
    with st.expander("➕ Agregar valor UF manualmente"):
        col_a, col_m, col_v = st.columns(3)
        with col_a:
            uf_anio = st.number_input("Año", min_value=2020, max_value=2030,
                                       value=2025, key="uf_add_anio")
        with col_m:
            uf_mes = st.number_input("Mes", min_value=1, max_value=12,
                                      value=1, key="uf_add_mes")
        with col_v:
            uf_val = st.number_input("Valor UF", min_value=1000.0, max_value=100000.0,
                                      value=38000.0, step=100.0, format="%.2f",
                                      key="uf_add_val")

        if st.button("Agregar", key="agregar_uf_manual"):
            indicadores.agregar_uf(int(uf_anio), int(uf_mes), uf_val)
            st.success(f"✅ UF {uf_anio}-{uf_mes:02d} = ${uf_val:,.2f} guardada")
            st.rerun()

    # ─── Actualizar desde API ────────────────────────────────────────────
    if st.button("🔄 Actualizar UF desde API", key="actualizar_api"):
        with st.spinner("Consultando findic.cl..."):
            uf, fecha, error = indicadores.actualizar_uf_desde_api()
            if error:
                st.error(f"⚠️ {error}")
            else:
                st.success(f"✅ UF actualizada: ${uf:,.2f} ({fecha})")
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Valores IMM
# ═══════════════════════════════════════════════════════════════════════════════
with tab_imm:
    st.markdown("##### Ingreso Mínimo Mensual por Período")
    st.caption("Se busca el valor vigente más cercano anterior a la fecha seleccionada")

    imm_data = indicadores.cargar_imm_historica()

    if imm_data:
        df_imm = pd.DataFrame(
            [{"Período": k, "IMM ($)": v} for k, v in sorted(imm_data.items(), reverse=True)]
        )

        edited_imm = st.data_editor(
            df_imm,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Período": st.column_config.TextColumn(help="Formato: AAAA-MM"),
                "IMM ($)": st.column_config.NumberColumn(format="$%d", min_value=0)
            },
            key="editor_imm"
        )

        if st.button("💾 Guardar cambios IMM", key="guardar_imm_config"):
            new_imm = {}
            for _, row in edited_imm.iterrows():
                periodo = str(row["Período"]).strip()
                valor = row["IMM ($)"]
                if periodo and not pd.isna(valor):
                    new_imm[periodo] = int(valor)
            indicadores.guardar_imm_historica(new_imm)
            st.success("✅ Valores IMM actualizados")

    # ─── Agregar IMM ────────────────────────────────────────────────────
    with st.expander("➕ Agregar valor IMM"):
        col_a2, col_m2, col_v2 = st.columns(3)
        with col_a2:
            imm_anio = st.number_input("Año", min_value=2020, max_value=2030,
                                        value=2025, key="imm_add_anio")
        with col_m2:
            imm_mes = st.number_input("Mes", min_value=1, max_value=12,
                                       value=7, key="imm_add_mes")
        with col_v2:
            imm_val = st.number_input("Valor IMM", min_value=100000, max_value=2000000,
                                       value=520000, step=10000,
                                       key="imm_add_val")

        if st.button("Agregar", key="agregar_imm_manual"):
            indicadores.agregar_imm(int(imm_anio), int(imm_mes), imm_val)
            st.success(f"✅ IMM {imm_anio}-{imm_mes:02d} = ${imm_val:,} guardado")
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Descuentos Legales
# ═══════════════════════════════════════════════════════════════════════════════
with tab_descuentos:
    st.markdown("##### Configuración de Descuentos Legales")
    st.caption("Estos valores se extraen de tus liquidaciones reales")

    config = calculos.cargar_config_descuentos()

    # ─── AFP ─────────────────────────────────────────────────────────────
    st.markdown("**Previsión (AFP)**")
    col_afp1, col_afp2 = st.columns(2)
    with col_afp1:
        afp_nombre = st.text_input("Nombre AFP", value=config["afp"]["nombre"],
                                    key="desc_afp_nombre")
    with col_afp2:
        afp_tasa = st.number_input("Tasa total (%)", value=config["afp"]["tasa_total_pct"],
                                    min_value=0.0, max_value=20.0, step=0.01,
                                    format="%.2f", key="desc_afp_tasa")

    # ─── Salud ───────────────────────────────────────────────────────────
    st.markdown("**Salud**")
    col_sal1, col_sal2 = st.columns(2)
    with col_sal1:
        salud_sistema = st.selectbox("Sistema", ["Fonasa", "Isapre"],
                                      index=0 if config["salud"]["sistema"] == "Fonasa" else 1,
                                      key="desc_salud_sistema")
    with col_sal2:
        salud_tasa = st.number_input("Tasa (%)", value=config["salud"]["tasa_pct"],
                                      min_value=0.0, max_value=20.0, step=0.1,
                                      format="%.1f", key="desc_salud_tasa")

    # ─── Cesantía ────────────────────────────────────────────────────────
    st.markdown("**Seguro de Cesantía**")
    cesantia_tasa = st.number_input("Tasa (%)", value=config["seguro_cesantia"]["tasa_pct"],
                                     min_value=0.0, max_value=5.0, step=0.1,
                                     format="%.1f", key="desc_cesantia_tasa")

    # ─── APV ─────────────────────────────────────────────────────────────
    st.markdown("**APV Individual Tributable**")
    apv_monto = st.number_input("Monto fijo mensual ($)", value=config.get("apv", {}).get("monto_fijo", 0),
                                 min_value=0, max_value=1000000, step=5000,
                                 key="desc_apv_monto")

    # ─── Internet ────────────────────────────────────────────────────────
    st.markdown("**Asignación Internet (no imponible)**")
    internet = st.number_input("Monto ($)", 
                                value=config.get("asignaciones_no_imponibles", {}).get("internet", 0),
                                min_value=0, max_value=100000, step=1000,
                                key="desc_internet")

    # ─── Guardar ─────────────────────────────────────────────────────────
    if st.button("💾 Guardar configuración de descuentos", key="guardar_desc"):
        from pathlib import Path
        nueva_config = {
            "afp": {"nombre": afp_nombre, "tasa_total_pct": afp_tasa},
            "salud": {"sistema": salud_sistema, "tasa_pct": salud_tasa},
            "seguro_cesantia": {"tasa_pct": cesantia_tasa},
            "apv": {"monto_fijo": apv_monto},
            "asignaciones_no_imponibles": {"internet": internet}
        }
        desc_file = Path(__file__).parent.parent / "data" / "descuentos_config.json"
        with open(desc_file, "w", encoding="utf-8") as f:
            json.dump(nueva_config, f, indent=2, ensure_ascii=False)
        st.success("✅ Configuración de descuentos guardada")
