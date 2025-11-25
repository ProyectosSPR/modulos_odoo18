-- Script para verificar configuración de monedas

-- 1. Ver todas las monedas activas
SELECT id, name, symbol, active, position
FROM res_currency
WHERE active = true
ORDER BY id;

-- 2. Ver cuál es la moneda con ID 1 (la que está usando la transacción)
SELECT id, name, symbol
FROM res_currency
WHERE id = 1;

-- 3. Ver la moneda de la compañía principal
SELECT c.id, c.name, cur.name as currency_name, cur.symbol
FROM res_company c
JOIN res_currency cur ON c.currency_id = cur.id
ORDER BY c.id
LIMIT 1;

-- 4. Ver la moneda de la orden de venta S00037
SELECT so.name, so.state, cur.name as currency_name, cur.symbol, so.amount_total
FROM sale_order so
JOIN res_currency cur ON so.currency_id = cur.id
WHERE so.name = 'S00037';

-- 5. Ver las listas de precios y sus monedas
SELECT id, name, currency_id, (SELECT name FROM res_currency WHERE id = pricelist.currency_id) as currency_name
FROM product_pricelist pricelist
WHERE active = true;
