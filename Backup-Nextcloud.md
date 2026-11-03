[**(←) Back**](README.md)

# **PROJECT — Backup & Disaster Recovery Nextcloud (AlmaLinux)**

**Nama** : M. Syaiful Karomah  
**NIM** : 09011282328111  
**Kelas** : SK7C  
**Mata Kuliah** : Manajemen Pusat Data

---

## Informasi Sistem

| Parameter | Nilai |
| --- | --- |
| Platform Virtualisasi | Proxmox VE 9.2.2 |
| Virtual Machine | VM 100 |
| OS Server | AlmaLinux 10.2 |
| IP Address Server | `192.168.218.134/24` |
| Web Server | Apache HTTP Server (`httpd`) |
| Private Cloud | Nextcloud 35.0.1 |
| Database | MariaDB 10.11.18 |
| Local Backup | Windows SMB Share |
| Cloud Backup | Google Drive |
| Backup Utility | Rclone 1.75.2 |
| Scheduler | systemd service dan timer |
| Direktori Nextcloud | `/var/www/html/nextcloud` |
| Direktori Backup | `/mnt/backup-nextcloud/backups` |
| Direktori Log | `/mnt/backup-nextcloud/logs` |
| Jadwal Backup | Setiap hari pukul 02.00 WIB |

> **Catatan:** konfigurasi IP dan nama share mengikuti lingkungan praktikum. Sesuaikan apabila diterapkan pada jaringan atau perangkat yang berbeda.

---

## Tujuan Project

Project ini mengembangkan sistem backup untuk layanan **private cloud Nextcloud** yang telah berjalan pada server AlmaLinux. Backup dilakukan untuk melindungi database dan file pengguna agar dapat dipulihkan apabila terjadi kerusakan atau kehilangan data.

Sistem menggunakan dua lokasi penyimpanan:

- **Local Backup** — folder `D:\Backup-Nextcloud` pada Windows yang diakses server AlmaLinux melalui SMB.
- **Cloud Backup** — Google Drive yang diakses menggunakan Rclone.

Proses backup dibuat otomatis menggunakan Bash Script dan systemd timer. Setiap hasil backup dilengkapi manifest dan checksum SHA-256 untuk membantu memeriksa integritas file.

Komponen utama:

- **AlmaLinux** — sistem operasi server.
- **Nextcloud** — aplikasi private cloud yang dicadangkan.
- **MariaDB** — database backend Nextcloud.
- **Windows SMB Share** — media penyimpanan backup lokal.
- **Rclone** — alat transfer dan verifikasi backup ke Google Drive.
- **systemd** — menjalankan backup secara terjadwal.

---

## Topologi Sistem

<img width="1680" height="1560" alt="topologi-backup-nextcloud" src="https://github.com/user-attachments/assets/b594bb73-bef6-40a7-bd44-f12bc475ca5f" />

**Catatan arsitektur:** penyimpanan lokal Windows berada pada laptop fisik yang sama dengan host virtualisasi. Penyimpanan ini terpisah secara logis, tetapi belum melindungi data dari kerusakan fisik laptop atau disk. Google Drive digunakan sebagai salinan off-site.

---

# A. Persiapan Penyimpanan Backup pada Windows

> Bagian ini dilakukan pada Windows host yang menjalankan VMware Workstation dan Proxmox.

## A.1 Membuat Direktori Backup

Buat folder khusus untuk menyimpan hasil backup. Folder yang digunakan adalah:

```
D:\Backup-Nextcloud
```

Folder khusus digunakan agar akses SMB tidak perlu diberikan ke seluruh drive `D:`.

<img width="349" height="468" alt="image" src="https://github.com/user-attachments/assets/261e8372-fa80-44ef-bdd9-fe660c82bec0" />

---

## A.2 Membuat Akun Khusus Backup

Buat akun lokal Windows dengan nama `ncbackup`. Akun ini digunakan oleh AlmaLinux ketika mengakses folder melalui SMB.

Pembuatan akun dilakukan melalui PowerShell:

```
New-LocalUser
```

Masukkan nama akun dan password ketika diminta. Password tidak perlu ditampilkan pada dokumentasi.

<img width="388" height="183" alt="Cuplikan layar 2026-11-01 134534" src="https://github.com/user-attachments/assets/443afdb4-99b9-4c4d-a978-fbba5a61ec9f" />

---

## A.3 Membagikan Folder Melalui SMB

Bagikan folder `D:\Backup-Nextcloud` dengan nama share:

```
Backup-Nextcloud
```

Berikan izin `Change` kepada akun `ncbackup`, kemudian hapus izin `Everyone` jika sebelumnya tersedia.

Dengan demikian, akses tulis ke share hanya diberikan kepada akun yang digunakan untuk proses backup.

<img width="440" height="270" alt="Cuplikan layar 2026-11-01 135338" src="https://github.com/user-attachments/assets/9499e3e4-ab52-4075-9de9-364ff5f0febc" />



---

## A.4 Mengatur NTFS Permission

Atur izin NTFS agar akun backup dapat membaca, menulis, dan mengubah file di dalam direktori backup.

```
icacls "D:\Backup-Nextcloud" /inheritance:r
icacls "D:\Backup-Nextcloud" /grant:r `
  "CAPUCHINO\ncbackup:(OI)(CI)M" `
  "BUILTIN\Administrators:(OI)(CI)F" `
  "NT AUTHORITY\SYSTEM:(OI)(CI)F"
