"""
calculos.py — Motor de cálculo de comisiones, descuentos y sueldo líquido

Incluye:
- Cálculo de comisiones por tramo DNP
- Semana Corrida (Art. 45 Código del Trabajo)
- Descuentos legales (AFP, Salud, Seguro de Cesantía)
- Impuesto Único de Segunda Categoría (basado en UTM)
"""

import json
import calendar
from datetime import date
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

# ─── Ruta de datos ───────────────────────────────────────────────────────────
_DATA_DIR = Path(__file__).parent.parent / "data"
_DESCUENTOS_FILE = _DATA_DIR / "descuentos_config.json"


# ═══════════════════════════════════════════════════════════════════════════════
# Dataclasses para resultados estructurados
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TramoEncontrado:
    """Tramo de comisión donde cae la recaudación."""
    indice: int
    desde_uf: float
    hasta_uf: Optional[float]
    comision_pct: float
    premio: int
    estado: str
    descripcion: str


@dataclass
class DetalleDescuentos:
    """Desglose de descuentos legales e impuestos."""
    afp_nombre: str
    afp_tasa: float
    afp_monto: int
    salud_sistema: str
    salud_tasa: float
    salud_monto: int
    cesantia_tasa: float
    cesantia_monto: int
    cuenta_ahorro_monto: int
    total_leyes_sociales: int

    base_tributable: int
    impuesto_unico_monto: int
    
    total_descuentos: int


@dataclass
class ResultadoCalculo:
    """Resultado completo del cálculo de sueldo."""
    # Inputs
    recaudacion_pesos: int
    valor_uf: float
    valor_utm: float
    mes: int
    anio: int
    tabla_usada: str

    # Conversión UF
    recaudacion_uf: float

    # Tramo
    tramo: TramoEncontrado

    # Haberes — desglose IMM
    sueldo_base: int
    ajuste_sueldo_base: int
    imm: int
    comision_recaudacion: int
    premio: int
    
    # Semana Corrida
    dias_trabajables: int
    domingos_festivos: int
    dias_licencia: int
    dias_efectivos_trabajables: int
    semana_corrida_monto: int
    
    asignacion_internet: int
    total_imponible: int
    total_haberes: int

    # Descuentos
    descuentos: DetalleDescuentos

    # Resultado
    sueldo_liquido: int

    # Otros descuentos
    anticipo: int = 0
    prestamo: int = 0

    # Haberes adicionales ocasionales (imponibles)
    gratificacion: int = 0
    comision_feriado: int = 0

    # Escenario alternativo (solo si hay tramos no confirmados)
    escenario_alternativo: Optional["ResultadoCalculo"] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Funciones de Cálculo
# ═══════════════════════════════════════════════════════════════════════════════

