-- Script para verificar e instalar el módulo saas_subscription_payment_auto_start

-- 1. Verificar si el módulo existe en la base de datos
SELECT name, state, latest_version
FROM ir_module_module
WHERE name = 'saas_subscription_payment_auto_start';

-- 2. Si no aparece arriba, primero necesitas actualizar la lista de aplicaciones
-- Desde Odoo: Apps → Update Apps List

-- 3. Luego ejecuta esto para instalarlo (si ya está en la lista):
-- UPDATE ir_module_module
-- SET state = 'to install'
-- WHERE name = 'saas_subscription_payment_auto_start';

-- 4. Después reinicia Odoo para que se instale
