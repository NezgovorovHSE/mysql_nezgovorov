# generate_test_data.py
import mysql.connector
import random
import os
import string
from datetime import datetime
from faker import Faker
from faker.providers import BaseProvider
import sys

# Настройки локализации для русских данных
fake = Faker('ru_RU')

# Кастомный провайдер для специфичных данных
class CustomProvider(BaseProvider):
    def russian_phone(self):
        return f'7{random.randint(9000000000, 9999999999)}'
    
    def supplier_phone(self):
        return f'{random.randint(1000000, 9999999)}'
    
    def current_account(self):
        return ''.join(str(random.randint(0, 9)) for _ in range(20))
    
    def product_name(self):
        products = [
            # Электроника
            'Смартфон', 'Ноутбук', 'Наушники', 'Планшет', 'Умные часы',
            'Телевизор', 'Игровая консоль', 'Фотоаппарат', 'Клавиатура', 'Мышь',
            'Монитор', 'Колонка Bluetooth', 'Роутер', 'Внешний жесткий диск',
            'Power Bank', 'Электронная книга', 'Фитнес-браслет', 'Дроид',
            
            # Одежда
            'Футболка', 'Джинсы', 'Куртка', 'Платье', 'Рубашка',
            'Свитер', 'Шорты', 'Пальто', 'Юбка', 'Блузка',
            'Толстовка', 'Брюки', 'Пиджак', 'Жилет', 'Комбинезон',
            
            # Книги
            'Роман', 'Детектив', 'Фэнтези', 'Научная литература', 'Учебник',
            'Биография', 'Поэзия', 'Комикс', 'Справочник', 'Энциклопедия',
            
            # Разное
            'Кофеварка', 'Блендер', 'Микроволновка', 'Чайник', 'Утюг',
            'Пылесос', 'Фен', 'Весы', 'Термопот', 'Мультиварка',
            'Игрушка', 'Настольная игра', 'Спортивный инвентарь', 'Косметика'
        ]
        adjectives = ['Профессиональный', 'Домашний', 'Портативный', 'Умный', 
                     'Быстрый', 'Энергосберегающий', 'Компактный', 'Стильный',
                     'Надежный', 'Инновационный', 'Классический', 'Модный']
        
        product = random.choice(products)
        if random.random() > 0.5:
            return f'{random.choice(adjectives)} {product} {random.choice(["Plus", "Pro", "Lite", "Max", "Mini"])}'
        elif random.random() > 0.7:
            brand = random.choice(['Xiaomi', 'Samsung', 'Apple', 'Sony', 'LG', 
                                  'Bosch', 'Philips', 'Nike', 'Adidas', 'Zara'])
            return f'{product} {brand} {random.randint(1, 10)}'
        else:
            return product
    
    def category_name(self):
        categories = [
            'Смартфоны', 'Ноутбуки', 'Аксессуары', 'Телевизоры', 'Аудиотехника',
            'Игровые консоли', 'Фототехника', 'Компьютерные комплектующие',
            'Мужская одежда', 'Женская одежда', 'Детская одежда', 'Обувь',
            'Аксессуары одежды', 'Спортивная одежда', 'Верхняя одежда',
            'Художественная литература', 'Научная литература', 'Детские книги',
            'Учебники', 'Комиксы', 'Энциклопедии', 'Бизнес-литература',
            'Кухонная техника', 'Климатическая техника', 'Бытовая техника',
            'Уход за собой', 'Товары для дома', 'Садовая техника',
            'Игрушки', 'Настольные игры', 'Конструкторы', 'Мягкие игрушки',
            'Спортивные товары', 'Туризм', 'Велосипеды', 'Фитнес',
            'Красота и здоровье', 'Парфюмерия', 'Косметика', 'Бижутерия',
            'Автотовары', 'Инструменты', 'Строительные материалы',
            'Офисная техника', 'Канцелярия', 'Мебель', 'Текстиль',
            'Продукты питания', 'Напитки', 'Сладости'
        ]
        return random.choice(categories)

fake.add_provider(CustomProvider)

