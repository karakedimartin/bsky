import requests
import time
import os
import json
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Ortam değişkenlerinden kimlik bilgilerini al
BSKY_KULLANICI_ADI = os.getenv("BLUESKY_USERNAME")
BSKY_SIFRE = os.getenv("BLUESKY_PASSWORD")

# Ollama ayarlarını al
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

# --- Yardımcı Fonksiyonlar (bsunfollow.py'den kopyalandı ve uyarlandı) ---

# 1. Giriş 
def giris_yap():
    # ... (Giriş fonksiyonu bsunfollow.py'deki ile aynı) ...
    kullanici_adi = BSKY_KULLANICI_ADI
    sifre = BSKY_SIFRE

    if not kullanici_adi or not sifre:
        print("[X] HATA: BLUESKY_USERNAME ve BLUESKY_PASSWORD ortam değişkenleri .env dosyasında ayarlanmamış!")
        return None, None

    url = "https://bsky.social/xrpc/com.atproto.server.createSession"
    print(f"[*] {kullanici_adi} için giriş deneniyor...")
    try:
        yanit = requests.post(url, json={"identifier": kullanici_adi, "password": sifre}, timeout=15)
        yanit.raise_for_status()
        veri = yanit.json()
        print("[✓] Giriş başarılı!")
        return veri.get("accessJwt"), veri.get("did")
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
        return None, None

# 2. "Takip Edilenler" listesini al (Sadece DID ve Handle yeterli)
def benim_takip_ettiklerimi_al(kullanici_adim, jwt):
    print(f"[*] 'Takip Edilenler' listen ({kullanici_adim}) alınıyor...")
    url = f"https://bsky.social/xrpc/app.bsky.graph.getFollows?actor={kullanici_adim}"
    takip_verileri = [] # Sözlük listesi {did, handle}
    imlec = None
    basliklar = {"Authorization": f"Bearer {jwt}"}
    while True:
        tam_url = url + (f"&cursor={imlec}" if imlec else "")
        try:
            yanit = requests.get(tam_url, headers=basliklar, timeout=30)
            if yanit.status_code == 401:
                print("[!] Takip edilenler alınırken token süresi doldu.")
                return None # Yeniden giriş gerekli
            yanit.raise_for_status()
            veri = yanit.json()
            takip_edilenler_grubu = veri.get('follows', [])
            if not takip_edilenler_grubu and imlec is None and not takip_verileri:
                 print(f"[i] Görünüşe göre ({kullanici_adim}) kimseyi takip etmiyorsun.")
                 break
            if not takip_edilenler_grubu and imlec: break
            for takip_kaydi in takip_edilenler_grubu:
                 if 'did' in takip_kaydi:
                     takip_verileri.append({'did': takip_kaydi['did'], 'handle': takip_kaydi.get('handle', 'bilinmiyor')})
                 else:
                     print(f"[?] Uyarı: Takip kaydında eksik 'did': {takip_kaydi}")

            imlec = veri.get('cursor')
            if not imlec: break
            print(f"[*] Şimdiye kadar {len(takip_verileri)} takip edilen bulundu...")
            time.sleep(0.2)
        except requests.exceptions.RequestException as e:
            durum_kodu = e.response.status_code if e.response is not None else "N/A"
            print(f"[X] Takip edilenler alınırken HATA! Durum: {durum_kodu} | URL: {tam_url} | Hata: {e}")
            return None 
    print(f"[✓] {len(takip_verileri)} 'Takip Edilen' kaydı bulundu.")
    return takip_verileri

# 3. Kullanıcı profil bilgilerini al
def get_profile(actor_did, jwt):
    # ... (Fonksiyon bsunfollow.py'deki ile aynı) ...
    print(f"[*] Profil bilgisi alınıyor: {actor_did}")
    url = f"https://bsky.social/xrpc/app.bsky.actor.getProfile?actor={actor_did}"
    basliklar = {"Authorization": f"Bearer {jwt}"}
    try:
        yanit = requests.get(url, headers=basliklar, timeout=20)
        if yanit.status_code == 401:
            print(f"[!] Profil alınırken token süresi doldu: {actor_did}")
            return None 
        yanit.raise_for_status()
        veri = yanit.json()
        profil = {
            "handle": veri.get("handle", "N/A"),
            "displayName": veri.get("displayName", ""),
            "description": veri.get("description", "")
        }
        return profil
    except requests.exceptions.RequestException as e:
        durum_kodu = e.response.status_code if e.response is not None else "N/A"
        print(f"[X] Profil alınırken HATA ({actor_did})! Durum: {durum_kodu} | Hata: {e}")
        return {} 

