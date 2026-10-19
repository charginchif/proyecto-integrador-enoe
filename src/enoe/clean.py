"""Limpieza (Preprocesamiento del ciclo KDD).

Cada regla es una función pequeña, con nombre propio y registrada en una bitácora
(``Bitacora``) que produce la tabla de "embudo" de registros (cuántos entran, cuántos salen y por qué).
Las reglas que NO eliminan filas (faltantes codificados, atípicos, calidad del ingreso) crean
banderas: así el análisis puede elegir y hacerse un análisis de sensibilidad sin volver a limpiar.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import config as C


# --------------------------------------------------------------------------- #
# Bitácora
# --------------------------------------------------------------------------- #
@dataclass
class Paso:
    id: str
    tipo: str            # "filtro" (elimina filas) | "marca" (solo crea una bandera)
    descripcion: str
    regla: str
    n_antes: int
    n_despues: int       # filas que quedan (filtro) o filas que cumplen la regla (marca)

    @property
    def afectados(self) -> int:
        return self.n_antes - self.n_despues if self.tipo == "filtro" else self.n_despues


class Bitacora:
    def __init__(self) -> None:
        self.pasos: list[Paso] = []

    def filtro(self, id: str, descripcion: str, regla: str, n_antes: int, n_despues: int) -> None:
        self.pasos.append(Paso(id, "filtro", descripcion, regla, int(n_antes), int(n_despues)))

    def marca(self, id: str, descripcion: str, regla: str, n_total: int, n_marcados: int) -> None:
        self.pasos.append(Paso(id, "marca", descripcion, regla, int(n_total), int(n_marcados)))

    def a_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            [dict(id=p.id, tipo=p.tipo, descripcion=p.descripcion, regla=p.regla,
                  n_antes=p.n_antes, n_despues=p.n_despues, afectados=p.afectados) for p in self.pasos]
        )


# --------------------------------------------------------------------------- #
# 1. Cobertura: ¿qué registros pertenecen al universo de estudio?
# --------------------------------------------------------------------------- #
def aplicar_cobertura(df: pd.DataFrame, bit: Bitacora) -> pd.DataFrame:
    """Universo: personas OCUPADAS de 15 años y más, con entrevista completa y residentes habituales.

    Es exactamente la base con la que INEGI publica sus indicadores; por eso las estimaciones
    ponderadas pueden contrastarse con las cifras oficiales (ver pipeline.validacion_externa).
    """
    n = len(df)
    bit.filtro("L0", "Registros crudos de la tabla SDEMT", "todas las personas del hogar, todas las edades", n, n)

    d = df[df["r_def"] == 0]
    bit.filtro("L1", "Entrevista completa", "r_def == 0 (resultado definitivo de la entrevista)", n, len(d))
    n = len(d)

    d = d[d["c_res"].isin([1, 3])]
    bit.filtro("L2", "Residente habitual", "c_res in {1, 3}; se excluye c_res = 2 (nuevo residente, sin datos de sexo/edad)", n, len(d))
    n = len(d)

    d = d[d["eda"].notna() & (d["eda"] >= C.EDAD_MIN) & (d["eda"] <= 98)]
    bit.filtro("L3", "Población de 15 años y más con edad válida", "15 <= eda <= 98 (99 = no especificado)", n, len(d))
    n = len(d)

    d = d[d["clase2"] == 1]
    bit.filtro("L4", "Población ocupada", "clase2 == 1", n, len(d))
    n = len(d)

    d = d[d["fac_tri"] > 0]
    bit.filtro("L5", "Ponderador positivo", "fac_tri > 0", n, len(d))

    return d.reset_index(drop=True)


def marcar_ventana(df: pd.DataFrame, bit: Bitacora) -> pd.DataFrame:
    d = df.copy()
    d["en_ventana_15_65"] = d["eda"] <= C.EDAD_MAX_ANALISIS
    bit.marca("L6", f"Ventana de análisis {C.EDAD_MIN}-{C.EDAD_MAX_ANALISIS} años (bandera)",
              f"eda <= {C.EDAD_MAX_ANALISIS}", len(d), int(d["en_ventana_15_65"].sum()))
    return d


# --------------------------------------------------------------------------- #
# 2. Faltantes codificados y valores imposibles
# --------------------------------------------------------------------------- #
def recodificar_faltantes(df: pd.DataFrame, bit: Bitacora) -> pd.DataFrame:
    """La ENOE no deja celdas vacías: los faltantes vienen como códigos válidos (99, 0, ...).

    * anios_esc == 99 -> NaN  (no especificado)
    * hrsocup == 0     -> NaN  (ocupado ausente de su trabajo la semana pasada: sin horas, no hay ingreso/hora)
    * hrsocup > 112    -> NaN  (más de 16 h diarias los 7 días: jornada materialmente imposible)
    """
    d = df.copy()
    n = len(d)

    d["anios_esc_valido"] = d["anios_esc"].ne(C.ANIOS_ESC_NO_ESPECIFICADO)
    bit.marca("M1", "Años de escolaridad no especificados", "anios_esc == 99 -> NaN", n, int((~d["anios_esc_valido"]).sum()))
    d["anios_esc"] = d["anios_esc"].where(d["anios_esc_valido"])

    d["hrsocup_raw"] = d["hrsocup"]
    cero = int((d["hrsocup"] == 0).sum())
    imposibles = int((d["hrsocup"] > C.HORAS_MAX).sum())
    bit.marca("M2", "Ocupados con 0 horas trabajadas la semana de referencia", "hrsocup == 0 -> NaN", n, cero)
    bit.marca("M3", f"Jornadas imposibles (> {C.HORAS_MAX} h/semana)", f"hrsocup > {C.HORAS_MAX} -> NaN", n, imposibles)
    d["horas_validas"] = d["hrsocup"].between(1, C.HORAS_MAX)
    d["hrsocup"] = d["hrsocup"].where(d["horas_validas"])

    d["nivel_especificado"] = d["niv_ins"].between(1, 4)
    bit.marca("M4", "Nivel de instrucción no especificado", "niv_ins == 5", n, int((~d["nivel_especificado"]).sum()))
    return d


# --------------------------------------------------------------------------- #
# 3. Calidad del ingreso: el ingreso 0 no es un solo fenómeno
# --------------------------------------------------------------------------- #
def clasificar_ingreso(df: pd.DataFrame, bit: Bitacora) -> pd.DataFrame:
    """Separa los cuatro tipos de reporte del ingreso laboral (hallazgo central de calidad de datos).

    A  monto exacto declarado      ingocup > 0
    B  solo rango de salarios mín. ingocup == 0 y ing7c in 1..5  (el público no trae el monto)
    C  no recibe ingresos          ing7c == 6   (p. ej. trabajadores sin pago)
    D  no especificó               ing7c == 7   (no sabe / no responde)
    """
    d = df.copy()
    condiciones = [d["ingocup"] > 0, d["ing7c"].between(1, 5), d["ing7c"] == 6, d["ing7c"] == 7]
    d["grupo_ingreso"] = np.select(condiciones, ["A", "B", "C", "D"], default="?")
    if (d["grupo_ingreso"] == "?").any():
        raise ValueError("Hay ocupados sin clasificación de ingreso")
    for g, desc in C.GRUPO_INGRESO.items():
        bit.marca(f"Q{g}", f"Ingreso grupo {g}: {desc}", "clasificación mutuamente excluyente", len(d), int((d["grupo_ingreso"] == g).sum()))
    return d


# --------------------------------------------------------------------------- #
# 4. Atípicos del ingreso por hora
# --------------------------------------------------------------------------- #
def marcar_atipicos(df: pd.DataFrame, bit: Bitacora) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Marca como atípicos los ingresos por hora fuera de [P0.5, P99.5] DENTRO de cada entidad.

    Los umbrales se estiman con el grupo A, horas válidas y ventana 15-65 (la muestra de análisis)
    usando percentiles sin ponderar (la limpieza es un criterio de registro, no de población).
    Se recortan las dos colas: la inferior (p. ej. $0.5 por hora) casi siempre es error de captura.
    """
    d = df.copy()
    base = d["grupo_ingreso"].eq("A") & d["horas_validas"] & d["en_ventana_15_65"]
    lo, hi = C.RECORTE_PCT
    umbrales = (
        d.loc[base].groupby("cve_ent")["ln_ing_hora"]
        .quantile([lo / 100, hi / 100]).unstack()
        .rename(columns={lo / 100: "ln_min", hi / 100: "ln_max"})
    )
    d = d.merge(umbrales, left_on="cve_ent", right_index=True, how="left")
    d["outlier_ing_hora"] = (d["ln_ing_hora"] < d["ln_min"]) | (d["ln_ing_hora"] > d["ln_max"])
    d["outlier_ing_hora"] = d["outlier_ing_hora"].fillna(False) & d["grupo_ingreso"].eq("A")
    bit.marca("O1", f"Ingreso por hora atípico (fuera de P{lo}-P{hi} por entidad)",
              "ln(ing_hora) < P0.5 o > P99.5 de su entidad", int(base.sum()), int((d["outlier_ing_hora"] & base).sum()))
    tabla_umbrales = umbrales.assign(
        hora_min=np.exp(umbrales["ln_min"]), hora_max=np.exp(umbrales["ln_max"])
    ).reset_index()
    return d.drop(columns=["ln_min", "ln_max"]), tabla_umbrales


