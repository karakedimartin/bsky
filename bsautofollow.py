import os
import requests
import time
import json
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# --- Globale Değişkenler ve Ayarlar ---
BLUESKY_API_BASE = "https://bsky.social/xrpc"
OLLAMA_API_BASE = None  # .env dosyasından yüklenecek
OLLAMA_MODEL = None     # .env dosyasından yüklenecek
ARANACAK_HASHTAGLER = [] # .env dosyasından yüklenecek
POST_GETIRME_LIMITI = 5    # Analiz için kullanıcı başına gönderi sayısı
HASHTAG_BASINA_ARAMA_LIMITI = 50 # Hashtag başına maksimum kullanıcı
ISTEK_ZAMAN_ASIMI = 15    # HTTP istekleri için zaman aşımı (saniye)
API_BEKLEME_SURESI = 2      # Bluesky API çağrıları sonrası bekleme süresi (saniye)
OLLAMA_BEKLEME_SURESI = 1   # Ollama API çağrıları sonrası bekleme süresi (saniye)
TAKIP_BEKLEME_SURESI = 5    # Takip etme eylemleri sonrası bekleme süresi (saniye)

# --- Oturum Verileri ve İstatistikler için Global Değişkenler ---
session = requests.Session() # İstekler için oturum objesi
erisim_tokeni = None       # Bluesky API erişim token'ı
kendi_didim = None         # Oturum açan kullanıcının DID'i
kendi_handle = None        # Oturum açan kullanıcının handle'ı
takip_ettiklerim_didleri = set() # Takip edilenlerin DID kümesi
takipcilerim_didleri = set()     # Takipçilerin DID kümesi
yeni_takip_edilen_sayisi = 0    # Bu çalıştırmada yeni takip edilenlerin sayısı
zaten_takip_edilen_sayisi = 0   # Zaten takip edilen adayların sayısı
geri_takip_eden_aday_sayisi = 0 # Analiz edilen adaylardan geri takip edenlerin sayısı
islenen_didler = set()          # Aynı kullanıcının tekrar analiz edilmesini önlemek için

def lade_umgebungsvariablen(): # Fonksiyon adını Almanca bırakıyorum, çağrıldığı yer belli.
    """Ortam değişkenlerini .env dosyasından yükler."""
    global OLLAMA_API_BASE, OLLAMA_MODEL, ARANACAK_HASHTAGLER
    load_dotenv()
    kullanici_adi = os.getenv("BLUESKY_USERNAME")
    sifre = os.getenv("BLUESKY_PASSWORD")
    OLLAMA_API_BASE = os.getenv("OLLAMA_BASE_URL")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
    hashtags_str = os.getenv("SEARCH_HASHTAGS") # .env'deki değişken adı İngilizce kalmalı

    if not all([kullanici_adi, sifre, OLLAMA_API_BASE, OLLAMA_MODEL, hashtags_str]):
        print("[HATA] Gerekli tüm ortam değişkenleri bulunamadı!")
        print("Gerekenler: BLUESKY_USERNAME, BLUESKY_PASSWORD, OLLAMA_BASE_URL, OLLAMA_MODEL, SEARCH_HASHTAGS")
        exit(1)

    # SEARCH_HASHTAGS'ı virgüle göre ayır ve boşlukları temizle
    ARANACAK_HASHTAGLER = [tag.strip() for tag in hashtags_str.split(',') if tag.strip()]
    if not ARANACAK_HASHTAGLER:
        print("[HATA] .env dosyasındaki SEARCH_HASHTAGS içinde geçerli hashtag bulunamadı.")
        exit(1)

    print("[BİLGİ] Ortam değişkenleri yüklendi.")
    return kullanici_adi, sifre

def check_ollama_api(): # Fonksiyon adını Almanca bırakıyorum.
    """Ollama API'sinin erişilebilir olup olmadığını kontrol eder."""
    if not OLLAMA_API_BASE:
        print("[HATA] OLLAMA_BASE_URL ayarlanmamış.")
        return False
    try:
        # HEAD isteği daha hızlı olabilir, sadece bağlantı kontrolü için
        response = session.head(OLLAMA_API_BASE, timeout=5)
        response.raise_for_status()  # HTTP hatalarında (4xx, 5xx) exception fırlatır
        print(f"[BİLGİ] Ollama API ({OLLAMA_API_BASE}) erişilebilir.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[HATA] Ollama API ({OLLAMA_API_BASE}) erişilemiyor: {e}")
        return False

