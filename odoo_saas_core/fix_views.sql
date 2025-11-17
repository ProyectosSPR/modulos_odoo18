-- Script SQL para limpiar y regenerar vistas de odoo_saas_core
-- ADVERTENCIA: Solo ejecutar si tienes problemas con las vistas

-- 1. Eliminar vistas antiguas/incorrectas
DELETE FROM ir_ui_view WHERE model IN ('saas.customer', 'saas.instance', 'saas.service.package')
  AND name NOT IN (
    'saas.customer.form',
    'saas.customer.tree',
    'saas.customer.kanban',
    'saas.customer.search',
    'saas.instance.form',
    'saas.instance.list',
    'saas.instance.kanban',
    'saas.instance.search',
    'saas.service.package.form',
    'saas.service.package.tree',
    'saas.service.package.kanban',
    'saas.service.package.search',
    'saas.customer.form.license',  -- odoo_saas_licensing
    'subscription.package.form.saas',  -- odoo_subscription
    'sale.order.form.saas',  -- sale_order extension
    'product.template.form.saas'  -- product extension
  );

-- 2. Limpiar acciones de ventana con referencias incorrectas
DELETE FROM ir_act_window_view WHERE act_window_id IN (
  SELECT id FROM ir_act_window WHERE res_model IN ('saas.customer', 'saas.instance', 'saas.service.package')
);

-- 3. Limpiar cache
DELETE FROM ir_model_data WHERE model = 'ir.ui.view' AND module = 'odoo_saas_core';
DELETE FROM ir_model_data WHERE model = 'ir.actions.act_window' AND module = 'odoo_saas_core' AND name LIKE 'action_saas%';

-- Para ejecutar este script:
-- 1. Hacer backup de la base de datos primero
-- 2. Conectarse a psql: psql -U odoo -d tu_database
-- 3. Ejecutar: \i fix_views.sql
-- 4. Actualizar módulo: odoo-bin -d tu_database -u odoo_saas_core --stop-after-init
