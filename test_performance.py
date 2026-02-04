import mysql.connector
import time
import random

db = mysql.connector.connect(
    host="127.0.0.1",
    port=3307,
    user="root",
    password="Infinitum97",
    database="mydb"
)

cursor = db.cursor()

# Получаем диапазоны ID для случайной выборки
cursor.execute("SELECT MIN(customer_id), MAX(customer_id) FROM customers")
min_cust, max_cust = cursor.fetchone()

cursor.execute("SELECT MIN(product_id), MAX(product_id) FROM products")  
min_prod, max_prod = cursor.fetchone()

cursor.execute("SELECT MIN(order_id), MAX(order_id) FROM orders")
min_ord, max_ord = cursor.fetchone()

print("Начинаем тест 100,000 случайных запросов на чтение из всех таблиц...")
start_time = time.time()

for i in range(100000):
    query_type = i % 6  # 6 разных типов запросов
    
    if query_type == 0:
        # Случайный customer
        cust_id = random.randint(min_cust, max_cust)
        cursor.execute(f"SELECT * FROM customers WHERE customer_id = {cust_id}")
    
    elif query_type == 1:
        # Случайный product
        prod_id = random.randint(min_prod, max_prod)
        cursor.execute(f"SELECT * FROM products WHERE product_id = {prod_id}")
    
    elif query_type == 2:
        # Случайный order
        ord_id = random.randint(min_ord, max_ord)
        cursor.execute(f"SELECT * FROM orders WHERE order_id = {ord_id}")
    
    elif query_type == 3:
        # JOIN: order + customer
        ord_id = random.randint(min_ord, max_ord)
        cursor.execute(f"""
            SELECT o.*, c.customer_name 
            FROM orders o 
            JOIN customers c ON o.customer_id = c.customer_id 
            WHERE o.order_id = {ord_id}
        """)
    
    elif query_type == 4:
        # JOIN: order_items + product
        prod_id = random.randint(min_prod, max_prod)
        cursor.execute(f"""
            SELECT oi.*, p.product_name 
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE oi.product_id = {prod_id}
        """)
    
    else:
        # Агрегация по product
        prod_id = random.randint(min_prod, max_prod)
        cursor.execute(f"""
            SELECT p.product_name, COUNT(oi.order_item_id) as order_count
            FROM products p
            LEFT JOIN order_items oi ON p.product_id = oi.product_id
            WHERE p.product_id = {prod_id}
            GROUP BY p.product_id
        """)
    
    cursor.fetchall()  # Забираем результат

total_time = time.time() - start_time

print(f"\nРезультаты:")
print(f"Общее время: {total_time:.2f} секунд")
print(f"Среднее время на запрос: {(total_time * 1000) / 100000:.3f} мс")
print(f"Запросов в секунду: {100000 / total_time:.2f}")

cursor.close()
db.close()