def giris_yap(kullanici_adi, sifre):
    """Bluesky'ye giriş yapar ve erişim token'ı alır."""
    global erisim_tokeni, kendi_didim, kendi_handle
    url = f"{BLUESKY_API_BASE}/com.atproto.server.createSession"
    payload = json.dumps({"identifier": kullanici_adi, "password": sifre})
    headers = {'Content-Type': 'application/json'}

    try:
        response = session.post(url, headers=headers, data=payload, timeout=ISTEK_ZAMAN_ASIMI)
        response.raise_for_status()
        veri = response.json()
        erisim_tokeni = veri.get('accessJwt')
        kendi_didim = veri.get('did')
        kendi_handle = veri.get('handle')
        if not erisim_tokeni or not kendi_didim:
            print("[HATA] Bluesky'den geçerli bir erişim token'ı veya DID alınamadı.")
            return False
        # Token'ı oturum başlıklarına ekle
        session.headers.update({'Authorization': f'Bearer {erisim_tokeni}'})
        print(f"[BİLGİ] Bluesky'ye {kendi_handle} ({kendi_didim}) olarak başarıyla giriş yapıldı.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[HATA] Bluesky'ye giriş yapılırken hata oluştu: {e}")
        if e.response is not None:
            print(f"[HATA] Sunucu yanıtı: {e.response.text}")
        return False
    except json.JSONDecodeError:
        print("[HATA] Bluesky'den giriş yapılırken geçersiz JSON yanıtı alındı.")
        return False

def get_paginated_results(endpoint, params, data_key, limit=None): # Fonksiyon adı İngilizce kalabilir
    """Bir Bluesky API uç noktasından sayfalanmış sonuçları alır."""
    sonuclar = []
    cursor = None
    params['limit'] = 100 # İstek başına varsayılan limit

    while True:
        if cursor:
            params['cursor'] = cursor
        try:
            time.sleep(API_BEKLEME_SURESI)
            response = session.get(endpoint, params=params, timeout=ISTEK_ZAMAN_ASIMI)
            response.raise_for_status()
            veri = response.json()

            ogeler = veri.get(data_key, [])
            if not ogeler:
                break # Başka öğe yok

            sonuclar.extend(ogeler)

            # Eğer bir limit belirtilmişse ve bu limite ulaşıldıysa
            if limit is not None and len(sonuclar) >= limit:
                 sonuclar = sonuclar[:limit] # Sonucu limite göre kırp
                 break

            cursor = veri.get('cursor')
            if not cursor:
                break # Cursor yoksa, tüm sayfalar yüklendi

        except requests.exceptions.RequestException as e:
            print(f"[HATA] {endpoint} adresinden veri alınırken hata: {e}")
            if e.response is not None and e.response.status_code == 401: # Token süresi dolmuş olabilir
                print("[UYARI] Token süresi dolmuş olabilir. Yeniden giriş deneniyor...")
                # Yeniden giriş yapmayı dene
                kullanici_adi_env = os.getenv("BLUESKY_USERNAME")
                sifre_env = os.getenv("BLUESKY_PASSWORD")
                if not kullanici_adi_env or not sifre_env:
                    print("[HATA] Yeniden giriş için kullanıcı adı/şifre ortam değişkenleri bulunamadı.")
                    return None # Hata durumunu belirt
                if not giris_yap(kullanici_adi_env, sifre_env):
                    print("[HATA] Yeniden giriş başarısız oldu. İşlem durduruluyor.")
                    return None # Hata durumunu belirt
                # Başarılı giriş sonrası aynı isteği tekrar dene
                print("[BİLGİ] Yeniden giriş başarılı. Son istek tekrarlanıyor...")
                continue
            # Diğer HTTP hatalarında döngüyü kır
            print(f"[HATA] Devam edilemeyen hata ({e.response.status_code if e.response else 'N/A'}). Veri alımı durduruldu.")
            break
        except json.JSONDecodeError:
            print(f"[HATA] {endpoint} adresinden geçersiz JSON yanıtı alındı.")
            break

    return sonuclar

