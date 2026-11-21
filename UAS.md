[**(←) Back**](README.md)

# **PROJECT — Implementasi Dual-WAN Load Balancing, VLAN, dan Web Server AlmaLinux**

**Nama** : M. Syaiful Karomah  
**NIM** : 09011282328111  
**Kelas** : SK7C  
**Mata Kuliah** : Manajemen Pusat Data

---

## Informasi Sistem

| Parameter | Nilai |
| --- | --- |
| Router | MikroTik RouterOS 7 |
| Koneksi Internet | 2 ISP (Dual-WAN): ISP 1 via kabel LAN/Ethernet, ISP 2 via wireless (Wi-Fi) |
| Metode Pengelolaan WAN | Load Balancing (PCC) dan Failover (Netwatch) |
| Segmentasi Jaringan | VLAN 10 dan VLAN 20 |
| Platform Virtualisasi | VMware Workstation + Proxmox VE |
| Host Server 1 | Laptop 1 |
| Host Server 2 | Laptop 2 |
| Sistem Operasi Server | AlmaLinux |
| Web Server | Apache HTTP Server (`httpd`) |
| Publikasi Web | Cloudflare Tunnel atau Port Forwarding |
| Jaringan Server 1 | VLAN 10 |
| Jaringan Server 2 | VLAN 20 |

> **Catatan:** proyek ini menggunakan satu perangkat MikroTik untuk mengatur koneksi dua ISP, routing, firewall, NAT, dan VLAN. Managed switch tidak digunakan. Port Ethernet MikroTik langsung dihubungkan ke masing-masing laptop. Nama interface, alamat IP, subnet, serta nomor port pada dokumen ini adalah **contoh** dan harus disesuaikan dengan perangkat yang digunakan.

---

## Tujuan Project

Project ini membangun infrastruktur jaringan menggunakan satu router MikroTik yang mengelola dua koneksi internet (dual-WAN), melakukan load balancing dan failover, serta memisahkan dua jaringan server menggunakan VLAN.

Dua server AlmaLinux dijalankan pada dua laptop fisik yang berbeda. Masing-masing laptop menjalankan VMware Workstation, kemudian di dalamnya terdapat Proxmox VE sebagai platform virtualisasi dan AlmaLinux sebagai server aplikasi.

MikroTik bertindak sebagai pusat pengelolaan lalu lintas jaringan. Selain mengatur koneksi ISP 1 (kabel LAN) dan ISP 2 (wireless), MikroTik juga menangani segmentasi VLAN 10 dan VLAN 20 sehingga kedua server berada pada jaringan yang berbeda.

Setiap AlmaLinux menjalankan web server secara mandiri. Layanan web kemudian dipublikasikan agar dapat diakses dari jaringan internet menggunakan metode yang sesuai.

Komponen utama:

- **MikroTik RouterOS 7** — mengelola dua ISP, load balancing, failover, routing, NAT, firewall, dan VLAN.
- **VMware Workstation** — menjalankan Proxmox VE pada masing-masing laptop.
- **Proxmox VE** — mengelola virtual machine AlmaLinux.
- **AlmaLinux Server 1 dan 2** — menjalankan layanan web.
- **Apache HTTP Server** — menyediakan layanan HTTP.
- **Cloudflare Tunnel / Port Forwarding** — menyediakan akses dari internet menuju layanan web.

---

## Topologi Sistem

<img width="1680" height="1560" alt="topologi-dual-wan-vlan-almalinux" src="images/topologi-dual-wan-vlan-almalinux.png" />

**Catatan arsitektur:** managed switch tidak diperlukan apabila jumlah port Ethernet MikroTik mencukupi. Port MikroTik dapat dikonfigurasi langsung sebagai access port untuk masing-masing VLAN. Pada rancangan ini, port menuju Laptop 1 menjadi access VLAN 10 dan port menuju Laptop 2 menjadi access VLAN 20. MikroTik sekaligus menjadi gateway kedua VLAN dan pengatur lalu lintas antarjaringan.

Topologi konseptual:

```text
      ISP 1 (Kabel LAN)             ISP 2 (Wireless)
            |  ether1                     :  wifi1 (station)
            +-------------+---------------+
                          |
                   MikroTik Router
              Dual-WAN / Load Balancing
                    /           \
             VLAN 10           VLAN 20
             Port LAN 1        Port LAN 2
                 |                 |
              Laptop 1          Laptop 2
                 |                 |
          VMware Workstation VMware Workstation
                 |                 |
              Proxmox           Proxmox
                 |                 |
            AlmaLinux 1       AlmaLinux 2
            Web Server        Web Server
```

> **Catatan:** topologi ini menggunakan port access/untagged pada sisi laptop. Dengan demikian, MikroTik yang memberi identitas VLAN berdasarkan port fisik. Proxmox tidak perlu menambahkan VLAN tag pada NIC VM selama bridge Proxmox meneruskan frame untagged dari adapter Bridged VMware.

---

## Urutan Pengerjaan (Ringkasan)

Kerjakan sesuai urutan berikut agar tidak kehilangan akses ke perangkat:

1. **Bagian A–B** — siapkan jalur jaringan di laptop (VMware → Proxmox → AlmaLinux).
2. **Bagian C** — periksa dan catat kondisi MikroTik, lalu **backup** konfigurasi.
3. **Bagian D** — buat VLAN di MikroTik dan hubungkan laptop.
4. **Bagian E** — konfigurasi dual-WAN, PCC, failover, NAT, dan firewall.
5. **Bagian F** — atur IP dan hostname AlmaLinux.
6. **Bagian G** — pasang Apache dan halaman uji.
7. **Bagian H** — publikasikan web (Port Forwarding / Cloudflare Tunnel).
8. **Bagian I–J** — uji seluruh skenario dan analisis hasil.

---

# A. Persiapan Network Adapter pada VMware Workstation

> Bagian ini dilakukan pada kedua laptop. Prosedur penambahan adapter sama, sedangkan port fisik yang digunakan akan terhubung ke VLAN yang berbeda pada MikroTik.

**Tujuan bagian ini:** VM Proxmox harus memiliki dua jalur jaringan. Jalur pertama (NAT) untuk mengakses Web GUI Proxmox dari Windows. Jalur kedua (Bridged) untuk meneruskan lalu lintas server langsung ke kabel Ethernet laptop menuju MikroTik.

```text
AlmaLinux ── vmbr1 ── ens34 (Proxmox) ── Adapter 2 (Bridged) ── VMnet0 ── Ethernet laptop ── MikroTik
Windows ──── VMnet8 (NAT) ── Adapter 1 ── vmbr0 (Proxmox, IP manajemen)
```

## A.1 Memeriksa Network Adapter Proxmox

1. Matikan VM Proxmox secara normal (`Power > Shut Down Guest`). Pengubahan hardware sebaiknya tidak dilakukan saat VM menyala.
2. Pilih VM Proxmox pada daftar VMware Workstation.
3. Buka menu:

   ```
   VM > Settings
   ```

4. Pada tab **Hardware**, klik **Network Adapter** (adapter pertama).
5. Pastikan mode yang dipilih adalah **NAT: Used to share the host's IP address**. Adapter ini dipertahankan untuk koneksi manajemen Proxmox (Web GUI `https://<ip-proxmox>:8006`) melalui jaringan virtual VMware.
6. Jangan mengubah adapter pertama agar IP manajemen Proxmox tidak berubah.

<img width="640" height="420" alt="Pengaturan Network Adapter NAT pada VMware" src="images/A.1-vmware-adapter-nat.png" />

> **Tips sekaligus pemeriksaan nested virtualization:** pada **Settings > Processors**, centang **Virtualize Intel VT-x/EPT or AMD-V/RVI** agar VM AlmaLinux dapat berjalan di dalam Proxmox yang berjalan di dalam VMware.

## A.2 Menambahkan Network Adapter Kedua

1. Masih pada jendela **Virtual Machine Settings**, klik **Add...**
2. Pilih **Network Adapter**, lalu klik **Next/Finish**.
3. Pada adapter baru, pilih mode:

   ```
   Bridged: Connected directly to the physical network
   ```

4. Jangan centang *Replicate physical network connection state* kecuali diperlukan (opsi ini membuat IP berubah saat berpindah jaringan; tidak dibutuhkan pada Ethernet tetap).
5. Aktifkan pada bagian **Device status**:
   - `Connected`
   - `Connect at power on`
6. Klik **OK** untuk menyimpan.

Adapter Bridged digunakan untuk meneruskan koneksi dari Proxmox menuju Ethernet fisik laptop, kemudian menuju port VLAN pada MikroTik.

<img width="640" height="420" alt="Penambahan Network Adapter kedua" src="images/A.2-vmware-add-adapter.png" />

## A.3 Memastikan VMware Bridged ke Ethernet Fisik

Secara default mode *Automatic* pada VMnet0 dapat memilih adapter yang salah (misalnya Wi-Fi atau adapter VPN). Karena itu pilih adapter secara manual.

1. Pada VMware Workstation buka:

   ```
   Edit > Virtual Network Editor
   ```

2. Klik tombol **Change Settings** di kiri bawah (perlu hak Administrator Windows).
3. Pilih baris **VMnet0** (tipe *Bridged*).
4. Pada **Bridged to**, ganti dari *Automatic* menjadi adapter **Ethernet fisik** laptop (contoh: `Realtek PCIe GbE Family Controller`). Nama adapter dapat dilihat pada `Control Panel > Network Connections` atau `ipconfig /all`.
5. Klik **Apply**, lalu **OK**.
6. Pastikan kabel Ethernet laptop sudah tertancap ke port MikroTik yang direncanakan, atau minimal adapter berstatus *Connected*.

