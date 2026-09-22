# Sotstech Python Editor'ü .exe Yapma Rehberi (güncel)

## Bu pakette ne değişti?
`config.py` içindeki bir hata düzeltildi: önceki sürümde, exe'ye
çevrilince "dosyam" klasörü PyInstaller'ın geçici (temp) klasörüne
kuruluyordu ve exe her kapandığında o klasör -- içindeki
kaydettiğiniz dosyalarla birlikte -- siliniyordu. Bu yüzden
kaydettiğiniz dosyaları `from ... import ...` ile çağırdığınızda
"yok" diyordu. Artık "dosyam" klasörü exe'nin GERÇEKTEN bulunduğu
klasörde, kalıcı olarak oluşuyor.

## Adımlar

1. Varsa eski `dist`, `build` klasörlerini ve `.spec`, `build_env`
   klasörlerini bu proje klasöründen tamamen silin (eski hatalı
   derlemeden kalanlar karışmasın diye).

2. `ai_code_editor` klasörünü Windows bilgisayarınıza kopyalayın.

3. `build_exe.bat` dosyasına çift tıklayın. Script kendi izole
   sanal ortamını (`build_env`) kurup exe'yi orada derleyecek.

4. Derleme bitince:
   `ai_code_editor\dist\SotstechPythonEditor.exe`

5. exe'yi test edin: bir dosya kaydedip, başka bir sekmede
   `from <dosya_adi> import ...` yazın -- artık öneri gelmeli ve
   exe'yi kapatıp yeniden açtığınızda dosya hâlâ orada olmalı.

## Önemli
exe'yi masaüstünüzde veya istediğiniz bir klasöre koyabilirsiniz --
"dosyam" klasörü exe ile AYNI klasörde otomatik oluşacak. exe'yi
farklı bir bilgisayara/klasöre taşırsanız, "dosyam" da onunla
birlikte taşınmalı (ya da yeni konumda otomatik boş olarak
yeniden oluşturulur).
