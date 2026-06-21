-- =============================================================
-- PrakrikaP — MySQL schema
-- Выполни этот скрипт один раз в своей MySQL-базе:
--   mysql -u <user> -p <database_name> < schema.sql
-- =============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- categories
-- ----------------------------
CREATE TABLE IF NOT EXISTS `categories` (
    `id`   INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(255) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_categories_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- suppliers
-- ----------------------------
CREATE TABLE IF NOT EXISTS `suppliers` (
    `id`      INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name`    VARCHAR(255) NOT NULL,
    `contact` VARCHAR(255) DEFAULT NULL,
    `phone`   VARCHAR(50)  DEFAULT NULL,
    `address` VARCHAR(500) DEFAULT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- clients
-- ----------------------------
CREATE TABLE IF NOT EXISTS `clients` (
    `id`      INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name`    VARCHAR(255) NOT NULL,
    `contact` VARCHAR(255) DEFAULT NULL,
    `phone`   VARCHAR(50)  DEFAULT NULL,
    `address` VARCHAR(500) DEFAULT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- products
-- ----------------------------
CREATE TABLE IF NOT EXISTS `products` (
    `id`          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name`        VARCHAR(255) NOT NULL,
    `sku`         VARCHAR(100) DEFAULT NULL,
    `price`       DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    `stock`       INT NOT NULL DEFAULT 0,
    `category_id` INT UNSIGNED DEFAULT NULL,
    `supplier_id` INT UNSIGNED DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `fk_products_category` (`category_id`),
    KEY `fk_products_supplier` (`supplier_id`),
    CONSTRAINT `fk_products_category` FOREIGN KEY (`category_id`)
        REFERENCES `categories` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT `fk_products_supplier` FOREIGN KEY (`supplier_id`)
        REFERENCES `suppliers` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- orders
-- ----------------------------
CREATE TABLE IF NOT EXISTS `orders` (
    `id`        INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `client_id` INT UNSIGNED DEFAULT NULL,
    `date`      DATE DEFAULT NULL,
    `status`    VARCHAR(50) NOT NULL DEFAULT 'новый',
    `total`     DECIMAL(14,2) NOT NULL DEFAULT 0.00,
    PRIMARY KEY (`id`),
    KEY `fk_orders_client` (`client_id`),
    CONSTRAINT `fk_orders_client` FOREIGN KEY (`client_id`)
        REFERENCES `clients` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- order_items
-- ----------------------------
CREATE TABLE IF NOT EXISTS `order_items` (
    `id`         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `order_id`   INT UNSIGNED NOT NULL,
    `product_id` INT UNSIGNED DEFAULT NULL,
    `qty`        INT NOT NULL DEFAULT 1,
    `price`      DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    PRIMARY KEY (`id`),
    KEY `fk_items_order`   (`order_id`),
    KEY `fk_items_product` (`product_id`),
    CONSTRAINT `fk_items_order` FOREIGN KEY (`order_id`)
        REFERENCES `orders` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_items_product` FOREIGN KEY (`product_id`)
        REFERENCES `products` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;