Hindari memilih adapter Wi-Fi atau adapter virtual lain apabila rancangan pengujian menggunakan Ethernet.

<img width="640" height="420" alt="VMnet0 diarahkan ke Ethernet fisik" src="images/A.3-vmnet0-ethernet.png" />

> **Catatan:** Windows pada laptop juga dapat memperoleh IP VLAN melalui adapter Ethernet yang sama. Hal ini normal. Jika Windows memakai Wi-Fi untuk internet, pastikan tidak ada konflik rute (metric) antara Wi-Fi dan Ethernet.

## A.4 Mengulangi Konfigurasi pada Laptop Kedua

Lakukan langkah A.1 sampai A.3 pada laptop kedua. Kedua laptop menggunakan dua adapter dengan fungsi yang sama:

| Adapter | Mode | Fungsi |
| --- | --- | --- |
| Network Adapter 1 | NAT | Koneksi manajemen Proxmox |
| Network Adapter 2 | Bridged | Jalur jaringan server menuju MikroTik |

Setelah selesai, nyalakan kembali VM Proxmox pada kedua laptop.

<img width="640" height="420" alt="Konfigurasi adapter VMware pada laptop kedua" src="images/A.4-vmware-laptop2.png" />

---

# B. Pemeriksaan dan Konfigurasi Bridge pada Proxmox

> Bagian ini dilakukan pada masing-masing Proxmox. Jangan mengubah bridge NAT (`vmbr0`) yang sedang digunakan untuk mengakses Web GUI Proxmox.

## B.1 Memeriksa Network Interface

1. Login ke Web GUI Proxmox (`https://<ip-proxmox>:8006`) lalu buka **Node > Shell**, atau login langsung ke console VM Proxmox sebagai `root`.
2. Jalankan:

   ```
   ip -br link
   ip -br addr
   ```

3. Baca hasilnya:
   - `ens33` (contoh) — adapter pertama (NAT), biasanya menjadi port `vmbr0`.
   - `ens34` (contoh) — adapter kedua (Bridged), belum memiliki IP dan belum menjadi anggota bridge.
   - `vmbr0` — bridge yang memegang IP manajemen Proxmox.

Identifikasi:

- Interface pertama yang terhubung ke NAT VMware.
- Interface kedua yang terhubung ke mode Bridged.
- Bridge utama yang digunakan untuk manajemen Proxmox.
- Bridge tambahan yang akan digunakan oleh AlmaLinux.

Nama interface dapat berbeda pada setiap instalasi. Pada konfigurasi yang diperiksa sebelumnya, adapter kedua terdeteksi sebagai `ens34`, tetapi nama aktual tetap harus diperiksa pada masing-masing host. Jika adapter kedua tidak muncul, matikan VM dan periksa kembali langkah A.2.

<img width="720" height="360" alt="Pemeriksaan interface Proxmox" src="images/B.1-proxmox-ip-link.png" />

## B.2 Memeriksa dan Membuat Bridge Tambahan

1. Lihat konfigurasi saat ini:

   ```
   cat /etc/network/interfaces
   ```

2. Pastikan bridge NAT (`vmbr0`) tetap dipertahankan dan tidak diedit. Periksa apakah bridge tambahan sudah ada dan apakah sedang dipakai VM lain.
3. Buat bridge baru `vmbr1` untuk adapter kedua. Ada dua cara.

**Cara 1 — Melalui Web GUI (lebih aman):**

1. Pilih node Proxmox > **System > Network**.
2. Klik **Create > Linux Bridge**.
3. Isi: **Name** = `vmbr1`, **IPv4/CIDR** = *kosong*, **Gateway** = *kosong*, **Bridge ports** = `ens34`.
4. Klik **Create**, kemudian klik **Apply Configuration**.

**Cara 2 — Melalui file konfigurasi:**

1. Cadangkan file terlebih dahulu:

   ```
   cp /etc/network/interfaces /etc/network/interfaces.bak
   ```

2. Edit file:

   ```
   nano /etc/network/interfaces
   ```

3. Tambahkan di bagian bawah file (tanpa menyentuh `vmbr0`):

   ```
   auto ens34
   iface ens34 inet manual

   auto vmbr1
   iface vmbr1 inet manual
       bridge-ports ens34
       bridge-stp off
       bridge-fd 0
   ```

4. Terapkan tanpa reboot (Proxmox 7/8 menggunakan `ifupdown2`):

   ```
   ifreload -a
   ```

> **Catatan:** konfigurasi di atas merupakan contoh. Sesuaikan nama interface dan bridge berdasarkan hasil pemeriksaan. Jangan menimpa konfigurasi `vmbr0` yang sudah memiliki IP manajemen. Bridge `vmbr1` sengaja **tidak diberi IP** karena hanya berfungsi sebagai "kabel virtual" antara AlmaLinux dan MikroTik.

<img width="720" height="360" alt="Konfigurasi network interfaces Proxmox" src="images/B.2-proxmox-interfaces.png" />

## B.3 Memastikan Bridge Terhubung ke Adapter Bridged

Setelah konfigurasi diterapkan, verifikasi:

```
ip -br link
bridge link
```

Hasil yang diharapkan:

- `vmbr1` berstatus `UP`.
- Pada `bridge link` terlihat `ens34` sebagai anggota (`master vmbr1`) dengan state `forwarding`.

Jika interface masih berstatus `DOWN`:

1. Periksa pengaturan adapter VMware (Connected / Connect at power on).
2. Periksa pilihan adapter Ethernet pada VMnet0 (A.3).
3. Periksa kabel Ethernet laptop ke MikroTik.

<img width="720" height="360" alt="Pemeriksaan bridge Proxmox" src="images/B.3-proxmox-bridge.png" />

## B.4 Menghubungkan Network Device AlmaLinux ke Bridge

1. Buka Web GUI Proxmox, pilih VM AlmaLinux pada panel kiri.
2. Masuk ke:

   ```
   Hardware > Network Device
   ```

3. Jika NIC server belum ada, klik **Add > Network Device**. Jika sudah ada, pilih lalu klik **Edit**.
4. Isi:
   - **Bridge**: `vmbr1`
   - **Model**: `VirtIO (paravirtualized)`
   - **VLAN Tag**: *kosong* (VLAN ditangani oleh port access MikroTik)
   - **Firewall**: tidak dicentang
5. Klik **Add/OK**. Nyalakan ulang VM bila diperlukan.

NIC lain (misalnya yang terhubung ke `vmbr0`/NAT) tidak perlu dihapus, tetapi agar tidak terjadi konflik default gateway, NIC tersebut tidak boleh dijadikan jalur internet server (lihat F.3).

<img width="720" height="420" alt="Network Device AlmaLinux pada Proxmox" src="images/B.4-proxmox-vm-network.png" />

## B.5 Mengulangi Konfigurasi pada Proxmox Laptop Kedua

Ulangi B.1 sampai B.4 pada Proxmox laptop kedua. Pastikan adapter Bridged terhubung ke bridge yang digunakan oleh AlmaLinux kedua.

<img width="720" height="360" alt="Bridge Proxmox laptop kedua" src="images/B.5-proxmox-laptop2.png" />

---

# C. Persiapan dan Identifikasi Interface MikroTik

> Bagian ini dilakukan pada satu router MikroTik. MikroTik menjadi pusat pengaturan koneksi ISP, VLAN, routing, NAT, dan firewall.

## C.1 Mengidentifikasi Port MikroTik

1. Hubungkan komputer admin ke MikroTik (WinBox: gunakan tab **Neighbors** dan hubungkan via MAC address bila IP belum diketahui; atau gunakan terminal SSH/Telnet/console).
2. Periksa jenis dan versi perangkat:

   ```
   /system resource print
   /system routerboard print
   ```

   Pastikan `version` RouterOS adalah 7.x.
3. Lihat seluruh interface:

   ```
   /interface print
   /interface ethernet print
   ```

4. Cadangkan konfigurasi sebelum mengubah apa pun:

   ```
   /system backup save name=backup-sebelum-project
   /export file=export-sebelum-project
   ```

   Unduh kedua file dari menu **Files** pada WinBox. Jika terjadi kesalahan, router dapat dipulihkan dari backup ini.
5. Tentukan pemetaan port.

Contoh pemetaan port (sesuaikan dengan perangkat aktual):

| Fungsi | Interface contoh |
| --- | --- |
| ISP 1 (kabel LAN) | `ether1` |
| ISP 2 (wireless) | `wifi1` (atau `wlan1` pada paket wireless lama) |
| Laptop 1 — VLAN 10 | `ether3` |
| Laptop 2 — VLAN 20 | `ether4` |

ISP 2 menggunakan **interface wireless MikroTik** yang bekerja sebagai *station* (client) dan terhubung ke SSID ISP. Interface wireless **tidak boleh dimasukkan ke bridge** VLAN. Jika MikroTik tidak memiliki Wi-Fi bawaan, gunakan perangkat perantara (travel router/repeater/access point mode client) yang terhubung ke Wi-Fi ISP, kemudian hubungkan perangkat itu dengan kabel ke `ether2`. Pada kasus ini, ganti `wifi1` menjadi `ether2` pada seluruh konfigurasi di dokumen ini.

