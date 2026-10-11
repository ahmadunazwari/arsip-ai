
import os
import shutil

import fitz
import pytesseract
from PIL import Image, ImageOps, ImageEnhance, ImageFilter


TESSERACT_PATH = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def configure_tesseract():
    """Mencari dan mengonfigurasi executable Tesseract."""

    candidates = [
        shutil.which("tesseract"),
        TESSERACT_PATH,
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]

    for path in candidates:
        if path and os.path.isfile(path):
            pytesseract.pytesseract.tesseract_cmd = path

            # Pastikan executable dapat dijalankan.
            version = pytesseract.get_tesseract_version()
            return path

    raise RuntimeError(
        "Tesseract OCR tidak ditemukan. "
        "Periksa lokasi instalasi tesseract.exe."
    )


def prepare_image(image):
    """Meningkatkan keterbacaan gambar dokumen."""

    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)
    image = ImageEnhance.Contrast(image).enhance(1.5)
    image = image.filter(ImageFilter.SHARPEN)

    return image


def get_ocr_language():
    """Memilih bahasa OCR yang tersedia."""

    available = pytesseract.get_languages(config="")

    if "ind" in available and "eng" in available:
        return "ind+eng"

    if "ind" in available:
        return "ind"

    if "eng" in available:
        return "eng"

    raise RuntimeError(
        "Data bahasa OCR tidak ditemukan. "
        "Pasang data bahasa eng atau ind."
    )


def ocr_pdf(pdf_path):
    """Mengekstrak teks PDF hasil pindai menggunakan OCR."""

    configure_tesseract()

    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(
            f"File PDF tidak ditemukan: {pdf_path}"
        )

    try:
        language = get_ocr_language()
        extracted_pages = []

        with fitz.open(pdf_path) as pdf:
            if len(pdf) == 0:
                raise ValueError("PDF tidak memiliki halaman.")

            for page_number, page in enumerate(pdf, start=1):
                # Render pada resolusi 300 DPI.
                pix = page.get_pixmap(
                    matrix=fitz.Matrix(300 / 72, 300 / 72),
                    colorspace=fitz.csGRAY,
                    alpha=False,
                )

                image = Image.frombytes(
                    "L",
                    (pix.width, pix.height),
                    pix.samples,
                )

                image = prepare_image(image)

                text = pytesseract.image_to_string(
                    image,
                    lang=language,
                    config="--oem 3 --psm 3",
                )

                # Alternatif tata letak jika hasil terlalu sedikit.
                if len(text.strip()) < 40:
                    alternative = pytesseract.image_to_string(
                        image,
                        lang=language,
                        config="--oem 3 --psm 6",
                    )

                    if len(alternative.strip()) > len(text.strip()):
                        text = alternative

                extracted_pages.append(
                    f"--- Halaman {page_number} ---\n"
                    f"{text.strip()}"
                )

        result = "\n\n".join(extracted_pages).strip()

        if not result:
            raise RuntimeError(
                "OCR tidak menghasilkan teks. "
                "Periksa kualitas hasil pindai PDF."
            )

        return result

    except Exception as e:
        raise RuntimeError(
            f"OCR gagal memproses PDF: {e}"
        ) from e
