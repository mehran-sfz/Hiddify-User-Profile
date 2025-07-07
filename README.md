# 🌐 پروفایل مدیریت کاربر هیدیفای

  
<div dir="rtl">
  

**پروفایل هیدیفای** یک وبسایت واسطه است که با استفاده از API **Hiddify** به کاربران این امکانات را ارائه می‌دهد:  

  

✅ دسترسی به اطلاعات حساب  

✅ ایجاد کانفیگ جدید  

✅ تمدید حساب  

✅ افزودن اطلاعات پرداخت  

✅ پرداخت از طریق سایت

  

---

  

  

## ✨ ویژگی‌ها

  

  

- 🔄 **بروزرسانی اطلاعات کاربران هر 1 دقیقه** (قابل تنظیم توسط کاربر)

- 🤖 **ربات تلگرامی** برای اطلاع‌رسانی کاربران در موارد زیر:

- 📅 موعد پرداخت

- ⏳ پایان یافتن اشتراک (زمانی یا حجمی)

- 🦾 **ربات ادمین** برای ربات برای ارسال اطلاعات پرداختی و دریافت نوتیفیکیشن هنگام ساخت اشتراک جدید

- 🔗 **تعریف لینک دعوت** (فقط با اجازه ادمین یا لینک دعوت اکانت فعال می‌شود)

- 🔒 **استفاده از HTTPS** با پشتیبانی از SSL برای امنیت بیشتر

- 🚀 **نصب آسان** با استفاده از Docker

  

  

---

  

  

## 🛠 ابزارهای استفاده‌شده

  

  

- 🐍 **Python Django**

- 💬 **Telegram Bot**

- ⚙️ **Celery** و **Redis** برای مدیریت وظایف زمان‌بندی‌شده

- 🗄 **PostgreSQL** به عنوان دیتابیس

- 🌐 **Nginx** برای مدیریت وب سرور

- 📦 **Docker** برای مدیریت و راه‌اندازی آسان

  

  

---

  

  

## 📖 آموزش استفاده و راه‌اندازی

  

  

### 💡 پیش‌نیازها:

  

1. 🌐 **یک دامنه معتبر**

2. 🖥 **یک سرور VPS**

3. 📦 **نصب داکر و docker compose**

  

  

---

  

  

### 🚀 مراحل نصب:

  

  

#### 1️⃣ آماده‌سازی اولیه

  

ابتدا سرور خود را بروزرسانی کنید:

  

```bash

sudo apt-get update && sudo apt-get upgrade -y

```

  

  

## 2️⃣ دریافت پروژه

  

پروژه را از گیت‌هاب دانلود کنید:

  

```bash

git clone https://github.com/mehran-sfz/Hiddify-User-Profile.git

```

  

وارد دایرکتوری پروژه شوید:

  

```bash

cd Hiddify-User-Profile

```

  

  

## 3️⃣ تنظیمات Nginx

  

فایل پیکربندی Nginx را باز کنید:

  

```bash

nano nginx/nginx.conf

```

  

🔄 در فایل، عبارت {YOURDOMIAN.COM} را با دامنه خود (مانند: mydomain.com) جایگزین کنید.

  

برای ذخیره و خروج، از کلیدهای زیر استفاده کنید:

  

- **Ctrl + O** برای ذخیره فایل
- **Enter** برای تأیید
- **Ctrl + X** برای خروج

  

  

## 4️⃣ تنظیمات سایت

  

فایل های .env پروژه با باز و طبق نیاز خود تغییر دهید.

  

  

```bash

nano hiddify/.env
nano telegram_bot/.env

```

  

```bash

## App variables

DEBUG=False # برای فعال سازی دولوپر مود
IS_DEVELOPMENT=False # برای فعال سازی دولوپر مود
ALLOWED_HOSTS=YOUR_DOMAIN_NAME # آدرس دامنه ی متصل به آیپی سرور EXAMPLE: example.com


# database
DATABASE_NAME=postgres
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_HOST=database
DATABASE_PORT=5432


# redis
REDIS_PASSWORD=REDIS_PASSWORD_HERE # EXAMPLE: "my_redis_password"
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0 
CELERY_RESULT_BACKEND=${CELERY_BROKER_URL}

# security
IS_HTTPS_USED=True
CSRF_COOKIE_SECURE=True # برای امنیت post requests ها
SESSION_COOKIE_SECURE=True


# configs
WAITING_FOR_PAYMENT_TIMEOUT_DAYS = 5 # مدت زمان انتظار بعد از سفارش هر اشتراک قبل از قطع شدن در صورت پرداخت نشدن صورت حساب
WARNING_FOR_PAYMENT_TIMEOUT_DAYS = 3 # پیام به ربات بعد از سه روز انتظار در صورت پرداخت نشدن اشتراک
WARNING_FOR_CONFIG_TIMEOUT_DAYS = 5 # 5 روز قبل از تموم شدن اشتراک یادآوری شود به کاربر
WARNING_FOR_USAGE_GB = 5 # کمتر از 5 گیگ اعتبار به کاربر اطلاع داده شود
FETCH_USERS_DURATION_SECONDS = 60 # گرفتن اطلاعات کاربر از هیدیفای پس هر 60 ثانیه
TELEGRAM_NOTIFICATION_INTERVAL_HOURS = 12 # نوتیفیکیشن های تلگرام هر 12 ساعت ارسال شود

  
# information

CHANNEL_LINK="https://t.me/YOUR_CHANNEL_ID_HERE" # EXAMPLE: "https://t.me/batmanam2" لینک چنل خود
SUPPORT_TELEGRAM_LINK="https://t.me/YOUR_SUPPORT_TELEGRAM_ID_HERE" # EXAMPLE: "https://t.me/batmanam2" لینک دامنه ی پشتیبانی خود

```

  