Port yang digunakan harus dipastikan melalui pemeriksaan perangkat. Jangan langsung mengasumsikan bahwa semua model MikroTik memiliki jumlah port dan susunan yang sama. Jika MikroTik memiliki port tambahan (misalnya `ether5`), sebaiknya dibiarkan bebas sebagai port cadangan akses manajemen.

<img width="720" height="420" alt="Daftar interface MikroTik" src="images/C.1-mikrotik-interface.png" />

## C.2 Mengidentifikasi Koneksi ISP

Catat metode koneksi masing-masing ISP, misalnya DHCP Client, IP statis, atau PPPoE.

1. Hubungkan kabel ISP 1 ke `ether1`. ISP 2 (wireless) disambungkan melalui interface `wifi1` pada langkah E.1 (Wi-Fi tidak memerlukan kabel); catat nama SSID dan password ISP 2.
2. Periksa apakah router sudah menerima IP:

   ```
   /ip dhcp-client print detail
   /ip address print
   /ip route print
   ```

3. Jika konfigurasi bawaan (default) MikroTik masih aktif, sudah ada DHCP client pada `ether1` dan bridge `bridge` berisi `ether2–ether5` dan `wifi1` dengan IP `192.168.88.1/24`. Konfigurasi bawaan ini akan bentrok dengan rancangan project, sehingga **perlu dihapus** (lihat D.2 langkah awal).
4. Catat hasil pada tabel berikut:

| Parameter | ISP 1 | ISP 2 |
| --- | --- | --- |
| Interface | `ether1` (kabel) | `wifi1` (wireless station) |
| Metode koneksi | DHCP/Static/PPPoE | Wi-Fi (SSID + password) lalu DHCP/Static |
| IP Address | Catat aktual | Catat aktual |
| Gateway | Catat aktual | Catat aktual |
| Status | Catat hasil | Catat hasil |
| SSID / sinyal (dBm) | — | Catat aktual |

> **Penting:** jika kedua ISP berupa modem/router rumahan atau hotspot dan sama-sama memakai subnet `192.168.1.0/24`, kedua WAN akan bentrok. Ubah subnet LAN salah satu modem (misalnya ISP 2 menjadi `192.168.2.0/24`). Subnet WAN juga tidak boleh sama dengan `192.168.10.0/24` maupun `192.168.20.0/24`.

<img width="720" height="420" alt="Status koneksi dua ISP pada MikroTik" src="images/C.2-mikrotik-dual-wan.png" />

## C.3 Menentukan Rencana VLAN

Dua jaringan server dipisahkan menggunakan VLAN:

| Nama VLAN | VLAN ID | Subnet contoh | Perangkat |
| --- | ---: | --- | --- |
| SERVER-1 | 10 | `192.168.10.0/24` | Laptop 1 / AlmaLinux 1 |
| SERVER-2 | 20 | `192.168.20.0/24` | Laptop 2 / AlmaLinux 2 |

Contoh alamat gateway dan server:

| Perangkat | VLAN | IP Address contoh |
| --- | ---: | --- |
| Gateway VLAN 10 | 10 | `192.168.10.1/24` |
| AlmaLinux 1 | 10 | `192.168.10.10/24` |
| Gateway VLAN 20 | 20 | `192.168.20.1/24` |
| AlmaLinux 2 | 20 | `192.168.20.10/24` |

Alamat di atas merupakan rancangan contoh. Pastikan subnet tidak bertabrakan dengan jaringan NAT VMware (biasanya `192.168.x.0/24` acak, cek via `Virtual Network Editor > VMnet8`) maupun jaringan lain yang digunakan.

<img width="720" height="360" alt="Rencana VLAN dan IP Address" src="images/C.3-vlan-ip-plan.png" />

---

# D. Konfigurasi VLAN pada MikroTik

## D.1 Konsep VLAN Tanpa Managed Switch

Karena hanya menggunakan satu router MikroTik, fungsi pemisahan VLAN dapat dilakukan langsung oleh MikroTik selama perangkat mendukung VLAN-aware bridge dan memiliki port Ethernet yang mencukupi.

Rancangan port:

| Port MikroTik | Mode | VLAN | Perangkat |
| --- | --- | ---: | --- |
| Port menuju Laptop 1 (`ether3`) | Access/Untagged | 10 | Proxmox dan AlmaLinux 1 |
| Port menuju Laptop 2 (`ether4`) | Access/Untagged | 20 | Proxmox dan AlmaLinux 2 |

Dengan konfigurasi access port, laptop menerima frame Ethernet tanpa tag VLAN. MikroTik menentukan VLAN berdasarkan **PVID** pada port yang terhubung ke masing-masing laptop: frame yang masuk dari `ether3` otomatis diberi tag 10, dan frame dari `ether4` diberi tag 20. Saat keluar menuju laptop, tag dilepas kembali.

Tidak diperlukan managed switch terpisah pada rancangan ini.

<img width="720" height="420" alt="Pemetaan port access VLAN MikroTik" src="images/D.1-mikrotik-vlan-port.png" />

## D.2 Membuat Bridge VLAN pada MikroTik

Konfigurasi VLAN pada RouterOS 7 menggunakan bridge dengan `vlan-filtering`. Kesalahan konfigurasi dapat memutus akses manajemen router, sehingga lakukan langkah berikut secara berurutan.

**Langkah 0 — Persiapan keamanan akses:**

1. Aktifkan **Safe Mode**: pada WinBox klik tombol *Safe Mode* di kiri atas, atau pada terminal tekan `Ctrl+X`. Jika koneksi terputus, perubahan akan dibatalkan otomatis.
2. Jika menghubungkan diri melalui salah satu port yang nanti menjadi port VLAN, ingat bahwa alamat IP admin akan berubah. Alternatif aman: terhubung melalui WinBox menggunakan **MAC address**, atau gunakan port cadangan (misalnya `ether5`) yang tidak dimasukkan ke bridge.

**Langkah 1 — Hapus konfigurasi bawaan yang bentrok** (hanya jika konfigurasi default masih ada; periksa dulu dengan `/interface bridge print` dan `/ip address print`):

```
/ip dhcp-server remove [find]
/ip pool remove [find]
/ip address remove [find where interface=bridge]
/interface bridge port remove [find]
/interface bridge remove [find]
```

> Perintah `remove [find]` menghapus semua entri pada tabel tersebut. Jika router sudah digunakan untuk keperluan lain, hapus entri satu per satu.

**Langkah 2 — Buat bridge (VLAN filtering masih mati):**

```
/interface bridge add name=bridge-lan vlan-filtering=no
```

**Langkah 3 — Masukkan port laptop sebagai access port dengan PVID:**

```
/interface bridge port
add bridge=bridge-lan interface=ether3 pvid=10 frame-types=admit-only-untagged-and-priority-tagged comment="Laptop 1 - VLAN 10"
add bridge=bridge-lan interface=ether4 pvid=20 frame-types=admit-only-untagged-and-priority-tagged comment="Laptop 2 - VLAN 20"
```

`frame-types=admit-only-untagged-and-priority-tagged` memastikan port hanya menerima frame tanpa tag (sesuai perilaku access port).

**Langkah 4 — Daftarkan VLAN pada Bridge VLAN Table:**

```
/interface bridge vlan
add bridge=bridge-lan vlan-ids=10 tagged=bridge-lan untagged=ether3
add bridge=bridge-lan vlan-ids=20 tagged=bridge-lan untagged=ether4
```

- `tagged=bridge-lan` berarti interface bridge (CPU router) ikut menerima VLAN tersebut sehingga router dapat menjadi gateway.
- `untagged=etherX` berarti frame keluar ke port itu dilepas tag-nya.

**Langkah 5 — Buat interface VLAN pada bridge:**

```
/interface vlan
add name=vlan10-server1 interface=bridge-lan vlan-id=10
add name=vlan20-server2 interface=bridge-lan vlan-id=20
```

**Langkah 6 — Aktifkan VLAN filtering (langkah terakhir):**

```
/interface bridge set bridge-lan vlan-filtering=yes
```

Jika Safe Mode aktif dan koneksi tetap normal, tekan `Ctrl+X` lagi (atau klik *Safe Mode*) untuk menyimpan perubahan.

**Langkah 7 — Verifikasi:**

```
/interface bridge port print
/interface bridge vlan print
```

Pastikan `ether3` memiliki `PVID 10` dan `ether4` memiliki `PVID 20`.

Rancangan logis:

- Port menuju Laptop 1 menjadi anggota VLAN 10.
- Port menuju Laptop 2 menjadi anggota VLAN 20.
- Interface bridge menjadi jalur Layer 3 router untuk kedua VLAN apabila router menjadi gateway.
- VLAN 10 dan VLAN 20 tidak dicampur sebagai satu jaringan Layer 2.

<img width="720" height="420" alt="Konfigurasi bridge VLAN filtering MikroTik" src="images/D.2-mikrotik-bridge-vlan.png" />

## D.3 Menentukan Gateway Setiap VLAN

MikroTik menjadi default gateway untuk kedua jaringan server.

| VLAN | Gateway |
| ---: | --- |
| 10 | `192.168.10.1/24` |
| 20 | `192.168.20.1/24` |

**Langkah-langkah:**

1. Beri IP pada interface VLAN (bukan pada port fisik):

   ```
   /ip address
   add address=192.168.10.1/24 interface=vlan10-server1 comment="Gateway VLAN 10"
   add address=192.168.20.1/24 interface=vlan20-server2 comment="Gateway VLAN 20"
   ```

2. Aktifkan DNS resolver router agar server dapat memakai MikroTik sebagai DNS:

   ```
   /ip dns set allow-remote-requests=yes servers=1.1.1.1,8.8.8.8
   ```