```

Keterangan:

- `M` — Modify.
- `F` — Full Control.
- `(OI)(CI)` — izin diwariskan ke file dan subfolder.

Nama komputer/domain `CAPUCHINO` mengikuti perangkat praktikum.

<img width="262" height="209" alt="Cuplikan layar 2026-11-01 135357" src="https://github.com/user-attachments/assets/ff7ff152-c4d5-4525-8580-b55a75158fe3" />
<img width="383" height="156" alt="Cuplikan layar 2026-11-01 142016" src="https://github.com/user-attachments/assets/a92bc0e0-208a-4e7a-94a4-c91aebf6cd1c" />


---

## A.5 Membatasi Akses SMB Melalui Windows Firewall

Akses SMB menggunakan TCP port 445. Aturan firewall dibuat agar koneksi hanya diterima dari alamat IP AlmaLinux melalui interface VMnet8.

```
New-NetFirewallRule `
  -DisplayName "SMB Backup from AlmaLinux" `
  -Direction Inbound `
  -Protocol TCP `
  -LocalPort 445 `
  -RemoteAddress 192.168.218.134 `
  -LocalAddress 192.168.218.1 `
  -Action Allow `
  -Profile Any
```

Firewall tidak dinonaktifkan secara keseluruhan. Pembatasan alamat sumber dan tujuan digunakan untuk mengurangi paparan layanan SMB.

<img width="552" height="300" alt="Cuplikan layar 2026-11-01 140032" src="https://github.com/user-attachments/assets/b5d7c4a9-2af6-4766-a9ce-202ba01850f6" />


---

# B. Konfigurasi SMB pada AlmaLinux

> Bagian ini dilakukan pada terminal VM AlmaLinux.

## B.1 Instalasi CIFS Utilities

Install paket `cifs-utils` untuk mendukung mount SMB/CIFS.

```
sudo dnf install -y cifs-utils
```

Buat direktori mount:

```
sudo mkdir -p /mnt/backup-nextcloud
```

---

## B.2 Membuat File Kredensial SMB

Buat file kredensial yang hanya dapat dibaca oleh root.

```
sudo nano /root/.smb-backup-credentials
```

Isi file:

```
username=ncbackup
password=PASSWORD_AKUN_WINDOWS
domain=CAPUCHINO
```

Ganti nilai password dengan password akun Windows yang sebenarnya.

Atur permission:

```
sudo chmod 600 /root/.smb-backup-credentials
sudo chown root:root /root/.smb-backup-credentials
```

Permission `600` memastikan hanya root yang dapat membaca dan mengubah file kredensial.

<img width="640" height="137" alt="Cuplikan layar 2026-11-01 1405501" src="https://github.com/user-attachments/assets/9f296c3e-b833-4a6c-b86f-25586e3201cb" />


---

## B.3 Menguji Koneksi SMB

Uji koneksi TCP port 445 dari AlmaLinux menuju Windows.

```
nc -zv 192.168.218.1 445
```

Jika berhasil, koneksi TCP ke layanan SMB Windows dapat dijangkau.

Lakukan mount share:

```
sudo mount -t cifs //192.168.218.1/Backup-Nextcloud \
  /mnt/backup-nextcloud \
  -o credentials=/root/.smb-backup-credentials,vers=3.1.1
```

Periksa hasil mount:

```
findmnt /mnt/backup-nextcloud
df -h /mnt/backup-nextcloud
```

Uji izin tulis:

```
sudo touch /mnt/backup-nextcloud/test-smb.txt
sudo rm /mnt/backup-nextcloud/test-smb.txt
```

Buat folder backup dan log:

```
sudo mkdir -p /mnt/backup-nextcloud/backups
sudo mkdir -p /mnt/backup-nextcloud/logs
```

<img width="576" height="328" alt="image" src="https://github.com/user-attachments/assets/fbccaefe-dfeb-4235-ba0b-d09838849963" />


<img width="1279" height="155" alt="image" src="https://github.com/user-attachments/assets/87438a68-f858-477d-bef2-45dceb497035" />

<img width="640" height="322" alt="Cuplikan layar 2026-11-01 142122" src="https://github.com/user-attachments/assets/92a2dd5a-ff7b-465d-8cf6-a7c3fcb6ffc1" />


---

## B.4 Mengatur Mount Otomatis

Agar share dapat dipasang kembali setelah reboot, buat salinan konfigurasi `fstab`.

```
sudo cp /etc/fstab /etc/fstab.bak
```

Tambahkan baris berikut pada `/etc/fstab`:

```
//192.168.218.1/Backup-Nextcloud /mnt/backup-nextcloud cifs credentials=/root/.smb-backup-credentials,vers=3.1.1,_netdev,nofail,x-systemd.automount 0 0
```

Muat ulang systemd dan uji konfigurasi:

```
sudo systemctl daemon-reload
sudo umount /mnt/backup-nextcloud
sudo mount -a
```

Akses direktori untuk memicu automount:

```
ls -la /mnt/backup-nextcloud
findmnt /mnt/backup-nextcloud
```

Opsi `x-systemd.automount` membuat mount dipicu ketika direktori diakses. Opsi `_netdev` menandai mount sebagai bergantung pada jaringan, sedangkan `nofail` mencegah kegagalan mount menghalangi proses boot.

<img width="640" height="112" alt="Cuplikan layar 2026-11-01 143119" src="https://github.com/user-attachments/assets/509a10f9-6aa6-40aa-8e70-9d14d7aea07e" />


<img width="640" height="194" alt="Cuplikan layar 2026-11-01 143506" src="https://github.com/user-attachments/assets/52869b37-0721-4715-95c1-730915946446" />

---

# C. Pemeriksaan Nextcloud dan MariaDB

## C.1 Memeriksa Status Nextcloud

Sebelum backup, periksa status aplikasi menggunakan `occ`.

```
sudo runuser -u apache -- php \
  /var/www/html/nextcloud/occ status --output=json