# 4. Kullanıcının gönderilerini/feed'ini al
def get_author_feed(actor_did, jwt, limit=25):
    # ... (Fonksiyon bsunfollow.py'deki ile aynı) ...
    print(f"[*] Gönderiler/Feed alınıyor: {actor_did} (limit: {limit})")
    url = f"https://bsky.social/xrpc/app.bsky.feed.getAuthorFeed?actor={actor_did}&limit={limit}"
    basliklar = {"Authorization": f"Bearer {jwt}"}
    feed_items = []
    imlec = None
    try:
        yanit = requests.get(url, headers=basliklar, timeout=45)
        if yanit.status_code == 401:
            print(f"[!] Feed alınırken token süresi doldu: {actor_did}")
            return None
        yanit.raise_for_status()
        veri = yanit.json()
        feed_list = veri.get('feed', [])
        for item in feed_list:
            post_text = item.get('post', {}).get('record', {}).get('text', '')
            reply_parent_uri = item.get('reply', {}).get('parent', {}).get('uri')
            if post_text:
                feed_items.append({
                    "text": post_text,
                    "is_reply": bool(reply_parent_uri)
                })
        return feed_items
    except requests.exceptions.RequestException as e:
        durum_kodu = e.response.status_code if e.response is not None else "N/A"
        print(f"[X] Feed alınırken HATA ({actor_did})! Durum: {durum_kodu} | Hata: {e}")
        return []

