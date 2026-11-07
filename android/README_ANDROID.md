# 📱 คู่มือการติดตั้งและใช้งาน VegCare AI บน Android

คุณสามารถใช้งานและติดตั้ง **VegCare AI** บนสมาร์ตโฟน Android ได้ 2 รูปแบบตามความสะดวกครับ:

---

## รูปแบบที่ 1: ติดตั้งลงบนมือถือ Android ทันที (PWA WebAPK - แนะนำ สะดวกที่สุด ไม่ต้องคอมไพล์)

ระบบรองรับมาตรฐาน **Progressive Web App (PWA)** เมื่อติดตั้งแล้วจะมีไอคอนแอป 🥬 VegCare AI บนหน้าจอหลัก (Home Screen) เปิดใช้งานแบบเต็มจอ (Standalone) และเรียกใช้งานกล้องถ่ายรูปได้เหมือนแอป Native 100%

### ขั้นตอนการติดตั้ง:
1. **เชื่อมต่อ Wi-Fi เดียวกัน**: ตรวจสอบว่ามือถือ Android เชื่อมต่อสัญญาณ Wi-Fi วงเดียวกับคอมพิวเตอร์ที่เปิดเซิร์ฟเวอร์
2. **เปิดหน้าแอปบนคอมพิวเตอร์**: ดับเบิลคลิก `run.bat` ในคอมพิวเตอร์
3. **สแกน QR Code**: 
   - คลิกที่ปุ่ม **"📱 ติดตั้งบน Android"** ที่แถบเมนูด้านบนของหน้าเว็บ
   - ใช้กล้องมือถือสแกน QR Code ที่แสดงขึ้นมา หรือพิมพ์ URL ใน **Google Chrome**:
     ```
     http://192.168.1.54:5000
     ```
4. **กดติดตั้งแอป**:
   - บนหน้าจอมือถือจะมีแถบแจ้งเตือนขึ้นมาถามว่า **"ติดตั้งแอป (Install App)"**
   - หรือแตะที่เมนูจุด 3 จุด (⋮) ด้านขวาบนของ Google Chrome แล้วเลือก **"เพิ่มลงในหน้าจอหลัก (Add to Home screen)"** หรือ **"ติดตั้งแอป"**
5. **พร้อมใช้งาน**: ไอคอนแอป **VegCare AI** จะปรากฏบนหน้าจอมือถือของคุณทันที สามารถพกพาไปถ่ายรูปและตรวจโรคผักในสวนหรือแปลงเกษตรได้ทันที!

---

## รูปแบบที่ 2: คอมไพล์เป็นไฟล์ APK ผ่าน Android Studio (Native WebView App)

หากต้องการไฟล์ `.apk` สำหรับติดตั้งแบบ sideloading ซอร์สโค้ดโปรเจกต์ Android Studio พร้อมใช้งานถูกจัดเตรียมไว้ในโฟลเดอร์นี้เรียบร้อยแล้ว:

### โครงสร้างโปรเจกต์ Android:
```
Vegapp/android/
├── app/
│   ├── src/main/
│   │   ├── java/com/vegcare/ai/MainActivity.java   # WebView + Camera Intent + FileChooser
│   │   ├── res/                                   # เลย์เอาต์ ไอคอน ธีม และข้อความภาษาไทย
│   │   │   ├── layout/activity_main.xml
│   │   │   ├── values/strings.xml (ตั้งค่า Server URL)
│   │   │   ├── values/colors.xml
│   │   │   ├── values/themes.xml
│   │   │   ├── xml/file_paths.xml (FileProvider สำหรับกล้อง)
│   │   │   ├── mipmap-hdpi/ic_launcher.png
│   │   │   └── mipmap-xxhdpi/ic_launcher.png
│   │   └── AndroidManifest.xml                    # สิทธิ์การเข้าถึงกล้องและอินเทอร์เน็ต
│   └── build.gradle
├── build.gradle
├── settings.gradle
└── gradle.properties
```

### ขั้นตอนการ Build APK ด้วย Android Studio:
1. เปิดโปรแกรม **Android Studio**
2. เลือกเมนู **Open** แล้วเลือกโฟลเดอร์ `c:\Note\other program\Vegapp\android`
3. หากต้องการเปลี่ยน IP เซิร์ฟเวอร์ ให้แก้ไขที่ไฟล์ `app/src/main/res/values/strings.xml` ที่แท็ก:
   ```xml
   <string name="default_server_url">http://192.168.1.54:5000</string>
   ```
4. ไปที่เมนูด้านบนเลือก **Build** > **Build Bundle(s) / APK(s)** > **Build APK(s)**
5. Android Studio จะสร้างไฟล์ `app-debug.apk` ให้นำไปติดตั้งบนมือถือ Android ได้ทันที
