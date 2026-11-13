import os
from dotenv import load_dotenv

load_dotenv()

# Подключение к MySQL в OSPanel
# Формат: mysql+pymysql://root:пароль@хост/имя_базы
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@MySQL-8.4.local/schedule_db?charset=utf8mb4'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = 'super-secret-key-for-admin'