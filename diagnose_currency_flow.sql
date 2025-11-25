-- Script completo para diagnosticar el problema de moneda

-- ========================================
-- 1. VERIFICAR CONFIGURACIÓN BASE
-- ========================================

\echo '=== 1. Monedas Activas ==='
SELECT id, name, symbol, active
FROM res_currency
WHERE name IN ('USD', 'MXN')
ORDER BY name;

\echo ''
\echo '=== 2. Moneda de la Compañía ==='
SELECT
    c.id,
    c.name as company_name,
    c.currency_id,
    cur.name as currency_code,
    cur.symbol
FROM res_company c
JOIN res_currency cur ON c.currency_id = cur.id
WHERE c.id = 1;

\echo ''
\echo '=== 3. Listas de Precios ==='
SELECT
    pl.id,
    pl.name as pricelist_name,
    pl.currency_id,
    cur.name as currency_code,
    pl.active
FROM product_pricelist pl
JOIN res_currency cur ON pl.currency_id = cur.id
WHERE pl.active = true
ORDER BY pl.id;

-- ========================================
-- 2. VERIFICAR ORDEN S00037
-- ========================================

\echo ''
\echo '=== 4. Orden de Venta S00037 ==='
SELECT
    so.id,
    so.name,
    so.state,
    so.currency_id,
    cur.name as currency_code,
    so.amount_total,
    so.pricelist_id,
    pl.name as pricelist_name
FROM sale_order so
JOIN res_currency cur ON so.currency_id = cur.id
LEFT JOIN product_pricelist pl ON so.pricelist_id = pl.id
WHERE so.name LIKE 'S00037%'
ORDER BY so.create_date DESC;

-- ========================================
-- 3. VERIFICAR TRANSACCIONES DE PAGO
-- ========================================

\echo ''
\echo '=== 5. Payment Transactions para S00037 ==='
SELECT
    pt.id,
    pt.reference,
    pt.state,
    pt.currency_id,
    cur.name as currency_code,
    pt.amount,
    pt.sale_order_ids,
    pt.create_date
FROM payment_transaction pt
JOIN res_currency cur ON pt.currency_id = cur.id
WHERE pt.reference LIKE 'S00037%'
ORDER BY pt.create_date DESC;

-- ========================================
-- 4. VERIFICAR PAYMENT PROVIDER (STRIPE)
-- ========================================

\echo ''
\echo '=== 6. Payment Provider Stripe ==='
SELECT
    pp.id,
    pp.name,
    pp.code,
    pp.state,
    pp.company_id,
    c.name as company_name
FROM payment_provider pp
LEFT JOIN res_company c ON pp.company_id = c.id
WHERE pp.code = 'stripe';

-- ========================================
-- 5. DIAGNÓSTICO: ¿DÓNDE ESTÁ EL PROBLEMA?
-- ========================================

\echo ''
\echo '=== 7. DIAGNÓSTICO ==='
\echo 'Verificando discrepancias...'

WITH diagnosis AS (
    SELECT
        'Company Currency' as item,
        cur.name as current_value,
        CASE WHEN cur.name = 'MXN' THEN 'OK' ELSE 'PROBLEMA: Debería ser MXN' END as status
    FROM res_company c
    JOIN res_currency cur ON c.currency_id = cur.id
    WHERE c.id = 1

    UNION ALL

    SELECT
        'Pricelist Currency' as item,
        cur.name as current_value,
        CASE WHEN cur.name = 'MXN' THEN 'OK' ELSE 'PROBLEMA: Debería ser MXN' END as status
    FROM product_pricelist pl
    JOIN res_currency cur ON pl.currency_id = cur.id
    WHERE pl.id = 1

    UNION ALL

    SELECT
        'Sale Order S00037 Currency' as item,
        COALESCE(cur.name, 'NO ENCONTRADA') as current_value,
        CASE
            WHEN cur.name = 'MXN' THEN 'OK'
            WHEN cur.name IS NULL THEN 'PROBLEMA: Orden no encontrada'
            ELSE 'PROBLEMA: Debería ser MXN'
        END as status
    FROM sale_order so
    LEFT JOIN res_currency cur ON so.currency_id = cur.id
    WHERE so.name = 'S00037'

    UNION ALL

    SELECT
        'Payment Transaction Currency' as item,
        COALESCE(cur.name, 'NO ENCONTRADA') as current_value,
        CASE
            WHEN cur.name = 'MXN' THEN 'OK'
            WHEN cur.name IS NULL THEN 'INFO: No hay transacción activa'
            ELSE 'PROBLEMA: Debería ser MXN'
        END as status
    FROM payment_transaction pt
    LEFT JOIN res_currency cur ON pt.currency_id = cur.id
    WHERE pt.reference LIKE 'S00037%'
    ORDER BY pt.create_date DESC
    LIMIT 1
)
SELECT * FROM diagnosis;

-- ========================================
-- 6. PRODUCTOS DE LA ORDEN
-- ========================================

\echo ''
\echo '=== 8. Productos en la Orden S00037 ==='
SELECT
    sol.id,
    p.name as product_name,
    sol.product_uom_qty as quantity,
    sol.price_unit,
    sol.price_subtotal,
    sol.currency_id,
    cur.name as currency_code
FROM sale_order_line sol
JOIN sale_order so ON sol.order_id = so.id
JOIN product_product pp ON sol.product_id = pp.id
JOIN product_template p ON pp.product_tmpl_id = p.id
LEFT JOIN res_currency cur ON sol.currency_id = cur.id
WHERE so.name = 'S00037'
ORDER BY sol.id;
