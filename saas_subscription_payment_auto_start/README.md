# Subscription Auto-Start on Payment

## Descripción

Este módulo inicia automáticamente las suscripciones cuando se procesa exitosamente el pago asociado.

## Problema que Resuelve

Cuando un cliente realiza un pago por una suscripción:
- La suscripción se crea en estado "Draft"
- Se procesa el pago
- **ANTES**: Había que ir manualmente a la suscripción y hacer clic en "START"
- **AHORA**: La suscripción se inicia automáticamente cuando el pago es exitoso

## Flujo Automático

```
Cliente realiza pago
  ↓
Payment Transaction = done
  ↓
Se buscan suscripciones en draft vinculadas a la orden
  ↓
Se llama automáticamente a button_start_date()
  ↓
Si tiene Stripe sync habilitado → Crea suscripción en Stripe
  ↓
Subscription = In Progress
```

## Instalación

1. Copiar módulo a addons
2. Actualizar lista de aplicaciones
3. Instalar **"Subscription Auto-Start on Payment"**

## Dependencias

- `payment` - Sistema de pagos de Odoo
- `sale` - Órdenes de venta
- `subscription_package` - Gestión de suscripciones

## Compatibilidad

- Funciona con cualquier payment provider
- Compatible con `saas_stripe_subscription`
- No interfiere con suscripciones manuales

## Logs

El módulo registra cada acción:

```
INFO: Auto-starting subscription SUS/001 for paid transaction TX-001
INFO: Successfully auto-started subscription SUS/001
```

Si hay errores, no bloquea el flujo de pago, solo registra:

```
ERROR: Failed to auto-start subscription SUS/001: [error message]
```

## Notas

- Solo inicia suscripciones en estado "draft"
- No afecta suscripciones ya iniciadas
- Registra mensajes en el chatter de la suscripción
- No bloquea el flujo de pago si hay errores

## Autor

**AutomateAI**
Website: https://automateai.com.mx
Licencia: LGPL-3
