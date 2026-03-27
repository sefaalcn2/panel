import streamlit as st
import pandas as pd
import math
import re
from io import BytesIO
import requests
from bs4 import BeautifulSoup
import time
# --- KULLANICI VERITABANI ---
USER_PROFILES = {
    "sefaalcn": {"pw": "1095Sefa.", "name": "Sefa Alçın", "title": "Mağaza Yöneticisi"},
    "avnialcin": {"pw": "1962", "name": "Avni Alçın", "title": "e-Ticaret Yöneticisi"},
    "ealakuzu": {"pw": "Gencal7994.", "name": "Emre Alakuzu", "title": "Mağaza Yöneticisi"},
    "arifhikmet": {"pw": "arifhikmet", "name": "Arif", "title": "Mağaza Yöneticisi"}
}

# OTURUM KONTROLLERI
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'user_full_name' not in st.session_state: st.session_state.user_full_name = ""
if 'user_title' not in st.session_state: st.session_state.user_title = ""

# --- KARAKTER TEMIZLEME FONKSIYONU ---
def create_slug(text):
    if pd.isna(text): return ""
    text = str(text).lower()
    search =  ['ç','ğ','ı','ö','ş','ü']
    replace = ['c','g','i','o','s','u']
    for s, r in zip(search, replace):
        text = text.replace(s, r)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text).strip('-')
    return text
#WEB SCRAPPER SİSTEMİ
# --- KURUMSAL TASARIM (CSS) ---
st.markdown("""
    <style>
    [data-testid="stAppViewBlockContainer"] {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
[data-testid="stHeader"] {
    visibility: visible;
    background: rgba(0,0,0,0); /* Arka planı şeffaf yapar */
}
    
    .stApp { background-color: #1e1f20; }
    h1, h2, h3, p, span, label { color: #e0e0e0 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    .stExpander, .nav-bar, .product-card-container, .mapping-container {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(12px) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        padding: 20px; margin-bottom: 20px;
    }

    .login-wrapper {
        display: flex;
        justify-content: center;
        align-items: flex-start;
        padding-top: 20px;
    }
    .login-card {
        padding: 15px;
        width: 350px !important;
        text-align: center;
        margin: auto;
    }

    .stButton>button {
        background-color: rgba(255, 255, 255, 0.08) !important;
        color: #e0e0e0 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 6px !important; height: 38px;
    }

    div.stButton > button[data-testid="baseButton-primary"] {
        background-color: #083957 !important; color: white !important; border: none !important; font-weight: 600 !important;
    }

    div[data-testid="stTextInput"] input {
        background-color: rgba(255, 255, 255, 0.05) !important; color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important; text-align: center; border-radius: 6px !important; height: 38px;
    }

    div.red-button > button {
        background-color: rgba(220, 53, 69, 0.1) !important;
        color: rgba(255, 255, 255, 0.6) !important;
        border: 1px solid rgba(220, 53, 69, 0.2) !important;
    }

    .product-card-container { border-left: 5px solid #083957 !important; }
    .product-title { font-size: 20px; font-weight: 800; color: #ffffff !important; margin-bottom: 8px; }
    .product-details { font-size: 14px; color: #e0e0e0 !important; line-height: 1.6; }
    
    .detail-value { color: #00ff88; font-weight: 500; }
    .detail-label { color: #7fbbff !important; font-weight: 700; }
    
    [data-testid="stSidebar"] { background-color: #161718 !important; border-right: 1px solid rgba(255, 255, 255, 0.05); }
    </style>
    """, unsafe_allow_html=True)

ZORUNLU_ALANLAR = [
    "Barkod", "Model Kodu", "Marka", "Kategori", "Para Birimi", 
    "Ürün Adı", "Ürün Açıklaması", "Piyasa Satış Fiyatı (KDV Dahil)", 
    "Pazaryeri Fiyatı (KDV Dahil)", "Ürün Stok Adedi", "Stok Kodu", 
    "KDV Oranı", "Desi", "Görsel Linki", "Sevkiyat Süresi"
]