def definir_muestras(df: pd.DataFrame) -> pd.DataFrame:
    """Construye las banderas de las dos muestras analíticas y devuelve el DataFrame.

    muestra_salarial     grupo A + horas válidas + escolaridad y nivel especificados + 15-65 + sin atípicos
    muestra_salarial_ext grupo A o B (con ingreso imputado por rango) bajo las mismas condiciones
    """
    d = df.copy()
    comunes = d["horas_validas"] & d["anios_esc_valido"] & d["nivel_especificado"] & d["en_ventana_15_65"]
    d["en_muestra_salarial"] = comunes & d["grupo_ingreso"].eq("A") & ~d["outlier_ing_hora"]
    d["en_muestra_salarial_ext"] = comunes & d["grupo_ingreso"].isin(["A", "B"]) & ~d["outlier_ing_hora"]
    return d


def embudo_muestra_salarial(df: pd.DataFrame) -> pd.DataFrame:
    """Embudo secuencial hasta la muestra salarial (para el informe de calidad)."""
    pasos = []
    m = df["en_ventana_15_65"]
    pasos.append(("W0", "Ocupados de 15 a 65 años", int(m.sum())))
    m = m & df["grupo_ingreso"].eq("A")
    pasos.append(("W1", "con monto exacto de ingreso (grupo A)", int(m.sum())))
    m = m & df["horas_validas"]
    pasos.append(("W2", "con horas trabajadas válidas (1-112)", int(m.sum())))
    m = m & df["anios_esc_valido"] & df["nivel_especificado"]
    pasos.append(("W3", "con escolaridad y nivel especificados", int(m.sum())))
    m = m & ~df["outlier_ing_hora"]
    pasos.append(("W4", "sin ingreso por hora atípico (P0.5-P99.5 por entidad)", int(m.sum())))
    assert int(m.sum()) == int(df["en_muestra_salarial"].sum())
    t = pd.DataFrame(pasos, columns=["id", "descripcion", "n"])
    t["excluidos"] = -t["n"].diff().fillna(0).astype(int)
    return t


