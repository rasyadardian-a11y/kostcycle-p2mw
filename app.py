import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import hashlib

# Menggunakan v4 untuk skema tabel baru dengan otentikasi akun dan tanpa kolom alamat asal kos
conn = sqlite3.connect('kostcycle_v4.db', check_same_thread=False)
c = conn.cursor()

# Tabel users sekarang memiliki kolom password enkripsi, nomor telepon, dan role akses
c.execute('''CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY, 
                password TEXT,
                phone TEXT,
                points INTEGER DEFAULT 0,
                role TEXT DEFAULT 'mahasiswa')''')

# Tabel transaksi drop-off mandiri (tanpa kolom alamat kosan asal)
c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                username TEXT, 
                trash_type TEXT, 
                weight REAL, 
                points_earned INTEGER, 
                status TEXT DEFAULT 'Menunggu Drop-off',
                date TEXT)''')

# Tabel riwayat penukaran hadiah
c.execute('''CREATE TABLE IF NOT EXISTS redemptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                reward_item TEXT,
                points_spent INTEGER,
                date TEXT)''')
conn.commit()

def hash_password(password):
    """Mengenkripsi password menggunakan algoritma SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

# Membuat akun Admin bawaan jika belum ada di database
admin_username = "admin"
c.execute("SELECT * FROM users WHERE username=?", (admin_username,))
if not c.fetchone():
    hashed_admin_pw = hash_password("admin123")
    c.execute("INSERT INTO users (username, password, phone, points, role) VALUES (?, ?, ?, 0, 'admin')", 
              (admin_username, hashed_admin_pw, "08123456789"))
    conn.commit()

PRICING = {
    "Tembaga (Kabel/Alat Rusak)": 15000,    # 1 kg = 15.000 poin
    "Sampah Elektronik (E-Waste)": 6000,    # Charger, headset, komponen elektronik rusak
    "Minyak Jelantah (Sisa Masak)": 4000,   # Sisa minyak goreng ramah lingkungan
    "Aluminium (Kaleng Minuman)": 3000,     # Kaleng soda, minuman isotonic
    "Kardus Bekas Paket": 2000,             # Kardus sisa belanja online mahasiswa
    "Kertas / Buku Bekas Tugas": 1500,       # Buku tulis, kertas ujian lama
    "Botol Kaca (Sirup/Kecap)": 1500,        # Botol kaca utuh
    "Plastik/Pet (Botol Mineral)": 1200     # Botol plastik bening
}

REWARDS = {
    "Saldo E-Wallet (OVO/GoPay/Dana) Rp 5.000": 50.000,
    "Saldo E-Wallet (OVO/GoPay/Dana) Rp 10.000": 100.000,
    "Voucher Makan Kantin Kampus Rp 5.000": 45.000,
    "Voucher Cetak/Print Tugas 10 Lembar": 30.000,
    "Token Listrik Prabayar Rp 20.000": 20.0000
}

st.set_page_config(page_title="KostCycle - Drop-off Mandiri Berbasis Akun", page_icon="♻️", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #1B5E20;'>♻️ KostCycle Portal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.1em;'>Silakan Masuk atau Daftarkan Akun Mahasiswa Anda untuk Mengumpulkan Poin Lingkungan</p>", unsafe_allow_html=True)
    
    # Tab Navigasi Otentikasi
    tab_login, tab_register = st.tabs(["🔐 Masuk Akun", "📝 Daftar Akun Baru"])
    
    with tab_login:
        login_user = st.text_input("Username / NIM:", placeholder="Masukkan Username Anda", key="login_user").strip()
        login_pass = st.text_input("Password:", type="password", placeholder="Masukkan Password Anda", key="login_pass")
        
        if st.button("Masuk", use_container_width=True):
            if login_user and login_pass:
                hashed_pw = hash_password(login_pass)
                c.execute("SELECT username, role FROM users WHERE username=? AND password=?", (login_user, hashed_pw))
                result = c.fetchone()
                
                if result:
                    st.session_state.logged_in = True
                    st.session_state.username = result[0]
                    st.session_state.role = result[1]
                    st.success(f"Selamat Datang Kembali, {result[0]}!")
                    st.rerun()
                else:
                    st.error("Username atau Password salah. Silakan periksa kembali.")
            else:
                st.warning("Mohon isi seluruh bidang login.")
                
    with tab_register:
        reg_user = st.text_input("Buat Username / NIM:", placeholder="Contoh: Budi_G6412", key="reg_user").strip()
        reg_phone = st.text_input("Nomor WhatsApp (Aktif untuk E-Wallet):", placeholder="Contoh: 0812xxxxxxxx", key="reg_phone").strip()
        reg_pass = st.text_input("Buat Password Akun:", type="password", placeholder="Minimal 6 Karakter", key="reg_pass")
        reg_pass_conf = st.text_input("Konfirmasi Password:", type="password", placeholder="Masukkan ulang password Anda", key="reg_pass_conf")
        
        if st.button("Daftarkan Akun", use_container_width=True):
            if reg_user and reg_phone and reg_pass and reg_pass_conf:
                if reg_pass != reg_pass_conf:
                    st.error("Konfirmasi password tidak cocok.")
                elif len(reg_pass) < 6:
                    st.error("Password harus minimal 6 karakter demi keamanan.")
                else:
                    # Cek apakah username sudah digunakan
                    c.execute("SELECT * FROM users WHERE username=?", (reg_user,))
                    if c.fetchone():
                        st.error("Username / NIM sudah terdaftar. Silakan gunakan username lain atau langsung masuk.")
                    else:
                        hashed_reg_pw = hash_password(reg_pass)
                        c.execute("INSERT INTO users (username, password, phone, points, role) VALUES (?, ?, ?, 0, 'mahasiswa')",
                                  (reg_user, hashed_reg_pw, reg_phone))
                        conn.commit()
                        st.success("🎉 Pendaftaran berhasil! Silakan masuk menggunakan tab Masuk Akun di atas.")
            else:
                st.warning("Mohon lengkapi seluruh formulir registrasi.")

else:
    # Sidebar Informasi Akun Pengguna
    st.sidebar.image("https://img.icons8.com/clouds/100/000000/recycle-sign.png", width=100)
    st.sidebar.title("KostCycle Menu")
    st.sidebar.markdown(f"👤 **Pengguna:** `{st.session_state.username}`")
    
    # Ambil poin user terbaru dari database secara real-time
    c.execute("SELECT points FROM users WHERE username=?", (st.session_state.username,))
    active_points = c.fetchone()[0]
    st.sidebar.markdown(f"🪙 **Poin Aktif Anda:** `{active_points} Poin`")
    st.sidebar.markdown("---")
    
    # Menu Navigasi Berdasarkan Role Akun
    if st.session_state.role == "admin":
        menu = [
            "👑 KostCycle Station (Admin)",
            "💰 Informasi Konversi Sampah"
        ]
    else:
        menu = [
            "🌱 Daftarkan Drop-off (Mahasiswa)", 
            "🎁 Tukar Poin Reward", 
            "💰 Informasi Konversi Sampah"
        ]
        
    choice = st.sidebar.selectbox("Pilih Layanan:", menu)
    
    # Tombol Logout di paling bawah sidebar
    st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
    if st.sidebar.button("🔓 Keluar Aplikasi", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.rerun()

    # Header Kampanye Utama
    st.markdown("<h1 style='text-align: center; color: #1B5E20;'>♻️ KostCycle: Gerakan Drop-off Mandiri</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.25em; font-weight: bold; color: #2E7D32;'>\"Jangan Buang Sampahmu, Tabung di KostCycle Hub & Tukarkan dengan Hadiah!\"</p>", unsafe_allow_html=True)
    st.markdown("---")

    if choice == "🌱 Daftarkan Drop-off (Mahasiswa)":
        st.header("📝 Daftarkan Rencana Penyerahan Sampah")
        st.write("Kumpulkan dan pilah sampahmu di kosan secara mandiri. Daftarkan rencana penyerahanmu di bawah ini, lalu bawa sampahmu ke **KostCycle Hub (Stasiun Pengumpulan)** untuk ditimbang bersama tim kami!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Menggunakan akun login secara otomatis, tidak perlu memasukkan nama atau alamat lagi!
            st.text_input("Akun Mahasiswa Pengirim:", value=st.session_state.username, disabled=True)
            trash_type = st.selectbox("Pilih Jenis Sampah yang Anda Bawa:", list(PRICING.keys()))
            
        with col2:
            weight = st.number_input("Estimasi Berat Sampah yang Dibawa (Kg / Liter untuk Jelantah):", min_value=0.1, step=0.1, value=1.0)
            
            # Kalkulasi Estimasi Poin
            points_to_earn = int(weight * PRICING[trash_type])
            st.info(f"Estimasi Nilai Reward: **{points_to_earn} Poin**")
        
        if st.button("Kirim Rencana Drop-off", use_container_width=True):
            date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
            # Simpan transaksi baru tanpa alamat asal kos
            c.execute('''INSERT INTO transactions (username, trash_type, weight, points_earned, status, date) 
                         VALUES (?, ?, ?, ?, 'Menunggu Drop-off', ?)''',
                      (st.session_state.username, trash_type, weight, points_to_earn, date_now))
            conn.commit()
            
            st.success("✅ Rencana drop-off berhasil dikirim! Silakan bawa sampahmu ke KostCycle Hub di area kampus.")
            st.toast("Rencana drop-off berhasil tercatat!")
            st.rerun()

    elif choice == "🎁 Tukar Poin Reward":
        st.header("🎁 Penukaran Poin & Reward")
        st.write("Tukarkan poin aksi peduli lingkunganmu dengan voucher digital dan kebutuhan harian anak kos.")
        
        st.info(f"Poin Anda saat ini: **{active_points} Poin**")
        
        reward_choice = st.selectbox("Pilih Kebutuhan / Reward:", list(REWARDS.keys()))
        points_needed = REWARDS[reward_choice]
        
        st.write(f"Poin yang dibutuhkan untuk klaim: **{points_needed} Poin**")
        
        if st.button("Klaim Reward Sekarang", use_container_width=True):
            if active_points >= points_needed:
                # Kurangi poin pengguna di database
                new_points = active_points - points_needed
                c.execute("UPDATE users SET points=? WHERE username=?", (new_points, st.session_state.username))
                
                # Catat transaksi klaim hadiah
                date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
                c.execute("INSERT INTO redemptions (username, reward_item, points_spent, date) VALUES (?, ?, ?, ?)",
                          (st.session_state.username, reward_choice, points_needed, date_now))
                conn.commit()
                
                st.balloons()
                st.success(f"🎉 Sukses mengklaim {reward_choice}! Silakan tunjukkan layar ini kepada petugas KostCycle Hub untuk pengambilan hadiah.")
                st.rerun()
            else:
                st.error("❌ Poin Anda tidak mencukupi untuk melakukan penukaran reward ini.")

    elif choice == "👑 KostCycle Station (Admin)":
        st.header("👑 KostCycle Station - Pusat Verifikasi Drop-off")
        st.write("Halaman khusus admin di booth KostCycle Hub untuk menerima, menimbang, dan memverifikasi sampah fisik yang dibawa langsung oleh mahasiswa.")
        
        # Statistik Utama Dampak Gerakan (Metrik Penyelamatan Lingkungan)
        col1, col2, col3, col4 = st.columns(4)
        
        c.execute("SELECT COUNT(DISTINCT username) FROM users WHERE role='mahasiswa'")
        total_active_students = c.fetchone()[0] or 0
        col1.metric("Mahasiswa Terdaftar", f"{total_active_students} Orang")
        
        c.execute("SELECT SUM(weight) FROM transactions WHERE status='Selesai'")
        total_weight = c.fetchone()[0] or 0.0
        col2.metric("Total Sampah Terselamatkan", f"{total_weight:.1f} Kg")
        
        c.execute("SELECT SUM(points) FROM users")
        total_points = c.fetchone()[0] or 0
        col3.metric("Total Poin Aktif Beredar", f"{total_points} Poin")
        
        c.execute("SELECT COUNT(id) FROM transactions WHERE status='Menunggu Drop-off'")
        pending_count = c.fetchone()[0] or 0
        col4.metric("Antrean Verifikasi di Hub", f"{pending_count} Pengajuan", delta="-Antrean" if pending_count == 0 else "Ada Antrean")
        
        st.markdown("---")
        
        # Verifikasi Sampah yang Dibawa Mahasiswa
        st.subheader("📋 Verifikasi Drop-off Mahasiswa (Konfirmasi di Booth)")
        pending_trans = pd.read_sql_query("SELECT id, username, trash_type, weight, points_earned, date FROM transactions WHERE status='Menunggu Drop-off'", conn)
        
        if not pending_trans.empty:
            st.write("Instruksi Admin: *Ketika mahasiswa menyerahkan sampah fisiknya, cocokkan jenis sampah dan timbang ulang berat aslinya di timbangan posko.*")
            for idx, row in pending_trans.iterrows():
                with st.expander(f"📥 Drop-off dari {row['username']} ({row['trash_type']} - Est. {row['weight']} Kg)"):
                    st.write(f"**Tanggal Pengajuan:** {row['date']}")
                    
                    # Admin melakukan penimbangan riil di booth/posko
                    actual_weight = st.number_input(f"Input Berat Riil Timbangan (Kg/Liter) untuk ID {row['id']}:", min_value=0.1, step=0.1, value=float(row['weight']), key=f"weight_{row['id']}")
                    calculated_points = int(actual_weight * PRICING[row['trash_type']])
                    st.write(f"Poin akhir yang akan ditransfer ke akun mahasiswa: **{calculated_points} Poin**")
                    
                    if st.button(f"Timbang Selesai & Kirim Poin (ID {row['id']})", key=f"btn_{row['id']}"):
                        # Dapatkan poin user saat ini
                        c.execute("SELECT points FROM users WHERE username=?", (row['username'],))
                        current_pts = c.fetchone()[0]
                        
                        # Update data transaksi menjadi selesai beserta berat riil dan poin akhir
                        c.execute("UPDATE transactions SET weight=?, points_earned=?, status='Selesai' WHERE id=?", 
                                  (actual_weight, calculated_points, row['id']))
                        
                        # Tambahkan poin ke user
                        new_pts = current_pts + calculated_points
                        c.execute("UPDATE users SET points=? WHERE username=?", (new_pts, row['username']))
                        conn.commit()
                        
                        st.success(f"Poin berhasil dikirim ke akun {row['username']}!")
                        st.rerun()
        else:
            st.success("Semua antrean drop-off mahasiswa telah selesai diverifikasi di KostCycle Hub!")
            
        st.markdown("---")
        
        # Visualisasi Data Kontribusi Lingkungan
        st.subheader("📊 Analisis Jenis Sampah yang Berhasil Dikumpulkan")
        df_chart_data = pd.read_sql_query("SELECT trash_type, SUM(weight) as total_weight FROM transactions WHERE status='Selesai' GROUP BY trash_type", conn)
        
        if not df_chart_data.empty:
            df_chart_data = df_chart_data.set_index('trash_type')
            st.bar_chart(df_chart_data)
        else:
            st.info("Grafik kontribusi lingkungan akan muncul setelah ada drop-off sampah yang diverifikasi oleh Admin.")
            
        # Daftar Peringkat Mahasiswa dan Riwayat Penukaran
        col_tabel1, col_tabel2 = st.columns(2)
        with col_tabel1:
            st.subheader("🏆 Peringkat Mahasiswa Ter-Eko-Friendly")
            df_users = pd.read_sql_query("SELECT username as 'Nama Mahasiswa', phone as 'No WhatsApp', points as 'Total Poin' FROM users WHERE role='mahasiswa' ORDER BY points DESC", conn)
            st.dataframe(df_users, use_container_width=True)
        with col_tabel2:
            st.subheader("📥 Riwayat Klaim Hadiah Mahasiswa")
            df_redeem = pd.read_sql_query("SELECT username as 'Nama Mahasiswa', reward_item as 'Hadiah', points_spent as 'Poin', date as 'Tanggal Klaim' FROM redemptions ORDER BY id DESC", conn)
            st.dataframe(df_redeem, use_container_width=True)

    elif choice == "💰 Informasi Konversi Sampah":
        st.header("💰 Panduan Konversi Sampah & Daftar Hadiah")
        st.write("Semakin rajin kamu memilah sampah dan melakukan drop-off mandiri, semakin banyak hadiah penunjang kuliah yang bisa kamu klaim!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Poin Berdasarkan Jenis Sampah (Per Kg/Liter)")
            df_pricing = pd.DataFrame(list(PRICING.items()), columns=["Jenis Sampah", "Poin yang Didapat"])
            st.table(df_pricing)
            
        with col2:
            st.subheader("Katalog Reward Penukaran Poin")
            df_rewards = pd.DataFrame(list(REWARDS.items()), columns=["Pilihan Reward", "Poin yang Dibutuhkan"])
            st.table(df_rewards)