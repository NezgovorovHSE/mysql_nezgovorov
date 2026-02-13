# generate_orders.py
import mysql.connector
import random
import logging
from datetime import datetime, timedelta
import sys
import time
import os
from decimal import Decimal

# Настройки
TARGET_ORDER_ITEMS = int(os.getenv('TARGET_ORDER_ITEMS', 2000000))
ITEMS_PER_BATCH = 10000

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
error_logger = logging.getLogger('error_logger')
error_logger.setLevel(logging.ERROR)

def connect_to_db():
    """Подключение к MySQL базе данных"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'mysql'),
            port=int(os.getenv('DB_PORT', '3306')),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'Infinitum97'),
            database=os.getenv('DB_NAME', 'mydb'),
            charset='utf8mb4',
            autocommit=False
        )
        logger.info("✅ Успешное подключение к базе данных")
        return conn
    except mysql.connector.Error as err:
        error_logger.error(f"❌ Ошибка подключения: {err}")
        raise

def get_random_customer_id(cursor):
    """Получение случайного customer_id"""
    try:
        cursor.execute("SELECT customer_id FROM customers ORDER BY RAND() LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else None
    except mysql.connector.Error as err:
        error_logger.error(f"Ошибка при получении customer_id: {err}")
        return None

def get_random_product_with_stock(cursor):
    """Получение случайного продукта с проверкой наличия на складе"""
    try:
        cursor.execute("""
            SELECT product_id, selling_price, stock_status 
            FROM products 
            WHERE stock_status > 0
            ORDER BY RAND() 
            LIMIT 1
        """)
        result = cursor.fetchone()
        if result:
            return {
                'product_id': result[0],
                'selling_price': result[1],
                'stock_status': result[2]
            }
        return None
    except mysql.connector.Error as err:
        error_logger.error(f"Ошибка при получении продукта: {err}")
        return None

def generate_order_data(cursor, start_date):
    """Генерация данных для одного заказа"""
    try:
        customer_id = get_random_customer_id(cursor)
        if not customer_id:
            raise ValueError("Нет доступных покупателей")
        
        discount = Decimal(str(round(random.uniform(0, 30), 2)))  # Скидка до 30%
        
        days_ahead = random.randint(0, 365)
        order_datetime = start_date + timedelta(days=days_ahead)
        order_date = order_datetime.date()
        order_time = order_datetime.time()
        
        num_items = random.randint(1, 5)  # Уменьшил для стабильности
        order_items = []
        
        for _ in range(num_items):
            product = get_random_product_with_stock(cursor)
            if not product:
                continue
            
            max_quantity = min(10, product['stock_status'])  # Не больше 10 и не больше чем на складе
            if max_quantity <= 0:
                continue
                
            quantity = random.randint(1, max_quantity)
            order_items.append({
                'product_id': product['product_id'],
                'quantity': quantity,
                'selling_price': product['selling_price']
            })
        
        if not order_items:
            raise ValueError("Не удалось добавить позиции в заказ (нет товаров в наличии)")
        
        return {
            'customer_id': customer_id,
            'discount': discount,
            'order_date': order_date,
            'order_time': order_time,
            'items': order_items
        }
        
    except Exception as e:
        error_logger.error(f"Ошибка генерации данных заказа: {str(e)}")
        raise

def create_order_simple(cursor, order_data):
    """Упрощенное создание заказа - ВСЕ В ОДНОЙ ТРАНЗАКЦИИ"""
    try:
        order_id = None
        
        # 1. Вставляем заказ
        cursor.execute("""
            INSERT INTO orders 
            (customer_id, discount, order_cost, order_date, order_time)
            VALUES (%s, %s, 0, %s, %s)
        """, (
            order_data['customer_id'],
            float(order_data['discount']),
            order_data['order_date'],
            order_data['order_time']
        ))
        
        order_id = cursor.lastrowid
        
        # 2. Вставляем позиции с FIXED_PRICE
        total_cost = 0
        for item in order_data['items']:
            # Вставляем с фиксированной ценой СРАЗУ
            cursor.execute("""
                INSERT INTO order_items 
                (order_id, product_id, product_quantity, fixed_price)
                VALUES (%s, %s, %s, %s)
            """, (
                order_id,
                item['product_id'],
                item['quantity'],
                item['selling_price']  # Вот здесь фиксируем цену!
            ))
            
            # Уменьшаем остатки
            cursor.execute("""
                UPDATE products 
                SET stock_status = stock_status - %s
                WHERE product_id = %s
            """, (item['quantity'], item['product_id']))
            
            total_cost += item['selling_price'] * item['quantity']
        
        # 3. Применяем скидку и обновляем стоимость
        discount = float(order_data['discount'])
        final_cost = int(total_cost * (1 - discount / 100))
        
        cursor.execute("""
            UPDATE orders 
            SET order_cost = %s 
            WHERE order_id = %s
        """, (final_cost, order_id))
        
        logger.debug(f"Создан заказ #{order_id}, стоимость: {final_cost}")
        return order_id
        
    except Exception as e:
        error_logger.error(f"Ошибка при создании заказа: {str(e)}")
        raise

def update_prices(cursor, percentage_increase):
    """Увеличение цен на определенный процент"""
    try:
        logger.info(f"🔧 Повышение цен на {percentage_increase}%...")
        
        cursor.execute("""
            UPDATE products 
            SET purchase_price = ROUND(purchase_price * %s),
                selling_price = ROUND(selling_price * %s)
        """, (
            1 + percentage_increase / 100,
            1 + percentage_increase / 100
        ))
        
        updated_rows = cursor.rowcount
        logger.info(f"✅ Обновлено цен: {updated_rows} продуктов")
        return updated_rows
        
    except mysql.connector.Error as err:
        error_logger.error(f"Ошибка при обновлении цен: {err}")
        return 0

def generate_order_summary_txt(order_id, order_data, output_file):
    """Запись информации о заказе в текстовый файл"""
    try:
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"ЗАКАЗ #{order_id}\n")
            f.write(f"{'='*60}\n")
            f.write(f"Покупатель ID: {order_data['customer_id']}\n")
            f.write(f"Дата: {order_data['order_date']} {order_data['order_time']}\n")
            f.write(f"Скидка: {order_data['discount']}%\n")
            f.write(f"\nПозиции заказа:\n")
            f.write(f"{'-'*60}\n")
            
            for i, item in enumerate(order_data['items'], 1):
                f.write(f"{i}. Товар ID: {item['product_id']}\n")
                f.write(f"   Количество: {item['quantity']} шт.\n")
                f.write(f"   Цена: {item['selling_price']} руб.\n")
            
            f.write(f"{'='*60}\n\n")
            
    except Exception as e:
        error_logger.error(f"Ошибка записи в файл: {str(e)}")

def display_progress(current, total, start_time):
    """Отображение прогресса"""
    elapsed = time.time() - start_time
    percent = (current / total) * 100 if total > 0 else 0
    
    if current > 0 and elapsed > 0:
        time_per_item = elapsed / current
        remaining = (total - current) * time_per_item
        
        elapsed_str = time.strftime('%H:%M:%S', time.gmtime(elapsed))
        remaining_str = time.strftime('%H:%M:%S', time.gmtime(remaining))
        speed = current / elapsed
    else:
        elapsed_str = "00:00:00"
        remaining_str = "??:??:??"
        speed = 0
    
    sys.stdout.write(f"\r📊 Прогресс: {current:,}/{total:,} ({percent:.1f}%) | "
                     f"Прошло: {elapsed_str} | Осталось: {remaining_str} | "
                     f"Скорость: {speed:.1f} поз./сек")
    sys.stdout.flush()

def verify_data_quality(cursor):
    """Проверка качества сгенерированных данных"""
    logger.info("\n🔍 ПРОВЕРКА КАЧЕСТВА ДАННЫХ:")
    
    try:
        # 1. Проверка fixed_price
        cursor.execute("SELECT COUNT(*) FROM order_items WHERE fixed_price IS NULL")
        null_fixed = cursor.fetchone()[0]
        logger.info(f"   Позиций с NULL fixed_price: {null_fixed}")
        
        # 2. Проверка order_cost
        cursor.execute("SELECT COUNT(*) FROM orders WHERE order_cost = 0")
        zero_cost = cursor.fetchone()[0]
        logger.info(f"   Заказов с order_cost = 0: {zero_cost}")
        
        # 3. Проверка вычислений
        cursor.execute("""
            SELECT o.order_id, o.order_cost, o.discount,
                   SUM(oi.product_quantity * oi.fixed_price) as calculated_total,
                   ROUND(SUM(oi.product_quantity * oi.fixed_price) * (1 - o.discount/100)) as should_be
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            GROUP BY o.order_id
            HAVING o.order_cost != ROUND(SUM(oi.product_quantity * oi.fixed_price) * (1 - o.discount/100))
            LIMIT 5
        """)
        mismatches = cursor.fetchall()
        
        logger.info(f"   Заказов с неверным расчетом: {len(mismatches)}")
        
        if mismatches:
            logger.info("   Примеры ошибок:")
            for row in mismatches:
                logger.info(f"     Заказ #{row[0]}: cost={row[1]}, calculated={row[4]}, diff={row[1]-row[4]}")
        
        # 4. Примеры корректных заказов
        cursor.execute("""
            SELECT o.order_id, o.order_cost, COUNT(oi.order_item_id) as items_count,
                   MIN(oi.fixed_price) as min_price, MAX(oi.fixed_price) as max_price
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.order_cost > 0 AND oi.fixed_price IS NOT NULL
            GROUP BY o.order_id
            ORDER BY o.order_id DESC
            LIMIT 3
        """)
        good_examples = cursor.fetchall()
        
        logger.info("   Примеры корректных заказов:")
        for ex in good_examples:
            logger.info(f"     Заказ #{ex[0]}: cost={ex[1]}, items={ex[2]}, prices={ex[3]}-{ex[4]}")
        
        return null_fixed == 0 and zero_cost == 0
    
    except Exception as e:
        logger.error(f"Ошибка при проверке данных: {e}")
        return False

def main():
    """Основная функция"""
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК ГЕНЕРАТОРА ЗАКАЗОВ")
    logger.info("=" * 60)
    
    # Подготовка
    os.makedirs('/app/generated_data', exist_ok=True)
    output_file = f'/app/generated_data/orders_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("ОТЧЕТ О СОЗДАННЫХ ЗАКАЗАХ\n")
        f.write(f"Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Целевое количество позиций: {TARGET_ORDER_ITEMS:,}\n")
        f.write("=" * 60 + "\n\n")
    
    conn = None
    cursor = None
    
    try:
        # Подключение
        conn = connect_to_db()
        cursor = conn.cursor()
        
        # В main() после подключения к БД добавьте:
        cursor.execute("SET autocommit = 0")
        cursor.execute("SET unique_checks = 0")
        cursor.execute("SET foreign_key_checks = 0")
        
        # Проверка данных
        cursor.execute("SELECT COUNT(*) as cnt FROM customers")
        customers = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) as cnt FROM products WHERE stock_status > 0")
        products = cursor.fetchone()[0]
        
        logger.info(f"📊 Доступно покупателей: {customers:,}")
        logger.info(f"📊 Товаров в наличии: {products:,}")
        
        if customers == 0 or products == 0:
            logger.error("❌ Недостаточно данных для генерации заказов")
            return
        
        # Генерация
        start_date = datetime.now()
        total_order_items = 0
        total_orders = 0
        batch_counter = 0
        start_time = time.time()
        
        logger.info(f"\n🎲 Начинаю генерацию {TARGET_ORDER_ITEMS:,} позиций...")
        
        while total_order_items < TARGET_ORDER_ITEMS:
            try:
                # Начинаем транзакцию для КАЖДОГО заказа
                conn.start_transaction()
                
                # Генерируем и создаем заказ
                order_data = generate_order_data(cursor, start_date)
                order_id = create_order_simple(cursor, order_data)
                
                # Коммитим - ЭТО КЛЮЧЕВОЙ МОМЕНТ!
                conn.commit()
                
                # Логируем
                generate_order_summary_txt(order_id, order_data, output_file)
                
                # Считаем
                num_items = len(order_data['items'])
                total_order_items += num_items
                total_orders += 1
                batch_counter += num_items
                
                # Прогресс
                if total_orders % 50 == 0 or total_order_items >= TARGET_ORDER_ITEMS:
                    display_progress(total_order_items, TARGET_ORDER_ITEMS, start_time)
                
                # Периодическое обновление цен
                if batch_counter >= ITEMS_PER_BATCH and total_order_items < TARGET_ORDER_ITEMS:
                    logger.info(f"\n💰 Обновление цен после {batch_counter:,} позиций...")
                    price_increase = random.uniform(5, 15)
                    conn.start_transaction()
                    update_prices(cursor, price_increase)
                    conn.commit()
                    batch_counter = 0
                    logger.info(f"   Цены повышены на {price_increase:.1f}%")
                
            except Exception as e:
                # Откат при ошибке
                if conn:
                    conn.rollback()
                error_logger.error(f"❌ Ошибка заказа #{total_orders+1}: {str(e)[:100]}")
                continue
        
        # Финальный прогресс
        display_progress(total_order_items, TARGET_ORDER_ITEMS, start_time)
        print("\n")
        
        # Итоги
        total_time = time.time() - start_time
        logger.info(f"\n✅ ГЕНЕРАЦИЯ ЗАВЕРШЕНА!")
        logger.info(f"📊 ИТОГИ:")
        logger.info(f"   Создано заказов: {total_orders:,}")
        logger.info(f"   Создано позиций: {total_order_items:,}")
        logger.info(f"   Время выполнения: {total_time:.2f} сек")
        if total_time > 0:
            logger.info(f"   Скорость: {total_order_items/total_time:.1f} поз./сек")
        
        # ПРОВЕРКА КАЧЕСТВА
        if verify_data_quality(cursor):
            logger.info("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            logger.warning("⚠️ Обнаружены проблемы в данных")
        
        logger.info(f"📄 Файл отчета: {output_file}")
        
        # Финальная проверка SQL
        logger.info("\n🔎 ФИНАЛЬНАЯ ПРОВЕРКА ЧЕРЕЗ SQL:")
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM order_items WHERE fixed_price IS NULL) as null_prices,
                (SELECT COUNT(*) FROM orders WHERE order_cost = 0) as zero_cost_orders,
                (SELECT COUNT(*) FROM orders) as total_orders,
                (SELECT COUNT(*) FROM order_items) as total_items
        """)
        stats = cursor.fetchone()
        logger.info(f"   NULL fixed_price: {stats[0]}")
        logger.info(f"   Заказов с cost=0: {stats[1]}")
        logger.info(f"   Всего заказов: {stats[2]}")
        logger.info(f"   Всего позиций: {stats[3]}")
        
    except Exception as e:
        logger.error(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.execute("SET autocommit = 1")
            cursor.execute("SET unique_checks = 1")
            cursor.execute("SET foreign_key_checks = 1")
            cursor.close()
        if conn:
            conn.close()
            logger.info("🔌 Соединение с БД закрыто")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Генерация прервана пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Фатальная ошибка: {e}")
        sys.exit(1)