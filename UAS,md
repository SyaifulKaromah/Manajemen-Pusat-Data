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
| Koneksi Internet | 2 ISP (Dual-WAN) |
| Metode Pengelolaan WAN | Load Balancing dan Failover |
| Segmentasi Jaringan | VLAN 10 dan VLAN 20 |
| Platform Virtualisasi | VMware Workstation + Proxmox VE |
| Host Server 1 | Laptop 1 |
| Host Server 2 | Laptop 2 |
| Sistem Operasi Server | AlmaLinux |
| Web Server | Apache HTTP Server (`httpd`) |
| Publikasi Web | Cloudflare Tunnel atau Port Forwarding |
| Jaringan Server 1 | VLAN 10 |
| Jaringan Server 2 | VLAN 20 |

> **Catatan:** proyek ini menggunakan satu perangkat MikroTik untuk mengatur koneksi dua ISP, routing, firewall, NAT, dan VLAN. Managed switch tidak digunakan. Port Ethernet MikroTik langsung dihubungkan ke masing-masing laptop. Nama interface, alamat IP, subnet, serta nomor port harus disesuaikan dengan perangkat yang digunakan.

---

## Tujuan Project

Project ini membangun infrastruktur jaringan menggunakan satu router MikroTik yang mengelola dua koneksi internet (dual-WAN), melakukan load balancing dan failover, serta memisahkan dua jaringan server menggunakan VLAN.

Dua server AlmaLinux dijalankan pada dua laptop fisik yang berbeda. Masing-masing laptop menjalankan VMware Workstation, kemudian di dalamnya terdapat Proxmox VE sebagai platform virtualisasi dan AlmaLinux sebagai server aplikasi.

MikroTik bertindak sebagai pusat pengelolaan lalu lintas jaringan. Selain mengatur koneksi ISP 1 dan ISP 2, MikroTik juga menangani segmentasi VLAN 10 dan VLAN 20 sehingga kedua server berada pada jaringan yang berbeda.

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
          ISP 1                         ISP 2
            |                             |
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

# A. Persiapan Network Adapter pada VMware Workstation

> Bagian ini dilakukan pada kedua laptop. Prosedur penambahan adapter sama, sedangkan port fisik yang digunakan akan terhubung ke VLAN yang berbeda pada MikroTik.

## A.1 Memeriksa Network Adapter Proxmox

Matikan VM Proxmox terlebih dahulu, kemudian buka VMware Workstation dan pilih VM Proxmox.

Buka menu:

```
VM > Settings
```

Pastikan adapter pertama tetap menggunakan mode NAT. Adapter ini dipertahankan untuk koneksi manajemen Proxmox melalui jaringan virtual VMware.

<img width="640" height="420" alt="Pengaturan Network Adapter NAT pada VMware" src="images/A.1-vmware-adapter-nat.png" />

## A.2 Menambahkan Network Adapter Kedua

Tambahkan adapter kedua melalui menu:

```
Add > Network Adapter > Finish
```

Pilih mode:

```
Bridged: Connected directly to the physical network
```

Aktifkan:

- `Connected`
- `Connect at power on`

Adapter Bridged digunakan untuk meneruskan koneksi dari Proxmox menuju Ethernet fisik laptop, kemudian menuju port VLAN pada MikroTik.

<img width="640" height="420" alt="Penambahan Network Adapter kedua" src="images/A.2-vmware-add-adapter.png" />

## A.3 Memastikan VMware Bridged ke Ethernet Fisik

Buka:

```
Edit > Virtual Network Editor
```

Pilih `VMnet0`, kemudian pastikan mode Bridged diarahkan ke adapter Ethernet fisik yang benar.

Hindari memilih adapter Wi-Fi atau adapter virtual lain apabila rancangan pengujian menggunakan Ethernet.

<img width="640" height="420" alt="VMnet0 diarahkan ke Ethernet fisik" src="images/A.3-vmnet0-ethernet.png" />

## A.4 Mengulangi Konfigurasi pada Laptop Kedua

Lakukan langkah A.1 sampai A.3 pada laptop kedua. Kedua laptop menggunakan dua adapter dengan fungsi yang sama:

| Adapter | Mode | Fungsi |
| --- | --- | --- |
| Network Adapter 1 | NAT | Koneksi manajemen Proxmox |
| Network Adapter 2 | Bridged | Jalur jaringan server menuju MikroTik |

<img width="640" height="420" alt="Konfigurasi adapter VMware pada laptop kedua" src="images/A.4-vmware-laptop2.png" />

---

# B. Pemeriksaan dan Konfigurasi Bridge pada Proxmox

