start transaction;

drop table if exists users;
drop table if exists reports;
drop table if exists sales;
drop table if exists product;
drop procedure if exists SellProduct;
drop procedure if exists AddReport;

create table if not exists product
(
    prod_id       int             not null
        primary key,
    prod_name     varchar(240)    null,
    prod_measure  varchar(240)    null,
    prod_category int             null,
    prod_price    float           null,
    prod_max      int default 100 not null
);

create table if not exists users
(
    user_id  int auto_increment
        primary key,
    login    varchar(50)  not null,
    password varchar(255) not null,
    role     varchar(20)  not null,
    constraint login
        unique (login)
);

CREATE TABLE IF NOT EXISTS sales
(
    sale_id   INT AUTO_INCREMENT
        PRIMARY KEY,
    prod_id   INT            NOT NULL,
    prod_name VARCHAR(240)   NOT NULL,
    amount    INT            NOT NULL,
    date      DATE           NOT NULL,

    CONSTRAINT fk_sales_product
        FOREIGN KEY (prod_id) REFERENCES product (prod_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS reports
(
    report_id    INT AUTO_INCREMENT
        PRIMARY KEY,
    report_month INT            NOT NULL,
    report_year  INT            NOT NULL,
    product_id   INT            NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,

    CONSTRAINT fk_reports_product
        FOREIGN KEY (product_id) REFERENCES product (prod_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    CONSTRAINT uq_reports_period_product
        UNIQUE (report_year, report_month, product_id)
);

DELIMITER //

DROP PROCEDURE IF EXISTS AddReport;

CREATE PROCEDURE AddReport(
    IN p_report_YEAR INT,
    IN p_report_MONTH INT
)
BEGIN
    DECLARE report_prod_id INT;
    DECLARE report_sum DECIMAL(10,2);
    DECLARE cursor_year INT;
    DECLARE cursor_month INT;
    DECLARE done INT DEFAULT 0;

    DECLARE sum_cursor CURSOR FOR
        SELECT
            prod_id,
            SUM(amount),
            YEAR(date),
            MONTH(date)
        FROM sales
        WHERE YEAR(date) = p_report_YEAR AND MONTH(date) = p_report_MONTH
        GROUP BY prod_id, YEAR(date), MONTH(date);

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    START TRANSACTION;

    OPEN sum_cursor;

    read_loop: LOOP
        FETCH sum_cursor INTO report_prod_id, report_sum, cursor_year, cursor_month;
        IF done THEN
            LEAVE read_loop;
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM reports
            WHERE report_month = cursor_month AND report_year = cursor_year AND product_id = report_prod_id
        ) THEN
            INSERT INTO reports (report_month, report_year, total_amount, product_id)
            VALUES (cursor_month, cursor_year, report_sum, report_prod_id);
        ELSE
            SELECT CONCAT('Предупреждение: запись для ', cursor_month, '/', cursor_year, ' уже существует') AS warning_message;
        END IF;
    END LOOP;

    CLOSE sum_cursor;

    COMMIT;
END//

DELIMITER ;

DELIMITER //

DROP PROCEDURE IF EXISTS SellProduct;
CREATE PROCEDURE SellProduct(
    IN p_prod_id INT,
    IN p_amount INT,
    out p_report VARCHAR(10000)
)
proc_block: BEGIN
    DECLARE prod_name_val VARCHAR(255);
    DECLARE prod_max_val INT;
    DECLARE msg TEXT DEFAULT NULL;

    -- Проверка входных параметров
    IF p_amount <= 0 THEN
        SET msg = CONCAT('Ошибка: количество должно быть больше 0');
        LEAVE proc_block;
    END IF;

    START TRANSACTION;

    -- Получаем текущее значение на складе
    SELECT prod_name, prod_max
    INTO prod_name_val, prod_max_val
    FROM product
    WHERE prod_id = p_prod_id
    FOR UPDATE;

    IF prod_max_val IS NULL THEN
        SET msg = CONCAT('Ошибка: товар с prod_id=', p_prod_id, ' не найден');
        LEAVE proc_block;
    END IF;

    -- Проверяем наличие
    IF p_amount > prod_max_val THEN
        SET msg = CONCAT('Ошибка: на складе только ', prod_max_val, ' шт. товара ', prod_name_val);
        LEAVE proc_block;
    END IF;

    -- Списываем со склада
    UPDATE product
    SET prod_max = prod_max - p_amount
    WHERE prod_id = p_prod_id;

    -- Добавляем запись в sales
    INSERT INTO sales(prod_id, amount, prod_name, date)
    VALUES (p_prod_id, p_amount, prod_name_val, CURDATE());

    COMMIT;

    SET p_report = msg;

END proc_block//

DELIMITER ;

INSERT INTO supermarket.users (login, password, role) VALUES ('admin', '1', 'admin');
INSERT INTO supermarket.users (login, password, role) VALUES ('user', '1', 'user');

commit;