3. (Opsional) Aktifkan DHCP Server per VLAN. Server AlmaLinux memakai IP statis `.10`, sehingga rentang DHCP dibuat di luar `.10` (misalnya `.100–.200`) untuk perangkat lain:

   ```
   /ip pool
   add name=pool-vlan10 ranges=192.168.10.100-192.168.10.200
   add name=pool-vlan20 ranges=192.168.20.100-192.168.20.200

   /ip dhcp-server
   add name=dhcp-vlan10 interface=vlan10-server1 address-pool=pool-vlan10 lease-time=1d disabled=no
   add name=dhcp-vlan20 interface=vlan20-server2 address-pool=pool-vlan20 lease-time=1d disabled=no

   /ip dhcp-server network
   add address=192.168.10.0/24 gateway=192.168.10.1 dns-server=192.168.10.1
   add address=192.168.20.0/24 gateway=192.168.20.1 dns-server=192.168.20.1
   ```

4. Buat daftar interface (*interface list*) untuk mempermudah aturan firewall. Daftar `WAN` dan `LAN` ini dipakai pada bagian D.4 dan E:

   ```
   /interface list
   add name=WAN
   add name=LAN

   /interface list member
   add list=WAN interface=ether1
   add list=WAN interface=wifi1
   add list=LAN interface=vlan10-server1
   add list=LAN interface=vlan20-server2
   ```

Pastikan DHCP Server hanya melayani subnet VLAN yang benar.

<img width="720" height="420" alt="Gateway VLAN pada MikroTik" src="images/D.3-mikrotik-vlan-gateway.png" />

## D.4 Membatasi Komunikasi Antar-VLAN

VLAN memisahkan broadcast domain, tetapi tidak otomatis memblokir komunikasi Layer 3 antar-VLAN karena router tetap dapat meneruskan paket antara `192.168.10.0/24` dan `192.168.20.0/24`.

Buat kebijakan firewall sesuai kebutuhan:

- Izinkan koneksi dari masing-masing server menuju internet.
- Izinkan akses administrasi dari sumber yang ditentukan.
- Tolak komunikasi antar-VLAN yang tidak diperlukan.
- Izinkan layanan tertentu antar-VLAN hanya jika memang dibutuhkan.

**Aturan chain `forward`** (urutan penting; aturan dibaca dari atas ke bawah):

```
/ip firewall filter
add chain=forward action=accept connection-state=established,related,untracked comment="Izinkan koneksi yang sudah berjalan"
add chain=forward action=drop connection-state=invalid comment="Buang paket invalid"
add chain=forward action=accept connection-nat-state=dstnat comment="Izinkan trafik hasil port forwarding"
add chain=forward action=drop in-interface=vlan10-server1 out-interface=vlan20-server2 comment="Blokir VLAN10 -> VLAN20"
add chain=forward action=drop in-interface=vlan20-server2 out-interface=vlan10-server1 comment="Blokir VLAN20 -> VLAN10"
add chain=forward action=accept in-interface-list=LAN out-interface-list=WAN comment="Izinkan LAN -> Internet"
add chain=forward action=drop comment="Buang sisanya"
```

**Aturan chain `input`** (melindungi router itu sendiri). Tambahkan **setelah** seluruh akses manajemen dipastikan berjalan, karena aturan `drop` terakhir dapat memutus akses WinBox dari port yang bukan anggota daftar `LAN`:

```
/ip firewall filter
add chain=input action=accept connection-state=established,related,untracked comment="Izinkan koneksi yang sudah berjalan"
add chain=input action=drop connection-state=invalid comment="Buang paket invalid"
add chain=input action=accept protocol=icmp comment="Izinkan ping"
add chain=input action=accept in-interface-list=LAN comment="Izinkan akses dari LAN"
add chain=input action=drop in-interface-list=WAN comment="Blokir akses ke router dari WAN"
```

Aturan `forward` dan `input` sebaiknya ditempatkan berurutan sesuai chain masing-masing. Jangan mengaktifkan aturan **FastTrack** bawaan karena FastTrack melewati proses mangle dan dapat merusak PCC pada bagian E.

**Verifikasi:** dari AlmaLinux 1 (setelah F selesai) jalankan `ping -c 3 192.168.20.10`. Hasil yang diharapkan adalah **gagal (100% packet loss)**.

<img width="720" height="420" alt="Firewall antar VLAN pada MikroTik" src="images/D.4-mikrotik-intervlan-firewall.png" />

## D.5 Mengulangi Pengujian pada Kedua Laptop

Setelah port access VLAN dikonfigurasi, hubungkan masing-masing laptop ke port yang telah ditentukan.

1. Colokkan kabel Laptop 1 ke `ether3` dan Laptop 2 ke `ether4`.
2. Pada MikroTik, periksa link aktif:

   ```
   /interface ethernet monitor ether3,ether4 once
   ```

   Status `link-ok` menandakan kabel terhubung.
3. Pada Windows laptop, jalankan `ipconfig`. Jika DHCP aktif, Laptop 1 harus mendapat IP `192.168.10.x` dan Laptop 2 `192.168.20.x`.
4. Dari Windows, uji ping ke gateway masing-masing (`192.168.10.1` / `192.168.20.1`).
5. Pada MikroTik, lihat perangkat yang terdeteksi:

   ```
   /ip dhcp-server lease print
   /interface bridge host print
   ```

   Alamat MAC dari Proxmox/AlmaLinux harus terlihat pada port dan VLAN yang benar.

- Laptop 1 harus berada pada VLAN 10.
- Laptop 2 harus berada pada VLAN 20.

Periksa alamat IP yang diterima AlmaLinux dan pastikan gateway sesuai VLAN (dilakukan pada bagian F).

<img width="720" height="360" alt="Pengujian VLAN dari kedua server" src="images/D.5-vlan-test.png" />

---

# E. Konfigurasi Dual-WAN, Load Balancing, dan Failover

> **Sebelum memulai:** ganti nilai berikut sesuai hasil catatan pada C.2.
>
> | Placeholder | Arti | Contoh |
> | --- | --- | --- |
> | `GW-ISP1` | IP gateway ISP 1 | `192.168.100.1` |
> | `GW-ISP2` | IP gateway ISP 2 (wireless) | `192.168.200.1` |
> | `wifi1` | Nama interface wireless (cek `/interface print`) | `wifi1` atau `wlan1` |
>
> Gateway dilihat dengan `/ip dhcp-client print detail` (kolom `gateway`) atau pada modem ISP. Jika gateway diperoleh via DHCP dan dapat berubah, pertimbangkan memberi IP statis pada WAN.

## E.1 Menguji Koneksi ISP Secara Terpisah

Sebelum load balancing dibuat, pastikan masing-masing ISP dapat terhubung ke internet secara mandiri.

**Langkah 0 — Sambungkan ISP 2 (wireless) ke SSID ISP.** Pastikan `wifi1` tidak menjadi anggota bridge (`/interface bridge port print`). Pilih sesuai paket wireless yang terpasang pada RouterOS 7:

```
# Paket "wifi" (wifi-qcom / wifi-qcom-ac)
/interface wifi
set wifi1 configuration.mode=station configuration.ssid="NAMA-SSID-ISP" \
    security.authentication-types=wpa2-psk security.passphrase="PASSWORD-ISP" disabled=no

# ATAU paket "wireless" lama (wlan1)
/interface wireless security-profiles
add name=isp2 mode=dynamic-keys authentication-types=wpa2-psk wpa2-pre-shared-key="PASSWORD-ISP"
/interface wireless
set wlan1 mode=station ssid="NAMA-SSID-ISP" security-profile=isp2 disabled=no
```

Periksa sambungan dan kekuatan sinyal:

```
/interface wifi registration-table print
/interface wireless registration-table print
```

(gunakan perintah yang sesuai dengan paket yang terpasang). Station harus berstatus terhubung sebelum DHCP client dibuat. Jika ISP 2 memakai perangkat perantara melalui kabel, lewati langkah ini dan gunakan `ether2`.

**Langkah 1 — Buat DHCP client untuk kedua WAN** (lewati jika ISP menggunakan IP statis/PPPoE; jika sudah ada entri, gunakan `set` bukan `add`). Opsi `add-default-route=no` dipakai karena rute default akan dibuat manual pada langkah E.2–E.3:

```
/ip dhcp-client
add interface=ether1 add-default-route=no use-peer-dns=no comment="ISP1"
add interface=wifi1 add-default-route=no use-peer-dns=no comment="ISP2"
```

**Langkah 2 — Periksa status dan catat IP serta gateway:**

```
/ip dhcp-client print detail
/ip address print
```

**Langkah 3 — Uji tiap ISP secara terpisah dengan rute sementara.** Untuk menguji ISP 1:

```
/ip route add dst-address=0.0.0.0/0 gateway=GW-ISP1 comment="tes-sementara"
/ping 1.1.1.1 count=4
/ping cloudflare.com count=4
/ip route remove [find comment="tes-sementara"]
```

Ulangi untuk ISP 2 (wireless) dengan `gateway=GW-ISP2`. Perhatikan latency dan kehilangan paket (`packet-loss`) karena jalur wireless cenderung kurang stabil dibanding kabel.

Pengujian meliputi:

- Status interface WAN.
- IP Address dari masing-masing ISP.
- Gateway ISP.
- Koneksi ke tujuan internet (`ping 1.1.1.1`).
- DNS resolution (`ping cloudflare.com`).

