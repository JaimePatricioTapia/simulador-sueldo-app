"""
indicadores.py — Gestión de UF, IMM y UTM históricos + integración API findic.cl

Responsabilidades:
- Cargar/guardar UF, IMM y UTM desde archivos JSON
- Consultar la API pública de UF (findic.cl) para obtener valor vigente
- Cachear los últimos ~30 días de UF desde la API
- Diferenciar UF "en vivo" (simulación futura) vs UF "histórica" (mes cerrado)
- Buscar el valor UF, IMM o UTM para un período dado

Regla de UF para meses cerrados (reconstrucción de sueldos pasados):
  El sueldo de un mes se calcula con la UF de cierre del mes de la recuperación.
  Ejemplo: sueldo de junio se calcula con la UF de cierre de mayo.
  La API findic.cl solo se usa para simulación del mes actual/futuro.
"""

import json
import os
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Tuple
import urllib.request
import urllib.error

# ─── Rutas de datos ──────────────────────────────────────────────────────────
_DATA_DIR = Path(__file__).parent.parent / "data"
_UF_FILE = _DATA_DIR / "uf_historica.json"
_IMM_FILE = _DATA_DIR / "imm_historica.json"
_UTM_FILE = _DATA_DIR / "utm_historica.json"

# ─── API ─────────────────────────────────────────────────────────────────────
_UF_API_URL = "https://findic.cl/api/uf"
_UTM_API_URL = "https://findic.cl/api/utm"
_API_TIMEOUT = 5  # segundos


# ═══════════════════════════════════════════════════════════════════════════════
# Utilidades genéricas para archivos JSON de indicadores
# ═══════════════════════════════════════════════════════════════════════════════

def _cargar_json(filepath: Path) -> dict:
    """Carga un JSON de indicadores, filtrando claves _metadata."""
    if not filepath.exists():
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_")}


def _guardar_json(filepath: Path, data: dict) -> None:
    """Guarda un dict al JSON, preservando _metadata existente."""
    existing = {}
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            existing = json.load(f)

    metadata = {k: v for k, v in existing.items() if k.startswith("_")}
    merged = {**data, **metadata}

    sorted_data = dict(sorted(
        merged.items(),
        key=lambda x: (x[0].startswith("_"), x[0])
    ))

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(sorted_data, f, indent=2, ensure_ascii=False)


def _buscar_vigente(data: dict, anio: int, mes: int):
    """
    Busca el valor vigente más cercano anterior o igual al período dado.
    Funciona para IMM y UTM (valores escalonados por período).
    """
    clave_consulta = f"{anio:04d}-{mes:02d}"
    if not data:
        return None

    claves_ordenadas = sorted(data.keys())
    valor_vigente = None

    for clave in claves_ordenadas:
        if clave <= clave_consulta:
            valor_vigente = data[clave]
        else:
            break

    return valor_vigente


# ═══════════════════════════════════════════════════════════════════════════════
# UF — Lectura y Escritura
# ═══════════════════════════════════════════════════════════════════════════════

def cargar_uf_historica() -> dict:
    """Carga el archivo JSON de UF histórica. Retorna dict {clave_mes: valor}."""
    return _cargar_json(_UF_FILE)


def guardar_uf_historica(data: dict) -> None:
    """Guarda el dict de UF histórica al JSON, preservando _metadata."""
    _guardar_json(_UF_FILE, data)


def obtener_uf(anio: int, mes: int) -> Optional[float]:
    """Busca el valor UF para un mes/año específico."""
    clave = f"{anio:04d}-{mes:02d}"
    data = cargar_uf_historica()
    return data.get(clave)


def agregar_uf(anio: int, mes: int, valor: float) -> None:
    """Agrega o actualiza un valor UF para un mes/año."""
    clave = f"{anio:04d}-{mes:02d}"
    data = cargar_uf_historica()
    data[clave] = round(valor, 2)
    guardar_uf_historica(data)


# ═══════════════════════════════════════════════════════════════════════════════
# UF — API findic.cl
# ═══════════════════════════════════════════════════════════════════════════════