- فایل را متناسب با نیاز خود تغییر دهید و ذخیره کنید.

  
  

  

## 5️⃣ تنظیمات SSL

  

فایل docker-compose.yml را باز کنید:

  

  

```bash

nano docker-compose.yml

```

  

  

در بخش certbot، مقادیر زیر را جایگزین کنید:

  

بخش های زیر را با # کامنت کنید (اگر هنوز cert خود را نگرفته اید)

  

```bash

  - ./nginx/nginx.conf:/etc/nginx/nginx.conf
  - ./certbot/conf:/etc/letsencrypt
  - ./certbot/www:/var/www/certbot
  - static:/var/www/static
  - media:/var/www/media

```

  

و بخش های زیر را از کامنت خارج کنید:

  

```bash

  - ./nginx/nginx-temp.conf:/etc/nginx/nginx.conf:ro
  - ./certbot/conf:/etc/letsencrypt
  - ./certbot/www:/var/www/certbot

```

  

در بخش certbot نیز اطلاعات مورد نیاز خود را جایگذاری کنید.

  

```bash

  - YOUREMAIL@EMAIL.COM: ایمیل خود
  - YOUTDOMAIN.COM: دامنه خود

```

سپس فایل را ذخیره و ببندید.

  

  

## 7️⃣ راه‌اندازی نهایی

  

دستور زیر را اجرا کنید تا پروژه ساخته و اجرا شود:

  

  

```bash


chmod +x ./hiddify/entrypoint.sh
docker-compose up -d --build


```

  
  

پس از Build شدن و گرفتن certbot حالا دوباره وارد docker-compose.yml شوید مواردی را که کامت کردید از کامنت خارج کنید و مواردی که از کامنت در آوردید را کامنت کنید.

  

```bash

nano docker-compose.yml

```

  

  سپس دستورات زیر را وارد کنید.

```bash

docker-compose down
docker-compose up -d --build

```

  

سایت شما آماده استفاده است.

  

---

  

  

## 🎯 مراحل بعد از راه‌اندازی

  

  

پس از اینکه سایت شما کاملاً بالا آمد، می‌توانید تنظیمات تکمیلی زیر را انجام دهید:

  

  

### 🧑‍💻 ایجاد SuperUser

  

برای دسترسی به پنل مدیریت Django، یک **SuperUser** ایجاد کنید. دستور زیر را اجرا کنید:

  

```bash

docker exec -it hiddify-app python manage.py createsuperuser

```

  

اطلاعات خواسته‌شده (شماره تماس ، رمز عبور) را وارد کنید تا کاربر مدیریت ایجاد شود.

  

  

## 🔧 افزودن اطلاعات API Hiddify

  

- 1- وارد سایت خود شوید.

  

- 2- به Django Admin Panel بروید.

  

- 3- از بخش Task Manager به Hiddify Info بروید.

  

- 4- اطلاعات API مربوط به Hiddify خود را وارد کنید.

  

  

## 🤖 تنظیمات اطلاعات تلگرام

  

- 1- از پنل مدیریت Django به بخش Telegram Bot بروید.

  

- 2- اطلاعات ربات تلگرام (مانند توکن و سایر تنظیمات) را در این بخش وارد کنید.

  

## 🏦 اطلاعات بانکی

  

- برای افزودن اطلاعات بانکی مثل شماره کارت برای پرداختی های کاربر از Bank_ informations اقدام کنید.

  

  

### 🎉 پایان

  

حالا همه چیز آماده است! 🌟

  

💻 از سایت خود لذت ببرید، و کاربران خود را خوشحال کنید. 😊

  
  

اگر مشکلی داشتید، حتماً بررسی کنید که تنظیمات و اطلاعات به‌درستی وارد شده‌اند.

  

موفق باشید! 🚀

حمایت مالی:

بیت کوین: `bc1ql6276z020qeyzrep3uwg4lln46gyqzz2zxhtr6`


سولانا: `4UPBtQuqH7w9yY9wZ7pd8EK1n6xqeihCeMrcqSqPmSev`


تتر: `4UPBtQuqH7w9yY9wZ7pd8EK1n6xqeihCeMrcqSqPmSev`


ترون: `TRxjtaPhT4sdoFXqueEAM97gTdY14uCRCW`



<!-- add screenshots -->


برگه ورود:
![برگه ورود](https://github.com/mehran-sfz/Hiddify-User-Profile/blob/main/screenshots/login.png?raw=true)


برگه ثبت نام:
![برگه ثبت نام](https://github.com/mehran-sfz/Hiddify-User-Profile/blob/main/screenshots/signup.png?raw=true)


برگه خانه کاربر:
![برگه خانه کاربر](https://github.com/mehran-sfz/Hiddify-User-Profile/blob/main/screenshots/user_home.png?raw=true)

برگه اضافه یا خرید کاربر:
![برگه اضافه یا خرید کاربر](https://github.com/mehran-sfz/Hiddify-User-Profile/blob/main/screenshots/user_buy_and_add.png?raw=true)


برگه خانه ادمین:
![برگه خانه ادمین](https://github.com/mehran-sfz/Hiddify-User-Profile/blob/main/screenshots/admin_home.png?raw=true)



</div>