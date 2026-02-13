import mysql.connector
import time
import random
import uuid

db = mysql.connector.connect(
    host="127.0.0.1",
    port=3307,
    user="root",
    password="Infinitum97",
    database="mydb",
    autocommit=False
)

cursor = db.cursor()

print("Начинаем тест на 50,000 INSERT + 50,000 UPDATE операций...")
start_time = time.time()

insert_operations = 0
update_operations = 0

try:
    # 50,000 INSERT операций
    for i in range(50000):
        unique_id = str(uuid.uuid4()).replace('-', '')[:16]
        timestamp = int(time.time() * 1000) % 1000000
        
        table_choice = random.randint(1, 4)
        
        try:
            if table_choice == 1:  # customers
                phone = f'79{random.randint(100000000, 999999999)}'[:11]
                cursor.execute(f"""
                    INSERT INTO customers 
                    (customer_name, customer_address, customer_phone_number, customer_email) 
                    VALUES 
                    ('Cust_{unique_id}', 'Addr_{unique_id}', 
                     '{phone}', 'cust_{unique_id}_{timestamp}@t.com')
                """)
                insert_operations += 1
            
            elif table_choice == 2:  # suppliers
                account_num = f'ACC{random.randint(100000000, 999999999):011d}'[:20]
                phone = f'{random.randint(1000000, 9999999)}'[:7]
                cursor.execute(f"""
                    INSERT INTO suppliers 
                    (supplier_name, current_account, supplier_phone_number, supplier_email) 
                    VALUES 
                    ('Supp_{unique_id}', '{account_num}', 
                     '{phone}', 'supp_{unique_id}_{timestamp}@t.com')
                """)
                insert_operations += 1
            
            elif table_choice == 3:  # category
                category_name = f'Cat_{unique_id}_{timestamp % 10000}'[:30]
                cursor.execute(f"""
                    INSERT INTO category (product_category) 
                    VALUES ('{category_name}')
                """)
                insert_operations += 1
            
            elif table_choice == 4:  # products
                cursor.execute("SELECT supplier_id FROM suppliers ORDER BY RAND() LIMIT 1")
                supplier_row = cursor.fetchone()
                supplier_id = supplier_row[0] if supplier_row else 1
                
                cursor.execute("SELECT category_id FROM category ORDER BY RAND() LIMIT 1")
                category_row = cursor.fetchone()
                category_id = category_row[0] if category_row else 1
                
                product_name = f'Prod_{unique_id}_{timestamp % 10000}'[:45]
                cursor.execute(f"""
                    INSERT INTO products 
                    (product_name, category_id, purchase_price, selling_price, stock_status, supplier) 
                    VALUES 
                    ('{product_name}', {category_id}, 
                     {random.randint(100, 1000)}, {random.randint(150, 1200)}, 
                     {random.randint(0, 100)}, {supplier_id})
                """)
                insert_operations += 1
        
        except mysql.connector.errors.IntegrityError:
            continue
        
        if i % 1000 == 0 and i > 0:
            db.commit()
    
    db.commit()
    
    # 50,000 UPDATE операций
    cursor.execute("SELECT customer_id FROM customers ORDER BY customer_id LIMIT 1000")
    customer_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT product_id FROM products ORDER BY product_id LIMIT 1000")
    product_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT supplier_id FROM suppliers ORDER BY supplier_id LIMIT 1000")
    supplier_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT category_id FROM category ORDER BY category_id LIMIT 1000")
    category_ids = [row[0] for row in cursor.fetchall()]
    
    for i in range(50000):
        unique_suffix = str(uuid.uuid4())[:8]
        table_choice = random.randint(1, 4)
        
        try:
            if table_choice == 1 and customer_ids:
                cust_id = random.choice(customer_ids)
                cursor.execute(f"""
                    UPDATE customers 
                    SET customer_address = CONCAT(LEFT(customer_address, 900), '_u')
                    WHERE customer_id = {cust_id}
                    LIMIT 1
                """)
                update_operations += 1
            
            elif table_choice == 2 and product_ids:
                prod_id = random.choice(product_ids)
                cursor.execute(f"""
                    UPDATE products 
                    SET stock_status = {random.randint(0, 100)}
                    WHERE product_id = {prod_id}
                    LIMIT 1
                """)
                update_operations += 1
            
            elif table_choice == 3 and supplier_ids:
                supp_id = random.choice(supplier_ids)
                cursor.execute(f"""
                    UPDATE suppliers 
                    SET supplier_email = CONCAT('u_', RIGHT(supplier_email, 40))
                    WHERE supplier_id = {supp_id}
                    LIMIT 1
                """)
                update_operations += 1
            
            elif table_choice == 4 and category_ids:
                cat_id = random.choice(category_ids)
                cursor.execute(f"""
                    UPDATE category 
                    SET product_category = CONCAT(LEFT(product_category, 25), '_u')
                    WHERE category_id = {cat_id}
                    LIMIT 1
                """)
                update_operations += 1
        
        except Exception:
            continue
        
        if i % 1000 == 0 and i > 0:
            db.commit()
    
    db.commit()
    
except Exception as e:
    db.rollback()
    print(f"Ошибка: {e}")
    raise

total_time = time.time() - start_time
total_operations = insert_operations + update_operations

print("\nРезультаты теста:")
print(f"Общее время: {total_time:.2f} секунд")
print(f"Всего успешных операций: {total_operations}")
print(f"Среднее время на операцию: {(total_time * 1000) / total_operations:.3f} мс")
print(f"Операций в секунду: {total_operations / total_time:.2f}")

cursor.close()
db.close()
