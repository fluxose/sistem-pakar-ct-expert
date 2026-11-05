
document.addEventListener("DOMContentLoaded", async () => {

    const container = document.getElementById("hasilContainer");
    const parameter = new URLSearchParams(window.location.search);
    const id = parameter.get("id");

    if (!id || !/^\d+$/.test(id)) {
        container.textContent = "ID konsultasi tidak valid.";
        return;
    }

    try {
        const response = await getDetailKonsultasi(id);

        const data = response.data;
        const pasien = data.konsultasi;
        const rincian = data.rincian;
        const rekomendasi = data.rekomendasi;

        tampilkanHasil(pasien, rincian, rekomendasi);

    } catch (error) {
        container.textContent = `Gagal memuat hasil: ${error.message}`;
    }

    function tampilkanHasil(pasien, rincian, rekomendasi) {

        const tingkat = [
            {
                kode: "cr",
                nama: "Ringan",
                nilai: pasien.cf_ringan * 100
            },
            {
                kode: "cs",
                nama: "Sedang",
                nilai: pasien.cf_sedang * 100
            },
            {
                kode: "cb",
                nama: "Berat",
                nilai: pasien.cf_berat * 100
            }
        ];

        const hasilTingkat = tingkat.map(item => `
            <div class="result-level">
                <div class="result-level-heading">
                    <strong>Reaksi ${item.nama}</strong>
                    <strong>${formatPersentase(item.nilai)}</strong>
                </div>
                <div class="progress-track">
                    <div class="progress-fill ${item.kode}"
                         style="width:${Math.min(100, Math.max(0, item.nilai))}%">
                    </div>
                </div>
            </div>
        `).join("");

        const rincianHTML = rincian.length
            ? rincian.map(item => `
                <tr>
                    <td>${escapeHTML(item.kode_gejala)}</td>
                    <td>${escapeHTML(item.nama_gejala)}</td>
                    <td>${Number(item.cf_pakar).toFixed(2)}</td>
                    <td>${Number(item.cf_user).toFixed(2)}</td>
                    <td>${Number(item.cf_gejala).toFixed(4)}</td>
                </tr>
            `).join("")
            : `<tr><td colspan="5" class="empty-cell">
                Tidak ada gejala dengan nilai keyakinan lebih dari 0.
               </td></tr>`;

        const rekomendasiHTML = rekomendasi.length
            ? rekomendasi.map(item => `
                <li>
                    ${escapeHTML(item.tindakan)}
                    <small>${escapeHTML(item.status_validasi)}</small>
                </li>
            `).join("")
            : `<li>Tidak ada rekomendasi khusus berdasarkan kesimpulan ini.</li>`;

        const adaKritis = Boolean(pasien.ada_kritis);

        container.innerHTML = `
            ${adaKritis ? `
                <div class="critical-banner">
                    <strong>PERHATIAN:</strong>
                    gejala kritis terdeteksi, segera hubungi dokter/radiolog
                </div>
            ` : ""}

            <section class="panel result-patient">
                <div class="section-heading">
                    <div>
                        <h2>Identitas Pasien</h2>
                        <p>Informasi konsultasi yang telah disimpan.</p>
                    </div>
                    <span class="step-label">ID #${pasien.id_konsultasi}</span>
                </div>

                <div class="patient-grid">
                    <div><small>Nomor RM</small><strong>${escapeHTML(pasien.no_rm)}</strong></div>
                    <div><small>Nama Pasien</small><strong>${escapeHTML(pasien.nama_pasien)}</strong></div>
                    <div><small>Usia</small><strong>${pasien.usia} tahun</strong></div>
                    <div><small>Jenis Kelamin</small><strong>${pasien.jenis_kelamin === "L" ? "Laki-laki" : "Perempuan"}</strong></div>
                    <div><small>Tanggal</small><strong>${formatTanggal(pasien.tanggal)}</strong></div>
                </div>
            </section>

            <section class="panel">
                <div class="section-heading">
                    <div>
                        <h2>Kesimpulan Sistem</h2>
                        <p>Tingkat reaksi dengan nilai CF tertinggi.</p>
                    </div>
                </div>

                <div class="conclusion-card">
                    <small>HASIL KESIMPULAN</small>
                    <h2>${escapeHTML(pasien.kesimpulan)}</h2>
                    <p>
                        ${pasien.kesimpulan === "Tidak ada reaksi terdeteksi"
                            ? "Sistem tidak menemukan nilai CF positif pada tingkat reaksi."
                            : "Sistem memilih tingkat reaksi dengan nilai CF tertinggi."}
                    </p>
                </div>

                <h3 class="subheading">Persentase Certainty Factor</h3>
                ${hasilTingkat}
            </section>

            <section class="panel">
                <div class="section-heading">
                    <div>
                        <h2>Rincian Perhitungan</h2>
                        <p>Nilai CF setiap gejala yang dipilih.</p>
                    </div>
                </div>

                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Kode</th>
                                <th>Gejala</th>
                                <th>CF Pakar</th>
                                <th>CF Pengguna</th>
                                <th>CF Gejala</th>
                            </tr>
                        </thead>
                        <tbody>${rincianHTML}</tbody>
                    </table>
                </div>

                <p class="formula-note">
                    CF Gejala = CF Pakar × CF Pengguna
                </p>
            </section>

            <section class="panel">
                <div class="section-heading">
                    <div>
                        <h2>Rekomendasi</h2>
                        <p>Tindakan berdasarkan tingkat kesimpulan sistem.</p>
                    </div>
                </div>

                <ul class="recommendation-list">
                    ${rekomendasiHTML}
                </ul>

                <div class="disclaimer">
                    Hasil sistem ini merupakan alat bantu. Keputusan akhir
                    ada pada radiolog/dokter yang berwenang.
                </div>
            </section>
        `;
    }

    // Menghindari teks dari database dibaca sebagai HTML
    function escapeHTML(value) {
        return String(value ?? "").replace(/[&<>"']/g, char => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        })[char]);
    }
});