def get_my_followings(): # Fonksiyon adı İngilizce kalabilir
    """Mevcut kullanıcının takip ettiği kişilerin DID'lerini alır."""
    global takip_ettiklerim_didleri
    print("[BİLGİ] Takip edilen kullanıcıların listesi alınıyor...")
    endpoint = f"{BLUESKY_API_BASE}/app.bsky.graph.getFollows"
    params = {'actor': kendi_handle}
    takip_edilenler = get_paginated_results(endpoint, params, 'follows')

    if takip_edilenler is None: # Sayfalama sırasında hata oluştu
         return False

    takip_ettiklerim_didleri = {takip['did'] for takip in takip_edilenler}
    print(f"[BİLGİ] {len(takip_ettiklerim_didleri)} takip edilen kullanıcı bulundu.")
    return True

def get_my_followers(): # Fonksiyon adı İngilizce kalabilir
    """Mevcut kullanıcıyı takip eden kişilerin DID'lerini alır."""
    global takipcilerim_didleri
    print("[BİLGİ] Takipçilerin listesi alınıyor...")
    endpoint = f"{BLUESKY_API_BASE}/app.bsky.graph.getFollowers"
    params = {'actor': kendi_handle}
    takipciler = get_paginated_results(endpoint, params, 'followers')

    if takipciler is None: # Sayfalama sırasında hata oluştu
        return False

    takipcilerim_didleri = {takipci['did'] for takipci in takipciler}
    print(f"[BİLGİ] {len(takipcilerim_didleri)} takipçi bulundu.")
    return True

def search_posts_by_hashtag(hashtag): # Fonksiyon adı İngilizce kalabilir
    """Belirli bir hashtag içeren gönderileri arar ve yazarların DID'lerini döndürür."""
    print(f"[BİLGİ] Hashtag içeren gönderiler aranıyor: #{hashtag} (Yazar Limiti: {HASHTAG_BASINA_ARAMA_LIMITI})")
    endpoint = f"{BLUESKY_API_BASE}/app.bsky.feed.searchPosts"
    # Not: Bluesky API'si doğrudan `#etiket` formatında aramayı desteklemiyor olabilir.
    # Metin içinde etiketi arıyoruz, bu daha az kesin sonuç verebilir.
    params = {'q': hashtag} # hashtag terimini ara
    # Limitten fazla gönderi alıp sonra yazarları filtrelemek daha garanti olabilir
    gonderiler = get_paginated_results(endpoint, params, 'posts', limit=200)

    if gonderiler is None:
        return set() # Hata durumunda boş küme döndür

    yazar_didleri = set()
    for gonderi in gonderiler:
        yazar_did = gonderi.get('author', {}).get('did')
        # Kendimizi ve zaten eklenenleri tekrar eklemeyelim
        if yazar_did and yazar_did != kendi_didim:
            yazar_didleri.add(yazar_did)
            # Belirlenen yazar limitine ulaşıldıysa döngüden çık
            if len(yazar_didleri) >= HASHTAG_BASINA_ARAMA_LIMITI:
                break

    print(f"[BİLGİ] #{hashtag} araması sonucu {len(yazar_didleri)} potansiyel yazar bulundu.")
    return yazar_didleri

def get_profile(actor_did): # Fonksiyon adı İngilizce kalabilir
    """Bir kullanıcının profil bilgilerini alır."""
    endpoint = f"{BLUESKY_API_BASE}/app.bsky.actor.getProfile"
    params = {'actor': actor_did}
    try:
        time.sleep(API_BEKLEME_SURESI)
        response = session.get(endpoint, params=params, timeout=ISTEK_ZAMAN_ASIMI)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[HATA] {actor_did} için profil alınırken hata: {e}")
        return None
    except json.JSONDecodeError:
        print(f"[HATA] {actor_did} için profil alınırken geçersiz JSON yanıtı.")
        return None

