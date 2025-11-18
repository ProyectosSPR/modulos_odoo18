# Guía de Instalación - SaaS Multi-Company

## Requisitos Previos

### Módulos Requeridos (en orden de instalación)

1. **subscription_package** (Cybrosys) - Gestión de paquetes de suscripción
2. **product_permissions** - Asignación automática de permisos
3. **saas_management** - Gestión de clientes e instancias SaaS
4. **saas_licensing** - Seguimiento de uso y facturación
5. **saas_multicompany** ← Este módulo

### Verificar Dependencias

```bash
# Verificar que todos los módulos estén presentes
cd /home/sergio/modulos_odoo18
ls -la product_permissions saas_management saas_licensing saas_multicompany

# Deben existir todos los directorios
```

## Instalación Paso a Paso

### 1. Verificar Sintaxis de Archivos

```bash
cd /home/sergio/modulos_odoo18/saas_multicompany

# Validar archivos Python
find models -name "*.py" -type f -exec python3 -m py_compile {} \;

# Validar archivos XML
python3 -c "
import xml.etree.ElementTree as ET
files = [
    'security/saas_multicompany_security.xml',
    'data/saas_multicompany_data.xml',
    'data/demo_data.xml',
    'views/product_template_views.xml',
    'views/res_company_views.xml',
    'views/saas_client_views.xml',
    'views/saas_multicompany_menus.xml'
]
for f in files:
    ET.parse(f)
    print(f'✓ {f}')
"
```

### 2. Reiniciar Odoo

```bash
# Reiniciar el servidor de Odoo para que detecte el nuevo módulo
sudo systemctl restart odoo
# o si usas docker:
# docker-compose restart odoo
```

### 3. Actualizar Lista de Aplicaciones

1. Ir a **Apps** (Aplicaciones)
2. Clic en **Update Apps List** (Actualizar Lista de Aplicaciones)
3. Confirmar la actualización

### 4. Instalar Módulo

1. Buscar "**SaaS Multi-Company**"
2. Clic en **Install**
3. Esperar a que se complete la instalación

### 5. Verificar Instalación

Verificar que aparezcan los siguientes menús:

```
SaaS Management
├── Clients
│   └── Clients (debe tener pestaña "Local Companies")
├── Instances
│   └── All Instances
├── Companies (NUEVO)
│   └── SaaS Companies
└── Licensing
    └── License Records
```

## Post-Instalación

### 1. Verificar Datos de Demo

Si instalaste con datos de demo, verifica que existan:

1. **Empresa Plantilla**: Settings → Companies → "SaaS Template Company"
2. **Paquetes de Suscripción**:
   - Subscriptions → Subscription Packages
   - "Multi-Company Plan - Basic" (5 users, 10GB)
   - "Multi-Company Plan - Professional" (20 users, 50GB)
3. **Productos de Demo**:
   - Sales → Products
   - "Module Access - Inventory Management"
   - "Module Access - Sales Management"

### 2. Configurar Empresa Plantilla (si no existe)

```
Settings → Companies → Create

Nombre: SaaS Template Company
☑ Is Template Company
Moneda: USD (o tu moneda preferida)
País: México (o tu país)
```

### 3. Crear Paquete de Suscripción

```
Subscriptions → Subscription Packages → Create

Nombre: Multi-Company Plan Basic
Max Users: 5
Max Companies: 1
Max Storage (GB): 10

Overage Pricing:
  Price per User: $50
  Price per Company: $200
  Price per GB: $10
```

### 4. Crear Producto de Acceso a Módulos

```
Sales → Products → Create

Nombre: Module Access - Inventory
Tipo: Service

Tab "Permissions":
  ☑ Assign Permissions
  Permission Groups: [Inventory / Manager]

Tab "Multi-Company":
  ☑ Is Module Access Product
  ☑ Auto-Create Company
  ☑ Restrict to Company
  Company Template: [SaaS Template Company]
  Multi-Company Subscription: [Multi-Company Plan Basic]
```

## Prueba Rápida (5 minutos)

### 1. Crear Cliente de Prueba

```
Contacts → Create

Nombre: Test Client ABC
Email: testclient@example.com
```

### 2. Crear Orden de Venta

```
Sales → Orders → Create

Cliente: Test Client ABC
Línea de Orden:
  Producto: Module Access - Inventory
  Cantidad: 1

Confirmar Orden
```

### 3. Verificar Resultados

**En el Chatter de la Orden**:
```
✅ SaaS Client created: Test Client ABC
🏢 Company created: Test Client ABC
📋 Subscription: Multi-Company Plan Basic
   • Max Users: 5
   • Max Companies: 1
   • Max Storage: 10 GB
👤 User testclient@example.com assigned to company Test Client ABC
🔒 Access restricted to this company only
✅ Permissions assigned: Inventory / Manager
📋 License tracking started
```

**Verificar la Empresa Creada**:
```
SaaS Management → Companies → SaaS Companies
→ Debe aparecer "Test Client ABC"
```

**Verificar el Cliente**:
```
SaaS Management → Clients → Clients
→ Abrir "Test Client ABC"
→ Tab "Local Companies" debe mostrar la empresa creada
```

**Verificar Licencia**:
```
SaaS Management → Licensing → License Records
→ Debe haber un registro para "Test Client ABC - [fecha]"
→ User Count: 1
→ Company Count: 1
```

## Troubleshooting

### Error: "External ID not found"

**Causa**: Datos de demo referencian grupos que no existen

**Solución**: Verificar que los módulos `stock` y `sales_team` estén instalados

```bash
# En Odoo, instalar:
Apps → Search "Inventory" → Install
Apps → Search "Sales" → Install
```

### Error: "User cannot have more than one user type"

**Causa**: El usuario es Portal y se le están asignando grupos internos

**Solución**: El módulo `product_permissions` debe estar actualizado con la conversión Portal→Internal automática

### Empresa no se crea al confirmar orden

**Verificar**:
1. ¿El producto tiene `is_module_access = True`?
2. ¿El producto tiene `auto_create_company = True`?
3. Revisar logs del servidor: `tail -f /var/log/odoo/odoo-server.log`

### Usuario no tiene acceso restringido

**Verificar**:
1. ¿El producto tiene `restrict_to_company = True`?
2. ¿El usuario está asignado a la empresa correcta?
3. ¿Las reglas de seguridad están activas?

```python
# Verificar reglas de seguridad
Settings → Technical → Security → Record Rules
→ Buscar "Multi-Company"
→ Deben aparecer las reglas con estado "Active"
```

## Siguientes Pasos

1. **Probar Licenciamiento**:
   - Crear snapshots de licencias manualmente
   - Ejecutar el cron job de licencias
   - Verificar detección de overages

2. **Probar Multi-Tenancy**:
   - Crear múltiples clientes
   - Verificar aislamiento de datos entre empresas
   - Probar con usuario no-admin

3. **Configurar Cron Job**:
   ```
   Settings → Technical → Automation → Scheduled Actions
   → "SaaS: Create Monthly License Records"
   → Configurar frecuencia (recomendado: diaria)
   ```

4. **Preparar para Producción**:
   - Configurar empresa plantilla con datos reales
   - Crear paquetes de suscripción comerciales
   - Crear productos de acceso a módulos
   - Configurar precios de overage

## Soporte

- **Documentación**: Ver `README.md` para documentación completa
- **Logs**: `/var/log/odoo/odoo-server.log`
- **Modo Debug**: Activar en Odoo para ver información detallada

---

**Versión**: 18.0.1.0.0
**Autor**: AutomateAI
**Website**: https://automateai.com.mx
