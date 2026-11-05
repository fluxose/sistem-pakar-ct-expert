document.addEventListener("DOMContentLoaded", async () => {

    const form = document.getElementById("formKonsultasi");
    const daftarGejala = document.getElementById("daftarGejala");
    const tombolProses = document.getElementById("btnProses");

    let dataTerminator = [];

    // Mengisi tanggal dengan tanggal lokal perangkat
    const tanggalInput = document.getElementById("tanggal");
    const sekarang = new Date();
    const tahun = sekarang.getFullYear();
    const bulan = String(sekarang.getMonth() + 1).padStart(2, "0");
    const hari = String(sekarang.getDate()).padStart(2, "0");

    tanggalInput.value = `${tahun}-${bulan}-${hari}`;

    // Memuat data gejala dan terminator
    async function muatData() {
        try {
            const [responseGejala, responseTerminator] =
                await Promise.all([
                    getGejala(),
                    getTerminator()
                ]);

            dataTerminator = responseTerminator.data;

            tampilkanGejala(responseGejala.data);

        } catch (error) {
            daftarGejala.innerHTML =
                `<div class="alert alert-danger">
                    Gagal memuat data: ${error.message}
                </div>`;
        }
    }

    // Membuat kelompok gejala
    function tampilkanGejala(data) {
        const kelompok = [
            { kode: "cr", nama: "Reaksi Ringan" },
            { kode: "cs", nama: "Reaksi Sedang" },
            { kode: "cb", nama: "Reaksi Berat" }
        ];

        daftarGejala.innerHTML = "";

        kelompok.forEach(group => {
            const gejalaKelompok = data.filter(
                item => item.tingkat === group.kode
            );

            const section = document.createElement("div");
            section.className = `symptom-group ${group.kode}`;

            const judul = document.createElement("h3");
            judul.textContent = group.nama;
            section.appendChild(judul);

            gejalaKelompok.forEach(item => {
                const card = document.createElement("div");
                card.className = "symptom-card";

                const info = document.createElement("div");
                info.className = "symptom-info";

                const nama = document.createElement("strong");
                nama.textContent = `${item.kode_gejala} — ${item.nama_gejala}`;

                const nilai = document.createElement("small");
                nilai.textContent =
                    `CF Pakar: ${Number(item.cf_pakar).toFixed(2)}`;

                info.append(nama, nilai);

                const select = document.createElement("select");
                select.name = `gejala_${item.kode_gejala}`;
                select.dataset.kode = item.kode_gejala;

                dataTerminator.forEach(terminator => {
                    const option = document.createElement("option");

                    option.value = terminator.nilai;
                    option.textContent =
                        `${terminator.keterangan} (${Number(terminator.nilai).toFixed(1)})`;

                    // Default pengguna adalah Tidak (0)
                    if (Number(terminator.nilai) === 0) {
                        option.selected = true;
                    }

                    select.appendChild(option);
                });

                card.append(info, select);
                section.appendChild(card);
            });

            daftarGejala.appendChild(section);
        });
    }

    // Menandai gejala yang sudah dipilih (nilai lebih dari 0)
    daftarGejala.addEventListener("change", (event) => {
        const select = event.target.closest("select[data-kode]");
        if (!select) return;

        select
            .closest(".symptom-card")
            .classList.toggle("terisi", Number(select.value) > 0);
    });

    // Mengirim data konsultasi
    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        sembunyikanPesan("pesanKonsultasi");

        const gejala = {};

        document.querySelectorAll("[data-kode]").forEach(select => {
            gejala[select.dataset.kode] = Number(select.value);
        });

        const data = {
            no_rm: document.getElementById("no_rm").value.trim(),
            nama_pasien: document.getElementById("nama_pasien").value.trim(),
            usia: Number(document.getElementById("usia").value),
            jenis_kelamin: document.getElementById("jenis_kelamin").value,
            tanggal: tanggalInput.value,
            gejala: gejala
        };

        tombolProses.disabled = true;
        tombolProses.textContent = "Memproses...";

        try {
            const response = await postKonsultasi(data);

            // Membuka halaman hasil berdasarkan ID konsultasi
            window.location.href =
                `hasil.html?id=${response.data.id_konsultasi}`;

        } catch (error) {
            tampilkanPesan(
                "pesanKonsultasi",
                error.message,
                "danger"
            );

            tombolProses.disabled = false;
            tombolProses.textContent = "Proses Konsultasi →";
        }
    });

    // Reset form dan mengembalikan semua gejala ke nilai 0
    form.addEventListener("reset", () => {
        setTimeout(() => {
            document.querySelectorAll("[data-kode]").forEach(select => {
                select.value = "0";
            });

            document.querySelectorAll(".symptom-card.terisi").forEach(card => {
                card.classList.remove("terisi");
            });

            sembunyikanPesan("pesanKonsultasi");
        }, 0);
    });

    await muatData();
});