# Bluesky Toplu Takibi Bırakma Betiği (`bsunfollow.py`) - **DIREKT MOD**

Bu betik, sizin takip ettiğiniz ancak sizi **geri takip etmeyen** kullanıcıları **OTOMATİK ve ONAYSIZ** olarak takibi bırakmanızı sağlar.

**Not:** Politik görüş analizi özelliği (`bsanalyze.py`) ayrı bir betiğe taşınmıştır. Bu betik sadece geri takip etmeyenleri kontrol eder.

## !! EXTREM ÖNEMLİ UYARILAR !!

*   **ONAYSIZ VE KALICI İŞLEM:** Bu betik, geri takip etmeyen kullanıcıları **SORMADAN ve KALICI OLARAK** takibi bırakır. Bu işlemin **GERİ DÖNÜŞÜ YOKTUR**. Betiği çalıştırmadan önce ne yaptığınızdan ve sonuçlarından **KESİNLİKLE EMİN OLUN! YANLIŞLIKLA ÖNEMLİ KİŞİLERİ TAKİBİ BIRAKABİLİRSİNİZ!**
*   **GÜVENLİK:** `.env` dosyasını güvende tutun.
*   **API LİMİTLERİ:** Bluesky'nin API kullanım limitleri vardır. Çok sayıda kullanıcıyı hızlıca takibi bırakmak limitleri zorlayabilir ve hesabınızı kısıtlayabilir. Betikte 1 saniyelik bekleme vardır, ancak yine de dikkatli olun.
*   **SORUMLULUK:** Bu betiği kullanmak **TAMAMEN SİZİN SORUMLULUĞUNUZDADIR**. Oluşabilecek herhangi bir hesap problemi, kısıtlama veya yanlışlıkla takipten çıkma durumundan dolayı sorumluluk kabul edilmez.

## Gereksinimler

*   **Python 3:** (bkz. `README_analyze.md`)
*   **Notwendige Python-Bibliotheken:** `requests`, `python-dotenv`.

## Kurulum ve Ayarlama

1.  **Dosyaları İndirme:**
    *   `bsunfollow.py` dosyasını bilgisayarınızda bir klasöre indirin.

2.  **Gerekli Kütüphaneleri Yükleme (`requests` ve `python-dotenv`):**
    ```bash
    pip install requests python-dotenv
    ```
    (Oder `pip3`, `py -m pip` etc., siehe `README_analyze.md`)

3.  **`.env` Dosyası Oluşturma ve Ayarlama:**
    *   `bsunfollow.py` dosyasının bulunduğu klasörde `.env` adında **yeni bir metin dosyası** oluşturun (veya mevcut olanı kullanın).
    *   Bu dosyanın içine **en az** aşağıdaki satırları yazın:
        ```dotenv
        BLUESKY_USERNAME="SENİN_KULLANICI_ADIN_BURAYA"
        BLUESKY_PASSWORD="SENİN_ŞİFREN_BURAYA"
        # Diğer değişkenler (TARGET_USERS, OLLAMA_*, SEARCH_HASHTAGS) bu betik için gerekli değildir.
        ```
    *   `BLUESKY_USERNAME` ve `BLUESKY_PASSWORD` kısımlarını kendi bilgilerinizle değiştirin.
    *   **Dosyayı `.env` olarak kaydedin**.

## Betiği Çalıştırma

1.  **Terminal/Kommandozeile öffnen:** Navigieren Sie mit `cd` in den Ordner, in dem sich `bsunfollow.py` und `.env` befinden.
2.  **Betiği Çalıştırın:**
    ```bash
    python bsunfollow.py
    ```
    (Oder `python3`, `py`)
3.  **Ablauf:**
    *   Betik takip ettiğiniz ve sizi geri takip etmeyen kişileri bulacak.
    *   **Anschließend beginnt es SOFORT damit, diese Benutzer zu entfolgen.** Es wird **KEINE** Liste angezeigt und **KEINE** Bestätigung angefordert.
    *   Der Fortschritt wird im Terminal angezeigt.
    *   Am Ende wird eine Zusammenfassung ausgegeben, wie viele Benutzer entfolgt wurden.

**Nochmal: SEHR VORSICHTIG SEIN! Diese Version fragt nicht nach!**

## Notlar

*   **Token Süresi:** Betik versucht, bei Token-Ablauf automatisch neu einzuloggen und den letzten fehlgeschlagenen Versuch zu wiederholen.
*   **Beklemeler:** Vor jedem Entfolge-Versuch wird 1 Sekunde gewartet.
*   **Hatalar:** Netzwerk- oder API-Fehler können auftreten. 