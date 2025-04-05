# Bluesky Otomatik Takip Betiği (`bsautofollow.py`)

**!!! BU BETİĞİ KULLANIRKEN ÇOK DİKKATLİ OLUNUZ !!!**

Bu betik **DENEYSEL** ve **RİSKLİDİR**. Belirli hashtag'leri kullanan ve yerel bir LLM (Ollama) tarafından yapılan karmaşık bir analize dayanarak "uygun" olarak sınıflandırılan (Türkçe konuşan, muhtemelen demokrasi/laiklik yanlısı, AKP/muhafazakar karşıtı) Bluesky kullanıcılarını otomatik olarak takip etmeye çalışır.

**ANA RİSKLER:**

*   **HATALI ANALİZ:** Dil ve politik/dünya görüşü eğilimini belirlemek için kullanılan yapay zeka analizi **ÇOK GÜVENİLMEZ** olup **sık sık HATA yapacaktır**. İroni, alay, alıntı veya incelikli ifadeleri doğru yorumlayamayabilir. Betik büyük olasılıkla gerçek kriterlerinize uymayan kullanıcıları takip edecek (veya etmeyecektir).
*   **ONAYSIZ OTOMATİK TAKİP:** Betik, bir kullanıcıyı takip etmeden önce **ONAY İSTEMEZ**. Analizdeki hatalar doğrudan istenmeyen takip eylemlerine yol açar.
*   **KULLANIM KOŞULLARI İHLALİ/API LİMİTLERİ:** Agresif veya hatalı otomatik takip, Bluesky kullanım koşullarını ihlal edebilir ve hesabınızın **kısıtlanmasına veya askıya alınmasına** neden olabilir. Betik beklemeler içerse de, özellikle çok sayıda hashtag/aday varsa API limitlerini aşmaya karşı bir garanti yoktur.
*   **KRİTERLERİN ÖZNELLİĞİ:** Kriterler ("demokratik", "muhafazakar", "laik", "tuhaf şeyler") özneldir ve LLM tarafından sizden farklı yorumlanabilir.

**KULLANIM TAMAMEN SİZİN SORUMLULUĞUNUZDADIR! YAZAR, BU BETİĞİN KULLANIMINDAN KAYNAKLANAN İSTENMEYEN TAKİP EYLEMLERİ, HESAP KISITLAMALARI VEYA DİĞER SONUÇLARDAN DOLAYI HİÇBİR SORUMLULUK KABUL ETMEZ.**

## Nasıl Çalışır?

1.  **Hashtag Araması:** `.env` dosyasında tanımlanan hashtag'leri içeren gönderileri arar.
2.  **Aday Seçimi:** Bu gönderilerin yazarlarını toplar (hashtag başına en fazla 50).
3.  **Analiz (Her Aday İçin):**
    *   Zaten takip edilip edilmediğini kontrol eder (ediliyorsa atlar).
    *   Profil bilgilerini ve son ~5 gönderiyi alır.
    *   Bu verileri, değerlendirme için karmaşık bir prompt ile Ollama'ya gönderir:
        *   Dil (Türkçe mi?)
        *   Dünya Görüşü (Demokrasi/Laiklik Yanlısı mı? AKP/Muhafazakar Karşıtı mı?)
    *   Ollama bir tavsiye döndürür: `TAKIP_ET` veya `TAKIP_ETME`.
4.  **Otomatik Eylem:**
    *   Ollama `TAKIP_ET` tavsiye ederse, betik kullanıcıyı **otomatik olarak** takip eder.
5.  **Raporlama:** Sonunda bir istatistik özeti gösterir.

## Gereksinimler

*   **Python 3:** Yüklü ve sistem yolunda tanımlı.
*   **Ollama:** Yüklü, **çalışıyor** ve uygun bir **Türkçe anlayan model** (örn. `llama3`, `mistral`) indirilmiş olmalı. Kurulum detayları için `README_analyze.md` dosyasına bakın.
*   **Gerekli Python Kütüphaneleri:** `requests`, `python-dotenv`.

## Kurulum

1.  **Betiği İndirme:** `bsautofollow.py` dosyasını bilgisayarınızdaki bir klasöre kaydedin.
2.  **Kütüphaneleri Yükleme:**
    ```bash
    pip install requests python-dotenv
    ```
    (Veya `pip3`, `py -m pip` vb., `README_analyze.md` dosyasına bakın)
3.  **`.env` Dosyası Oluşturma/Düzenleme:** `bsautofollow.py` ile aynı klasörde bir `.env` dosyası bulunmalıdır. Aşağıdaki satırları ekleyin veya mevcutları düzenleyin (yer tutucuları değiştirin):
    ```dotenv
    BLUESKY_USERNAME="SENIN_BLUESKY_KULLANICI_ADIN"
    BLUESKY_PASSWORD="SENIN_BLUESKY_UYGULAMA_SIFREN_VEYA_GIRIS_SIFREN"
    OLLAMA_BASE_URL="http://localhost:11434" # Varsayılan Ollama adresi
    OLLAMA_MODEL="llama3" # Ollama ile kullanmak istediğiniz model
    SEARCH_HASHTAGS="özgürgenclik,alkolboykot,laiklik" # Hashtagleriniz (# olmadan), virgülle ayrılmış!
    ```
    *   **ÖNEMLİ:** `SEARCH_HASHTAGS` kısmını istediğiniz arama terimleriyle güncelleyin. Terimleri sadece virgülle, etraflarında boşluk bırakmadan ayırın.

## Çalıştırma

1.  **Ollama'yı Başlatın:** Ollama'nın çalıştığından emin olun.
2.  **Terminal/Komut İstemi Açın:** `cd` komutu ile `bsautofollow.py` ve `.env` dosyalarının bulunduğu klasöre gidin.
3.  **Betiği Başlatın:**
    ```bash
    python bsautofollow.py
    ```
    (Veya `python3 bsautofollow.py`, `py bsautofollow.py`)
4.  **İlerlemeyi İzleyin:** Betik, ilerleme hakkında birçok bilgi yazdıracaktır. Hashtag ve bulunan kullanıcı sayısına bağlı olarak uzun sürebilir.
5.  **Sonucu Kontrol Edin:** Sonunda özet rapor gösterilecektir.

**Tekrar: Çok dikkatli olun ve betiğin kimi takip ettiğini düzenli olarak manuel kontrol edin!** 