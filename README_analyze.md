# Bluesky Detaylı Takip Edilen Analiz Betiği (`bsanalyze.py`)

Bu betik, Bluesky sosyal ağında takip ettiğiniz kişilerin profil yazılarını ve son gönderilerini/yanıtlarını analiz etmek için bilgisayarınızda yerel olarak çalışan bir yapay zeka dil modeli (LLM) olan Ollama'yı kullanır. Betik, kullanıcıları belirli kriterlere göre **detaylı olarak** değerlendirir:

*   Konuşulan dil (Türkçe mi?)
*   Laik/Seküler/Atatürkçü duruş belirtileri (Pozitif)
*   AKP/Erdoğan destekçisi duruş belirtileri (Negatif)
*   Şeriat yanlısı/Aşırı Muhafazakar duruş belirtileri (Negatif)

**>> BU BETİK OTOMATİK OLARAK KİMSEYİ TAKİPTEN ÇIKARMAZ! <<**

Bu betik **yalnızca analiz yapar**. Her bir takip edilen kullanıcı için analiz sonuçlarını ekranda gösterir ve betiğin çalıştığı klasörde **`analiz_sonuclari.txt`** adlı bir dosyaya detaylı olarak kaydeder. Bu dosyayı inceleyip, takip listeniz hakkında daha detaylı bir fikir edinebilirsiniz.

## !!! ÇOK ÖNEMLİ UYARILAR !!!

*   **LLM ANALİZİ DENEYSELDİR VE HATALIDIR:** Yapay zeka analizi **kesin değildir** ve **%100 doğru sonuç vermez**. Özellikle politik ve dünya görüşü gibi karmaşık ve nüanslı konuları değerlendirirken **hatalar yapacaktır**. İroni, alay, alıntılar veya bağlam dışı ifadeler yanlış yorumlanabilir. **Bu betiğin çıktısını yalnızca bir ipucu ve başlangıç noktası olarak kullanın. Sonuçlara dayanarak kesin yargılara varmadan veya manuel işlem yapmadan önce mutlaka kendiniz de profilleri dikkatlice kontrol edin.**
*   **ÇOK YAVAŞ ÇALIŞMA:** LLM analizi, özellikle çok sayıda kişiyi takip ediyorsanız **çok yavaş çalışacaktır**. Betik, takip ettiğiniz her kullanıcı için profil bilgilerini ve gönderilerini Bluesky'den almalı, ardından bu bilgileri bilgisayarınızdaki Ollama yapay zeka modeline gönderip yanıtını beklemelidir. Bu süreç, takip ettiğiniz kişi sayısına ve bilgisayarınızın işlem gücüne bağlı olarak **saatler sürebilir**.
*   **YEREL LLM GEREKLİ:** Bu betiği kullanmak için bilgisayarınızda **Ollama yazılımının kurulu ve çalışır durumda olması** ve analiz için uygun bir dil modelinin (örneğin `llama3`, `mistral` gibi Türkçe anlayabilen bir model) indirilmiş olması **zorunludur**.
*   **GÜVENLİK:** Bluesky şifrenizi içeren `.env` dosyasını **güvende tutun** ve kimseyle paylaşmayın.
*   **API LİMİTLERİ:** Bluesky'nin API kullanım limitleri vardır. Çok sayıda kullanıcıyı kısa sürede analiz etmek bu limitleri zorlayabilir ve hesabınızın geçici olarak kısıtlanmasına neden olabilir. Betik içinde beklemeler olsa da dikkatli olun.
*   **SORUMLULUK:** Bu betiği kullanmak **TAMAMEN SİZİN SORUMLULUĞUNUZDADIR**. Analiz sonuçlarının doğruluğu garanti edilmez ve betiğin kullanımından kaynaklanabilecek herhangi bir sorun veya kısıtlamadan sorumluluk kabul edilmez.

## Adım Adım Kurulum ve Kullanım (Windows ve Linux)

Bu bölümde, betiği çalıştırmak için gerekli yazılımların nasıl kurulacağı ve betiğin nasıl kullanılacağı adım adım anlatılmaktadır.

### Adım 1: Python 3 Kurulumu

