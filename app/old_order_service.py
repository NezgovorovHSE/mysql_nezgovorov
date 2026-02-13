import logging
import time  # Добавь в начало файла, рядом с другими импортами
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import event
from .database import engine, SessionLocal, Base
from .models import Order, OrderItem, Product, Customer

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_order_after_insert(session: Session, order: Order):
    """Обработчик после создания заказа (аналог триггера)"""
    try:
        logger.info(f"Обработка заказа #{order.order_id}")
        
        # 1. Получаем все позиции заказа ИЗ БАЗЫ ДАННЫХ
        order_items = session.query(OrderItem).filter_by(order_id=order.order_id).all()
        
        logger.info(f"Найдено позиций: {len(order_items)}")
        
        if not order_items:
            logger.warning(f"Заказ #{order.order_id} без позиций")
            return
        
        total_cost = 0
        
        # 2. Обрабатываем каждую позицию
        for item in order_items:
            # Загружаем товар с блокировкой
            product = session.query(Product).filter(
                Product.product_id == item.product_id
            ).with_for_update().first()
            
            if not product:
                raise ValueError(f"Товар #{item.product_id} не найден")
            
            # 3. Проверяем наличие на складе
            if product.stock_status < item.product_quantity:
                raise ValueError(
                    f"Недостаточно товара #{product.product_id}. "
                    f"На складе: {product.stock_status}, требуется: {item.product_quantity}"
                )
            
            # 4. Фиксируем цену
            if item.fixed_price is None:
                item.fixed_price = product.selling_price
                logger.info(f"Зафиксирована цена {item.fixed_price} для товара #{product.product_id}")
            
            # 5. Рассчитываем стоимость позиции
            item_cost = item.product_quantity * item.fixed_price
            total_cost += item_cost
            
            # 6. Уменьшаем количество на складе
            product.stock_status -= item.product_quantity
            logger.info(f"Списано {item.product_quantity} шт. товара #{product.product_id}")
        
        # 7. Применяем скидку
        discount_percent = float(order.discount) if order.discount else 0.0
        if discount_percent < 0 or discount_percent > 100:
            raise ValueError(f"Некорректная скидка: {discount_percent}%")
        
        final_cost = int(total_cost * (1 - discount_percent / 100))
        order.order_cost = final_cost
        
        # 8. Обновляем дату и время (если не установлены)
        if not order.order_date:
            order.order_date = datetime.now().date()
        if not order.order_time:
            order.order_time = datetime.now().time()
        
        logger.info(f"Заказ #{order.order_id} обработан. Итог: {final_cost} руб.")
        
        # 9. Обновляем объект order в сессии
        session.add(order)
        
    except Exception as e:
        logger.error(f"Ошибка обработки заказа #{order.order_id}: {str(e)}")
        session.rollback()
        raise

def create_order_with_items(customer_id: int, items_data: list, discount: float = 0.0):
    """Создание заказа с позициями"""
    db = SessionLocal()
    try:
        # Создаем заказ
        order = Order(
            customer_id=customer_id,
            discount=discount,
            order_cost=0
        )
        db.add(order)
        db.flush()  # Получаем order_id
        
        # Добавляем позиции
        for item_data in items_data:
            order_item = OrderItem(
                order_id=order.order_id,
                product_id=item_data['product_id'],
                product_quantity=item_data['quantity']
            )
            db.add(order_item)
        
        # ФЛАШИМ ПОЗИЦИИ, чтобы они сохранились в БД
        db.flush()
        
        # ВЫЗЫВАЕМ ТРИГГЕР
        process_order_after_insert(db, order)
        
        db.commit()
        logger.info(f"Заказ #{order.order_id} успешно создан")
        return order
        
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка создания заказа: {str(e)}")
        raise
    finally:
        db.close()

def init_database():
    """Инициализация базы данных"""
    Base.metadata.create_all(bind=engine)
    logger.info("База данных инициализирована")

from sqlalchemy import inspect, text

def check_database_ready():
    """Проверяем, готова ли БД: существует ли таблица orders"""
    try:
        with engine.connect() as conn:
            # Простая проверка существования таблицы orders
            result = conn.execute(
                text("SHOW TABLES LIKE 'orders'")
            ).fetchone()
            return result is not None
    except Exception:
        return False

def wait_for_database(max_retries=30, delay=2):
    """Ожидание готовности БД"""
    logger.info("Ожидание готовности базы данных...")
    for i in range(max_retries):
        if check_database_ready():
            logger.info("База данных готова")
            return True
        logger.warning(f"Попытка {i+1}/{max_retries}...")
        time.sleep(delay)
    logger.error("База данных не готова после всех попыток")
    return False

if __name__ == "__main__":
    import time
    
    if wait_for_database():
        example_usage()
    else:
        logger.error("Не удалось подключиться к БД. Проверьте контейнер MySQL.")
