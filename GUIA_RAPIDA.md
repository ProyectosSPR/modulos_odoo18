# ⚡ Guía Rápida - 5 Minutos

Si quieres probar rápidamente los módulos, sigue estos pasos:

---

## 🚀 Prueba Rápida (5 minutos)

### 1️⃣ Instalar Módulos (2 min)

```
Aplicaciones → Quitar filtro "Apps" → Buscar:
1. product_permissions → Instalar
2. saas_management → Instalar
3. saas_licensing → Instalar (opcional)
```

### 2️⃣ Crear Producto SaaS + Permisos (1 min)

**Ventas → Productos → Crear**

```yaml
Nombre: SaaS Odoo Trial
Precio: 500

# Pestaña "Permissions"
Assign Permissions: ✓
Permission Groups: [Sales / User: Own Documents Only]

# Pestaña "SaaS Configuration"
Is SaaS Instance Product: ✓
Auto-Create Instance: ✓
Trial Days: 7

→ Guardar
```

### 3️⃣ Crear Cliente de Prueba (30 seg)

**Contactos → Crear**

```yaml
Nombre: Test Company
Email: test@demo.com

→ Guardar
```

### 4️⃣ Vender y Confirmar (1 min)

**Ventas → Presupuestos → Crear**

```yaml
Cliente: Test Company
Línea: SaaS Odoo Trial (qty: 1)

→ Guardar → Confirmar
```

### 5️⃣ Verificar Resultados (30 seg)

**Ver el Chatter de la orden:**
```
✅ User created: Test Company
✅ Permissions assigned...
✅ SaaS Client created: Test Company
🖥️ SaaS Instance created: ... (https://test-company.odoo.cloud)
```

**Ir a SaaS Management → Instances**
- ✅ Aparece instancia nueva
- ✅ Estado: Trial
- ✅ URL generada

---

## 🎯 Casos de Uso Comunes

### Caso 1: Solo Permisos (sin SaaS)

```yaml
Producto: Licencia de Acceso
  Permissions: ✓
  Permission Groups: [grupo que necesites]
  SaaS Configuration: ✗
```
**Resultado:** Solo asigna permisos al confirmar venta

---

### Caso 2: Solo SaaS (sin permisos)

```yaml
Producto: Instancia Odoo
  Permissions: ✗
  Is SaaS Instance: ✓
  Auto-Create Instance: ✓
```
**Resultado:** Solo crea cliente e instancia SaaS

---

### Caso 3: Completo (SaaS + Permisos + Licensing)

```yaml
Producto: Odoo Enterprise
  Permissions: ✓
  Permission Groups: [varios grupos]
  Is SaaS Instance: ✓
  Auto-Create Instance: ✓

Subscription Package: Plan Pro
  Max Users: 10
  Price per User: $50
```

**Resultado:**
1. Asigna permisos ✓
2. Crea cliente SaaS ✓
3. Crea instancia ✓
4. Hace tracking de uso ✓
5. Factura excesos ✓

---

## 🔍 Verificación Rápida

### ¿Funcionan los permisos?

```
Ajustes → Usuarios → [buscar usuario creado]
→ Pestaña "Derechos de Acceso"
→ Ver grupos asignados
```

### ¿Se creó el cliente SaaS?

```
SaaS Management → Clients
→ Buscar por nombre
→ Ver estado e instancias
```

### ¿Se creó la instancia?

```
SaaS Management → Instances
→ Ver lista
→ Abrir instancia → Ver subdomain y URL
```

### ¿Funciona el licensing?

```
Instancia → Asignar Subscription
Instancia → Pestaña "Licensing" → Click "Snapshot"
→ Configurar uso que exceda límites
→ Verificar overage amount
→ Click "Create Invoice"
```

---

## 📞 ¿Problemas?

Ver **GUIA_PRUEBAS.md** sección 6: Troubleshooting

---

## 🎓 Siguiente Nivel

Para pruebas completas y detalladas, revisar:
- **GUIA_PRUEBAS.md** - Guía paso a paso completa
- **README.md** - Documentación de cada módulo

---

**¡Listo para producción!** 🚀
