"""
pdf_generator.py — Genera resúmenes PDF del cálculo de sueldo

Usa fpdf2 para crear PDFs limpios con desglose completo del cálculo,
formateado en pesos chilenos.
"""

from fpdf import FPDF
from io import BytesIO
from datetime import datetime
from modules.calculos import ResultadoCalculo, formato_clp


# ─── Meses en español ────────────────────────────────────────────────────────
_MESES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]


def generar_pdf_resumen(resultado: ResultadoCalculo) -> bytes:
    """
    Genera un PDF con el resumen del cálculo de sueldo.
    Retorna bytes del PDF listo para descargar.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ─── Header ──────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(0, 122, 255)  # Azul Apple
    pdf.cell(0, 12, "Simulador de Sueldo", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    mes_nombre = _MESES[resultado.mes] if 1 <= resultado.mes <= 12 else str(resultado.mes)
    pdf.cell(0, 8, f"Estimación para {mes_nombre} {resultado.anio}", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}",
             align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)

    # ─── Resultado Principal ─────────────────────────────────────────────
    pdf.set_fill_color(245, 245, 247)  # Gris Apple
    pdf.set_draw_color(220, 220, 220)
    pdf.rect(15, pdf.get_y(), 180, 28, style="DF")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "Tu sueldo líquido estimado", align="C",
             new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(0, 122, 255)
    pdf.cell(0, 16, formato_clp(resultado.sueldo_liquido), align="C",
             new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)

    # ─── Datos de Entrada ────────────────────────────────────────────────
    pdf.set_text_color(30, 30, 31)
    _seccion_titulo(pdf, "Datos de Entrada")

    _fila(pdf, "Recaudación", formato_clp(resultado.recaudacion_pesos))
    _fila(pdf, "Valor UF utilizado", f"$ {resultado.valor_uf:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    _fila(pdf, "Recaudación en UF", f"{resultado.recaudacion_uf:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    _fila(pdf, "Tramo alcanzado", resultado.tramo.descripcion)
    _fila(pdf, "Tabla de comisión", resultado.tabla_usada)

    pdf.ln(4)

    # ─── Haberes ─────────────────────────────────────────────────────────
    _seccion_titulo(pdf, "Haberes")

    _fila(pdf, "Ingreso Mínimo Mensual (IMM)", formato_clp(resultado.imm))
    _fila(pdf, f"Comisión por recaudación ({resultado.tramo.comision_pct}%)",
          formato_clp(resultado.comision_recaudacion))
    if resultado.premio > 0:
        _fila(pdf, "Premio del tramo", formato_clp(resultado.premio))
    _fila(pdf, "Semana Corrida", formato_clp(resultado.semana_corrida_monto))
    _fila(pdf, "Asignación Internet (no imponible)", formato_clp(resultado.asignacion_internet))

    pdf.set_font("Helvetica", "B", 10)
    _fila(pdf, "TOTAL HABERES", formato_clp(resultado.total_haberes), bold=True)

    pdf.ln(4)

    # ─── Descuentos ──────────────────────────────────────────────────────
    _seccion_titulo(pdf, "Descuentos Legales e Impuestos")

    d = resultado.descuentos
    _fila(pdf, f"{d.afp_nombre} ({d.afp_tasa}%)", f"-{formato_clp(d.afp_monto)}")
    _fila(pdf, f"Salud {d.salud_sistema} ({d.salud_tasa}%)", f"-{formato_clp(d.salud_monto)}")
    _fila(pdf, f"Seguro Cesantía ({d.cesantia_tasa}%)", f"-{formato_clp(d.cesantia_monto)}")
    if d.apv_monto > 0:
        _fila(pdf, "APV Individual Tributable", f"-{formato_clp(d.apv_monto)}")
    
    _fila(pdf, "Impuesto Único de 2da Categoría", f"-{formato_clp(d.impuesto_unico_monto)}")

    pdf.set_font("Helvetica", "B", 10)
    _fila(pdf, "TOTAL DESCUENTOS", f"-{formato_clp(d.total_descuentos)}", bold=True)

    pdf.ln(6)

    # ─── Línea final ─────────────────────────────────────────────────────
    pdf.set_draw_color(0, 122, 255)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(0, 122, 255)
    pdf.cell(95, 10, "SUELDO LÍQUIDO ESTIMADO", align="L")
    pdf.cell(85, 10, formato_clp(resultado.sueldo_liquido), align="R",
             new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)

    # ─── Disclaimer ──────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(0, 4,
        "Este es un cálculo estimativo y no constituye una liquidación de sueldo oficial. "
        "No incluye anticipos u otros descuentos particulares de la empresa. "
        "Consulta tu liquidación oficial para los montos definitivos."
    )

    return pdf.output()


# ─── Helpers internos ────────────────────────────────────────────────────────

def _seccion_titulo(pdf: FPDF, titulo: str):
    """Dibuja un título de sección con línea decorativa."""
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 30, 31)
    pdf.cell(0, 8, titulo, new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(230, 230, 230)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(2)


def _fila(pdf: FPDF, etiqueta: str, valor: str, bold: bool = False):
    """Dibuja una fila de detalle (etiqueta a la izquierda, valor a la derecha)."""
    if bold:
        pdf.set_font("Helvetica", "B", 10)
    else:
        pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(110, 6, etiqueta, align="L")
    pdf.set_text_color(30, 30, 31)
    pdf.cell(70, 6, valor, align="R", new_x="LMARGIN", new_y="NEXT")
