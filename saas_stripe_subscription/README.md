# SaaS Stripe Subscription Integration

## Descripción

Este módulo integra el módulo `subscription_package` con la API de Suscripciones de Stripe para sincronizar automáticamente las suscripciones entre Odoo y Stripe.

## Características

### Sincronización Automática de Suscripciones

- **Creación**: Al iniciar una suscripción en Odoo, se crea automáticamente un customer y una subscription en Stripe
- **Cancelación**: Al cerrar una suscripción en Odoo, se cancela automáticamente en Stripe
- **Actualización**: Al modificar productos o cantidades, se actualiza la suscripción en Stripe
- **Estado**: Sincronización del estado de la suscripción desde Stripe

### Gestión de Productos

- Creación automática de productos en Stripe
- Sincronización de precios con Stripe
- Conversión automática de períodos de recurrencia de Odoo a intervalos de Stripe
- Soporte para productos de suscripción recurrentes

### Modo Test y Producción

- Detección automática de modo test/producción basado en el payment provider
- Usa las claves API configuradas en el payment provider de Stripe
- Campo indicador `is_test_subscription` para identificar suscripciones de prueba

## Instalación

### Dependencias

Este módulo requiere los siguientes módulos:

- `subscription_package` - Gestión de suscripciones
- `payment_stripe` - Integración de pagos con Stripe
- `saas_management` - Gestión de instancias SaaS

### Pasos de Instalación

1. Copiar el módulo a la carpeta de addons de Odoo
2. Actualizar la lista de módulos
3. Instalar el módulo `saas_stripe_subscription`

## Configuración

### 1. Configurar Payment Provider de Stripe

Antes de usar este módulo, debes configurar el payment provider de Stripe:

1. Ir a **Contabilidad > Configuración > Proveedores de Pago**
2. Seleccionar o crear un proveedor Stripe
3. Configurar las claves API:
   - **Publishable Key**: Tu clave pública de Stripe
   - **Secret Key**: Tu clave secreta de Stripe
   - **Webhook Secret**: (Opcional) Para recibir webhooks de Stripe

**Modo Test vs Producción**:
- Para modo test: usar claves que empiezan con `sk_test_...` y `pk_test_...`
- Para modo producción: usar claves que empiezan con `sk_live_...` y `pk_live_...`

### 2. Configurar el Módulo

Ir a **Ajustes > Stripe Subscriptions**:

- **Enable Stripe Subscription Sync**: Activar sincronización automática
- **Auto-sync Products to Stripe**: Crear productos automáticamente en Stripe
- **Default Stripe Provider**: Seleccionar el proveedor Stripe por defecto

## Uso

### Crear una Suscripción Sincronizada con Stripe

1. Ir a **Suscripciones > Suscripciones**
2. Crear una nueva suscripción
3. Configurar los campos:
   - **Customer**: Cliente de la suscripción
   - **Subscription Plan**: Plan de suscripción
   - **Products**: Agregar productos a la suscripción
   - **Sync with Stripe**: Activar (por defecto está activado)
   - **Payment Provider**: Seleccionar el proveedor Stripe

4. Hacer clic en **Start Subscription**

Al iniciar la suscripción:
- Se crea un customer en Stripe (si no existe)
- Se crean los productos en Stripe (si no existen)
- Se crea la suscripción en Stripe
- Se vincula con los IDs de Stripe

### Modificar una Suscripción

1. Abrir la suscripción
2. Modificar productos o cantidades
3. Guardar

Los cambios se sincronizan automáticamente con Stripe.

### Cancelar una Suscripción

1. Abrir la suscripción
2. Hacer clic en **Close**
3. Seleccionar motivo de cierre

La suscripción se cancela automáticamente en Stripe.

### Sincronizar Estado Manualmente

Si necesitas sincronizar el estado de una suscripción desde Stripe:

1. Abrir la suscripción
2. Hacer clic en **Sync Stripe Status**

## Campos Agregados

### Subscription Package

- `stripe_subscription_id`: ID de la suscripción en Stripe
- `stripe_customer_id`: ID del customer en Stripe
- `payment_provider_id`: Proveedor de pago Stripe a usar
- `stripe_sync_enabled`: Activar/desactivar sincronización
- `stripe_subscription_status`: Estado actual en Stripe
- `is_test_subscription`: Indica si es suscripción de prueba

### Product Template

- `stripe_product_id`: ID del producto en Stripe
- `stripe_auto_sync`: Sincronizar automáticamente con Stripe

## Flujo de Sincronización

### Creación de Suscripción

```
Odoo: Crear suscripción
  ↓
Odoo: Hacer clic en "Start Subscription"
  ↓
Stripe: Crear/obtener customer
  ↓
Stripe: Crear productos y precios
  ↓
Stripe: Crear subscription
  ↓
Odoo: Guardar IDs de Stripe
```

### Actualización de Suscripción

```
Odoo: Modificar product_line_ids
  ↓
Stripe: Obtener subscription actual
  ↓
Stripe: Eliminar items antiguos
  ↓
Stripe: Agregar items nuevos
  ↓
Odoo: Confirmar actualización
```

### Cancelación de Suscripción

```
Odoo: Hacer clic en "Close"
  ↓
Stripe: Cancelar subscription
  ↓
Odoo: Actualizar estado
```

## Mapeo de Períodos de Recurrencia

El módulo convierte automáticamente los períodos de recurrencia de Odoo a intervalos de Stripe:

| Odoo (UOM)        | Stripe Interval |
|-------------------|-----------------|
| Día / Day         | day             |
| Semana / Week     | week            |
| Mes / Month       | month           |
| Año / Year        | year            |

## Manejo de Errores

- Si falla la creación en Stripe: Se muestra error y no se crea la suscripción en Odoo
- Si falla la actualización en Stripe: Se registra en el chatter pero no bloquea la operación
- Si falla la cancelación en Stripe: Se registra en el chatter pero se permite cerrar en Odoo

## Logs

Todos los eventos importantes se registran en el log de Odoo:

- Creación de customers, productos, precios y suscripciones
- Actualizaciones y cancelaciones
- Errores de sincronización

Nivel de log: `INFO` para operaciones exitosas, `ERROR` para fallos

## Seguridad

- Las claves API de Stripe se almacenan en el payment provider
- Las claves secretas solo son visibles para el grupo `base.group_system`
- Todas las operaciones usan las credenciales del payment provider configurado

## Limitaciones Conocidas

- No sincroniza suscripciones existentes en Stripe hacia Odoo (solo Odoo → Stripe)
- Los webhooks de Stripe deben configurarse manualmente para sincronización bidireccional
- Solo soporta suscripciones con productos recurrentes

## Soporte y Contribuciones

Desarrollado por: **AutomateAI**
Website: https://automateai.com.mx
Licencia: LGPL-3

## Versión

- **Versión**: 18.0.1.0.0
- **Odoo Version**: 18.0
- **Fecha**: 2025