```

Kondisi yang diharapkan:

- `installed: true`
- `maintenance: false`
- `needsDbUpgrade: false`

Status tersebut menunjukkan aplikasi terpasang, tidak sedang dalam maintenance mode, dan tidak membutuhkan upgrade database.

<img width="640" height="52" alt="Cuplikan layar 2026-11-01 1447401" src="https://github.com/user-attachments/assets/5370ff64-bd50-45ef-8504-e56b0951b944" />


---

## C.2 Memeriksa MariaDB

Periksa service MariaDB:

```
sudo systemctl status mariadb --no-pager
```

Periksa versi database dan keberadaan database Nextcloud:

```
sudo mariadb -NBe "SELECT VERSION(); SHOW DATABASES LIKE 'nextcloud';"
```

Pada lingkungan pengujian digunakan MariaDB 10.11.18 dan database `nextcloud`.

<img width="1248" height="413" alt="image" src="https://github.com/user-attachments/assets/ce677dfe-e4a2-4596-9049-0c380362417e" />



---

## C.3 Memeriksa Kemampuan Database Dump

Periksa versi `mariadb-dump`:

```
mariadb-dump --version
```

Uji dump struktur database tanpa menyimpan hasilnya:

```
sudo mariadb-dump --single-transaction --no-data nextcloud > /dev/null \
  && echo "Database dump: OK"
```

Seluruh 138 tabel pada database Nextcloud dalam pengujian menggunakan InnoDB. Opsi `--single-transaction` digunakan agar dump tabel InnoDB diambil menggunakan snapshot transaksi.

<img width="640" height="71" alt="Cuplikan layar 2026-11-01 143619" src="https://github.com/user-attachments/assets/43a027aa-bc1d-4fe7-8e3c-4cb80979b30f" />


---

# D. Konfigurasi Rclone dan Google Drive

## D.1 Instalasi Rclone

Install Rclone pada AlmaLinux:

```
sudo dnf install -y rclone
```

Periksa versi:

```
rclone version
```

Pada pengujian digunakan Rclone versi 1.75.2.

<img width="584" height="181" alt="image" src="https://github.com/user-attachments/assets/b682db42-2100-4ce3-8143-4df58be23dcc" />


---

## D.2 Membuat Remote Google Drive

Jalankan konfigurasi:

```
rclone config
```

Remote yang dibuat menggunakan parameter:

| Parameter | Nilai |
| --- | --- |
| Remote name | `gDrive` |
| Storage | Google Drive |
| Scope | Full access |
| Client ID | OAuth Client milik pengguna |
| Client Secret | OAuth Client milik pengguna |
| Service Account | Kosong |
| Advanced config | No |
| Auto config pada AlmaLinux | No |
| Shared Drive | No |

Karena AlmaLinux VM tidak menggunakan browser, otorisasi OAuth dilakukan melalui Windows dengan perintah `rclone authorize`. Token hasil otorisasi kemudian dimasukkan ke prompt `config_token>` pada AlmaLinux.

> **Penting:** Client Secret, access token, refresh token, dan isi file konfigurasi Rclone merupakan informasi rahasia. Jangan memasukkannya ke screenshot atau repository publik.

---

## D.3 Memeriksa Remote Google Drive

Periksa lokasi file konfigurasi:

```
rclone config file
```

Periksa remote:

```
rclone lsd gDrive:
```

Folder tujuan yang digunakan pada Google Drive adalah:

```
Bakcup-Nextcloud
```

Nama folder mengikuti folder yang sudah tersedia di akun Google Drive.

<img width="640" height="96" alt="Cuplikan layar 2026-11-01 155744" src="https://github.com/user-attachments/assets/1f23ea20-44da-4191-86ee-ce210f0e73cc" />


---

## D.4 Menyiapkan Konfigurasi Rclone untuk Root

Script backup berjalan menggunakan hak akses root. Konfigurasi Rclone awalnya dibuat oleh akun `user1-proxmox`, sehingga file konfigurasi disalin ke direktori root.

```
sudo mkdir -p /root/.config/rclone
sudo cp /home/user1-proxmox/.config/rclone/rclone.conf \
  /root/.config/rclone/rclone.conf
sudo chmod 600 /root/.config/rclone/rclone.conf
sudo chown root:root /root/.config/rclone/rclone.conf
```

Uji akses Google Drive sebagai root:

```
sudo rclone lsd gDrive:
```

<img width="1646" height="173" alt="image" src="https://github.com/user-attachments/assets/9fc11257-70c9-4e74-a02a-082a75222293" />


---

## D.5 Uji Upload dan Verifikasi Google Drive

Upload satu folder backup yang sudah tersedia:

```
sudo rclone copy \
  /mnt/backup-nextcloud/backups/20261101_144831 \
  gDrive:Bakcup-Nextcloud/20261101_144831 \
  --progress
```

Setelah transfer selesai, periksa kesesuaian file:

```
sudo rclone check \
  /mnt/backup-nextcloud/backups/20261101_144831 \
  gDrive:Bakcup-Nextcloud/20261101_144831 \
  --one-way
