# ipprovider

Herramienta de línea de comandos en Python 3 que lee un PDF con texto seleccionable, detecta direcciones **IPv4** e **IPv6** válidas y genera un **informe en PDF** con datos de registro (**RDAP**) para las direcciones **públicas** (ASN, organización/red, CIDR cuando existan).

## Requisitos

- Python 3.10 o superior (probado en 3.12).
- PDF con capa de texto. Los PDF escaneados como imagen **no** exponen texto salvo que se use OCR (fuera de alcance).

## Instalación

```bash
pip install -e ".[dev]"
```

O solo dependencias de ejecución:

```bash
pip install -e .
```

## Uso

```bash
ipprovider ruta/al/archivo.pdf
```

El informe se escribe por defecto como `informe_ips.pdf` en el directorio actual.

Salida explícita:

```bash
ipprovider entrada.pdf -o informe_salida.pdf
```

También:

```bash
python -m ipprovider entrada.pdf -o salida.pdf
```

## Comportamiento

- Las IPs se listan **sin duplicados**, en orden de **primera aparición** en el texto extraído.
- **Privadas**, loopback, enlace local, etc.: se incluyen en la tabla con alcance descriptivo; no se consulta RDAP.
- **Públicas**: se consulta RDAP vía la librería `ipwhois`. Hace falta **conectividad** a Internet; si la consulta falla, la fila puede quedar con campos RDAP vacíos (—).

## Pruebas

```bash
pytest
```

## Estructura del proyecto

- `src/ipprovider/`: paquete principal (`pdf_extract`, `ip_find`, `enrichment`, `report_pdf`, `cli`).
- `tests/`: pruebas con `pytest` (PDFs generados en pruebas, RDAP mockeado).
