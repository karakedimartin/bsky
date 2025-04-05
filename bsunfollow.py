import requests
import time
import re # URI'den rkey çıkarmak için gerekli
import os
# import json # Ollama için gerekli değil
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Ortam değişkenlerinden kimlik bilgilerini al
BSKY_KULLANICI_ADI = os.getenv("BLUESKY_USERNAME")
BSKY_SIFRE = os.getenv("BLUESKY_PASSWORD")

# Ollama ayarları kaldırıldı
# OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") 
# OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

# --- Ollama ile ilgili yardımcı fonksiyonlar kaldırıldı ---
# get_profile, get_author_feed, analyze_user_with_ollama


# --- bs.py'den yeniden kullanılan ve uyarlanan fonksiyonlar ---

# 1. Giriş (artık parametresiz)
def giris_yap():
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

# 2. Takipçileri al (kullanıcı adı parametresi kaldı)
def benim_takipcilerimi_al(kullanici_adim, jwt):
    print(f"[*] Takipçilerin ({kullanici_adim}) alınıyor...")
    url = f"https://bsky.social/xrpc/app.bsky.graph.getFollowers?actor={kullanici_adim}"
    takipciler = []
    imlec = None
    basliklar = {"Authorization": f"Bearer {jwt}"}
    while True:
        tam_url = url + (f"&cursor={imlec}" if imlec else "")
        try:
            yanit = requests.get(tam_url, headers=basliklar, timeout=30)
            if yanit.status_code == 401:
                print("[!] Takipçilerin alınırken token süresi doldu.")
                return None # Yeniden giriş gerekli
            yanit.raise_for_status()
            veri = yanit.json()
            takipci_grubu = veri.get('followers', [])
            if not takipci_grubu and imlec is None and not takipciler:
                print(f"[i] Görünüşe göre ({kullanici_adim}) hiç takipçin yok.")
                break
            if not takipci_grubu and imlec: break
            takipciler += [f['did'] for f in takipci_grubu]
            imlec = veri.get('cursor')
            if not imlec: break
            print(f"[*] Şimdiye kadar {len(takipciler)} takipçi bulundu...")
            time.sleep(0.2)
        except requests.exceptions.RequestException as e:
            durum_kodu = e.response.status_code if e.response is not None else "N/A"
            print(f"[X] Takipçilerin alınırken HATA! Durum: {durum_kodu} | URL: {tam_url} | Hata: {e}")
            return None # Hata bildir, muhtemelen yeniden giriş gerekli
    print(f"[✓] {len(takipciler)} takipçi bulundu.")
    return takipciler

# 3. "Takip Edilenler" listesini al (kullanıcı adı parametresi kaldı)
def benim_takip_ettiklerimi_uri_ile_al(kullanici_adim, jwt):
    print(f"[*] 'Takip Edilenler' listen ({kullanici_adim}) alınıyor...")
    url = f"https://bsky.social/xrpc/app.bsky.graph.getFollows?actor={kullanici_adim}"
    takip_verileri = [] # Sözlük listesi
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
            
            # Korrigierte Logik: DID und Follow-Record-URI extrahieren
            for takip_kaydi in takip_edilenler_grubu:
                user_did = takip_kaydi.get('did')
                # Die benötigte URI zum Entfolgen ist im 'following'-Feld des Viewers
                follow_uri = takip_kaydi.get('viewer', {}).get('following') 
                user_handle = takip_kaydi.get('handle', 'bilinmiyor')

                if user_did and follow_uri:
                    # Stelle sicher, dass die URI ein gültiger AT URI ist (string, startet mit at://)
                    if isinstance(follow_uri, str) and follow_uri.startswith('at://'):
                        takip_verileri.append({'did': user_did, 'uri': follow_uri, 'handle': user_handle})
                    else:
                         print(f"[?] Warnung: Ungültige oder fehlende Follow-URI für DID {user_did} gefunden: {follow_uri}")
                else:
                    # Dieser Fall sollte selten sein, aber loggen wir ihn
                    print(f"[?] Warnung: Konnte DID ({user_did}) oder Follow-URI ({follow_uri}) für einen Follow-Eintrag nicht extrahieren: {takip_kaydi}")

            imlec = veri.get('cursor')
            if not imlec: break
            print(f"[*] Şimdiye kadar {len(takip_verileri)} gültige 'Takip Edilen' Datensätze gefunden...") # Angepasste Meldung
            time.sleep(0.2)
        except requests.exceptions.RequestException as e:
            durum_kodu = e.response.status_code if e.response is not None else "N/A"
            print(f"[X] Takip edilenler alınırken HATA! Durum: {durum_kodu} | URL: {tam_url} | Hata: {e}")
            return None # Hata bildir, muhtemelen yeniden giriş gerekli
    print(f"[✓] {len(takip_verileri)} 'Takip Edilen' kaydı (URI und Handle ile) erfolgreich extrahiert.") # Angepasste Meldung
    return takip_verileri

