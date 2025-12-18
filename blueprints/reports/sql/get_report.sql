SELECT
    r.product_id,
    p.prod_name,
    r.total_amount,
    r.report_month,
    r.report_year
FROM
    reports r
    INNER JOIN product p ON r.product_id = p.prod_id
WHERE
    r.report_year = %s
    AND r.report_month = %s
ORDER BY
    r.total_amount DESC;

