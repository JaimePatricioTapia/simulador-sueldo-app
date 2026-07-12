"""
tramos.py — Gestión de tablas de tramos de comisión (CRUD dinámico)

Responsabilidades:
- Leer/escribir tablas de tramos desde JSON
- Agregar, editar, eliminar tramos y tablas
- Validar coherencia (sin huecos ni solapamientos)
- Calcular rangos en pesos dinámicamente a partir de valor UF
"""

import json
from pathlib import Path
from typing import Optional

# ─── Ruta de datos ───────────────────────────────────────────────────────────
_DATA_DIR = Path(__file__).parent.parent / "data"
_TRAMOS_FILE = _DATA_DIR / "tramos_comision.json"


# ═══════════════════════════════════════════════════════════════════════════════
# Lectura y Escritura
# ═══════════════════════════════════════════════════════════════════════════════

def cargar_tablas() -> dict:
    """Carga todas las tablas de tramos desde el JSON."""
    if not _TRAMOS_FILE.exists():
        return {"tablas": {}}
    with open(_TRAMOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_tablas(data: dict) -> None:
    """Guarda el dict completo de tablas al JSON."""
    with open(_TRAMOS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def listar_tablas() -> list:
    """Retorna lista de IDs de tablas disponibles."""
    data = cargar_tablas()
    return list(data.get("tablas", {}).keys())


def obtener_tabla(tabla_id: str) -> Optional[dict]:
    """Retorna una tabla específica o None."""
    data = cargar_tablas()
    return data.get("tablas", {}).get(tabla_id)


def obtener_tramos(tabla_id: str) -> list:
    """Retorna la lista de tramos de una tabla."""
    tabla = obtener_tabla(tabla_id)
    if tabla is None:
        return []
    return tabla.get("tramos", [])


# ═══════════════════════════════════════════════════════════════════════════════
# CRUD de Tablas
# ═══════════════════════════════════════════════════════════════════════════════

def crear_tabla(tabla_id: str, nombre_display: str, tramos: list = None) -> None:
    """Crea una nueva tabla de tramos."""
    data = cargar_tablas()
    data["tablas"][tabla_id] = {
        "nombre_display": nombre_display,
        "tramos": tramos or []
    }
    guardar_tablas(data)


def eliminar_tabla(tabla_id: str) -> bool:
    """Elimina una tabla. Retorna True si existía."""
    data = cargar_tablas()
    if tabla_id in data.get("tablas", {}):
        del data["tablas"][tabla_id]
        guardar_tablas(data)
        return True
    return False


def actualizar_tramos(tabla_id: str, tramos: list) -> None:
    """Reemplaza los tramos completos de una tabla."""
    data = cargar_tablas()
    if tabla_id not in data.get("tablas", {}):
        raise ValueError(f"La tabla '{tabla_id}' no existe")
    data["tablas"][tabla_id]["tramos"] = tramos
    guardar_tablas(data)


# ═══════════════════════════════════════════════════════════════════════════════
# Cálculos Derivados
# ═══════════════════════════════════════════════════════════════════════════════

def tramos_con_pesos(tramos: list, valor_uf: float) -> list:
    """
    Calcula los rangos en pesos para cada tramo a partir del valor UF vigente.
    Esto NUNCA se guarda — siempre se calcula en tiempo real.

    Retorna lista de tramos enriquecidos con:
    - recuperacion_desde_pesos: int
    - recuperacion_hasta_pesos: int o None (sin tope)
    """
    resultado = []
    for tramo in tramos:
        enriquecido = {**tramo}
        enriquecido["recuperacion_desde_pesos"] = round(tramo["desde_uf"] * valor_uf)
        if tramo["hasta_uf"] is not None:
            enriquecido["recuperacion_hasta_pesos"] = round(tramo["hasta_uf"] * valor_uf)
        else:
            enriquecido["recuperacion_hasta_pesos"] = None
        resultado.append(enriquecido)
    return resultado


# ═══════════════════════════════════════════════════════════════════════════════
# Validación
# ═══════════════════════════════════════════════════════════════════════════════

def validar_tramos(tramos: list) -> list:
    """
    Valida coherencia de los tramos.
    Retorna lista de errores (vacía si todo OK).
    """
    errores = []

    if not tramos:
        errores.append("La tabla no tiene tramos definidos")
        return errores

    for i, tramo in enumerate(tramos):
        # Validar campos requeridos
        if "desde_uf" not in tramo:
            errores.append(f"Tramo {i+1}: falta 'desde_uf'")
        if "comision_pct" not in tramo:
            errores.append(f"Tramo {i+1}: falta 'comision_pct'")
        if tramo.get("comision_pct", 0) < 0:
            errores.append(f"Tramo {i+1}: la comisión no puede ser negativa")
        if tramo.get("premio", 0) < 0:
            errores.append(f"Tramo {i+1}: el premio no puede ser negativo")

    # Validar que el primer tramo empiece en 0
    if tramos[0].get("desde_uf", -1) != 0:
        errores.append("El primer tramo debe empezar en 0 UF")

    # Validar que el último tramo no tenga tope (hasta_uf = null)
    if tramos[-1].get("hasta_uf") is not None:
        errores.append("El último tramo debe tener 'hasta_uf' sin tope (null)")

    # Validar continuidad entre tramos
    for i in range(len(tramos) - 1):
        actual_hasta = tramos[i].get("hasta_uf")
        siguiente_desde = tramos[i + 1].get("desde_uf", 0)

        if actual_hasta is None:
            errores.append(f"Tramo {i+1}: tiene 'hasta_uf' sin tope pero no es el último")
        elif siguiente_desde > actual_hasta + 1:
            errores.append(
                f"Hay un hueco entre tramo {i+1} (hasta {actual_hasta} UF) "
                f"y tramo {i+2} (desde {siguiente_desde} UF)"
            )

    return errores


def tiene_tramos_no_confirmados(tramos: list) -> bool:
    """Verifica si hay algún tramo con estado != 'confirmado'."""
    return any(
        tramo.get("estado", "confirmado") != "confirmado"
        for tramo in tramos
    )