> Bagian ini dilakukan pada masing-masing Proxmox. Jangan mengubah bridge NAT yang sedang digunakan untuk mengakses Web GUI Proxmox.

## B.1 Memeriksa Network Interface

Login ke console Proxmox sebagai `root`, kemudian jalankan:

```
ip -br link
ip -br addr
```

Perintah tersebut digunakan untuk melihat nama interface, status link, dan alamat IP.

Identifikasi:

- Interface pertama yang terhubung ke NAT VMware.
- Interface kedua yang terhubung ke mode Bridged.
- Bridge utama yang digunakan untuk manajemen Proxmox.
- Bridge tambahan yang akan digunakan oleh AlmaLinux.

Nama interface dapat berbeda pada setiap instalasi. Pada konfigurasi yang diperiksa sebelumnya, adapter kedua terdeteksi sebagai `ens34`, tetapi nama aktual tetap harus diperiksa pada masing-masing host.

<img width="720" height="360" alt="Pemeriksaan interface Proxmox" src="images/B.1-proxmox-ip-link.png" />

## B.2 Memeriksa Konfigurasi Network Proxmox

Jalankan:

```
cat /etc/network/interfaces
```

Pastikan bridge NAT tetap dipertahankan. Periksa juga apakah bridge tambahan sudah tersedia dan apakah bridge tersebut sedang digunakan oleh VM lain.

Contoh rancangan bridge untuk adapter kedua:

```
auto ens34
iface ens34 inet manual

auto vmbr1
iface vmbr1 inet manual
    bridge-ports ens34
    bridge-stp off
    bridge-fd 0
```

> **Catatan:** konfigurasi di atas merupakan contoh. Sesuaikan nama interface dan bridge berdasarkan hasil pemeriksaan. Jangan menimpa konfigurasi `vmbr0` yang sudah memiliki IP manajemen. Pastikan bridge yang akan diubah tidak sedang digunakan oleh VM lain.

<img width="720" height="360" alt="Konfigurasi network interfaces Proxmox" src="images/B.2-proxmox-interfaces.png" />

## B.3 Memastikan Bridge Terhubung ke Adapter Bridged

Setelah konfigurasi diterapkan dengan aman, periksa kembali:

```
ip -br link
bridge link
```

Pastikan interface adapter kedua menjadi port dari bridge yang direncanakan.

Jika interface masih berstatus `DOWN`, periksa pengaturan adapter VMware, pilihan VMnet0, dan koneksi Ethernet fisik laptop.

<img width="720" height="360" alt="Pemeriksaan bridge Proxmox" src="images/B.3-proxmox-bridge.png" />

## B.4 Menghubungkan Network Device AlmaLinux ke Bridge

Buka Web GUI Proxmox, kemudian pilih VM AlmaLinux.

Masuk ke:

```
Hardware > Network Device
```

Tambahkan NIC untuk jaringan server apabila belum tersedia. Pilih bridge yang terhubung ke adapter Bridged.

NIC NAT/manajemen yang sudah digunakan tidak perlu dihapus apabila masih diperlukan.

<img width="720" height="420" alt="Network Device AlmaLinux pada Proxmox" src="images/B.4-proxmox-vm-network.png" />

## B.5 Mengulangi Konfigurasi pada Proxmox Laptop Kedua

Ulangi pemeriksaan interface dan bridge pada Proxmox laptop kedua. Pastikan adapter Bridged terhubung ke bridge yang digunakan oleh AlmaLinux kedua.

<img width="720" height="360" alt="Bridge Proxmox laptop kedua" src="images/B.5-proxmox-laptop2.png" />

---

# C. Persiapan dan Identifikasi Interface MikroTik

> Bagian ini dilakukan pada satu router MikroTik. MikroTik menjadi pusat pengaturan koneksi ISP, VLAN, routing, NAT, dan firewall.

## C.1 Mengidentifikasi Port MikroTik

Periksa seluruh interface Ethernet pada MikroTik melalui WinBox atau terminal RouterOS.

Contoh pemetaan port (sesuaikan dengan perangkat aktual):

| Fungsi | Interface contoh |
| --- | --- |
| ISP 1 | `ether1` |
| ISP 2 | `ether2` |
| Laptop 1 — VLAN 10 | `ether3` |
| Laptop 2 — VLAN 20 | `ether4` |

Port yang digunakan harus dipastikan melalui pemeriksaan perangkat. Jangan langsung mengasumsikan bahwa semua model MikroTik memiliki jumlah port dan susunan yang sama.

<img width="720" height="420" alt="Daftar interface MikroTik" src="images/C.1-mikrotik-interface.png" />

