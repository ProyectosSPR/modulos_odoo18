#!/bin/bash
###############################################################################
# Script para Solucionar Problema de Wizard en Vistas de SaaS Core
###############################################################################

echo "======================================================================"
echo " Solucionador de Problema de Wizard - SaaS Modules"
echo "======================================================================"
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Paso 1: Verificar que estamos en el directorio correcto
echo "Paso 1: Verificando directorio..."
if [ ! -d "odoo_saas_core" ]; then
    print_error "No se encontró odoo_saas_core. ¿Estás en el directorio correcto?"
    echo "          Debes ejecutar este script desde: /home/user/modulos_odoo18"
    exit 1
fi
print_status "Directorio correcto"
echo ""

# Paso 2: Buscar bindings de wizard incorrectos
echo "Paso 2: Buscando configuraciones de wizard incorrectas..."
BINDING_ISSUES=$(grep -r "binding_model.*saas\." odoo_saas_core/ 2>/dev/null | grep -v ".pyc" | grep -v "__pycache__")
if [ ! -z "$BINDING_ISSUES" ]; then
    print_warning "Se encontraron bindings de wizard:"
    echo "$BINDING_ISSUES"
else
    print_status "No se encontraron bindings incorrectos"
fi
echo ""

# Paso 3: Verificar estructura de acciones
echo "Paso 3: Verificando acciones de ventana..."
ACTION_FILES=$(find odoo_saas_core/views -name "*.xml" -exec grep -l "ir.actions.act_window" {} \;)
for file in $ACTION_FILES; do
    echo "   Revisando: $file"
    # Buscar acciones con target='new' que no sean wizards
    SUSPICIOUS=$(grep -A5 "res_model.*saas\." "$file" | grep "target.*new" | grep -v "wizard")
    if [ ! -z "$SUSPICIOUS" ]; then
        print_warning "Posible acción con target='new' encontrada en $file"
        echo "$SUSPICIOUS"
    fi
done
print_status "Verificación de acciones completada"
echo ""

# Paso 4: Verificar que las vistas están correctamente definidas
echo "Paso 4: Verificando definiciones de vistas..."
CUSTOMER_FORM=$(grep -c "view_saas_customer_form" odoo_saas_core/views/saas_customer_views.xml)
INSTANCE_FORM=$(grep -c "view_saas_instance_form" odoo_saas_core/views/saas_instance_views.xml)

if [ $CUSTOMER_FORM -gt 0 ]; then
    print_status "Vista de formulario de Customer encontrada"
else
    print_error "Vista de formulario de Customer NO encontrada"
fi

if [ $INSTANCE_FORM -gt 0 ]; then
    print_status "Vista de formulario de Instance encontrada"
else
    print_error "Vista de formulario de Instance NO encontrada"
fi
echo ""

# Paso 5: Crear script SQL para diagnosticar en base de datos
echo "Paso 5: Creando script de diagnóstico SQL..."
cat > /tmp/diagnose_wizard_issue.sql <<'SQL'
-- Script de diagnóstico para problema de wizard

\echo '=== Acciones de Ventana para Modelos SaaS ==='
SELECT
    id,
    name,
    res_model,
    view_mode,
    target,
    context
FROM ir_act_window
WHERE res_model LIKE 'saas.%'
ORDER BY res_model;

\echo ''
\echo '=== Vistas para Modelos SaaS ==='
SELECT
    id,
    name,
    model,
    type,
    priority,
    mode
FROM ir_ui_view
WHERE model LIKE 'saas.%'
  AND type = 'form'
ORDER BY model, priority;

\echo ''
\echo '=== Vistas de Wizard ==='
SELECT
    id,
    name,
    model,
    type
FROM ir_ui_view
WHERE model LIKE '%wizard%'
  AND model LIKE '%saas%';
SQL

print_status "Script SQL creado en: /tmp/diagnose_wizard_issue.sql"
echo ""