```

Hasil pengujian:

```
0 differences found
4 matching files
```

Hasil tersebut menunjukkan empat file pada folder backup lokal cocok dengan file yang ditemukan pada tujuan Google Drive.

<img width="640" height="150" alt="Cuplikan layar 2026-11-01 160323" src="https://github.com/user-attachments/assets/92a0f6e2-77e5-4f1a-b201-252e8f559661" />


---

# E. Pembuatan Script Backup Nextcloud

## E.1 Membuat File Script

Script backup dibuat pada:

```
/usr/local/sbin/backup_nextcloud.sh
```

Buat atau edit file:

```
sudo nano /usr/local/sbin/backup_nextcloud.sh
```

Script dijalankan sebagai root karena membutuhkan akses untuk membaca direktori Nextcloud, membuat arsip, mengelola mount SMB, dan menjalankan proses backup.

Atur kepemilikan dan permission:

```
sudo chown root:root /usr/local/sbin/backup_nextcloud.sh
sudo chmod 750 /usr/local/sbin/backup_nextcloud.sh
```

<img width="640" height="188" alt="Cuplikan layar 2026-11-01 144602" src="https://github.com/user-attachments/assets/a48ee133-c811-4d46-8214-d1101aa681c8" />


---

## E.2 Konfigurasi Parameter Backup

Parameter utama yang digunakan:

```
NC_DIR="/var/www/html/nextcloud"
NC_OCC="$NC_DIR/occ"
DB_NAME="nextcloud"

BACKUP_MOUNT="/mnt/backup-nextcloud"
EXPECTED_SOURCE="//192.168.218.1/Backup-Nextcloud"
BACKUP_ROOT="$BACKUP_MOUNT/backups"
LOG_DIR="$BACKUP_MOUNT/logs"
LOG_FILE="$LOG_DIR/backup.log"

RCLONE_REMOTE="gDrive:Bakcup-Nextcloud"
LOCK_FILE="/run/lock/backup_nextcloud.lock"
```

Keterangan:

- `NC_DIR` — direktori instalasi Nextcloud.
- `DB_NAME` — nama database yang dicadangkan.
- `BACKUP_MOUNT` — mount point SMB Windows.
- `BACKUP_ROOT` — lokasi penyimpanan hasil backup.
- `LOG_FILE` — lokasi catatan proses backup.
- `RCLONE_REMOTE` — folder tujuan Google Drive.
- `LOCK_FILE` — mencegah proses backup berjalan bersamaan.

<img width="640" height="400" alt="Cuplikan layar 2026-11-01 160748" src="https://github.com/user-attachments/assets/5203cfe6-f7fa-47be-bb84-f54fc5046a79" />


---

## E.3 Pemeriksaan Awal Script

Sebelum membuat backup, script melakukan beberapa pemeriksaan:

1. Memastikan script dijalankan sebagai root.
2. Memastikan direktori SMB dapat diakses.
3. Memastikan filesystem yang terpasang adalah CIFS.
4. Memastikan sumber mount sesuai dengan share Windows yang ditentukan.
5. Memastikan direktori backup dan log tersedia.
6. Memastikan lokasi backup dapat ditulis.
7. Memeriksa kapasitas penyimpanan yang tersedia.
8. Menggunakan `flock` untuk mencegah backup ganda.
9. Memeriksa status Nextcloud.
10. Memastikan Nextcloud tidak sedang maintenance dan tidak membutuhkan upgrade database.

Pemeriksaan tersebut mencegah script melanjutkan proses ketika lokasi penyimpanan atau kondisi aplikasi tidak sesuai.

---

## E.4 Proses Backup Database dan File

Setelah pemeriksaan awal berhasil, script membuat ID backup berdasarkan tanggal dan waktu.

Contoh:

```
20261101_161618
```

Selanjutnya script mengaktifkan maintenance mode:

```
run_occ maintenance:mode --on
```

Dump database dibuat menggunakan:

```
mariadb-dump \
  --single-transaction \
  --routines \
  --triggers \
  --events \
  --default-character-set=utf8mb4 \
  nextcloud | gzip -1
```

Direktori Nextcloud kemudian diarsipkan menggunakan `tar` dengan opsi ACL, extended attributes, SELinux metadata, dan numeric owner.

Hasil backup disimpan dalam struktur:

```
backups/
└── 20261101_161618/
    ├── manifest.txt
    ├── SHA256SUMS
    ├── database/
    │   └── nextcloud.sql.gz
    └── files/
        └── nextcloud-files.tar.gz
```

<img width="640" height="349" alt="Cuplikan layar 2026-11-01 161341" src="https://github.com/user-attachments/assets/8ab6550d-1cea-4d4f-a42d-1f839a6277ce" />


---

## E.5 Manifest dan SHA-256

Setelah database dan file berhasil diarsipkan, script memeriksa arsip:

```
gzip -t database/nextcloud.sql.gz
gzip -t files/nextcloud-files.tar.gz
tar -tzf files/nextcloud-files.tar.gz
```

Kemudian script membuat `manifest.txt` yang berisi informasi backup, antara lain:

- Backup ID dan waktu pembuatan.
- Hostname server.
- Versi Nextcloud.
- Versi MariaDB.
- Nama database.
- Direktori sumber.
- Ukuran arsip database dan file.

Checksum SHA-256 dibuat menggunakan:

```
sha256sum manifest.txt database/nextcloud.sql.gz files/nextcloud-files.tar.gz > SHA256SUMS
sha256sum -c SHA256SUMS
```

Pemeriksaan checksum digunakan untuk mendeteksi perubahan atau kerusakan file setelah proses backup.

<img width="513" height="125" alt="image" src="https://github.com/user-attachments/assets/72f7217d-aa3b-41d4-b7bd-43c3b2e4db7c" />


---

## E.6 Integrasi Upload ke Google Drive

Setelah backup lokal dan checksum selesai, script mengirim direktori backup ke Google Drive menggunakan:

```
rclone copy "$DEST" "$RCLONE_REMOTE/$RUN_ID" \
  --log-level INFO \
  --stats 30s
```

Setelah upload selesai, script menjalankan verifikasi:

```
rclone check "$DEST" "$RCLONE_REMOTE/$RUN_ID" --one-way
```

Apabila upload dan verifikasi berhasil, log mencatat:

```
BACKUP GOOGLE DRIVE BERHASIL DAN TERVERIFIKASI.
```

Apabila upload atau verifikasi gagal, script mencatat error dan mengembalikan status gagal. Backup lokal yang sudah selesai tetap dipertahankan agar salinan lokal tidak hilang hanya karena koneksi cloud bermasalah.

<img width="640" height="34" alt="Cuplikan layar 2026-11-01 155904" src="https://github.com/user-attachments/assets/a7968754-8346-465b-93ff-7c2457b869aa" />


---

## E.7 Cleanup dan Maintenance Mode

Script menggunakan fungsi `cleanup` dan `trap` untuk memastikan maintenance mode dimatikan setelah proses backup berakhir.

Perintah yang digunakan:

```
run_occ maintenance:mode --off
```

Jika proses backup gagal setelah maintenance mode aktif, fungsi cleanup tetap berusaha mematikan maintenance mode dan mencatat kode akhir proses.

<img width="505" height="402" alt="image" src="https://github.com/user-attachments/assets/7dd0091b-9609-4100-96c1-014fd79304c3" />

---

## E.8 Validasi Sintaks Script

Sebelum script dijalankan, periksa sintaks:

```
sudo bash -n /usr/local/sbin/backup_nextcloud.sh \
  && echo "Sintaks script: OK"
```

Hasil yang diharapkan:

```
Sintaks script: OK
```

<img width="627" height="129" alt="image" src="https://github.com/user-attachments/assets/dbf7ebcb-6010-4596-92ef-3e6bdca4cad4" />


---

# F. Pengujian Backup Manual

## F.1 Menjalankan Script Backup

Jalankan script secara manual:

```
sudo /usr/local/sbin/backup_nextcloud.sh
```

Script akan menjalankan pemeriksaan awal, mengaktifkan maintenance mode, membuat dump database, mengarsipkan direktori Nextcloud, membuat checksum, mengunggah hasil backup ke Google Drive, dan memverifikasi hasil transfer.

---

## F.2 Memantau Log Backup

Log dapat dipantau menggunakan:

```
sudo tail -f /mnt/backup-nextcloud/logs/backup.log
```

Tekan `Ctrl+C` untuk keluar dari tampilan pemantauan. Perintah tersebut tidak menghentikan proses backup.

Periksa bagian akhir log:

```
sudo tail -n 35 /mnt/backup-nextcloud/logs/backup.log
```

Salah satu hasil pengujian menunjukkan:

```
BACKUP GOOGLE DRIVE BERHASIL DAN TERVERIFIKASI.
========== BACKUP NEXTCLOUD SELESAI ==========
Maintenance mode disabled
Maintenance mode berhasil dimatikan.
Backup berakhir dengan kode: 0
```

<img width="640" height="191" alt="Cuplikan layar 2026-11-01 145058" src="https://github.com/user-attachments/assets/5bbf6465-2151-4eff-9265-5c6cbfd37bc1" />


---

## F.3 Memeriksa Status Nextcloud Setelah Backup

Setelah backup selesai, periksa kembali status Nextcloud:

```
sudo runuser -u apache -- php \
  /var/www/html/nextcloud/occ status --output=json
```

Hasil pengujian:

```
{
  "installed": true,
  "version": "35.0.1.1",
  "versionstring": "35.0.1",
  "maintenance": false,
  "needsDbUpgrade": false
}
```

Nilai `maintenance: false` menunjukkan maintenance mode telah berhasil dinonaktifkan dan aplikasi kembali siap digunakan.

<img width="640" height="349" alt="Cuplikan layar 2026-11-01 161341" src="https://github.com/user-attachments/assets/1f021687-7797-422b-a3a5-e371ddf540c7" />


---

# G. Penjadwalan Backup Otomatis

## G.1 Memeriksa Zona Waktu

Periksa zona waktu AlmaLinux:

```
timedatectl
```

Konfigurasi yang digunakan:

```
Time zone: Asia/Jakarta (WIB, +0700)
System clock synchronized: yes
NTP service: active
```

<img width="640" height="64" alt="Cuplikan layar 2026-11-01 1614161" src="https://github.com/user-attachments/assets/a6ab46ec-fd0e-4397-a57b-81e52f7389f2" />


---

## G.2 Membuat systemd Service

Buat file service:

```
sudo nano /etc/systemd/system/backup-nextcloud.service
```

Isi:

```
[Unit]
Description=Automated Nextcloud Backup to SMB and Google Drive
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/backup_nextcloud.sh
```

Service menggunakan `Type=oneshot` karena proses backup berjalan sampai selesai, kemudian berhenti.

<img width="638" height="400" alt="Cuplikan layar 2026-11-01 161437" src="https://github.com/user-attachments/assets/d1b42909-566e-4fed-a6b1-9b3165f09bb0" />

---

## G.3 Membuat systemd Timer

Buat file timer:

```
sudo nano /etc/systemd/system/backup-nextcloud.timer
```

Isi:

```
[Unit]
Description=Daily Nextcloud Backup Schedule

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true
Unit=backup-nextcloud.service