def connect_to_db():
    try:
        conn = mysql.connector.connect(
            host='mysql',  # ← ЖЁСТКО mysql
            port=3306,
            user='root',
            password='Infinitum97',
            database='mydb',
            charset='utf8mb4'
        )
        print("✅ Успешное подключение к базе данных")
        return conn
    except mysql.connector.Error as err:
        print(f"❌ Ошибка подключения: {err}")
        sys.exit(1)

def clear_existing_data(conn):
    """Очистка существующих тестовых данных (кроме схемы)"""
    cursor = conn.cursor()
    
    # Отключаем проверку внешних ключей для очистки
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    
    # Очищаем таблицы в правильном порядке (обратном зависимостям)
    tables = ['order_items', 'orders', 'products', 'customers', 'suppliers', 'category']
    
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM `{table}`")
            conn.commit()
            print(f"🧹 Очищена таблица: {table}")
        except mysql.connector.Error as err:
            print(f"⚠️ Не удалось очистить {table}: {err}")
    
    # Включаем проверку внешних ключей обратно
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    cursor.close()

def generate_categories(conn, count=50):
    """Генерация категорий товаров"""
    cursor = conn.cursor()
    
    # Добавляем категорию "Другое" как первую (как в исходном скрипте)
    categories = ['Другое']
    
    # Генерируем уникальные категории
    while len(categories) < count:
        category = fake.category_name()
        if category not in categories:
            categories.append(category)
    
    inserted = 0
    for category in categories:
        try:
            cursor.execute(
                "INSERT IGNORE INTO category (product_category) VALUES (%s)",
                (category,)
            )
            inserted += cursor.rowcount
        except mysql.connector.Error as err:
            print(f"Ошибка при вставке категории {category}: {err}")
    
    conn.commit()
    cursor.close()
    print(f"✅ Сгенерировано категорий: {inserted}")
    return inserted

def generate_suppliers(conn, count=1000):
    """Генерация поставщиков"""
    cursor = conn.cursor()
    
    suppliers_data = []
    for i in range(count):
        supplier_name = fake.company()[:40]
        
        # Уникальные данные
        while True:
            email = f"{fake.user_name()}{i}@{fake.domain_name()}"
            phone = fake.supplier_phone()
            account = fake.current_account()
            
            # Проверка уникальности в уже сгенерированных данных
            if not any(s[3] == email for s in suppliers_data):
                break
        
        suppliers_data.append((
            supplier_name,
            account,
            phone,
            email.lower()
        ))
    
    inserted = 0
    for supplier in suppliers_data:
        try:
            cursor.execute(
                """INSERT INTO suppliers 
                (supplier_name, current_account, supplier_phone_number, supplier_email) 
                VALUES (%s, %s, %s, %s)""",
                supplier
            )
            inserted += cursor.rowcount
        except mysql.connector.Error as err:
            # Если дубликат - пропускаем
            if err.errno == 1062:
                continue
            print(f"Ошибка при вставке поставщика: {err}")
    
    conn.commit()
    cursor.close()
    print(f"✅ Сгенерировано поставщиков: {inserted}")
    return inserted

def generate_customers(conn, count=10000):
    """Генерация покупателей"""
    cursor = conn.cursor()
    
    batch_size = 500
    inserted = 0
    
    for batch_start in range(0, count, batch_size):
        batch_end = min(batch_start + batch_size, count)
        customers_batch = []
        
        for i in range(batch_start, batch_end):
            name = fake.name()
            address = fake.address().replace('\n', ', ')
            phone = fake.russian_phone()
            
            # Генерация уникального email
            email = f"{name.lower().replace(' ', '.')}{i}@{fake.domain_name()}"
            email = email.replace("'", "").replace('"', '')
            
            customers_batch.append((name, address, phone, email))
        
        # Вставка батчем
        try:
            cursor.executemany(
                """INSERT IGNORE INTO customers 
                (customer_name, customer_address, customer_phone_number, customer_email) 
                VALUES (%s, %s, %s, %s)""",
                customers_batch
            )
            inserted += cursor.rowcount
            conn.commit()
            
            # Прогресс
            if batch_end % 2000 == 0 or batch_end >= count:
                print(f"  Покупатели: {batch_end}/{count}")
                
        except mysql.connector.Error as err:
            print(f"Ошибка при вставке покупателей: {err}")
            conn.rollback()
    
    cursor.close()
    print(f"✅ Сгенерировано покупателей: {inserted}")
    return inserted