<img width="720" height="420" alt="Pengujian ISP 1 dan ISP 2" src="images/E.1-wan-connectivity.png" />

## E.2 Konsep Load Balancing (Konfigurasi PCC)

Load balancing digunakan untuk membagi koneksi keluar melalui dua ISP.

Salah satu metode yang dapat digunakan pada MikroTik RouterOS 7 adalah PCC (Per Connection Classifier). PCC mengelompokkan koneksi sehingga koneksi yang sama menggunakan jalur WAN yang konsisten.

Load balancing per-connection tidak berarti satu sesi unduhan otomatis memperoleh gabungan bandwidth kedua ISP. Pembagian dilakukan terhadap beberapa koneksi.

**Cara kerja singkat:**

1. Setiap koneksi baru dari LAN dibagi dua kelompok berdasarkan hash alamat/port (`2/0` dan `2/1`).
2. Kelompok `2/0` diberi tanda `conn-isp1`, kelompok `2/1` diberi tanda `conn-isp2`.
3. Tanda koneksi diubah menjadi tanda routing (`to-isp1` / `to-isp2`).
4. Tabel routing `to-isp1` mengarah ke ISP 1, tabel `to-isp2` mengarah ke ISP 2.

**Langkah 1 — Buat tabel routing:**

```
/routing table
add name=to-isp1 fib
add name=to-isp2 fib
```

**Langkah 2 — Buat aturan mangle:**

```
/ip firewall mangle
# a. Trafik antar-LAN tidak ikut PCC
add chain=prerouting action=accept dst-address=192.168.10.0/24 in-interface-list=LAN comment="PCC: bypass VLAN10"
add chain=prerouting action=accept dst-address=192.168.20.0/24 in-interface-list=LAN comment="PCC: bypass VLAN20"

# b. Koneksi masuk dari WAN ditandai agar balasan keluar lewat ISP yang sama (penting untuk port forwarding)
add chain=prerouting action=mark-connection new-connection-mark=conn-isp1 passthrough=yes in-interface=ether1 connection-mark=no-mark comment="PCC: koneksi masuk ISP1"
add chain=prerouting action=mark-connection new-connection-mark=conn-isp2 passthrough=yes in-interface=wifi1 connection-mark=no-mark comment="PCC: koneksi masuk ISP2"

# c. Koneksi baru dari LAN dibagi dua dengan PCC
add chain=prerouting action=mark-connection new-connection-mark=conn-isp1 passthrough=yes in-interface-list=LAN connection-mark=no-mark dst-address-type=!local per-connection-classifier=both-addresses-and-ports:2/0 comment="PCC: bagian 0 -> ISP1"
add chain=prerouting action=mark-connection new-connection-mark=conn-isp2 passthrough=yes in-interface-list=LAN connection-mark=no-mark dst-address-type=!local per-connection-classifier=both-addresses-and-ports:2/1 comment="PCC: bagian 1 -> ISP2"

# d. Ubah tanda koneksi menjadi tanda routing (trafik dari LAN)
add chain=prerouting action=mark-routing new-routing-mark=to-isp1 passthrough=no in-interface-list=LAN connection-mark=conn-isp1 comment="Routing: conn-isp1 -> to-isp1"
add chain=prerouting action=mark-routing new-routing-mark=to-isp2 passthrough=no in-interface-list=LAN connection-mark=conn-isp2 comment="Routing: conn-isp2 -> to-isp2"

# e. Trafik yang dihasilkan router sendiri
add chain=output action=mark-routing new-routing-mark=to-isp1 passthrough=no connection-mark=conn-isp1 comment="Output: conn-isp1"
add chain=output action=mark-routing new-routing-mark=to-isp2 passthrough=no connection-mark=conn-isp2 comment="Output: conn-isp2"
```

**Pembagian beban tidak seimbang.** Jalur wireless umumnya lebih lambat atau kurang stabil daripada kabel. Jika bandwidth kedua ISP berbeda jauh, ubah PCC menjadi tiga bagian dan berikan dua bagian ke ISP yang lebih cepat. Contoh bila ISP 1 (kabel) dua kali lebih cepat: pada kedua aturan PCC pada langkah (c), ganti `2/0` dan `2/1` dengan `3/0`, `3/1` (keduanya `conn-isp1`) dan `3/2` (`conn-isp2`), sehingga dibutuhkan tiga aturan `mark-connection` sebagai pengganti dua aturan tersebut.

Ganti `both-addresses-and-ports` dengan `both-addresses` bila ingin pembagian per pasangan alamat saja. Opsi dengan port memberi distribusi lebih merata untuk server yang hanya dua alamat IP.

<img width="720" height="420" alt="Konfigurasi load balancing PCC" src="images/E.2-mikrotik-pcc.png" />

## E.3 Konsep Failover (Rute dan Netwatch)

Failover digunakan untuk mengalihkan koneksi ke ISP yang masih aktif ketika salah satu jalur mengalami gangguan.

Pemantauan jalur perlu memperhatikan keterjangkauan tujuan di luar jaringan lokal ISP, bukan hanya status kabel atau interface. Karena itu digunakan **Netwatch** untuk ping ke host internet melalui masing-masing ISP.

**Langkah 1 — Buat rute pemantauan** (rute `/32` yang memaksa ping ke host tertentu lewat ISP tertentu). Host yang berbeda dipakai agar tidak tumpang tindih dengan `1.1.1.1` yang dipakai untuk uji manual:

```
/ip route
add dst-address=1.0.0.1/32 gateway=GW-ISP1 comment="monitor-ISP1"
add dst-address=8.8.4.4/32 gateway=GW-ISP2 comment="monitor-ISP2"
```

**Langkah 2 — Buat rute default.** Setiap tabel memiliki jalur utama (distance 1) dan jalur cadangan ke ISP lain (distance 2). Jika ISP utama dimatikan oleh Netwatch, jalur cadangan otomatis dipakai:

```
/ip route
# Tabel main (trafik router sendiri)
add dst-address=0.0.0.0/0 gateway=GW-ISP1 distance=1 comment="default-via-isp1"
add dst-address=0.0.0.0/0 gateway=GW-ISP2 distance=2 comment="default-via-isp2"

# Tabel to-isp1 : utama ISP1, cadangan ISP2
add dst-address=0.0.0.0/0 gateway=GW-ISP1 routing-table=to-isp1 distance=1 comment="default-via-isp1"
add dst-address=0.0.0.0/0 gateway=GW-ISP2 routing-table=to-isp1 distance=2 comment="default-via-isp2"

# Tabel to-isp2 : utama ISP2, cadangan ISP1
add dst-address=0.0.0.0/0 gateway=GW-ISP2 routing-table=to-isp2 distance=1 comment="default-via-isp2"
add dst-address=0.0.0.0/0 gateway=GW-ISP1 routing-table=to-isp2 distance=2 comment="default-via-isp1"
```

**Langkah 3 — Buat Netwatch.** Jika ping gagal, semua rute default yang melewati ISP tersebut dinonaktifkan; jika ping kembali berhasil, rute diaktifkan lagi:

```
/tool netwatch
add host=1.0.0.1 interval=5s timeout=1s comment="Watch ISP1" \
    down-script="/ip route disable [find comment=\"default-via-isp1\"]" \
    up-script="/ip route enable [find comment=\"default-via-isp1\"]"
add host=8.8.4.4 interval=5s timeout=1s comment="Watch ISP2" \
    down-script="/ip route disable [find comment=\"default-via-isp2\"]" \
    up-script="/ip route enable [find comment=\"default-via-isp2\"]"
```

**Langkah 4 — Periksa:**

```
/tool netwatch print
/ip route print where comment~"default"
```

Rancangan pengujian:

1. ISP 1 dan ISP 2 aktif.
2. ISP 1 dinonaktifkan, ISP 2 tetap aktif.
3. ISP 1 dipulihkan, kemudian ISP 2 dinonaktifkan.
4. Kedua ISP dinonaktifkan.
5. Kedua ISP dipulihkan.

> **Catatan:** koneksi yang sedang berjalan melalui ISP yang mati akan terputus. Koneksi baru akan diarahkan ke ISP yang masih aktif setelah Netwatch mendeteksi gangguan (sekitar 5–10 detik dengan pengaturan di atas).

<img width="720" height="420" alt="Konfigurasi failover MikroTik" src="images/E.3-mikrotik-failover.png" />

## E.4 NAT untuk Akses Internet

Koneksi dari VLAN 10 dan VLAN 20 perlu memperoleh akses internet melalui mekanisme NAT yang sesuai dengan rancangan multi-WAN.

**Langkah 1 — Masquerade untuk semua WAN.** Satu aturan dengan `out-interface-list=WAN` cukup karena masquerade memakai IP dari interface keluar yang sebenarnya digunakan paket (ISP 1 atau ISP 2):

```
/ip firewall nat
add chain=srcnat action=masquerade out-interface-list=WAN comment="Masquerade ke WAN"
```

**Langkah 2 — Verifikasi:**

```
/ip firewall nat print
/ip firewall connection print where connection-mark=conn-isp1
/ip firewall connection print where connection-mark=conn-isp2
```

Pastikan aturan NAT dan routing konsisten dengan jalur WAN yang digunakan. Jangan membuat aturan masquerade yang saling bertentangan atau mengabaikan kebijakan routing PCC. Jangan menambahkan masquerade terpisah dengan `out-interface=bridge-lan` karena tidak diperlukan.

<img width="720" height="420" alt="Konfigurasi NAT MikroTik" src="images/E.4-mikrotik-nat.png" />

