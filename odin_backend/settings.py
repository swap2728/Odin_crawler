from decimal import Decimal  # Add this import at the top of the file
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-t!6w-5co7rxl(!3w7t#di2=d1+lbk1p=#=9x_-7ynanip5cj*-'

DEBUG = False

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "rest_framework",
    "crawler",
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'odin_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'odin_backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "frontend", "dist"),
]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = True
CSRF_TRUSTED_ORIGINS = ["http://localhost:8000", "http://localhost:5173"]

# Razorpay Configuration
# Add these to your existing settings
RAZORPAY_KEY_ID = "rzp_live_JCExPjTteNgBfp"
RAZORPAY_KEY_SECRET = "FIzzzQeXFAJRACGj4TRjojYd"
RAZORPAY_WEBHOOK_SECRET = "Winner@2003"
RAZORPAY_PLAN_ID = "plan_QDLtHDl4bb7LQd"
RAZORPAY_SUBSCRIPTION_ID = "sub_QDRgsHdV69HCt2"
RAZORPAY_SUBSCRIPTION_LINK = "https://rzp.io/rzp/Qli0K4kY"
WEBHOOK_URL = "https://astraeusnextgen.com/verification"


# # Subscription Settings
# TRIAL_PERIOD_DAYS = 3
# SUBSCRIPTION_AMOUNT_USD = Decimal('0.012')  # $0.012 ≈ ₹1 when converted