[Install]
WantedBy=timers.target
```

`OnCalendar=*-*-* 02:00:00` menjadwalkan backup setiap hari pukul 02.00. `Persistent=true` memungkinkan systemd mengejar jadwal yang terlewat ketika server kembali aktif.

<img width="640" height="400" alt="Cuplikan layar 2026-11-01 161501" src="https://github.com/user-attachments/assets/e3ec5c23-90b7-46f2-b658-ffe820856649" />

---

## G.4 Mengaktifkan Timer

Muat ulang konfigurasi systemd:

```
sudo systemctl daemon-reload
```

Aktifkan timer:

```
sudo systemctl enable --now backup-nextcloud.timer
```

Periksa jadwal:

```
systemctl list-timers backup-nextcloud.timer
```

Pada pengujian 1 November 2026, jadwal berikutnya ditampilkan pada 2 November 2026 pukul 02.00 WIB.

<img width="640" height="187" alt="Cuplikan layar 2026-11-01 161527" src="https://github.com/user-attachments/assets/b433787d-de0f-40e1-929e-dc824b8b8f9a" />

---

## G.5 Menguji Eksekusi Service

Jalankan service secara manual melalui systemd:

```
sudo systemctl start backup-nextcloud.service
```

Periksa status:

```
sudo systemctl status backup-nextcloud.service --no-pager
```

Hasil pengujian menunjukkan:

```
Active: inactive (dead)
ExecStart=... (code=exited, status=0/SUCCESS)
```

Status `inactive (dead)` merupakan kondisi normal karena service menggunakan `Type=oneshot`. Service selesai dan tidak berjalan terus-menerus. Keberhasilan ditunjukkan oleh `status=0/SUCCESS`.

Periksa timer kembali:

```
systemctl list-timers backup-nextcloud.timer
```

<img width="976" height="371" alt="image" src="https://github.com/user-attachments/assets/67ca3860-bf53-40f9-9351-4fcc6f66096e" />

---

# H. Verifikasi Backup pada Windows dan Google Drive

## H.1 Memeriksa Struktur Backup Lokal

Pada Windows, buka:

```
D:\Backup-Nextcloud\backups
```

Contoh struktur backup:

```
20261101_144831
├── manifest.txt
├── SHA256SUMS
├── database
│   └── nextcloud.sql.gz
└── files
    └── nextcloud-files.tar.gz
```

Pada pengujian, direktori backup pertama berisi tiga file dengan total ukuran sekitar 537.791.657 byte.

<img width="1920" height="1200" alt="image" src="https://github.com/user-attachments/assets/32faf310-f119-490c-86e1-5c0dd769a566" />

---

## H.2 Memeriksa SHA-256 dari Windows

Checksum file juga diperiksa dari Windows menggunakan PowerShell:

```
Get-FileHash "D:\Backup-Nextcloud\backups\20261101_144831\manifest.txt" -Algorithm SHA256
Get-FileHash "D:\Backup-Nextcloud\backups\20261101_144831\database\nextcloud.sql.gz" -Algorithm SHA256
Get-FileHash "D:\Backup-Nextcloud\backups\20261101_144831\files\nextcloud-files.tar.gz" -Algorithm SHA256
```

Nilai hash dibandingkan dengan file `SHA256SUMS`. Pada pengujian, ketiga file dinyatakan valid.

<img width="640" height="198" alt="Cuplikan layar 2026-11-01 145414" src="https://github.com/user-attachments/assets/f3e5acb5-b859-4125-a1d4-f7a0d3eec465" />

---

## H.3 Memeriksa Backup pada Google Drive

Folder cloud yang digunakan:

```
Bakcup-Nextcloud
```

Untuk melihat daftar folder:

```
sudo rclone lsd gDrive:Bakcup-Nextcloud
```

Untuk memeriksa isi salah satu backup:

```
sudo rclone ls gDrive:Bakcup-Nextcloud/20261101_161618
```

<img width="991" height="171" alt="image" src="https://github.com/user-attachments/assets/b7d16f4b-26e2-47a3-ba90-e1042826d1f5" />


---

# I. Simulasi Pemulihan (Restore Test)

> Pengujian dilakukan pada direktori sementara dan database pengujian. Database produksi `nextcloud` tidak ditimpa, dihapus, atau digunakan sebagai target import.

## I.1 Menyiapkan Direktori Restore

Buat direktori sementara:

```
sudo mkdir -p /tmp/nextcloud-restore-test
```

Direktori ini digunakan sebagai lokasi ekstraksi arsip agar file produksi tetap aman.

---

## I.2 Mengekstrak Arsip Nextcloud

Ekstrak arsip file:

```
sudo tar -xzpf \
  /mnt/backup-nextcloud/backups/20261101_144831/files/nextcloud-files.tar.gz \
  -C /tmp/nextcloud-restore-test