def get_author_feed(actor_did): # Fonksiyon adı İngilizce kalabilir
    """Bir kullanıcının son gönderilerini alır."""
    endpoint = f"{BLUESKY_API_BASE}/app.bsky.feed.getAuthorFeed"
    params = {'actor': actor_did, 'limit': POST_GETIRME_LIMITI}
    try:
        time.sleep(API_BEKLEME_SURESI)
        response = session.get(endpoint, params=params, timeout=ISTEK_ZAMAN_ASIMI)
        response.raise_for_status()
        veri = response.json()
        return veri.get('feed', []) # feed listesini döndür
    except requests.exceptions.RequestException as e:
        print(f"[HATA] {actor_did} için gönderi akışı alınırken hata: {e}")
        return [] # Hata durumunda boş liste döndür
    except json.JSONDecodeError:
        print(f"[HATA] {actor_did} için gönderi akışı alınırken geçersiz JSON yanıtı.")
        return []

def kullanici_uygunlugunu_analiz_et(handle, profil_verisi, akis_verisi):
    """
    Kullanıcı verilerini Ollama ile analiz ederek dil ve takip uygunluğunu belirler.

    Döndürdüğü değerler:
        'TAKIP_ET': Kriterler karşılanıyorsa.
        'TAKIP_ETME': Kriterler karşılanmıyorsa.
        'HATA': Analiz sırasında bir hata oluşursa.
    """
    if not OLLAMA_MODEL or not OLLAMA_API_BASE:
        print("[HATA] Ollama yapılandırması eksik.")
        return 'HATA'

    # Profil bilgilerini çıkar, yoksa boş string kullan
    profil_aciklamasi = profil_verisi.get('description', '') if profil_verisi else ''
    gorunen_ad = profil_verisi.get('displayName', '') if profil_verisi else ''

    # Gönderi metinlerini birleştir
    gonderi_metinleri = ""
    for oge in akis_verisi:
        gonderi_kaydi = oge.get('post', {}).get('record', {})
        # Sadece orijinal gönderileri dikkate al (basitlik için repost/yanıtları hariç tut)
        if gonderi_kaydi.get('@type') == 'app.bsky.feed.post' and not gonderi_kaydi.get('reply'):
             gonderi_metni = gonderi_kaydi.get('text', '')
             # Metinleri çift satır arasıyla ayır
             gonderi_metinleri += gonderi_metni + "\n\n"

    # --- YENİ, BASİTLEŞTİRİLMİŞ TÜRKÇE PROMPT ---
    prompt = f"""
    Bluesky kullanıcısı '{handle}' için kullanıcı analizi:

    Profil Bilgileri:
    - Görünen Ad: {gorunen_ad}
    - Açıklama: {profil_aciklamasi}

    Son {POST_GETIRME_LIMITI} Gönderi (sadece orijinal gönderiler):
    {gonderi_metinleri}

    Görevler:
    1.  Dil: Bu kullanıcı ağırlıklı olarak Türkçe mi konuşuyor? (EVET/HAYIR)
    2.  Pozitif İşaretler: Atatürk sevgisi veya laik/seküler bir duruşa dair net işaretler var mı? (EVET/HAYIR/BELİRSİZ)
    3.  Kesin Negatif İşaretler (Şeriat): Şeriat istediğine veya aşırı köktenci bir yaklaşıma dair net işaretler var mı? (EVET/HAYIR/BELİRSİZ)
    4.  Kesin Negatif İşaretler (AKP/Erdoğan): Erdoğan veya AKP'yi desteklediğine dair net işaretler var mı? (EVET/HAYIR/BELİRSİZ)

    Nihai Karar: Bu kullanıcı takip edilmeli mi?
    Analizine dayanarak SADECE aşağıdaki kelimelerden BİRİ ile yanıt ver:
    - 'TAKIP_ET': Eğer Dil = EVET VE Pozitif İşaretler = EVET VE Kesin Negatif İşaretler (Şeriat) = HAYIR VE Kesin Negatif İşaretler (AKP/Erdoğan) = HAYIR ise.
    - 'TAKIP_ETME': Diğer tüm durumlarda.

    Yanıt (sadece TEK kelime: TAKIP_ET veya TAKIP_ETME):"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False, # Akış olmayan yanıt bekleniyor
         "options": { # Modelin yanıtını ayarlamak için seçenekler
             "temperature": 0.2 # Daha kesin, daha az yaratıcı yanıtlar için düşük sıcaklık
         }
    }
    api_url = f"{OLLAMA_API_BASE}/api/generate"

    try:
        time.sleep(OLLAMA_BEKLEME_SURESI)
        response = session.post(api_url, json=payload, timeout=60) # LLM için daha uzun zaman aşımı
        response.raise_for_status()
        sonuc = response.json()
        # Yanıtı al, boşlukları temizle ve büyük harfe çevir
        yanit_metni = sonuc.get('response', '').strip().upper()

        if yanit_metni == 'TAKIP_ET':
            print(f"[OLLAMA] Karar ({handle} için): TAKIP_ET")
            return 'TAKIP_ET'
        elif yanit_metni == 'TAKIP_ETME':
            print(f"[OLLAMA] Karar ({handle} için): TAKIP_ETME")
            return 'TAKIP_ETME'
        else:
            # Beklenmeyen bir yanıt gelirse
            print(f"[UYARI] Ollama'dan {handle} için beklenmeyen yanıt: {yanit_metni}")
            return 'TAKIP_ETME' # Şüphe durumunda takip etme

    except requests.exceptions.RequestException as e:
        print(f"[HATA] Ollama ile iletişimde hata: {e}")
        return 'HATA'
    except json.JSONDecodeError:
        print("[HATA] Ollama'dan geçersiz JSON yanıtı.")
        return 'HATA'

def follow_user(actor_did): # Fonksiyon adı İngilizce kalabilir
    """Bluesky API üzerinden bir kullanıcıyı takip eder."""
    print(f"[EYLEM] Kullanıcı {actor_did} takip edilmeye çalışılıyor...")
    endpoint = f"{BLUESKY_API_BASE}/com.atproto.repo.createRecord"
    payload = {
        "repo": kendi_didim, # Takip eden kişinin (benim) DID'i
        "collection": "app.bsky.graph.follow", # Koleksiyon tipi
        "record": {
            "$type": "app.bsky.graph.follow", # Kayıt tipi
            "subject": actor_did, # Takip edilecek kişinin DID'i
            "createdAt": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z') # Zaman damgası (UTC)
        }
    }

    try:
        time.sleep(TAKIP_BEKLEME_SURESI)
        response = session.post(endpoint, json=payload, timeout=ISTEK_ZAMAN_ASIMI)
        response.raise_for_status()
        print(f"[BİLGİ] Kullanıcı {actor_did} başarıyla takip edildi.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[HATA] Kullanıcı {actor_did} takip edilirken hata: {e}")
        if e.response is not None:
            print(f"[HATA] Sunucu yanıtı: {e.response.text}")
            # Eğer zaten takip ediliyorsa (race condition veya önceki hata), bunu başarı say
            if "subject already follows target" in e.response.text.lower() or e.response.status_code == 409:
                 print(f"[BİLGİ] Kullanıcı {actor_did} zaten takip ediliyormuş (veya race condition).")
                 return True # Başarı olarak kabul et
        return False
    except json.JSONDecodeError:
        print(f"[HATA] {actor_did} takip edilirken geçersiz JSON yanıtı.")
        return False


# --- Ana Çalışma Mantığı ---
if __name__ == "__main__":
    baslama_zamani = time.time()
    print("--- Bluesky Otomatik Takip Betiği (Hashtag & Ollama Analizi Tabanlı) ---")
    print("!!! DİKKAT: Bu betik, kullanıcıları otomatik olarak ONAYSIZ takip eder! Kullanım riski size aittir! !!!")

    # Ortam değişkenlerini yükle ve doğrula
    kullanici_adi, sifre = lade_umgebungsvariablen()

    # Ollama API erişimini kontrol et
    if not check_ollama_api():
        print("[HATA] Ollama API'sine erişilemiyor. Betik durduruluyor.")
        exit(1)

    # Bluesky'ye giriş yap
    if not giris_yap(kullanici_adi, sifre):
        print("[HATA] Bluesky girişi başarısız. Betik durduruluyor.")
        exit(1)

    # Kendi takip ettiklerimi ve takipçilerimi al
    if not get_my_followings():
         print("[HATA] Takip edilenler listesi alınamadı. Betik durduruluyor.")
         exit(1)
    if not get_my_followers():
         print("[HATA] Takipçi listesi alınamadı. Betik durduruluyor.")
         exit(1)

    print("-" * 30)
    print(f"Aranacak Hashtagler: {', '.join(ARANACAK_HASHTAGLER)}")
    print("-" * 30)

    # Hashtag araması yaparak adayları bul
    aday_didler = set()
    for hashtag in ARANACAK_HASHTAGLER:
        bulunan_didler = search_posts_by_hashtag(hashtag)
        aday_didler.update(bulunan_didler)
        print(f"[BİLGİ] Şu ana kadar {len(aday_didler)} benzersiz aday bulundu.")
        time.sleep(API_BEKLEME_SURESI) # Hashtag aramaları arasında kısa bekleme

    print("-" * 30)
    print(f"Toplam {len(aday_didler)} aday analiz edilecek...")
    print("-" * 30)

    # Adayları analiz et ve uygunsa takip et
    for i, did in enumerate(aday_didler):
        # Kendimi veya bu çalıştırmada zaten işlenmiş birini atla
        if did == kendi_didim or did in islenen_didler:
            continue

        print(f"\n--- Aday {i+1}/{len(aday_didler)} işleniyor: {did} ---")
        islenen_didler.add(did) # Bu DID'i işlendi olarak işaretle

        # Zaten takip ediyor muyum?
        if did in takip_ettiklerim_didleri:
            print(f"[BİLGİ] Kullanıcı {did} zaten takip ediliyor.")
            zaten_takip_edilen_sayisi += 1
            # Eğer zaten takip edilen kişi beni de takip ediyorsa sayacı artır
            if did in takipcilerim_didleri:
                 geri_takip_eden_aday_sayisi +=1
            continue # Sonraki adaya geç

        # Profil ve gönderi akışını al
        profil = get_profile(did)
        if not profil:
            print(f"[UYARI] {did} için profil alınamadı. Atlanıyor.")
            continue

        # Handle'ı al (varsa), yoksa DID'i kullan
        handle = profil.get('handle', did)

        akis = get_author_feed(did)
        # Akış boş olabilir, analiz fonksiyonu bununla başa çıkabilmeli

        # Ollama ile analiz et
        analiz_sonucu = kullanici_uygunlugunu_analiz_et(handle, profil, akis)

        # Analiz sonucuna göre takip et
        if analiz_sonucu == 'TAKIP_ET':
            print(f"[KARAR] Kullanıcı {handle} ({did}) analiz sonucuna göre takip edilecek.")
            if follow_user(did):
                yeni_takip_edilen_sayisi += 1
                takip_ettiklerim_didleri.add(did) # Yerel listeyi güncelle
                # Yeni takip edilen kullanıcı beni takip ediyor mu?
                if did in takipcilerim_didleri:
                     geri_takip_eden_aday_sayisi += 1
            else:
                print(f"[HATA] {handle} ({did}) takip edilemedi.")
        elif analiz_sonucu == 'TAKIP_ETME':
            print(f"[KARAR] Kullanıcı {handle} ({did}) analiz sonucuna göre takip EDİLMEYECEK.")
        else: # HATA durumu
            print(f"[UYARI] {handle} ({did}) için analiz başarısız veya belirsiz. Atlanıyor.")

        print("-" * 20) # Adaylar arası ayırıcı


    # --- Betik Sonu Özeti ---
    bitis_zamani = time.time()
    toplam_sure = bitis_zamani - baslama_zamani
    print("\n" + "=" * 40)
    print("--- Betik Çalışması Tamamlandı ---")
    print(f"Toplam Süre: {toplam_sure:.2f} saniye")
    print("-" * 40)
    print(f"Aranan Hashtagler: {', '.join(ARANACAK_HASHTAGLER)}")
    print(f"Bulunan Toplam Potansiyel Aday (Benzersiz): {len(aday_didler)}")
    print(f"Analiz Edilen Aday Sayısı (Bu Çalıştırmada Yeni): {len(islenen_didler)}")
    print("-" * 40)
    print(f"Başarıyla YENİ Takip Edilen Kullanıcı Sayısı: {yeni_takip_edilen_sayisi}")
    print(f"Tespit Edilen ve Zaten Takip Edilen Aday Sayısı: {zaten_takip_edilen_sayisi}")
    print(f"Geri Takip Eden Aday Sayısı (Tüm Analiz Edilenlerden, Eski+Yeni): {geri_takip_eden_aday_sayisi}")
    print("=" * 40) 