## C.2 Mengidentifikasi Koneksi ISP

Catat metode koneksi masing-masing ISP, misalnya DHCP Client, IP statis, atau PPPoE.

| Parameter | ISP 1 | ISP 2 |
| --- | --- | --- |
| Interface | Sesuaikan | Sesuaikan |
| Metode koneksi | DHCP/Static/PPPoE | DHCP/Static/PPPoE |
| IP Address | Catat aktual | Catat aktual |
| Gateway | Catat aktual | Catat aktual |
| Status | Catat hasil | Catat hasil |

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

Alamat di atas merupakan rancangan contoh. Pastikan subnet tidak bertabrakan dengan jaringan NAT VMware maupun jaringan lain yang digunakan.

<img width="720" height="360" alt="Rencana VLAN dan IP Address" src="images/C.3-vlan-ip-plan.png" />

---

# D. Konfigurasi VLAN pada MikroTik

## D.1 Konsep VLAN Tanpa Managed Switch

Karena hanya menggunakan satu router MikroTik, fungsi pemisahan VLAN dapat dilakukan langsung oleh MikroTik selama perangkat mendukung VLAN-aware bridge dan memiliki port Ethernet yang mencukupi.

Rancangan port:

| Port MikroTik | Mode | VLAN | Perangkat |
| --- | --- | ---: | --- |
| Port menuju Laptop 1 | Access/Untagged | 10 | Proxmox dan AlmaLinux 1 |
| Port menuju Laptop 2 | Access/Untagged | 20 | Proxmox dan AlmaLinux 2 |

Dengan konfigurasi access port, laptop menerima frame Ethernet tanpa tag VLAN. MikroTik menentukan VLAN berdasarkan PVID pada port yang terhubung ke masing-masing laptop.

Tidak diperlukan managed switch terpisah pada rancangan ini.

<img width="720" height="420" alt="Pemetaan port access VLAN MikroTik" src="images/D.1-mikrotik-vlan-port.png" />

## D.2 Membuat Bridge VLAN pada MikroTik

Konfigurasi VLAN pada RouterOS 7 dapat menggunakan bridge dengan `vlan-filtering`.

Sebelum mengaktifkan VLAN filtering, tentukan terlebih dahulu port anggota bridge, PVID, tagged port, dan untagged port. Kesalahan konfigurasi dapat memutus akses manajemen router.

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

Alamat gateway ditempatkan pada interface VLAN yang sesuai. Pastikan DHCP Server (jika digunakan) hanya melayani subnet VLAN yang benar.

<img width="720" height="420" alt="Gateway VLAN pada MikroTik" src="images/D.3-mikrotik-vlan-gateway.png" />

## D.4 Membatasi Komunikasi Antar-VLAN

VLAN memisahkan broadcast domain, tetapi tidak otomatis memblokir komunikasi Layer 3 antar-VLAN.

Buat kebijakan firewall sesuai kebutuhan:

- Izinkan koneksi dari masing-masing server menuju internet.
- Izinkan akses administrasi dari sumber yang ditentukan.
- Tolak komunikasi antar-VLAN yang tidak diperlukan.
- Izinkan layanan tertentu antar-VLAN hanya jika memang dibutuhkan.

<img width="720" height="420" alt="Firewall antar VLAN pada MikroTik" src="images/D.4-mikrotik-intervlan-firewall.png" />

## D.5 Mengulangi Pengujian pada Kedua Laptop

Setelah port access VLAN dikonfigurasi, hubungkan masing-masing laptop ke port yang telah ditentukan.

- Laptop 1 harus berada pada VLAN 10.
- Laptop 2 harus berada pada VLAN 20.

Periksa alamat IP yang diterima AlmaLinux dan pastikan gateway sesuai VLAN.

<img width="720" height="360" alt="Pengujian VLAN dari kedua server" src="images/D.5-vlan-test.png" />

---

# E. Konfigurasi Dual-WAN, Load Balancing, dan Failover

## E.1 Menguji Koneksi ISP Secara Terpisah

Sebelum load balancing dibuat, pastikan masing-masing ISP dapat terhubung ke internet secara mandiri.

Pengujian meliputi:

- Status interface WAN.
- IP Address dari masing-masing ISP.
- Gateway ISP.
- Koneksi ke tujuan internet.
- DNS resolution.

<img width="720" height="420" alt="Pengujian ISP 1 dan ISP 2" src="images/E.1-wan-connectivity.png" />

## E.2 Konsep Load Balancing

Load balancing digunakan untuk membagi koneksi keluar melalui dua ISP.

