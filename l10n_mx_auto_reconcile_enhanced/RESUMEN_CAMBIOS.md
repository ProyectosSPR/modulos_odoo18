# Sistema Unificado de Conciliación - Resumen de Cambios

## 🎯 Problema que Resuelve

El sistema anterior tenía **dos modelos separados** (reglas directas y reglas por relación) que eran confusos y no permitían búsquedas inversas (desde órdenes hacia pagos).

## ✨ Solución: Sistema Unificado

Creé un **único modelo** (`mx.reconcile.rule.unified`) que soporta **3 modos de búsqueda**:

### 1️⃣ Modo Directo: Pago → Factura
- Compara directamente campos entre pagos y facturas
- Ejemplo: `payment_ref` contiene `invoice.name`

### 2️⃣ Modo Relación: Pago → Orden → Factura
- Busca el valor del pago en órdenes de venta/compra
- Obtiene las facturas de esas órdenes
- Ejemplo: "Pago SO001234" → busca Orden SO001234 → obtiene sus facturas

### 3️⃣ Modo Relación Inversa: Orden → Pago → Factura ⭐ **NUEVO**
- **Empieza desde órdenes** (filtradas por `relation_domain`)
- Para cada orden, **busca pagos** que la referencien
- **Concilia las facturas de la orden** con esos pagos

**Caso de uso del modo inverso:**
Tienes órdenes de venta ya facturadas y quieres encontrar automáticamente los pagos que los clientes hicieron referenciando el número de orden.

```
Orden SO001234 (facturada → INV/2024/00123)
    ↓
Buscar pagos con "SO001234" en payment_ref
    ↓
Pago encontrado: "Pago cliente SO001234"
    ↓
Conciliar factura INV/2024/00123 con ese pago
```

---

## 📋 Configuración en 4 Pasos Simples

### PASO 1: ¿Qué campo del Pago buscar?
- Selecciona cualquier campo: `payment_ref`, `narration`, `ref`, `partner_id`, etc.
- **Opcional:** Patrón de extracción regex
  - Ejemplo: `r"SO(\d+)"` extrae "001234" de "Pago SO001234"

### PASO 2: ¿Buscar Directo o por Relación?
- **Directo:** Selecciona campo de factura
- **Relación:** Selecciona modelo intermedio (Orden Venta/Compra) + campo
- **Relación Inversa:** Igual que relación, pero búsqueda desde órdenes

### PASO 3: ¿Cómo Comparar?
- `=`: Igualdad exacta
- `ilike`: Contiene (insensible a mayúsculas) ← **El más común**
- `like`: Patrón con %
- `in`: Está en lista
- `=ilike`: Igual O contiene

### PASO 4: Filtros Adicionales (Opcional)
- **Filtro de Pagos:** `[('amount', '>', 1000)]`
- **Filtro de Facturas:** `[('move_type', '=', 'out_invoice')]`
- **Filtro de Órdenes:** `[('state', '=', 'sale')]`
  - ⚠️ **IMPORTANTE para modo inverso:** Este filtro define qué órdenes buscar

---

## 📂 Archivos Creados

```
models/
  ├── mx_reconcile_rule_unified.py          ← Modelo principal

views/
  ├── mx_reconcile_rule_unified_views.xml   ← Vista del modelo

wizard/
  ├── mx_reconcile_rule_test_wizard_unified.py       ← Wizard de prueba
  └── mx_reconcile_rule_test_wizard_unified_views.xml

data/
  └── mx_reconcile_rule_unified_data.xml    ← 6 reglas de ejemplo
```

## 📚 Archivos Modificados

```
models/__init__.py                          ← Agregado import
wizard/__init__.py                          ← Agregado import
__manifest__.py                             ← Agregadas vistas y datos
security/ir.model.access.csv               ← Agregados permisos
views/menu_views.xml                        ← Agregado menú
```

---

## 🧪 Wizard de Prueba

Cada regla tiene un botón **"Probar Regla"** que abre un wizard donde puedes:

1. **Seleccionar período** de fechas
2. **Ejecutar prueba** con esa regla
3. **Ver tabla detallada** de matches:
   - Fecha, Referencia, Monto del pago
   - Score de coincidencia (barra de progreso)
   - Factura, Partner, Monto factura
   - Información del match
4. **Abrir Vista OCA** para ver visualmente los matches

---

## 📌 Ejemplos de Reglas Incluidas

### 1. Match Directo por Referencia
```
Campo Pago: payment_ref
Campo Factura: name
Operador: ilike
```

### 2. Match por Orden de Venta
```
Modo: relation
Campo Pago: payment_ref
Patrón: SO(\d+)Referencia de la orden (Orden de venta)
Documento: sale.order
Campo Orden: name
```

### 3. Match por Orden de Compra
```
Modo: relation
Campo Pago: payment_ref
Patrón: PO(\d+)
Documento: purchase.order
Campo Orden: name
```

### 4. Match por Partner
```
Modo: direct
Campo Pago: partner_id
Campo Factura: partner_id
Operador: =
```

### 5. ⭐ Match Inverso - Órdenes Facturadas → Pagos
```
Modo: relation_reverse
Campo Pago: payment_ref
Patrón: SO(\d+)
Documento: sale.order
Campo Orden: name
Filtro Órdenes: [('state', '=', 'sale'), ('invoice_status', '=', 'invoiced')]
```

