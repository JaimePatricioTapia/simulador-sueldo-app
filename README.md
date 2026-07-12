# 💰 Simulador de Sueldo

Aplicación web que permite simular y entender tu sueldo según tu recaudación de cobranza, con cálculos de comisiones por tramos UF, descuentos legales chilenos y exportación a PDF.

## ✨ Características

- **Simulación en vivo**: ingresa tu recaudación y ve el sueldo líquido estimado al instante
- **Valor UF automático**: se actualiza desde la API de [findic.cl](https://findic.cl/api/uf)
- **Tramos de comisión configurables**: tabla de tramos editable con premios
- **Descuentos e Impuestos Reales**: AFP, Fonasa/Isapre, Seguro Cesantía, APV, e Impuesto Único de 2da Categoría (según tramos SII usando UTM)
- **Cálculo de Semana Corrida**: integrado y configurable según días trabajables, festivos y licencias
- **Historial de cálculos**: guarda y compara tus estimaciones
- **Exportar a PDF**: descarga un resumen profesional de cada cálculo
- **Diseño Apple**: interfaz limpia, moderna y fácil de usar

## 🚀 Instalación Local

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/simulador-sueldo-app.git
cd simulador-sueldo-app

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
streamlit run app.py
```

## ☁️ Deploy en Streamlit Community Cloud

1. Sube este repositorio a GitHub
2. Ve a [share.streamlit.io](https://share.streamlit.io)
3. Conecta tu cuenta de GitHub
4. Selecciona este repositorio y `app.py` como archivo principal
5. ¡Listo!

## 📁 Estructura del Proyecto

```
simulador-sueldo-app/
├── app.py                        # Simulador principal
├── pages/
│   ├── 1_📊_Mi_Historial.py      # Histórico de cálculos
│   └── 2_⚙️_Configuración.py     # Gestión de tramos, UF, IMM
├── modules/
│   ├── calculos.py               # Motor de cálculo
│   ├── tramos.py                 # Gestión de tablas de tramos
│   ├── indicadores.py            # UF e IMM + API findic.cl
│   └── pdf_generator.py          # Exportar a PDF
├── data/
│   ├── tramos_comision.json      # Tablas de tramos
│   ├── uf_historica.json         # Valores UF históricos
│   ├── imm_historica.json        # Valores IMM
│   ├── utm_historica.json        # Valores UTM (Impuesto Único)
│   └── descuentos_config.json    # Configuración de descuentos
├── .streamlit/
│   └── config.toml               # Tema visual
├── requirements.txt
└── README.md
```

## 📊 Tabla de Comisiones (DNP)

| Tramo | Desde UF | Hasta UF | Comisión | Premio |
|-------|----------|----------|----------|--------|
| 1     | 0        | 315      | 1.25%    | —      |
| 2     | 316      | 474      | 1.45%    | —      |
| 3     | 475      | 631      | 1.55%    | $10.000 |
| 4     | 632      | 789      | 1.80%    | $40.000 |
| 5     | 790      | 946      | 2.00%    | $60.000 |
| 6     | 947      | 1.100    | 2.20%    | $80.000 |
| 7     | 1.101    | ∞        | 2.30%    | $100.000 |

## 🔒 Datos

Los datos se almacenan localmente en archivos JSON dentro de la carpeta `data/`. No se envía información personal a ningún servidor externo (la única conexión externa es para obtener el valor UF vigente).

---

Desarrollado con ❤️ usando [Streamlit](https://streamlit.io)
