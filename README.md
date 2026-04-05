# ipprovider

Python 3 CLI that reads **PDF**, **Excel (.xlsx)**, or **Word (.docx)** with extractable text, finds valid **IPv4** and **IPv6** addresses, and writes an **HTML report** with **RDAP** registry-style data for **public** addresses (ASN, organization/network, CIDR, contact fields when available).

## Requirements

- Python 3.10+ (tested on 3.12).
- **PDF**: needs a real text layer. Scanned image-only PDFs yield no text unless you add OCR (out of scope).
- **Excel**: `.xlsx` only. Legacy **`.xls`** is not supported (convert to `.xlsx` or export to CSV).
- **Word**: **`.docx`** only. Legacy binary **`.doc`** is not supported.

## Install

Install runtime dependencies (**includes** `python-docx`, `openpyxl`, `pypdf`, `ipwhois`):

```bash
pip install -e .
```

For running the full test suite (adds `pytest` and `reportlab` for PDF test fixtures):

```bash
pip install -e ".[dev]"
```

If you run `pytest` without installing the project first, imports such as `docx` will fail; use `pip install -e .` in the same environment.

## Usage

```bash
ipprovider path/to/file.pdf
ipprovider path/to/workbook.xlsx
ipprovider path/to/document.docx
```

Default output: `informe_ips.html` in the current working directory.

While running, the tool prints to the console:

- **`.xlsx`**: progress while reading each sheet and every 5,000 rows (to stderr).
- **RDAP** (public IPs): start message and periodic lines when there are many lookups (to stderr).
- **After processing**: the **list of IPs found** and a **per-IP summary** (stdout).

Use `-q` / `--quiet` to hide all of the above.

Explicit output path:

```bash
ipprovider input.pdf -o report.html
python -m ipprovider data.xlsx -o out.html
```

Para inspeccionar el **JSON RDAP crudo** de una IP pública (misma consulta que el informe), p. ej. al depurar el parseo:

```bash
ipprovider-rdap-json 186.143.162.187
ipprovider-rdap-json 8.8.8.8 -o rdap.json
```

## Behaviour

- IPs are **deduplicated**, ordered by **first occurrence** in the merged extracted text.
- **Private**, loopback, link-local, etc.: included in the table with a scope label; **no RDAP** lookup.
- **Public**: RDAP via `ipwhois` (Internet required). On failure, RDAP fields may show as —.

## Tests

```bash
pytest
```

## Project layout

- `src/ipprovider/`: `document_extract`, `pdf_extract`, `ip_find`, `enrichment`, `report_html`, `rdap_dump`, `cli`.
- `tests/`: `pytest` (synthetic PDF/Excel/Word, mocked RDAP).
