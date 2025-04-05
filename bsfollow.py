import requests  # requests kütüphanesini import et
import time      # time modülünü import et
import os        # Ortam değişkenlerini okumak için
from dotenv import load_dotenv # .env dosyasını okumak için

# .env dosyasındaki değişkenleri yükle
load_dotenv()

# Ortam değişkenlerinden kimlik bilgilerini al
BSKY_KULLANICI_ADI = os.getenv("BLUESKY_USERNAME")
BSKY_SIFRE = os.getenv("BLUESKY_PASSWORD")

# Ortam değişkeninden hedef kullanıcı listesini al (virgülle ayrılmış)
TARGET_USERS_STR = os.getenv("TARGET_USERS", "") # Varsayılan olarak boş string

# Hedef kullanıcıları string'den listeye çevir
# Baştaki/sondaki boşlukları temizle ve boş girdileri filtrele
hedef_kullanicilar = [user.strip() for user in TARGET_USERS_STR.split(',') if user.strip()]

# Global değişkenleri kaldırıyoruz, artık doğrudan ortam değişkenlerini veya parametreleri kullanacağız.
# KULLANICI_ADI_GLOBAL = ""
# SIFRE_GLOBAL = ""

# 1. Bluesky'e giriş yap, accessJwt ve DID al
#    Fonksiyon şimdi doğrudan global ortam değişkenlerini kullanacak
def giris_yap():
    kullanici_adi = BSKY_KULLANICI_ADI
    sifre = BSKY_SIFRE
    
    if not kullanici_adi or not sifre:
        print("[X] HATA: BLUESKY_USERNAME ve BLUESKY_PASSWORD ortam değişkenleri .env dosyasında ayarlanmamış!")
        return None, None

    # Global değişkenleri ayarlamaya gerek yok
    # global KULLANICI_ADI_GLOBAL, SIFRE_GLOBAL
    # KULLANICI_ADI_GLOBAL = kullanici_adi
    # SIFRE_GLOBAL = sifre

    url = "https://bsky.social/xrpc/com.atproto.server.createSession"
    print(f"[*] {kullanici_adi} için giriş deneniyor...")
    try:
        yanit = requests.post(url, json={
            "identifier": kullanici_adi,
            "password": sifre
        }, timeout=15)
        yanit.raise_for_status() # 4xx/5xx hataları için istisna oluşturur
        veri = yanit.json()
        print("[✓] Giriş başarılı!")
        # JWT ve DID'yi döndür
        return veri.get("accessJwt"), veri.get("did")
    except requests.exceptions.RequestException as e:
        print(f"[X] GİRİŞ HATASI! URL: {url}")
        hata_mesaji = ""
        if e.response is not None:
            # Şifre hatası olup olmadığını kontrol et (daha iyi hata mesajı için)
            if e.response.status_code == 401:
                 hata_mesaji = "Giriş başarısız. Kullanıcı adı veya şifre yanlış olabilir."
            elif e.response.status_code == 400 and "Invalid identifier or password" in e.response.text:
                 hata_mesaji = "Giriş başarısız. Kullanıcı adı veya şifre yanlış olabilir."
            else:
                 hata_mesaji = f"Durum Kodu: {e.response.status_code} | Yanıt: {e.response.text}"
        else:
            hata_mesaji = f"Hata: {e}"
        print(f"    {hata_mesaji}")
        return None, None # Girişte hata olduğunu belirtir