---

# F. Konfigurasi Jaringan pada AlmaLinux

> Bagian ini dilakukan pada masing-masing VM AlmaLinux. Perintah dan prosedurnya sama, sedangkan hostname, VLAN, dan alamat IP disesuaikan.

## F.1 Menentukan Identitas Server

| Parameter | Server 1 | Server 2 |
| --- | --- | --- |
| Hostname | `webserver-01` | `webserver-02` |
| VLAN | 10 | 20 |
| IP contoh | `192.168.10.10/24` | `192.168.20.10/24` |
| Gateway | `192.168.10.1` | `192.168.20.1` |

Atur hostname:

```
sudo hostnamectl set-hostname webserver-01
hostnamectl
```

Pada Server 2 gunakan `webserver-02`.

## F.2 Memeriksa Interface AlmaLinux

Buka console VM dari Web GUI Proxmox (**Console**), lalu jalankan:

```
ip -br link
ip -br addr
nmcli device status
```

Identifikasi NIC yang terhubung ke bridge server (`vmbr1`). Pada NIC VirtIO biasanya bernama `ens18` atau `ens19`. Jika VM juga memiliki NIC ke `vmbr0` (NAT), bedakan keduanya melalui alamat MAC pada tab **Hardware** Proxmox.

<img width="720" height="360" alt="Network interface AlmaLinux" src="images/F.2-almalinux-interface.png" />

## F.3 Mengatur IP Address

Alamat IP dapat diperoleh melalui DHCP dari MikroTik atau diatur secara statis. Untuk server, IP statis lebih disarankan.

**Cara 1 — Statis dengan `nmcli` (contoh Server 1; ganti nama koneksi `ens18` sesuai hasil `nmcli connection show`):**

```
sudo nmcli connection modify "ens18" \
    ipv4.method manual \
    ipv4.addresses 192.168.10.10/24 \
    ipv4.gateway 192.168.10.1 \
    ipv4.dns "192.168.10.1 1.1.1.1" \
    connection.autoconnect yes
sudo nmcli connection up "ens18"
```

Pada Server 2 gunakan `192.168.20.10/24` dan gateway `192.168.20.1`.

**Cara 2 — DHCP:**

```
sudo nmcli connection modify "ens18" ipv4.method auto
sudo nmcli connection up "ens18"
```

**Jika VM memiliki NIC kedua (NAT/`vmbr0`):** cegah NIC tersebut menjadi jalur default agar tidak terjadi konflik gateway:

```
sudo nmcli connection modify "ens19" ipv4.never-default yes
sudo nmcli connection up "ens19"
```

Jika menggunakan IP statis, pastikan:

- IP sesuai subnet VLAN.
- Gateway sesuai interface VLAN MikroTik.
- DNS dapat dijangkau.
- Tidak terjadi konflik IP.

Periksa routing:

```
ip route
```

Hasil yang diharapkan: `default via 192.168.10.1 dev ens18`.

Uji gateway Server 1:

```
ping -c 4 192.168.10.1
```

Pada Server 2, sesuaikan gateway menjadi `192.168.20.1`.

<img width="720" height="360" alt="Konfigurasi IP dan gateway AlmaLinux" src="images/F.3-almalinux-ip.png" />

## F.4 Menguji Koneksi Internet

Uji koneksi ke alamat IP internet:

```
ping -c 4 1.1.1.1
```

Uji resolusi DNS:

```
getent hosts cloudflare.com
```

Uji paket dapat diunduh (dibutuhkan untuk instalasi Apache):

```
curl -I https://almalinux.org
```

Jika koneksi IP berhasil tetapi DNS gagal, periksa konfigurasi DNS (`nmcli ... ipv4.dns` dan `/ip dns` pada MikroTik). Jika keduanya gagal, periksa berurutan: kabel dan port MikroTik → VLAN/PVID → gateway → routing PCC → NAT → status WAN. Contoh pemeriksaan di MikroTik:

```
/ping 1.1.1.1 src-address=192.168.10.1
/ip firewall nat print stats
/tool torch interface=vlan10-server1
```

<img width="720" height="360" alt="Pengujian koneksi internet AlmaLinux" src="images/F.4-almalinux-internet.png" />

---

# G. Instalasi dan Konfigurasi Web Server

## G.1 Instalasi Apache HTTP Server

Pada masing-masing AlmaLinux, jalankan:

1. Perbarui metadata paket (opsional):

   ```
   sudo dnf makecache
   ```

2. Pasang Apache:

   ```
   sudo dnf install -y httpd
   ```

3. Aktifkan layanan agar langsung berjalan dan otomatis start saat boot:

   ```
   sudo systemctl enable --now httpd
   ```

4. Periksa status:

   ```
   sudo systemctl status httpd
   ```

   Status yang diharapkan: `active (running)`. Tekan `q` untuk keluar dari tampilan status.

<img width="720" height="360" alt="Status Apache HTTP Server" src="images/G.1-apache-status.png" />

## G.2 Membuat Halaman Web Pengujian

Buat halaman web sederhana sebagai pembeda antar server:

```
sudo nano /var/www/html/index.html
```

Contoh isi halaman Server 1:

```
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Web Server 1</title>
</head>
<body>
    <h1>Web Server AlmaLinux 1 Berhasil Diakses</h1>
    <p>Server: webserver-01</p>
    <p>VLAN: 10</p>
</body>
</html>
```

Simpan di `nano` dengan `Ctrl+O`, `Enter`, lalu keluar dengan `Ctrl+X`.

Pada Server 2, ubah identitas menjadi `webserver-02` dan VLAN `20`.

<img width="720" height="360" alt="Halaman web Server 1" src="images/G.2-webserver-1.png" />

<img width="720" height="360" alt="Halaman web Server 2" src="images/G.2-webserver-2.png" />

## G.3 Mengatur Firewall AlmaLinux

Firewall bawaan AlmaLinux (`firewalld`) memblokir port 80 secara default. Izinkan layanan HTTP:

```
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload
```

Verifikasi:

```
sudo firewall-cmd --list-services
```

Jika HTTPS telah dikonfigurasi, izinkan layanan HTTPS:

```
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

Jangan membuka layanan administrasi seperti SSH ke seluruh internet tanpa pembatasan.

<img width="720" height="360" alt="Firewall HTTP AlmaLinux" src="images/G.3-almalinux-firewall.png" />

## G.4 Menguji Web Server dari Jaringan Lokal

1. Dari AlmaLinux sendiri:

   ```
   curl -I http://localhost
   curl http://localhost
   ```

   Respons `HTTP/1.1 200 OK` dan isi halaman menandakan Apache berjalan.
2. Dari perangkat lain pada VLAN yang sama (misalnya Windows laptop yang berada di VLAN 10), buka browser ke `http://192.168.10.10`.
3. Dari VLAN yang berbeda, akses seharusnya **gagal** karena diblokir firewall MikroTik (D.4). Hal ini merupakan hasil yang benar.

<img width="720" height="360" alt="Pengujian web server lokal" src="images/G.4-webserver-local-test.png" />

---

# H. Publikasi Web Server agar Dapat Diakses dari Internet

## H.1 Konsep Self-Hosting

Aplikasi web berjalan langsung pada AlmaLinux. Laptop Windows hanya berfungsi sebagai host VMware Workstation dan tidak menjadi web server.

Untuk membuat layanan dapat diakses dari internet, diperlukan metode publikasi dari jaringan lokal menuju pengguna internet.

Dua metode yang dapat digunakan:

- **Port Forwarding** — MikroTik meneruskan koneksi dari alamat publik menuju AlmaLinux.
- **Cloudflare Tunnel** — program `cloudflared` berjalan pada AlmaLinux dan membuat koneksi keluar menuju jaringan Cloudflare.

## H.2 Opsi Port Forwarding

Port forwarding dapat digunakan apabila koneksi ISP memiliki alamat IP publik yang dapat menerima koneksi masuk.

**Langkah 1 — Periksa apakah WAN memiliki IP publik:**

1. Lihat IP WAN pada MikroTik: `/ip address print`.
2. Bandingkan dengan IP publik yang terlihat dari internet, misalnya dari AlmaLinux: `curl https://api.ipify.org`.
3. Jika kedua IP **sama**, WAN memiliki IP publik. Jika **berbeda**, ada NAT tambahan (modem ISP atau CGNAT) dan port forwarding tidak akan berfungsi tanpa pengaturan tambahan atau layanan khusus dari ISP. Rentang `100.64.0.0/10` pada WAN merupakan tanda CGNAT.

Hal yang perlu diperiksa:

- Apakah WAN memperoleh public IP atau berada di belakang CGNAT.
- Apakah terdapat NAT tambahan pada modem/router ISP.
- Apakah alamat IP server tetap.
- Apakah firewall MikroTik mengizinkan koneksi yang diperlukan.
- Apakah HTTPS telah disiapkan.

**Langkah 2 — Buat aturan dstnat.** Contoh: akses HTTP ke IP ISP 1 (kabel) diarahkan ke Server 1, sedangkan akses ke IP ISP 2 (wireless) diarahkan ke Server 2. ISP wireless atau hotspot sangat sering berada di belakang CGNAT sehingga aturan untuk ISP 2 mungkin tidak dapat dijangkau dari internet; dalam hal itu gunakan Cloudflare Tunnel (H.3):