Salah satu metode yang dapat digunakan pada MikroTik RouterOS 7 adalah PCC (Per Connection Classifier). PCC mengelompokkan koneksi sehingga koneksi yang sama menggunakan jalur WAN yang konsisten.

Load balancing per-connection tidak berarti satu sesi unduhan otomatis memperoleh gabungan bandwidth kedua ISP. Pembagian dilakukan terhadap beberapa koneksi.

<img width="720" height="420" alt="Konfigurasi load balancing PCC" src="images/E.2-mikrotik-pcc.png" />

## E.3 Konsep Failover

Failover digunakan untuk mengalihkan koneksi ke ISP yang masih aktif ketika salah satu jalur mengalami gangguan.

Pemantauan jalur perlu memperhatikan keterjangkauan tujuan di luar jaringan lokal ISP, bukan hanya status kabel atau interface.

Rancangan pengujian:

1. ISP 1 dan ISP 2 aktif.
2. ISP 1 dinonaktifkan, ISP 2 tetap aktif.
3. ISP 1 dipulihkan, kemudian ISP 2 dinonaktifkan.
4. Kedua ISP dinonaktifkan.
5. Kedua ISP dipulihkan.

<img width="720" height="420" alt="Konfigurasi failover MikroTik" src="images/E.3-mikrotik-failover.png" />

## E.4 NAT untuk Akses Internet

Koneksi dari VLAN 10 dan VLAN 20 perlu memperoleh akses internet melalui mekanisme NAT yang sesuai dengan rancangan multi-WAN.

Pastikan aturan NAT dan routing konsisten dengan jalur WAN yang digunakan. Jangan membuat aturan masquerade yang saling bertentangan atau mengabaikan kebijakan routing PCC.

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

## F.2 Memeriksa Interface AlmaLinux

Jalankan:

```
ip -br link
ip -br addr
```

Identifikasi NIC yang terhubung ke bridge server pada Proxmox.

<img width="720" height="360" alt="Network interface AlmaLinux" src="images/F.2-almalinux-interface.png" />

## F.3 Mengatur IP Address

Alamat IP dapat diperoleh melalui DHCP dari MikroTik atau diatur secara statis.

Jika menggunakan IP statis, pastikan:

- IP sesuai subnet VLAN.
- Gateway sesuai interface VLAN MikroTik.
- DNS dapat dijangkau.
- Tidak terjadi konflik IP.

Periksa routing:

```
ip route
```

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

Jika koneksi IP berhasil tetapi DNS gagal, periksa konfigurasi DNS. Jika keduanya gagal, periksa gateway, VLAN, routing, NAT, dan status WAN.

<img width="720" height="360" alt="Pengujian koneksi internet AlmaLinux" src="images/F.4-almalinux-internet.png" />

---

# G. Instalasi dan Konfigurasi Web Server

## G.1 Instalasi Apache HTTP Server

Pada masing-masing AlmaLinux, jalankan:

```
sudo dnf install -y httpd
```

Aktifkan layanan:

```
sudo systemctl enable --now httpd
```

Periksa status:

```
sudo systemctl status httpd
```

<img width="720" height="360" alt="Status Apache HTTP Server" src="images/G.1-apache-status.png" />

## G.2 Membuat Halaman Web Pengujian

Buat halaman web sederhana:

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

Pada Server 2, ubah identitas menjadi `webserver-02` dan VLAN `20`.

<img width="720" height="360" alt="Halaman web Server 1" src="images/G.2-webserver-1.png" />

<img width="720" height="360" alt="Halaman web Server 2" src="images/G.2-webserver-2.png" />

## G.3 Mengatur Firewall AlmaLinux

Izinkan layanan HTTP:

```
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload
```

Jika HTTPS telah dikonfigurasi, izinkan layanan HTTPS:

```
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

Jangan membuka layanan administrasi seperti SSH ke seluruh internet tanpa pembatasan.

<img width="720" height="360" alt="Firewall HTTP AlmaLinux" src="images/G.3-almalinux-firewall.png" />

## G.4 Menguji Web Server dari Jaringan Lokal

Dari AlmaLinux:

```
curl -I http://localhost
```

Dari perangkat lain yang memiliki izin akses, uji alamat IP server sesuai VLAN.

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

Hal yang perlu diperiksa:

- Apakah WAN memperoleh public IP atau berada di belakang CGNAT.
- Apakah terdapat NAT tambahan pada modem/router ISP.
- Apakah alamat IP server tetap.
- Apakah firewall MikroTik mengizinkan koneksi yang diperlukan.
- Apakah HTTPS telah disiapkan.

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
- Pada port forwarding, akses masuk bergantung pada alamat publik dan jalur ISP yang digunakan.
- Jika kedua ISP mati, akses dari internet tidak tersedia.
- Load balancing PCC tidak menggabungkan dua ISP menjadi satu alamat IP publik.

---

# I. Pengujian Load Balancing, Failover, dan Ketersediaan Web

## I.1 Skenario 1 — Kedua ISP Aktif

Kondisi:

- ISP 1 aktif.
- ISP 2 aktif.
- Load balancing berjalan.

Pengujian:

1. Pastikan kedua interface WAN aktif.
2. Buat beberapa koneksi internet dari AlmaLinux.
3. Periksa trafik pada masing-masing interface WAN.
4. Uji akses web server dari jaringan eksternal.
5. Catat hasil pengujian.

<img width="720" height="420" alt="Kedua ISP aktif" src="images/I.1-both-isp-active.png" />

## I.2 Skenario 2 — Hanya ISP 1 Aktif

Kondisi:

- ISP 1 aktif.
- ISP 2 dinonaktifkan atau disimulasikan mengalami gangguan.

Pengujian:

1. Putuskan koneksi ISP 2 secara terkontrol.
2. Pastikan MikroTik mendeteksi gangguan.
3. Uji koneksi internet dari AlmaLinux.
4. Uji akses web dari jaringan eksternal.
5. Catat waktu pemulihan dan hasil pengujian.

<img width="720" height="420" alt="ISP 1 aktif dan ISP 2 mati" src="images/I.2-isp1-only.png" />

## I.3 Skenario 3 — Hanya ISP 2 Aktif

Kondisi:

- ISP 1 dinonaktifkan atau disimulasikan mengalami gangguan.
- ISP 2 aktif.

Ulangi prosedur pengujian dan catat hasilnya.

<img width="720" height="420" alt="ISP 2 aktif dan ISP 1 mati" src="images/I.3-isp2-only.png" />

## I.4 Skenario 4 — Kedua ISP Mati

Kondisi:

- ISP 1 mati.
- ISP 2 mati.

Pengujian:

1. Putuskan kedua koneksi WAN secara terkontrol.
2. Pastikan MikroTik mendeteksi kedua jalur tidak tersedia.
3. Uji akses internet dari AlmaLinux.
4. Uji akses domain publik dari perangkat eksternal.
5. Uji apakah web server masih dapat diakses dari jaringan lokal.

Hasil yang diharapkan: web server masih dapat berjalan dan diakses dari jaringan lokal selama server dan jaringan lokal aktif, tetapi tidak dapat diakses dari internet karena kedua jalur WAN tidak tersedia.

<img width="720" height="420" alt="Kedua ISP mati" src="images/I.4-both-isp-down.png" />

## I.5 Tabel Hasil Pengujian

| Skenario | ISP 1 | ISP 2 | Internet AlmaLinux | Akses Web dari Internet |
| --- | --- | --- | --- | --- |
| 1 | Aktif | Aktif | Catat hasil | Catat hasil |
| 2 | Aktif | Mati | Catat hasil | Catat hasil |
| 3 | Mati | Aktif | Catat hasil | Catat hasil |
| 4 | Mati | Mati | Tidak tersedia | Tidak tersedia |

> **Catatan:** isi hasil berdasarkan pengujian aktual. Jangan menyatakan berhasil sebelum pengujian dilakukan.

---

# J. Analisis dan Evaluasi

Analisis dilakukan berdasarkan hasil pengujian yang diperoleh.

Hal yang dievaluasi:

1. **Load Balancing** — apakah koneksi baru terbagi melalui ISP 1 dan ISP 2 sesuai kebijakan.
2. **Failover** — apakah koneksi berpindah ke ISP yang masih aktif ketika salah satu jalur mengalami gangguan.
3. **Recovery** — apakah jalur kembali normal setelah ISP dipulihkan.
4. **VLAN Segmentation** — apakah Server 1 dan Server 2 berada pada broadcast domain yang berbeda.
5. **Inter-VLAN Firewall** — apakah komunikasi yang tidak diizinkan berhasil diblokir.
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

---

# K. Kesimpulan

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

> **Catatan implementasi:** konfigurasi CLI MikroTik final belum dituliskan sebagai perintah siap tempel karena model MikroTik, jumlah port, nama interface, metode koneksi kedua ISP, dan kondisi konfigurasi router belum diketahui. Informasi tersebut harus diperiksa terlebih dahulu agar konfigurasi VLAN filtering dan dual-WAN tidak memutus akses manajemen router.
