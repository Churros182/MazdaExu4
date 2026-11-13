# -*- coding: utf-8 -*-
"""Lector de archivos VBF (Mazda/Ford) para la app Mazda Calibration Files Android."""
import hashlib
import os
import re
import zlib

MODULOS = {0x7E0: "PCM / ECM (motor)", 0x7E1: "TCM (transmisión)"}
TIPOS = {
    "SBL": "SBL (cargador secundario)",
    "EXE": "EXE (ejecutable)",
    "DATA": "DATA (datos / calibración)",
}
CONOCIDOS = (
    "sw_part_number", "sw_part_type", "ecu_address", "network",
    "frame_format", "data_format_identifier", "file_checksum", "erase",
)


def _modulo(valor):
    limpio = valor.strip().lower()
    if limpio.startswith("0x"):
        limpio = limpio[2:]
    try:
        direccion = int(limpio, 16)
    except ValueError:
        return valor
    return "0x%X → %s" % (direccion, MODULOS.get(direccion, "módulo no identificado"))


def _cierre_encabezado(texto, abre):
    profundidad = 0
    en_texto = False
    for i in range(abre, len(texto)):
        c = texto[i]
        if c == '"':
            en_texto = not en_texto
        if en_texto:
            continue
        if c == "{":
            profundidad += 1
        elif c == "}":
            profundidad -= 1
            if profundidad == 0:
                return i
    return -1


def _bloques(datos, pos):
    """Recorre bloques [dirección 4B][largo 4B][datos][CRC 2B]; None si no cuadran."""
    bloques = []
    total = len(datos)
    while pos < total:
        if pos + 8 > total:
            return None
        inicio = int.from_bytes(datos[pos:pos + 4], "big")
        largo = int.from_bytes(datos[pos + 4:pos + 8], "big")
        fin = pos + 8 + largo + 2
        if largo == 0 or fin > total:
            return None
        bloques.append((inicio, largo))
        pos = fin
    return bloques or None


def leer_vbf(ruta):
    lineas = []
    with open(ruta, "rb") as f:
        datos = f.read()
    lineas.append("📄 %s (%d bytes)" % (os.path.basename(ruta), len(datos)))

    if datos[:2] == b"PK":
        lineas.append("❌ Este archivo es un ZIP, no un .vbf.")
        return lineas
    if datos.lstrip()[:1] == b"<":
        lineas.append("❌ El archivo parece una página web (HTML), no un VBF.")
        return lineas

    texto = datos[:65536].decode("latin-1")
    inicio = re.search(r"header\s*\{", texto, re.IGNORECASE)
    if inicio is None:
        vista = re.sub(r"[^\x20-\x7E]", ".", texto[:60])
        lineas.append("❌ No se encontró el encabezado VBF (archivo incompleto o dañado).")
        lineas.append("   Inicio del archivo: %s" % vista)
        return lineas

    abre = inicio.end() - 1
    cierra = _cierre_encabezado(texto, abre)
    if cierra < 0:
        lineas.append("❌ Encabezado VBF incompleto.")
        return lineas

    version = re.search(r"vbf_version\s*=\s*([^;]+);", texto)
    if version:
        lineas.append("   Versión VBF: %s" % version.group(1).strip())

    bloque = texto[abre + 1:cierra]
    campos = {}
    for m in re.finditer(r"(\w+)\s*=\s*([^;]*);", bloque, re.DOTALL):
        campos[m.group(1)] = m.group(2).strip()

    if "sw_part_number" in campos:
        lineas.append("   Número de parte SW: %s" % campos["sw_part_number"].replace('"', ""))
    if "sw_part_type" in campos:
        tipo = campos["sw_part_type"]
        lineas.append("   Tipo de software: %s" % TIPOS.get(tipo.strip().upper(), tipo.strip()))
    if "ecu_address" in campos:
        lineas.append("   Módulo (dirección ECU): %s" % _modulo(campos["ecu_address"]))
    if "network" in campos:
        lineas.append("   Red: %s" % campos["network"])
    if "frame_format" in campos:
        lineas.append("   Formato de trama: %s" % campos["frame_format"])
    if "data_format_identifier" in campos:
        lineas.append("   Formato de datos: %s" % campos["data_format_identifier"])
    if "file_checksum" in campos:
        lineas.append("   Checksum del archivo: %s" % campos["file_checksum"])

    if "erase" in campos:
        pares = re.findall(
            r"\{\s*(0x[0-9A-Fa-f]+)\s*,\s*(0x[0-9A-Fa-f]+)\s*\}", campos["erase"])
        if pares:
            total = sum(int(largo, 16) for _, largo in pares)
            lineas.append("   Regiones de borrado: %d (%d KB)" % (len(pares), total // 1024))

    pos = cierra + 1
    for salto in range(0, 3):
        bloques = _bloques(datos, pos + salto)
        if bloques:
            peso = sum(largo for _, largo in bloques)
            menor = min(inicio for inicio, _ in bloques)
            mayor = max(inicio + largo - 1 for inicio, largo in bloques)
            lineas.append("   Bloques de datos: %d (%d KB)" % (len(bloques), peso // 1024))
            lineas.append("   Rango de memoria: 0x%X – 0x%X" % (menor, mayor))
            break

    lineas.append("   CRC32 del archivo: 0x%08X" % (zlib.crc32(datos) & 0xFFFFFFFF))
    lineas.append("   SHA-256: %s…" % hashlib.sha256(datos).hexdigest()[:16])

    for clave, valor in campos.items():
        if clave not in CONOCIDOS:
            corto = re.sub(r"\s+", " ", valor).replace('"', "")
            lineas.append("   %s: %s" % (clave, corto[:80] + ("…" if len(corto) > 80 else "")))
    return lineas