Betiği çalıştırmak için bilgisayarınızda Python 3 yüklü olmalıdır.

1.  **Python Yüklü mü Kontrol Edin:**
    *   **Windows:** Başlat menüsünü açın, `cmd` yazıp "Komut İstemi"ni çalıştırın. Açılan siyah ekrana `python --version` yazıp Enter'a basın. Eğer bir sürüm numarası (örn. `Python 3.10.4`) görünüyorsa ve sürüm 3 ile başlıyorsa, Python 3 yüklüdür. Hata verirse veya sürüm 2 ile başlıyorsa, `py --version` veya `python3 --version` komutlarını deneyin.
    *   **Linux:** Terminal uygulamasını açın (genellikle Ctrl+Alt+T kısayolu ile açılır). `python3 --version` yazıp Enter'a basın. Sürüm numarası görünüyorsa Python 3 yüklüdür.
2.  **Python Yükleyin (Eğer Yüklü Değilse):**
    *   **Windows:**
        1.  Web tarayıcınızı açın ve [https://www.python.org/downloads/](https://www.python.org/downloads/) adresine gidin.
        2.  "Download Python" düğmesine tıklayarak en son sürümün yükleyicisini indirin.
        3.  İndirilen `.exe` dosyasını çalıştırın.
        4.  **ÇOK ÖNEMLİ:** Yükleyicinin ilk ekranında en altta bulunan **"Add Python.exe to PATH"** veya **"Add Python 3.x to PATH"** kutucuğunu **işaretleyin**.
        5.  "Install Now" seçeneğine tıklayın ve kurulumun tamamlanmasını bekleyin.
    *   **Linux:** Genellikle Linux dağıtımları Python 3 ile birlikte gelir. Eğer yoksa veya eski bir sürüm varsa, terminalde şu komutlarla yükleyebilirsiniz (Dağıtıma göre komut değişebilir):
        *   **Debian/Ubuntu/Mint:** `sudo apt update && sudo apt install python3 python3-pip`
        *   **Fedora:** `sudo dnf install python3 python3-pip`

### Adım 2: Ollama Kurulumu ve Model İndirme

Bu betik, analiz için Ollama'yı kullanır.

1.  **Ollama'yı İndirin ve Kurun:**
    *   Web tarayıcınızla [https://ollama.com/](https://ollama.com/) adresine gidin.
    *   "Download" düğmesine tıklayın ve işletim sisteminize (Windows veya Linux) uygun sürümü indirin.
    *   **Windows:** İndirilen `.exe` dosyasını çalıştırın ve kurulum sihirbazını takip edin. Ollama genellikle kurulumdan sonra otomatik olarak arka planda çalışmaya başlar.
    *   **Linux:** İndirme sayfasındaki Linux kurulum talimatlarını takip edin. Genellikle terminalde çalıştırılacak tek satırlık bir komut (`curl ... | sh`) verilir.
2.  **Ollama'nın Çalıştığından Emin Olun:**
    *   **Windows:** Görev çubuğunuzun sağ alt köşesindeki bildirim alanında Ollama (lama) ikonunu görmelisiniz. Göremiyorsanız, Başlat menüsünden Ollama'yı aratıp çalıştırın.
    *   **Linux:** Terminali açıp `ollama` yazıp Enter'a basın. Yardım metni çıkıyorsa çalışıyordur. Sistem servisi olarak kurulduysa genellikle otomatik başlar (`systemctl status ollama` ile kontrol edilebilir).
3.  **Dil Modelini İndirin:**
    *   Ollama'nın analiz yapabilmesi için bir dil modeline ihtiyacı vardır. Türkçe'yi iyi anlayan modellerden birini (örneğin `llama3` veya `mistral`) indirmeniz gerekir.
    *   **Windows:** Komut İstemi'ni (`cmd`) açın.
    *   **Linux:** Terminali açın.
    *   Açılan ekrana şu komutu yazıp Enter'a basın (örnek olarak `llama3` modeli):
        ```bash
        ollama pull llama3
        ```
        (Eğer başka bir model, örneğin `mistral` kullanmak isterseniz: `ollama pull mistral`)
    *   Modelin boyutuna göre indirme işlemi biraz zaman alabilir. İndirme bitene kadar bekleyin.

### Adım 3: Betik Dosyasını İndirme

1.  `bsanalyze.py` adlı betik dosyasını bu projenin bulunduğu yerden (örneğin GitHub sayfasından) bilgisayarınıza indirin.
2.  İndirdiğiniz dosyayı kolayca bulabileceğiniz bir klasöre kaydedin (örneğin Masaüstünde `bluesky_analiz` adında yeni bir klasör oluşturup içine koyabilirsiniz).

### Adım 4: Gerekli Python Kütüphanelerini Yükleme

Betiğin çalışması için `requests` ve `python-dotenv` adlı iki ek Python kütüphanesine ihtiyaç vardır.

1.  **Windows:** Komut İstemi'ni (`cmd`) açın.
2.  **Linux:** Terminali açın.
3.  Açılan ekrana aşağıdaki komutu **tam olarak** yazıp Enter'a basın:
    ```bash
    pip install requests python-dotenv
    ```
4.  **Eğer Windows'ta `pip` bulunamadı hatası alırsanız:** Önce `pip3 install requests python-dotenv` komutunu deneyin. O da olmazsa `py -m pip install requests python-dotenv` komutunu deneyin.
5.  **Eğer Linux'ta `pip` bulunamadı hatası alırsanız:** `pip3 install requests python-dotenv` komutunu deneyin.
6.  Kütüphanelerin indirilip kurulmasını bekleyin.

### Adım 5: Yapılandırma Dosyasını (`.env`) Oluşturma

Betik, Bluesky giriş bilgilerinizi ve Ollama ayarlarınızı güvenli bir şekilde saklamak için `.env` adlı bir dosya kullanır.

1.  Betiği kaydettiğiniz klasöre gidin (örneğin `bluesky_analiz` klasörü).
2.  Bu klasörün içinde **yeni bir metin dosyası** oluşturun.
    *   **Windows:** Klasörde boş bir alana sağ tıklayın, "Yeni" -> "Metin Belgesi" seçin. Dosya adı olarak geçici bir isim verin (örn. `yapilandirma`), sonra adını değiştireceğiz.
    *   **Linux:** Metin düzenleyici kullanın (örn. `gedit .env` veya terminalde `nano .env`).
3.  Oluşturduğunuz bu boş metin dosyasını açın ve içine **tam olarak** aşağıdaki satırları kopyalayıp yapıştırın:
    ```dotenv
    BLUESKY_USERNAME="SENIN_BLUESKY_KULLANICI_ADIN"
    BLUESKY_PASSWORD="SENIN_BLUESKY_UYGULAMA_SIFREN_VEYA_GIRIS_SIFREN"
    OLLAMA_BASE_URL="http://localhost:11434"
    OLLAMA_MODEL="llama3"
    ```
4.  **Bu satırları kendi bilgilerinizle değiştirin:**
    *   `"SENIN_BLUESKY_KULLANICI_ADIN"` yazan yeri, tırnak işaretlerini koruyarak kendi Bluesky **kullanıcı adınızla** (handle, örn. `"ornek.bsky.social"`) değiştirin.
    *   `"SENIN_BLUESKY_UYGULAMA_SIFREN_VEYA_GIRIS_SIFREN"` yazan yeri, tırnak işaretlerini koruyarak kendi Bluesky **şifrenizle** değiştirin. (Güvenlik için uygulama şifresi (App Password) kullanmanız önerilir, eğer oluşturduysanız onu yazın).
    *   `OLLAMA_BASE_URL="http://localhost:11434"` satırını genellikle değiştirmeniz gerekmez. Ollama varsayılan olarak bu adreste çalışır.
    *   `OLLAMA_MODEL="llama3"` satırındaki `llama3` kısmını, Adım 2'de indirdiğiniz ve kullanmak istediğiniz Ollama modelinin adıyla (örn. `mistral`) değiştirin. Model adını doğru yazdığınızdan emin olun.
5.  **Dosyayı `.env` olarak kaydedin:**
    *   **Windows (Not Defteri):** "Dosya" -> "Farklı Kaydet..." seçeneğine gidin. "Kayıt türü" olarak **"Tüm Dosyalar (\*.\*)"** seçeneğini seçin. Dosya adı olarak **tam olarak** `.env` (başında nokta var, sonunda uzantı yok!) yazın ve "Kaydet" düğmesine tıklayın. Windows size uzantısız kaydetmek isteyip istemediğinizi sorarsa onaylayın.
    *   **Linux:** Eğer `nano .env` ile açtıysanız, `Ctrl+X` tuşuna basın, kaydetmek için `E` (veya `Y`) tuşuna basın ve dosya adı `.env` olarak onaylayıp Enter'a basın. Diğer metin düzenleyicilerde de farklı kaydetme seçeneklerini kullanarak adı `.env` yapın.

### Adım 6: Betiği Çalıştırma

Artık her şey hazır, betiği çalıştırabiliriz.

1.  **Ollama'nın Çalıştığından Emin Olun:** Adım 2'de açıklandığı gibi Ollama'nın arka planda çalıştığından emin olun.
2.  **Komut İstemi / Terminal'i Açın:**
    *   **Windows:** Başlat menüsüne `cmd` yazıp "Komut İstemi"ni açın.
    *   **Linux:** Terminal uygulamasını açın.
3.  **Betiğin Olduğu Klasöre Gidin:** `cd` komutunu kullanarak betik dosyasının (`bsanalyze.py`) ve `.env` dosyasının bulunduğu klasöre gidin.
    *   Örnek (Eğer dosyalar Masaüstündeki `bluesky_analiz` klasöründeyse):
        *   Windows: `cd Desktop\bluesky_analiz` (yol sizde farklı olabilir)
        *   Linux: `cd Desktop/bluesky_analiz` (yol sizde farklı olabilir)
4.  **Betiği Çalıştırın:** Komut istemcisine aşağıdaki komutu yazıp Enter'a basın:
    ```bash
    python bsanalyze.py
    ```
    *   Eğer `python` komutu bulunamadı hatası verirse, Windows'ta `py bsanalyze.py`, Linux'ta `python3 bsanalyze.py` deneyin.
5.  **İşlemi İzleyin:**
    *   Betik önce Ollama'ya bağlanmayı deneyecek, sonra Bluesky'e giriş yapacak ve takip ettiğiniz kişileri listeleyecektir.
    *   Ardından her bir kullanıcı için **detaylı analiz** sürecini başlatacaktır. Ekranda hangi kullanıcının analiz edildiğini ve Ollama'dan gelen detaylı yanıtı (Dil, Pozitif_Laik, Negatif_AKP, Negatif_Seriat) göreceksiniz.
    *   Bu işlem takip ettiğiniz kişi sayısına bağlı olarak **uzun sürebilir**. Sabırlı olun.
    *   İşlem bittiğinde, analiz edilen kullanıcı sayısı ve hata sayısı özetlenecektir.

### Adım 7: Sonuçları İnceleme

*   Betik bittikten sonra, betiğin çalıştığı klasörde **`analiz_sonuclari.txt`** adlı bir dosya bulacaksınız.
*   Bu dosyayı bir metin düzenleyici ile açarak **her bir takip ettiğiniz kullanıcı için detaylı analiz sonuçlarını** (Dil, Pozitif_Laik, Negatif_AKP, Negatif_Seriat) görebilirsiniz.
*   **Unutmayın:** Bu analizler yapay zeka tahminidir ve hatalı olabilir. Listeyi ve sonuçları dikkatlice inceleyin.

## Notlar

*   **Token Süresi:** Betik çalışırken Bluesky oturumunuzun süresi dolarsa (genellikle birkaç saat), betik otomatik olarak yeniden giriş yapmaya çalışır ve kaldığı yerden devam etmeye çalışır.
*   **Beklemeler:** Betik, Bluesky ve Ollama API'lerini aşırı yüklememek için işlemler arasında otomatik olarak kısa süreler bekler.
*   **Hatalar:** Ağ bağlantısı sorunları, Bluesky API hataları veya Ollama ile ilgili sorunlar nedeniyle hatalar oluşabilir. Betik genellikle hatalı kullanıcıyı atlayıp devam etmeye çalışır ve sonunda hata sayısını raporlar. 