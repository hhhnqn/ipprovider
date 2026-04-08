"""OCR de imágenes (Tesseract) para texto incrustado en documentos."""

from __future__ import annotations

import io
import os
import zipfile
from pathlib import Path
from typing import Iterator

# Extensiones típicas en OOXML (xl/media, word/media).
_IMAGE_SUFFIXES = (
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
)

DEFAULT_OCR_LANG = "spa+eng"


def _missing_ocr_packages_message() -> str:
    return (
        "El modo OCR requiere dependencias extra. Instálelas con:\n"
        '  pip install -e ".[ocr]"'
    )


def _missing_tesseract_message(cause: str | None = None) -> str:
    hint = ""
    if cause:
        hint = f"\nDetalle: {cause}\n"
    return (
        "No se pudo ejecutar el binario de Tesseract OCR.\n\n"
        "En Ubuntu / Debian, instale por ejemplo:\n"
        "  sudo apt install tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng "
        "poppler-utils\n"
        "(poppler-utils convierte cada página del PDF a imagen; sin Tesseract "
        "no hay OCR.)\n\n"
        "Si Tesseract está instalado pero no en el PATH, indique la ruta:\n"
        "  export IPPROVIDER_TESSERACT=/usr/bin/tesseract\n"
        "  (alternativa: TESSERACT_CMD con el mismo valor)"
        f"{hint}"
    )


def _configure_tesseract_from_env() -> None:
    import pytesseract

    for key in ("IPPROVIDER_TESSERACT", "TESSERACT_CMD"):
        cmd = os.environ.get(key, "").strip()
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd
            return


def _missing_pdf2image_message() -> str:
    return (
        "Para OCR en PDF hace falta el paquete pdf2image (incluido en pip install -e \".[ocr]\") "
        "y las utilidades Poppler (p. ej. poppler-utils en Debian/Ubuntu)."
    )


def ensure_ocr_core() -> None:
    """Pillow + pytesseract + binario Tesseract."""
    try:
        import pytesseract
        from PIL import Image  # noqa: F401
    except ImportError as e:
        raise ValueError(_missing_ocr_packages_message()) from e
    _configure_tesseract_from_env()
    try:
        pytesseract.get_tesseract_version()
    except Exception as e:
        raise ValueError(_missing_tesseract_message(str(e).strip() or type(e).__name__)) from e


def ensure_pdf_ocr_deps() -> None:
    """Incluye pdf2image (Poppler se comprueba al convertir)."""
    ensure_ocr_core()
    try:
        import pdf2image  # noqa: F401  # type: ignore[import-untyped]
    except ImportError as e:
        raise ValueError(_missing_pdf2image_message()) from e


def ocr_pil_image(image: object, lang: str) -> str:
    import pytesseract

    raw = pytesseract.image_to_string(image, lang=lang)
    return (raw or "").strip()


def ocr_image_bytes(data: bytes, lang: str) -> str:
    from PIL import Image

    img = Image.open(io.BytesIO(data))
    return ocr_pil_image(img, lang)


def iter_ooxml_embedded_images(path: Path, media_prefix: str) -> Iterator[bytes]:
    """
    Lee bytes de imágenes bajo p. ej. xl/media/ o word/media/ dentro del ZIP OOXML.
    """
    with zipfile.ZipFile(path, "r") as zf:
        names = sorted(zf.namelist())
        for name in names:
            if not name.startswith(media_prefix):
                continue
            lower = name.lower()
            if any(lower.endswith(ext) for ext in _IMAGE_SUFFIXES):
                yield zf.read(name)


def ocr_pdf_pages(path: Path, *, lang: str, dpi: int = 200, progress: bool = False) -> str:
    """Rasteriza cada página del PDF y aplica OCR; devuelve texto concatenado."""
    ensure_pdf_ocr_deps()
    from pdf2image import convert_from_path  # type: ignore[import-untyped]

    try:
        images = convert_from_path(str(path), dpi=dpi)
    except Exception as e:
        msg = str(e).lower()
        if "poppler" in msg or "pdftoppm" in msg or "page count" in msg:
            raise ValueError(
                "Fallo al rasterizar el PDF (¿falta Poppler?). "
                "En Linux: sudo apt install poppler-utils"
            ) from e
        raise

    parts: list[str] = []
    n = len(images)
    for i, img in enumerate(images, start=1):
        if progress:
            import sys

            print(f"  OCR PDF página {i}/{n} ...", file=sys.stderr, flush=True)
        t = ocr_pil_image(img, lang)
        if t:
            parts.append(t)
    return "\n\n".join(parts)


def ocr_ooxml_embedded_images(
    path: Path,
    *,
    media_prefix: str,
    label: str,
    lang: str,
    progress: bool = False,
) -> str:
    ensure_ocr_core()
    parts: list[str] = []
    for i, blob in enumerate(iter_ooxml_embedded_images(path, media_prefix), start=1):
        if progress:
            import sys

            print(f"  OCR {label} imagen {i} ...", file=sys.stderr, flush=True)
        t = ocr_image_bytes(blob, lang)
        if t:
            parts.append(t)
    return "\n\n".join(parts)
