
import os
import re
import hashlib
import hmac

import pandas as pd
import streamlit as st

from modules.database import (
    init_db,
    insert_archive,
    get_archives,
    get_stats,
    update_status,
    get_archive,
    delete_archive,
)
from modules.document_reader import extract_pdf_text
from modules.ocr import ocr_pdf
from modules.metadata import extract_metadata
from modules.classifier import classify_document, RULES


# =========================================================
# 1. KONFIGURASI APLIKASI
# =========================================================

ROOT = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(ROOT, "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)
init_db()

st.set_page_config(
    page_title="ARSIP.AI | Sistem Kearsipan Cerdas",
    page_icon="📁",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# 2. STYLE PREMIUM
# =========================================================

st.markdown(
    """
    <style>
    :root {
        --primary: #175cd3;
        --primary-dark: #123b70;
        --primary-soft: #eaf2ff;
        --background: #f5f7fb;
        --surface: #ffffff;
        --text: #172b4d;
        --muted: #66758a;
        --border: #e3e9f2;
        --success: #13845b;
        --warning: #b7791f;
        --danger: #c43232;
        --radius: 15px;
        --shadow: 0 5px 22px rgba(24, 47, 83, .055);
    }

    /* GLOBAL */
    .stApp {
        background: var(--background);
        color: var(--text);
        font-family: Inter, "Segoe UI", sans-serif;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.7rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3, h4 {
        color: var(--text);
        font-weight: 750;
        letter-spacing: -.3px;
    }

    h1 {
        font-size: clamp(1.65rem, 3vw, 2.2rem);
    }

    h2 {
        font-size: 1.45rem;
    }

    h3 {
        font-size: 1.12rem;
    }

    hr {
        border-color: var(--border);
        margin: 1.4rem 0;
    }

    [data-testid="stCaptionContainer"] {
        color: var(--muted);
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--border);
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.3rem;
    }

    section[data-testid="stSidebar"] h2 {
        color: var(--primary-dark);
        font-size: 1.5rem;
        font-weight: 850;
    }

    section[data-testid="stSidebar"] [data-testid="stRadio"] {
        margin-top: 12px;
    }

    section[data-testid="stSidebar"] [data-testid="stRadio"] label p {
        font-size: .92rem;
        font-weight: 550;
    }

    /* HERO */
    .hero {
        position: relative;
        overflow: hidden;
        background: linear-gradient(
            120deg,
            #10376b 0%,
            #175cd3 68%,
            #3985ef 100%
        );
        padding: 27px 30px;
        border-radius: 18px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 12px 28px rgba(23, 92, 211, .14);
    }

    .hero::after {
        content: "";
        position: absolute;
        width: 180px;
        height: 180px;
        right: -50px;
        top: -90px;
        border: 26px solid rgba(255,255,255,.09);
        border-radius: 50%;
        pointer-events: none;
    }

    .hero h1 {
        position: relative;
        z-index: 1;
        color: #ffffff;
        margin: 0;
        line-height: 1.35;
        font-size: clamp(1.5rem, 3vw, 2rem);
    }

    .hero p {
        position: relative;
        z-index: 1;
        color: #e4efff;
        margin: 8px 0 0;
        font-size: .96rem;
    }

    /* SECTION HEADER */
    .section-heading {
        font-size: 1.12rem;
        font-weight: 750;
        color: var(--text);
        margin: 5px 0 3px;
    }

    .section-description {
        color: var(--muted);
        font-size: .87rem;
        margin-bottom: 15px;
    }

    /* METRIC CARDS */
    [data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 18px 19px;
        box-shadow: var(--shadow);
        min-height: 108px;
    }

    [data-testid="stMetricLabel"] {
        color: var(--muted);
        font-size: .85rem;
        font-weight: 600;
    }

    [data-testid="stMetricValue"] {
        color: var(--primary-dark);
        font-size: clamp(1.45rem, 2.3vw, 2rem);
        font-weight: 800;
    }

    /* INPUT */
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div {
        border-color: #d6deea;
        border-radius: 10px;
        background: #ffffff;
    }

    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="textarea"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within {
        border-color: var(--primary);
        box-shadow: 0 0 0 2px rgba(23, 92, 211, .12);
    }

    /* BUTTONS */
    .stButton > button,
    .stDownloadButton > button,
    [data-testid="stFormSubmitButton"] > button {
        border-radius: 10px;
        min-height: 41px;
        font-weight: 650;
        transition: all .18s ease;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: var(--primary);
    }

    /* FORMS */
    [data-testid="stForm"] {
        background: #ffffff;
        border: 1px solid var(--border);
        border-radius: 15px;
        padding: 22px;
        box-shadow: var(--shadow);
    }

    /* LOGIN CARD: hanya form yang berisi password */
    div[data-testid="stForm"]:has(input[type="password"]) {
        width: 100%;
        max-width: 410px;
        margin: 0 auto;
        padding: 28px;
        box-sizing: border-box;
        border-radius: 18px;
        box-shadow: 0 15px 45px rgba(24, 47, 83, .10);
    }

    div[data-testid="stForm"]:has(input[type="password"]) h2,
    div[data-testid="stForm"]:has(input[type="password"]) h3 {
        text-align: center;
        color: var(--primary-dark);
    }

    div[data-testid="stForm"]:has(input[type="password"]) input {
        min-height: 42px;
    }

    /* LOGIN BRAND */
    .login-brand {
        color: #073b70;
        font-size: 2.05rem;
        font-weight: 850;
        letter-spacing: -1px;
        text-align: center;
        margin-bottom: 5px;
    }

    .login-sub {
        color: var(--muted);
        text-align: center;
        font-size: .91rem;
        line-height: 1.6;
        margin-bottom: 24px;
    }

    .login-footer {
        max-width: 410px;
        margin: 15px auto 0;
        color: var(--muted);
        font-size: .8rem;
        text-align: center;
    }

    /* TABLE */
    [data-testid="stDataFrame"] {
        background: #ffffff;
        border: 1px solid var(--border);
        border-radius: 13px;
        overflow: hidden;
        box-shadow: var(--shadow);
    }

    /* EXPANDER */
    [data-testid="stExpander"] {
        border: 1px solid var(--border);
        border-radius: 12px;
        background: #ffffff;
    }

    [data-testid="stExpander"] summary {
        font-weight: 650;
    }

    /* UPLOADER */
    [data-testid="stFileUploader"] {
        background: #ffffff;
        border: 1px dashed #a9bfdc;
        border-radius: 14px;
        padding: 14px;
    }

    /* ALERTS */
    [data-testid="stAlert"] {
        border-radius: 12px;
    }

    /* CHARTS */
    [data-testid="stVegaLiteChart"],
    [data-testid="stArrowVegaLiteChart"],
    [data-testid="stPlotlyChart"] {
        background: #ffffff;
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 10px;
        box-shadow: var(--shadow);
    }

    /* MOBILE */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 1rem 2rem;
        }

        .hero {
            padding: 21px 19px;
            border-radius: 14px;
        }

        [data-testid="stMetric"] {
            padding: 13px;
            min-height: 92px;
        }

        [data-testid="stMetricLabel"] {
            font-size: .77rem;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.35rem;
        }

        [data-testid="stForm"] {
            padding: 16px;
        }
    }

    @media (max-width: 480px) {
        .login-brand {
            font-size: 1.75rem;
        }

        .hero h1 {
            font-size: 1.45rem;
        }

        .hero p {
            font-size: .87rem;
        }

        div[data-testid="stForm"]:has(input[type="password"]) {
            max-width: 100%;
            padding: 21px 17px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 3. FUNGSI BANTUAN
# =========================================================

def hero(title, subtitle):
    st.markdown(
        f"""
        <div class="hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_heading(title, description=None):
    st.markdown(
        f'<div class="section-heading">{title}</div>',
        unsafe_allow_html=True,
    )

    if description:
        st.markdown(
            f'<div class="section-description">{description}</div>',
            unsafe_allow_html=True,
        )


def resolve_pdf_path(record):
    """Mencari PDF yang berada di dalam direktori proyek."""

    candidates = []
    stored_path = record.get("file_path")

    if stored_path:
        candidates.append(stored_path)

    filename = os.path.basename(record.get("filename") or "")

    if filename:
        candidates.append(os.path.join(UPLOAD_DIR, filename))

    for candidate in candidates:
        if not candidate:
            continue

        full_path = os.path.realpath(candidate)

        try:
            inside_project = (
                os.path.commonpath([ROOT, full_path]) == ROOT
            )
        except ValueError:
            inside_project = False

        if (
            inside_project
            and os.path.isfile(full_path)
            and full_path.lower().endswith(".pdf")
        ):
            return full_path

    return None


def is_inside_uploads(path):
    """Memastikan file PDF berada langsung di folder uploads."""

    if not path:
        return False

    uploads_real = os.path.realpath(UPLOAD_DIR)
    file_real = os.path.realpath(path)

    return (
        os.path.dirname(file_real) == uploads_real
        and os.path.isfile(file_real)
        and file_real.lower().endswith(".pdf")
    )


def download_pdf_button(record, key_prefix="pdf"):
    """Menampilkan tombol untuk mengunduh PDF asli."""

    pdf_path = resolve_pdf_path(record)

    if not pdf_path:
        st.warning(
            "PDF asli tidak ditemukan. Periksa folder uploads "
            "dan lokasi file_path pada database."
        )
        return

    try:
        with open(pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()

        st.download_button(
            label="📥 Download PDF Asli",
            data=pdf_bytes,
            file_name=os.path.basename(pdf_path),
            mime="application/pdf",
            key=f"{key_prefix}_{record['id']}",
            use_container_width=True,
        )

    except OSError as error:
        st.error(f"Gagal membaca PDF: {error}")


def display_archives(rows):
    """Menambahkan nomor urut tampilan tanpa mengubah ID database."""

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    if "No." in df.columns:
        df = df.drop(columns=["No."])

    df.insert(0, "No.", range(1, len(df) + 1))
    return df


def show_archive_table(df, columns):
    """Menampilkan kolom tabel yang tersedia saja."""

    available = [column for column in columns if column in df.columns]

    if not available:
        st.info("Kolom arsip belum tersedia untuk ditampilkan.")
        return

    st.dataframe(
        df[available],
        use_container_width=True,
        hide_index=True,
    )


def archive_label(row):
    """Membuat label pilihan arsip yang mudah dikenali."""

    return (
        f"ID #{row['id']} — "
        f"{row.get('filename') or 'Tanpa nama'}"
    )


# =========================================================
# 4. LOGIN / AUTENTIKASI
# =========================================================

def password_hash(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


ADMIN_USER = os.environ.get("ARSIP_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get(
    "ARSIP_ADMIN_PASSWORD",
    "ArsipAI#2026",
)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:

    # Latar khusus halaman login.
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(
                    circle at 10% 5%,
                    #e2efff 0%,
                    transparent 42%
                ),
                #f4f7fb;
        }

        .block-container {
            padding-top: 3vh;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, center_col, _ = st.columns([1, 1.5, 1])

    with center_col:

        st.markdown(
            """
            <div style="padding-top:4vh">
                <div class="login-brand">📁 ARSIP.AI</div>
                <div class="login-sub">
                    Sistem Kearsipan Cerdas Berbasis AI<br>
                    Kelola dokumen secara lebih terstruktur.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("login_form"):

            st.subheader("Masuk ke Sistem")

            username = st.text_input(
                "Username",
                placeholder="Masukkan username",
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Masukkan password",
            )

            login_submit = st.form_submit_button(
                "Masuk ke ARSIP.AI",
                type="primary",
                use_container_width=True,
            )

        if login_submit:

            valid_user = hmac.compare_digest(
                username.strip(),
                ADMIN_USER,
            )

            valid_password = hmac.compare_digest(
                password_hash(password),
                password_hash(ADMIN_PASSWORD),
            )

            if valid_user and valid_password:
                st.session_state.authenticated = True
                st.session_state.login_user = username.strip()
                st.rerun()
            else:
                st.error("Username atau password salah.")

        st.markdown(
            """
            <div class="login-footer">
                🔒 Akses terbatas untuk pengguna yang berwenang.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.stop()


# =========================================================
# 5. SIDEBAR NAVIGASI
# =========================================================

# Terapkan navigasi yang diminta sebelum widget radio dibuat.
# Pola ini mencegah StreamlitWidgetAlreadyInstantiatedError.
_pending_page = st.session_state.pop("_pending_navigation", None)
if _pending_page in {
    "Dashboard",
    "Upload & Proses AI",
    "Repository Arsip",
    "Tentang Sistem",
}:
    st.session_state["main_navigation"] = _pending_page

with st.sidebar:

    st.markdown("## 📁 ARSIP.AI")
    st.caption("Sistem Kearsipan Cerdas Berbasis AI")

    st.divider()

    page = st.radio(
        "MENU UTAMA",
        [
            "Dashboard",
            "Upload & Proses AI",
            "Repository Arsip",
            "Tentang Sistem",
        ],
        key="main_navigation",
    )

    st.divider()

    st.markdown("**👤 Pengguna Aktif**")
    st.caption(
        st.session_state.get("login_user", "admin")
    )

    if st.button(
        "Keluar / Logout",
        use_container_width=True,
        key="logout_button",
    ):
        st.session_state.authenticated = False
        st.session_state.pop("login_user", None)
        st.rerun()

    st.divider()

    st.caption("ARSIP.AI · Prototipe Tahap 1")
    st.caption("Penyimpanan lokal")


# =========================================================
# 6. DASHBOARD
# =========================================================

if page == "Dashboard":

    hero(
        "Dashboard ARSIP.AI",
        "Pusat informasi dan pengelolaan arsip digital Anda.",
    )

    stats = get_stats() or {}

    total = stats.get("total", 0) or 0
    validated = stats.get("validated", 0) or 0
    review = stats.get("review", 0) or 0
    categories_count = stats.get("categories", 0) or 0

    section_heading(
        "Ringkasan Arsip",
        "Gambaran umum dokumen yang tersimpan di sistem.",
    )

    cols = st.columns(4)

    metrics = [
        ("📚", "Total Arsip", total),
        ("✅", "Tervalidasi", validated),
        ("⏳", "Perlu Validasi", review),
        ("🗂️", "Kategori Terisi", categories_count),
    ]

    for col, (icon, label, value) in zip(cols, metrics):
        with col:
            st.metric(
                label=f"{icon} {label}",
                value=f"{value:,}",
            )

    st.divider()

    rows = get_archives(limit=10) or []

    section_heading(
        "Aktivitas Terbaru",
        "Sepuluh arsip terakhir yang masuk ke sistem.",
    )

    if rows:

        df = display_archives(rows)

        show_archive_table(
            df,
            [
                "No.",
                "id",
                "filename",
                "jenis_dokumen",
                "nomor",
                "tanggal",
                "kategori",
                "status",
                "created_at",
            ],
        )

        st.markdown("### Statistik Arsip")

        chart_left, chart_right = st.columns(2)

        with chart_left:
            st.markdown("**Distribusi Kategori**")

            if "kategori" in df.columns:
                category_data = (
                    df["kategori"]
                    .fillna("Belum diklasifikasi")
                    .replace("", "Belum diklasifikasi")
                    .value_counts()
                )

                if not category_data.empty:
                    st.bar_chart(category_data)
                else:
                    st.info("Belum ada data kategori.")
            else:
                st.info("Kolom kategori belum tersedia.")

        with chart_right:
            st.markdown("**Distribusi Status**")

            if "status" in df.columns:
                status_data = (
                    df["status"]
                    .fillna("Belum ditentukan")
                    .value_counts()
                )

                if not status_data.empty:
                    st.bar_chart(status_data)
                else:
                    st.info("Belum ada data status.")
            else:
                st.info("Kolom status belum tersedia.")

        st.info(
            "Untuk melihat detail, mengunduh PDF, memvalidasi, "
            "atau menghapus arsip, buka menu Repository Arsip."
        )

    else:
        st.info(
            "Repository masih kosong. Unggah dokumen pertama "
            "melalui menu Upload & Proses AI."
        )

        if st.button(
            "📤 Mulai Upload Arsip",
            type="primary",
            key="dashboard_upload",
        ):
            st.session_state["_pending_navigation"] = "Upload & Proses AI"
            st.rerun()

    st.divider()

    st.caption(
        "Catatan: hasil klasifikasi AI merupakan rekomendasi "
        "awal dan harus diperiksa oleh arsiparis."
    )

    st.warning(
        "Gunakan dokumen non-rahasia selama uji coba. "
        "Pastikan backup dan pengamanan data tersedia sebelum "
        "sistem digunakan untuk dokumen resmi."
    )


# =========================================================
# 7. UPLOAD & PROSES AI
# =========================================================

elif page == "Upload & Proses AI":

    hero(
        "Upload Arsip & Proses AI",
        "Unggah PDF, ekstrak teks, periksa metadata, lalu simpan arsip.",
    )

    section_heading(
        "Langkah 1 — Pilih Dokumen",
        "Format yang diterima adalah PDF dengan ukuran maksimum 20 MB.",
    )

    up = st.file_uploader(
        "Pilih file PDF",
        type=["pdf"],
        key="archive_uploader",
        help="Pilih dokumen PDF yang akan diproses.",
    )

    if up:

        if up.size > 20 * 1024 * 1024:
            st.error("Ukuran file maksimum 20 MB.")
            st.stop()

        if up.size == 0:
            st.error("File yang dipilih kosong.")
            st.stop()

        safe_name = re.sub(
            r"[^A-Za-z0-9._-]+",
            "_",
            os.path.basename(up.name),
        ).strip("._")

        if not safe_name:
            safe_name = "dokumen.pdf"

        if not safe_name.lower().endswith(".pdf"):
            safe_name += ".pdf"

        path = os.path.realpath(
            os.path.join(UPLOAD_DIR, safe_name)
        )

        try:
            inside_uploads = (
                os.path.commonpath(
                    [os.path.realpath(UPLOAD_DIR), path]
                )
                == os.path.realpath(UPLOAD_DIR)
            )
        except ValueError:
            inside_uploads = False

        if not inside_uploads:
            st.error("Lokasi penyimpanan file tidak valid.")
            st.stop()

        try:
            # Simpan file sumber.
            with open(path, "wb") as file:
                file.write(up.getbuffer())

            # Ekstraksi teks PDF.
            with st.spinner("Membaca teks dari dokumen PDF..."):
                txt = extract_pdf_text(path) or ""

            method = "Ekstraksi teks PDF"

            # OCR jika PDF berupa hasil pindai.
            if len(txt.strip()) < 80:
                with st.spinner("Teks sedikit. Menjalankan OCR..."):
                    txt = ocr_pdf(path) or ""

                method = "OCR"

            if not txt.strip():
                st.error(
                    "Teks tidak berhasil dibaca. Periksa file PDF "
                    "atau konfigurasi Tesseract OCR."
                )
                st.stop()

            # Ekstraksi metadata dan klasifikasi.
            with st.spinner("Menganalisis metadata dan klasifikasi..."):
                meta = extract_metadata(txt, up.name)
                pred = classify_document(txt, meta)

        except Exception as error:
            st.error(f"Gagal memproses PDF: {error}")
            st.stop()

        st.success(f"Dokumen berhasil dibaca menggunakan {method}.")

        section_heading(
            "Dokumen Sumber",
            "File asli tetap tersedia untuk diunduh.",
        )

        st.download_button(
            label="📥 Download PDF yang Diunggah",
            data=up.getvalue(),
            file_name=safe_name,
            mime="application/pdf",
            key=f"upload_pdf_{safe_name}",
        )

        with st.expander("👁️ Pratinjau teks hasil ekstraksi"):
            st.text_area(
                "Teks dokumen",
                txt,
                height=220,
                key=f"preview_{safe_name}",
            )

        st.divider()

        section_heading(
            "Langkah 2 — Periksa Metadata",
            "Periksa hasil rekomendasi sebelum menyimpan dokumen.",
        )

        categories = list(dict.fromkeys(
            list(RULES.keys()) + ["Perlu Review Arsiparis"]
        ))

        suggested = pred.get("kategori", "Perlu Review Arsiparis")

        if suggested not in categories:
            suggested = "Perlu Review Arsiparis"

        with st.form("save_form"):

            left, right = st.columns(2)

            with left:
                filename = st.text_input(
                    "Nama file",
                    value=up.name,
                )

                jenis = st.text_input(
                    "Jenis dokumen",
                    value=meta.get("jenis_dokumen", ""),
                )

                nomor = st.text_input(
                    "Nomor dokumen",
                    value=meta.get("nomor", ""),
                )

                tanggal = st.text_input(
                    "Tanggal dokumen",
                    value=meta.get("tanggal", ""),
                )

            with right:
                perihal = st.text_input(
                    "Perihal",
                    value=meta.get("perihal", ""),
                )

                unit = st.text_input(
                    "Unit kerja",
                    value=meta.get("unit_kerja", ""),
                )

                tahun = st.text_input(
                    "Tahun",
                    value=meta.get("tahun", ""),
                )

                kategori = st.selectbox(
                    "Klasifikasi arsip",
                    categories,
                    index=categories.index(suggested),
                )

            st.divider()

            st.markdown("**Hasil analisis klasifikasi**")

            confidence = pred.get("confidence", 0)
            try:
                confidence = float(confidence)
            except (ValueError, TypeError):
                confidence = 0.0

            confidence = max(0.0, min(1.0, confidence))

            st.info(
                f"Kategori rekomendasi: **{suggested}**  \n"
                f"Keyakinan indikatif: **{confidence:.0%}**"
            )

            evidence = pred.get("evidence", [])

            st.caption(
                "Kata kunci pendukung: "
                + (
                    ", ".join(map(str, evidence))
                    if evidence
                    else "Tidak ditemukan; perlu pemeriksaan manual."
                )
            )

            status = st.radio(
                "Status arsip",
                ["Perlu Validasi", "Tervalidasi"],
                horizontal=True,
            )

            checked = st.checkbox(
                "Saya telah memeriksa metadata dan klasifikasi."
            )

            submit = st.form_submit_button(
                "💾 Simpan Arsip",
                type="primary",
                use_container_width=True,
            )

        if submit:

            if not checked:
                st.error(
                    "Centang konfirmasi setelah memeriksa metadata."
                )

            elif not filename.strip():
                st.error("Nama file wajib diisi.")

            else:
                try:
                    archive_id = insert_archive(
                        filename=filename.strip(),
                        file_path=path,
                        jenis_dokumen=jenis.strip(),
                        nomor=nomor.strip(),
                        tanggal=tanggal.strip(),
                        perihal=perihal.strip(),
                        unit_kerja=unit.strip(),
                        tahun=tahun.strip(),
                        kategori=kategori,
                        confidence=confidence,
                        extracted_text=txt,
                        status=status,
                    )

                    if archive_id is not None:
                        st.success(
                            f"Arsip berhasil disimpan dengan ID #{archive_id}."
                        )
                        st.session_state["_pending_navigation"] = "Repository Arsip"
                        st.rerun()
                    else:
                        st.error(
                            "Database tidak mengembalikan ID arsip. "
                            "Periksa fungsi insert_archive."
                        )

                except Exception as error:
                    st.error(f"Gagal menyimpan arsip: {error}")


# =========================================================
# 8. REPOSITORY ARSIP
# =========================================================

elif page == "Repository Arsip":

    hero(
        "Repository Arsip",
        "Temukan, tinjau, validasi, dan unduh dokumen tersimpan.",
    )

    section_heading(
        "Pencarian dan Filter",
        "Gunakan kata kunci atau filter untuk mempersempit daftar arsip.",
    )

    categories = list(dict.fromkeys(
        list(RULES.keys()) + ["Perlu Review Arsiparis"]
    ))

    col_search, col_category, col_status = st.columns([2, 1, 1])

    with col_search:
        query = st.text_input(
            "Cari arsip",
            placeholder="Nama file, nomor, perihal, atau teks...",
            key="repository_search",
        )

    with col_category:
        category = st.selectbox(
            "Kategori",
            ["Semua"] + categories,
            key="repository_category",
        )

    with col_status:
        status_filter = st.selectbox(
            "Status",
            ["Semua", "Perlu Validasi", "Tervalidasi"],
            key="repository_status",
        )

    try:
        rows = get_archives(
            search=query,
            kategori=category,
            status=status_filter,
        ) or []
    except Exception as error:
        st.error(f"Gagal memuat repository: {error}")
        rows = []

    st.divider()

    if rows:

        df = display_archives(rows)

        section_heading(
            f"Daftar Arsip ({len(rows)})",
            "Pilih arsip pada bagian detail untuk melakukan tindakan.",
        )

        show_archive_table(
            df,
            [
                "No.",
                "id",
                "filename",
                "jenis_dokumen",
                "nomor",
                "tanggal",
                "perihal",
                "unit_kerja",
                "tahun",
                "kategori",
                "status",
                "created_at",
            ],
        )

        # Ekspor CSV tanpa kolom internal yang berisi teks lengkap/path.
        csv_data = df.drop(
            columns=["extracted_text", "file_path"],
            errors="ignore",
        ).to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="📊 Unduh Daftar Arsip (CSV)",
            data=csv_data,
            file_name="daftar_arsip.csv",
            mime="text/csv",
            key="download_archive_csv",
        )

        st.divider()

        section_heading(
            "Detail dan Tindakan Arsip",
            "Pilih dokumen untuk melihat metadata, mengunduh PDF, "
            "memvalidasi, atau menghapusnya.",
        )

        selected_id = st.selectbox(
            "Pilih dokumen",
            options=[row["id"] for row in rows],
            format_func=lambda archive_id: next(
                (
                    archive_label(row)
                    for row in rows
                    if row["id"] == archive_id
                ),
                f"ID #{archive_id}",
            ),
            key="selected_archive_id",
        )

        record = get_archive(selected_id)

        if record:

            st.markdown(
                f"### 📄 {record.get('filename') or 'Tanpa nama'}"
            )

            current_status = record.get("status") or "Belum ditentukan"

            st.caption(
                f"ID database: #{record['id']} · Status: {current_status}"
            )

            detail_left, detail_right = st.columns(2)

            with detail_left:
                with st.container(border=True):
                    st.markdown("**Informasi Dokumen**")
                    st.write(
                        "**Perihal:**",
                        record.get("perihal") or "-",
                    )
                    st.write(
                        "**Nomor:**",
                        record.get("nomor") or "-",
                    )
                    st.write(
                        "**Tanggal:**",
                        record.get("tanggal") or "-",
                    )
                    st.write(
                        "**Unit kerja:**",
                        record.get("unit_kerja") or "-",
                    )

            with detail_right:
                with st.container(border=True):
                    st.markdown("**Klasifikasi dan Status**")
                    st.write(
                        "**Jenis:**",
                        record.get("jenis_dokumen") or "-",
                    )
                    st.write(
                        "**Kategori:**",
                        record.get("kategori") or "-",
                    )
                    st.write(
                        "**Tahun:**",
                        record.get("tahun") or "-",
                    )
                    st.write(
                        "**Status:**",
                        current_status,
                    )

            st.markdown("**Dokumen Asli**")

            download_pdf_button(
                record,
                key_prefix="repository_pdf",
            )

            with st.expander("👁️ Teks hasil ekstraksi"):
                st.text_area(
                    "Teks dokumen",
                    value=record.get("extracted_text") or "",
                    height=230,
                    key=f"txt_{selected_id}",
                )

            # VALIDASI
            st.divider()

            section_heading(
                "Validasi Arsip",
                "Pastikan metadata dan klasifikasi telah diperiksa.",
            )

            if current_status != "Tervalidasi":

                if st.button(
                    "✅ Tandai sebagai Tervalidasi",
                    type="primary",
                    key=f"validate_{selected_id}",
                ):
                    try:
                        update_status(selected_id, "Tervalidasi")
                        st.success("Status arsip berhasil diperbarui.")
                        st.rerun()
                    except Exception as error:
                        st.error(f"Gagal memperbarui status: {error}")

            else:
                st.success("Arsip ini sudah berstatus Tervalidasi.")

            # PENGHAPUSAN
            st.divider()

            section_heading(
                "Penghapusan Arsip",
                "Periksa pilihan dengan teliti. Penghapusan data tidak "
                "dapat dibatalkan dari halaman ini.",
            )

            with st.container(border=True):

                st.markdown("**🗑️ Hapus Arsip Terpilih**")

                delete_pdf = st.checkbox(
                    "Hapus juga file PDF asli dari folder uploads",
                    value=False,
                    key=f"delete_pdf_{selected_id}",
                    help=(
                        "Jika tidak dicentang, record database dihapus "
                        "tetapi file PDF asli tetap disimpan."
                    ),
                )

                confirm_delete = st.checkbox(
                    f"Saya yakin ingin menghapus arsip ID #{selected_id}.",
                    value=False,
                    key=f"confirm_delete_{selected_id}",
                )

                if st.button(
                    "🗑️ Hapus Arsip Terpilih",
                    type="primary",
                    key=f"delete_archive_{selected_id}",
                    use_container_width=True,
                ):

                    if not confirm_delete:
                        st.error(
                            "Centang kotak konfirmasi sebelum menghapus."
                        )

                    else:
                        try:
                            # Simpan lokasi file sebelum record dihapus.
                            pdf_path = resolve_pdf_path(record)

                            # Hapus record memakai ID database asli.
                            deleted = delete_archive(selected_id)

                            if deleted:

                                if delete_pdf:

                                    if (
                                        pdf_path
                                        and is_inside_uploads(pdf_path)
                                    ):
                                        try:
                                            os.remove(pdf_path)
                                            st.success(
                                                "Data arsip dan file PDF "
                                                "berhasil dihapus."
                                            )
                                        except OSError as error:
                                            st.warning(
                                                "Data arsip sudah dihapus, "
                                                "tetapi file PDF gagal dihapus: "
                                                f"{error}"
                                            )
                                    else:
                                        st.warning(
                                            "Data arsip sudah dihapus, "
                                            "tetapi file PDF tidak ditemukan "
                                            "atau lokasinya tidak sesuai."
                                        )

                                else:
                                    st.success(
                                        "Data arsip berhasil dihapus. "
                                        "File PDF asli tetap disimpan."
                                    )

                                # Bersihkan state pilihan agar tidak menunjuk
                                # ke arsip yang sudah dihapus.
                                st.session_state.pop(
                                    "selected_archive_id",
                                    None,
                                )
                                st.session_state.pop(
                                    f"confirm_delete_{selected_id}",
                                    None,
                                )
                                st.session_state.pop(
                                    f"delete_pdf_{selected_id}",
                                    None,
                                )

                                st.rerun()

                            else:
                                st.error(
                                    "Arsip tidak ditemukan atau sudah dihapus."
                                )

                        except Exception as error:
                            st.error(
                                f"Gagal menghapus arsip: {error}"
                            )

    else:
        st.info(
            "Tidak ada arsip yang cocok dengan pencarian atau filter. "
            "Coba kata kunci lain atau pilih kategori Semua."
        )


# =========================================================
# 9. TENTANG SISTEM
# =========================================================

elif page == "Tentang Sistem":

    hero(
        "Tentang ARSIP.AI",
        "Asisten digital untuk mendukung pengelolaan arsip yang terstruktur.",
    )

    section_heading(
        "Gambaran Sistem",
        "Prototipe pengelolaan dokumen digital dengan bantuan ekstraksi "
        "teks dan klasifikasi awal.",
    )

    st.markdown(
        """
        ARSIP.AI membantu proses penerimaan, pembacaan, pengelompokan,
        dan peninjauan dokumen. Sistem memberikan rekomendasi awal
        sehingga arsiparis dapat memeriksa metadata dan menentukan
        klasifikasi yang tepat.
        """
    )

    st.divider()

    feature_left, feature_right = st.columns(2)

    with feature_left:
        with st.container(border=True):
            st.markdown("### 📤 Pengolahan Dokumen")
            st.markdown(
                """
                - Upload dokumen PDF
                - Ekstraksi teks dari PDF
                - OCR untuk dokumen hasil pindai
                - Ekstraksi metadata berbasis pola
                - Rekomendasi klasifikasi berbasis kata kunci
                """
            )

    with feature_right:
        with st.container(border=True):
            st.markdown("### 🗂️ Pengelolaan Repository")
            st.markdown(
                """
                - Pencarian dan filter arsip
                - Koreksi metadata sebelum penyimpanan
                - Validasi oleh pengguna
                - Download dokumen PDF asli
                - Ekspor daftar arsip ke CSV
                - Penghapusan dengan konfirmasi
                """
            )

    st.divider()

    st.markdown("### 🔐 Catatan Keamanan")

    st.warning(
        "Versi ini masih berupa prototipe. Kredensial default perlu "
        "diganti, akses database dan folder uploads perlu dilindungi, "
        "dan backup harus disiapkan sebelum penggunaan resmi."
    )

    st.markdown(
        """
        **Batasan sistem**

        Klasifikasi saat ini berbasis aturan dan kata kunci, bukan model
        pembelajaran mesin yang telah dilatih. Nilai keyakinan yang
        ditampilkan adalah indikator dari classifier dan tidak boleh
        dianggap sebagai jaminan ketepatan klasifikasi.

        **Rekomendasi sebelum produksi**

        - Gunakan autentikasi yang aman dan pengelolaan akun.
        - Terapkan audit trail untuk perubahan dan penghapusan.
        - Siapkan backup serta prosedur pemulihan data.
        - Batasi akses ke dokumen sesuai kewenangan.
        - Sesuaikan klasifikasi dengan pedoman kearsipan instansi.
        """
    )

    st.divider()

    st.caption(
        "ARSIP.AI · Prototipe Tahap 1 · Sistem Kearsipan Cerdas Berbasis AI"
    )