# 4. Bir kullanıcıyı takibi bırak (jwt, my_did parametreleri kaldı)
def takibi_birak(jwt, benim_did, takip_uri):
    # URI'den rkey'i çıkar
    eslesme = re.match(r"at://([^/]+)/([^/]+)/([^/]+)", takip_uri)
    if not eslesme:
        print(f"[X] Takibi bırakmak için geçersiz URI formatı: {takip_uri}")
        return False
    
    repo_did = eslesme.group(1)
    koleksiyon = eslesme.group(2)
    rkey = eslesme.group(3)

    if repo_did != benim_did: print(f"[X] URI {takip_uri} kendi deponuza ({benim_did}) ait değil."); return False
    if koleksiyon != "app.bsky.graph.follow": print(f"[X] URI {takip_uri} bir takip kaydı değil."); return False

    url = "https://bsky.social/xrpc/com.atproto.repo.deleteRecord"
    basliklar = {"Authorization": f"Bearer {jwt}"}
    payload = {"repo": benim_did, "collection": koleksiyon, "rkey": rkey}
    hedef_did_log = f"Kayıt {rkey}"

    try:
        # Wartezeit vor jeder Anfrage
        time.sleep(1) # 1 Sekunde Pause um API Limits zu vermeiden
        r = requests.post(url, headers=basliklar, json=payload, timeout=10)
        if r.status_code == 401:
            print(f"[!] {hedef_did_log} takibi bırakılırken token süresi doldu.")
            return "TOKEN_SURESI_DOLDU"
        r.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        hata_mesaji = f"[!] Takibi bırakma başarısız: {hedef_did_log} (URI: {takip_uri})"
        if e.response is not None:
            try: 
                hata_verisi = e.response.json()
                hata_tipi = hata_verisi.get('error')
                hata_detayi = hata_verisi.get('message')
            except ValueError: 
                hata_mesaji += f" - Status: {e.response.status_code} | Response: {e.response.text}"
            else: 
                hata_mesaji += f" - Status: {e.response.status_code} | Type: {hata_tipi} | Message: {hata_detayi}"
                # Spezifische Fehlerbehandlung für "Record not found" (falls User schon entfolgt wurde)
                if e.response.status_code == 400 and hata_tipi == 'InvalidRequest' and 'could not find record' in hata_detayi:
                    print(f" [INFO] {hedef_did_log} bereits nicht mehr vorhanden (evtl. schon entfolgt).")
                    return True # Zählen wir als Erfolg, da Ziel erreicht
        else: 
            hata_mesaji += f" - Error: {e}"
        print(hata_mesaji)
        return False


# --- Ana Mantık --- (Sadece geri takip etmeyenleri direkt bırakır)

