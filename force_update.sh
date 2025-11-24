#!/bin/bash
# Script para forzar la actualización del módulo saas_stripe_subscription

echo "=== Forzando actualización de módulos Stripe ==="

# Actualizar marca de tiempo del __manifest__.py para forzar detección de cambios
touch /home/dml/modulos_odoo18/saas_stripe_subscription/__manifest__.py

echo "Módulos marcados para actualización"
echo ""
echo "Ahora ejecuta UNO de estos comandos según tu instalación:"
echo ""
echo "OPCIÓN 1 - Si usas odoo-bin directamente:"
echo "  cd /ruta/a/odoo"
echo "  ./odoo-bin -u saas_stripe_subscription -d odoo18"
echo ""
echo "OPCIÓN 2 - Si usas systemd:"
echo "  sudo systemctl restart odoo"
echo ""
echo "OPCIÓN 3 - Si usas Docker/Kubernetes:"
echo "  kubectl rollout restart deployment odoo18"
echo ""
echo "OPCIÓN 4 - Vía interfaz de Odoo:"
echo "  1. Ir a Aplicaciones"
echo "  2. Quitar filtro 'Aplicaciones'"
echo "  3. Buscar 'saas_stripe_subscription'"
echo "  4. Click en los 3 puntos → Actualizar"
echo ""
