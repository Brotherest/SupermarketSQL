SELECT
    p.prod_id,
    p.prod_name,
    p.prod_category,
    p.prod_measure,
    p.prod_price,
    p.prod_max
FROM product p
WHERE p.prod_category = %s
ORDER BY p.prod_name ASC;