```
/ip firewall nat
add chain=dstnat action=dst-nat in-interface=ether1 protocol=tcp dst-port=80 to-addresses=192.168.10.10 to-ports=80 comment="ISP1:80 -> Server1"
add chain=dstnat action=dst-nat in-interface=wifi1 protocol=tcp dst-port=80 to-addresses=192.168.20.10 to-ports=80 comment="ISP2:80 -> Server2"
```

**Langkah 3 — Pastikan aturan forward mengizinkan dstnat.** Aturan `connection-nat-state=dstnat` sudah dibuat pada D.4. Aturan mangle E.2 bagian (b) memastikan balasan dari server keluar lewat ISP yang sama dengan arah masuknya.

**Langkah 4 — Jika WAN berada di belakang modem ISP**, aktifkan juga port forwarding (atau mode DMZ/bridge) pada modem tersebut agar port 80 diteruskan ke IP WAN MikroTik.

**Langkah 5 — Uji dari luar jaringan** (misalnya dari HP dengan data seluler): buka `http://<IP-publik-ISP1>` dan `http://<IP-publik-ISP2>`.

Alur koneksi:

```text
Pengguna Internet
       |
Public IP
       |
MikroTik
       |
Port Forwarding
       |
VLAN Server
       |
AlmaLinux Web Server
```

<img width="720" height="420" alt="Port forwarding MikroTik" src="images/H.2-port-forwarding.png" />

## H.3 Opsi Cloudflare Tunnel

Cloudflare Tunnel dapat digunakan tanpa membuka port inbound pada router. Program `cloudflared` dijalankan langsung pada AlmaLinux, bukan pada Windows.

Persyaratan umum:

- Akun Cloudflare.
- Domain yang dikelola melalui Cloudflare untuk hostname aplikasi.
- AlmaLinux memiliki akses internet.
- Web server lokal berjalan.
- `cloudflared` dipasang dan dijalankan pada AlmaLinux.

**Langkah 1 — Siapkan domain di Cloudflare.** Tambahkan domain ke akun Cloudflare dan arahkan *nameserver* domain ke nameserver yang diberikan Cloudflare.

**Langkah 2 — Buat tunnel melalui dashboard.** Masuk ke dashboard Cloudflare Zero Trust, buka bagian **Networks > Tunnels** (nama menu dapat berubah mengikuti pembaruan Cloudflare), lalu:

1. Klik **Create a tunnel**, pilih tipe **Cloudflared**.
2. Beri nama, misalnya `tunnel-server1` (untuk Server 2: `tunnel-server2`).
3. Pilih sistem operasi **Red Hat/Linux** dan arsitektur **64-bit**. Dashboard menampilkan perintah instalasi lengkap beserta token tunnel. Salin token tersebut dan jaga kerahasiaannya.

**Langkah 3 — Pasang `cloudflared` pada AlmaLinux.** Gunakan perintah yang ditampilkan dashboard. Secara umum bentuknya adalah menambahkan repositori Cloudflare, memasang paket, lalu mendaftarkan service dengan token:

```
curl -fsSL https://pkg.cloudflare.com/cloudflared.repo | sudo tee /etc/yum.repos.d/cloudflared.repo
sudo dnf install -y cloudflared
sudo cloudflared service install <TOKEN-DARI-DASHBOARD>
```

**Langkah 4 — Verifikasi service:**

```
sudo systemctl status cloudflared
```

Pada dashboard, status tunnel harus berubah menjadi **Healthy**.

**Langkah 5 — Tambahkan Public Hostname** pada tunnel tersebut:

- **Subdomain/Domain**: `server1` / `domain.tld`
- **Service type**: `HTTP`
- **URL**: `localhost:80`

Ulangi untuk Server 2 dengan tunnel dan hostname sendiri (`server2.domain.tld`).

**Langkah 6 — Uji dari luar:** buka `https://server1.domain.tld` dan `https://server2.domain.tld`. HTTPS ditangani oleh Cloudflare sehingga tidak perlu memasang sertifikat pada Apache untuk pengujian ini.

Alur koneksi:

```text
Pengguna Internet
       |
Domain Cloudflare
       |
Cloudflare Network
       |
Tunnel
       |
cloudflared pada AlmaLinux
       |
Apache / Nginx
```

Contoh pemetaan hostname:

| Server | Hostname contoh | Layanan lokal |
| --- | --- | --- |
| AlmaLinux 1 | `server1.domain.tld` | `http://localhost:80` |
| AlmaLinux 2 | `server2.domain.tld` | `http://localhost:80` |

Hostname tersebut hanya contoh dan harus diganti dengan domain milik sendiri.

<img width="720" height="420" alt="Pembuatan Cloudflare Tunnel" src="images/H.3-cloudflare-tunnel.png" />

<img width="720" height="420" alt="Pengujian akses domain publik" src="images/H.4-public-web-test.png" />

## H.4 Pengaruh Dual-WAN terhadap Akses Publik

Load balancing dan failover untuk koneksi keluar tidak otomatis menjamin semua koneksi masuk ke web server selalu tersedia.

- Pada Cloudflare Tunnel, koneksi dibuat dari AlmaLinux menuju Cloudflare. Jika salah satu ISP mati dan ISP lain masih aktif, tunnel dapat tersambung kembali melalui jalur yang tersedia, bergantung pada routing dan pemulihan koneksi.
- Pada port forwarding, akses masuk bergantung pada alamat publik dan jalur ISP yang digunakan. Jika ISP 1 mati, alamat publik ISP 1 tidak dapat diakses meskipun ISP 2 masih aktif.
- Jika ISP 2 (wireless) berada di belakang CGNAT, port forwarding hanya dapat bekerja melalui ISP 1; Cloudflare Tunnel tidak terpengaruh oleh CGNAT.
- Jika kedua ISP mati, akses dari internet tidak tersedia.
- Load balancing PCC tidak menggabungkan dua ISP menjadi satu alamat IP publik.

---

# I. Pengujian Load Balancing, Failover, dan Ketersediaan Web

**Persiapan umum sebelum pengujian:**

1. Buka WinBox dan siapkan jendela berikut untuk dipantau: `Interfaces` (kolom Tx/Rx `ether1` dan `wifi1`), `IP > Firewall > Connections`, dan `Tools > Netwatch`.
2. Siapkan alat uji dari terminal MikroTik:

   ```
   /interface monitor-traffic ether1,wifi1
   ```

3. Dari AlmaLinux, perintah berikut membuat 10 koneksi dan menampilkan IP publik yang terlihat. Jika load balancing berjalan, akan muncul **dua IP publik berbeda** (satu milik masing-masing ISP):

   ```
   for i in $(seq 1 10); do curl -s --max-time 5 https://api.ipify.org; echo; done
   ```

## I.1 Skenario 1 — Kedua ISP Aktif

Kondisi:

- ISP 1 aktif.
- ISP 2 aktif.
- Load balancing berjalan.

Pengujian:

1. Pastikan kedua interface WAN aktif (`/interface print`, status `R`) dan Netwatch berstatus **up** pada keduanya.
2. Buat beberapa koneksi internet dari AlmaLinux dengan perintah loop `curl` pada persiapan di atas. Catat IP publik yang muncul.
3. Periksa trafik pada masing-masing interface WAN dengan `/interface monitor-traffic ether1,wifi1`. Keduanya harus menunjukkan trafik.
4. Hitung koneksi per ISP:

   ```
   /ip firewall connection print count-only where connection-mark=conn-isp1
   /ip firewall connection print count-only where connection-mark=conn-isp2
   ```

5. Uji akses web server dari jaringan eksternal (Port Forwarding atau Cloudflare Tunnel).
6. Catat hasil pengujian.

<img width="720" height="420" alt="Kedua ISP aktif" src="images/I.1-both-isp-active.png" />

## I.2 Skenario 2 — Hanya ISP 1 Aktif

Kondisi:

- ISP 1 aktif.
- ISP 2 dinonaktifkan atau disimulasikan mengalami gangguan.

Pengujian:

1. Putuskan koneksi ISP 2 secara terkontrol, misalnya `/interface disable wifi1`, atau mematikan hotspot/AP ISP 2, atau menjauhkan antena hingga sambungan terputus.
2. Pastikan MikroTik mendeteksi gangguan: `/tool netwatch print` (status ISP2 menjadi **down**) dan `/ip route print where comment="default-via-isp2"` (rute berstatus disabled/inactive).
3. Uji koneksi internet dari AlmaLinux (`ping -c 4 1.1.1.1`, lalu loop `curl`). Seluruh koneksi harus keluar dengan IP publik ISP 1 saja.
4. Uji akses web dari jaringan eksternal.
5. Catat waktu pemulihan (selisih antara gangguan dan internet kembali normal, kira-kira beberapa detik) dan hasil pengujian.
6. Pulihkan ISP 2 dengan `/interface enable wifi1`, lalu pastikan Netwatch kembali **up** dan koneksi kembali terbagi dua.

<img width="720" height="420" alt="ISP 1 aktif dan ISP 2 mati" src="images/I.2-isp1-only.png" />

## I.3 Skenario 3 — Hanya ISP 2 Aktif

Kondisi:

- ISP 1 dinonaktifkan atau disimulasikan mengalami gangguan.
- ISP 2 aktif.

Ulangi prosedur I.2 dengan memutus ISP 1 (`/interface disable ether1`), lalu catat hasilnya. Seluruh koneksi dari AlmaLinux harus keluar melalui ISP 2. Pulihkan ISP 1 setelah pengujian selesai dan catat waktu pemulihan.

<img width="720" height="420" alt="ISP 2 aktif dan ISP 1 mati" src="images/I.3-isp2-only.png" />

