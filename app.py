import streamlit as st
import pandas as pd
import math
import re
from io import BytesIO

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Alet Edevat | Yönetim Merkezi", layout="wide")

# --- KULLANICI VERİTABANI VE HAFIZASI ---
USER_PROFILES = {
    "sefaalcn": {"pw": "1095Sefa.", "name": "Sefa Alçın", "title": "Mağaza Yöneticisi"},
    "avnialcin": {"pw": "1962", "name": "Avni Alçın", "title": "e-Ticaret Yöneticisi"}
}

if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if 'user_full_name' not in st.session_state: st.session_state.user_full_name = ""
if 'user_title' not in st.session_state: st.session_state.user_title = ""

# --- TÜRKÇE KARAKTER TEMİZLEME ---
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

# --- MODERN KURUMSAL TASARIM (CSS) ---
st.markdown("""
    <style>
    /* 1. Streamlit'in kendi footer ve header kalıntılarını tamamen siler */
    footer {visibility: hidden;}
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    [data-testid="stHeader"] {display: none !important;}

    /* 2. KRİTİK: SAYFAYI EN ÜSTE YAPIŞTIRAN KODLAR */
    [data-testid="stAppViewBlockContainer"] {
        padding-top: 1rem !important; /* En üstteki boşluğu öldürdük */
        padding-bottom: 0rem !important;
    }
    
    .stApp { background-color: #1e1f20; }
    h1, h2, h3, p, span, label { color: #e0e0e0 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    .stExpander, .nav-bar, .product-card-container, .mapping-container {{
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(12px) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        padding: 20px; margin-bottom: 20px;
    }}

    /* GİRİŞ PANELİ: COMPACT VE EN TEPEDE */
    .login-wrapper {{
        display: flex;
        justify-content: center;
        align-items: flex-start; /* Merkeze değil en tepeye yasladık */
        padding-top: 20px;
    }}
    .login-card {{
        padding: 15px;
        width: 350px !important;
        text-align: center;
        margin: auto;
    }}
    .login-card div[data-testid="stTextInput"] {{
        margin-bottom: -15px;
    }}

    div[data-testid="column"] {{ display: flex; align-items: center; justify-content: center; }}

    .stButton>button {{
        background-color: rgba(255, 255, 255, 0.08) !important;
        color: #e0e0e0 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 6px !important; height: 38px;
        transition: all 0.2s ease;
    }}
    .stButton>button:hover {{ background-color: rgba(255, 255, 255, 0.15) !important; transform: translateY(-1px); }}

    div.stButton > button[data-testid="baseButton-primary"] {{
        background-color: #083957 !important; color: white !important; border: none !important; font-weight: 600 !important;
    }}

    div[data-testid="stTextInput"] input {{
        background-color: rgba(255, 255, 255, 0.05) !important; color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important; text-align: center; border-radius: 6px !important; height: 38px;
    }}

    /* Sönük Kırmızı Çıkış Butonu */
    div.red-button > button {{
        background-color: rgba(220, 53, 69, 0.1) !important;
        color: rgba(255, 255, 255, 0.6) !important;
        border: 1px solid rgba(220, 53, 69, 0.2) !important;
    }}
    div.red-button > button:hover {{
        background-color: rgba(220, 53, 69, 0.25) !important;
        color: rgba(255, 255, 255, 0.9) !important;
    }}

    .product-card-container {{ border-left: 5px solid #083957 !important; }}
    .product-title {{ font-size: 22px; font-weight: 800; color: #ffffff !important; margin-bottom: 12px; }}
    .product-details {{ font-size: 15px; color: #e0e0e0 !important; line-height: 1.8; }}
    
    .detail-value {{ color: #00ff88; font-weight: 500; }}
    .detail-label {{ color: #7fbbff !important; font-weight: 700; }}
    
    [data-testid="stSidebar"] {{ background-color: #161718 !important; border-right: 1px solid rgba(255, 255, 255, 0.05); }}
    [data-testid="stElementToolbar"] {{ display: none; }}
    </style>
    """, unsafe_allow_html=True)