# --------------------------------------------------------------------------- #
# 5. Expectativas de calidad (contratos que debe cumplir la tabla final)
# --------------------------------------------------------------------------- #
def verificar_expectativas(d: pd.DataFrame) -> pd.DataFrame:
    """Lista de comprobaciones "tipo Great Expectations"; el pipeline falla si alguna crítica no se cumple."""
    r = []

    def anota(nombre: str, ok: bool, detalle: str, critica: bool = True) -> None:
        r.append(dict(expectativa=nombre, cumple=bool(ok), critica=critica, detalle=detalle))

    anota("persona_id único", d["persona_id"].is_unique, f"{d['persona_id'].nunique():,} ids distintos / {len(d):,} filas")
    anota("32 entidades presentes", d["cve_ent"].nunique() == 32, f"{d['cve_ent'].nunique()} entidades")
    anota("sexo en {1,2}", d["sex"].isin([1, 2]).all(), str(sorted(d["sex"].unique())))
    anota("edad entre 15 y 98", d["eda"].between(15, 98).all(), f"min={d['eda'].min()}, max={d['eda'].max()}")
    anota("ponderador positivo", (d["fac_tri"] > 0).all(), f"min={d['fac_tri'].min()}")
    anota("todos son ocupados", (d["clase2"] == 1).all(), "clase2 == 1")
    anota("grupo de ingreso exhaustivo", d["grupo_ingreso"].isin(list("ABCD")).all(), d["grupo_ingreso"].value_counts().to_dict().__repr__())

    a = d[d["grupo_ingreso"] == "A"]
    r_sm = a["ingocup"] / a["salario"]
    cotas = {1: (0, 1), 2: (1, 2), 3: (2, 3), 4: (3, 5), 5: (5, np.inf)}
    dentro = np.zeros(len(a), dtype=bool)
    for k, (lo, hi) in cotas.items():
        sel = a["ing7c"].to_numpy() == k
        dentro[sel] = ((r_sm[sel] > lo) & (r_sm[sel] <= hi)).to_numpy()
    anota("ing7c consistente con ingocup/salario mínimo", dentro.mean() > 0.999, f"{dentro.mean():.4%} de los registros del grupo A")

    h = a[a["horas_validas"]]
    rel = ((h["ingocup"] / (h["hrsocup"] * C.SEMANAS_POR_MES)) / h["ing_x_hrs"] - 1).abs().max()
    anota("ing_x_hrs = ingocup / (hrsocup x 4.3)", rel < 1e-3, f"máxima diferencia relativa {rel:.2e}")

    cero = d[(d["niv_ins"] == 1) & d["anios_esc"].notna()]
    anota("niv_ins=1 implica <= 5 años de escolaridad", (cero["anios_esc"] <= 5).all(), f"{len(cero):,} registros")
    sup = d[(d["niv_ins"] == 4) & d["anios_esc"].notna()]
    anota("niv_ins=4 implica >= 12 años de escolaridad", (sup["anios_esc"] >= 12).all(), f"{len(sup):,} registros")

    anota("horas entre 0 y 168 (crudas)", d["hrsocup_raw"].between(0, 168).all(), f"max={d['hrsocup_raw'].max()}")
    anota("ingocup entre 0 y 1,000,000", d["ingocup"].between(0, 1_000_000).all(), f"max={d['ingocup'].max():,}")

    b = d[(d["grupo_ingreso"] == "B")]
    mapa = {1: 1, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 5}
    ok_b = b["p6c"].map(mapa).eq(b["ing7c"])
    anota("p6c (COE2T) reproduce ing7c (SDEMT) en el grupo B", ok_b.mean() > 0.999, f"{ok_b.mean():.4%} de {len(b):,} registros")

    p = a["p6b2"]
    anota("ingocup == p6b2 (COE2T) en el grupo A", float((a["ingocup"] == p).mean()) > 0.999, f"{float((a['ingocup'] == p).mean()):.4%} de {len(a):,} registros", critica=False)
    return pd.DataFrame(r)