## I.4 Skenario 4 — Kedua ISP Mati

Kondisi:

- ISP 1 mati.
- ISP 2 mati.

Pengujian:

1. Putuskan kedua koneksi WAN secara terkontrol (`/interface disable ether1,wifi1`).
2. Pastikan MikroTik mendeteksi kedua jalur tidak tersedia (Netwatch kedua host **down**).
3. Uji akses internet dari AlmaLinux (`ping -c 4 1.1.1.1` harus gagal).
4. Uji akses domain publik dari perangkat eksternal (harus gagal).
5. Uji apakah web server masih dapat diakses dari jaringan lokal: `curl http://192.168.10.10` dari perangkat pada VLAN 10.
6. Pulihkan kedua ISP (`/interface enable ether1,wifi1`) dan catat waktu hingga layanan normal kembali.

Hasil yang diharapkan: web server masih dapat berjalan dan diakses dari jaringan lokal selama server dan jaringan lokal aktif, tetapi tidak dapat diakses dari internet karena kedua jalur WAN tidak tersedia.

<img width="720" height="420" alt="Kedua ISP mati" src="images/I.4-both-isp-down.png" />

## I.5 Tabel Hasil Pengujian

| Skenario | ISP 1 | ISP 2 | Internet AlmaLinux | Akses Web dari Internet |
| --- | --- | --- | --- | --- |
| 1 | Aktif | Aktif | Catat hasil | Catat hasil |
| 2 | Aktif | Mati | Catat hasil | Catat hasil |
| 3 | Mati | Aktif | Catat hasil | Catat hasil |
| 4 | Mati | Mati | Tidak tersedia | Tidak tersedia |

Tabel tambahan yang disarankan untuk dicatat:

| Pengujian | Hasil | Keterangan |
| --- | --- | --- |
| Jumlah koneksi `conn-isp1` / `conn-isp2` (Skenario 1) | Catat hasil | |
| Waktu failover ISP 1 → ISP 2 (detik) | Catat hasil | |
| Waktu failover ISP 2 → ISP 1 (detik) | Catat hasil | |
| Ping Server 1 → Server 2 (diblokir?) | Catat hasil | |
| Akses web lokal saat kedua ISP mati | Catat hasil | |

> **Catatan:** isi hasil berdasarkan pengujian aktual. Jangan menyatakan berhasil sebelum pengujian dilakukan.

---

# J. Analisis dan Evaluasi

Analisis dilakukan berdasarkan hasil pengujian yang diperoleh.

Hal yang dievaluasi:

1. **Load Balancing** — apakah koneksi baru terbagi melalui ISP 1 dan ISP 2 sesuai kebijakan. Bukti: IP publik berbeda pada loop `curl` dan jumlah koneksi `conn-isp1`/`conn-isp2`.
2. **Failover** — apakah koneksi berpindah ke ISP yang masih aktif ketika salah satu jalur mengalami gangguan. Bukti: status Netwatch, status rute, dan hasil `ping`.
3. **Recovery** — apakah jalur kembali normal setelah ISP dipulihkan.
4. **VLAN Segmentation** — apakah Server 1 dan Server 2 berada pada broadcast domain yang berbeda. Bukti: IP subnet berbeda dan `/interface bridge host print`.
5. **Inter-VLAN Firewall** — apakah komunikasi yang tidak diizinkan berhasil diblokir (ping/curl antar-server gagal).
6. **Web Server** — apakah masing-masing AlmaLinux dapat melayani permintaan HTTP/HTTPS.
7. **Public Access** — apakah aplikasi dapat diakses dari jaringan eksternal.
8. **Availability** — apakah layanan publik pulih melalui ISP yang masih aktif setelah satu jalur mengalami gangguan.

## J.1 Batasan Pengujian

- PCC membagi koneksi, bukan menjumlahkan bandwidth kedua ISP untuk setiap satu sesi.
- Sesi yang sedang berjalan dapat terputus ketika ISP yang digunakan mengalami gangguan.
- VLAN memisahkan broadcast domain, tetapi komunikasi antar-VLAN tetap perlu diatur menggunakan firewall.
- Cloudflare Tunnel tetap membutuhkan setidaknya satu jalur internet yang aktif.
- Jika kedua ISP mati, akses dari internet tidak tersedia.
- Dua server AlmaLinux belum otomatis menjadi high availability server. Redundansi aplikasi, database, penyimpanan, dan mekanisme perpindahan layanan merupakan pengembangan terpisah.
- ISP 2 menggunakan wireless sehingga kualitasnya dipengaruhi sinyal, interferensi, dan jarak. Failover pada jalur ini dapat terpicu oleh gangguan sesaat, dan kecepatan kedua ISP umumnya tidak seimbang.
- ISP wireless/hotspot sering berada di belakang CGNAT sehingga tidak dapat menerima koneksi masuk melalui port forwarding.
- Seluruh jalur jaringan bergantung pada satu router MikroTik dan satu kabel per laptop sehingga MikroTik merupakan *single point of failure*.

---

# K. Pemecahan Masalah Umum

| Gejala | Kemungkinan penyebab | Tindakan |
| --- | --- | --- |
| `ens34` tidak muncul di Proxmox | Adapter kedua belum ditambahkan / VM belum dimatikan saat penambahan | Ulangi A.2, nyalakan ulang VM |
| `vmbr1` `DOWN` | VMnet0 salah adapter atau kabel belum terhubung | Periksa A.3 dan link `ether3`/`ether4` di MikroTik |
| AlmaLinux tidak mendapat IP | Port bukan access VLAN yang benar / DHCP server belum aktif | Cek `PVID` (`/interface bridge port print`) dan `/ip dhcp-server print` |
| Ping gateway berhasil, internet gagal | NAT/routing/PCC bermasalah | Cek `/ip firewall nat print`, `/ip route print`, `/ping 1.1.1.1` dari router |
| Ping IP berhasil, DNS gagal | DNS belum diatur | Cek `/ip dns print` dan `ipv4.dns` pada `nmcli` |
| Sebagian koneksi lambat/gagal | Salah satu WAN bermasalah tetapi Netwatch belum mendeteksi | Cek `/tool netwatch print` dan rute monitor `/32` |
| Port forwarding tidak berfungsi | CGNAT / modem ISP / aturan forward / firewalld | Ikuti pemeriksaan H.2 langkah 1 dan 4, `firewall-cmd --list-services` |
| `wifi1` tidak mendapat IP / tidak terhubung | SSID/password salah, sinyal lemah, atau `wifi1` masih menjadi anggota bridge | Cek registration table, keluarkan dari bridge, dekatkan antena/AP |
| ISP 2 sering terdeteksi down lalu up | Sinyal tidak stabil atau Netwatch terlalu sensitif | Naikkan `timeout`/`interval` Netwatch (misalnya `interval=10s timeout=2s`) |
| Router tidak dapat diakses setelah `vlan-filtering=yes` | Port manajemen tidak termasuk VLAN | Gunakan Safe Mode, WinBox via MAC, atau reset lalu restore backup |

---

# L. Kesimpulan

Project ini merancang jaringan dengan satu router MikroTik yang mengelola dua koneksi ISP, melakukan load balancing dan failover, serta memisahkan dua server AlmaLinux menggunakan VLAN 10 dan VLAN 20.

Managed switch tidak digunakan karena pemisahan VLAN dilakukan langsung oleh MikroTik melalui konfigurasi port dan VLAN-aware bridge. Port menuju laptop pertama ditempatkan pada VLAN 10, sedangkan port menuju laptop kedua ditempatkan pada VLAN 20.

Masing-masing AlmaLinux menjalankan web server secara mandiri. Layanan web dapat dipublikasikan ke internet menggunakan port forwarding apabila tersedia public IP yang dapat menerima koneksi masuk, atau Cloudflare Tunnel sebagai alternatif.

Pengujian dilakukan dalam empat kondisi, yaitu kedua ISP aktif, hanya ISP 1 aktif, hanya ISP 2 aktif, serta kedua ISP mati. Hasil pengujian digunakan untuk mengevaluasi load balancing, failover, segmentasi VLAN, dan ketersediaan layanan web.

---

## Referensi

1. MikroTik RouterOS Documentation — Bridge VLAN Table: https://help.mikrotik.com/docs/display/ROS/Bridge+VLAN+Table
2. MikroTik RouterOS Documentation — Load Balancing: https://manual.mikrotik.com/docs/high-availability-solutions/load-balancing/
3. Proxmox VE Documentation — Network Configuration: https://pve.proxmox.com/pve-docs/pve-admin-guide.html#sysadmin_network_configuration
4. Cloudflare Documentation — Cloudflare Tunnel: https://developers.cloudflare.com/tunnel/
5. AlmaLinux Documentation: https://docs.almalinux.org/

---

> **Catatan implementasi:** perintah CLI MikroTik pada dokumen ini adalah **templat** berdasarkan rancangan contoh (`ether1` kabel untuk ISP 1, `wifi1` wireless untuk ISP 2, `ether3`–`ether4` untuk VLAN, subnet `192.168.10.0/24` dan `192.168.20.0/24`, gateway ISP sebagai placeholder `GW-ISP1`/`GW-ISP2`). Sebelum menempelkan perintah, sesuaikan nama interface, alamat IP, gateway ISP, dan metode koneksi (DHCP/Static/PPPoE) dengan kondisi perangkat. Selalu buat backup dan gunakan Safe Mode agar konfigurasi VLAN filtering dan dual-WAN tidak memutus akses manajemen router.