def show_login():
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown('<div class="login-wrapper"><div class="login-card">', unsafe_allow_html=True)
        st.image("https://aletedevat.com.tr/wp-content/uploads/2026/02/Yeni-Proje-5.png", width=220)
        st.markdown("<h2 style='margin-bottom:25px; font-weight:700; color:white;'>Yönetici Paneli</h2>", unsafe_allow_html=True)
        
        # key parametreleri hatayı çözer:
        username = st.text_input("Kullanıcı Adı", placeholder="Kullanıcı Adı", label_visibility="collapsed", key="user_input")
        password = st.text_input("Şifre", type="password", placeholder="Şifre", label_visibility="collapsed", key="pass_input")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sisteme Giriş Yap", type="primary", use_container_width=True, key="login_btn"):
            if username in USER_PROFILES and password == USER_PROFILES[username]["pw"]:
                st.session_state.authenticated = True
                st.session_state.user_full_name = USER_PROFILES[username]["name"]
                st.session_state.user_title = USER_PROFILES[username]["title"]
                st.rerun()
            else:
                st.error("Giriş bilgileri hatalı.")
        st.markdown('</div></div>', unsafe_allow_html=True)

if not st.session_state.authenticated:
    show_login()
else:
    if 'master_df' not in st.session_state: st.session_state.master_df = pd.DataFrame()
    if 'mapping_done' not in st.session_state: st.session_state.mapping_done = False
    if 'column_map' not in st.session_state: st.session_state.column_map = {}
    if 'current_page' not in st.session_state: st.session_state.current_page = 1
    if 'selected_global_indices' not in st.session_state: st.session_state.selected_global_indices = set()

    with st.sidebar:
        st.image("https://aletedevat.com.tr/wp-content/uploads/2026/02/Yeni-Proje-5.png", use_container_width=True)
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.08); border-radius:10px; padding:10px; text-align:center; border:1px solid rgba(255,255,255,0.1); margin-bottom:15px;">
            <span style="font-size:14px; font-weight:700; color:#7fbbff;">{st.session_state.user_title}</span>
        </div>
        <div style="text-align:center; margin-bottom:15px;">
            <span style="font-size:16px;">Hoş geldiniz,</span><br>
            <span style="font-size:18px; font-weight:800; color:white;">{st.session_state.user_full_name}</span>
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        # İsimlendirmeler isteğin üzerine güncellendi
        modul = st.selectbox("Uygulama Seçin:", ["Excel Düzenleme", "Alan Eşleme Paneli", "Pazaryeri Şablon Oluşturma", "Excel Alan Özelleştirme"])
        st.divider()

        if modul == "Excel Düzenleme":
            dosya = st.file_uploader("Excel Dosyası Yükle", type=['xlsx', 'csv'], key="excel_up")
            if dosya:
                if st.session_state.get('last_uploaded_file') != dosya.name:
                    df = pd.read_excel(dosya) if dosya.name.endswith('xlsx') else pd.read_csv(dosya)
                    df.columns = df.columns.str.strip()
                    if "Excel Satırı" not in df.columns:
                        df.insert(0, "Excel Satırı", range(2, len(df) + 2))
                    st.session_state.master_df = df
                    st.session_state.mapping_done = False
                    st.session_state.last_uploaded_file = dosya.name
                    st.session_state.current_page = 1
                    st.rerun()

    if modul == "Excel Düzenleme":
        if not st.session_state.master_df.empty:
            excel_satir_kolonu = "Excel Satırı"
            if not st.session_state.mapping_done:
                st.subheader("Sütun Eşleştirme Ayarları")
                all_cols = [c for c in st.session_state.master_df.columns if c != excel_satir_kolonu]
                secenekler = ["Eşleşme Yok"] + all_cols
                
                c1, c2 = st.columns(2)
                with c1: 
                    m_urun = st.selectbox("Ürün Adı Sütunu:", secenekler, index=1 if len(secenekler) > 1 else 0)
                    m_marka = st.selectbox("Marka Sütunu:", secenekler, index=0)
                    m_resim_url = st.selectbox("Resim URL Sütunu:", secenekler, index=0)
                with c2: 
                    m_stok_kodu = st.selectbox("Stok Kodu (SKU) Sütunu:", secenekler, index=0)
                    m_kategori = st.selectbox("Kategori Sütunu:", secenekler, index=0)
                    m_fiyat_ref = st.selectbox("Fiyat Sütunu:", secenekler, index=0)

                if st.button("Eşleştirmeyi Onayla", type="primary"):
                    mapping_plani = {'urun':(m_urun,"Ürün Adı"), 'marka':(m_marka,"Marka"), 'resim_url':(m_resim_url,"Görsel Linki"), 'stok_kodu':(m_stok_kodu,"Stok Kodu"), 'kategori':(m_kategori,"Kategori"), 'fiyat_ref':(m_fiyat_ref,"Fiyat")}
                    yeni_map = {}
                    for key, (secilen, varsayilan_ad) in mapping_plani.items():
                        if secilen == "Eşleşme Yok":
                            if varsayilan_ad not in st.session_state.master_df.columns:
                                st.session_state.master_df[varsayilan_ad] = ""
                            yeni_map[key] = varsayilan_ad
                        else: yeni_map[key] = secilen
                    st.session_state.column_map = yeni_map
                    st.session_state.mapping_done = True
                    st.rerun()
            else:
                map_info = st.session_state.column_map
                with st.sidebar:
                    st.divider()
                    s_yonu = st.selectbox("Fiyat Sıralaması:", ["Varsayılan", "Düşükten Yükseğe", "Yüksekten Düşüğe"])
                    s_marka = st.multiselect("Markalar:", st.session_state.master_df[map_info['marka']].unique(), placeholder="Marka Seçin")
                    s_kategori = st.multiselect(
    "Kategoriler:", 
    st.session_state.master_df[map_info['kategori']].unique(),
    placeholder="Kategori seçin"
)
                    temp_prices = pd.to_numeric(st.session_state.master_df[map_info['fiyat_ref']], errors='coerce').fillna(0)
                    f_min = st.number_input("Minimum Fiyat:", value=float(temp_prices.min()))
                    f_max = st.number_input("Maksimum Fiyat:", value=float(temp_prices.max()))
                    if st.button("Sütunları Yeniden Eşleştir", use_container_width=True):
                        st.session_state.mapping_done = False; st.rerun()

                df_f = st.session_state.master_df.copy()
                df_f['_price_num'] = pd.to_numeric(df_f[map_info['fiyat_ref']], errors='coerce').fillna(0)
                if s_marka: df_f = df_f[df_f[map_info['marka']].isin(s_marka)]
                if s_kategori: df_f = df_f[df_f[map_info['kategori']].isin(s_kategori)]
                df_f = df_f[(df_f['_price_num'] >= f_min) & (df_f['_price_num'] <= f_max)]
                arama = st.text_input("Arama:", placeholder="Ürün Adı veya Stok Kodu")
                if arama: df_f = df_f[df_f.astype(str).apply(lambda x: x.str.contains(arama, case=False, na=False)).any(axis=1)]
                
                if s_yonu == "Düşükten Yükseğe": df_f = df_f.sort_values(by='_price_num', ascending=True)
                elif s_yonu == "Yüksekten Düşüğe": df_f = df_f.sort_values(by='_price_num', ascending=False)
                else: df_f = df_f.sort_values(by=excel_satir_kolonu, ascending=True)

                st.markdown("<div class='nav-bar'>", unsafe_allow_html=True)
                nc1, nc2, nc3, nc4, nc5 = st.columns([1.5, 0.6, 0.6, 0.6, 2])
                with nc1: s_size = st.selectbox("Satır:", [15, 50, 100, "Tümü"], index=0, label_visibility="collapsed"); sayfa_boyutu = len(df_f) if s_size == "Tümü" else s_size
                toplam_s = math.ceil(len(df_f) / sayfa_boyutu) if len(df_f) > 0 else 1
                if st.session_state.current_page > toplam_s: st.session_state.current_page = 1
                with nc2:
                    page_input = st.text_input("Sayfa", value=str(st.session_state.current_page), label_visibility="collapsed")
                    if page_input.isdigit() and int(page_input) != st.session_state.current_page:
                        st.session_state.current_page = int(page_input); st.rerun()
                with nc3:
                    if st.button("Geri", disabled=(st.session_state.current_page <= 1)): st.session_state.current_page -= 1; st.rerun()
                with nc4:
                    if st.button("İleri", disabled=(st.session_state.current_page >= toplam_s)): st.session_state.current_page += 1; st.rerun()
                with nc5: select_page = st.checkbox("Tümünü Seç", key="sel_all_page")
                st.markdown("</div>", unsafe_allow_html=True)

                dilim_df = df_f.drop(columns=['_price_num']).iloc[(st.session_state.current_page - 1) * sayfa_boyutu : st.session_state.current_page * sayfa_boyutu].copy()
                dilim_df.insert(0, "Seç", select_page)
                
                edited_df = st.data_editor(dilim_df, use_container_width=True, hide_index=True, column_config={"Seç": st.column_config.CheckboxColumn("Seç", default=False), excel_satir_kolonu: st.column_config.TextColumn(excel_satir_kolonu, disabled=True)}, key="main_table_edit")

                c_btn1, c_btn2, c_btn3 = st.columns([1, 1, 4])
                with c_btn1:
                    if st.button("Kaydet", type="primary", use_container_width=True):
                        st.session_state.master_df.update(edited_df.drop(columns=["Seç"]))
                        st.success("Veriler güncellendi."); st.rerun()
                with c_btn2:
                    selected_to_delete = edited_df[edited_df["Seç"] == True]
                    if not selected_to_delete.empty:
                        if st.button("Satırı Sil", use_container_width=True):
                            st.session_state.master_df = st.session_state.master_df.drop(selected_to_delete.index)
                            st.session_state.selected_global_indices = set()
                            st.warning("Seçili satırlar silindi."); st.rerun()

                curr_sel = edited_df[edited_df["Seç"] == True].index.tolist()
                for idx in curr_sel: st.session_state.selected_global_indices.add(idx)
                curr_unsel = edited_df[edited_df["Seç"] == False].index.tolist()
                for idx in curr_unsel: st.session_state.selected_global_indices.discard(idx)

                # --- 3. OTOMATİK MARKALANDIRMA PANELİ (İSTEĞİN ÜZERİNE ESKİ HIZLI YAPIYA DÖNÜLDÜ) ---
                st.divider()
                with st.expander("Otomatik Markalandırma Paneli (Toplu Onay)", expanded=False):
                    m_df = st.session_state.master_df.copy()
                    m_df['ilk_kelime'] = m_df[map_info['urun']].astype(str).str.split().str[0]
                    
                    stats = m_df.groupby('ilk_kelime').size().reset_index(name='Adet')
                    stats = stats.sort_values(by='Adet', ascending=False)
                    stats['Marka Tanımı'] = stats['ilk_kelime']
                    stats.insert(0, "Onay", False)
                    
                    st.info(f"Sistem toplamda **{len(stats)}** farklı marka kökü tespit etti. Uygun olanları işaretleyip topluca tanımlayabilirsiniz.")
                    
                    brand_editor = st.data_editor(
                        stats,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Onay": st.column_config.CheckboxColumn("Onay", default=False),
                            "ilk_kelime": st.column_config.TextColumn("Öneri", disabled=True),
                            "Adet": st.column_config.NumberColumn("Ürün Sayısı", disabled=True),
                            "Marka Tanımı": st.column_config.TextColumn("Düzenlenebilir Marka Adı")
                        },
                        key="brand_batch_editor"
                    )
                    
                    if st.button("Seçili Markaları Topluca Uygula", type="primary"):
                        onayli_gruplar = brand_editor[brand_editor["Onay"] == True]
                        if not onayli_gruplar.empty:
                            marka_kolonu = map_info['marka']
                            if marka_kolonu not in st.session_state.master_df.columns:
                                st.session_state.master_df["Marka"] = ""
                                st.session_state.column_map['marka'] = "Marka"
                                marka_kolonu = "Marka"
                            
                            for _, row in onayli_gruplar.iterrows():
                                st.session_state.master_df.loc[m_df['ilk_kelime'] == row['ilk_kelime'], marka_kolonu] = row['Marka Tanımı']
                            
                            st.success(f"{len(onayli_gruplar)} marka grubu başarıyla güncellendi."); st.rerun()
                        else:
                            st.warning("Lütfen güncellenecek grupları Onay kutusundan seçiniz.")

                # TOPLU FIYAT İŞLEMLERİ
                st.divider()
                with st.expander("Toplu Fiyat İşlemleri", expanded=True):
                    g_mod = st.radio("İşlem Kapsamı:", ["Filtrelenmiş Liste", "Seçili Ürünler"], horizontal=True)
                    hedef_idx = df_f.index if g_mod == "Filtrelenmiş Liste" else list(st.session_state.selected_global_indices)
                    if len(hedef_idx) > 0:
                        st.info(f"İşlem yapılacak ürün sayısı: {len(hedef_idx)}")
                        c_m1, c_m2, c_m3, c_m4 = st.columns([2, 1, 1, 1])
                        with c_m1: t_cols = st.multiselect("Sütunlar:", [c for c in st.session_state.master_df.columns if not c.startswith('Yeni ') and c != excel_satir_kolonu], placeholder="Sütun seçin")
                        with c_m2: i_tip = st.selectbox("Yöntem:", ["Yüzdesel (%)", "Sabit (+/-)", "Kat Sayı (x)"])
                        with c_m3: i_deg = st.number_input("Değer:", value=0.0)
                        with c_m4: i_yon = st.selectbox("Yön:", ["Arttır", "Düşür"])
                        if st.button("Hesaplamayı Uygula", type="primary"):
                            for c in t_cols:
                                new_c = f"Yeni {c}"
                                base = pd.to_numeric(st.session_state.master_df[c], errors='coerce').fillna(0)
                                if new_c not in st.session_state.master_df.columns: st.session_state.master_df[new_c] = base
                                oran = ((1 + i_deg/100) if i_yon == "Arttır" else (1 - i_deg/100))
                                if i_tip == "Yüzdesel (%)": st.session_state.master_df.loc[hedef_idx, new_c] = base.loc[hedef_idx] * oran
                                elif i_tip == "Kat Sayı": st.session_state.master_df.loc[hedef_idx, new_c] = base.loc[hedef_idx] * i_deg
                                else: st.session_state.master_df.loc[hedef_idx, new_c] = base.loc[hedef_idx] + (i_deg if i_yon == "Arttır" else -i_deg)
                            st.rerun()

                # --- ÜRÜN KARTI (PAYLAŞTIĞIN KODDAKİ YERİ) ---
                if len(st.session_state.selected_global_indices) > 0:
                    st.divider()
                    v_idx = [i for i in st.session_state.selected_global_indices if i in st.session_state.master_df.index]
                    if v_idx:
                        p = st.session_state.master_df.loc[v_idx[0]]
                        st.markdown("<div class='product-card-container'>", unsafe_allow_html=True)
                        ci, cd = st.columns([1, 4])
                        with ci:
                            img_url = p[map_info['resim_url']]
                            if pd.notna(img_url) and str(img_url).startswith('http'): st.image(img_url, width=160)
                            else: st.info("Görsel Yok")
                        with cd:
                            st.markdown(f"<div class='product-title'>{p[map_info['urun']]}</div>", unsafe_allow_html=True)
                            st.markdown(f"""<div class='product-details'>
                                <span class='detail-label'>Marka:</span> <span class="detail-value">{p[map_info['marka']]}</span> | 
                                <span class='detail-label'>SKU:</span> <span class="detail-value">{p[map_info['stok_kodu']]}</span> | 
                                <span class='detail-label'>Kategori:</span> <span class="detail-value">{p[map_info['kategori']]}</span>
                            </div>""", unsafe_allow_html=True)
                            p_curr = pd.to_numeric(p[map_info['fiyat_ref']], errors='coerce')
                            st.markdown(f"<span style='color:#7fbbff; font-size:18px; font-weight:bold;'>{p_curr:,.2f} TL</span>", unsafe_allow_html=True)
                            st.link_button("Sitede Gör", f"https://aletedevat.com.tr/magaza/{create_slug(p[map_info['urun']])}/", type="primary")
                        st.markdown("</div>", unsafe_allow_html=True)

                st.divider()
                st.subheader("Veri Dışa Aktarma")
                final_download_df = df_f.drop(columns=['_price_num'])
                d1, d2 = st.columns(2)
                with d1: 
                    st.download_button("CSV Olarak İndir", final_download_df.to_csv(index=False).encode('utf-8'), "aletedevat_liste.csv", use_container_width=True)
                with d2:
                    xlsx_out = BytesIO()
                    with pd.ExcelWriter(xlsx_out, engine='xlsxwriter') as wr: final_download_df.to_excel(wr, index=False)
                    st.download_button("Excel Olarak İndir", xlsx_out.getvalue(), "aletedevat_liste.xlsx", use_container_width=True, type="primary")
        else: st.info("Excel dosyasını yükleyiniz.")

    # --- YENI MODÜL: ALAN EŞLEME PANELI (VLOOKUP MANTIĞI) ---
    elif modul == "Alan Eşleme Paneli":
        st.subheader("Veri Birleştirme ve Alan Eşleme Merkezi")
        st.info("İki farklı Excel dosyasını ortak bir anahtar sütun (Örn: Stok Kodu) üzerinden eşleştirerek eksik verileri tamamlayabilirsiniz.")
        
        c1, c2 = st.columns(2)
        with c1:
            kaynak_dosya = st.file_uploader("Kaynak Dosya (Verilerin Alınacağı)", type=['xlsx', 'csv'], key="k_dosya")
        with c2:
            hedef_dosya = st.file_uploader("Hedef Dosya (Verilerin Ekleneceği)", type=['xlsx', 'csv'], key="h_dosya")
            
        if kaynak_dosya and hedef_dosya:
            df_k = pd.read_excel(kaynak_dosya) if kaynak_dosya.name.endswith('xlsx') else pd.read_csv(kaynak_dosya)
            df_h = pd.read_excel(hedef_dosya) if hedef_dosya.name.endswith('xlsx') else pd.read_csv(hedef_dosya)
            
            st.divider()
            cc1, cc2 = st.columns(2)
            with cc1:
                k_anahtar = st.selectbox("Kaynak Dosya Anahtar Sütun (Ortak Alan):", df_k.columns)
            with cc2:
                h_anahtar = st.selectbox("Hedef Dosya Anahtar Sütun (Ortak Alan):", df_h.columns)
                
            aktarilacaklar = st.multiselect("Hedef Dosyaya Aktarılacak Sütunlar:", [c for c in df_k.columns if c != k_anahtar])
            
            if st.button("Eşleştirmeyi Başlat ve Verileri Aktar", type="primary", use_container_width=True):
                if not aktarilacaklar:
                    st.warning("Lütfen aktarılacak en az bir sütun seçiniz.")
                else:
                    df_k[k_anahtar] = df_k[k_anahtar].astype(str).str.strip()
                    df_h[h_anahtar] = df_h[h_anahtar].astype(str).str.strip()
                    # Kaynak dosyadan sadece anahtar ve seçilen sütunları al, kopyaları temizle
                    df_k_sub = df_k[[k_anahtar] + aktarilacaklar].drop_duplicates(subset=[k_anahtar])
                    # VLOOKUP işlemi (Left Merge)
                    sonuc_df = pd.merge(df_h, df_k_sub, left_on=h_anahtar, right_on=k_anahtar, how='left')
                    if k_anahtar != h_anahtar: sonuc_df = sonuc_df.drop(columns=[k_anahtar])
                    
                    st.success("Eşleştirme ve veri aktarımı başarıyla tamamlandı.")
                    st.dataframe(sonuc_df, use_container_width=True)
                    out_merged = BytesIO()
                    with pd.ExcelWriter(out_merged, engine='xlsxwriter') as wr: sonuc_df.to_excel(wr, index=False)
                    st.download_button("Eşleşmiş Listeyi İndir", out_merged.getvalue(), "eslesmis_veri_listesi.xlsx", use_container_width=True, type="primary")

    # MODÜL: PAZARYERI ŞABLON OLUŞTURMA ---
    elif modul == "Pazaryeri Şablon Oluşturma":
        st.subheader("Pazaryeri Şablon Yapılandırma")
        tpl_file = st.file_uploader("Pazaryeri Şablonu Yükle", type=['xlsx', 'csv'], key="tpl_up")
        if tpl_file:
            tpl_df = pd.read_excel(tpl_file) if tpl_file.name.endswith('xlsx') else pd.read_csv(tpl_file)
            tpl_cols = tpl_df.columns.tolist()
            with st.expander("Şablon Sütun Tanımları", expanded=True):
                tpl_map = {}
                c1, c2 = st.columns(2)
                for i, field in enumerate(ZORUNLU_ALANLAR):
                    with c1 if i < 8 else c2: tpl_map[field] = st.selectbox(f"{field}:", ["Boş Bırak"] + tpl_cols, key=f"tpl_{field}")
            src_file = st.file_uploader("Kaynak Ürün Verisi Yükle", type=['xlsx', 'csv'], key="src_up")
            if src_file:
                src_df = pd.read_excel(src_file) if src_file.name.endswith('xlsx') else pd.read_csv(src_file)
                src_cols = src_df.columns.tolist()
                with st.expander("Sütun Eşleştirme", expanded=True):
                    src_map = {}
                    sc1, sc2 = st.columns(2)
                    for i, field in enumerate(ZORUNLU_ALANLAR):
                        if tpl_map[field] != "Boş Bırak":
                            with sc1 if i < 8 else sc2: src_map[field] = st.selectbox(f"{field} Kaynağı:", ["Veri Yok"] + src_cols, key=f"src_{field}")
                if st.button("Verileri Şablona Aktar", type="primary", use_container_width=True):
                    final_list = []
                    for _, row in src_df.iterrows():
                        new_row = {col: "" for col in tpl_cols}
                        for field in ZORUNLU_ALANLAR:
                            t_col = tpl_map[field]; s_col = src_map.get(field, "Veri Yok")
                            if t_col != "Boş Bırak" and s_col != "Veri Yok": new_row[t_col] = row[s_col]
                        final_list.append(new_row)
                    final_mapped_df = pd.DataFrame(final_list)
                    st.success("Aktarım tamamlandı.")
                    st.dataframe(final_mapped_df, use_container_width=True)
                    out_mapped = BytesIO()
                    with pd.ExcelWriter(out_mapped, engine='xlsxwriter') as wrm: final_mapped_df.to_excel(wrm, index=False)
                    st.download_button("Pazaryeri Dosyasını İndir", out_mapped.getvalue(), "pazaryeri_aktarim.xlsx", use_container_width=True, type="primary")
    # MODÜL: EXCEL ALAN ÖZELLEŞTİRME ---
    elif modul == "Excel Alan Özelleştirme":
        st.subheader("Excel Alan Özelleştirme ve İsim Düzenleme")
        st.info("İsimleri benzersizleştirmek için kriterlerinizi belirleyin.")

        islem_tipi = st.radio("İşlem Türü Seçin:", ["Tek Excel (Aynı Dosya İçinde)", "Çift Excel (Başka Dosyadan Veri Çek)"], horizontal=True)

        if islem_tipi == "Tek Excel (Aynı Dosya İçinde)":
            f = st.file_uploader("Excel Dosyası Yükle", type=['xlsx', 'csv'], key="ozel_tek")
            if f:
                # Dosyayı yükle ve tümünü göster
                df_ozel = pd.read_excel(f) if f.name.endswith('xlsx') else pd.read_csv(f)
                cols = df_ozel.columns.tolist()
                
                c1, c2, c3 = st.columns(3)
                with c1: target_col = st.selectbox("Düzenlenecek Sütun (Örn: Ürün Adı):", cols)
                with c2: source_col = st.selectbox("Eklenecek Sütun (Örn: Stok Kodu):", cols)
                with c3: ayrac = st.text_input("Araya Gelecek Karakter:", value=" - ")
                
                # Kapsam Seçenekleri
                kapsam = st.radio("İşlem Kapsamı:", ["Tüm Liste", "Sadece Tekrar Eden İsimler", "Tablodan Seçtiklerim"], horizontal=True)
                
                # Seçim için tabloyu göster (Tüm liste görünür)
                df_display = df_ozel.copy()
                if kapsam == "Tablodan Seçtiklerim":
                    df_display.insert(0, "Seç", False)
                
                edited_ozel = st.data_editor(df_display, use_container_width=True, hide_index=True, key="ozel_editor_tablo")

                if st.button("İsimleri Güncelle", type="primary", use_container_width=True):
                    # Mantığı belirle
                    if kapsam == "Tüm Liste":
                        df_ozel[target_col] = df_ozel[target_col].astype(str) + ayrac + df_ozel[source_col].astype(str)
                    
                    elif kapsam == "Sadece Tekrar Eden İsimler":
                        # Sadece aynı isme sahip olanları bul (mask oluştur)
                        mask = df_ozel.duplicated(subset=[target_col], keep=False)
                        df_ozel.loc[mask, target_col] = df_ozel.loc[mask, target_col].astype(str) + ayrac + df_ozel.loc[mask, source_col].astype(str)
                        st.write(f"Bilgi: {mask.sum()} adet tekrar eden ürün ismi güncellendi.")
                    
                    elif kapsam == "Tablodan Seçtiklerim":
                        selected_indices = edited_ozel[edited_ozel["Seç"] == True].index
                        df_ozel.loc[selected_indices, target_col] = df_ozel.loc[selected_indices, target_col].astype(str) + ayrac + df_ozel.loc[selected_indices, source_col].astype(str)

                    st.success("İşlem Başarıyla Tamamlandı!")
                    st.dataframe(df_ozel, use_container_width=True) # Güncel halini göster
                    
                    out = BytesIO()
                    with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_ozel.to_excel(wr, index=False)
                    st.download_button("Güncel Listeyi İndir", out.getvalue(), "aletedevat_ozellestirilmis_liste.xlsx", use_container_width=True)

        else: # Çift Excel Modu
            c1, c2 = st.columns(2)
            with c1: f1 = st.file_uploader("1. Ana Excel (İsimlerin Değişeceği)", type=['xlsx', 'csv'], key="f1_final")
            with c2: f2 = st.file_uploader("2. Referans Excel (Verinin Alınacağı)", type=['xlsx', 'csv'], key="f2_final")
            
            if f1 and f2:
                # 1. DOSYALARI OKU VE ANINDA BENZERSİZLEŞTİR
                df1_raw = pd.read_excel(f1) if f1.name.endswith('xlsx') else pd.read_csv(f1)
                df2_raw = pd.read_excel(f2) if f2.name.endswith('xlsx') else pd.read_csv(f2)

                # Sütunları garantili benzersiz yapma fonksiyonu
                def make_cols_unique(df):
                    new_cols = []
                    counts = {}
                    for col in df.columns:
                        if col in counts:
                            counts[col] += 1
                            new_cols.append(f"{col}_{counts[col]}")
                        else:
                            counts[col] = 0
                            new_cols.append(col)
                    df.columns = new_cols
                    return df

                df1 = make_cols_unique(df1_raw)
                df2 = make_cols_unique(df2_raw)

                st.success("Dosyalar yüklendi.")

                # 2. SEÇİM ALANLARI
                cc1, cc2 = st.columns(2)
                with cc1: 
                    key1 = st.selectbox("1. Excel Ortak Sütun (SKU):", df1.columns, key="key1_unique")
                    target_col = st.selectbox("1. Excel Düzenlenecek Sütun (İsim):", df1.columns, key="target_unique")
                with cc2: 
                    key2 = st.selectbox("2. Excel Ortak Sütun (SKU):", df2.columns, key="key2_unique")
                    source_col = st.selectbox("2. Excel'den Alınacak Sütun (Ek Bilgi):", df2.columns, key="source_unique")
                
                ayrac = st.text_input("Araya Gelecek Karakter:", value=" - ", key="ayrac_son")
                
                # 3. İŞLEM KAPSAMI SEÇİMİ
                kapsam = st.radio("Hangi Ürünlere İşlem Yapılsın?", 
                                  ["Tüm Liste", "Sadece İsmi Aynı Olanlar", "Sadece Seçtiğim Ürünler"], 
                                  horizontal=True)

                # 4. TAM ÖNİZLEME VE SEÇİM TABLOSU
                df_to_show = df1.copy()
                if kapsam == "Sadece Seçtiğim Ürünler":
                    df_to_show.insert(0, "Seç", False)
                
                # Tüm listeyi gösteren editör
                edited_df = st.data_editor(df_to_show, use_container_width=True, hide_index=True, key="full_editor_cift")

                if st.button("Verileri Eşleştir ve Güncelle", type="primary", use_container_width=True):
                    # Referans tabloyu hazırla (Eğer key2 ve source_col aynıysa hata vermemesi için)
                    if key2 == source_col:
                        df2_sub = df2[[key2]].copy()
                        df2_sub['extra_val'] = df2_sub[key2]
                        ref_col = 'extra_val'
                    else:
                        df2_sub = df2[[key2, source_col]].copy()
                        ref_col = source_col
                    
                    df2_sub = df2_sub.drop_duplicates(subset=[key2])
                    
                    # MERGE (Hatayı burada önlüyoruz)
                    merged = pd.merge(df1, df2_sub, left_on=key1, right_on=key2, how='left')

                    # 5. MANTIK FİLTRELERİ
                    if kapsam == "Tüm Liste":
                        mask = merged[ref_col].notna()
                    
                    elif kapsam == "Sadece İsmi Aynı Olanlar":
                        # 1. Tabloda ismi aynı olanları bul (25 tane matkap gibi)
                        is_duplicate = merged.duplicated(subset=[target_col], keep=False)
                        mask = is_duplicate & merged[ref_col].notna()
                    
                    elif kapsam == "Sadece Seçtiğim Ürünler":
                        selected_indices = edited_df[edited_df["Seç"] == True].index
                        mask = (merged.index.isin(selected_indices)) & (merged[ref_col].notna())

                    # GÜNCELLEME İŞLEMİ
                    merged.loc[mask, target_col] = merged.loc[mask, target_col].astype(str) + ayrac + merged.loc[mask, ref_col].astype(str)
                    
                    # Gereksiz sütunları temizle
                    if key2 in merged.columns: merged = merged.drop(columns=[key2])
                    if 'extra_val' in merged.columns: merged = merged.drop(columns=['extra_val'])
                    # Eğer source_col target_col'dan farklıysa ve merge'den geldiyse onu da temizleyelim
                    if source_col in merged.columns and source_col != target_col and source_col != key1:
                        merged = merged.drop(columns=[source_col])

                    st.success(f"İşlem Tamamlandı! {mask.sum()} satır güncellendi.")
                    st.dataframe(merged, use_container_width=True) # Son halini göster

                    # İNDİRME BUTONU
                    out = BytesIO()
                    with pd.ExcelWriter(out, engine='xlsxwriter') as wr: merged.to_excel(wr, index=False)
                    st.download_button("Güncel Listeyi İndir", out.getvalue(), "aletedevat_final_liste.xlsx", use_container_width=True)

    with st.sidebar:
        st.divider()
        if not st.session_state.master_df.empty:
            if st.button("Sistemi Sıfırla", use_container_width=True):
                st.session_state.master_df = pd.DataFrame(); st.session_state.mapping_done = False; st.rerun()
        st.markdown('<div class="red-button">', unsafe_allow_html=True)
        if st.button("Güvenli Çıkış", use_container_width=True):
            st.session_state.authenticated = False; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
