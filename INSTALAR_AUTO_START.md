# Instalar Módulo de Auto-Start

## Problema Actual
El pago se procesa correctamente, pero la suscripción **NO** se inicia automáticamente porque el módulo `saas_subscription_payment_auto_start` no está instalado.

## Evidencia
En los logs del pago (S00033) no aparecen estos mensajes que deberían aparecer:
```
=== PAYMENT AUTO-START: _reconcile_after_done called ===
Auto-starting subscription...
```

## Solución: Instalar el Módulo

### Opción 1: Via Interfaz de Odoo (RECOMENDADO)

1. **Ir a Aplicaciones**
   - Menú principal → Aplicaciones

2. **Activar modo desarrollador** (si no está activado)
   - Ir a Ajustes → General Settings
   - Scroll hasta abajo → "Developer Tools"
   - Click en "Activate the developer mode"

3. **Actualizar Lista de Aplicaciones**
   - En el menú Aplicaciones
   - Click en el menú de 3 líneas (☰) arriba a la derecha
   - Seleccionar "Update Apps List"
   - Click "Update" en el diálogo

4. **Buscar e Instalar**
   - En Aplicaciones, quitar el filtro "Apps" (para ver todos los módulos)
   - Buscar: `saas_subscription_payment_auto_start`
   - O buscar: `Subscription Auto-Start`
   - Click en "Install" / "Instalar"

5. **Verificar instalación**
   - El módulo debería aparecer como "Installed"
   - Reiniciar Odoo si es necesario

### Opción 2: Via Terminal/Línea de Comandos

```bash
# Si tienes acceso directo a odoo-bin
cd /ruta/a/odoo
./odoo-bin -u saas_subscription_payment_auto_start -d odoo18 --stop-after-init

# Si usas systemd
sudo systemctl restart odoo

# Si usas Docker/Kubernetes
kubectl exec -it <pod-name> -- odoo-bin -u saas_subscription_payment_auto_start -d odoo18 --stop-after-init
kubectl rollout restart deployment odoo18
```

### Opción 3: Via Python/ORM (modo desarrollador)

1. Ir a Settings → Technical → Database Structure → Models
2. Buscar modelo: `ir.module.module`
3. Filtrar por name = 'saas_subscription_payment_auto_start'
4. Si existe, cambiar state a 'to install'
5. Reiniciar servidor Odoo

## Verificar que Funciona

Después de instalar, prueba con un nuevo pago:

1. **Crear nueva suscripción** (quedará en Draft)
2. **Procesar pago** para esa suscripción
3. **Revisar logs** - deberías ver:

```
=== PAYMENT AUTO-START: _reconcile_after_done called ===
Payment transaction S00034 - state: done, has sale_order_ids: True
Payment transaction S00034 is done with sale orders: ['S00034']
=== Searching for subscriptions linked to sale orders: [34] ===
Found 1 draft subscriptions for transaction S00034
Auto-starting subscription SUS/xxx (ID: 795) for paid transaction S00034
Created Stripe customer cus_xxxxx for partner XX
Created Stripe product prod_xxxxx for Odoo product XX
Created Stripe price price_xxxxx for product XXX
Creating Stripe subscription with payload keys: [...]
Created Stripe subscription sub_xxxxx for Odoo subscription 795
Successfully auto-started subscription SUS/xxx
```

4. **Verificar en Stripe Dashboard** - la suscripción debe aparecer

## Si Sigue Sin Funcionar

Verifica:

1. **El módulo está instalado:**
   ```sql
   SELECT name, state FROM ir_module_module
   WHERE name = 'saas_subscription_payment_auto_start';
   ```
   Debe mostrar: `state = 'installed'`

2. **Las suscripciones tienen sale_order_id:**
   - Ve a la suscripción
   - Verifica que tiene un campo "Sale Order" lleno
   - Si no tiene, el auto-start no puede encontrarla

3. **El payment.transaction tiene sale_order_ids:**
   - Esto se llena automáticamente al procesar el pago
   - Verifica en los logs: "has sale_order_ids: True"

## Notas Importantes

- El auto-start **SOLO** funciona cuando el pago se procesa **DESPUÉS** de que la suscripción se crea
- Si haces START manual primero, el pago posterior no hace nada
- El flujo correcto es: Crear suscripción (draft) → Procesar pago → Auto-start
