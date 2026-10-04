[**(←) Back**](https://github.com/SyaifulKaromah/Manajemen-Pusat-Data/blob/main/README.md)

# **PROJECT --- Private Cloud Storage & Server Monitoring (AlmaLinux)**

**Nama** : M. Syaiful Karomah\
**NIM** : 09011282328111\
**Kelas** : SK7C\
**Mata Kuliah** : Manajemen Pusat Data

------------------------------------------------------------------------

## Informasi Sistem

  Parameter               Nilai
  ----------------------- ------------------------------
  Platform Virtualisasi   Proxmox VE
  OS Server               AlmaLinux
  Interface Server        `ens18`
  IP Address Server       `192.168.218.134/24`
  Web Server              Apache HTTP Server (`httpd`)
  Private Cloud           Nextcloud
  Database                MariaDB
  Monitoring              Netdata
  Port HTTP               `80`
  Port Database           `3306`
  Port Netdata            `19999`
  Akses Client            Web Browser dari Windows

> **Catatan:** alamat IP dapat berubah apabila AlmaLinux masih
> menggunakan DHCP. Gunakan hasil `ip a` terbaru apabila IP server
> berubah.

------------------------------------------------------------------------

## Tujuan Project

Project ini membangun sebuah **private cloud storage sederhana** pada
server AlmaLinux. File yang diunggah oleh pengguna disimpan pada storage
server pribadi, sedangkan Nextcloud menyediakan antarmuka web untuk
mengakses dan mengelola file.

Server juga dilengkapi **Netdata** untuk memonitor penggunaan CPU, RAM,
disk, network, dan service secara real-time.

Komponen utama:

-   **Apache HTTP Server** --- web server.
-   **Nextcloud** --- aplikasi private cloud/file storage.
-   **MariaDB** --- database backend Nextcloud.
-   **Netdata** --- monitoring dan dashboard server.
-   **AlmaLinux** --- sistem operasi server.

------------------------------------------------------------------------

## Topologi Jaringan

``` text
┌──────────────────────────┐
│      WINDOWS CLIENT      │
│                          │
│ Browser / Web Client     │
└────────────┬─────────────┘
             │
             │ HTTP
             ▼
┌────────────────────────────────────────────┐
│             PROXMOX VE                     │
│                                            │
│   ┌────────────────────────────────────┐   │
│   │           ALMALINUX SERVER         │   │
│   │         192.168.218.134            │   │
│   │                                    │   │
│   │  Apache :80                        │   │
│   │      │                             │   │
│   │      ▼                             │   │
│   │  Nextcloud                         │   │
│   │    ├── MariaDB                     │   │
│   │    └── Local File Storage          │   │
│   │                                    │   │
│   │  Netdata :19999                    │   │
│   └────────────────────────────────────┘   │
└────────────────────────────────────────────┘
```

------------------------------------------------------------------------

# A. Persiapan Server AlmaLinux

> Bagian ini dilakukan langsung pada VM AlmaLinux di Proxmox.
<img width="448" height="192" alt="image" src="https://github.com/user-attachments/assets/d5f47879-6e68-4408-a3b5-ceb54aa11bea" />

## A.1 Cek IP Address Server

``` bash
ip a
```

Pastikan interface `ens18` memiliki alamat IP yang dapat dijangkau oleh
client.

Contoh:

``` text
2: ens18: <BROADCAST,MULTICAST,UP,LOWER_UP>
    inet 192.168.218.134/24
```

<img width="1387" height="390" alt="image" src="https://github.com/user-attachments/assets/278f150c-c37b-4677-b25c-fa8dcb339bef" />


------------------------------------------------------------------------

## A.2 Cek Koneksi Internet

``` bash
ping -c 4 8.8.8.8
```

Kemudian:

``` bash
ping -c 4 google.com
```

Apabila keduanya berhasil, koneksi IP dan DNS server berfungsi.

<img width="1386" height="494" alt="image" src="https://github.com/user-attachments/assets/f7d669c1-438d-42d0-ae63-4e48f32bcbcf" />


------------------------------------------------------------------------

## A.3 Update Package

``` bash
sudo dnf update -y
```
<img width="1386" height="825" alt="image" src="https://github.com/user-attachments/assets/8753f276-e5c7-4619-914a-50b2d96c3b55" />

------------------------------------------------------------------------

## A.4 Cek Service yang Sedang Berjalan

``` bash
systemctl --type=service --state=running
```

Pada server yang digunakan, Apache sebelumnya sudah aktif sebagai
`httpd.service`.
<img width="1376" height="513" alt="image" src="https://github.com/user-attachments/assets/787adde1-8740-4329-96da-2ee5311c967c" />

------------------------------------------------------------------------

# B. Konfigurasi Apache HTTP Server

> Apache digunakan sebagai web server untuk menyediakan aplikasi
> Nextcloud kepada client.

## B.1 Install Apache

Jika Apache belum terpasang:

``` bash
sudo dnf install httpd -y
```

------------------------------------------------------------------------

## B.2 Aktifkan Apache

``` bash
sudo systemctl enable --now httpd
```

Verifikasi:

``` bash
sudo systemctl status httpd
```

Status yang diharapkan:

``` text
Active: active (running)
```

<img width="1384" height="602" alt="image" src="https://github.com/user-attachments/assets/a226aa6a-f957-42a4-8684-c16e98217a81" />


------------------------------------------------------------------------

## B.3 Verifikasi Port 80

``` bash
sudo ss -lntp | grep :80
```

Contoh hasil:

<img width="1376" height="145" alt="image" src="https://github.com/user-attachments/assets/cf96afc6-a6dd-4866-a88f-a17adf2b8853" />


Hal tersebut menunjukkan Apache telah mendengarkan koneksi pada port
`80`.

------------------------------------------------------------------------

## B.4 Buka HTTP pada Firewall

``` bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload
```

Verifikasi:

``` bash
sudo firewall-cmd --list-services
```

Pastikan terdapat:

``` text
http
```
<img width="1373" height="206" alt="image" src="https://github.com/user-attachments/assets/298a887d-c123-42f0-9ec8-d792f1e4a06a" />

------------------------------------------------------------------------

## B.5 Pengujian dari Client Windows

Buka browser pada Windows:

``` text
http://192.168.218.134
```

Apabila halaman Apache dapat dibuka, komunikasi client menuju web server
telah berhasil.

<img width="1920" height="1200" alt="image" src="https://github.com/user-attachments/assets/1c3d251b-9239-484f-a662-4aed39460585" />


------------------------------------------------------------------------

# C. Instalasi dan Konfigurasi MariaDB

> MariaDB digunakan sebagai database backend Nextcloud. File pengguna
> tetap disimpan pada storage server, sedangkan MariaDB menyimpan data
> aplikasi seperti akun, konfigurasi, metadata, dan informasi sharing.

## C.1 Install MariaDB

``` bash
sudo dnf install mariadb-server -y
```

------------------------------------------------------------------------

## C.2 Aktifkan MariaDB

``` bash
sudo systemctl enable --now mariadb
```

Verifikasi:

``` bash
sudo systemctl status mariadb
```

<img width="1385" height="834" alt="image" src="https://github.com/user-attachments/assets/48feacbb-9b5e-440a-9fb9-65b7d50fcd4f" />


------------------------------------------------------------------------

## C.3 Amankan Instalasi MariaDB

Jalankan:

``` bash
sudo mariadb-secure-installation
```

Ikuti pertanyaan keamanan yang tampil pada terminal. Simpan password
administrator database dengan aman.
<img width="1385" height="825" alt="image" src="https://github.com/user-attachments/assets/7fe8ebf1-ff36-490c-8f7a-a6095dcbc09a" />

------------------------------------------------------------------------

## C.4 Buat Database Nextcloud

Masuk ke MariaDB:

``` bash
sudo mariadb
```

Buat database:

``` sql
CREATE DATABASE nextcloud CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

Buat user database:

``` sql
CREATE USER 'nextclouduser'@'localhost' IDENTIFIED BY 'Passwd';
```

Berikan hak akses:

``` sql
GRANT ALL PRIVILEGES ON nextcloud.* TO 'nextclouduser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```
<img width="1390" height="563" alt="image" src="https://github.com/user-attachments/assets/4edbf6e0-c9f5-4d82-852e-e7e5a21d90cb" />


------------------------------------------------------------------------

## C.5 Verifikasi Database

``` bash
sudo mariadb -e "SHOW DATABASES;"
```

Pastikan terdapat:

``` text
nextcloud
```

<img width="1388" height="293" alt="image" src="https://github.com/user-attachments/assets/26334235-3fc5-4e00-a721-33e34f26d951" />


------------------------------------------------------------------------

# D. Instalasi PHP dan Modul Pendukung

> Nextcloud merupakan aplikasi PHP sehingga membutuhkan PHP beserta
> beberapa extension.

## D.1 Install PHP dan Extension

``` bash
sudo dnf install php php-cli php-fpm php-mysqlnd php-gd php-curl php-zip php-mbstring php-intl php-bcmath php-gmp php-process php-xml php-opcache -y
```

> Nama paket dapat berbeda tergantung versi AlmaLinux dan repository
> yang aktif. Jika ada paket yang tidak ditemukan, cek terlebih dahulu
> dengan `dnf search`.

------------------------------------------------------------------------

## D.2 Aktifkan PHP-FPM

``` bash
sudo systemctl enable --now php-fpm
```

Verifikasi:

``` bash
sudo systemctl status php-fpm
```

<img width="1383" height="538" alt="image" src="https://github.com/user-attachments/assets/bab7343e-e506-4aa1-9e58-6eaf1ba3f5ed" />


------------------------------------------------------------------------

## D.3 Verifikasi PHP

``` bash
php -v
```

<img width="1384" height="185" alt="image" src="https://github.com/user-attachments/assets/8db8377f-3244-40bc-bac0-a88e575f10c1" />


------------------------------------------------------------------------

# E. Instalasi Nextcloud

> Nextcloud menjadi aplikasi utama yang menyediakan akses private cloud
> storage melalui browser.

## E.1 Install Tool Download dan Ekstraksi

``` bash
sudo dnf install wget unzip -y
```

------------------------------------------------------------------------

## E.2 Download Nextcloud

Masuk ke direktori sementara:

``` bash
cd /tmp
```

Download paket Nextcloud dari sumber resmi. Gunakan versi stabil yang
tersedia saat praktikum.

Contoh pola perintah:

``` bash
wget https://download.nextcloud.com/server/releases/latest.zip
```

------------------------------------------------------------------------

## E.3 Extract Nextcloud

``` bash
unzip latest.zip
```

Pindahkan ke direktori Apache:

``` bash
sudo mv nextcloud /var/www/html/
```

------------------------------------------------------------------------

## E.4 Atur Ownership

``` bash
sudo chown -R apache:apache /var/www/html/nextcloud
```

Atur permission dasar:

``` bash
sudo find /var/www/html/nextcloud -type d -exec chmod 750 {} \;
sudo find /var/www/html/nextcloud -type f -exec chmod 640 {} \;
```

------------------------------------------------------------------------

## E.5 Konfigurasi SELinux

Pada AlmaLinux, SELinux perlu diperhatikan agar Apache dapat menulis ke
direktori yang diperlukan Nextcloud.

``` bash
sudo semanage fcontext -a -t httpd_sys_rw_content_t "/var/www/html/nextcloud/(config|data|apps)(/.*)?"
sudo restorecon -Rv /var/www/html/nextcloud
```

Jika perintah `semanage` belum tersedia:

``` bash
sudo dnf install policycoreutils-python-utils -y
```

Izinkan koneksi jaringan yang diperlukan oleh aplikasi web:

``` bash
sudo setsebool -P httpd_can_network_connect 1
sudo setsebool -P httpd_can_network_connect_db 1
```

------------------------------------------------------------------------

## E.6 Restart Apache dan PHP-FPM

``` bash
sudo systemctl restart httpd
sudo systemctl restart php-fpm
```

------------------------------------------------------------------------

## E.7 Akses Nextcloud dari Client

Pada Windows buka:

``` text
http://192.168.218.134/nextcloud
```

Halaman setup Nextcloud seharusnya tampil.

<img width="1920" height="1200" alt="image" src="https://github.com/user-attachments/assets/bf92270c-ebd7-4ae4-8158-15066e41176c" />


------------------------------------------------------------------------

## E.8 Konfigurasi Awal Nextcloud

Pada halaman setup:

``` text
Administrator Account
Username : admin
Password : ********

Database
Type     : MySQL/MariaDB
User     : nextclouduser
Password : ********
Database : nextcloud
Host     : localhost
```

<img width="1920" height="1200" alt="image" src="https://github.com/user-attachments/assets/6124c411-769b-4f7a-87d8-64185534b8fb" />

Kemudian selesaikan proses instalasi.

<img width="296" height="35" alt="image" src="https://github.com/user-attachments/assets/43daa2d8-3fa7-4b9d-b6a0-5d4bb4ecf33f" />


------------------------------------------------------------------------

## E.9 Verifikasi Dashboard Nextcloud

Setelah instalasi berhasil, login sebagai administrator.

Pastikan halaman **Files** dapat dibuka.

<img width="1920" height="1200" alt="image" src="https://github.com/user-attachments/assets/a1be8376-1fa8-4d70-a063-001a40409491" />


------------------------------------------------------------------------

# F. Konfigurasi Private Cloud Storage

## F.1 Membuka Manajemen Akun

Login ke Nextcloud menggunakan akun **administrator**.

Klik **ikon profil** pada pojok kanan atas, kemudian pilih:

```text
Accounts
```

Halaman manajemen akun juga dapat diakses langsung melalui:

```text
http://192.168.218.134/nextcloud/index.php/settings/users
```

Pada halaman **Accounts**, administrator dapat membuat dan mengelola akun pengguna yang akan menggunakan layanan private cloud.

<img width="1920" height="1200" alt="image" src="https://github.com/user-attachments/assets/67d75395-f615-4cf2-8fdb-d8179ae79e28" />

---

## F.2 Membuat User Client 1

Pada halaman **Accounts**, klik tombol:

```text
+ Akun baru
```

Kemudian buat akun pengguna pertama:

```text
Nama akun    : client01
Nama tampilan: Client 01
Password     : [password client01]
```

Jika tidak diperlukan, bagian email dan grup dapat dibiarkan kosong/default.

Setelah selesai, pastikan akun `client01` muncul pada daftar **Semua akun**.

<img width="1920" height="1200" alt="image" src="https://github.com/user-attachments/assets/f7dd3f1e-dbf3-4055-884f-a7ed06ff5410" />


---

## F.3 Membuat User Client 2

Klik kembali:

```text
+ Akun baru
```

Buat akun kedua:

```text
Nama akun    : client02
Nama tampilan: Client 02
Password     : [password client02]
```

Setelah selesai, halaman **Accounts** seharusnya menampilkan:

```text
admin
client01
client02
```

<img width="1920" height="1200" alt="image" src="https://github.com/user-attachments/assets/a95ba56e-43cb-4013-99df-2300651024ee" />


---

## F.4 Login sebagai Client 01

Logout dari akun administrator:

```text
Ikon Profil → Keluar
```

Kemudian login menggunakan:

```text
Nama akun : client01
Password  : [password client01]
```

Setelah berhasil login, buka aplikasi **Files / Berkas**.

<img width="1917" height="1199" alt="image" src="https://github.com/user-attachments/assets/3fa9b690-8d85-4395-aad5-47da8b708249" />

---

## F.5 Upload File Client 01

Pada halaman **Files / Berkas**, upload sebuah file pengujian.

Contoh:

```text
M. Syaiful Karomah - Modul Praktikum Mikroprosessor.pdf
```

Pastikan file berhasil muncul pada penyimpanan akun `client01`.

<img width="1920" height="1200" alt="image" src="https://github.com/user-attachments/assets/ea327fad-c8b5-475a-b40e-7fd4b393061d" />


---

## F.6 Pengujian Download File

Pilih file:

```text
M. Syaiful Karomah - Modul Praktikum Mikroprosessor.pdf
```

Kemudian lakukan **Download**.

Pastikan file berhasil tersimpan pada komputer Windows client.

<img width="449" height="232" alt="image" src="https://github.com/user-attachments/assets/b994f592-3ed0-4125-8fee-46ee90ca2e35" />


---

## F.7 Pengujian Isolasi Antar-User

Logout dari akun:

```text
client01
```

Kemudian login menggunakan:

```text
Nama akun : client02
Password  : [password client02]
```

Buka aplikasi **Files / Berkas**.

File:

```text
M. Syaiful Karomah - Modul Praktikum Mikroprosessor.pdf
```

seharusnya **tidak terlihat pada akun Client 02**, karena file tersebut merupakan file pribadi milik Client 01 dan belum dibagikan.

```text
┌───────────────┐
│   Client 01   │
│               │
│ file       ✔ │
└───────────────┘

        │
        │ Tidak dibagikan
        ▼

┌───────────────┐
│   Client 02   │
│               │
│ file        ✘ │
└───────────────┘
```

<img width="1920" height="1200" alt="image" src="https://github.com/user-attachments/assets/06ca6a6f-7c03-4ce2-9382-8e4ece96fc61" />


---

## F.8 Pengujian File Sharing

Login kembali sebagai `client01`.

Pilih file:

```text
M. Syaiful Karomah - Modul Praktikum Mikroprosessor.pdf
```

Kemudian gunakan fitur **Share / Bagikan** dan berikan akses kepada:

```text
client02
```

Setelah file dibagikan, login kembali sebagai `client02`.

File tersebut sekarang seharusnya dapat diakses oleh Client 02.

```text
Client 01
    │
    │ Share
    ▼
M. Syaiful Karomah - Modul Praktikum Mikroprosessor.pdf
    │
    ▼
Client 02 ✔
```

Pengujian ini menunjukkan bahwa file antar-user tetap terisolasi secara default, tetapi dapat dibagikan apabila pemilik memberikan hak akses.

<img width="1918" height="1200" alt="image" src="https://github.com/user-attachments/assets/191b7016-102d-4276-9962-e40e695e637c" />

<img width="1920" height="1200" alt="image" src="https://github.com/user-attachments/assets/011f0725-30c1-458e-a70b-079eb06b9f68" />

# G. Instalasi Netdata

> Netdata digunakan sebagai sistem monitoring server secara real-time. Dashboard Netdata dapat menampilkan penggunaan CPU, RAM, disk, network, serta berbagai metric sistem AlmaLinux.

## G.1 Install Dependency Dasar

Sebelum melakukan instalasi Netdata, install beberapa dependency dasar:

```bash
sudo dnf install -y epel-release curl wget git tar gcc make
```

Dependency tersebut digunakan untuk mendukung proses download dan instalasi Netdata pada AlmaLinux.

<!-- FOTO G.1 — Screenshot proses instalasi dependency dasar berhasil -->

---

## G.2 Download Script Instalasi Netdata

Instalasi Netdata dilakukan menggunakan **kickstart script**.

Terdapat dua metode yang dapat digunakan.

### Metode 1 — Menggunakan `wget`

Download script:

```bash
wget -O /tmp/netdata-kickstart.sh https://get.netdata.cloud/kickstart.sh
```

Kemudian jalankan:

```bash
sudo sh /tmp/netdata-kickstart.sh --dont-wait
```

### Metode 2 — Menggunakan `curl`

Sebagai alternatif, script dapat di-download menggunakan:

```bash
curl https://get.netdata.cloud/kickstart.sh > /tmp/netdata-kickstart.sh
```

Kemudian jalankan:

```bash
sudo sh /tmp/netdata-kickstart.sh --dont-wait
```

> Cukup gunakan **salah satu metode**, `wget` atau `curl`. Tidak perlu menjalankan keduanya.

Kickstart script akan mendeteksi sistem operasi dan melakukan proses instalasi Netdata beserta komponen yang dibutuhkan.

<img width="1384" height="825" alt="image" src="https://github.com/user-attachments/assets/0975bd4b-af68-4b48-9ef0-7af226ac3ecd" />


---

## G.3 Verifikasi Service Netdata

Setelah instalasi selesai, periksa status Netdata:

```bash
sudo systemctl status netdata
```

Status yang diharapkan:

```text
Active: active (running)
```

Jika service belum berjalan, aktifkan menggunakan:

```bash
sudo systemctl enable --now netdata
```

<img width="1390" height="832" alt="image" src="https://github.com/user-attachments/assets/52880a81-f4a8-4ede-8a54-7f21393ff9b0" />


---

## G.4 Verifikasi Port Netdata

Secara default dashboard Netdata dapat diakses melalui port:

```text
19999
```

Periksa apakah port tersebut sudah aktif:

```bash
sudo ss -lntp | grep 19999
```

Contoh hasil:

```text
LISTEN ... :19999 ...
```


<img width="1387" height="185" alt="image" src="https://github.com/user-attachments/assets/da532455-9866-468d-884b-f98cc88fca0d" />


---

## G.5 Konfigurasi Firewall

Izinkan koneksi menuju port Netdata:

```bash
sudo firewall-cmd --permanent --add-port=19999/tcp
sudo firewall-cmd --reload
```

Verifikasi:

```bash
sudo firewall-cmd --list-ports
```

Pastikan terdapat:

```text
19999/tcp
```


<img width="1388" height="206" alt="image" src="https://github.com/user-attachments/assets/01e3c703-e5db-427e-a557-adedfcd062a5" />


---

## G.6 Akses Dashboard Netdata

Dari browser pada Windows Client, akses:

```text
http://192.168.218.134:19999
```

Jika instalasi dan konfigurasi berhasil, dashboard Netdata akan tampil pada browser.

Dashboard tersebut dapat digunakan untuk memonitor beberapa resource server, antara lain:

- CPU Usage
- RAM Usage
- Disk Usage
- Disk I/O
- Network Traffic
- Process dan Service
- System Load

<img width="1920" height="1188" alt="image" src="https://github.com/user-attachments/assets/55915929-d9e3-4846-a773-0c94aaeb4c65" />
<img width="1920" height="1200" alt="image" src="https://github.com/user-attachments/assets/e6625f85-ec6c-4a42-875f-1a3aa7393e23" />


------------------------------------------------------------------------

# Alur Sistem

## Gambaran Umum

``` text
┌───────────────────────────────────────────────────────────────┐
│                       WINDOWS CLIENT                          │
│                                                               │
│  Browser                                                      │
│  ├── Nextcloud :80                                            │
│  └── Netdata   :19999                                         │
└───────────────────────┬───────────────────────────────────────┘
                        │
                        │ Network
                        ▼
┌───────────────────────────────────────────────────────────────┐
│                       ALMALINUX SERVER                         │
│                       192.168.218.134                          │
│                                                               │
│   Apache HTTP Server (:80)                                    │
│          │                                                    │
│          ▼                                                    │
│      Nextcloud                                                │
│       │      │                                                │
│       │      └──────────────► Local File Storage              │
│       │                                                       │
│       └─────────────────────► MariaDB                          │
│                                                               │
│   Netdata (:19999)                                            │
│       └── CPU / RAM / Disk / Network / Process Monitoring     │
└───────────────────────────────────────────────────────────────┘
```

------------------------------------------------------------------------

# Alur Akses Private Cloud

``` text
Windows Client
      │
      │ buka browser
      ▼
192.168.218.134/nextcloud
      │
      ▼
Apache HTTP Server
      │
      ▼
Nextcloud
      │
      ├── autentikasi user
      │
      ├── baca metadata ─────────► MariaDB
      │
      └── akses file ────────────► Storage AlmaLinux
```

------------------------------------------------------------------------

# Alur Upload File

``` text
Client
   │
   │ pilih file
   ▼
Browser
   │ HTTP
   ▼
Apache
   │
   ▼
Nextcloud
   │
   ├── simpan metadata ─────► MariaDB
   │
   └── simpan file ─────────► Storage Server
                               │
                               ▼
                          Disk AlmaLinux
```

------------------------------------------------------------------------

# Alur Isolasi User

``` text
                    NEXTCLOUD
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
      CLIENT 01                 CLIENT 02
          │                         │
          ▼                         ▼
     File milik 01              File milik 02
          │                         │
          └──── tidak saling ───────┘
                terlihat secara
                default
```

File antar-user hanya dapat diakses apabila diberikan hak akses/sharing
oleh pemilik atau administrator sesuai konfigurasi.

------------------------------------------------------------------------

# Alur Monitoring

``` text
Apache ────────┐
MariaDB ───────┤
PHP-FPM ───────┤
Disk ──────────┤
Network ───────┼──► AlmaLinux ──► Netdata ──► Dashboard Client
CPU ───────────┤
RAM ───────────┘
```

Netdata tidak menjadi media penyimpanan file pengguna. Netdata hanya
digunakan untuk mengamati kondisi dan penggunaan resource server.

------------------------------------------------------------------------

# Peran Setiap Service

  Service             Fungsi
  ------------------- -----------------------------------------
  Apache (`httpd`)    Menyediakan layanan web kepada client
  PHP/PHP-FPM         Menjalankan aplikasi Nextcloud
  Nextcloud           Antarmuka private cloud/file storage
  MariaDB             Menyimpan database aplikasi Nextcloud
  Storage AlmaLinux   Menyimpan file pengguna secara fisik
  Netdata             Monitoring resource dan performa server
  firewalld           Mengatur akses port/service jaringan

------------------------------------------------------------------------

# Troubleshooting

## Apache Tidak Bisa Diakses

Cek:

``` bash
sudo systemctl status httpd
sudo ss -lntp | grep :80
sudo firewall-cmd --list-all
```

------------------------------------------------------------------------

## Nextcloud Tidak Bisa Dibuka

Cek log Apache:

``` bash
sudo journalctl -u httpd --no-pager -n 50
```

Cek PHP-FPM:

``` bash
sudo systemctl status php-fpm
```

------------------------------------------------------------------------

## Database Gagal Terhubung

Cek MariaDB:

``` bash
sudo systemctl status mariadb
```

Coba login:

``` bash
mariadb -u nextclouduser -p
```

Kemudian:

``` sql
SHOW DATABASES;
```

------------------------------------------------------------------------

## Permission / SELinux Error

Cek status SELinux:

``` bash
getenforce
```

Cek context:

``` bash
ls -lZ /var/www/html/nextcloud
```

Jangan langsung menonaktifkan SELinux. Perbaiki ownership, permission,
dan SELinux context terlebih dahulu.

------------------------------------------------------------------------

## Netdata Tidak Bisa Diakses

Cek:

``` bash
sudo systemctl status netdata
sudo ss -lntp | grep 19999
sudo firewall-cmd --list-ports
```

------------------------------------------------------------------------

# Kesimpulan

Project ini mengimplementasikan server **private cloud storage**
menggunakan AlmaLinux pada lingkungan virtualisasi Proxmox.

Apache berfungsi sebagai web server, Nextcloud menyediakan antarmuka
pengelolaan file, MariaDB menyimpan database aplikasi, sedangkan file
pengguna disimpan pada storage server AlmaLinux. Setiap akun Nextcloud
memiliki ruang file masing-masing dan file pribadi tidak secara otomatis
dapat dilihat oleh pengguna lain.

Netdata digunakan untuk melakukan monitoring resource server secara
real-time sehingga administrator dapat mengamati penggunaan CPU, RAM,
disk, network, dan aktivitas sistem ketika layanan digunakan oleh
client.

Dengan demikian, project mencakup tiga aspek utama dalam pengelolaan
server:

``` text
Penyediaan Layanan
        +
Manajemen Penyimpanan
        +
Monitoring Infrastruktur
```

------------------------------------------------------------------------

# Referensi

Dokumentasi yang digunakan sebagai acuan teknis:

-   Apache HTTP Server Documentation
-   Nextcloud Administration Manual
-   MariaDB Documentation
-   Netdata Documentation
-   Red Hat / AlmaLinux Documentation