def takip_etmeyenleri_birak():
    print("[*] Geri takip etmeyenleri **direkt** takibi bırakma betiği başlatıldı.")
    print("!!! ACHTUNG: KEINE BESTÄTIGUNG! AKTIONEN SIND ENDGÜLTIG! !!!")
    
    # --- Giriş ---
    jwt, benim_did = giris_yap()
    if not jwt or not benim_did: print("[X] Giriş başarısız oldu."); return
    kendi_kullanici_adim = BSKY_KULLANICI_ADI

    # --- Gerekli Verileri Topla ---
    print("\n--- Veri Toplama Aşaması ---")
    takip_ettiklerim_verisi = benim_takip_ettiklerimi_uri_ile_al(kendi_kullanici_adim, jwt)
    if takip_ettiklerim_verisi is None:
        print("[*] Yeniden giriş deneniyor (Takip Edilenler)...")
        jwt, benim_did = giris_yap();
        if not jwt or not benim_did: print("[X] Yeniden giriş başarısız."); return
        takip_ettiklerim_verisi = benim_takip_ettiklerimi_uri_ile_al(kendi_kullanici_adim, jwt)
        if takip_ettiklerim_verisi is None: print("[X] Takip edilenler alınamadı."); return

    takipcilerim_listesi = benim_takipcilerimi_al(kendi_kullanici_adim, jwt)
    if takipcilerim_listesi is None:
        print("[*] Yeniden giriş deneniyor (Takipçiler)...")
        jwt, benim_did = giris_yap();
        if not jwt or not benim_did: print("[X] Yeniden giriş başarısız."); return
        takipcilerim_listesi = benim_takipcilerimi_al(kendi_kullanici_adim, jwt)
        if takipcilerim_listesi is None: print("[X] Takipçiler alınamadı."); return

    takipcilerim_kumesi = set(takipcilerim_listesi)
    print(f"[*] Toplam takip edilen: {len(takip_ettiklerim_verisi)}, Toplam takipçi: {len(takipcilerim_kumesi)}")

    # --- Geri Takip Etmeyenleri Bul --- 
    print("\n--- Geri Takip Etmeyenler Kontrol Ediliyor ---")
    takibi_birakilacak_kullanicilar = [] # {did, uri, handle} sözlük listesi
    for takip_kaydi in takip_ettiklerim_verisi:
        if takip_kaydi['did'] not in takipcilerim_kumesi:
            takibi_birakilacak_kullanicilar.append(takip_kaydi)

    # --- Direkte Takibi Bırakma --- 
    print("\n--- Takibi Bırakma İşlemi Başlatılıyor (DIREKT) ---")
    if not takibi_birakilacak_kullanicilar:
        print("[*] Geri takip etmeyen ve takibi bırakılacak kullanıcı bulunamadı.")
        return

    print(f"[*] {len(takibi_birakilacak_kullanicilar)} kullanıcı wird jetzt entfolgt...")
    takip_birakilan_sayisi = 0
    basarisiz_sayisi = 0
    token_problem_sayisi = 0

    for i, kullanici_bilgisi in enumerate(takibi_birakilacak_kullanicilar):
        if not benim_did: 
            print("[X] Takibi bırakma denemesi öncesi kendi DID'im geçersiz. Breche ab."); 
            basarisiz_sayisi += (len(takibi_birakilacak_kullanicilar) - i)
            break 

        silinecek_takip_uri = kullanici_bilgisi['uri']
        hedef_handle = kullanici_bilgisi.get('handle', 'bilinmiyor')
        hedef_did = kullanici_bilgisi.get('did')

        takibi_birakma_sonucu = takibi_birak(jwt, benim_did, silinecek_takip_uri)

        if takibi_birakma_sonucu == "TOKEN_SURESI_DOLDU":
            token_problem_sayisi += 1
            yeni_jwt, yeni_did = giris_yap()
            if not yeni_jwt or not yeni_did: 
                print("[X] Yeniden giriş başarısız. Restliche Aktionen werden übersprungen.")
                basarisiz_sayisi += (len(takibi_birakilacak_kullanicilar) - i)
                break # Schleife abbrechen
            jwt = yeni_jwt
            benim_did = yeni_did
            
            # Erneuter Versuch für denselben Benutzer
            takibi_birakma_sonucu = takibi_birak(jwt, benim_did, silinecek_takip_uri)
            # Ergebnis des zweiten Versuchs nur noch intern auswerten
            if takibi_birakma_sonucu == True:
                takip_birakilan_sayisi += 1
            elif takibi_birakma_sonucu == "TOKEN_SURESI_DOLDU":
                 basarisiz_sayisi += 1
            else: # False oder anderer Fehler
                 basarisiz_sayisi += 1
        
        elif takibi_birakma_sonucu == True:
            takip_birakilan_sayisi += 1
        else: # False
            basarisiz_sayisi += 1

    # --- Zusammenfassung --- 
    print("\n--- Zusammenfassung der Takibi Bırakma Aktion ---")
    print(f"[*] Erfolgreich entfolgte Benutzer: {takip_birakilan_sayisi}")
    print(f"[*] Fehlgeschlagene Entfolge-Versuche: {basarisiz_sayisi}")
    if token_problem_sayisi > 0:
        print(f"[*] Anzahl der Token-Ablauf-Probleme (mit Re-Login-Versuch): {token_problem_sayisi}")
    print("[*] Direkte Takibi Bırakma abgeschlossen.")


# -----------------------------
# KULLANIM
# -----------------------------
if __name__ == "__main__":
    print("UYARI: Bu betik, sizi geri takip etmeyen kullanıcıları")
    print("       otomatik olarak takibi bırakmaya çalışacaktır!")
    print("       Bu işlemin geri dönüşü yoktur.")
    print("       Sonuçlarını anladığınızdan emin olun.")
    print("       .env dosyasındaki kimlik bilgilerini kontrol edin.")
    print("-" * 30)

    # Başlangıçta ortam değişkenlerini kontrol et
    if not BSKY_KULLANICI_ADI or not BSKY_SIFRE:
        print("[X] Lütfen proje klasöründe bir .env dosyası oluşturun ve içine BLUESKY_USERNAME ve BLUESKY_PASSWORD değişkenlerini ayarlayın.")
    else:
        # Ana fonksiyonu doğrudan çağır
        takip_etmeyenleri_birak()
