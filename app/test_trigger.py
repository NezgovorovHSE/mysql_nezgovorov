import sys
import os

# Добавляем родительскую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Order, OrderItem, Product, Customer, Category, Supplier
from datetime import datetime

def test_trigger():
    """Тестирование автоматического триггера"""
    db = SessionLocal()  # Теперь SessionLocal определён
    ...
    
    try:
        print("=== Тест автоматического триггера ===")
        
        # 1. Создаём тестовые данные (если нет)
        # Категория
        category = db.query(Category).first()
        if not category:
            category = Category(product_category="Тестовая категория")
            db.add(category)
            db.flush()
        
        # Поставщик
        supplier = db.query(Supplier).first()
        if not supplier:
            supplier = Supplier(
                supplier_name="Тестовый поставщик",
                current_account="12345678901234567890",
                supplier_email="supplier@test.com"
            )
            db.add(supplier)
            db.flush()
        
        # Товар
        product = db.query(Product).filter_by(product_name="Тестовый товар").first()
        if not product:
            product = Product(
                product_name="Тестовый товар",
                category_id=category.category_id,
                purchase_price=1000,
                selling_price=1500,
                stock_status=10,  # 10 штук на складе
                supplier=supplier.supplier_id
            )
            db.add(product)
            db.flush()
        
        # Клиент
        customer = db.query(Customer).filter_by(customer_email="trigger_test@test.com").first()
        if not customer:
            customer = Customer(
                customer_name="Тестовый Клиент",
                customer_address="ул. Тестовая, 1",
                customer_phone_number="79990000001",
                customer_email="trigger_test@test.com"
            )
            db.add(customer)
            db.flush()
        
        db.commit()  # Сохраняем тестовые данные
        
        # 2. Создаём заказ (триггер сработает автоматически)
        print(f"Создаю заказ для клиента ID={customer.customer_id}...")
        
        # 2. Создаём заказ через create_order_with_items (вызовет триггер)
        from app.order_service import create_order_with_items

        order = create_order_with_items(
            customer_id=customer.customer_id,
            items_data=[{'product_id': product.product_id, 'quantity': 2}],
            discount=10.0
        )

        # 3. Проверяем результаты
        print(f"\nРезультаты:")
        print(f"ID заказа: {order.order_id}")
        print(f"Стоимость заказа: {order.order_cost}")
        print(f"Дата заказа: {order.order_date}")
        print(f"Время заказа: {order.order_time}")

        # НЕ используем старую сессию db — создаём новую для проверки
        check_db = SessionLocal()

        # Проверяем остаток товара
        check_product = check_db.query(Product).filter_by(product_id=product.product_id).first()
        print(f"Остаток товара на складе: {check_product.stock_status} (было 10)")

        # Проверяем позицию заказа
        order_item = check_db.query(OrderItem).filter_by(order_id=order.order_id).first()
        if order_item:
            print(f"Фиксированная цена в заказе: {order_item.fixed_price}")
        else:
            print("Позиция заказа не найдена")

        check_db.close()

        if order.order_cost > 0 and check_product.stock_status == 8:
            print("\n✅ Триггер сработал корректно!")
        else:
            print("\n❌ Проблема с триггером")
            
    except Exception as e:
        db.rollback()
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_trigger()