### 6. ⭐ Match Inverso - Órdenes de Compra
```
Modo: relation_reverse
Campo Pago: payment_ref
Patrón: PO(\d+)
Documento: purchase.order
Campo Orden: name
Filtro Órdenes: [('state', 'in', ['purchase', 'done']), ('invoice_status', '=', 'invoiced')]
```

---

## 🚀 Cómo Usar

### En Kubernetes:

1. **Copiar archivos** modificados al servidor
2. **Reiniciar pod** de Odoo
3. **Actualizar módulo** desde UI de Odoo:
   - Ir a Apps
   - Buscar "Conciliación Automática"
   - Click en "Upgrade"

4. **Acceder al menú:**
   ```
   Declaraciones Fiscales → Conciliación Automática → Configuración → Reglas de Conciliación (Nuevo)
   ```

5. **Crear tu primera regla:**
   - Click en "Crear"
   - Seguir los 4 pasos
   - Guardar
   - Click en "Probar Regla" para testear

### Reglas Antiguas

Los modelos antiguos (`mx.reconcile.rule` y `mx.reconcile.relation.rule`) siguen existiendo pero:
- Solo visibles para grupo `base.group_no_one` (Technical Features)
- Se recomienda migrar a reglas unificadas
- Se pueden eliminar en futuras versiones

---

## 🔑 Ventajas del Sistema Unificado

✅ **Más simple:** Un solo modelo en lugar de dos
✅ **Más flexible:** 3 modos de búsqueda
✅ **Búsqueda inversa:** Desde órdenes hacia pagos
✅ **Mejor UI:** Explicaciones claras en cada paso
✅ **Ejemplos incluidos:** 6 reglas pre-configuradas
✅ **Wizard de prueba:** Testear antes de ejecutar
✅ **Integración OCA:** Ver resultados en vista de conciliación

---

## 📊 Flujo Técnico del Modo Inverso

```python
def _apply_relation_reverse_match(self, payments, invoices):
    """
    1. Buscar órdenes con filtro relation_domain
    2. Para cada orden:
       a. Obtener valor del campo (ej. "SO001234")
       b. Buscar en todos los pagos si referencian ese valor
       c. Obtener facturas de la orden
       d. Hacer match: pago encontrado → factura de orden
    """
```

**Ejemplo real:**
```
Órdenes en BD:
  - SO001234 (state=sale, invoice_ids=[INV/2024/00123])
  - SO001235 (state=sale, invoice_ids=[INV/2024/00124])

Pagos en BD:
  - Pago 1: payment_ref = "Transferencia SO001234"
  - Pago 2: payment_ref = "Efectivo cliente"
  - Pago 3: payment_ref = "Pago orden SO001235"

Resultado:
  ✓ Match: Pago 1 → INV/2024/00123 (via SO001234)
  ✓ Match: Pago 3 → INV/2024/00124 (via SO001235)
```

---

## 🎓 Tips de Uso

### Para Facturas de Cliente (Órdenes de Venta)
```python
# Modo inverso para encontrar pagos de órdenes facturadas
match_mode: relation_reverse
relation_model: sale.order
relation_domain: [('state', '=', 'sale'), ('invoice_status', '=', 'invoiced')]
```

### Para Facturas de Proveedor (Órdenes de Compra)
```python
# Modo inverso para encontrar pagos de órdenes de compra
match_mode: relation_reverse
relation_model: purchase.order
relation_domain: [('state', 'in', ['purchase', 'done']), ('invoice_status', '=', 'invoiced')]
```

### Patrones Regex Comunes
```python
SO(\d+)      # Extrae "001234" de "Pago SO001234"
PO(\d+)      # Extrae "005678" de "Compra PO005678"
INV.*?(\d+)  # Extrae números de "INV/2024/00123"
```

---

## ❓ FAQ

**P: ¿Puedo usar reglas directas y por relación al mismo tiempo?**
R: Sí, puedes crear múltiples reglas. Se ejecutan en orden de secuencia/prioridad.

**P: ¿Qué pasa si una regla encuentra múltiples matches?**
R: Todos se guardan con su score. El usuario decide cuál aplicar en la vista OCA.

**P: ¿El modo inverso es más lento?**
R: Depende. Si tienes muchas órdenes, puede ser más lento. Usa filtros en `relation_domain` para limitar la búsqueda.

**P: ¿Puedo combinar filtros?**
R: Sí, todos los dominios se pueden combinar:
```python
[('state', '=', 'sale'), ('partner_id.country_id.code', '=', 'MX'), ('amount_total', '>', 1000)]
```

---

## 🐛 Troubleshooting

### No encuentra matches
1. Verificar que los campos tengan valores
2. Probar con operador `ilike` (más flexible)
3. Reducir `min_score`
4. Revisar que extract_pattern sea correcto
5. Verificar dominios no sean muy restrictivos

### Modo inverso no funciona
1. **Verificar `relation_domain`:** Debe retornar órdenes
2. **Verificar `invoice_status`:** Órdenes deben estar facturadas
3. **Revisar logs:** Buscar "RELACIÓN INVERSA" en logs de Odoo

### Error de permisos
```bash
# Verificar que usuario tenga grupo reconcile_user o reconcile_manager
```

---

## 📞 Soporte

Para dudas o problemas, revisar:
1. Logs de Odoo (buscar "REGLA UNIFICADA")
2. Descripción de reglas de ejemplo
3. Tooltips en cada campo del formulario
