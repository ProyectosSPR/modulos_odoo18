# Guía de Modelos de Pricing - SaaS Licensing

**Versión**: 18.0.2.0.0
**Fecha**: 2025-11-17

---

## Índice

1. [Resumen de Modelos](#resumen-de-modelos)
2. [Modelo 1: Overage Only](#modelo-1-overage-only)
3. [Modelo 2: Base + Included + Overage](#modelo-2-base--included--overage)
4. [Modelo 3: Per User](#modelo-3-per-user)
5. [Modelo 4: Base + Per User](#modelo-4-base--per-user)
6. [Configuración de Facturación](#configuración-de-facturación)
7. [Ejemplos Prácticos](#ejemplos-prácticos)

---

## Resumen de Modelos

El sistema ahora soporta **4 modelos de pricing flexibles** que puedes elegir por cada Subscription Package:

| Modelo | Costo Base | Usuarios Incluidos | Cobro por Usuario | Mejor para |
|--------|------------|-------------------|-------------------|------------|
| **Overage Only** | $0 | Sí (hasta límite) | Solo si excede límite | Planes gratuitos con límites |
| **Base + Included + Overage** | ✓ | Sí (X usuarios) | Solo adicionales | SaaS tradicional |
| **Per User** | $0 | No | Todos los usuarios | Pricing basado en uso |
| **Base + Per User** | ✓ | No | Todos los usuarios | Costo fijo + variable |

---

## Modelo 1: Overage Only

### Descripción
**Solo cobras cuando el cliente excede los límites del plan**. Es ideal para planes "freemium" o de prueba.

### Configuración

```
Pricing Model: Overage Only
Base Monthly Price: $0
Included Users: 5
Price per User: $50
```

### Cómo Funciona

- **0-5 usuarios**: $0 (gratis)
- **6 usuarios**: $50 (1 usuario adicional × $50)
- **10 usuarios**: $250 (5 usuarios adicionales × $50)

### Fórmula

```
Total = (Usuarios - Usuarios Incluidos) × Precio por Usuario

Solo si Usuarios > Usuarios Incluidos
```

### Caso de Uso

**Plan Startup Gratuito:**
- "Hasta 5 usuarios gratis"
- "Usuarios adicionales: $50/mes c/u"

---

## Modelo 2: Base + Included + Overage

### Descripción
**Precio base mensual que incluye X usuarios, cobras por usuarios adicionales**. Es el modelo SaaS más común.

### Configuración

```
Pricing Model: Base + Included + Overage
Base Monthly Price: $200
Included Users: 5
Price per Additional User: $50
```

### Cómo Funciona

- **0-5 usuarios**: $200 (base price)
- **6 usuarios**: $250 ($200 base + $50 adicional)
- **10 usuarios**: $450 ($200 base + $250 adicionales)

### Fórmula

```
Total = Base Price + (MAX(0, Usuarios - Usuarios Incluidos) × Precio por Usuario)
```

### Caso de Uso

**Plan Professional:**
- "Base: $200/mes (incluye hasta 5 usuarios)"
- "Usuarios adicionales: $50/mes c/u"

---

## Modelo 3: Per User

### Descripción
**Sin costo base, cobras por cada usuario**. Modelo completamente escalable.

### Configuración

```
Pricing Model: Per User
Base Monthly Price: $0
Price per User: $50 (ALL users count)
Max Users: 0 (unlimited, solo alerta)
```

### Cómo Funciona

- **1 usuario**: $50
- **5 usuarios**: $250
- **10 usuarios**: $500

### Fórmula

```
Total = Usuarios × Precio por Usuario
```

### Caso de Uso

**Plan Enterprise:**
- "Sin costo fijo"
- "$50/mes por cada usuario"
- "Paga solo por lo que usas"

---

## Modelo 4: Base + Per User

### Descripción
**Precio base fijo + cobro por TODOS los usuarios**. Modelo híbrido con costo mínimo garantizado.

### Configuración

```
Pricing Model: Base + Per User
Base Monthly Price: $100
Price per User: $50 (ALL users count)
```

### Cómo Funciona

- **1 usuario**: $150 ($100 base + $50 usuario)
- **5 usuarios**: $350 ($100 base + $250 usuarios)
- **10 usuarios**: $600 ($100 base + $500 usuarios)

### Fórmula

```
Total = Base Price + (Usuarios × Precio por Usuario)
```

### Caso de Uso

**Plan Premium:**
- "Base: $100/mes (infraestructura)"
- "Usuarios: $50/mes c/u"
- "Garantiza ingreso mínimo de $100"

---

## Configuración de Facturación

### Auto-Invoice

```python
auto_invoice = True  # Usa cron de subscription_package
```

**Funcionamiento:**
- El módulo `subscription_package` tiene un cron automático
- Crea facturas recurrentes según el plan
- Frecuencia configurable (mensual, anual, etc.)

**Cuándo usar:**
- Quieres facturación 100% automática
- Clientes pagan mensualmente sin intervención

### Invoice on Overage Detection

```python
invoice_on_overage = True  # Factura al detectar overage
```

**Funcionamiento:**
- El cron de `saas_licensing` crea snapshots diarios/mensuales
- Si detecta overage (o uso según modelo), marca como billable
- Puedes crear factura manualmente o automáticamente

**Cuándo usar:**
- Quieres revisar antes de facturar
- Usas modelo "overage only" y solo facturas cuando hay excesos
- Prefieres control manual

### Combinaciones Recomendadas

**Opción A: Completamente Manual**
```
auto_invoice = False
invoice_on_overage = False

→ Revisas snapshots y creas facturas manualmente
```

**Opción B: Semi-Automática (Recomendado)**
```
auto_invoice = False
invoice_on_overage = True

→ Sistema detecta overages automáticamente
→ Tú decides cuándo facturar (botón "Create Invoice")
```

**Opción C: Completamente Automática**
```
auto_invoice = True
invoice_on_overage = True

→ Sistema factura automáticamente vía subscription_package
→ Overages se detectan y facturan inmediatamente
```

---

## Ejemplos Prácticos

### Ejemplo 1: SaaS de Contabilidad

**Configuración:**
```
Pricing Model: Base + Included + Overage
Base Monthly Price: $300
Included Users: 3
Price per Additional User: $75
Price per Company: $200
Max Storage GB: 50
Price per GB: $5
```

**Escenario:**
- Cliente tiene 5 usuarios
- 1 empresa
- 55 GB de almacenamiento

**Cálculo:**
```
Base Amount: $300 (plan base)
User Amount: $150 (2 usuarios adicionales × $75)
Overage Amount: $25 (5 GB adicionales × $5)

Total: $475/mes
```

### Ejemplo 2: Platform as a Service

**Configuración:**
```
Pricing Model: Per User
Price per User: $40
Max Users: 0 (unlimited)
```

**Escenario:**
- Cliente tiene 12 usuarios

**Cálculo:**
```
Base Amount: $0
User Amount: $480 (12 usuarios × $40)
Overage Amount: $0

Total: $480/mes
```

### Ejemplo 3: Infraestructura + Uso

**Configuración:**
```
Pricing Model: Base + Per User
Base Monthly Price: $500 (infraestructura dedicada)
Price per User: $30
```

**Escenario:**
- Cliente tiene 20 usuarios

**Cálculo:**
```
Base Amount: $500 (costo fijo infraestructura)
User Amount: $600 (20 usuarios × $30)
Overage Amount: $0

Total: $1,100/mes
```

### Ejemplo 4: Freemium

**Configuración:**
```
Pricing Model: Overage Only
Included Users: 10
Price per User: $25
```

**Escenario A:** Cliente con 8 usuarios
```
Base Amount: $0
User Amount: $0 (dentro del límite)
Total: $0/mes
```

**Escenario B:** Cliente con 15 usuarios
```
Base Amount: $0
User Amount: $125 (5 usuarios adicionales × $25)
Total: $125/mes
```

---

## Migración desde Versión Anterior

### Cambios en Campos

| Campo Antiguo | Campo Nuevo | Notas |
|--------------|-------------|-------|
| `max_users` | `max_users` | Ahora es límite máximo (0 = ilimitado) |
| N/A | `included_users` | Nuevo - usuarios incluidos en base |
| N/A | `base_monthly_price` | Nuevo - precio base mensual |
| `price_per_user` | `price_per_user` | Significado cambia según modelo |
| N/A | `pricing_model` | Nuevo - selección de modelo |

### Datos Existentes

Al actualizar, todos los subscription packages existentes tendrán:
```
pricing_model = 'overage_only'  (comportamiento original)
```

Si quieres cambiar el modelo:
1. Ir a Subscriptions → Subscription Packages
2. Abrir el paquete
3. Tab "Pricing & Limits"
4. Seleccionar nuevo modelo
5. Configurar campos según modelo

---

## Campos de Facturación en License Records

Cada registro de licencia ahora tiene:

### Campos de Cálculo

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| `base_amount` | Costo base mensual | $200 |
| `user_amount` | Costo por usuarios | $150 |
| `overage_amount` | Costo adicional (companies, storage) | $25 |
| `total_amount` | **Total a facturar** | **$375** |

### Vista en Odoo

```
SaaS Management → Licensing → License Records

Tab "Billing":
  Pricing Breakdown:
    Base Amount: $200
    User Amount: $150
    Overage Amount: $25
    ─────────────────
    Total Amount: $375

  Overage Quantities:
    User Overage: 3
    Storage Overage: 5 GB
```

---

## Troubleshooting

### Problema: Total amount es $0 pero hay usuarios

**Causa**: Pricing model es "overage_only" y usuarios están dentro del límite

**Solución**: Esto es correcto. Solo se cobra cuando se excede `included_users`

### Problema: No veo base_amount en las vistas

**Causa**: Base amount es $0 (modelo "overage_only" o "per_user")

**Solución**: Los campos se ocultan automáticamente si son $0

### Problema: Quiero cambiar de modelo para un cliente existente

**Precaución**: Cambiar el modelo afecta cómo se calculan las futuras facturas

**Pasos**:
1. Crear nuevo Subscription Package con nuevo modelo
2. Migrar cliente al nuevo paquete
3. Los license records antiguos conservan su cálculo original

---

## Mejores Prácticas

### 1. Elegir el Modelo Correcto

**Overage Only**: Cuando quieres ofrecer gratis hasta cierto límite
**Base + Included + Overage**: Modelo SaaS tradicional con ingresos predecibles
**Per User**: Para máxima flexibilidad y escalabilidad
**Base + Per User**: Cuando necesitas garantizar un ingreso mínimo

### 2. Configurar Límites

```
Max Users = 0     → Ilimitado (solo para alertas)
Max Users > 0     → Límite estricto + overage billing
```

### 3. Pricing Psychology

**Bajo costo de entrada:**
→ Usa "Per User" ($0 base) o "Overage Only"

**Ingresos predecibles:**
→ Usa "Base + Included + Overage" ($200/mes base)

**Maximizar ingresos:**
→ Usa "Base + Per User" (siempre cobras base + todos los usuarios)

### 4. Nombrar los Planes

```
❌ Plan 1, Plan 2, Plan 3
✅ Startup ($0), Professional ($200), Enterprise ($500)
```

---

## FAQ

**P: ¿Puedo tener múltiples paquetes con diferentes modelos?**
R: Sí, cada Subscription Package puede tener su propio modelo de pricing.

**P: ¿Cómo desactivo la facturación automática?**
R: Desmarca `auto_invoice` y `invoice_on_overage` en el paquete.

**P: ¿Puedo cobrar diferente por usuario según el tipo de usuario?**
R: No en esta versión. Todos los usuarios internos cuentan igual. Para eso necesitarías una customización.

**P: ¿El pricing model afecta solo usuarios o también empresas/storage?**
R: Solo afecta usuarios. Companies y storage siempre se cobran como overage.

**P: ¿Puedo cambiar el modelo después de vender paquetes?**
R: Sí, pero solo afecta nuevos snapshots. Los existentes conservan su cálculo.

---

**Documentación completa**: Ver `README.md` en saas_licensing
**Soporte**: https://automateai.com.mx