# --- STANDART ALAN LİSTESİ ---
ZORUNLU_ALANLAR = [
    "Barkod", "Model Kodu", "Marka", "Kategori", "Para Birimi", 
    "Ürün Adı", "Ürün Açıklaması", "Piyasa Satış Fiyatı (KDV Dahil)", 
    "Pazaryeri Fiyatı (KDV Dahil)", "Ürün Stok Adedi", "Stok Kodu", 
    "KDV Oranı", "Desi", "Görsel Linki", "Sevkiyat Süresi"
]

# --- GİRİŞ EKRANI FONKSİYONU ---
def show_login():
    # Sayfayı yatayda ortalamak için kolonlar
    c1, c2, c3 = st.columns([1, 1.2, 1])
    
    with c2:
        st.markdown('<div class="login-wrapper"><div class="login-card">', unsafe_allow_html=True)
        st.image("https://aletedevat.com.tr/wp-content/uploads/2026/02/Yeni-Proje-5.png", width=220)
        st.markdown("<h2 style='margin-bottom:25px; font-weight:700; color:white;'>Yönetim Merkezi</h2>", unsafe_allow_html=True)
        
        username = st.text_input("Kullanıcı Adı", placeholder="Kullanıcı Adınız", label_visibility="collapsed")
        password = st.text_input("Şifre", type="password", placeholder="Şifre", label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sisteme Giriş Yap", type="primary", use_container_width=True):
            if username in USER_PROFILES and password == USER_PROFILES[username]["pw"]:
                st.session_state.authenticated = True
                st.session_state.user_full_name = USER_PROFILES[username]["name"]
                st.session_state.user_title = USER_PROFILES[username]["title"]
                st.rerun()
            else:
                st.error("Giriş bilgileri hatalı.")
        st.markdown('</div></div>', unsafe_allow_html=True)

# --- ANA UYGULAMA ---
if not st.session_state.authenticated:
    show_login()
else:
    # GLOBAL HAFIZA (Giriş sonrası yüklenir)
    if 'master_df' not in st.session_state: st.session_state.master_df = pd.DataFrame()
    if 'mapping_done' not in st.session_state: st.session_state.mapping_done = False
    if 'column_map' not in st.session_state: st.session_state.column_map = {}
    if 'current_page' not in st.session_state: st.session_state.current_page = 1
    if 'selected_global_indices' not in st.session_state: st.session_state.selected_global_indices = set()

    # SOL PANEL (Sidebar)
    with st.sidebar:
        st.image("https://aletedevat.com.tr/wp-content/uploads/2026/02/Yeni-Proje-5.png", use_container_width=True)
        
        # --- KULLANICI BİLGİ ALANI ---
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.08); border-radius:10px; padding:10px; text-align:center; border:1px solid rgba(255,255,255,0.1); margin-bottom:15px;">
            <span style="font-size:14px; font-weight:700; color:#7fbbff;">{st.session_state.user_title}</span>
        </div>
        <div style="text-align:center; margin-bottom:15px;">
            <span style="font-size:16px;">Hoşgeldiniz,</span><br>
            <span style="font-size:18px; font-weight:800; color:white;">{st.session_state.user_full_name}</span>
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        
        modul = st.selectbox("Uygulama Seçin:", ["Excel Düzenleme", "Alan Eşleme Paneli"])
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

    # --- MODÜL 1: EXCEL DÜZENLEME ---
    if modul == "Excel Düzenleme":
        if not st.session_state.master_df.empty:
            excel_satir_kolonu = "Excel Satırı"
            if not st.session_state.mapping_done:
                st.subheader("Sütun Eşleştirme Ayarları")
                all_cols = [c for c in st.session_state.master_df.columns if c != excel_satir_kolonu]
                c1, c2 = st.columns(2)
                with c1: 
                    m_urun = st.selectbox("Ürün Adı Sütunu:", all_cols, placeholder="Seçiniz")
                    m_marka = st.selectbox("Marka Sütunu:", all_cols, placeholder="Seçiniz")
                    m_resim_url = st.selectbox("Resim URL Sütunu:", all_cols, placeholder="Seçiniz")
                with c2: 
                    m_stok_kodu = st.selectbox("Stok Kodu (SKU) Sütunu:", all_cols, placeholder="Seçiniz")
                    m_kategori = st.selectbox("Kategori Sütunu:", all_cols, placeholder="Seçiniz")
                    m_fiyat_ref = st.selectbox("Fiyat Sütunu:", all_cols, placeholder="Seçiniz")

                if st.button("Eşleştirmeyi Onayla", type="primary"):
                    st.session_state.column_map = {'urun': m_urun, 'marka': m_marka, 'stok_kodu': m_stok_kodu, 'kategori': m_kategori, 'resim_url': m_resim_url, 'fiyat_ref': m_fiyat_ref}
                    st.session_state.mapping_done = True
                    st.rerun()
            else:
                map_info = st.session_state.column_map
                with st.sidebar:
                    st.divider()
                    s_yonu = st.selectbox("Fiyat Sıralaması:", ["Varsayılan", "Düşükten Yükseğe", "Yüksekten Düşüğe"])
                    s_marka = st.multiselect("Markalar:", st.session_state.master_df[map_info['marka']].unique(), placeholder="Seçiniz")
                    s_kategori = st.multiselect("Kategoriler:", st.session_state.master_df[map_info['kategori']].unique(), placeholder="Seçiniz")
                    
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
                arama = st.text_input("Ürünlerde Ara:", placeholder="Ürün Adı veya Stok Kodu Girin")
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
                    page_input = st.text_input("S", value=str(st.session_state.current_page), label_visibility="collapsed")
                    if page_input.isdigit() and int(page_input) != st.session_state.current_page:
                        st.session_state.current_page = int(page_input); st.rerun()
                with nc3:
                    if st.button("Geri", disabled=(st.session_state.current_page <= 1)): st.session_state.current_page -= 1; st.rerun()
                with nc4:
                    if st.button("İleri", disabled=(st.session_state.current_page >= toplam_s)): st.session_state.current_page += 1; st.rerun()
                with nc5: select_page = st.checkbox("Sayfadaki Tümünü Seç", key="sel_all_page")
                st.markdown("</div>", unsafe_allow_html=True)

                dilim_df = df_f.drop(columns=['_price_num']).iloc[(st.session_state.current_page - 1) * sayfa_boyutu : st.session_state.current_page * sayfa_boyutu].copy()
                dilim_df.insert(0, "Seç", select_page)
                edited_df = st.data_editor(dilim_df, use_container_width=True, hide_index=True, column_config={"Seç": st.column_config.CheckboxColumn("Seç", default=False), excel_satir_kolonu: st.column_config.TextColumn(excel_satir_kolonu, disabled=True)}, key="main_table_edit")

                if not edited_df.drop(columns=["Seç"]).equals(dilim_df.drop(columns=["Seç"])):
                    if st.button("Değişiklikleri Kaydet", type="primary"):
                        st.session_state.master_df.update(edited_df.drop(columns=["Seç"])); st.success("Kaydedildi."); st.rerun()

                curr_sel = edited_df[edited_df["Seç"] == True].index.tolist()
                for idx in curr_sel: st.session_state.selected_global_indices.add(idx)
                curr_unsel = edited_df[edited_df["Seç"] == False].index.tolist()
                for idx in curr_unsel: st.session_state.selected_global_indices.discard(idx)
                if st.session_state.selected_global_indices:
                    if st.button("Seçimleri Temizle"): st.session_state.selected_global_indices = set(); st.rerun()

                st.divider()
                with st.expander("Fiyat Güncelleme Paneli", expanded=True):
                    g_mod = st.radio("Kapsam:", ["Tüm Filtreli Liste", "Sadece Seçili Ürünler"], horizontal=True)
                    hedef = df_f.index if g_mod == "Tüm Filtreli Liste" else list(st.session_state.selected_global_indices)
                    if len(hedef) > 0:
                        st.info(f"Şu an **{len(hedef)}** ürün üzerinde işlem yapmaktasınız.")
                        c_m1, c_m2, c_m3, c_m4 = st.columns([2, 1, 1, 1])
                        with c_m1: t_cols = st.multiselect("Güncellenecek Sütunlar:", [c for c in st.session_state.master_df.columns if not c.startswith('Yeni ') and c != excel_satir_kolonu], placeholder="Sütun Seçiniz")
                        with c_m2: i_tip = st.selectbox("Yöntem:", ["Yüzdesel (%)", "Sabit (+/-)", "Kat Sayı (x)"])
                        with c_m3: i_deg = st.number_input("Değer:", value=0.0)
                        with c_m4: i_yon = st.selectbox("Yön:", ["Arttır", "Düşür"])
                        if st.button("Uygula", type="primary"):
                            for c in t_cols:
                                new_c = f"Yeni {c}"
                                base = pd.to_numeric(st.session_state.master_df[c], errors='coerce').fillna(0)
                                if new_c not in st.session_state.master_df.columns: st.session_state.master_df[new_c] = base
                                oran = ((1 + i_deg/100) if i_yon == "Arttır" else (1 - i_deg/100))
                                if i_tip == "Yüzdesel (%)": st.session_state.master_df.loc[hedef, new_c] = base.loc[hedef] * oran
                                elif i_tip == "Kat Sayı (x)": st.session_state.master_df.loc[hedef, new_c] = base.loc[hedef] * i_deg
                                else: st.session_state.master_df.loc[hedef, new_c] = base.loc[hedef] + (i_deg if i_yon == "Arttır" else -i_deg)
                            st.rerun()
                    else: st.warning("Lütfen tablodan ürün seçiniz.")

                if st.session_state.selected_global_indices:
                    v_idx = [i for i in st.session_state.selected_global_indices if i in st.session_state.master_df.index]
                    if v_idx:
                        p = st.session_state.master_df.loc[v_idx[0]]
                        st.markdown("<div class='product-card-container'>", unsafe_allow_html=True)
                        ci, cd = st.columns([1, 4])
                        with ci:
                            img_url = p[map_info['resim_url']]
                            if pd.notna(img_url) and str(img_url).startswith('http'): st.image(img_url, use_container_width=True)
                            else: st.info("Görsel Yok")
                        with cd:
                            st.markdown(f"<div class='product-title'>{p[map_info['urun']]}</div>", unsafe_allow_html=True)
                            st.markdown(f"""<div class='product-details'>
                                <span class='detail-label'>Marka:</span> <span class="detail-value">{p[map_info['marka']]}</span><br>
                                <span class='detail-label'>SKU:</span> <span class="detail-value">{p[map_info['stok_kodu']]}</span><br>
                                <span class='detail-label'>Kategori:</span> <span class="detail-value">{p[map_info['kategori']]}</span>
                            </div>""", unsafe_allow_html=True)
                            y_f = f"Yeni {map_info['fiyat_ref']}"
                            p_curr = pd.to_numeric(p[map_info['fiyat_ref']], errors='coerce')
                            if y_f in p.index and pd.notna(p[y_f]): st.markdown(f"<span style='color:#ff4b4b; text-decoration:line-through; margin-right:10px;'>{p_curr:,.2f} TL</span> <span style='color:#00ff88; font-size:22px; font-weight:bold;'>{p[y_f]:,.2f} TL</span>", unsafe_allow_html=True)
                            else: st.markdown(f"<span style='color:#7fbbff; font-size:20px; font-weight:bold;'>{p_curr:,.2f} TL</span>", unsafe_allow_html=True)
                            st.link_button("Sitede Gör", f"https://aletedevat.com.tr/magaza/{create_slug(p[map_info['urun']])}/", type="primary")
                        st.markdown("</div>", unsafe_allow_html=True)

                st.divider()
                d1, d2 = st.columns(2)
                with d1: st.download_button("Dosyayı CSV Olarak İndir", st.session_state.master_df.to_csv(index=False).encode('utf-8'), "aletedevat_guncel.csv", use_container_width=True)
                with d2:
                    out = BytesIO()
                    with pd.ExcelWriter(out, engine='xlsxwriter') as w: st.session_state.master_df.to_excel(w, index=False)
                    st.download_button("Dosyayı Excel Olarak İndir", out.getvalue(), "aletedevat_guncel.xlsx", use_container_width=True)
        else: st.info("Sol Taraftan Excel Dosyanızı Yükleyin.")

    elif modul == "Alan Eşleme Paneli":
        st.subheader("Alan Eşleme ve Şablon Oluşturma")
        tpl_file = st.file_uploader("Şablon Dosyası", type=['xlsx', 'csv'], key="tpl_up")
        if tpl_file:
            tpl_df = pd.read_excel(tpl_file) if tpl_file.name.endswith('xlsx') else pd.read_csv(tpl_file)
            tpl_cols = tpl_df.columns.tolist()
            with st.expander("Şablon Sütunlarını Sisteme Tanımlayın", expanded=True):
                tpl_map = {}
                c1, c2 = st.columns(2)
                for i, field in enumerate(ZORUNLU_ALANLAR):
                    with c1 if i < 8 else c2: tpl_map[field] = st.selectbox(f"{field} Sütunu:", ["Boş Bırak"] + tpl_cols, key=f"tpl_{field}")
            st.divider()
            src_file = st.file_uploader("Kendi Ürün Listeniz", type=['xlsx', 'csv'], key="src_up")
            if src_file:
                src_df = pd.read_excel(src_file) if src_file.name.endswith('xlsx') else pd.read_csv(src_file)
                src_cols = src_df.columns.tolist()
                with st.expander("Kendi Sütunlarınızı Eşleştirin", expanded=True):
                    src_map = {}
                    sc1, sc2 = st.columns(2)
                    for i, field in enumerate(ZORUNLU_ALANLAR):
                        if tpl_map[field] != "Boş Bırak":
                            with sc1 if i < 8 else sc2: src_map[field] = st.selectbox(f"{field} için Veri Sütunu:", ["Veri Yok"] + src_cols, key=f"src_{field}")
                if st.button("Verileri Şablona Naklet ve Hazırla", type="primary", use_container_width=True):
                    final_df = pd.DataFrame(columns=tpl_cols)
                    rows_list = []
                    for _, row in src_df.iterrows():
                        new_row = {col: "" for col in tpl_cols}
                        for field in ZORUNLU_ALANLAR:
                            target_col = tpl_map[field]; source_col = src_map.get(field, "Veri Yok")
                            if target_col != "Boş Bırak" and source_col != "Veri Yok": new_row[target_col] = row[source_col]
                        rows_list.append(new_row)
                    final_df = pd.DataFrame(rows_list)
                    st.success(f"Başarılı! {len(final_df)} adet ürün şablona yerleştirildi.")
                    st.dataframe(final_df, use_container_width=True, height=600)
                    out_map = BytesIO()
                    with pd.ExcelWriter(out_map, engine='xlsxwriter') as w: final_df.to_excel(w, index=False)
                    st.download_button("Excel İndir", out_map.getvalue(), "pazaryeri_listesi.xlsx", use_container_width=True, type="primary")

    # --- ALT NAVİGASYON (SIFIRLA VE ÇIKIŞ EN ALTA) ---
    with st.sidebar:
        st.divider()
        if not st.session_state.master_df.empty:
            if st.button("Sistemi Sıfırla (Hafızayı Temizle)", use_container_width=True):
                st.session_state.master_df = pd.DataFrame(); st.session_state.mapping_done = False; st.rerun()
        
        st.markdown('<div class="red-button">', unsafe_allow_html=True)
        if st.button("Güvenli Çıkış", use_container_width=True):
            st.session_state.authenticated = False; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
