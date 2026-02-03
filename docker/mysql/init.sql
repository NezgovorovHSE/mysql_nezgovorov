CREATE DATABASE IF NOT EXISTS mydb;
USE mydb;
-- Устанавливаем настройки
SET FOREIGN_KEY_CHECKS=0;
SET NAMES utf8mb4;

-- Table category
CREATE TABLE IF NOT EXISTS `category` (
  `category_id` int NOT NULL AUTO_INCREMENT,
  `product_category` varchar(30) DEFAULT 'Другое',
  PRIMARY KEY (`category_id`)
) ENGINE=InnoDB;

-- Table customers
CREATE TABLE IF NOT EXISTS `customers` (
  `customer_id` int NOT NULL AUTO_INCREMENT,
  `customer_name` varchar(45) NOT NULL,
  `customer_address` varchar(1000) NOT NULL,
  `customer_phone_number` char(11) NOT NULL,
  `customer_email` varchar(45) NOT NULL,
  PRIMARY KEY (`customer_id`),
  UNIQUE KEY `емэйл_заказчика_UNIQUE` (`customer_email`),
  UNIQUE KEY `телефонный_номер_заказчика_UNIQUE` (`customer_phone_number`)
) ENGINE=InnoDB;

-- Table suppliers
CREATE TABLE IF NOT EXISTS `suppliers` (
  `supplier_id` int NOT NULL AUTO_INCREMENT,
  `supplier_name` varchar(45) NOT NULL,
  `current_account` char(20) NOT NULL,
  `supplier_phone_number` char(7) NOT NULL DEFAULT '',
  `supplier_email` varchar(45) NOT NULL,
  PRIMARY KEY (`supplier_id`),
  UNIQUE KEY `расчетный_счет_UNIQUE` (`current_account`),
  UNIQUE KEY `емэйл_UNIQUE` (`supplier_email`),
  UNIQUE KEY `поставщик_UNIQUE` (`supplier_name`)
) ENGINE=InnoDB;

-- Table products
CREATE TABLE IF NOT EXISTS `products` (
  `product_id` int NOT NULL AUTO_INCREMENT,
  `product_name` varchar(45) NOT NULL,
  `category_id` int DEFAULT NULL,
  `purchase_price` smallint unsigned NOT NULL,
  `selling_price` smallint unsigned NOT NULL DEFAULT 0,
  `stock_status` smallint unsigned NOT NULL DEFAULT 0,
  `supplier` int DEFAULT NULL,
  PRIMARY KEY (`product_id`),
  KEY `supplier_id_idx` (`supplier`),
  KEY `category_id_idx` (`category_id`),
  CONSTRAINT `fk_products_category` FOREIGN KEY (`category_id`) REFERENCES `category` (`category_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_products_supplier` FOREIGN KEY (`supplier`) REFERENCES `suppliers` (`supplier_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Table orders
CREATE TABLE IF NOT EXISTS `orders` (
  `order_id` int NOT NULL AUTO_INCREMENT,
  `discount` decimal(4,2) NOT NULL DEFAULT '0.00',
  `order_cost` mediumint unsigned NOT NULL,
  `order_date` date NOT NULL,
  `order_time` time NOT NULL,
  `customer_id` int NOT NULL,
  PRIMARY KEY (`order_id`),
  KEY `idx_orders_customer` (`customer_id`),
  KEY `idx_orders_date` (`order_date`),
  CONSTRAINT `fk_orders_customers` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`customer_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_discount_range` CHECK (((`discount` >= 0) and (`discount` <= 100)))
) ENGINE=InnoDB;

-- Table order_items
CREATE TABLE IF NOT EXISTS `order_items` (
  `order_item_id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `product_id` int NOT NULL,
  `product_quantity` tinyint unsigned NOT NULL DEFAULT '1',
  `fixed_price` smallint unsigned DEFAULT NULL,
  PRIMARY KEY (`order_item_id`),
  KEY `fk_order_items_order_idx` (`order_id`),
  KEY `fk_order_items_product_idx` (`product_id`),
  CONSTRAINT `fk_order_items_order` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_order_items_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

SET FOREIGN_KEY_CHECKS=1;

-- Тестовые данные
INSERT IGNORE INTO `category` (`product_category`) VALUES 
  ('Электроника'),
  ('Одежда'),
  ('Книги'),
  ('Другое');

INSERT IGNORE INTO `customers` (`customer_name`, `customer_address`, `customer_phone_number`, `customer_email`) VALUES
  ('Тестовый Клиент', 'ул. Примерная, д.1', '79991234567', 'test@example.com');

SELECT 'Database initialized successfully' as status;