"""
test_liquidaciones_2026.py — Suite de pruebas automatizadas contra las liquidaciones oficiales del 2026.

Comprueba que el modelo calcula exactamente los mismos montos ($0 de diferencia en todos los conceptos)
para cada mes entre febrero y septiembre de 2026.
"""

import unittest
from modules import calculos as c
from modules.tramos import obtener_tramos
from modules.indicadores import obtener_imm, obtener_utm


class TestLiquidaciones2026(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tramos = obtener_tramos("DNP")

    def test_mes_a_mes_2026(self):
        meses_test = [
            {
                "mes": 2, "anio": 2026,
                "nombre": "Febrero 2026",
                "recaudacion_pesos": 28813833,
                "valor_uf": 39665.79,
                "anticipo": 170000, "prestamo": 0, "feriado": 0, "gratificacion": 0,
                "esperado": {
                    "sueldo_base": 380000, "ajuste": 159000, "imm": 539000,
                    "comision": 518649, "sc": 103730, "premio": 40000,
                    "total_imp": 1201379, "internet": 15000, "total_hab": 1216379,
                    "afp": 135395, "salud": 84097, "ces": 7208, "cuenta_ahorro": 15000,
                    "base_trib": 974679, "imp": 1397, "desc_leg": 243097,
                    "anticipo": 170000, "prestamo": 0, "liq": 803282
                }
            },
            {
                "mes": 3, "anio": 2026,
                "nombre": "Marzo 2026",
                "recaudacion_pesos": 20878516,
                "valor_uf": 39833.62,
                "anticipo": 170000, "prestamo": 0, "feriado": 477116, "gratificacion": 0,
                "esperado": {
                    "sueldo_base": 380000, "ajuste": 159000, "imm": 539000,
                    "comision": 323617, "sc": 73549, "premio": 10000,
                    "total_imp": 1423282, "internet": 15000, "total_hab": 1438282,
                    "afp": 160404, "salud": 99630, "ces": 8540, "cuenta_ahorro": 15000,
                    "base_trib": 1154708, "imp": 8448, "desc_leg": 292022,
                    "anticipo": 170000, "prestamo": 0, "liq": 976260
                }
            },
            {
                "mes": 4, "anio": 2026,
                "nombre": "Abril 2026",
                "recaudacion_pesos": 51309739,
                "valor_uf": 41015.0,
                "anticipo": 180000, "prestamo": 70000, "feriado": 0, "gratificacion": 743789,
                "dias_trabajables": 22, "domingos_festivos": 4,  # RRHH usó 22/4 (sin descontar Viernes Santo)
                "esperado": {
                    "sueldo_base": 380000, "ajuste": 159000, "imm": 539000,
                    "comision": 1180124, "sc": 214568, "premio": 100000,
                    "total_imp": 2777481, "internet": 15000, "total_hab": 2792481,
                    "afp": 313022, "salud": 194424, "ces": 16665, "cuenta_ahorro": 15000,
                    "base_trib": 2253370, "imp": 58663, "desc_leg": 597774,
                    "anticipo": 180000, "prestamo": 70000, "liq": 1944707
                }
            },
            {
                "mes": 5, "anio": 2026,
                "nombre": "Mayo 2026",
                "recaudacion_pesos": 31442650,
                "valor_uf": 39800.0,
                "anticipo": 160000, "prestamo": 72011, "feriado": 33793, "gratificacion": 0,
                "esperado": {
                    "sueldo_base": 380000, "ajuste": 159000, "imm": 539000,
                    "comision": 628853, "sc": 231683, "premio": 60000,
                    "total_imp": 1493329, "internet": 15000, "total_hab": 1508329,
                    "afp": 168298, "salud": 104533, "ces": 8960, "cuenta_ahorro": 15000,
                    "base_trib": 1211538, "imp": 10344, "desc_leg": 307135,
                    "anticipo": 160000, "prestamo": 72011, "liq": 969183
                }
            },
            {
                "mes": 6, "anio": 2026,
                "nombre": "Junio 2026",
                "recaudacion_pesos": 23265000,
                "valor_uf": 24489.0,
                "anticipo": 180000, "prestamo": 72011, "feriado": 110110, "gratificacion": 0,
                "esperado": {
                    "sueldo_base": 380000, "ajuste": 173553, "imm": 553553,
                    "comision": 511830, "sc": 121864, "premio": 80000,
                    "total_imp": 1377357, "internet": 15000, "total_hab": 1392357,
                    "afp": 155228, "salud": 96415, "ces": 8264, "cuenta_ahorro": 15000,
                    "base_trib": 1117450, "imp": 6085, "desc_leg": 280992,
                    "anticipo": 180000, "prestamo": 72011, "liq": 859354
                }
            },
            {
                "mes": 7, "anio": 2026,
                "nombre": "Julio 2026",
                "recaudacion_pesos": 67766320,
                "valor_uf": 40844.79,
                "anticipo": 230000, "prestamo": 0, "feriado": 0, "gratificacion": 0,
                "esperado": {
                    "sueldo_base": 380000, "ajuste": 173553, "imm": 553553,
                    "comision": 1694158, "sc": 385036, "premio": 140000,
                    "total_imp": 2772747, "internet": 15000, "total_hab": 2787747,
                    "afp": 312489, "salud": 194092, "ces": 16636, "cuenta_ahorro": 15000,
                    "base_trib": 2249530, "imp": 55293, "desc_leg": 593510,
                    "anticipo": 230000, "prestamo": 0, "liq": 1964237
                }
            },
            {
                "mes": 8, "anio": 2026,
                "nombre": "Agosto 2026",
                "recaudacion_pesos": 46859217,
                "valor_uf": 40951.0,
                "anticipo": 240000, "prestamo": 0, "feriado": 0, "gratificacion": 0,
                "esperado": {
                    "sueldo_base": 380000, "ajuste": 173553, "imm": 553553,
                    "comision": 1077762, "sc": 256610, "premio": 100000,
                    "total_imp": 1987925, "internet": 15000, "total_hab": 2002925,
                    "afp": 224039, "salud": 139155, "ces": 11928, "cuenta_ahorro": 15000,
                    "base_trib": 1612803, "imp": 25822, "desc_leg": 415944,
                    "anticipo": 240000, "prestamo": 0, "liq": 1346981
                }
            },
            {
                "mes": 9, "anio": 2026,
                "nombre": "Septiembre 2026",
                "recaudacion_pesos": 69138960,
                "valor_uf": 41057.2,
                "anticipo": 240000, "prestamo": 0, "feriado": 0, "gratificacion": 0,
                "esperado": {
                    "sueldo_base": 380000, "ajuste": 173553, "imm": 553553,
                    "comision": 1728474, "sc": 411541, "premio": 150000,
                    "total_imp": 2843568, "internet": 15000, "total_hab": 2858568,
                    "afp": 320470, "salud": 199050, "ces": 17061, "cuenta_ahorro": 15000,
                    "base_trib": 2306987, "imp": 59764, "desc_leg": 611345,
                    "anticipo": 240000, "prestamo": 0, "liq": 2007223
                }
            }
        ]

        for t in meses_test:
            m = t["mes"]
            a = t["anio"]
            imm = obtener_imm(a, m)
            utm = obtener_utm(a, m)
            dias_auto, fest_auto = c.calcular_dias_mes(a, m)
            dias = t.get("dias_trabajables", dias_auto)
            fest = t.get("domingos_festivos", fest_auto)

            res = c.calcular_sueldo(
                recaudacion_pesos=t["recaudacion_pesos"],
                valor_uf=t["valor_uf"],
                valor_utm=utm,
                imm=imm,
                tramos=self.tramos,
                mes=m,
                anio=a,
                dias_trabajables=dias,
                domingos_festivos=fest,
                anticipo=t["anticipo"],
                prestamo=t["prestamo"],
                gratificacion=t["gratificacion"],
                comision_feriado=t["feriado"]
            )

            e = t["esperado"]

            # Validar todos los conceptos
            self.assertEqual(res.sueldo_base, e["sueldo_base"], f"{t['nombre']} - Sueldo Base")
            self.assertEqual(res.ajuste_sueldo_base, e["ajuste"], f"{t['nombre']} - Ajuste Sueldo Base")
            self.assertEqual(res.imm, e["imm"], f"{t['nombre']} - IMM")
            self.assertEqual(res.comision_recaudacion, e["comision"], f"{t['nombre']} - Comisión")
            self.assertEqual(res.semana_corrida_monto, e["sc"], f"{t['nombre']} - Semana Corrida")
            self.assertEqual(res.premio, e["premio"], f"{t['nombre']} - Premio")
            self.assertEqual(res.total_imponible, e["total_imp"], f"{t['nombre']} - Total Imponible")
            self.assertEqual(res.asignacion_internet, e["internet"], f"{t['nombre']} - Internet")
            self.assertEqual(res.total_haberes, e["total_hab"], f"{t['nombre']} - Total Haberes")
            self.assertEqual(res.descuentos.afp_monto, e["afp"], f"{t['nombre']} - AFP")
            self.assertEqual(res.descuentos.salud_monto, e["salud"], f"{t['nombre']} - Salud")
            self.assertEqual(res.descuentos.cesantia_monto, e["ces"], f"{t['nombre']} - Cesantía")
            self.assertEqual(res.descuentos.cuenta_ahorro_monto, e["cuenta_ahorro"], f"{t['nombre']} - Cuenta Ahorro")
            self.assertEqual(res.descuentos.base_tributable, e["base_trib"], f"{t['nombre']} - Base Tributable")
            self.assertEqual(res.descuentos.impuesto_unico_monto, e["imp"], f"{t['nombre']} - Impuesto Único")
            self.assertEqual(res.descuentos.total_descuentos, e["desc_leg"], f"{t['nombre']} - Total Descuentos Legales")
            self.assertEqual(res.anticipo, e["anticipo"], f"{t['nombre']} - Anticipo")
            self.assertEqual(res.prestamo, e["prestamo"], f"{t['nombre']} - Préstamo")
            self.assertEqual(res.sueldo_liquido, e["liq"], f"{t['nombre']} - Alcance Líquido")

            print(f"✅ {t['nombre']}: Todos los 19 conceptos validados al peso ($0 diferencia). Líquido: ${res.sueldo_liquido:,.0f}")


if __name__ == "__main__":
    unittest.main()
