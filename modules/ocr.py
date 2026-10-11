
import os
import shutil

import fitz
import pytesseract
from PIL import Image, ImageOps, ImageEnhance, ImageFilter


# Lokasi Tesseract Windows dapat diatur melalui environment variable.
# Pada Streamlit Cloud, lokasi akan ditemukan secara otomatis.
TESSERACT_PATH = os.environ.get("TESSERACT_CMD", "")


def configure_tesseract():
    """Mencari dan mengonfigurasi executable Tesseract."""

    candidates = [
        shutil.which("tesseract"),
        TESSERACT_PATH,
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]

    for path in candidates:
        if not path:
            continue

        # Jika hanya nama executable, cari melalui PATH.
        resolved = shutil.which(path) if not os.path.isabs(path) else path

        if not resolved or not os.path.isfile(resolved):
            continue

        try:
            pytesseract.pytesseract.tesseract_cmd = resolved

            # Pastikan executable benar-benar dapat dijalankan.
            pytesseract.get_tesseract_version()

            return resolved

        except Exception:
            continue

    raise RuntimeError(
        "Tesseract OCR tidak ditemukan atau tidak dapat dijalankan. "
        "Pada Streamlit Cloud, pastikan packages.txt berisi "
        "'tesseract-ocr' dan aplikasi sudah selesai melakukan deployment."
    )


def prepare_image(image):
    """Meningkatkan keterbacaan gambar dokumen hasil pindai."""

    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)
    image = ImageEnhance.Contrast(image).enhance(1.5)
    image = image.filter(ImageFilter.SHARPEN)

    return image


def get_ocr_language():
    """Memilih bahasa OCR berdasarkan data yang tersedia."""

    try:
        available = pytesseract.get_languages(config="")
    except Exception as e:
        raise RuntimeError(
            "Gagal membaca data bahasa Tesseract. "
            "Periksa instalasi Tesseract dan folder tessdata."
        ) from e

    if "ind" in available and "eng" in available:
        return "ind+eng"

    if "ind" in available:
        return "ind"

    if "eng" in available:
        return "eng"

    raise RuntimeError(
        "Data bahasa OCR tidak ditemukan. "
        "Pastikan paket tesseract-ocr-eng atau "
        "tesseract-ocr-ind telah terpasang."
    )


def ocr_pdf(pdf_path):
    """Mengekstrak teks dari setiap halaman PDF hasil pindai."""

    configure_tesseract()

    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(
            f"File PDF tidak ditemukan: {pdf_path}"
        )

    extracted_pages = []

    try:
        language = get_ocr_language()

        with fitz.open(pdf_path) as pdf:
            if len(pdf) == 0:
                raise ValueError("PDF tidak memiliki halaman.")

            for page_number, page in enumerate(pdf, start=1):
                # Render halaman dengan resolusi 300 DPI.
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

                # Coba tata letak alternatif jika teks terlalu sedikit.
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

