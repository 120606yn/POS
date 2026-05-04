SET NAMES utf8mb4;
SET GLOBAL time_zone = '+07:00';
SET time_zone = '+07:00';

CREATE DATABASE IF NOT EXISTS restaurant
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE restaurant;

CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(50) DEFAULT '🍽️',
    display_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE menu_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    image_url VARCHAR(500),
    is_available TINYINT(1) DEFAULT 1,
    display_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

CREATE TABLE tables (
    id INT AUTO_INCREMENT PRIMARY KEY,
    table_number VARCHAR(20) NOT NULL UNIQUE,
    capacity INT DEFAULT 4,
    status ENUM('available', 'occupied', 'reserved') DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE staff (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    role ENUM('admin', 'waiter', 'kitchen') NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    table_id INT,
    staff_id INT,
    status ENUM('pending', 'cooking', 'ready', 'paid', 'cancelled') DEFAULT 'pending',
    notes TEXT,
    total_amount DECIMAL(10,2) DEFAULT 0,
    payment_method ENUM('cash', 'card', 'transfer') NULL,
    paid_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (table_id) REFERENCES tables(id) ON DELETE SET NULL,
    FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE SET NULL
);

CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    menu_item_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (menu_item_id) REFERENCES menu_items(id) ON DELETE CASCADE
);

INSERT INTO categories (name, icon, display_order) VALUES
('Khai vị', '🥗', 1),
('Món chính', '🍖', 2),
('Cơm & Mì', '🍜', 3),
('Lẩu & Nướng', '🔥', 4),
('Tráng miệng', '🍮', 5),
('Đồ uống', '🥤', 6);

INSERT INTO menu_items (category_id, name, description, price, is_available, display_order) VALUES
(1, 'Gỏi cuốn tôm thịt', 'Gỏi cuốn tươi với tôm, thịt heo, rau sống và bún', 45000, 1, 1),
(1, 'Chả giò chiên', 'Chả giò giòn rụm nhân thịt heo và rau củ', 55000, 1, 2),
(1, 'Súp cua thịt cua', 'Súp cua béo ngậy, thơm ngon', 65000, 1, 3),
 
(2, 'Sườn nướng mật ong', 'Sườn heo nướng sốt mật ong thơm lừng', 120000, 1, 1),
(2, 'Gà nướng muối ớt', 'Gà nướng với muối ớt đặc biệt', 150000, 1, 2),
(2, 'Cá lóc hấp bầu', 'Cá lóc tươi hấp với bầu non', 180000, 1, 3),
(2, 'Bò lúc lắc', 'Thịt bò xào lúc lắc với tiêu xanh', 165000, 1, 4),
 
(3, 'Cơm tấm sườn bì chả', 'Cơm tấm đặc biệt với sườn, bì, chả', 75000, 1, 1),
(3, 'Bún bò Huế', 'Bún bò cay đặc trưng miền Trung', 65000, 1, 2),
(3, 'Phở bò tái nạm', 'Phở bò truyền thống với nước dùng đậm đà', 70000, 1, 3),
(3, 'Mì xào hải sản', 'Mì xào giòn với hải sản tươi', 95000, 1, 4),
 
(4, 'Lẩu thái hải sản', 'Lẩu thái chua cay với hải sản tươi sống', 350000, 1, 1),
(4, 'Lẩu bò nhúng dấm', 'Lẩu bò chua ngọt đặc trưng', 320000, 1, 2),
(4, 'Nướng BBQ combo 2', 'Combo nướng BBQ cho 2 người', 280000, 1, 3),
 
(5, 'Chè ba màu', 'Chè ba màu mát lạnh truyền thống', 35000, 1, 1),
(5, 'Bánh flan caramel', 'Bánh flan mềm mịn với caramel', 40000, 1, 2),
(5, 'Kem dừa', 'Kem dừa tươi mát', 45000, 1, 3),
 
(6, 'Nước dừa tươi', 'Nước dừa tươi nguyên chất', 35000, 1, 1),
(6, 'Sinh tố xoài', 'Sinh tố xoài tươi béo ngậy', 45000, 1, 2),
(6, 'Trà đào cam sả', 'Trà đào thơm mát với cam và sả', 50000, 1, 3),
(6, 'Coca Cola', 'Coca Cola lon lạnh', 25000, 1, 4),
(6, 'Bia Tiger', 'Bia Tiger lon', 30000, 1, 5);

INSERT INTO tables (table_number, capacity) VALUES
('B01', 4), ('B02', 4), ('B03', 2), ('B04', 6),
('B05', 4), ('B06', 4), ('B07', 8), ('B08', 2),
('VIP1', 10), ('VIP2', 12);

INSERT INTO staff (username, password_hash, full_name, role) VALUES
('admin', 'scrypt:32768:8:1$oULGVE8qBFkiCB8i$ca7c178b43ad94a7c1543cd3115da9f0d739e3bec847a9e34220150740d381ff5e5f87280523a76936624e7c2db1df53545e3d766f5644d15daf86dd602433a6', 'Quản trị viên', 'admin'),
('waiter1', 'scrypt:32768:8:1$oULGVE8qBFkiCB8i$ca7c178b43ad94a7c1543cd3115da9f0d739e3bec847a9e34220150740d381ff5e5f87280523a76936624e7c2db1df53545e3d766f5644d15daf86dd602433a6', 'Nguyễn Văn An', 'waiter'),
('kitchen1', 'scrypt:32768:8:1$oULGVE8qBFkiCB8i$ca7c178b43ad94a7c1543cd3115da9f0d739e3bec847a9e34220150740d381ff5e5f87280523a76936624e7c2db1df53545e3d766f5644d15daf86dd602433a6', 'Trần Thị Bếp', 'kitchen');

ALTER TABLE categories CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE menu_items CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE orders CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE order_items CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE tables CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE staff CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;