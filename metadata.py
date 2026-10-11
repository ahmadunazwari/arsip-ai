
import re
from datetime import datetime

MONTHS = {
    "januari": "01", "februari": "02", "maret": "03",
    "april": "04", "mei": "05", "juni": "06",
    "juli": "07", "agustus": "08", "september": "09",
    "oktober": "10", "november": "11", "desember": "12"
}

MONTH_PATTERN = "|".join(MONTHS.keys())


def clean_line(value):
    """Membersihkan spasi dan tanda baca di awal/akhir baris."""
    return re.sub(r"\s+", " ", value or "").strip(" \t:;,-")


def normalize_date(value):
    """Mengubah tanggal ke format DD-MM-YYYY jika dikenali."""
    value = clean_line(value)

    m = re.search(
        rf"\b(\d{{1,2}})\s+({MONTH_PATTERN})\s+(\d{{4}})\b",
        value,
        re.IGNORECASE
    )
    if m:
        day = int(m.group(1))
        month = MONTHS[m.group(2).lower()]
        return f"{day:02d}-{month}-{m.group(3)}"

    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", value)
    if m:
        day, month, year = map(int, m.groups())
        if 1 <= day <= 31 and 1 <= month <= 12:
            return f"{day:02d}-{month:02d}-{year}"

    return ""


def find_labeled_value(lines, labels):
    """
    Mencari nilai setelah label, baik pada baris yang sama
    maupun pada baris berikutnya.
    """
    for i, line in enumerate(lines):
        for label in labels:
            # Label harus berada di awal baris agar tidak mengambil
            # kata yang kebetulan muncul di tengah kalimat.
            pattern = (
                r"^\s*" + label +
                r"\s*(?:[:.]|[-])?\s*(.*?)\s*$"
            )
            m = re.match(pattern, line, re.IGNORECASE)

            if not m:
                continue

            value = clean_line(m.group(1))

            if value:
                return value

            # Nilai mungkin berada pada baris berikutnya.
            if i + 1 < len(lines):
                next_line = clean_line(lines[i + 1])

                if next_line and not re.match(
                    r"^(nomor|no\.?|tanggal|tgl\.?|perihal|hal|"
                    r"lampiran|sifat|kepada)\b",
                    next_line,
                    re.IGNORECASE
                ):
                    return next_line

    return ""


def extract_number(lines):
    """Mengambil nomor dokumen tanpa menerima potongan label."""
    value = find_labeled_value(
        lines,
        [
            r"nom[o0]r(?:\s+surat)?",
            r"n[o0]\s*(?:\.|omor)?"
        ]
    )

    if not value:
        # Alternatif jika label Nomor gagal terbaca oleh OCR.
        for line in lines:
            m = re.search(
                r"\b\d{1,5}(?:\.\d+)*(?:/[A-Z0-9._-]+){1,6}\b",
                line,
                re.IGNORECASE
            )
            if m:
                value = m.group(0)
                break

    # Pastikan hasil bukan label atau fragmen pendek.
    value = clean_line(value)
    if not value or re.fullmatch(
        r"(nomor|no|mor|n[o0]m[o0]r)",
        value,
        re.IGNORECASE
    ):
        return ""

    # Nomor surat biasanya mengandung angka dan pemisah/karakter.
    if not re.search(r"\d", value):
        return ""

    return value[:120]


def extract_metadata(text, filename=""):
    # OCR dapat menghasilkan baris kosong dan spasi tidak beraturan.
    text = (text or "").replace("\x00", " ")
    lines = [
        clean_line(line)
        for line in text.splitlines()
        if clean_line(line)
    ]

    alltext = "\n".join(lines)

    # 1. Nomor dokumen
    nomor = extract_number(lines)

    # 2. Tanggal: utamakan label tanggal, lalu cari pola tanggal umum.
    raw_date = find_labeled_value(
        lines,
        [r"tanggal", r"tgl\.?"]
    )
    tanggal = normalize_date(raw_date)

    if not tanggal:
        date_match = re.search(
            rf"\b\d{{1,2}}\s+(?:{MONTH_PATTERN})\s+\d{{4}}\b"
            r"|\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b",
            alltext,
            re.IGNORECASE
        )
        if date_match:
            tanggal = normalize_date(date_match.group(0))

    # 3. Perihal/Hal
    perihal = find_labeled_value(
        lines,
        [r"perihal", r"hal"]
    )

    # Jika label tidak ditemukan, cari kandidat judul yang masuk akal.
    # Jangan otomatis mengambil baris pertama.
    if not perihal:
        excluded = re.compile(
            r"^(nomor|no\.?|tanggal|tgl\.?|lampiran|sifat|"
            r"kepada|yth\.?|dengan hormat|perihal|hal)\b",
            re.IGNORECASE
        )
        candidates = []

        for line in lines[:30]:
            if len(line) < 12 or excluded.search(line):
                continue
            if re.search(r"\b(?:dinas|pemerintah|provinsi|kabupaten)\b",
                         line, re.IGNORECASE):
                continue
            if normalize_date(line):
                continue
            if len(re.findall(r"[A-Za-z]", line)) < 8:
                continue

            candidates.append(line)

        # Kandidat hanya saran; tetap perlu pemeriksaan arsiparis.
        if candidates:
            preferred = next(
                (
                    x for x in candidates
                    if re.search(
                        r"usul|reklasifikasi|permohonan|laporan|"
                        r"pengadaan|undangan|keputusan",
                        x,
                        re.IGNORECASE
                    )
                ),
                ""
            )
            perihal = preferred or ""

    # 4. Unit kerja
    unit = ""
    for line in lines[:40]:
        if re.search(
            r"\b(dinas|badan|kantor|uptd|sekretariat|bidang|bagian)\b",
            line,
            re.IGNORECASE
        ) and len(line) <= 160:
            unit = line
            break

    # 5. Jenis dokumen: gunakan nama file sebagai petunjuk awal.
    name = (filename or "").lower()
    kind = "Dokumen Umum"

    kinds = [
        ("berita_acara", "Berita Acara"),
        ("berita acara", "Berita Acara"),
        ("perjanjian", "Perjanjian"),
        ("laporan", "Laporan"),
        ("nota", "Nota Dinas"),
        ("undangan", "Surat Undangan"),
        ("keputusan", "Surat Keputusan"),
        ("reklas", "Surat Usulan/Reklasifikasi"),
        ("usul", "Surat Usulan"),
        ("surat", "Surat"),
    ]

    for key, label in kinds:
        if key in name:
            kind = label
            break

    # 6. Tahun: tanggal lebih diutamakan.
    year_match = re.search(r"\b(20\d{2})\b", tanggal)
    if not year_match:
        year_match = re.search(r"\b(20\d{2})\b", alltext)

    tahun = year_match.group(1) if year_match else ""

    return {
        "nomor": nomor,
        "tanggal": tanggal,
        "perihal": perihal[:250],
        "unit_kerja": unit,
        "jenis_dokumen": kind,
        "tahun": tahun
    }
