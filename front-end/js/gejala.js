
document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("formGejala");
    const tabel = document.getElementById("tabelGejala");
    const inputKode = document.getElementById("kode_gejala");
    const tombolSimpan = document.getElementById("btnSimpanGejala");
    const tombolBatal = document.getElementById("btnBatalEdit");
    const judul = document.getElementById("judulFormGejala");

    let kodeSedangDiedit = null;

    async function muatGejala() {
        tabel.innerHTML = `
            <tr><td colspan="6" class="empty-cell">Memuat data...</td></tr>
        `;

        try {
            const response = await getGejala();

            tabel.innerHTML = response.data.map(item => `
                <tr>
                    <td>${escapeHTML(item.kode_gejala)}</td>
                    <td>${escapeHTML(item.nama_gejala)}</td>
                    <td>${namaTingkat(item.tingkat)}</td>
                    <td>${Number(item.cf_pakar).toFixed(2)}</td>
                    <td>
                        ${item.kritis
                            ? '<span class="critical-label">Kritis</span>'
                            : "Tidak"}
                    </td>
                    <td>
                        <div class="table-actions">
                            <button class="btn-small btn-edit"
                                data-action="edit"
                                data-kode="${escapeHTML(item.kode_gejala)}">
                                Edit
                            </button>
                            <button class="btn-small btn-delete"
                                data-action="delete"
                                data-kode="${escapeHTML(item.kode_gejala)}">
                                Hapus
                            </button>
                        </div>
                    </td>
                </tr>
            `).join("") || `
                <tr><td colspan="6" class="empty-cell">
                    Belum ada data gejala.
                </td></tr>
            `;

            // Simpan data untuk proses edit
            window.dataGejala = response.data;

        } catch (error) {
            tabel.innerHTML = `
                <tr><td colspan="6" class="empty-cell">
                    ${escapeHTML(error.message)}
                </td></tr>
            `;
        }
    }

    function namaTingkat(tingkat) {
        return {
            cr: "Ringan",
            cs: "Sedang",
            cb: "Berat"
        }[tingkat] || tingkat;
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

    function resetForm() {
        form.reset();
        kodeSedangDiedit = null;

        inputKode.disabled = false;
        judul.textContent = "Tambah Gejala";
        tombolSimpan.textContent = "Simpan Gejala";
        tombolBatal.hidden = true;

        sembunyikanPesan("pesanGejala");
    }

    // Tambah atau ubah data gejala
    form.addEventListener("submit", async event => {
        event.preventDefault();

        const data = {
            nama_gejala: document.getElementById("nama_gejala").value.trim(),
            tingkat: document.getElementById("tingkat").value,
            cf_pakar: Number(document.getElementById("cf_pakar").value),
            kritis: document.getElementById("kritis").value === "true"
        };

        try {
            if (kodeSedangDiedit) {
                await updateGejala(kodeSedangDiedit, data);

                tampilkanPesan(
                    "pesanGejala",
                    "Gejala berhasil diperbarui.",
                    "success"
                );
            } else {
                data.kode_gejala = inputKode.value.trim().toUpperCase();

                await tambahGejala(data);

                tampilkanPesan(
                    "pesanGejala",
                    "Gejala berhasil ditambahkan.",
                    "success"
                );
            }

            resetForm();
            await muatGejala();

        } catch (error) {
            tampilkanPesan("pesanGejala", error.message, "danger");
        }
    });

    // Mengatur aksi edit dan hapus
    tabel.addEventListener("click", async event => {
        const tombol = event.target.closest("button[data-action]");

        if (!tombol) return;

        const kode = tombol.dataset.kode;
        const aksi = tombol.dataset.action;

        if (aksi === "edit") {
            const item = window.dataGejala.find(
                data => data.kode_gejala === kode
            );

            if (!item) return;

            kodeSedangDiedit = kode;

            inputKode.value = item.kode_gejala;
            inputKode.disabled = true;

            document.getElementById("nama_gejala").value =
                item.nama_gejala;

            document.getElementById("tingkat").value =
                item.tingkat;

            document.getElementById("cf_pakar").value =
                item.cf_pakar;

            document.getElementById("kritis").value =
                String(item.kritis);

            judul.textContent = `Edit Gejala ${kode}`;
            tombolSimpan.textContent = "Perbarui Gejala";
            tombolBatal.hidden = false;

            window.scrollTo({ top: 0, behavior: "smooth" });
        }

        if (aksi === "delete") {
            const setuju = confirm(
                `Apakah kamu yakin ingin menghapus gejala ${kode}?`
            );

            if (!setuju) return;

            try {
                await deleteGejala(kode);
                await muatGejala();

                tampilkanPesan(
                    "pesanGejala",
                    "Gejala berhasil dihapus.",
                    "success"
                );

            } catch (error) {
                tampilkanPesan(
                    "pesanGejala",
                    error.message,
                    "danger"
                );
            }
        }
    });

    tombolBatal.addEventListener("click", resetForm);

    muatGejala();
});