# Paso 6: Instrucciones para el usuario
echo "======================================================================"
echo " INSTRUCCIONES PARA SOLUCIONAR"
echo "======================================================================"
echo ""
echo "${GREEN}OPCIÓN 1: Actualizar módulo desde Odoo (RECOMENDADO)${NC}"
echo "   1. Ir a: Aplicaciones → Remover filtro 'Apps'"
echo "   2. Buscar: 'Odoo SaaS Core'"
echo "   3. Hacer clic en 'Actualizar'"
echo "   4. Limpiar caché del navegador (Ctrl+Shift+Delete)"
echo "   5. Recargar Odoo (Ctrl+F5)"
echo ""

echo "${GREEN}OPCIÓN 2: Actualizar desde terminal${NC}"
echo "   Ejecuta uno de estos comandos:"
echo ""
if command -v odoo-bin &> /dev/null; then
    DB_NAME=$(sudo grep "^db_name" /etc/odoo/odoo.conf 2>/dev/null | cut -d'=' -f2 | tr -d ' ')
    if [ ! -z "$DB_NAME" ]; then
        echo "   ${YELLOW}sudo -u odoo odoo-bin -c /etc/odoo/odoo.conf -u odoo_saas_core -d $DB_NAME --stop-after-init${NC}"
    else
        echo "   ${YELLOW}sudo -u odoo odoo-bin -c /etc/odoo/odoo.conf -u odoo_saas_core -d TU_BASE_DE_DATOS --stop-after-init${NC}"
    fi
    echo "   ${YELLOW}sudo systemctl restart odoo${NC}"
elif command -v odoo &> /dev/null; then
    echo "   ${YELLOW}sudo systemctl restart odoo${NC}"
else
    print_warning "No se encontró comando odoo-bin. Actualiza manualmente desde la interfaz."
fi
echo ""

echo "${GREEN}OPCIÓN 3: Diagnosticar en base de datos${NC}"
echo "   Si tienes acceso a PostgreSQL, ejecuta:"
echo "   ${YELLOW}psql -U odoo -d nombre_base_datos -f /tmp/diagnose_wizard_issue.sql${NC}"
echo ""

# Paso 7: Verificar si el usuario quiere ejecutar actualización automática
echo "======================================================================"
read -p "¿Quieres que intente actualizar el módulo automáticamente? (s/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[SsYy]$ ]]; then
    echo ""
    print_status "Intentando actualizar módulo..."

    # Buscar configuración de Odoo
    ODOO_CONF="/etc/odoo/odoo.conf"
    if [ ! -f "$ODOO_CONF" ]; then
        ODOO_CONF="/etc/odoo-server.conf"
    fi

    if [ -f "$ODOO_CONF" ]; then
        DB_NAME=$(sudo grep "^db_name" "$ODOO_CONF" | cut -d'=' -f2 | tr -d ' ')

        if [ -z "$DB_NAME" ]; then
            read -p "Ingresa el nombre de tu base de datos: " DB_NAME
        fi

        echo "Base de datos: $DB_NAME"
        echo "Actualizando módulo odoo_saas_core..."

        if command -v odoo-bin &> /dev/null; then
            sudo -u odoo odoo-bin -c "$ODOO_CONF" -u odoo_saas_core -d "$DB_NAME" --stop-after-init
            echo ""
            print_status "Módulo actualizado. Reiniciando Odoo..."
            sudo systemctl restart odoo
            print_status "¡Listo! Ahora prueba abrir las vistas en Odoo"
        else
            print_warning "No se encontró odoo-bin. Ejecuta manualmente desde la interfaz."
        fi
    else
        print_error "No se encontró archivo de configuración de Odoo"
        print_warning "Actualiza manualmente desde la interfaz de Odoo"
    fi
else
    echo ""
    print_status "OK. Actualiza manualmente siguiendo las instrucciones arriba."
fi

echo ""
echo "======================================================================"
echo " Para más información, consulta: UPDATE_SAAS_MODULES.md"
echo "======================================================================"