# 5. Kullanıcı verilerini Ollama ile analiz et
def analyze_user_with_ollama(profile_info, feed_items):
    # ... (Fonksiyon bsunfollow.py'deki ile aynı, sadece handle daha güvenilir) ...
    handle = profile_info.get('handle', 'Bilinmeyen')
    print(f"[*] Ollama ile analiz ediliyor: {handle}...")
    analysis_text = f"Profil Bilgileri:\nAd: {profile_info.get('displayName', '')}\nAçıklama: {profile_info.get('description', '')}\n\nSon Gönderiler/Yanıtlar:\n"
    for i, item in enumerate(feed_items):
        item_type = "Yanıt" if item['is_reply'] else "Gönderi"
        analysis_text += f"{i+1}. ({item_type}): {item['text']}\n"
        if i > 30: analysis_text += "... (daha fazla gönderi kısaltıldı)\n"; break
    prompt = f"""Aşağıdaki Bluesky kullanıcısının profil bilgileri ve son gönderileri verilmiştir. Bu metinlere dayanarak, kullanıcının güçlü bir şekilde AKP (Adalet ve Kalkınma Partisi) veya Recep Tayyip Erdoğan destekçisi olma olasılığı yüksek mi? Sadece 'EVET' veya 'HAYIR' yanıtı ver.

{analysis_text}

Yanıt (EVET/HAYIR):"""
    ollama_api_url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}}
    try:
        response = requests.post(ollama_api_url, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        ollama_response = result.get('response', '').strip().upper()
        print(f"[✓] Ollama yanıtı ({handle}): '{ollama_response}'")
        return "EVET" in ollama_response
    except requests.exceptions.RequestException as e:
        print(f"[X] Ollama ile iletişimde HATA ({handle})! URL: {ollama_api_url} | Hata: {e}")
        if e.response is not None: print(f"    Ollama Yanıtı: {e.response.text}")
        print("[*] Ollama hatası nedeniyle analiz başarısız.")
        return False
    except json.JSONDecodeError as e:
        print(f"[X] Ollama yanıtı JSON olarak ayrıştırılamadı ({handle})! Hata: {e}")
        print(f"    Alınan Yanıt: {response.text}")
        return False

# --- Ana Analiz Mantığı ---

def analyze_followings():
    print("[*] Takip edilenleri politik görüş (AKP) için analiz etme betiği.")
    print("[!] BU BETİK KİMSEYİ TAKİPTEN ÇIKARMAZ! Sadece analiz yapar ve listeyi dosyaya yazar.")
    
    if not OLLAMA_MODEL:
        print("[X] HATA: .env dosyasında OLLAMA_MODEL değişkeni ayarlanmamış. Analiz yapılamaz.")
        return

    print(f"[*] Ollama analizi etkin. Model: {OLLAMA_MODEL}, URL: {OLLAMA_BASE_URL}")
    try:
        print(f"[*] Ollama API erişimi kontrol ediliyor: {OLLAMA_BASE_URL} ...")
        test_response = requests.get(f"{OLLAMA_BASE_URL}", timeout=5)
        test_response.raise_for_status()
        print("[✓] Ollama API'sine erişilebiliyor.")
    except requests.exceptions.RequestException as e:
        print(f"[X] HATA: Ollama API'sine erişilemiyor ({OLLAMA_BASE_URL}). Hata: {e}")
        print("[*] Lütfen Ollama'nın çalıştığından ve URL'nin doğru olduğundan emin olun.")
        return

    # --- Giriş ---
    jwt, benim_did = giris_yap()
    if not jwt or not benim_did: return
    kendi_kullanici_adim = BSKY_KULLANICI_ADI

    # --- Takip Edilenleri Al ---
    print("\n--- Takip Edilenler Alınıyor ---")
    takip_ettiklerim_listesi = benim_takip_ettiklerimi_al(kendi_kullanici_adim, jwt)
    if takip_ettiklerim_listesi is None:
        print("[*] Yeniden giriş deneniyor (Takip Edilenler)...")
        jwt, benim_did = giris_yap();
        if not jwt or not benim_did: print("[X] Yeniden giriş başarısız."); return
        takip_ettiklerim_listesi = benim_takip_ettiklerimi_al(kendi_kullanici_adim, jwt)
        if takip_ettiklerim_listesi is None: print("[X] Takip edilenler alınamadı."); return

    print(f"[*] Analiz edilecek toplam takip edilen sayısı: {len(takip_ettiklerim_listesi)}")

    # --- Analiz Döngüsü ---
    print("\n--- Analiz Döngüsü Başlatılıyor --- (Bu işlem uzun sürebilir!)")
    identified_supporters = []
    analysis_errors = 0

    for i, user_data in enumerate(takip_ettiklerim_listesi):
        hedef_did = user_data['did']
        handle = user_data.get('handle', hedef_did)

        print(f"\n--- Kullanıcı {i+1}/{len(takip_ettiklerim_listesi)} Analiz Ediliyor: {handle} ({hedef_did}) ---")

        # Profil ve feed bilgilerini al
        profil_info = get_profile(hedef_did, jwt)
        if profil_info is None: # Token süresi doldu
            print("[*] Yeniden giriş deneniyor (Profil)...")
            jwt, benim_did = giris_yap();
            if not jwt or not benim_did: print("[X] Yeniden giriş başarısız. Kalan kullanıcılar atlanıyor."); break # Döngüden çık
            profil_info = get_profile(hedef_did, jwt)
            if profil_info is None: print(f"[X] Yeniden giriş sonrası profil alınamadı ({handle}). Atlanıyor."); analysis_errors += 1; continue
        
        # Handle'ı profilden gelen ile güncelle (daha güvenilir)
        handle = profil_info.get("handle", handle) 

        feed_items = get_author_feed(hedef_did, jwt, limit=25)
        if feed_items is None: # Token süresi doldu
            print("[*] Yeniden giriş deneniyor (Feed)...")
            jwt, benim_did = giris_yap();
            if not jwt or not benim_did: print("[X] Yeniden giriş başarısız. Kalan kullanıcılar atlanıyor."); break # Döngüden çık
            feed_items = get_author_feed(hedef_did, jwt, limit=25)
            if feed_items is None: print(f"[X] Yeniden giriş sonrası feed alınamadı ({handle}). Atlanıyor."); analysis_errors += 1; continue

        # Ollama ile analiz et
        is_akp_supporter = analyze_user_with_ollama(profil_info, feed_items)
        if is_akp_supporter:
            print(f"[!] Bir TAYYIPCI bulundu: {handle}")
            identified_supporters.append(handle)
            try:
                with open("tayyipci_listesi.txt", "a", encoding="utf-8") as f:
                    f.write(f"{handle}\n")
                print(f"[*] {handle} ismi tayyipci_listesi.txt dosyasına eklendi.")
            except Exception as e:
                print(f"[X] Dosyaya yazma hatası (tayyipci_listesi.txt): {e}")

        # API limitlerini aşmamak için bekle
        print("[*] Sonraki kullanıcıya geçmeden önce kısa bir süre bekleniyor...")
        time.sleep(3) 

    # --- Analiz Sonu Raporu ---
    print("\n--- Analiz Tamamlandı ---")
    print(f"[*] Toplam {len(takip_ettiklerim_listesi)} kullanıcı analiz edildi.")
    print(f"[*] {len(identified_supporters)} kullanıcı potansiyel TAYYIPCI olarak işaretlendi.")
    if analysis_errors > 0:
        print(f"[!] Analiz sırasında {analysis_errors} kullanıcı için hata oluştu (atlandı).")
    print("[*] İşaretlenen kullanıcıların listesi 'tayyipci_listesi.txt' dosyasına yazıldı.")
    print("[*] BU BETİK KİMSEYİ TAKİPTEN ÇIKARMADI.")


# -----------------------------
# KULLANIM
# -----------------------------
if __name__ == "__main__":
    print("UYARI: Bu betik, takip ettiğiniz kişileri yerel LLM (Ollama) kullanarak")
    print("       belirli bir politik görüşe (AKP) sahip olup olmadıkları açısından analiz eder.")
    print("       >> LLM ANALİZİ DENEYSELDİR VE HATALI OLABİLİR! <<")
    print("       >> BU BETİK OTOMATİK OLARAK KİMSEYİ TAKİPTEN ÇIKARMAZ! <<")
    print("       Sadece potansiyel destekçileri listeler ve bir dosyaya yazar.")
    print("       .env dosyasındaki kimlik bilgilerini ve Ollama ayarlarını kontrol edin.")
    print("-" * 30)

    # Başlangıçta ortam değişkenlerini kontrol et
    if not BSKY_KULLANICI_ADI or not BSKY_SIFRE:
        print("[X] Lütfen proje klasöründe bir .env dosyası oluşturun ve içine BLUESKY_USERNAME ve BLUESKY_PASSWORD değişkenlerini ayarlayın.")
    elif not OLLAMA_MODEL:
         print("[X] HATA: .env dosyasında OLLAMA_MODEL değişkeni ayarlanmamış. Analiz yapılamaz.")
    else:
        # Ana analiz fonksiyonunu çağır
        analyze_followings() 