def generate_products(conn, count=50000):
    """Генерация продуктов с привязкой к существующим категориям и поставщикам"""
    cursor = conn.cursor()
    
    # Получаем все существующие категории и поставщиков
    cursor.execute("SELECT category_id FROM category")
    category_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT supplier_id FROM suppliers")
    supplier_ids = [row[0] for row in cursor.fetchall()]
    
    if not category_ids or not supplier_ids:
        print("❌ Нет категорий или поставщиков для привязки продуктов")
        return 0
    
    batch_size = 1000
    inserted = 0
    
    for batch_start in range(0, count, batch_size):
        batch_end = min(batch_start + batch_size, count)
        products_batch = []
        
        for i in range(batch_start, batch_end):
            product_name = fake.product_name()
            
            # Цены: purchase_price < selling_price
            purchase_price = random.randint(100, 10000)
            selling_price = random.randint(purchase_price + 50, purchase_price * 2)
            
            # Статус склада (от 0 до 1000)
            stock_status = random.randint(0, 1000)
            
            # Случайная категория и поставщик
            category_id = random.choice(category_ids)
            supplier_id = random.choice(supplier_ids)
            
            products_batch.append((
                product_name,
                category_id,
                purchase_price,
                selling_price,
                stock_status,
                supplier_id
            ))
        
        # Вставка батчем
        try:
            cursor.executemany(
                """INSERT INTO products 
                (product_name, category_id, purchase_price, selling_price, stock_status, supplier) 
                VALUES (%s, %s, %s, %s, %s, %s)""",
                products_batch
            )
            inserted += cursor.rowcount
            conn.commit()
            
            # Прогресс
            if batch_end % 10000 == 0 or batch_end >= count:
                print(f"  Продукты: {batch_end}/{count}")
                
        except mysql.connector.Error as err:
            print(f"Ошибка при вставке продуктов: {err}")
            conn.rollback()
    
    cursor.close()
    print(f"✅ Сгенерировано продуктов: {inserted}")
    return inserted

def verify_data(conn):
    """Проверка целостности данных"""
    cursor = conn.cursor()
    
    print("\n🔍 Проверка целостности данных:")
    
    tables = ['category', 'suppliers', 'customers', 'products']
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} записей")
    
    # Проверяем, что у всех продуктов есть категория и поставщик
    cursor.execute("""
        SELECT COUNT(*) FROM products 
        WHERE category_id IS NULL OR supplier IS NULL
    """)
    null_products = cursor.fetchone()[0]
    print(f"  Продуктов без категории/поставщика: {null_products}")
    
    cursor.close()

def main():
    """Основная функция"""
    print("🚀 Начало генерации тестовых данных")
    print("=" * 50)
    
    # Подключаемся к БД
    conn = connect_to_db()
    
    try:
        # Очищаем существующие данные
        print("\n1️⃣ Очистка существующих данных...")
        clear_existing_data(conn)
        
        # Генерация данных в правильном порядке
        print("\n2️⃣ Генерация категорий (50)...")
        generate_categories(conn, 50)
        
        print("\n3️⃣ Генерация поставщиков (1000)...")
        generate_suppliers(conn, 1000)
        
        print("\n4️⃣ Генерация покупателей (10000)...")
        generate_customers(conn, 10000)
        
        print("\n5️⃣ Генерация продуктов (50000)...")
        generate_products(conn, 50000)
        
        # Проверка данных
        print("\n6️⃣ Проверка целостности...")
        verify_data(conn)
        
        print("\n" + "=" * 50)
        print("✅ Генерация данных успешно завершена!")
        print("📊 Данные сохранены в базе данных mydb")
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("\n🔌 Соединение с базой данных закрыто")

if __name__ == "__main__":
    main()