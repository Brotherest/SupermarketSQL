SELECT report_id, supply_date, total_amount
FROM reports
WHERE YEAR(supply_date) = %s AND MONTH(supply_date) = %s
ORDER BY supply_date DESC;