def consultar_uf_api() -> Tuple[Optional[float], Optional[str], list, Optional[str]]:
    """
    Consulta la API pública de UF.

    Returns:
        Tuple de:
        - uf_vigente: float o None si falla
        - fecha_vigente: str "YYYY-MM-DD" o None
        - serie_completa: lista de {"fecha": str, "valor": float}
        - error_msg: None si OK, str con mensaje si hubo error
    """
    try:
        req = urllib.request.Request(_UF_API_URL, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=_API_TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        serie = body.get("serie", [])
        if not serie:
            return None, None, [], "La API respondió pero sin datos de UF"

        uf_vigente = serie[0]["valor"]
        fecha_vigente = serie[0]["fecha"]
        return uf_vigente, fecha_vigente, serie, None

    except urllib.error.URLError as e:
        return None, None, [], f"Sin conexión a internet: {e.reason}"
    except Exception as e:
        return None, None, [], f"Error consultando UF: {str(e)}"


def actualizar_uf_desde_api() -> Tuple[Optional[float], Optional[str], Optional[str]]:
    """
    Consulta la API, actualiza el caché local con los ~30 días de historial,
    y retorna el valor vigente.

    Returns:
        Tuple de:
        - uf_vigente: float o None
        - fecha_vigente: str o None
        - error_msg: None si OK, str si hubo error
    """
    uf_vigente, fecha_vigente, serie, error = consultar_uf_api()

    if error:
        return None, None, error

    # Actualizar caché local con toda la serie (agrupada por mes, último valor)
    data = cargar_uf_historica()
    meses_actualizados = {}

    for punto in serie:
        fecha_str = punto["fecha"]  # "YYYY-MM-DD"
        valor = punto["valor"]
        clave_mes = fecha_str[:7]  # "YYYY-MM"

        # Guardar el valor más reciente de cada mes
        if clave_mes not in meses_actualizados:
            meses_actualizados[clave_mes] = valor

    # Mergear con datos existentes (API sobrescribe los meses que cubre)
    data.update(meses_actualizados)
    guardar_uf_historica(data)

    return uf_vigente, fecha_vigente, None


def es_mes_pasado(anio: int, mes: int) -> bool:
    """Determina si un período ya es un mes cerrado (pasado)."""
    hoy = date.today()
    if anio < hoy.year:
        return True
    if anio == hoy.year and mes < hoy.month:
        return True
    return False


def obtener_uf_con_fallback(anio: int, mes: int) -> Tuple[float, str, bool]:
    """
    Obtiene la UF correcta para el período según la regla:
    - Mes pasado (cerrado): usa UF de cierre del mes desde el caché local
    - Mes actual o futuro: usa API en vivo (con fallback a caché)

    Returns:
        Tuple de:
        - valor_uf: float
        - fuente: str describiendo de dónde viene
        - es_cache: True si usó caché en vez de API en vivo
    """
    hoy = date.today()
    es_actual = (anio == hoy.year and mes == hoy.month)
    es_pasado = es_mes_pasado(anio, mes)

    if es_pasado:
        # ── Mes cerrado: usar UF histórica del caché ─────────────────────
        valor = obtener_uf(anio, mes)
        if valor is not None:
            return valor, f"UF cierre {anio}-{mes:02d} (histórica)", True

        # Si no hay dato del mes exacto, intentar el mes anterior más cercano
        data = cargar_uf_historica()
        valor_cercano = _buscar_vigente(data, anio, mes)
        if valor_cercano is not None:
            return valor_cercano, "UF histórica aproximada (mes más cercano)", True

        return 0.0, "no disponible", True

    elif es_actual:
        # ── Mes actual: intentar API, fallback a caché ───────────────────
        uf, fecha, error = actualizar_uf_desde_api()
        if uf is not None:
            return uf, f"API findic.cl ({fecha})", False

        # Fallback a caché local
        valor = obtener_uf(anio, mes)
        if valor is not None:
            return valor, "caché local (sin conexión)", True

        return 0.0, "no disponible", True

    else:
        # ── Mes futuro: intentar API para UF vigente, o caché ────────────
        uf, fecha, error = actualizar_uf_desde_api()
        if uf is not None:
            return uf, f"UF vigente API ({fecha}) — proyección", False

        # Fallback a UF del último mes disponible
        data = cargar_uf_historica()
        valor_cercano = _buscar_vigente(data, anio, mes)
        if valor_cercano is not None:
            return valor_cercano, "UF proyectada (último valor conocido)", True

        return 0.0, "no disponible", True


# ═══════════════════════════════════════════════════════════════════════════════
# IMM — Lectura y Escritura
# ═══════════════════════════════════════════════════════════════════════════════

def cargar_imm_historica() -> dict:
    """Carga el archivo JSON de IMM histórico."""
    return _cargar_json(_IMM_FILE)


def guardar_imm_historica(data: dict) -> None:
    """Guarda el dict de IMM al JSON."""
    _guardar_json(_IMM_FILE, data)


def obtener_imm(anio: int, mes: int) -> Optional[int]:
    """
    Busca el IMM vigente para un mes/año.
    Lógica: encuentra el período vigente más cercano anterior o igual.
    """
    data = cargar_imm_historica()
    result = _buscar_vigente(data, anio, mes)
    return int(result) if result is not None else None


def agregar_imm(anio: int, mes: int, valor: int) -> None:
    """Agrega o actualiza un valor IMM para un período."""
    clave = f"{anio:04d}-{mes:02d}"
    data = cargar_imm_historica()
    data[clave] = valor
    guardar_imm_historica(data)


# ═══════════════════════════════════════════════════════════════════════════════
# UTM — Lectura y Escritura
# ═══════════════════════════════════════════════════════════════════════════════

def cargar_utm_historica() -> dict:
    """Carga el archivo JSON de UTM histórico."""
    return _cargar_json(_UTM_FILE)


def guardar_utm_historica(data: dict) -> None:
    """Guarda el dict de UTM al JSON."""
    _guardar_json(_UTM_FILE, data)


def obtener_utm(anio: int, mes: int) -> Optional[int]:
    """
    Obsoleto: usar obtener_utm_con_fallback para usar la API en vivo.
    """
    clave = f"{anio:04d}-{mes:02d}"
    data = cargar_utm_historica()
    if clave in data:
        return int(data[clave])
    result = _buscar_vigente(data, anio, mes)
    return int(result) if result is not None else None


def consultar_utm_api() -> Tuple[Optional[int], Optional[str], list, Optional[str]]:
    """
    Consulta la API pública de UTM. Retorna la serie histórica.
    """
    try:
        req = urllib.request.Request(_UTM_API_URL, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=_API_TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        serie = body.get("serie", [])
        if not serie:
            return None, None, [], "La API respondió pero sin datos de UTM"

        utm_vigente = int(serie[0]["valor"])
        fecha_vigente = serie[0]["fecha"]
        return utm_vigente, fecha_vigente, serie, None

    except urllib.error.URLError as e:
        return None, None, [], f"Sin conexión a internet: {e.reason}"
    except Exception as e:
        return None, None, [], f"Error consultando UTM: {str(e)}"


def actualizar_utm_desde_api() -> Tuple[Optional[int], Optional[str], list, Optional[str]]:
    """
    Consulta la API, actualiza el caché local, y retorna valor vigente y serie.
    """
    utm_vigente, fecha_vigente, serie, error = consultar_utm_api()

    if error:
        return None, None, [], error

    # Actualizar caché local
    data = cargar_utm_historica()
    meses_actualizados = {}

    for punto in serie:
        fecha_str = punto["fecha"]  # "YYYY-MM-DD"
        valor = int(punto["valor"])
        clave_mes = fecha_str[:7]  # "YYYY-MM"
        meses_actualizados[clave_mes] = valor

    data.update(meses_actualizados)
    guardar_utm_historica(data)

    return utm_vigente, fecha_vigente, serie, None


def obtener_utm_con_fallback(anio: int, mes: int) -> Tuple[Optional[int], str, bool]:
    """
    Obtiene la UTM correcta usando la API findic.cl o el caché local.
    - Mes pasado: busca la fecha YYYY-MM-01 en la serie API o caché local.
    - Mes actual/futuro: usa serie[0] (el más reciente).
    """
    es_pasado = es_mes_pasado(anio, mes)
    clave = f"{anio:04d}-{mes:02d}"
    fecha_buscar = f"{anio:04d}-{mes:02d}-01"

    # Siempre intentamos actualizar desde la API para tener la serie más reciente
    utm_vigente, fecha_vigente, serie, error = actualizar_utm_desde_api()

    if es_pasado:
        # Reconstruir sueldo pasado
        # 1. Buscar en la serie de la API
        if serie:
            for punto in serie:
                if punto["fecha"] == fecha_buscar:
                    return int(punto["valor"]), f"API findic.cl ({fecha_buscar})", False

        # 2. Si no está en la API (ej: anterior a 2024), buscar en caché local
        data = cargar_utm_historica()
        if clave in data:
            return int(data[clave]), "Caché local (histórica)", True
        
        # 3. Fallback a la más cercana anterior del caché
        result = _buscar_vigente(data, anio, mes)
        if result is not None:
            return int(result), "Caché local (aproximada)", True
            
        return None, "no disponible", True

    else:
        # Simular sueldo actual/futuro
        if utm_vigente is not None:
            return utm_vigente, f"API findic.cl ({fecha_vigente})", False

        # Fallback a caché local si la API falló
        data = cargar_utm_historica()
        result = _buscar_vigente(data, anio, mes)
        if result is not None:
            return int(result), "Caché local (sin conexión)", True
            
        return None, "no disponible", True


def agregar_utm(anio: int, mes: int, valor: int) -> None:
    """Agrega o actualiza un valor UTM para un mes/año."""
    clave = f"{anio:04d}-{mes:02d}"
    data = cargar_utm_historica()
    data[clave] = valor
    guardar_utm_historica(data)
