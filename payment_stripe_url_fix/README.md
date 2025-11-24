# Payment Stripe URL Fix for Kubernetes

## Problema

Cuando Odoo corre en Kubernetes con un cloudtunnel o ingress, el módulo `payment_stripe` genera URLs de retorno usando los headers HTTP del request, que apuntan a direcciones internas del cluster (como `http://odoo18.default.svc.cluster.local:8069`) en lugar de la URL pública configurada.

Esto causa que después de un pago exitoso en Stripe, el usuario sea redirigido a una URL no accesible desde internet.

## Solución

Este módulo sobrescribe los métodos relevantes de `payment.transaction` y `payment.provider` para forzar el uso del parámetro `web.base.url` configurado en Odoo, ignorando los headers HTTP del request.

## Instalación

1. Copiar este módulo a tu directorio de addons
2. Actualizar lista de módulos en Odoo
3. Instalar el módulo `Payment Stripe URL Fix for Kubernetes`

## Configuración

Asegúrate de que el parámetro `web.base.url` esté configurado correctamente:

1. En Odoo, ir a **Ajustes > Parámetros del Sistema**
2. Buscar o crear el parámetro `web.base.url`
3. Establecer el valor a tu URL pública (ej: `https://automateai.com.mx`)
4. Guardar

## Verificación

Después de instalar el módulo, verifica los logs de Odoo. Deberías ver mensajes como:

```
INFO odoo.addons.payment_stripe_url_fix.models.payment_transaction: Fixed Stripe return URL for transaction S00028: https://automateai.com.mx/payment/stripe/return?reference=S00028
```

## Notas Técnicas

- Compatible con Odoo 18.0
- Depende de: `payment_stripe`
- No modifica la base de datos, solo el comportamiento en tiempo de ejecución
- Puede desinstalarse sin problema si no se necesita

## Autor

**AutomateAI**
Website: https://automateai.com.mx
Licencia: LGPL-3
