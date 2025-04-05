import requests
import time
import os
import json
from dotenv import load_dotenv
from datetime import datetime

# .env dosyasını yükle
load_dotenv()

# Ortam değişkenlerinden kimlik bilgilerini al
BSKY_KULLANICI_ADI = os.getenv("BLUESKY_USERNAME")
BSKY_SIFRE = os.getenv("BLUESKY_PASSWORD")

# Ollama ayarlarını al
OLLAMA_API_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

ANALIZ_LOG_DOSYASI = "analiz_sonuclari.txt" # Log dosyasının adı

# --- Yardımcı Fonksiyonlar (bsautofollow.py'den kopyalandı/uyarlandı) ---

# requests için oturum (session) oluştur, bağlantıları tekrar kullanır
session = requests.Session()
erisim_tokeni = None
kendi_didim = None
kendi_handle = None

# 1. Giriş
def giris_yap():
    global erisim_tokeni, kendi_didim, kendi_handle
    kullanici_adi = BSKY_KULLANICI_ADI
    sifre = BSKY_SIFRE

    if not kullanici_adi or not sifre:
        print("[X] HATA: BLUESKY_USERNAME ve BLUESKY_PASSWORD ortam değişkenleri .env dosyasında ayarlanmamış!")
        return False

    url = "https://bsky.social/xrpc/com.atproto.server.createSession"
    print(f"[*] {kullanici_adi} için giriş deneniyor...")
    try:
        yanit = session.post(url, json={"identifier": kullanici_adi, "password": sifre}, timeout=15)
        yanit.raise_for_status()
        veri = yanit.json()
        erisim_tokeni = veri.get("accessJwt")
        kendi_didim = veri.get("did")
        kendi_handle = veri.get("handle")
        if not erisim_tokeni or not kendi_didim:
             print("[HATA] Bluesky'den geçerli bir erişim token'ı veya DID alınamadı.")
             return False
        session.headers.update({'Authorization': f'Bearer {erisim_tokeni}'})
        print("[✓] Giriş başarılı!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[X] GİRİŞ HATASI! URL: {url}")
        hata_mesaji = ""
        if e.response is not None:
            if e.response.status_code == 401:
                 hata_mesaji = "Giriş başarısız. Kullanıcı adı veya şifre yanlış olabilir."
            elif e.response.status_code == 400 and "Invalid identifier or password" in e.response.text:
                 hata_mesaji = "Giriş başarısız. Kullanıcı adı veya şifre yanlış olabilir."
            else:
                 hata_mesaji = f"Durum Kodu: {e.response.status_code} | Yanıt: {e.response.text}"
        else:
            hata_mesaji = f"Hata: {e}"
        print(f"    {hata_mesaji}")
        return False
    except json.JSONDecodeError:
        print("[HATA] Bluesky'den giriş yapılırken geçersiz JSON yanıtı alındı.")
        return False

# Sayfalama yardımcısı (bsautofollow.py'den)
def get_paginated_results(endpoint, params, data_key, limit=None):
    sonuclar = []
    cursor = None
    params['limit'] = 100 # İstek başına varsayılan limit

    while True:
        if cursor:
            params['cursor'] = cursor
        try:
            time.sleep(1) # API çağrıları arasında kısa bekleme
            response = session.get(endpoint, params=params, timeout=20)
            response.raise_for_status()
            veri = response.json()
            ogeler = veri.get(data_key, [])
            if not ogeler:
                break
            sonuclar.extend(ogeler)
            if limit is not None and len(sonuclar) >= limit:
                 sonuclar = sonuclar[:limit]
                 break
            cursor = veri.get('cursor')
            if not cursor:
                break
        except requests.exceptions.RequestException as e:
            print(f"[HATA] {endpoint} adresinden veri alınırken hata: {e}")
            if e.response is not None and e.response.status_code == 401: 
                print("[UYARI] Token süresi dolmuş olabilir. Yeniden giriş deneniyor...")
                if not giris_yap():
                    print("[HATA] Yeniden giriş başarısız oldu. İşlem durduruluyor.")
                    return None 
                print("[BİLGİ] Yeniden giriş başarılı. Son istek tekrarlanıyor...")
                continue
            print(f"[HATA] Devam edilemeyen hata ({e.response.status_code if e.response else 'N/A'}). Veri alımı durduruldu.")
            return None # Hata durumunu belirtmek için None döndür
        except json.JSONDecodeError:
            print(f"[HATA] {endpoint} adresinden geçersiz JSON yanıtı alındı.")
            return None # Hata durumunu belirtmek için None döndür
    return sonuclar

