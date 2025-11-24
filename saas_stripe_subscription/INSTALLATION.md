# Guía de Instalación - SaaS Stripe Subscription

## Requisitos Previos

### Módulos Requeridos
Asegúrate de tener instalados los siguientes módulos antes de instalar `saas_stripe_subscription`:

1. **subscription_package** - Gestión de suscripciones para Odoo Community
2. **payment_stripe** - Integración de pagos con Stripe (incluido en Odoo)
3. **saas_management** - Gestión de instancias SaaS

### Cuenta de Stripe
Necesitas una cuenta de Stripe con:
- API Keys (test y/o production)
- Acceso a la API de Subscriptions

## Pasos de Instalación

### 1. Copiar el Módulo

```bash
# Copiar el módulo a tu directorio de addons
cp -r saas_stripe_subscription /path/to/odoo/addons/
```

### 2. Actualizar Lista de Módulos

En Odoo:
1. Ir a **Aplicaciones**
2. Hacer clic en el menú de tres puntos (⋮)
3. Seleccionar **Actualizar Lista de Aplicaciones**
4. Hacer clic en **Actualizar**

### 3. Instalar el Módulo

1. En **Aplicaciones**, buscar "SaaS Stripe Subscription"
2. Hacer clic en **Instalar**

## Configuración Inicial

### 1. Configurar Payment Provider de Stripe

#### Para Modo Test (Desarrollo):

1. Ir a **Contabilidad > Configuración > Proveedores de Pago**
2. Buscar o crear proveedor "Stripe"
3. Configurar:
   - **Estado**: Test
   - **Publishable Key**: `pk_test_...` (tu clave pública de test)
   - **Secret Key**: `sk_test_...` (tu clave secreta de test)
4. Guardar

#### Para Modo Producción:

1. Ir a **Contabilidad > Configuración > Proveedores de Pago**
2. Configurar el proveedor Stripe con:
   - **Estado**: Enabled
   - **Publishable Key**: `pk_live_...` (tu clave pública de producción)
   - **Secret Key**: `sk_live_...` (tu clave secreta de producción)
   - **Webhook Secret**: (opcional) `whsec_...` para webhooks
3. Guardar

### 2. Configurar el Módulo de Suscripciones Stripe

1. Ir a **Ajustes > General Settings**
2. Buscar la sección **Stripe Subscriptions**
3. Configurar:
   - ✅ **Enable Stripe Subscription Sync**: Activar
   - ✅ **Auto-sync Products to Stripe**: Activar (recomendado)
   - **Default Stripe Provider**: Seleccionar el proveedor Stripe configurado
4. Guardar

## Verificación de la Instalación

### Probar en Modo Test

1. Crear una suscripción de prueba:
   - Ir a **Suscripciones > Suscripciones**
   - Crear nueva suscripción
   - Agregar cliente y productos
   - Verificar que **Sync with Stripe** esté activado
   - Verificar que **Payment Provider** esté seleccionado

2. Iniciar la suscripción:
   - Hacer clic en **Start Subscription**
   - Verificar que no hay errores
   - Verificar que aparecen los campos:
     - **Stripe Customer ID**
     - **Stripe Subscription ID**
     - **Stripe Status**

3. Verificar en Stripe Dashboard:
   - Ir a https://dashboard.stripe.com/test/subscriptions
   - Buscar la suscripción recién creada
   - Verificar que los datos coinciden con Odoo

## Solución de Problemas

### Error: "No Stripe payment provider configured"

**Solución**:
- Verificar que hay un proveedor Stripe configurado
- Verificar que el proveedor tiene estado "Test" o "Enabled"
- Verificar que las API keys están configuradas correctamente

### Error: "Failed to create subscription in Stripe"

**Posibles causas**:
1. API keys incorrectas o inválidas
2. Sin conexión a internet
3. Cuenta de Stripe no activa
4. Límite de API excedido

**Solución**:
- Verificar las API keys en el payment provider
- Verificar conexión a internet
- Revisar los logs de Odoo para más detalles
- Verificar el estado de la cuenta en Stripe Dashboard

### Las suscripciones no se sincronizan

**Verificar**:
1. Que el campo **Sync with Stripe** esté activado en la suscripción
2. Que haya un **Payment Provider** seleccionado
3. Revisar los logs de Odoo: `/var/log/odoo/odoo.log`
4. Verificar que los productos tengan precios configurados

## Configuración Avanzada

### Webhooks de Stripe (Opcional)

Para sincronización bidireccional (Stripe → Odoo), configura webhooks:

1. En Stripe Dashboard:
   - Ir a **Developers > Webhooks**
   - Hacer clic en **Add endpoint**
   - URL: `https://tu-dominio.com/payment/stripe/webhook`
   - Eventos a escuchar:
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`

2. En Odoo:
   - Copiar el **Webhook Secret** de Stripe
   - Pegarlo en el campo **Webhook Signing Secret** del payment provider

### Personalización de Intervalos

El módulo mapea automáticamente los períodos de recurrencia:
- Para personalizar el mapeo, editar el método `_stripe_get_interval_from_period` en `product_template.py`

## Próximos Pasos

1. **Probar en Test**: Crear varias suscripciones de prueba
2. **Verificar Sincronización**: Modificar y cancelar suscripciones
3. **Migrar a Producción**: Cambiar a API keys de producción
4. **Configurar Webhooks**: Para sincronización completa

## Soporte

Para soporte técnico:
- Email: support@automateai.com.mx
- Website: https://automateai.com.mx
- Documentación: Ver README.md

## Referencias

- [Stripe API Documentation](https://stripe.com/docs/api)
- [Stripe Subscriptions Guide](https://stripe.com/docs/billing/subscriptions/overview)
- [Odoo Payment Provider Documentation](https://www.odoo.com/documentation/18.0/developer/reference/backend/payment.html)
