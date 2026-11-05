
// Alamat API backend
const API_BASE_URL = "/api";

// Fungsi umum untuk mengirim permintaan ke backend
async function apiRequest(endpoint, options = {}) {
    const config = {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        }
    };

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.message || "Terjadi kesalahan pada server."
            );
        }

        return result;

    } catch (error) {
        console.error("API Error:", error);
        throw error;
    }
}

// Mengambil daftar gejala
async function getGejala() {
    return apiRequest("/gejala");
}

// Mengambil daftar terminator
async function getTerminator() {
    return apiRequest("/terminator");
}

// Mengirim konsultasi baru
async function postKonsultasi(data) {
    return apiRequest("/konsultasi", {
        method: "POST",
        body: JSON.stringify(data)
    });
}

// Mengambil riwayat konsultasi
async function getRiwayat(keyword = "") {
    return apiRequest(
        `/konsultasi?q=${encodeURIComponent(keyword)}`
    );
}

// Mengambil detail konsultasi berdasarkan ID
async function getDetailKonsultasi(id) {
    return apiRequest(`/konsultasi/${id}`);
}

// Menambahkan gejala baru
async function tambahGejala(data) {
    return apiRequest("/gejala", {
        method: "POST",
        body: JSON.stringify(data)
    });
}

// Memperbarui gejala
async function updateGejala(kode, data) {
    return apiRequest(`/gejala/${encodeURIComponent(kode)}`, {
        method: "PUT",
        body: JSON.stringify(data)
    });
}

// Menghapus gejala
async function deleteGejala(kode) {
    return apiRequest(`/gejala/${encodeURIComponent(kode)}`, {
        method: "DELETE"
    });
}

// Format angka menjadi persentase
function formatPersentase(nilai) {
    return `${Number(nilai || 0).toFixed(2)}%`;
}

// Format tanggal ke format Indonesia
function formatTanggal(tanggal) {
    if (!tanggal) return "-";

    const bagian = tanggal.split("-");
    if (bagian.length !== 3) return tanggal;

    return `${bagian[2]}/${bagian[1]}/${bagian[0]}`;
}

// Menampilkan pesan pada halaman
function tampilkanPesan(elementId, pesan, tipe = "info") {
    const element = document.getElementById(elementId);

    if (!element) return;

    element.textContent = pesan;
    element.className = `alert alert-${tipe}`;
    element.hidden = false;
}

// Menyembunyikan pesan
function sembunyikanPesan(elementId) {
    const element = document.getElementById(elementId);

    if (element) {
        element.hidden = true;
    }
}
