from sqlalchemy import Column, Integer, String, DECIMAL, Date, Time, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import SessionLocal
from .database import Base

class Customer(Base):
    __tablename__ = 'customers'
    
    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_name = Column(String(45), nullable=False)
    customer_address = Column(String(1000), nullable=False)
    customer_phone_number = Column(String(11), nullable=False, unique=True)
    customer_email = Column(String(45), nullable=False, unique=True)
    
    orders = relationship("Order", back_populates="customer")

class Product(Base):
    __tablename__ = 'products'
    
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(45), nullable=False)
    category_id = Column(Integer, ForeignKey('category.category_id'))
    purchase_price = Column(Integer, nullable=False)
    selling_price = Column(Integer, nullable=False, default=0)
    stock_status = Column(Integer, nullable=False, default=0)
    supplier = Column(Integer, ForeignKey('suppliers.supplier_id'))

class Category(Base):
    __tablename__ = 'category'
    
    category_id = Column(Integer, primary_key=True, autoincrement=True)
    product_category = Column(String(30), default='Другое')

class Supplier(Base):
    __tablename__ = 'suppliers'
    
    supplier_id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_name = Column(String(45), nullable=False, unique=True)
    current_account = Column(String(20), nullable=False, unique=True)
    supplier_phone_number = Column(String(7), nullable=False, default='')
    supplier_email = Column(String(45), nullable=False, unique=True)

class Order(Base):
    __tablename__ = 'orders'
    
    order_id = Column(Integer, primary_key=True, autoincrement=True)
    discount = Column(DECIMAL(4,2), nullable=False, default=0.00)
    order_cost = Column(Integer, nullable=False)
    order_date = Column(Date, nullable=False, default=func.current_date())
    order_time = Column(Time, nullable=False, default=func.current_time())
    customer_id = Column(
        Integer, 
        ForeignKey('customers.customer_id', ondelete='RESTRICT'), 
        nullable=False
    )
    
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = 'order_items'
    
    order_item_id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(
        Integer, 
        ForeignKey('orders.order_id', ondelete='CASCADE'), 
        nullable=False
    )
    product_id = Column(
        Integer, 
        ForeignKey('products.product_id', ondelete='RESTRICT'), 
        nullable=False
    )
    product_quantity = Column(Integer, nullable=False, default=1)
    fixed_price = Column(Integer, nullable=True)  # Будет заполняться триггером
    
    product = relationship("Product")


# Добавь после всех определений классов:
