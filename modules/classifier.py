RULES={
"Kepegawaian":["pegawai","asn","pns","cpns","kenaikan pangkat","cuti","mutasi","jabatan","disiplin"],
"Keuangan":["anggaran","keuangan","spj","realisasi","pajak","pembayaran","honorarium","bendahara"],
"Pengadaan Barang/Jasa":["pengadaan","barang/jasa","kontrak","tender","penyedia","spk","pembelian"],
"Perencanaan":["rencana kerja","renja","renstra","perencanaan","program kegiatan","indikator kinerja"],
"Pelaporan":["laporan","evaluasi","monitoring","capaian","pertanggungjawaban","rekomendasi"],
"Administrasi Umum":["undangan","nota dinas","surat edaran","disposisi","rapat","korespondensi"],
"Aset dan Barang Milik Daerah":["aset","barang milik daerah","bmd","inventaris","penghapusan","mutasi barang"]}
def classify_document(text, metadata=None):
    src=((metadata or {}).get("perihal","")+" "+text).lower()
    hits={k:[w for w in v if w in src] for k,v in RULES.items()}
    best=max(hits,key=lambda k:len(hits[k]))
    n=len(hits[best])
    if not n: return {"kategori":"Perlu Review Arsiparis","confidence":0.0,"evidence":[]}
    return {"kategori":best,"confidence":round(min(.98,.55+.12*n),2),"evidence":hits[best]}