```

Periksa file konfigurasi:

```
sudo ls -l \
  /tmp/nextcloud-restore-test/nextcloud/config/config.php
```

Keberadaan `config.php` menunjukkan bahwa file konfigurasi Nextcloud ikut tersimpan dalam arsip.

<img width="640" height="400" alt="Cuplikan layar 2026-11-01 150037" src="https://github.com/user-attachments/assets/e61b562d-3828-42de-a044-f8622e5d5d03" />

---

## I.3 Membandingkan Direktori Data

Bandingkan direktori data produksi dengan hasil ekstraksi:

```
sudo diff -qr \
  /var/www/html/nextcloud/data \
  /tmp/nextcloud-restore-test/nextcloud/data
```

Pada pengujian, perintah tidak menampilkan perbedaan. Hal tersebut menunjukkan isi kedua direktori data identik berdasarkan pemeriksaan `diff`.

Perbedaan nilai `maintenance` pada `config.php` dapat terjadi karena arsip dibuat ketika maintenance mode aktif, kemudian maintenance mode dimatikan kembali oleh fungsi cleanup setelah backup selesai.

<img width="1870" height="66" alt="image" src="https://github.com/user-attachments/assets/5e92ac55-0c47-4a17-badb-dd83cf9a129f" />


---

## I.4 Memvalidasi Arsip Database

Periksa integritas file database:

```
sudo gzip -t \
  /mnt/backup-nextcloud/backups/20261101_144831/database/nextcloud.sql.gz
```

File yang valid tidak menghasilkan pesan error dari gzip.

---

## I.5 Membuat Database Pengujian

Buat database terpisah:

```
sudo mariadb -e "CREATE DATABASE nextcloud_restore_test;"
```

Import dump ke database pengujian:

```
sudo bash -o pipefail -c \
  'zcat /mnt/backup-nextcloud/backups/20261101_144831/database/nextcloud.sql.gz | mariadb nextcloud_restore_test'
```

Database `nextcloud_restore_test` digunakan agar proses import tidak mengubah database produksi `nextcloud`.

<img width="1873" height="293" alt="image" src="https://github.com/user-attachments/assets/999db5b8-5066-43d8-8456-2f862614bedb" />


---

## I.6 Memeriksa Jumlah Tabel

Hitung jumlah tabel hasil restore:

```
sudo mariadb -NBe "
SELECT COUNT(*)
FROM information_schema.tables
WHERE table_schema = 'nextcloud_restore_test'
AND table_type = 'BASE TABLE';
"
```

Bandingkan dengan database produksi:

```
sudo mariadb -NBe "
SELECT table_schema, COUNT(*)
FROM information_schema.tables
WHERE table_schema IN ('nextcloud','nextcloud_restore_test')
AND table_type = 'BASE TABLE'
GROUP BY table_schema;
"
```

Hasil pengujian:

| Database | Jumlah Tabel |
| --- | ---: |
| `nextcloud` | 138 |
| `nextcloud_restore_test` | 138 |

Jumlah tabel yang sama menunjukkan seluruh struktur tabel berhasil diimpor pada database pengujian.

<img width="660" height="203" alt="image" src="https://github.com/user-attachments/assets/fcd716ac-eba1-4961-98bc-1b99a1570594" />


---

## I.7 Membersihkan Lingkungan Pengujian

Setelah pengujian selesai, hapus database pengujian:

```
sudo mariadb -e "DROP DATABASE nextcloud_restore_test;"
```

Hapus direktori sementara:

```
sudo rm -rf /tmp/nextcloud-restore-test
```

Penghapusan hanya dilakukan terhadap database dan direktori pengujian, bukan database maupun direktori produksi.

<img width="1907" height="86" alt="image" src="https://github.com/user-attachments/assets/0cc20ffd-96dd-4f50-b2c5-d859da928970" />

---

## I.8 Hasil Restore Test

| Pengujian | Hasil |
| --- | --- |
| Ekstraksi arsip Nextcloud | Berhasil |
| File `config.php` tersedia | Berhasil |
| Perbandingan direktori data | Tidak ditemukan perbedaan |
| Validasi gzip database | Berhasil |
| Import database pengujian | Berhasil |
| Jumlah tabel hasil restore | 138 tabel |
| Database produksi | Tidak diubah |
| Pembersihan database pengujian | Berhasil |

Restore test membuktikan bahwa arsip file dan dump database dapat dibaca serta dipulihkan ke lingkungan pengujian.

> **Batas pengujian:** simulasi ini belum termasuk full disaster recovery. Belum dilakukan pemulihan seluruh layanan Nextcloud ke VM pengganti atau pemulihan setelah kehilangan VM produksi.

---

# J. Hasil Implementasi

## J.1 Daftar Backup yang Dihasilkan

Pada pengujian tanggal 1 November 2026, terdapat tiga direktori backup:

| Backup ID | Keterangan |
| --- | --- |
| `20261101_144831` | Backup awal dan bahan restore test |
| `20261101_161017` | Pengujian integrasi Google Drive |
| `20261101_161618` | Pengujian melalui systemd service |

Total penggunaan direktori backup lokal pada saat pemeriksaan adalah sekitar 1,6 GB.

<img width="640" height="400" alt="Cuplikan layar 2026-11-01 162726" src="https://github.com/user-attachments/assets/7563e217-e7e8-4df1-91fb-c0c78832d61c" />

<img width="1598" height="1003" alt="image" src="https://github.com/user-attachments/assets/cd48cfae-4477-4497-9d13-04461dab1464" />


---

## J.2 Ringkasan Hasil Pengujian

| No. | Pengujian | Hasil |
| ---: | --- | --- |
| 1 | Koneksi SMB Windows | Berhasil |
| 2 | Mount SMB pada AlmaLinux | Berhasil |
| 3 | Automount setelah reboot | Berhasil |
| 4 | Rclone terhubung ke Google Drive | Berhasil |
| 5 | Backup database | Berhasil |
| 6 | Backup direktori Nextcloud | Berhasil |
| 7 | Pembuatan checksum SHA-256 | Berhasil |
| 8 | Upload ke Google Drive | Berhasil |
| 9 | Verifikasi cloud | 4 file cocok, 0 perbedaan |
| 10 | Eksekusi systemd service | `0/SUCCESS` |
| 11 | Penjadwalan systemd timer | Aktif |
| 12 | Restore file ke direktori sementara | Berhasil |
| 13 | Restore database pengujian | Berhasil |
| 14 | Full disaster recovery | Belum diuji |
| 15 | Retensi otomatis | Belum diterapkan |
| 16 | Simulasi ransomware | Belum dilakukan |

---

# Alur Sistem

## Alur Backup Otomatis

<img width="1680" height="2020" alt="image" src="https://github.com/user-attachments/assets/b7c087e2-922b-40a5-be28-4804664bef2c" />


Hasil backup lokal disimpan pada SMB Share Windows, kemudian salinan yang sama dikirim ke Google Drive dan diverifikasi.

---

# Peran Setiap Komponen

| Komponen | Fungsi |
| --- | --- |
| AlmaLinux VM | Server yang menjalankan Nextcloud dan script backup |
| Nextcloud | Aplikasi private cloud yang dicadangkan |
| MariaDB | Database backend Nextcloud |
| Bash Script | Pemeriksaan awal, backup, manifest, checksum, dan upload |
| Windows SMB Share | Penyimpanan backup lokal |
| Rclone | Transfer dan verifikasi backup ke Google Drive |
| Google Drive | Salinan backup off-site |
| systemd service dan timer | Menjalankan backup otomatis setiap hari pukul 02.00 WIB |

---

# Troubleshooting

## SMB Tidak Dapat Diakses

Periksa koneksi port 445:

```
nc -zv 192.168.218.1 445
```

Periksa mount:

```
findmnt /mnt/backup-nextcloud
```

Periksa permission file kredensial:

```
sudo ls -l /root/.smb-backup-credentials
```

Pastikan share Windows, akun `ncbackup`, permission, dan firewall sudah benar.

---

## Rclone Tidak Menemukan Remote

Jika muncul pesan remote `gDrive` tidak ditemukan ketika menggunakan `sudo`, periksa konfigurasi root:

```
sudo rclone lsd gDrive:
```

Pastikan file konfigurasi root tersedia:

```
sudo ls -l /root/.config/rclone/rclone.conf
```

Jangan menampilkan isi file konfigurasi karena berisi token OAuth.

---

## Backup Gagal

Periksa log:

```
sudo tail -n 50 /mnt/backup-nextcloud/logs/backup.log
```

Periksa status Nextcloud:

```
sudo runuser -u apache -- php \
  /var/www/html/nextcloud/occ status --output=json