# 2. Hedef kullanıcının takipçilerini al (Yeniden giriş kontrolü ve düzeltilmiş sayfalama ile)
def takipcileri_al(kullanici_adi, jwt):
    print(f"[*] {kullanici_adi} kullanıcısının takipçileri alınıyor...")
    url = f"https://bsky.social/xrpc/app.bsky.graph.getFollowers?actor={kullanici_adi}"
    takipciler = []
    imlec = None
    basliklar = {"Authorization": f"Bearer {jwt}"}
    sayfa_sayisi = 0

    while True:
        sayfa_sayisi += 1
        tam_url = url + (f"&cursor={imlec}" if imlec else "")
        print(f"[*] Takipçi sayfası {sayfa_sayisi} alınıyor... (URL: ...{tam_url[-30:]})") # URL'nin bir kısmını göster
        try:
            yanit = requests.get(tam_url, headers=basliklar, timeout=45) # Biraz daha uzun zaman aşımı
            if yanit.status_code == 401:
                 print("[!] Takipçiler alınırken token süresi doldu.")
                 return None # Yeniden giriş gerekliliğini belirtir
            yanit.raise_for_status() # Diğer 4xx/5xx hatalarını tetikle
            veri = yanit.json()
            takipci_grubu = veri.get('followers', [])
            
            if not takipci_grubu and imlec is None and not takipciler:
                 print(f"[!] Kullanıcı '{kullanici_adi}' bulunamadı veya hiç takipçisi yok? İlk sayfada boş yanıt alındı.")
                 break # Takipçi yok veya kullanıcı adı geçersiz
            
            if takipci_grubu:
                takipciler.extend([f['did'] for f in takipci_grubu])
                print(f"[*] Şimdiye kadar {len(takipciler)} takipçi bulundu...")

            imlec = veri.get('cursor')
            
            # Doğru durdurma koşulu: İmleç kalmadı.
            if not imlec:
                print("[*] API'den başka imleç gelmedi, sayfalama tamamlandı.")
                break 
            
            # Rate Limiting'i önlemek için kısa bir duraklama
            time.sleep(0.25) 

        except requests.exceptions.RequestException as e:
            durum_kodu = e.response.status_code if e.response is not None else "N/A"
            print(f"[X] Sayfa {sayfa_sayisi} alınırken HATA! Durum: {durum_kodu} | URL: {tam_url} | Hata: {e}")
            print(f"[*] Alma işlemi iptal ediliyor. Şimdiye kadar {len(takipciler)} takipçi toplandı.")
            # Burada None veya kısmi listeyi döndürebiliriz. Kısmi listeyi döndürüyoruz.
            break
    print(f"[✓] {kullanici_adi} için toplam {len(takipciler)} takipçi bulundu.")
    return takipciler

# 3. Kendi "Takip Edilenler" listesini al (Yeniden giriş kontrolü ve düzeltilmiş sayfalama ile)
def takip_edilenleri_al(kullanici_adi, jwt):
    print(f"[*] {kullanici_adi} kullanıcısının 'Takip Edilenler' listesi alınıyor...")
    url = f"https://bsky.social/xrpc/app.bsky.graph.getFollows?actor={kullanici_adi}"
    takip_edilenler = []
    imlec = None
    basliklar = {"Authorization": f"Bearer {jwt}"}
    sayfa_sayisi = 0

    while True:
        sayfa_sayisi += 1
        tam_url = url + (f"&cursor={imlec}" if imlec else "")
        print(f"[*] Takip edilenler sayfası {sayfa_sayisi} alınıyor... (URL: ...{tam_url[-30:]})")
        try:
            yanit = requests.get(tam_url, headers=basliklar, timeout=45)
            if yanit.status_code == 401:
                print("[!] Takip edilenler alınırken token süresi doldu.")
                return None # Yeniden giriş gerekliliğini belirtir
            yanit.raise_for_status() # Diğer 4xx/5xx hatalarını tetikle
            veri = yanit.json()
            takip_edilenler_grubu = veri.get('follows', [])
            
            if not takip_edilenler_grubu and imlec is None and not takip_edilenler:
                 print(f"[!] Kullanıcı '{kullanici_adi}' bulunamadı veya kimseyi takip etmiyor? İlk sayfada boş yanıt alındı.")
                 break
                 
            if takip_edilenler_grubu:
                takip_edilenler.extend([f['did'] for f in takip_edilenler_grubu])
                print(f"[*] Şimdiye kadar {len(takip_edilenler)} takip edilen bulundu...")

            imlec = veri.get('cursor')
            
            # Doğru durdurma koşulu
            if not imlec:
                print("[*] API'den başka imleç gelmedi, sayfalama tamamlandı.")
                break 
            
            time.sleep(0.25)

        except requests.exceptions.RequestException as e:
            durum_kodu = e.response.status_code if e.response is not None else "N/A"
            print(f"[X] Sayfa {sayfa_sayisi} alınırken HATA! Durum: {durum_kodu} | URL: {tam_url} | Hata: {e}")
            print(f"[*] Alma işlemi iptal ediliyor. Şimdiye kadar {len(takip_edilenler)} takip edilen toplandı.")
            break
    print(f"[✓] {kullanici_adi} için toplam {len(takip_edilenler)} 'Takip Edilen' kaydı bulundu.")
    return takip_edilenler


