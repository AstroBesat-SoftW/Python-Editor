<div align="center">

# 🧠 Sotstech Python Editor

### Yapay zekâ destekli, çok sekmeli, masaüstü Python kod editörü

![Python](https://img.shields.io/badge/python-3.9%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Windows-0078D6?logo=windows&logoColor=white)
![OpenAI](https://img.shields.io/badge/AI-OpenAI%20GPT--4o--mini-412991?logo=openai&logoColor=white)
![Build](https://img.shields.io/badge/build-PyInstaller-orange)
![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-2.0.34-blueviolet)

**Kod yaz, tek tıkla çalıştır, seçtiğin kod parçasına doğal dilde talimat ver, yapay zekâ senin için düzenlesin.**
Eksik kütüphaneleri otomatik kurar, `input()` çağrılarını pencere ile karşılar, matplotlib/OpenCV gibi grafik çıktılarını sorunsuz gösterir.

[Özellikler](#-özellikler) •
[Ekran Görüntüleri](#-ekran-görüntüleri) •
[Kurulum](#-kurulum) •
[API Anahtarı](#-openai-api-anahtarını-tanımlama) •
[.exe Olarak Kullanım](#-hazır-exe-ile-kullanım-windows) •
[Teknolojiler](#️-kullanılan-teknolojiler) •
[Proje Yapısı](#-proje-yapısı)

</div>

---

## 📌 Hakkında

**Sotstech Python Editor**, Tkinter üzerine inşa edilmiş, karanlık temalı, profesyonel görünümlü bir masaüstü Python IDE'sidir. Klasik bir kod editörünün tüm temel özelliklerini (çoklu sekme, satır numarası, sözdizimi renklendirme, çalıştırma konsolu) sunmanın yanında, işin içine **OpenAI destekli bir yapay zekâ asistanı** ekler: editördeki herhangi bir kod bloğunu seçip *"bunu optimize et"*, *"hata yönetimi ekle"*, *"bunu iki modüle böl"* gibi doğal dilde bir talimat verirsiniz; yapay zekâ kodu talimata göre yeniden yazar ve siz onaylamadan hiçbir değişiklik editöre yansımaz.

Bu proje sıfırdan geliştirilmiş, tek dosyalık (`.exe`) bir Windows uygulaması olarak da dağıtılabilir — kaynak kod ile birlikte PyInstaller derleme betiği de bu depoda yer alır.

---

## 🖼 Ekran Görüntüleri

Aşağıdaki akış, uygulamanın gerçek kullanımından alınmıştır: sıfır kod yazmadan sadece **doğal dil talimatı** vererek, matematiksel bir denklemi 3B grafiğe döken ve ardından bir webcam uygulamasını anında çalıştırıp çalıştıran uçtan uca bir örnektir.

<table>
<tr>
<td width="50%">

**1️⃣ Ana ekran ve hazır demo**
Karanlık IDE teması, sekme çubuğu, araç çubuğu (Run / AI Suggest / Add API Key) ve alt konsol paneli. Uygulama ilk açıldığında kullanım talimatlarını içeren bir örnek dosya (`demo.py`) hazır gelir ve tek tıkla çalıştırılabilir.

<img src="docs/screenshots/01-editor-anasayfa.png" width="100%">

</td>
<td width="50%">

**2️⃣ AI Suggest — doğal dilde talimat**
`Ctrl+Space` ya da araç çubuğundaki **AI Suggest** butonuyla açılan pencereye, seçili kod için ne yapılmasını istediğiniz yazılır. Burada örnek talimat: *"main.py ve işlem/grafik modülünden oluşan, kullanıcıdan denklem alıp 3B grafik çizen modüler bir Python çözümü yaz."*

<img src="docs/screenshots/02-ai-suggest-talimat.png" width="100%">

</td>
</tr>
<tr>
<td width="50%">

**3️⃣ Yapay zekânın ürettiği kod — önizleme**
Model, talimatı iki dosyalık (`main.py` + `processing.py`) çalışan bir çözüme dönüştürür. Kod editöre uygulanmadan önce tam metin olarak gösterilir; kullanıcı **"Yes, Replace Code"** ile onaylar ya da reddeder.

<img src="docs/screenshots/03-ai-suggest-sonuc.png" width="100%">

</td>
<td width="50%">

**4️⃣ Üretilen kod, sözdizimi renklendirmeli sekmede**
Onaylanan kod otomatik olarak ilgili sekmeye (burada `processing.py`) yazılır; `numpy`, `matplotlib`, `sympy` importları ve fonksiyon tanımı canlı sözdizimi renklendirmesiyle görüntülenir.

<img src="docs/screenshots/04-uretilen-kod-sekmesi.png" width="100%">

</td>
</tr>
<tr>
<td width="50%">

**5️⃣ Çalışma anında `input()` desteği**
Kod `input()` çağırdığında konsol donmaz — bunun yerine yerel bir **"Input Required"** penceresi açılır, kullanıcı değeri girer ve program kaldığı yerden devam eder.

<img src="docs/screenshots/05-input-dialog.png" width="100%">

</td>
<td width="50%">

**6️⃣ Anlık çalıştırma + grafik çıktısı**
`Run` (`F5`) ile kod çalıştırılır, konsolda `sympy` ile ayrıştırılmış denklem yazdırılır ve `matplotlib` ile interaktif, döndürülebilir bir **3B yüzey grafiği** ayrı bir pencerede açılır.

<img src="docs/screenshots/06-3d-grafik-ciktisi.png" width="100%">

</td>
</tr>
<tr>
<td width="50%">

**7️⃣ Eksik kütüphaneleri otomatik kurma**
Yeni bir örnekte (`cv2` ile kamera uygulaması) çalıştırılan kodun ihtiyaç duyduğu `numpy` ve `opencv-python` paketleri sistemde yoksa veya sürüm uyumsuzsa, editör bunu tespit edip **arka planda `pip` ile otomatik kurar** ve kodu yeniden çalıştırır — kullanıcı terminale hiç dokunmaz.

<img src="docs/screenshots/07-otomatik-paket-kurulumu.png" width="100%">

</td>
<td width="50%">

**8️⃣ Gerçek zamanlı donanım erişimi**
Otomatik kurulumun ardından `OpenCV` penceresi açılır ve bilgisayarın kamerasından canlı görüntü akışını gösterir — editör, GUI açan/pencere oluşturan (matplotlib, OpenCV, Tkinter vb.) her türlü Python kodunu sorunsuz destekler.

<img src="docs/screenshots/08-canli-kamera-ciktisi.png" width="100%">

</td>
</tr>
</table>

---

## ✨ Özellikler

### 📝 Editör
- **Çok sekmeli düzenleme** — `+ New Tab` (`Ctrl+T`) ile sınırsız sayıda sayfa; `Run` ve `AI Suggest` her zaman aktif sekme üzerinde çalışır.
- **Sözdizimi renklendirme** — harici bağımlılık gerektirmeyen, hafif regex tabanlı Python vurgulayıcı (anahtar kelimeler, string'ler, yorumlar, sayılar, built-in fonksiyonlar).
- **Senkronize satır numarası gutter'ı** her sekmede.
- **Modern koyu tema** — profesyonel renk paleti, araç çubuğu, sekme şeridi, durum çubuğu.
- **Standart dosya işlemleri** — Open / Save / Save As, sekme bazlı kaydedilmemiş değişiklik koruması.
- **`dosyam/` çalışma alanı** — açtığınız/kaydettiğiniz her dosya uygulamayla aynı klasördeki bu klasörde tutulur.
- **`import` otomatik önerisi** — `import ` veya `from ` yazmaya başlayınca, `dosyam/` klasöründeki diğer `.py` dosyaları soluk gri renkte önerilir; `Tab` ile kabul edilir.
- **Kilitlenmeye dayanıklı tasarım** — kodunuzda, AI isteğinde ya da editörün kendisinde oluşan her beklenmeyen hata yakalanır, size gösterilir ve Output paneline loglanır; uygulama asla sessizce kapanmaz.

### 🤖 Yapay Zekâ Asistanı
- **Talimat tabanlı kod önerisi** — herhangi bir kod parçasını seçip `AI Suggest` (`Ctrl+Space`) ile ne yapılmasını istediğinizi serbest metin olarak yazarsınız (*"performansı artır"*, *"hata yönetimi ekle"*, *"bunu iki dosyaya böl"* vb.).
- **Onay mekanizması** — üretilen kod doğrudan uygulanmaz; yan yana önizlenir, siz **Replace** ya da **Keep Original** seçersiniz.
- **Tek seferlik API anahtarı kaydı** — `Add API Key` ile bir kez girilen anahtar yerel olarak saklanır, bir daha sorulmaz.
- **OpenAI Chat Completions** üzerinden `gpt-4o-mini` modeli kullanılır (model, ortam değişkeni ile değiştirilebilir).

### ▶️ Kod Çalıştırma Motoru
- **Tek tıkla çalıştırma** (`F5`) — aktif sekmenin kodu çalıştırılır, çıktı/hata ortak konsol panelinde gösterilir.
- **Çalışan `input()` desteği** — konsolu kilitlemeden değeri bir pencere ile alır.
- **Eksik paket tespiti ve otomatik kurulum** — `ModuleNotFoundError` / ABI uyuşmazlığı gibi durumlarda ilgili pip paketini otomatik tespit edip kurar, ardından kodu tekrar çalıştırır.
- **matplotlib GUI backend yönetimi** — grafik çıktılarının ayrı, interaktif bir pencerede (Tk backend) doğru şekilde açılmasını garanti eder.
- **GUI açan her türlü kodu destekler** — matplotlib, OpenCV, Tkinter gibi pencere/kamera açan scriptler dahil.

### 📦 Dağıtım
- **PyInstaller ile tek dosya `.exe`** — `build_exe.bat`, izole bir sanal ortam kurup bağımlılıkları oraya kurar ve `--onefile --windowed` modunda derler; ekstra kurulum gerektirmez.
- `dosyam/` klasörü, derlenmiş `.exe` ile **aynı gerçek klasörde** kalıcı olarak oluşturulur (PyInstaller'ın geçici klasörüne değil) — böylece kaydettiğiniz dosyalar uygulamayı kapatıp açtığınızda kaybolmaz.

---

## ⌨️ Klavye Kısayolları

| İşlem                | Kısayol            |
|-----------------------|---------------------|
| Kodu çalıştır         | `F5`                |
| AI Suggest            | `Ctrl + Space`      |
| Yeni sekme            | `Ctrl + T`          |
| Sekmeyi kapat         | `Ctrl + W`          |
| Dosya aç              | `Ctrl + O`          |
| Kaydet                | `Ctrl + S`          |
| Farklı kaydet         | `Ctrl + Shift + S`  |

---

## 🛠️ Kullanılan Teknolojiler

| Katman | Teknoloji | Amaç |
|---|---|---|
| **Dil** | Python 3.9+ | Uygulamanın tamamı saf Python ile yazılmıştır |
| **Arayüz (GUI)** | Tkinter / `ttk` | Pencere, sekmeler, menüler, diyaloglar, koyu tema |
| **Yapay Zekâ** | [OpenAI API](https://platform.openai.com/) (`openai` Python SDK) — model: `gpt-4o-mini` | Seçili kodu, kullanıcı talimatına göre yeniden yazma |
| **Ortam değişkenleri** | `python-dotenv` | Opsiyonel `.env` dosyasından `OPENAI_API_KEY` okuma |
| **Süreç yönetimi** | `subprocess`, `importlib` | Eksik pip paketlerini arka planda tespit edip kurma |
| **Paketleme** | [PyInstaller](https://pyinstaller.org/) | Tek dosyalık, bağımlılık gerektirmeyen `.exe` üretimi |
| **Kalıcı ayarlar** | Yerel JSON dosyası (`~/.sotstech_python_editor/settings.json`) | API anahtarının güvenli/kalıcı şekilde saklanması |
| **Örnek/çalıştırılabilir kodlarda** (kullanıcı tarafında, editörün kendi bağımlılığı değil) | `sympy`, `numpy`, `matplotlib`, `opencv-python` | Ekran görüntülerindeki 3B grafik ve kamera örnekleri bu editörde **üretilip çalıştırılan** kodlardır; editör bu paketleri kod ihtiyaç duyduğunda otomatik kurar |

> ℹ️ **Not:** `sympy`, `numpy`, `matplotlib`, `opencv-python` editörün kendi `requirements.txt`'inde **yer almaz**. Bunlar, editör içinde yazılan/AI ile üretilen örnek programların bağımlılıklarıdır ve editörün "eksik paketi otomatik kurma" özelliği sayesinde ilk çalıştırmada otomatik yüklenir.

---

## 📥 Kurulum

### Gereksinimler
- Python **3.9+**
- (Opsiyonel) Bir **OpenAI API anahtarı** — sadece *AI Suggest* özelliği için gereklidir; editör ve kod çalıştırma özelliği anahtar olmadan da tam çalışır.

### Kaynak koddan çalıştırma

```bash
git clone https://github.com/<kullanici-adiniz>/<repo-adi>.git
cd <repo-adi>/ai_code_editor
python -m pip install -r requirements.txt
python main.py
```

---

## 🔑 OpenAI API Anahtarını Tanımlama

Herhangi bir dosya düzenlemenize veya ortam değişkeni ayarlamanıza **gerek yoktur**:

1. Araç çubuğundaki **Add API Key** butonuna (veya menüden **AI Assistant → Add API Key**) tıklayın.
2. `sk-...` ile başlayan OpenAI API anahtarınızı yapıştırın.
3. **Save Key**'e basın.

Anahtar, kullanıcı klasörünüzdeki küçük bir ayar dosyasına (`~/.sotstech_python_editor/settings.json`) kaydedilir ve uygulama her açıldığında otomatik yüklenir. Aynı pencereden istediğiniz zaman anahtarı güncelleyebilir veya silebilirsiniz.

> 🔒 Anahtarınız yalnızca kendi bilgisayarınızda yerel olarak saklanır; bir öneri istediğinizde doğrudan OpenAI'ye gönderilir dışında hiçbir yere iletilmez.

*(İleri düzey/opsiyonel: `OPENAI_API_KEY` ortam değişkeni ya da yerel bir `.env` dosyası da tanımlayabilirsiniz — bu, kayıtlı anahtara göre önceliklidir.)*

```env
# .env (opsiyonel)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini
```

---

## 💾 Hazır .exe ile Kullanım (Windows)

Kaynak kodu hiç görmeden, Python kurmadan doğrudan kullanmak isteyenler için derlenmiş sürüm:

1. **[Releases](../../releases)** bölümünden en güncel `SotstechPythonEditor.exe` dosyasını indirin *(ya da bu depodaki `ai_code_editor/dist/` klasöründen)*.
2. `.exe` dosyasını istediğiniz bir klasöre koyun ve çift tıklayarak çalıştırın — kurulum gerekmez.
3. Uygulama ilk açıldığında, `.exe` ile **aynı klasörde** otomatik olarak bir `dosyam/` klasörü oluşturulur; tüm açtığınız/kaydettiğiniz dosyalar burada kalıcı olarak tutulur.
4. AI Suggest özelliğini kullanmak için yukarıdaki [API anahtarı adımlarını](#-openai-api-anahtarını-tanımlama) izleyin.

> ⚠️ `.exe`'yi farklı bir bilgisayara veya klasöre taşırsanız, yanındaki `dosyam/` klasörünü de birlikte taşıyın (taşımazsanız yeni konumda otomatik olarak boş şekilde yeniden oluşturulur).

### Kendi `.exe` dosyanızı derlemek isterseniz

Depoda hazır bir derleme betiği bulunur:

```bat
cd ai_code_editor
build_exe.bat
```

Bu betik izole bir sanal ortam (`build_env`) kurar, bağımlılıkları oraya yükler ve PyInstaller ile `--onefile --windowed` modunda derler. Çıktı: `ai_code_editor\dist\SotstechPythonEditor.exe`. Detaylı adımlar için [`HOW_TO_BUILD_EXE.md`](HOW_TO_BUILD_EXE.md) dosyasına bakın.

---

## 📂 Proje Yapısı

```
SotstechPythonEditor/
├── ai_code_editor/
│   ├── main.py                    # Uygulama giriş noktası
│   ├── editor_app.py              # Ana pencere: sekmeler, menüler, araç çubuğu, çalıştırma motoru
│   ├── editor_tab.py              # Tek bir editör sekmesi (metin alanı, gutter, durum)
│   ├── ai_assistant.py            # OpenAI API entegrasyonu (talimat tabanlı)
│   ├── syntax_highlighter.py      # Hafif Python sözdizimi renklendirici
│   ├── line_numbers.py            # Satır numarası gutter bileşeni
│   ├── console_redirector.py      # stdout/stderr çıktısını Output paneline yönlendirir
│   ├── theme.py                   # Merkezi renk/yazı tipi/boşluk tanımları
│   ├── config.py                  # Uygulama ayarları, API anahtarı ve çalışma alanı yolları
│   ├── app_icon.ico                # Uygulama simgesi
│   ├── SotstechPythonEditor.spec   # PyInstaller derleme tanımı
│   ├── build_exe.bat               # Tek tıkla .exe derleme betiği
│   ├── requirements.txt
│   ├── dosyam/                     # Varsayılan çalışma alanı — dosyalarınız burada
│   │   ├── demo.py                   # Örnek dosya (import önerisi + input() denemesi)
│   │   └── helper_utils.py           # İçe aktarılabilecek örnek ikinci modül
│   └── dist/
│       └── SotstechPythonEditor.exe  # ← Derlenmiş .exe'yi buraya ekleyin
├── docs/
│   └── screenshots/                # README'deki ekran görüntüleri
├── HOW_TO_BUILD_EXE.md
└── README.md
```

---

## 🔐 Güvenlik Notu

Editördeki `Run` komutu, yazdığınız kodu `exec()` ile çalıştırır — tıpkı yerelde kendi başınıza çalıştıracağınız herhangi bir Python betiği gibi. **Sadece güvendiğiniz kodu çalıştırın.** API anahtarınız yalnızca kendi makinenizde saklanır ve yalnızca doğrudan OpenAI'ye giden isteklerde kullanılır.

---

## 🗺️ Yol Haritası

- [ ] Çoklu AI sağlayıcı desteği (Anthropic, yerel modeller)
- [ ] Entegre `pip` paket yöneticisi paneli
- [ ] Tema özelleştirme (açık/koyu tema geçişi)
- [ ] macOS / Linux için derleme betikleri

---

## 🤝 Katkıda Bulunma

Katkılar memnuniyetle karşılanır! Bir *issue* açabilir veya doğrudan *pull request* gönderebilirsiniz:

```bash
git checkout -b ozellik/harika-bir-ozellik
git commit -m "Harika bir özellik eklendi"
git push origin ozellik/harika-bir-ozellik
```

---

## 📄 Lisans

Bu proje **MIT Lisansı** ile lisanslanmıştır — kullanabilir, değiştirebilir ve üzerine geliştirme yapabilirsiniz. Detaylar için [`LICENSE`](LICENSE) dosyasına bakın.

---

<div align="center">

Made with ❤️ using Python & OpenAI — **Sotstech Python Editor**

</div>