```

Pastikan maintenance mode kembali `false` sebelum menjalankan backup berikutnya.

---

## systemd Service Berstatus Inactive

Periksa:

```
sudo systemctl status backup-nextcloud.service --no-pager
```

Service `Type=oneshot` memang kembali ke `inactive (dead)` setelah proses selesai. Periksa `status=0/SUCCESS` untuk memastikan eksekusi berhasil.

---

# Kesimpulan

Implementasi backup Nextcloud berhasil dilakukan menggunakan penyimpanan lokal Windows melalui SMB dan penyimpanan cloud Google Drive melalui Rclone.

Proses backup mencakup database MariaDB, direktori Nextcloud, manifest, serta checksum SHA-256. Hasil backup lokal dikirim ke Google Drive dan diverifikasi menggunakan `rclone check`. Penjadwalan otomatis dibuat menggunakan systemd timer setiap hari pukul 02.00 WIB.

Pengujian menunjukkan bahwa backup manual dan eksekusi melalui systemd berhasil. Verifikasi cloud menghasilkan empat file cocok tanpa perbedaan. Restore test juga berhasil dilakukan pada direktori sementara dan database pengujian yang berisi 138 tabel, tanpa mengubah database produksi.

Dengan demikian, mekanisme backup lokal, backup cloud, pemeriksaan integritas, penjadwalan, dan pemulihan komponen telah berhasil diuji. Pengembangan berikutnya yang masih diperlukan adalah penerapan retensi otomatis, simulasi ransomware, serta pengujian full disaster recovery pada lingkungan pengganti.

```
Backup Lokal (SMB)
        +
Backup Cloud (Google Drive)
        +
Verifikasi Integritas & Restore Test
```

---

# Referensi

Dokumentasi yang digunakan sebagai acuan teknis:

- [Nextcloud Administration Manual](https://docs.nextcloud.com/server/latest/admin_manual/)
- [MariaDB Documentation](https://mariadb.com/kb/en/documentation/)
- [Rclone Documentation](https://rclone.org/docs/)
- [Rclone Google Drive](https://rclone.org/drive/)
- [systemd.timer Manual](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html)
- [AlmaLinux Documentation](https://docs.almalinux.org/)