def cargar_config_descuentos() -> dict:
    """Carga la configuración de descuentos legales."""
    if not _DESCUENTOS_FILE.exists():
        # Defaults basados en liquidaciones reales
        return {
            "afp": {"nombre": "AFP Habitat", "tasa_total_pct": 11.27},
            "salud": {"sistema": "Fonasa", "tasa_pct": 7.0},
            "seguro_cesantia": {"tasa_pct": 0.6},
            "cuenta_ahorro": {"monto_fijo": 15000},
            "asignaciones_no_imponibles": {"internet": 15000}
        }
    with open(_DESCUENTOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def calcular_recaudacion_uf(monto_pesos: int, valor_uf: float) -> float:
    """Convierte un monto en pesos chilenos a UF."""
    if valor_uf <= 0:
        return 0.0
    return round(monto_pesos / valor_uf, 2)


def encontrar_tramo(recaudacion_uf: float, tramos: list) -> TramoEncontrado:
    """
    Encuentra el tramo correspondiente a una recaudación en UF.
    """
    for i, tramo in enumerate(tramos):
        desde = tramo["desde_uf"]
        hasta = tramo.get("hasta_uf")

        if hasta is None:
            en_tramo = recaudacion_uf >= desde
        else:
            en_tramo = desde <= recaudacion_uf <= hasta

        if en_tramo:
            if hasta is None:
                desc = f"Tramo {i+1}: sobre {desde:,.0f} UF ({tramo['comision_pct']}%)"
            else:
                desc = f"Tramo {i+1}: {desde:,.0f} – {hasta:,.0f} UF ({tramo['comision_pct']}%)"

            return TramoEncontrado(
                indice=i,
                desde_uf=desde,
                hasta_uf=hasta,
                comision_pct=tramo["comision_pct"],
                premio=tramo.get("premio", 0),
                estado=tramo.get("estado", "confirmado"),
                descripcion=desc
            )

    if tramos:
        t = tramos[0]
        return TramoEncontrado(
            indice=0, desde_uf=0, hasta_uf=t.get("hasta_uf"),
            comision_pct=t["comision_pct"], premio=0,
            estado=t.get("estado", "confirmado"),
            descripcion=f"Tramo 1: 0 – {t.get('hasta_uf', '?')} UF ({t['comision_pct']}%)"
        )

    raise ValueError("No hay tramos definidos en la tabla de comisiones")


# ─── Feriados legales de Chile (mes, día) ─────────────────────────────────────
_FERIADOS_FIJOS = [
    (1, 1),   # Año Nuevo
    (5, 1),   # Día del Trabajo
    (5, 21),  # Día de las Glorias Navales
    (6, 20),  # Día Nacional de los Pueblos Indígenas (varía, aprox)
    (6, 29),  # San Pedro y San Pablo
    (7, 16),  # Virgen del Carmen
    (8, 15),  # Asunción de la Virgen
    (9, 18),  # Fiestas Patrias
    (9, 19),  # Glorias del Ejército
    (10, 12), # Encuentro de Dos Mundos (puede moverse)
    (10, 31), # Día de las Iglesias Evangélicas
    (11, 1),  # Todos los Santos
    (12, 8),  # Inmaculada Concepción
    (12, 25), # Navidad
]


def calcular_dias_mes(anio: int, mes: int) -> tuple:
    """
    Calcula automáticamente los días trabajables (L-V menos feriados)
    y los domingos + festivos del mes, para Semana Corrida.
    
    Returns:
        (dias_trabajables, domingos_y_festivos)
    """
    _, dias_en_mes = calendar.monthrange(anio, mes)
    
    dias_habiles = 0
    domingos = 0
    feriados_en_habil = 0
    
    feriados_del_mes = {d for m, d in _FERIADOS_FIJOS if m == mes}
    
    for dia in range(1, dias_en_mes + 1):
        d = date(anio, mes, dia)
        dow = d.weekday()  # 0=Lun, 6=Dom
        
        if dow == 6:  # Domingo
            domingos += 1
        elif dow < 5:  # Lunes a Viernes
            if dia in feriados_del_mes:
                feriados_en_habil += 1
            else:
                dias_habiles += 1
        # Sábados: no se cuentan como trabajables ni como festivos
    
    dias_trabajables = dias_habiles
    domingos_festivos = domingos + feriados_en_habil
    
    return dias_trabajables, domingos_festivos


def calcular_semana_corrida(comision: int, dias_trabajables: int, domingos_festivos: int, dias_licencia: int) -> int:
    """
    Calcula el monto de semana corrida.
    Fórmula: (Comisión / dias_efectivos_que_correspondia_trabajar) * domingos_y_festivos
    dias_efectivos = dias_trabajables - dias_licencia
    """
    dias_efectivos = max(1, dias_trabajables - dias_licencia)
    if comision <= 0 or domingos_festivos <= 0:
        return 0
    
    promedio_diario = comision / dias_efectivos
    return round(promedio_diario * domingos_festivos)


def calcular_impuesto_unico(base_tributable: int, valor_utm: float) -> int:
    """
    Calcula el Impuesto Único de Segunda Categoría.
    Tabla SII (valores fijos en factores, los tramos se mueven con UTM):
    
    Tramo 1: 0 a 13.5 UTM (Exento)
    Tramo 2: 13.5 a 30 UTM (Factor 0.04, Rebaja 0.54 UTM)
    Tramo 3: 30 a 50 UTM (Factor 0.08, Rebaja 1.74 UTM)
    Tramo 4: 50 a 70 UTM (Factor 0.135, Rebaja 4.49 UTM)
    Tramo 5: 70 a 90 UTM (Factor 0.23, Rebaja 11.14 UTM)
    Tramo 6: 90 a 120 UTM (Factor 0.304, Rebaja 17.80 UTM)
    Tramo 7: 120 a 150 UTM (Factor 0.35, Rebaja 23.32 UTM)
    Tramo 8: Más de 150 UTM (Factor 0.40, Rebaja 30.82 UTM)
    """
    if valor_utm <= 0:
        return 0
        
    base_utm = base_tributable / valor_utm
    
    factor = 0.0
    rebaja_utm = 0.0
    
    if base_utm <= 13.5:
        return 0
    elif base_utm <= 30.0:
        factor = 0.04
        rebaja_utm = 0.54
    elif base_utm <= 50.0:
        factor = 0.08
        rebaja_utm = 1.74
    elif base_utm <= 70.0:
        factor = 0.135
        rebaja_utm = 4.49
    elif base_utm <= 90.0:
        factor = 0.23
        rebaja_utm = 11.14
    elif base_utm <= 120.0:
        factor = 0.304
        rebaja_utm = 17.80
    elif base_utm <= 150.0:
        factor = 0.35
        rebaja_utm = 23.32
    else:
        factor = 0.40
        rebaja_utm = 30.82
        
    impuesto = (base_tributable * factor) - (rebaja_utm * valor_utm)
    return max(0, round(impuesto))


def calcular_descuentos(total_imponible: int, valor_utm: float, config: dict = None) -> DetalleDescuentos:
    """
    Calcula los descuentos legales e impuestos sobre el total imponible.
    
    NOTA: La Cuenta de Ahorro NO reduce la base tributable (verificado
    contra liquidación real de septiembre 2026).
    """
    if config is None:
        config = cargar_config_descuentos()

    afp_tasa = config["afp"]["tasa_total_pct"]
    salud_tasa = config["salud"]["tasa_pct"]
    cesantia_tasa = config["seguro_cesantia"]["tasa_pct"]
    cuenta_ahorro_monto = config.get("cuenta_ahorro", config.get("apv", {})).get("monto_fijo", 0)

    afp_monto = round(total_imponible * afp_tasa / 100)
    salud_monto = round(total_imponible * salud_tasa / 100)
    cesantia_monto = round(total_imponible * cesantia_tasa / 100)

    total_leyes_sociales = afp_monto + salud_monto + cesantia_monto
    
    # Base tributable = Imponible - AFP - Fonasa - Cesantía
    # La Cuenta de Ahorro NO reduce la base tributable
    base_tributable = max(0, total_imponible - total_leyes_sociales)
    
    impuesto_unico = calcular_impuesto_unico(base_tributable, valor_utm)

    total_descuentos = total_leyes_sociales + cuenta_ahorro_monto + impuesto_unico

    return DetalleDescuentos(
        afp_nombre=config["afp"]["nombre"],
        afp_tasa=afp_tasa,
        afp_monto=afp_monto,
        salud_sistema=config["salud"]["sistema"],
        salud_tasa=salud_tasa,
        salud_monto=salud_monto,
        cesantia_tasa=cesantia_tasa,
        cesantia_monto=cesantia_monto,
        cuenta_ahorro_monto=cuenta_ahorro_monto,
        total_leyes_sociales=total_leyes_sociales,
        base_tributable=base_tributable,
        impuesto_unico_monto=impuesto_unico,
        total_descuentos=total_descuentos
    )


def calcular_sueldo(
    recaudacion_pesos: int,
    valor_uf: float,
    valor_utm: float,
    imm: int,
    tramos: list,
    tabla_nombre: str = "DNP",
    mes: int = 1,
    anio: int = 2025,
    dias_trabajables: int = 20,
    domingos_festivos: int = 4,
    dias_licencia: int = 0,
    anticipo: int = 0,
    prestamo: int = 0,
    gratificacion: int = 0,
    comision_feriado: int = 0,
    sueldo_base: int = 380000,
    config_descuentos: dict = None
) -> ResultadoCalculo:
    """
    Cálculo completo del sueldo líquido estimado.
    """
    if config_descuentos is None:
        config_descuentos = cargar_config_descuentos()

    recaudacion_uf = calcular_recaudacion_uf(recaudacion_pesos, valor_uf)
    tramo = encontrar_tramo(recaudacion_uf, tramos)

    comision = round(recaudacion_pesos * tramo.comision_pct / 100)
    premio = tramo.premio if recaudacion_uf >= tramo.desde_uf else 0

    # Semana Corrida (solo sobre la comisión pura, NO incluye el premio)
    semana_corrida = calcular_semana_corrida(
        comision=comision,
        dias_trabajables=dias_trabajables,
        domingos_festivos=domingos_festivos,
        dias_licencia=dias_licencia
    )

    asig_internet = config_descuentos.get("asignaciones_no_imponibles", {}).get("internet", 0)

    # Desglose IMM: sueldo base + ajuste
    ajuste_sueldo_base = imm - sueldo_base

    # Totales (Semana corrida, gratificación y feriado son imponibles)
    total_imponible = imm + comision + premio + semana_corrida + gratificacion + comision_feriado
    total_haberes = total_imponible + asig_internet

    # Descuentos legales e impuestos
    descuentos = calcular_descuentos(total_imponible, valor_utm, config_descuentos)

    # Sueldo líquido = Total Haberes - Desc. Legales - Anticipo - Préstamo
    sueldo_liquido = total_haberes - descuentos.total_descuentos - anticipo - prestamo

    resultado = ResultadoCalculo(
        recaudacion_pesos=recaudacion_pesos,
        valor_uf=valor_uf,
        valor_utm=valor_utm,
        mes=mes,
        anio=anio,
        tabla_usada=tabla_nombre,
        recaudacion_uf=recaudacion_uf,
        tramo=tramo,
        sueldo_base=sueldo_base,
        ajuste_sueldo_base=ajuste_sueldo_base,
        imm=imm,
        comision_recaudacion=comision,
        premio=premio,
        
        dias_trabajables=dias_trabajables,
        domingos_festivos=domingos_festivos,
        dias_licencia=dias_licencia,
        dias_efectivos_trabajables=max(1, dias_trabajables - dias_licencia),
        semana_corrida_monto=semana_corrida,
        
        asignacion_internet=asig_internet,
        total_imponible=total_imponible,
        total_haberes=total_haberes,
        descuentos=descuentos,
        anticipo=anticipo,
        prestamo=prestamo,
        gratificacion=gratificacion,
        comision_feriado=comision_feriado,
        sueldo_liquido=sueldo_liquido
    )

    if tramo.estado != "confirmado":
        tramos_confirmados = [t for t in tramos if t.get("estado") == "confirmado"]
        if tramos_confirmados:
            resultado.escenario_alternativo = calcular_sueldo(
                recaudacion_pesos=recaudacion_pesos,
                valor_uf=valor_uf,
                valor_utm=valor_utm,
                imm=imm,
                tramos=tramos_confirmados,
                tabla_nombre=tabla_nombre,
                mes=mes,
                anio=anio,
                dias_trabajables=dias_trabajables,
                domingos_festivos=domingos_festivos,
                dias_licencia=dias_licencia,
                anticipo=anticipo,
                prestamo=prestamo,
                gratificacion=gratificacion,
                comision_feriado=comision_feriado,
                sueldo_base=sueldo_base,
                config_descuentos=config_descuentos
            )

    return resultado


# ═══════════════════════════════════════════════════════════════════════════════
# Utilidades de Formato
# ═══════════════════════════════════════════════════════════════════════════════

def formato_clp(monto: int) -> str:
    if monto < 0:
        return f"-$ {abs(monto):,.0f}".replace(",", ".")
    return f"$ {monto:,.0f}".replace(",", ".")


def formato_uf(valor: float) -> str:
    entero = int(valor)
    decimales = round((valor - entero) * 100)
    parte_entera = f"{entero:,}".replace(",", ".")
    return f"{parte_entera},{decimales:02d} UF"
