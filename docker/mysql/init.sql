CREATE DATABASE IF NOT EXISTS mydb;
USE mydb;

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

-- Триггер для обработки заказа
DELIMITER //

CREATE TRIGGER process_order_trigger
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    DECLARE order_discount DECIMAL(4,2);
    DECLARE total_cost MEDIUMINT UNSIGNED DEFAULT 0;
    DECLARE product_count INT;
    DECLARE done BOOLEAN DEFAULT FALSE;
    
    DECLARE cur_products CURSOR FOR
        SELECT 
            p.product_id,
            p.stock_status,
            p.selling_price,
            oi.product_quantity,
            oi.fixed_price
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        WHERE oi.order_id = NEW.order_id
        FOR UPDATE;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    -- Блокируем заказ и все связанные товары
    SELECT discount INTO order_discount
    FROM orders 
    WHERE order_id = NEW.order_id
    FOR UPDATE;
    
    -- Проверяем корректность скидки
    IF order_discount < 0 OR order_discount > 100 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = CONCAT('Некорректная скидка: ', order_discount, '%');
    END IF;
    
    OPEN cur_products;
    
    product_loop: LOOP
        FETCH cur_products INTO 
            @product_id, 
            @stock_status, 
            @selling_price, 
            @product_quantity,
            @fixed_price;
        
        IF done THEN
            LEAVE product_loop;
        END IF;
        
        -- Проверяем наличие товара
        IF @stock_status < @product_quantity THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = CONCAT(
                'Недостаточно товара #', @product_id, 
                '. На складе: ', @stock_status, 
                ', требуется: ', @product_quantity
            );
        END IF;
        
        -- Фиксируем цену, если не указана
        IF @fixed_price IS NULL THEN
            UPDATE order_items 
            SET fixed_price = @selling_price
            WHERE order_id = NEW.order_id 
            AND product_id = @product_id;
            SET @fixed_price = @selling_price;
        END IF;
        
        -- Списание товара со склада
        UPDATE products 
        SET stock_status = stock_status - @product_quantity
        WHERE product_id = @product_id;
        
        -- Суммируем стоимость
        SET total_cost = total_cost + (@product_quantity * @fixed_price);
    END LOOP;
    
    CLOSE cur_products;
    
    -- Применяем скидку
    SET total_cost = total_cost * (1 - order_discount / 100);
    
    -- Обновляем заказ
    UPDATE orders 
    SET 
        order_cost = total_cost,
        order_date = IF(order_date = '0000-00-00', CURDATE(), order_date),
        order_time = IF(order_time = '00:00:00', CURTIME(), order_time)
    WHERE order_id = NEW.order_id;
END //

DELIMITER ;

SELECT 'Database initialized successfully' as status;