# 2. "Takip Edilenler" listesini al (Sadece DID ve Handle yeterli)
def benim_takip_ettiklerimi_al():
    if not kendi_handle: 
        print("[HATA] Giriş yapılmadığı için handle bilinmiyor.")
        return None
    print(f"[*] 'Takip Edilenler' listen ({kendi_handle}) alınıyor...")
    endpoint = f"https://bsky.social/xrpc/app.bsky.graph.getFollows"
    params = {'actor': kendi_handle}
    takip_edilenler = get_paginated_results(endpoint, params, 'follows')

    if takip_edilenler is None: return None # Hata oluştu

    takip_verileri = []
    for takip_kaydi in takip_edilenler:
         if 'did' in takip_kaydi:
             takip_verileri.append({'did': takip_kaydi['did'], 'handle': takip_kaydi.get('handle', 'bilinmiyor')})
         else:
             print(f"[?] Uyarı: Takip kaydında eksik 'did': {takip_kaydi}")
    
    print(f"[✓] {len(takip_verileri)} 'Takip Edilen' kaydı bulundu.")
    return takip_verileri

# 3. Kullanıcı profil bilgilerini al
def get_profile(actor_did):
    print(f"[*] Profil bilgisi alınıyor: {actor_did}")
    url = f"https://bsky.social/xrpc/app.bsky.actor.getProfile?actor={actor_did}"
    try:
        time.sleep(1)
        yanit = session.get(url, timeout=20)
        if yanit.status_code == 401:
            print(f"[!] Profil alınırken token süresi doldu: {actor_did}")
            return None # Yeniden giriş sinyali
        yanit.raise_for_status()
        veri = yanit.json()
        profil = {
            "handle": veri.get("handle", actor_did), # Handle yoksa DID kullan
            "displayName": veri.get("displayName", ""),
            "description": veri.get("description", "")
        }
        return profil
    except requests.exceptions.RequestException as e:
        durum_kodu = e.response.status_code if e.response is not None else "N/A"
        print(f"[X] Profil alınırken HATA ({actor_did})! Durum: {durum_kodu} | Hata: {e}")
        return {} # Başarısız ama devam et
    except json.JSONDecodeError:
        print(f"[HATA] {actor_did} için profil alınırken geçersiz JSON yanıtı.")
        return {}

# 4. Kullanıcının gönderilerini/feed'ini al
def get_author_feed(actor_did, limit=5):
    print(f"[*] Gönderiler/Feed alınıyor: {actor_did} (limit: {limit})")
    url = f"https://bsky.social/xrpc/app.bsky.feed.getAuthorFeed?actor={actor_did}&limit={limit}"
    try:
        time.sleep(1)
        yanit = session.get(url, timeout=30)
        if yanit.status_code == 401:
            print(f"[!] Feed alınırken token süresi doldu: {actor_did}")
            return None # Yeniden giriş sinyali
        yanit.raise_for_status()
        veri = yanit.json()
        feed_list = veri.get('feed', [])
        feed_items = []
        for item in feed_list:
            post_record = item.get('post', {}).get('record', {})
            # Sadece orijinal gönderileri dikkate al
            if post_record.get('@type') == 'app.bsky.feed.post' and not post_record.get('reply'):
                post_text = post_record.get('text', '')
                if post_text:
                    feed_items.append({"text": post_text})
        return feed_items
    except requests.exceptions.RequestException as e:
        durum_kodu = e.response.status_code if e.response is not None else "N/A"
        print(f"[X] Feed alınırken HATA ({actor_did})! Durum: {durum_kodu} | Hata: {e}")
        return [] # Başarısız ama devam et
    except json.JSONDecodeError:
        print(f"[HATA] {actor_did} için gönderi akışı alınırken geçersiz JSON yanıtı.")
        return []

# 5. Kullanıcı verilerini Ollama ile DETAYLI analiz et
def kullaniciyi_detayli_analiz_et(handle, profil_info, feed_items):
    if not OLLAMA_MODEL or not OLLAMA_API_BASE:
        print("[HATA] Ollama yapılandırması eksik.")
        return None # Analiz yapılamadığını belirt

    print(f"[*] Ollama ile DETAYLI analiz ediliyor: {handle}...")
    profil_aciklamasi = profil_info.get('description', '')
    gorunen_ad = profil_info.get('displayName', '')
    gonderi_metinleri = "\n".join([item['text'] for item in feed_items])

    # --- DETAYLI ANALİZ İÇİN YENİ PROMPT --- 
    prompt = f"""
    Bluesky kullanıcısı '{handle}' hakkında aşağıdaki bilgilere dayanarak bir analiz yap:

    Profil Bilgileri:
    - Görünen Ad: {gorunen_ad}
    - Açıklama: {profil_aciklamasi}

    Son Gönderiler (en fazla 5):
    {gonderi_metinleri}

    Lütfen aşağıdaki 4 madde için değerlendirme yap (EVET, HAYIR veya BELİRSIZ olarak cevapla):
    1.  Dil Türkçe mi?
    2.  Laik/Seküler/Atatürkçü bir duruş var mı?
    3.  AKP/Erdoğan destekçisi bir duruş var mı?
    4.  Şeriat yanlısı/Aşırı Muhafazakar bir duruş var mı?

    Cevabını ŞU FORMATTA ver (her madde yeni satırda):
    Dil=YANIT
    Pozitif_Laik=YANIT
    Negatif_AKP=YANIT
    Negatif_Seriat=YANIT
    """

    ollama_api_url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}}
    
    try:
        time.sleep(1)
        response = requests.post(ollama_api_url, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        ollama_response_raw = result.get('response', '').strip()
        print(f"[✓] Ollama ham yanıtı ({handle}):\n{ollama_response_raw}")
        
        # Yanıtı ayrıştır
        analiz_sonuclari = {
            'Dil': 'BELİRSIZ',
            'Pozitif_Laik': 'BELİRSIZ',
            'Negatif_AKP': 'BELİRSIZ',
            'Negatif_Seriat': 'BELİRSIZ'
        }
        for line in ollama_response_raw.split('\n'):
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().upper()
                if key in analiz_sonuclari:
                    # Değeri EVET/HAYIR/BELIRSIZ olarak doğrula
                    if value in ['EVET', 'HAYIR', 'BELİRSIZ']:
                        analiz_sonuclari[key] = value
                    else:
                        print(f"[?] Uyarı: Ollama yanıtında geçersiz değer ({value}) bulundu, '{key}' için BELİRSIZ olarak ayarlandı.")
        
        return analiz_sonuclari

    except requests.exceptions.RequestException as e:
        print(f"[X] Ollama ile iletişimde HATA ({handle})! URL: {ollama_api_url} | Hata: {e}")
        if e.response is not None: print(f"    Ollama Yanıtı: {e.response.text}")
        print("[*] Ollama hatası nedeniyle analiz başarısız.")
        return None
    except json.JSONDecodeError as e:
        print(f"[X] Ollama yanıtı JSON olarak ayrıştırılamadı ({handle})! Hata: {e}")
        print(f"    Alınan Yanıt: {response.text}")
        return None

# --- Ana Analiz Mantığı --- 

def analyze_followings(): # Fonksiyon adını değiştirmedim
    print("[*] Takip edilenleri detaylı analiz etme betiği.")
    print(f"[!] Analiz sonuçları '{ANALIZ_LOG_DOSYASI}' dosyasına yazılacak.")
    
    if not OLLAMA_MODEL:
        print("[X] HATA: .env dosyasında OLLAMA_MODEL değişkeni ayarlanmamış. Analiz yapılamaz.")
        return

    print(f"[*] Ollama analizi etkin. Model: {OLLAMA_MODEL}, URL: {OLLAMA_BASE_URL}")
    try:
        print(f"[*] Ollama API erişimi kontrol ediliyor: {OLLAMA_BASE_URL} ...")
        test_response = session.head(f"{OLLAMA_BASE_URL}", timeout=5)
        test_response.raise_for_status()
        print("[✓] Ollama API'sine erişilebiliyor.")
    except requests.exceptions.RequestException as e:
        print(f"[X] HATA: Ollama API'sine erişilemiyor ({OLLAMA_BASE_URL}). Hata: {e}")
        print("[*] Lütfen Ollama'nın çalıştığından ve URL'nin doğru olduğundan emin olun.")
        return

    # --- Giriş ---
    if not giris_yap(): return

    # --- Takip Edilenleri Al ---
    print("\n--- Takip Edilenler Alınıyor ---")
    takip_ettiklerim_listesi = benim_takip_ettiklerimi_al()
    if takip_ettiklerim_listesi is None: 
        print("[X] Takip edilenler alınamadı. Betik durduruluyor."); return

    print(f"[*] Analiz edilecek toplam takip edilen sayısı: {len(takip_ettiklerim_listesi)}")

    # --- Analiz Döngüsü ---
    print("\n--- Analiz Döngüsü Başlatılıyor --- (Bu işlem uzun sürebilir!)")
    analiz_hatalari = 0
    log_dosyasi_acik = False
    try:
        # Log dosyasını yazma modunda aç (önceki içeriği siler)
        with open(ANALIZ_LOG_DOSYASI, "w", encoding="utf-8") as log_file:
            log_dosyasi_acik = True
            log_file.write(f"# Analiz Başlangıcı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write("# Format: handle: Dil=... | Pozitif_Laik=... | Negatif_AKP=... | Negatif_Seriat=...\n")
            log_file.write("-"*50 + "\n")

            for i, user_data in enumerate(takip_ettiklerim_listesi):
                hedef_did = user_data['did']
                handle = user_data.get('handle', hedef_did)
                print(f"\n--- Kullanıcı {i+1}/{len(takip_ettiklerim_listesi)} Analiz Ediliyor: {handle} ({hedef_did}) ---")

                # Profil ve feed bilgilerini al
                profil_info = get_profile(hedef_did)
                while profil_info is None: # Token süresi doldu
                    print("[*] Yeniden giriş deneniyor (Profil)...")
                    if not giris_yap(): print("[X] Yeniden giriş başarısız. Kalan kullanıcılar atlanıyor."); break 
                    profil_info = get_profile(hedef_did)
                if profil_info is None: analiz_hatalari += 1; continue # Atla
                
                # Handle'ı profilden gelen ile güncelle (daha güvenilir)
                handle = profil_info.get("handle", handle) 

                feed_items = get_author_feed(hedef_did, limit=5)
                while feed_items is None: # Token süresi doldu
                    print("[*] Yeniden giriş deneniyor (Feed)...")
                    if not giris_yap(): print("[X] Yeniden giriş başarısız. Kalan kullanıcılar atlanıyor."); break
                    feed_items = get_author_feed(hedef_did, limit=5)
                if feed_items is None: analiz_hatalari += 1; continue # Atla

                # Ollama ile detaylı analiz et
                analiz_sonucu_dict = kullaniciyi_detayli_analiz_et(handle, profil_info, feed_items)
                
                if analiz_sonucu_dict:
                    # Analiz sonucunu formatla ve ekrana yazdır
                    sonuc_str = f"Dil={analiz_sonucu_dict['Dil']} | Pozitif_Laik={analiz_sonucu_dict['Pozitif_Laik']} | Negatif_AKP={analiz_sonucu_dict['Negatif_AKP']} | Negatif_Seriat={analiz_sonucu_dict['Negatif_Seriat']}"
                    print(f"[ANALİZ SONUCU] {handle}: {sonuc_str}")
                    # Log dosyasına yaz
                    log_file.write(f"{handle}: {sonuc_str}\n")
                else:
                    print(f"[X] {handle} için analiz başarısız oldu veya Ollama'dan geçerli yanıt alınamadı.")
                    analiz_hatalari += 1
                    log_file.write(f"{handle}: ANALİZ BAŞARISIZ\n") # Hatalı analizleri de logla
                
                # API limitlerini aşmamak için bekleme
                time.sleep(0.5) 
            
            # Döngü bittiğinde son satırı ekle
            log_file.write("-"*50 + "\n")
            log_file.write(f"# Analiz Bitişi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    except IOError as e:
        print(f"[X] HATA: Log dosyası '{ANALIZ_LOG_DOSYASI}' açılamadı veya yazılamadı: {e}")
    except Exception as e:
        print(f"[X] Beklenmedik bir hata oluştu: {e}")
    finally:
        if log_dosyasi_acik:
             print(f"[*] Analiz sonuçları '{ANALIZ_LOG_DOSYASI}' dosyasına kaydedildi.")
        else: 
             print(f"[*] Log dosyası oluşturulamadığı için sonuçlar kaydedilemedi.")

    # --- Özet --- 
    print("\n--- Analiz Özeti ---")
    print(f"[*] Toplam analiz edilen kullanıcı: {len(takip_ettiklerim_listesi)}")
    print(f"[*] Analiz sırasında oluşan hata sayısı: {analiz_hatalari}")
    print("[*] Analiz tamamlandı.")

if __name__ == "__main__":
    analyze_followings() 