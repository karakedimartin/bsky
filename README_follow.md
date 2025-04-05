# Bluesky Toplu Takip Betiği (`bs.py`)

Bu betik, Bluesky sosyal ağında belirli kullanıcıların takipçilerini analiz eder ve sizin henüz takip etmediğiniz kişileri otomatik olarak takip etmenizi sağlar.

## !! ÖNEMLİ UYARILAR !!

*   **GÜVENLİK:** Bluesky kullanıcı adınızı ve **özellikle şifrenizi** doğrudan betik dosyalarının içine yazmak **GÜVENLİ DEĞİLDİR**. Bu betik, daha güvenli olan `.env` dosyasını kullanır, ancak bu dosyayı da güvende tutmalısınız.
*   **API LİMİTLERİ:** Bluesky'nin API kullanım limitleri vardır. Betiği çok sık veya çok fazla hedef kullanıcıyla çalıştırmak, hesabınızın geçici olarak kısıtlanmasına neden olabilir. Dikkatli kullanın.
*   **SORUMLULUK:** Bu betiği kullanmak **TAMAMEN SİZİN SORUMLULUĞUNUZDADIR**. Oluşabilecek herhangi bir hesap problemi veya kısıtlamadan dolayı sorumluluk kabul edilmez.

## Gereksinimler

*   **Python 3:** Bilgisayarınızda Python 3'ün yüklü olması gerekir (Genellikle Python 3.7 veya üstü).

    *   **Yüklü olup olmadığını kontrol etme:**
        *   **Windows:** Komut İstemi'ni (CMD) açın ve `python --version` yazıp Enter'a basın. Eğer hata verirse veya Python 2 sürümü görünürse, `py --version` veya `python3 --version` deneyin.
        *   **Linux/macOS:** Terminal'i açın ve `python3 --version` yazıp Enter'a basın. Eğer hata verirse, `python --version` deneyin.
    *   **Python Yükleme (Eğer yoksa):**
        *   **Windows:** [https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/) adresinden en son Python 3 sürümünü indirin. Yükleyiciyi çalıştırırken **"Add Python X.Y to PATH"** seçeneğini **işaretlediğinizden emin olun**.
        *   **Linux:** Genellikle dağıtımınızın paket yöneticisi ile yüklenir. Örnek (Debian/Ubuntu): `sudo apt update && sudo apt install python3 python3-pip`
        *   **macOS:** [https://www.python.org/downloads/macos/](https://www.python.org/downloads/macos/) adresinden indirebilir veya Homebrew kullanıyorsanız: `brew install python`

## Kurulum ve Ayarlama

1.  **Dosyaları İndirme:**
    *   `bs.py` dosyasını bilgisayarınızda bir klasöre indirin (örn. `Masaüstü\bluesky_betikler`).

2.  **Gerekli Kütüphaneleri Yükleme (`requests` ve `python-dotenv`):**
    *   Betiklerin çalışması için `requests` ve `python-dotenv` adlı Python kütüphaneleri gereklidir.
    *   **Windows:** Komut İstemi'ni (CMD) açın ve şu komutu çalıştırın:
        ```bash
        pip install requests python-dotenv
        ```
        Eğer `pip` bulunamadı hatası alırsanız, `pip3 install requests python-dotenv` veya `py -m pip install requests python-dotenv` deneyin.
    *   **Linux/macOS:** Terminal'i açın ve şu komutu çalıştırın:
        ```bash
        pip3 install requests python-dotenv
        ```
        Eğer `pip3` bulunamadı hatası alırsanız, `pip install requests python-dotenv` deneyin.

3.  **`.env` Dosyası Oluşturma ve Ayarlama:**
    *   `bs.py` dosyasının bulunduğu klasörde `.env` adında **yeni bir metin dosyası** oluşturun.
    *   Bu dosyanın içine **tam olarak** aşağıdaki gibi satırları yazın:
        ```dotenv
        BLUESKY_USERNAME="SENİN_KULLANICI_ADIN_BURAYA"
        BLUESKY_PASSWORD="SENİN_ŞİFREN_BURAYA"
        TARGET_USERS="hedef1.bsky.social,hedef2.net,baska.bir.kullanici"
        ```
    *   `SENİN_KULLANICI_ADIN_BURAYA` kısmını kendi Bluesky kullanıcı adınızla (handle) değiştirin.
    *   `SENİN_ŞİFREN_BURAYA` kısmını kendi Bluesky **şifrenizle** (tercihen uygulama şifresi) değiştirin.
    *   `TARGET_USERS` satırındaki kullanıcı adlarını, takipçilerini takip etmek istediğiniz kişilerin kullanıcı adları (handle) ile değiştirin. **Kullanıcı adlarını virgülle (,) ayırın.**
    *   **Dosyayı `.env` olarak kaydedin** (dosya adında başta nokta olduğuna ve uzantısı olmadığına emin olun).

## Betiği Çalıştırma

1.  **Komut İstemi / Terminal'i Açın:**
    *   **Windows:** Başlat menüsüne `cmd` yazıp Komut İstemi'ni açın.
    *   **Linux/macOS:** Uygulamalarınızdan Terminal'i bulun ve açın.

2.  **Klasöre Gidin:**
    *   Komut istemcisine `cd` komutunu kullanarak `bs.py` ve `.env` dosyasının bulunduğu klasöre gidin. Örnek:
        *   Eğer dosyalar Masaüstündeki `bluesky_betikler` klasöründeyse:
            ```bash
            cd Desktop/bluesky_betikler
            ```
        *   (Windows'da `Desktop` yerine `Masaüstü` olabilir, yol size göre değişir.)

3.  **Betiği Çalıştırın:**
    *   Şu komutu girin:
        ```bash
        python bs.py
        ```
    *   Eğer `python` komutu çalışmazsa, `python3 bs.py` veya `py bs.py` (Windows'ta) deneyin.
    *   Betik çalışmaya başlayacak, `.env` dosyasındaki `TARGET_USERS` listesindeki hedefleri sırayla işleyecek ve kimleri takip ettiğini veya atladığını gösterecektir.

## Notlar

*   **Token Süresi:** Betik çalışırken Bluesky token'ınızın süresi dolarsa (genellikle birkaç saat), betik otomatik olarak yeniden giriş yapmaya çalışacak ve işleme devam edecektir.
*   **Beklemeler:** Betikteki kısa beklemeler (`time.sleep`), Bluesky API limitlerine çok hızlı takılmamak içindir.
*   **Hatalar:** Ağ hataları veya beklenmedik API yanıtları durumunda betik hata mesajı verip durabilir veya o anki hedefi atlayabilir. 