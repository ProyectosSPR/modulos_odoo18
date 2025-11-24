# Cómo Actualizar los Módulos

## Problema Resuelto
Se corrigió el error: `'subscription.package.plan' object has no attribute 'recurrence_period_id'`

## Módulos a Actualizar

1. **saas_stripe_subscription** - Corregido el paso de parámetro `recurrence_period`
2. **saas_subscription_payment_auto_start** - Añadidos logs detallados

## Opción 1: Actualizar vía Interfaz de Odoo

1. Ir a **Aplicaciones**
2. Quitar filtro "Aplicaciones"
3. Buscar: `saas_stripe_subscription`
4. Click en el módulo → **Actualizar**
5. Buscar: `saas_subscription_payment_auto_start`
6. Si no está instalado → **Instalar**
7. Si está instalado → **Actualizar**

## Opción 2: Actualizar vía Terminal

```bash
# Detener Odoo
sudo systemctl stop odoo

# O si está en Docker/Kubernetes, reiniciar el pod con:
kubectl rollout restart deployment odoo18

# O si usas odoo-bin directamente:
./odoo-bin -u saas_stripe_subscription,saas_subscription_payment_auto_start -d odoo18 --stop-after-init

# Iniciar Odoo de nuevo
sudo systemctl start odoo
```

## Opción 3: Actualizar en Desarrollo

```bash
# Si estás corriendo Odoo en modo desarrollo:
./odoo-bin -u saas_stripe_subscription,saas_subscription_payment_auto_start -d odoo18
```

## Qué esperar después de actualizar

### 1. Al hacer START manual en una suscripción:
- ✅ Debería crear el customer en Stripe
- ✅ Debería crear el product en Stripe
- ✅ Debería crear el price con el intervalo correcto
- ✅ Debería crear la subscription en Stripe
- ✅ No más error de `recurrence_period_id`

### 2. Al procesar un pago:
Los logs ahora mostrarán:
```
=== PAYMENT AUTO-START: _reconcile_after_done called ===
Payment transaction S00031 - state: done, has sale_order_ids: True
Payment transaction S00031 is done with sale orders: ['S00123']
=== Searching for subscriptions linked to sale orders: [123] ===
Found 1 draft subscriptions for transaction S00031
Auto-starting subscription SUS/001 (ID: 45) for paid transaction S00031
Successfully auto-started subscription SUS/001
```

### 3. Si no encuentra suscripciones:
```
No draft subscriptions found for transaction S00031 (sale orders: S00123)
Total subscriptions found for these sale orders: 1 (states: ['progress'])
```

Esto indica que la suscripción ya fue iniciada manualmente.

## Verificar que todo funciona

1. **Crear una nueva suscripción de prueba**
2. **NO hacer START manual**
3. **Procesar el pago**
4. **Verificar logs** - deberías ver los mensajes de auto-start
5. **Verificar en Stripe** - debería aparecer la suscripción

## Notas Importantes

- **recurrence_period_id** está en `subscription.package` (la suscripción), NO en el plan
- El plan tiene `renewal_period` y `renewal_value` (texto)
- La suscripción puede tener su propio `recurrence_period_id` que SOBRESCRIBE el del plan
- Prioridad: `subscription.recurrence_period_id` > `plan.renewal_period`
