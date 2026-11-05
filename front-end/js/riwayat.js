document.addEventListener("DOMContentLoaded", () => {

    const inputCari = document.getElementById("cariRiwayat");
    const tombolCari = document.getElementById("btnCari");
    const tabel = document.getElementById("tabelRiwayat");

    // Menentukan class lencana dari teks kesimpulan
    // cr = ringan, cs = sedang, cb = berat, none = tidak ada reaksi
    function kelasTingkat(kesimpulan) {
        const teks = String(kesimpulan ?? "").toLowerCase();

        if (teks.includes("berat")) return "cb";
        if (teks.includes("sedang")) return "cs";
        if (teks.includes("ringan")) return "cr";
        return "none";
    }

    async function muatRiwayat(keyword = "") {
        tabel.innerHTML = `
            <tr><td colspan="6" class="empty-cell">
                Memuat data...
            </td></tr>
        `;

        try {
            const response = await getRiwayat(keyword);
            const data = response.data;

            if (!data.length) {
                tabel.innerHTML = `
                    <tr><td colspan="6" class="empty-cell">
                        Tidak ada riwayat konsultasi.
                    </td></tr>
                `;
                return;
            }

            tabel.innerHTML = data.map((item, index) => `
                <tr>
                    <td>${index + 1}</td>
                    <td>${escapeHTML(item.no_rm)}</td>
                    <td>${escapeHTML(item.nama_pasien)}</td>
                    <td>${formatTanggal(item.tanggal)}</td>
                    <td>
                        <span class="result-badge ${kelasTingkat(item.kesimpulan)}">
                            ${escapeHTML(item.kesimpulan)}
                        </span>
                    </td>
                    <td>
                        <a class="table-link"
                           href="hasil.html?id=${encodeURIComponent(item.id_konsultasi)}">
                           Lihat Hasil →
                        </a>
                    </td>
                </tr>
            `).join("");

        } catch (error) {
            tabel.innerHTML = `
                <tr><td colspan="6" class="empty-cell">
                    Gagal mengambil data: ${escapeHTML(error.message)}
                </td></tr>
            `;
        }
    }

    function escapeHTML(value) {
        return String(value ?? "").replace(/[&<>"']/g, char => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        })[char]);
    }

    tombolCari.addEventListener("click", () => {
        muatRiwayat(inputCari.value.trim());
    });

    inputCari.addEventListener("keydown", event => {
        if (event.key === "Enter") {
            muatRiwayat(inputCari.value.trim());
        }
    });

    muatRiwayat();
});