# 4. Belirtilen DID'leri takip et (Yeniden giriş kontrolü ve Payload düzeltmesi ile)
def takip_et(jwt, benim_did, hedef_did):
    # Kayıt oluşturmak için doğru uç nokta
    url = "https://bsky.social/xrpc/com.atproto.repo.createRecord"
    basliklar = {"Authorization": f"Bearer {jwt}"}
    # Düzeltilmiş Payload yapısı
    payload = {
        "repo": benim_did,
        "collection": "app.bsky.graph.follow",
        "record": {
            "$type": "app.bsky.graph.follow",
            "subject": hedef_did,
            "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    }

    try:
        r = requests.post(url, headers=basliklar, json=payload, timeout=10)
        if r.status_code == 401:
            print(f"[!] {hedef_did} takip edilirken token süresi doldu.")
            return "TOKEN_SURESI_DOLDU" # Özel dönüş değeri
        r.raise_for_status() # Diğer hatalar
        print(f"[+] Takip edildi: {hedef_did}")
        return True # Başarı
    except requests.exceptions.RequestException as e:
        hata_mesaji = f"[!] Takip edilemedi: {hedef_did}"
        if e.response is not None:
            try:
                hata_verisi = e.response.json()
                hata_tipi = hata_verisi.get('error', 'BilinmeyenHata')
                hata_detayi = hata_verisi.get('message', e.response.text)
                if e.response.status_code == 409 or "subject is already followed" in hata_detayi:
                     print(f"[i] Zaten takip ediliyor (veya Hata 409): {hedef_did}")
                else:
                     hata_mesaji += f" - Durum: {e.response.status_code} | Tip: {hata_tipi} | Mesaj: {hata_detayi}"
                     print(hata_mesaji)
            except ValueError:
                hata_mesaji += f" - Durum: {e.response.status_code} | Yanıt: {e.response.text}"
                print(hata_mesaji)
        else:
            hata_mesaji += f" - Hata: {e}"
            print(hata_mesaji)
        return False # Genel hata

# 5. Ana fonksiyon - Birden fazla hedef kullanıcı listesini işler
#    Artık başlangıç kullanıcı adı/şifre parametrelerine ihtiyaç duymaz
def coklu_hedefleri_isle(hedef_kullanici_listesi):
    print("[*] Birden fazla hedefin takipçilerini takip etme betiği başlatıldı.")
    # Doğrudan login fonksiyonunu çağır (artık parametresiz)
    jwt, benim_did = giris_yap()
    if not jwt:
        # Hata mesajı zaten giris_yap içinde yazdırıldı.
        print("[X] Betik sonlandırılıyor.")
        return

    # Kendi kullanıcı adımızı global değişkenden alalım (loglama için)
    kendi_kullanici_adim = BSKY_KULLANICI_ADI

    islenen_hedefler = 0
    toplam_yeni_takip = 0
    toplam_basarisiz_veya_atlanmis = 0

    # Hedef kullanıcı listesi üzerinde döngü
    for hedef_kullanici in hedef_kullanici_listesi:
        islenen_hedefler += 1
        print(f"\n{'='*40}")
        print(f"[*] Hedef {islenen_hedefler}/{len(hedef_kullanici_listesi)} işleniyor: {hedef_kullanici}")
        print(f"{'='*40}")

        # --- Kendi Takip Edilenlerimi Al (Her hedeften önce yeniden, çünkü değişiyor!) ---
        takip_ettiklerim_listesi = takip_edilenleri_al(kendi_kullanici_adim, jwt)
        if takip_ettiklerim_listesi is None: # Token süresi doldu
            print(f"[*] {hedef_kullanici} işlenmeden önce yeniden giriş deneniyor (Takip Edilenler)..." )
            # Parametresiz login çağrısı
            jwt, benim_did = giris_yap()
            if not jwt: print("[X] Yeniden giriş başarısız oldu. Betik sonlandırılıyor."); return
            # DID kontrolü
            if not benim_did: print("[X] Yeniden giriş sonrası DID alınamadı."); return
            takip_ettiklerim_listesi = takip_edilenleri_al(kendi_kullanici_adim, jwt)
            if takip_ettiklerim_listesi is None: print(f"[X] {hedef_kullanici} için takip edilenler yeniden giriş sonrası alınamadı. Hedef atlanıyor."); continue # Sonraki hedef

        takip_ettiklerim_kumesi = set(takip_ettiklerim_listesi)
        print(f"[*] Sen ({kendi_kullanici_adim}) şu anda {len(takip_ettiklerim_kumesi)} kullanıcıyı takip ediyorsun (bu hedeften önce).")

        # --- Hedef Takipçilerini Al (Yeniden giriş denemesi ile) ---
        hedef_takipciler = takipcileri_al(hedef_kullanici, jwt)
        if hedef_takipciler is None: # Token süresi doldu
            print(f"[*] {hedef_kullanici} işlenmeden önce yeniden giriş deneniyor (Takipçiler)..." )
            jwt, benim_did = giris_yap()
            if not jwt: print("[X] Yeniden giriş başarısız oldu. Betik sonlandırılıyor."); return
            if not benim_did: print("[X] Yeniden giriş sonrası DID alınamadı."); return
            hedef_takipciler = takipcileri_al(hedef_kullanici, jwt)
            if hedef_takipciler is None: print(f"[X] {hedef_kullanici} takipçileri yeniden giriş sonrası alınamadı. Hedef atlanıyor."); continue # Sonraki hedef

        if not hedef_takipciler:
            print(f"[*] '{hedef_kullanici}' hedefinde hiç takipçi bulunamadı. Hedef atlanıyor.")
            continue # Sonraki hedef

        # --- Filtreleme ---
        takip_edilecek_takipciler = []
        zaten_takip_edilen_sayisi = 0
        for did in hedef_takipciler:
            if did == benim_did: # Kendini takip etme
                continue
            if did not in takip_ettiklerim_kumesi:
                takip_edilecek_takipciler.append(did)
            else:
                zaten_takip_edilen_sayisi += 1

        print(f"[*] Hedef '{hedef_kullanici}' {len(hedef_takipciler)} takipçiye sahip.")
        print(f"[*] Bunlardan {zaten_takip_edilen_sayisi} tanesini zaten takip ediyorsun.")
        print(f"[*] '{hedef_kullanici}' kullanıcısının {len(takip_edilecek_takipciler)} yeni takipçisi takip edilmeye çalışılacak.")

        if not takip_edilecek_takipciler:
            print(f"[*] '{hedef_kullanici}' hedefi için takip edilecek yeni kullanıcı bulunamadı.")
            continue # Sonraki hedef

        print(f"[*] '{hedef_kullanici}' için örnek DID'ler (en fazla 10): {takip_edilecek_takipciler[:10]}")

        # --- Takip Döngüsü (Yeniden giriş mantığı ile) ---
        mevcut_hedef_takip_sayisi = 0
        mevcut_hedef_basarisiz_sayisi = 0
        mevcut_indeks = 0
        while mevcut_indeks < len(takip_edilecek_takipciler):
            if not benim_did: print("[X] Takip denemesi öncesi kendi DID'im geçersiz. İptal ediliyor."); break
            takip_edilecek_did = takip_edilecek_takipciler[mevcut_indeks]
            print(f"[*] Hedef '{hedef_kullanici}' | Deneme {mevcut_indeks + 1}/{len(takip_edilecek_takipciler)}: Takip et {takip_edilecek_did}")

            takip_sonucu = takip_et(jwt, benim_did, takip_edilecek_did)

            if takip_sonucu == "TOKEN_SURESI_DOLDU":
                print("[*] Token süresi dolduktan sonra yeniden giriş deneniyor (Takip)..." )
                # Parametresiz login çağrısı
                yeni_jwt, yeni_did = giris_yap()
                if not yeni_jwt: print("[X] Yeniden giriş başarısız oldu. Hedef işleme iptal ediliyor."); break
                jwt = yeni_jwt
                benim_did = yeni_did
                print("[✓] Yeniden giriş başarılı. Takip denemesi tekrarlanıyor...")
                continue
            elif takip_sonucu:
                mevcut_hedef_takip_sayisi += 1
                time.sleep(0.6)
            else:
                mevcut_hedef_basarisiz_sayisi += 1
                time.sleep(0.3)

            mevcut_indeks += 1

        print(f"\n[*] Hedef '{hedef_kullanici}' için ara özet:")
        print(f"[*] Başarıyla takip edilen yeni kullanıcı sayısı: {mevcut_hedef_takip_sayisi}")
        print(f"[*] Başarısız/Zaten takip edilen: {mevcut_hedef_basarisiz_sayisi}")
        toplam_yeni_takip += mevcut_hedef_takip_sayisi
        toplam_basarisiz_veya_atlanmis += mevcut_hedef_basarisiz_sayisi

    # --- Tüm hedefler için döngü sonu ---
    print(f"\n{'='*40}")
    print("[*] Tüm hedef kullanıcılar işlendi.")
    print(f"[*] Toplam başarıyla takip edilen yeni kullanıcı sayısı: {toplam_yeni_takip}")
    print(f"[*] Toplam başarısız/zaten takip edilen/atlanan: {toplam_basarisiz_veya_atlanmis}")
    print(f"{'='*40}")


# -----------------------------
# KULLANIM: ARTIK .env DOSYASINDA!
# -----------------------------
# --- ÖNEMLİ GÜVENLİK UYARISI ---
# Kimlik bilgilerini (kullanıcı adı/şifre) doğrudan koda yazmak güvenli değildir!
# BU BETİK ŞİMDİ .env DOSYASINI KULLANIR.
# Hedef kullanıcılar da artık .env dosyasından okunur.
# -----------------------------
# --- Kullanım ---
# Kimlik bilgileri ve hedef kullanıcılar artık .env dosyasından okunur.
# hedef_kullanicilar listesi aşağıdan kaldırıldı.

# --- Hedef Kullanıcı LİSTESİ ---
# BU LİSTE ARTIK KULLANILMIYOR. LÜTFEN .env DOSYASINDAKİ 'TARGET_USERS' DEĞİŞKENİNİ AYARLAYIN.
# hedef_kullanicilar = [
#     "tengrim.bsky.social",
#     "kkucukkarabalikk.bsky.social",
#     "genzowakabayasi.bsky.social",
#     "kaleminjero.bsky.social",
# ]


if not BSKY_KULLANICI_ADI or not BSKY_SIFRE:
     print("[X] Lütfen proje klasöründe bir .env dosyası oluşturun ve içine BLUESKY_USERNAME ve BLUESKY_PASSWORD değişkenlerini ayarlayın.")
elif not hedef_kullanicilar: # Artık ayrıştırılmış listeyi kontrol et
    print("[X] 'TARGET_USERS' ortam değişkeni .env dosyasında bulunamadı veya boş. Lütfen hedef kullanıcıları virgülle ayırarak ekleyin.")
else:
    # Fonksiyon hedef_kullanicilar listesini (env'den gelen) kullanır
    coklu_hedefleri_isle(hedef_kullanicilar)





