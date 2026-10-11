import os, sqlite3
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "data", "arsip.db")

def connect():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with connect() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS archives (
          id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL, file_path TEXT,
          jenis_dokumen TEXT, nomor TEXT, tanggal TEXT, perihal TEXT, unit_kerja TEXT,
          tahun TEXT, kategori TEXT, confidence REAL DEFAULT 0, extracted_text TEXT,
          status TEXT DEFAULT 'Perlu Validasi', created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

def insert_archive(**kw):
    keys = ["filename","file_path","jenis_dokumen","nomor","tanggal","perihal","unit_kerja","tahun","kategori","confidence","extracted_text","status"]
    vals = [kw.get(k, "") for k in keys]
    with connect() as c:
        cur = c.execute(f"INSERT INTO archives ({','.join(keys)}) VALUES ({','.join(['?']*len(keys))})", vals)
        return cur.lastrowid

def get_archives(search="", kategori="Semua", status="Semua", limit=None):
    sql = "SELECT * FROM archives WHERE 1=1"; args=[]
    if search:
        sql += " AND (filename LIKE ? OR perihal LIKE ? OR nomor LIKE ? OR extracted_text LIKE ?)"
        args += [f"%{search}%"]*4
    if kategori != "Semua": sql += " AND kategori=?"; args.append(kategori)
    if status != "Semua": sql += " AND status=?"; args.append(status)
    sql += " ORDER BY id DESC"
    if limit: sql += " LIMIT ?"; args.append(int(limit))
    with connect() as c: return [dict(r) for r in c.execute(sql,args).fetchall()]

def get_stats():
    with connect() as c:
        return {
          "total": c.execute("SELECT COUNT(*) FROM archives").fetchone()[0],
          "validated": c.execute("SELECT COUNT(*) FROM archives WHERE status='Tervalidasi'").fetchone()[0],
          "review": c.execute("SELECT COUNT(*) FROM archives WHERE status='Perlu Validasi'").fetchone()[0],
          "categories": c.execute("SELECT COUNT(DISTINCT kategori) FROM archives WHERE kategori IS NOT NULL AND kategori!=''").fetchone()[0]
        }

def get_archive(i):
    with connect() as c:
        r=c.execute("SELECT * FROM archives WHERE id=?", (int(i),)).fetchone()
        return dict(r) if r else None

def update_status(i, status):
    with connect() as c: c.execute("UPDATE archives SET status=? WHERE id=?", (status,int(i)))

def delete_archive(i):
    """Menghapus satu arsip dari database berdasarkan ID."""

    with connect() as c:
        cur = c.execute(
            "DELETE FROM archives WHERE id = ?",
            (int(i),)
        )

        return cur.rowcount > 0

def reset_archive_id_if_empty():
    """
    Mengatur ulang ID arsip jika tabel benar-benar kosong.
    Aman: tidak mengubah ID ketika masih ada arsip.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM archives")
        total = cursor.fetchone()[0]

        if total == 0:
            cursor.execute(
                "DELETE FROM sqlite_sequence WHERE name = ?",
                ("archives",),
            )

        conn.commit()
    finally:
        conn.close()