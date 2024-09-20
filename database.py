import sqlite3
from contextlib import closing
import random

DATABASE_FILE = "user_data.db"
generated_numbers = set()

def init_db():
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        cursor = conn.cursor()
        # إنشاء جدول المستخدمين مع ترتيب واضح للأعمدة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                account_number TEXT UNIQUE,
                balance REAL DEFAULT 0,
                language TEXT DEFAULT 'العربية'
            )
        ''')
        conn.commit()

def generate_account_number():
    while True:
        account_number = ''.join(random.choices('0123456789', k=8))
        if account_number not in generated_numbers:
            generated_numbers.add(account_number)
            return account_number

def save_user_data(user_id, language, balance, account_number):
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        cursor = conn.cursor()
        # إدخال أو تحديث بيانات المستخدم
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, account_number, balance, language)
            VALUES (?, ?, ?, ?)
        ''', (user_id, account_number, balance, language))
        conn.commit()

def load_user_data(user_id):
    with closing(sqlite3.connect(DATABASE_FILE)) as conn:
        cursor = conn.cursor()
        # تحميل بيانات المستخدم
        cursor.execute('SELECT account_number, balance, language FROM users WHERE user_id = ?', (user_id,))
        data = cursor.fetchone()
    
    if data:
        return data
    else:
        account_number = generate_account_number()
        save_user_data(user_id, 'العربية', 0, account_number)
        return account_number, 0, 'العربية'