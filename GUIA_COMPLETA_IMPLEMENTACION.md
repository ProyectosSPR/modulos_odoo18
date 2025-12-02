# 📘 GUÍA COMPLETA DE IMPLEMENTACIÓN
## Sistema de Declaraciones Fiscales SAT México para Odoo 18

**Versión:** 1.0.0
**Fecha:** 2025-12-02
**Autor:** IT Admin
**Odoo Version:** 18.0

---

## 📑 TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Módulos Implementados](#módulos-implementados)
4. [Instalación Paso a Paso](#instalación-paso-a-paso)
5. [Configuración Inicial](#configuración-inicial)
6. [Estructura de Archivos](#estructura-de-archivos)
7. [Modelos de Datos](#modelos-de-datos)
8. [Prompts Completos](#prompts-completos)
9. [Próximos Módulos](#próximos-módulos)
10. [Troubleshooting](#troubleshooting)
11. [Migración a Otra PC](#migración-a-otra-pc)

---

## 📊 RESUMEN EJECUTIVO

### ¿Qué es este proyecto?

Sistema completo e integrado para gestionar **declaraciones fiscales ante el SAT en México** dentro de Odoo 18. Permite a las empresas:

- Configurar sus obligaciones fiscales (IVA, ISR, IEPS, retenciones, etc.)
- Auto-marcar facturas para incluir en declaraciones
- Calcular impuestos dinámicamente con fórmulas personalizables
- Generar declaraciones paso a paso
- Conciliar pagos automáticamente
- Generar reportes fiscales imprimibles

### Estado Actual del Proyecto

| Módulo | Estado | Progreso | Archivos |
|--------|--------|----------|----------|
| l10n_mx_tax_declaration_base | ✅ Instalado | 100% | 17 archivos |
| l10n_mx_tax_declaration_sat_sync | ✅ Instalado | 100% | 7 archivos |
| l10n_mx_tax_declaration_wizard | ⏳ Pendiente | 0% | - |
| l10n_mx_auto_reconcile_enhanced | ⏳ Pendiente | 0% | - |
| l10n_mx_tax_reports | ⏳ Pendiente | 0% | - |

**Progreso Total:** 40% completado (2 de 5 módulos)

---

## 🏗️ ARQUITECTURA DEL SISTEMA

### Diagrama de Módulos

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│              SISTEMA DE DECLARACIONES FISCALES                  │
│                                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌───────────────┐  ┌─────────────┐  ┌──────────────┐
│   MÓDULO 1    │  │  MÓDULO 2   │  │  MÓDULO 3    │
│     BASE      │◄─┤ SAT SYNC    │  │   WIZARD     │
│   ✅ HECHO    │  │ ✅ HECHO     │  │ ⏳ PENDIENTE  │
└───────┬───────┘  └─────────────┘  └──────┬───────┘
        │                                   │
        │         ┌─────────────┐          │
        └─────────┤  MÓDULO 4   ├──────────┘
                  │CONCILIACIÓN │
                  │⏳ PENDIENTE  │
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │  MÓDULO 5   │
                  │  REPORTES   │
                  │⏳ PENDIENTE  │
                  └─────────────┘
```

### Flujo de Datos

```
1. IMPORTACIÓN SAT
   └─> Facturas XML del SAT
       └─> Auto-marcado para declaración
           └─> Campo: include_in_tax_declaration = True

2. CONFIGURACIÓN
   └─> Obligaciones fiscales por empresa
       └─> Reglas de cálculo dinámicas
           └─> Fórmulas personalizadas

3. DECLARACIÓN (cuando se implemente)
   └─> Wizard paso a paso
       └─> Selección de facturas
           └─> Conciliación bancaria
               └─> Cálculos automáticos
                   └─> Reporte final
```

---

## ✅ MÓDULOS IMPLEMENTADOS

### Módulo 1: l10n_mx_tax_declaration_base

**Ubicación:** `/home/sergio/modulos_odoo18/l10n_mx_tax_declaration_base/`

**Propósito:** Infraestructura base para declaraciones fiscales

**Componentes:**

#### 📁 Modelos Python (6 archivos)

1. **mx_tax_obligation_type.py**
   - Catálogo de tipos de obligaciones fiscales
   - 22+ obligaciones pre-configuradas
   - Categorías: IVA, ISR, IEPS, Retenciones, etc.

2. **mx_tax_periodicity.py**
   - Catálogo de periodicidades
   - 10 periodicidades (mensual, bimestral, trimestral, etc.)

3. **mx_tax_obligation.py**
   - Configuración de obligaciones por empresa
   - Auto-marcado de facturas
   - Filtros por tipo de factura
   - Día límite de pago

4. **mx_tax_calculation_rule.py**
   - Motor de cálculo dinámico
   - 6 tipos de operaciones:
     * Suma simple
     * Resta simple
     * Suma con filtros (dominio Odoo)
     * Resta con filtros
     * Operaciones matemáticas (×, ÷, %)
     * Fórmulas Python (safe_eval)

5. **account_move.py**
   - Extensión de facturas
   - Nuevos campos:
     * include_in_tax_declaration
     * tax_declaration_status
     * tax_declaration_period
     * tax_declaration_month/year
     * tax_declaration_notes

6. **res_company.py**
   - Extensión de compañía
   - Relación a obligaciones fiscales
   - Configuración general

#### 📁 Vistas XML (5 archivos)

1. **menu_views.xml**
   - Menú principal "Declaraciones Fiscales"
   - Submenús de configuración

2. **mx_tax_obligation_views.xml**
   - Vistas list, form, kanban, search
   - Acciones y menús

3. **mx_tax_calculation_rule_views.xml**
   - Vistas de reglas de cálculo
   - Editor de fórmulas
   - Configuración de filtros

4. **account_move_views.xml**
   - Extensión de facturas
   - Tab "Declaración Fiscal"
   - Filtros de búsqueda
   - Campos en lista

5. **res_company_views.xml**
   - Extensión de compañía
   - Tab de configuración fiscal

#### 📁 Datos (2 archivos)

1. **mx_tax_periodicity_data.xml**
   - 10 registros de periodicidades

2. **mx_tax_obligation_type_data.xml**
   - 22+ tipos de obligaciones:
     * IVA-01: IVA Mensual
     * IVA-02: IVA Trimestral (RESICO)
     * ISR-PM-01: ISR Pagos Provisionales PM
     * ISR-PM-02: ISR Anual PM
     * ISR-PF-01: ISR Pagos Provisionales PF
     * ISR-PF-02: ISR Anual PF
     * IEPS-01, 02, 03, 04: IEPS varios
     * RET-ISR-01, 02, 03, 04: Retenciones ISR
     * RET-IVA-01: Retención IVA
     * DIOT-01: DIOT
     * Y más...

#### 📁 Seguridad (2 archivos)

1. **security.xml**
   - 3 grupos de usuarios:
     * Usuario: Ver declaraciones
     * Contador: Crear declaraciones
     * Manager: Configurar obligaciones
   - Reglas multi-compañía

2. **ir.model.access.csv**
   - Permisos de acceso por grupo
   - 12 reglas de acceso

---

### Módulo 2: l10n_mx_tax_declaration_sat_sync

**Ubicación:** `/home/sergio/modulos_odoo18/l10n_mx_tax_declaration_sat_sync/`

**Propósito:** Integración con importación de facturas SAT

**Componentes:**

#### 📁 Modelos Python (2 archivos)

1. **cfdi_invoice_attachment.py**
   - Extensión del wizard de importación
   - Método `import_xml_file()` override
   - Auto-marcado después de importar
   - Nuevos campos:
     * auto_mark_for_declaration
     * tax_declaration_period

2. **ir_attachment.py**
   - Extensión de attachments XML
   - Acción manual para marcar facturas
   - Campo: auto_mark_for_tax_declaration

#### 📁 Vistas XML (2 archivos)

1. **cfdi_invoice_views.xml**
   - Extensión del wizard de importación
   - Grupo "Configuración de Declaraciones Fiscales"

2. **ir_attachment_views.xml**
   - Botón "Marcar para Declaración" en attachments
   - Campos adicionales

**Dependencias:**
- l10n_mx_tax_declaration_base
- l10n_mx_sat_sync_itadmin

**Auto-instalación:** Sí

---

## 🚀 INSTALACIÓN PASO A PASO

### Pre-requisitos

```bash
# Sistema operativo
Ubuntu 20.04+ / Debian 11+

# Odoo 18 instalado
# Python 3.10+
# PostgreSQL 14+

# Módulos Odoo requeridos:
- account (core)
- l10n_mx (core)
- l10n_mx_sat_sync_itadmin (custom)
```

### Paso 1: Copiar Módulos

```bash
# Los módulos deben estar en tu directorio de addons
# Ruta típica: /mnt/extra-addons/modulos_odoo18/

# Verificar que existan:
ls -la /home/sergio/modulos_odoo18/l10n_mx_tax_declaration_base/
ls -la /home/sergio/modulos_odoo18/l10n_mx_tax_declaration_sat_sync/

# Estructura esperada:
modulos_odoo18/
├── l10n_mx_tax_declaration_base/
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── models/
│   ├── views/
│   ├── data/
│   ├── security/
│   └── static/
└── l10n_mx_tax_declaration_sat_sync/
    ├── __init__.py
    ├── __manifest__.py
    ├── models/
    ├── views/
    └── security/
```

### Paso 2: Reiniciar Odoo

```bash
# Opción 1: Si tienes systemd
sudo systemctl restart odoo18

# Opción 2: Si usas otro método
# Detener y reiniciar según tu configuración

# Verificar que esté corriendo
sudo systemctl status odoo18
```

### Paso 3: Actualizar Lista de Aplicaciones

En Odoo Web:
1. Ir a **Apps** (Aplicaciones)
2. Clic en el menú de 3 puntos (⋮)
3. Seleccionar **"Update Apps List"** (Actualizar Lista de Aplicaciones)
4. Confirmar

### Paso 4: Instalar Módulo Base

1. En **Apps**, buscar: `declaraciones fiscales`
2. Encontrarás: **"México - Declaraciones Fiscales SAT (Base)"**
3. Clic en **"Install"** (Instalar)
4. Esperar a que termine (puede tomar 1-2 minutos)

**Si hay errores**, ver sección [Troubleshooting](#troubleshooting)

### Paso 5: Instalar Módulo de Integración

Debería instalarse automáticamente junto con el módulo base si tienes `l10n_mx_sat_sync_itadmin` instalado.

Si no:
1. En **Apps**, buscar: `sat sync integration`
2. Clic en **"Install"**

### Paso 6: Verificar Instalación

```bash
# En Odoo Web, verificar que aparezcan:

1. Menú principal: "Declaraciones Fiscales"
   ├── Obligaciones Fiscales
   ├── Reglas de Cálculo
   └── Configuración
       ├── Tipos de Obligación
       └── Periodicidades

2. En Contabilidad > Facturas:
   - Nuevo tab: "Declaración Fiscal"
   - Nuevos filtros de búsqueda

3. En importación de facturas SAT:
   - Nuevo grupo: "Configuración de Declaraciones Fiscales"
```

---

## ⚙️ CONFIGURACIÓN INICIAL

### Configuración Básica (15 minutos)

#### 1. Configurar Obligación IVA Mensual

```
Menú: Declaraciones Fiscales > Obligaciones Fiscales > Crear

Campos a llenar:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tipo de Obligación:     IVA - Declaración Mensual
Periodicidad:           Mensual
Día Límite de Pago:     17
Auto-incluir Facturas:  ✓ (activado)
Filtro de Tipo:         Todas
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Guardar
```

#### 2. Crear Reglas de Cálculo para IVA

**Regla 1: IVA Causado (Facturas de Cliente)**

```
Menú: Declaraciones Fiscales > Reglas de Cálculo > Crear

Campos:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nombre:                 IVA Causado
Obligación:             IVA - Declaración Mensual
Secuencia:              10
Tipo de Cálculo:        Suma con Filtros
Modelo Origen:          Facturas
Campo a Sumar:          Impuestos
Filtro (Dominio):       [('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]
Es Subtotal:            ✓
Mostrar en Reporte:     ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Descripción:
"Suma de todos los impuestos (IVA) de las facturas de cliente
confirmadas en el período fiscal"

Guardar
```

**Regla 2: IVA Acreditable (Facturas de Proveedor)**

```
Crear nueva regla:

Campos:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nombre:                 IVA Acreditable
Obligación:             IVA - Declaración Mensual
Secuencia:              20
Tipo de Cálculo:        Suma con Filtros
Modelo Origen:          Facturas
Campo a Sumar:          Impuestos
Filtro (Dominio):       [('move_type', '=', 'in_invoice'), ('state', '=', 'posted')]
Es Subtotal:            ✓
Mostrar en Reporte:     ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Descripción:
"Suma de todos los impuestos (IVA) de las facturas de proveedor
que pueden acreditarse"

Guardar
```

**Regla 3: IVA a Pagar (Cálculo Final)**

```
Crear nueva regla:

Campos:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nombre:                 IVA a Pagar
Obligación:             IVA - Declaración Mensual
Secuencia:              30
Tipo de Cálculo:        Resta Simple
Operando 1:             IVA Causado
Operando 2:             IVA Acreditable
Es Monto Final:         ✓
Mostrar en Reporte:     ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Descripción:
"Monto final de IVA a pagar al SAT = IVA Causado - IVA Acreditable"

Guardar
```

#### 3. Configurar Auto-marcado en Importación

```
Cuando importes facturas del SAT:

Wizard de Importación:
┌─────────────────────────────────────────┐
│ Configuración de Declaraciones Fiscales │
├─────────────────────────────────────────┤
│ ☑ Auto-marcar para Declaración         │
│ Período Fiscal: [dejar vacío]          │
│   (usará la fecha de la factura)        │
└─────────────────────────────────────────┘

Importar
```

#### 4. Verificar que Funciona

```bash
# Después de importar facturas:

1. Ir a: Contabilidad > Facturas
2. Abrir cualquier factura importada
3. Verificar tab "Declaración Fiscal":
   ✓ Incluir en Declaración: Sí
   ✓ Estado: Pendiente de Declarar
   ✓ Período Fiscal: [fecha de la factura]

4. Usar filtros:
   - Buscar > "Para Declarar"
   - Debería mostrar facturas marcadas
```

---

## 📂 ESTRUCTURA DE ARCHIVOS COMPLETA

### l10n_mx_tax_declaration_base/

```
l10n_mx_tax_declaration_base/
│
├── __init__.py                          # Inicialización del módulo
├── __manifest__.py                      # Manifest con dependencias y datos
│
├── models/                              # Modelos Python
│   ├── __init__.py
│   ├── mx_tax_obligation_type.py        # Catálogo tipos de obligación
│   ├── mx_tax_periodicity.py            # Catálogo periodicidades
│   ├── mx_tax_obligation.py             # Obligaciones por empresa
│   ├── mx_tax_calculation_rule.py       # Motor de cálculo dinámico
│   ├── account_move.py                  # Extensión de facturas
│   └── res_company.py                   # Extensión de compañía
│
├── views/                               # Vistas XML
│   ├── menu_views.xml                   # Menús principales
│   ├── mx_tax_obligation_views.xml      # Vistas de obligaciones
│   ├── mx_tax_calculation_rule_views.xml # Vistas de reglas
│   ├── account_move_views.xml           # Extensión facturas
│   └── res_company_views.xml            # Extensión compañía
│
├── data/                                # Datos iniciales
│   ├── mx_tax_periodicity_data.xml      # 10 periodicidades
│   └── mx_tax_obligation_type_data.xml  # 22+ tipos obligaciones
│
├── security/                            # Seguridad
│   ├── security.xml                     # Grupos y reglas
│   └── ir.model.access.csv              # Permisos de acceso
│
└── static/                              # Recursos estáticos
    └── description/
        ├── icon.png                     # Icono del módulo
        └── index.html                   # Descripción HTML
```

### l10n_mx_tax_declaration_sat_sync/

```
l10n_mx_tax_declaration_sat_sync/
│
├── __init__.py
├── __manifest__.py
│
├── models/
│   ├── __init__.py
│   ├── cfdi_invoice_attachment.py       # Extensión wizard importación
│   └── ir_attachment.py                 # Extensión attachments
│
├── views/
│   ├── cfdi_invoice_views.xml           # Extensión wizard
│   └── ir_attachment_views.xml          # Extensión attachments
│
└── security/
    └── ir.model.access.csv              # Permisos (vacío)
```

---

## 💾 MODELOS DE DATOS

### Diagrama ER (Entity-Relationship)

```
┌─────────────────────────┐
│  res.company            │
│  (Odoo Core)            │
└───────┬─────────────────┘
        │ 1
        │
        │ N
┌───────▼─────────────────┐
│  mx.tax.obligation      │
│  ━━━━━━━━━━━━━━━━━━━━━  │
│  - company_id           │
│  - obligation_type_id   │─────┐
│  - periodicity_id       │     │
│  - deadline_day         │     │
│  - auto_include_invoices│     │
└───────┬─────────────────┘     │
        │ 1                     │
        │                       │ N
        │ N              ┌──────▼──────────────────┐
┌───────▼──────────────┐ │ mx.tax.obligation.type  │
│ mx.tax.calculation.  │ │ ━━━━━━━━━━━━━━━━━━━━━━  │
│ rule                 │ │ - name                  │
│ ━━━━━━━━━━━━━━━━━━━  │ │ - code                  │
│ - obligation_id      │ │ - category              │
│ - calculation_type   │ │ - default_periodicity_id│─┐
│ - domain_filter      │ └─────────────────────────┘ │
│ - python_formula     │                             │
│ - operand_1          │                             │
│ - operand_2          │                             │ N
│ - is_final_amount    │                   ┌─────────▼────────┐
└──────────────────────┘                   │ mx.tax.periodicity│
                                           │ ━━━━━━━━━━━━━━━━  │
┌─────────────────────────┐               │ - code            │
│  account.move           │               │ - months          │
│  (Odoo Core Extended)   │               └───────────────────┘
│  ━━━━━━━━━━━━━━━━━━━━━  │
│  + include_in_tax_declaration
│  + tax_declaration_status
│  + tax_declaration_period
│  + tax_declaration_month
│  + tax_declaration_year
│  + tax_declaration_notes
└─────────────────────────┘
```

### Campos Principales por Modelo

#### mx.tax.obligation.type

| Campo | Tipo | Descripción |
|-------|------|-------------|
| name | Char | Nombre del tipo de obligación |
| code | Char | Código SAT oficial |
| category | Selection | Categoría (iva, isr, ieps, etc.) |
| sequence | Integer | Orden de visualización |
| default_periodicity_id | Many2one | Periodicidad típica |
| requires_electronic_accounting | Boolean | Requiere contabilidad electrónica |
| has_complement | Boolean | Tiene complemento XML |

#### mx.tax.periodicity

| Campo | Tipo | Descripción |
|-------|------|-------------|
| name | Char | Nombre de la periodicidad |
| code | Selection | Código (01-10) |
| months | Integer | Número de meses |
| sequence | Integer | Orden |

#### mx.tax.obligation

| Campo | Tipo | Descripción |
|-------|------|-------------|
| name | Char | Nombre (computed) |
| company_id | Many2one | Compañía |
| obligation_type_id | Many2one | Tipo de obligación |
| periodicity_id | Many2one | Periodicidad |
| deadline_day | Integer | Día límite de pago |
| auto_include_invoices | Boolean | Auto-marcar facturas |
| invoice_type_filter | Selection | Filtro de tipo de factura |
| calculation_rule_ids | One2many | Reglas de cálculo |

#### mx.tax.calculation.rule

| Campo | Tipo | Descripción |
|-------|------|-------------|
| name | Char | Nombre de la regla |
| obligation_id | Many2one | Obligación fiscal |
| sequence | Integer | Orden de ejecución |
| calculation_type | Selection | Tipo de cálculo |
| source_model | Selection | Modelo origen (facturas/pagos) |
| field_to_sum | Selection | Campo a sumar |
| domain_filter | Text | Filtro tipo dominio Odoo |
| python_formula | Text | Fórmula Python personalizada |
| operand_1 | Many2one | Operando 1 (otra regla) |
| operand_2 | Many2one | Operando 2 (otra regla) |
| operand_value | Float | Valor fijo |
| is_subtotal | Boolean | Es subtotal |
| is_final_amount | Boolean | Es monto final a pagar |
| show_in_report | Boolean | Mostrar en reporte |

#### account.move (extensión)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| include_in_tax_declaration | Boolean | Incluir en declaración |
| tax_declaration_status | Selection | Estado (pending/included/excluded/declared) |
| tax_declaration_period | Date | Período fiscal |
| tax_declaration_month | Integer | Mes fiscal (computed) |
| tax_declaration_year | Integer | Año fiscal (computed) |
| tax_declaration_notes | Text | Notas fiscales |

---

## 📝 PROMPTS COMPLETOS

### Prompt Original del Proyecto

```
Tengo estos módulos de Odoo: cdfi_invoice, account_reconcile_model_oca,
account_reconcile_oca, l10n_mx_sat_sync_itadmin. Son un conjunto de
facturación. Quiero hacer un módulo para poder generar declaraciones
fiscales ante el SAT en México.

El sistema debe:

1. IMPORTACIÓN Y MARCADO
   - Al importar facturas del SAT, poder marcar si esa factura va a ser
     parte de una declaración
   - Sistema de auto-marcado configurable

2. CONFIGURACIÓN DE OBLIGACIONES
   - Cada empresa puede tener distintas responsabilidades de declaración
   - Configurar si declara IVA, ISR, etc.
   - Cada empresa puede tener distintas obligaciones

3. MOTOR DE CÁLCULO DINÁMICO
   - El sistema debe poder hacer cálculos de manera dinámica
   - El contador debe poder crear las declaraciones con funciones
     matemáticas que él pueda programar
   - Sistema de sumas, subtotales, multiplicaciones, divisiones
   - Filtros de Odoo
   - Algo dinámico que se pueda configurar

4. PROCESO GUIADO
   - Botón "Iniciar Declaración" que empiece un recorrido paso a paso:
     a. Seleccionar facturas a declarar (las marcadas)
     b. Hacer conciliación bancaria
     c. Gestionar pagos no deducibles
     d. Generar reporte imprimible

5. CONCILIACIÓN AVANZADA
   - Conciliar automáticamente cruzando campos específicos
   - Factura.campo = Pago.campo
   - Con opciones: equals, contains, like
   - También por relaciones de órdenes de compra/venta
   - Ejemplo: pago tiene ref con ID, factura no tiene ese ID pero está
     compuesta por 30 órdenes de venta, y en esas órdenes sí está ese ID

6. PAGOS NO DEDUCIBLES
   - Pagos que no se pudieron ligar porque se pagaron sin factura
   - Marcar si es deducible o no deducible

7. REPORTE FINAL
   - Al terminar cada paso, generar reporte imprimible
   - Mostrar cuánto se tiene que pagar de cada impuesto
   - Por cada responsabilidad de cada empresa
```

### Prompt para Continuar en Otra PC

```
Estoy continuando el proyecto de Sistema de Declaraciones Fiscales SAT
México para Odoo 18.

ESTADO ACTUAL:
- ✅ Módulo base implementado (l10n_mx_tax_declaration_base)
- ✅ Módulo integración SAT implementado (l10n_mx_tax_declaration_sat_sync)
- ⏳ Pendiente: Wizard de declaraciones
- ⏳ Pendiente: Conciliación avanzada
- ⏳ Pendiente: Reportes fiscales

UBICACIÓN DE ARCHIVOS:
/home/sergio/modulos_odoo18/l10n_mx_tax_declaration_base/
/home/sergio/modulos_odoo18/l10n_mx_tax_declaration_sat_sync/

DOCUMENTACIÓN COMPLETA:
Ver archivo: GUIA_COMPLETA_IMPLEMENTACION.md

SIGUIENTE PASO:
Crear el módulo l10n_mx_tax_declaration_wizard que implemente:

1. Wizard multi-paso (TransientModel)
   Estados: step1_config, step2_invoices, step3_reconcile,
            step4_non_deductible, step5_calculate, step6_report

2. Modelo de declaración final (Model)
   - mx.tax.declaration (cabecera)
   - mx.tax.declaration.line (líneas de facturas)
   - mx.tax.declaration.calculation (resultados)

3. Flujo del wizard:
   - Paso 1: Seleccionar período y obligaciones
   - Paso 2: Seleccionar facturas marcadas
   - Paso 3: Mostrar estado de conciliación
   - Paso 4: Clasificar pagos no deducibles
   - Paso 5: Ejecutar reglas de cálculo
   - Paso 6: Mostrar resumen y generar reporte

4. Integración con módulos existentes:
   - Usar campo include_in_tax_declaration de account.move
   - Ejecutar método calculate() de mx.tax.calculation.rule
   - Crear registros mx.tax.declaration

TECNOLOGÍAS:
- Odoo 18
- Python 3.10+
- PostgreSQL
- XML para vistas

CONVENCIONES:
- Usar "list" en lugar de "tree" para vistas (Odoo 18)
- Prefijos de módulo en external IDs
- safe_eval para fórmulas Python
- Grupos de seguridad heredados del módulo base

¿Puedes crear el módulo l10n_mx_tax_declaration_wizard con toda su
estructura, modelos, vistas y lógica de negocio?
```

### Prompt para Módulo de Conciliación

```
Necesito crear el módulo l10n_mx_auto_reconcile_enhanced para el
Sistema de Declaraciones Fiscales SAT México.

CONTEXTO:
- Proyecto existente en /home/sergio/modulos_odoo18/
- Odoo 18
- Ver GUIA_COMPLETA_IMPLEMENTACION.md para detalles

OBJETIVO:
Sistema de conciliación automática avanzada que permita:

1. Reglas de match directo:
   - Campo factura = Campo pago
   - Tipos de match: equals, contains, like, in
   - Case sensitive/insensitive

2. Reglas por relación:
   - Match a través de Sale Orders/Purchase Orders
   - Ejemplo: pago.ref → sale.order.client_order_ref → invoice_ids
   - Configuración de rutas de relación

3. Clasificación de pagos sin factura:
   - Campo is_deductible en account.payment
   - Razón: with_invoice, without_invoice_deductible,
            without_invoice_non_deductible

4. Modelos a crear:
   - mx.reconcile.rule (reglas directas)
   - mx.reconcile.relation.rule (reglas por relación)

5. Algoritmo de conciliación:
   - Ordenar reglas por secuencia
   - Match único → conciliar automáticamente
   - Múltiples matches → marcar para revisión manual
   - Sin match → siguiente regla

DEPENDENCIAS:
- l10n_mx_tax_declaration_base
- account_reconcile_oca
- account_reconcile_model_oca

¿Puedes crear este módulo completo?
```

---

## 🔄 PRÓXIMOS MÓDULOS

### Módulo 3: l10n_mx_tax_declaration_wizard

**Estado:** ⏳ Pendiente
**Prioridad:** Alta
**Tiempo estimado:** 2-3 horas

**Componentes a implementar:**

```python
# Modelos
- mx.tax.declaration.wizard (TransientModel)
- mx.tax.declaration (Model)
- mx.tax.declaration.line (Model)
- mx.tax.declaration.calculation (Model)

# Estados del wizard
1. step1_config: Configuración inicial
2. step2_invoices: Selección de facturas
3. step3_reconcile: Conciliación bancaria
4. step4_non_deductible: Pagos sin factura
5. step5_calculate: Cálculos
6. step6_report: Reporte final

# Métodos principales
- action_next_step()
- action_previous_step()
- action_validate_and_create()
- _execute_calculations()
- _generate_report()
```

**Vistas:**
- Wizard form view (multi-estado)
- Declaración list/form views
- Acción en menú "Iniciar Declaración"

---

### Módulo 4: l10n_mx_auto_reconcile_enhanced

**Estado:** ⏳ Pendiente
**Prioridad:** Alta
**Tiempo estimado:** 2-3 horas

**Componentes a implementar:**

```python
# Modelos
- mx.reconcile.rule
  * source_field
  * target_field
  * match_type (equals/contains/like/in)
  * case_sensitive

- mx.reconcile.relation.rule
  * payment_field
  * relation_model (sale.order/purchase.order)
  * relation_field
  * invoice_relation_field

# Extensiones
- account.payment
  * is_deductible
  * deductible_reason
  * reconcile_rule_id

# Métodos principales
- auto_reconcile(invoices, payments)
- _apply_direct_rules()
- _apply_relation_rules()
- _mark_non_deductible()
```

---

### Módulo 5: l10n_mx_tax_reports

**Estado:** ⏳ Pendiente
**Prioridad:** Media
**Tiempo estimado:** 1-2 horas

**Componentes a implementar:**

```python
# Reportes QWeb
- report_tax_declaration (PDF principal)
- report_invoice_list (Lista de facturas)
- report_reconciliation (Conciliaciones)
- report_non_deductible (Pagos no deducibles)

# Exports
- Excel export con xlsxwriter
- XML SAT (si aplica)

# Métodos
- generate_pdf()
- export_to_excel()
- send_by_email()
```

---

## 🔧 TROUBLESHOOTING

### Error: "External ID not found"

**Síntoma:**
```
ValueError: External ID not found in the system:
l10n_mx_tax_declaration_base.group_mx_tax_declaration_user
```

**Solución:**
1. Verificar orden de carga en `__manifest__.py`
2. `security.xml` debe cargarse ANTES de `ir.model.access.csv`

```python
'data': [
    'security/security.xml',          # ← PRIMERO
    'security/ir.model.access.csv',   # ← DESPUÉS
    # ... resto de archivos
],
```

---

### Error: "El elemento xpath no se puede localizar"

**Síntoma:**
```
El elemento "<xpath expr="//field[@name='state']">" no se puede
localizar en la vista principal
```

**Solución:**
Usar xpaths más genéricos:

```xml
<!-- ❌ MAL -->
<xpath expr="//field[@name='state']" position="after">

<!-- ✅ BIEN -->
<xpath expr="//list" position="inside">
```

---

### Error: Módulo no aparece en Apps

**Solución:**
1. Verificar que el módulo esté en el addons_path
2. Reiniciar Odoo: `sudo systemctl restart odoo18`
3. Actualizar lista: Apps > ⋮ > Update Apps List
4. Buscar nuevamente

---

### Error: Permisos de acceso

**Síntoma:**
```
AccessError: No tienes permisos para acceder a este modelo
```

**Solución:**
1. Verificar que el usuario tenga el grupo correcto
2. Ir a: Settings > Users & Companies > Users
3. Editar usuario
4. Tab "Access Rights"
5. Buscar: "Declaraciones Fiscales México"
6. Asignar grupo apropiado

---

### Error: Reglas de cálculo no funcionan

**Problema:** Las reglas no calculan correctamente

**Checklist:**
```
☐ Verificar que la obligación esté activa
☐ Verificar que las reglas tengan secuencia correcta
☐ Verificar que el dominio_filter sea válido
☐ Probar la fórmula Python en modo debug
☐ Verificar que haya facturas en el período
☐ Verificar que las facturas estén marcadas: include_in_tax_declaration=True
```

---

## 💻 MIGRACIÓN A OTRA PC

### Opción 1: Copia Manual

```bash
# En PC origen:
cd /home/sergio/modulos_odoo18/
tar -czf declaraciones_fiscales.tar.gz \
    l10n_mx_tax_declaration_base/ \
    l10n_mx_tax_declaration_sat_sync/ \
    *.md

# Transferir archivo a PC destino (usar scp, rsync, USB, etc.)

# En PC destino:
cd /ruta/a/tu/addons/
tar -xzf declaraciones_fiscales.tar.gz

# Reiniciar Odoo
sudo systemctl restart odoo

# Actualizar Apps > Install
```

---

### Opción 2: Git Repository

```bash
# En PC origen - Inicializar repositorio
cd /home/sergio/modulos_odoo18/
git init
git add l10n_mx_tax_declaration_base/
git add l10n_mx_tax_declaration_sat_sync/
git add *.md
git commit -m "Sistema de Declaraciones Fiscales SAT - v1.0"

# Subir a GitHub/GitLab/Bitbucket
git remote add origin <tu-repo-url>
git push -u origin main

# En PC destino - Clonar
cd /ruta/a/tu/addons/
git clone <tu-repo-url>

# Reiniciar e instalar
sudo systemctl restart odoo
```

---

### Opción 3: Exportar desde Odoo (no recomendado)

Odoo no tiene función nativa para exportar módulos ya instalados.
Mejor usar opciones 1 o 2.

---

## 📋 CHECKLIST DE MIGRACIÓN

```
PRE-MIGRACIÓN (PC Origen)
☐ Hacer backup de la base de datos
☐ Exportar módulos con tar o git
☐ Copiar documentación (.md files)
☐ Anotar versión de Odoo
☐ Anotar dependencias instaladas

TRANSFERENCIA
☐ Copiar archivos a PC destino
☐ Verificar integridad (checksums)

POST-MIGRACIÓN (PC Destino)
☐ Colocar módulos en addons_path
☐ Verificar permisos de archivos
☐ Reiniciar Odoo
☐ Actualizar lista de apps
☐ Instalar módulos en orden:
   1. l10n_mx_tax_declaration_base
   2. l10n_mx_tax_declaration_sat_sync
☐ Verificar que funcionan correctamente
☐ Importar datos de prueba
☐ Probar configuración básica

VERIFICACIÓN
☐ Menú "Declaraciones Fiscales" visible
☐ Crear obligación de prueba
☐ Crear regla de cálculo de prueba
☐ Importar factura y verificar auto-marcado
☐ Revisar logs de errores
```

---

## 📚 RECURSOS ADICIONALES

### Archivos de Documentación

```
/home/sergio/modulos_odoo18/
├── GUIA_COMPLETA_IMPLEMENTACION.md      ← Este archivo
├── DECLARACIONES_FISCALES_README.md     ← Documentación general
└── INICIO_RAPIDO.md                     ← Guía rápida
```

### Comandos Útiles

```bash
# Ver logs de Odoo en tiempo real
tail -f /var/log/odoo/odoo.log

# Buscar errores recientes
grep -i error /var/log/odoo/odoo.log | tail -20

# Verificar módulos instalados (desde Python)
psql -U odoo -d nombre_db -c \
  "SELECT name, state FROM ir_module_module
   WHERE name LIKE '%tax_declaration%';"

# Limpiar assets cache
# Ir a: Settings > Activate Developer Mode
# Settings > Technical > Views > Clear Assets Cache

# Reiniciar Odoo forzado
sudo systemctl stop odoo
sudo systemctl start odoo
sudo systemctl status odoo
```

### Modo Debug en Odoo

```
# Activar Developer Mode
Settings > Activate the developer mode

# Con developer mode activo:
- Ver IDs de registros
- Ver external IDs
- Ver estructura de vistas
- Editar vistas directo
- Ver campos técnicos
```

---

## 🎓 CONCEPTOS TÉCNICOS

### Dominios de Odoo

Los dominios se usan en `domain_filter` de las reglas de cálculo:

```python
# Ejemplos de dominios válidos:

# Facturas de cliente confirmadas
[('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]

# Facturas del último mes
[('invoice_date', '>=', '2025-01-01'),
 ('invoice_date', '<=', '2025-01-31')]

# Facturas de un partner específico
[('partner_id', '=', 123)]

# Facturas con monto mayor a 10000
[('amount_total', '>', 10000)]

# Combinaciones con OR
['|', ('state', '=', 'posted'), ('state', '=', 'draft')]

# NOT
[('state', '!=', 'cancel')]
```

### Safe Eval en Fórmulas Python

Variables disponibles en `python_formula`:

```python
# Ejemplo de fórmula válida:

# Sumar todos los montos sin impuestos
sum(inv.amount_untaxed for inv in invoices)

# Filtrar y sumar
sum(inv.amount_total for inv in invoices
    if inv.move_type == 'out_invoice')

# Usar resultados de otras reglas
rules[regla_id] * 0.16  # IVA 16%

# Operaciones complejas
total = sum(invoices.mapped('amount_untaxed'))
iva = total * 0.16
total + iva

# Funciones disponibles:
# sum, len, abs, min, max, round
```

---

## 📞 SOPORTE Y CONTACTO

### Para Problemas Técnicos

1. Revisar sección [Troubleshooting](#troubleshooting)
2. Revisar logs: `/var/log/odoo/odoo.log`
3. Activar modo debug en Odoo
4. Buscar el error en Google/Stack Overflow
5. Consultar documentación oficial de Odoo 18

### Para Continuar Desarrollo

1. Leer esta guía completa
2. Revisar código existente de los módulos
3. Seguir convenciones establecidas
4. Usar los prompts proporcionados
5. Documentar nuevos cambios

---

## 📄 LICENCIA Y CRÉDITOS

**Licencia:** OPL-1 (Odoo Proprietary License)
**Autor:** IT Admin
**Website:** www.itadmin.com.mx
**Versión Odoo:** 18.0
**Fecha:** 2025-12-02

---

## 📝 HISTORIAL DE CAMBIOS

### v1.0.0 - 2025-12-02
- ✅ Módulo base implementado
- ✅ Módulo integración SAT implementado
- ✅ 22+ obligaciones fiscales configuradas
- ✅ Motor de cálculo dinámico funcional
- ✅ Auto-marcado de facturas activo
- ✅ Sistema de seguridad implementado
- ⏳ Wizard de declaraciones pendiente
- ⏳ Conciliación avanzada pendiente
- ⏳ Reportes fiscales pendientes

---

## ✅ CHECKLIST FINAL

```
ANTES DE MIGRAR
☐ Leer toda esta guía
☐ Entender la arquitectura
☐ Revisar código de módulos existentes
☐ Hacer backup de datos importantes
☐ Tener acceso a PC destino

DURANTE LA MIGRACIÓN
☐ Copiar todos los archivos
☐ Copiar toda la documentación
☐ Verificar versión de Odoo compatible
☐ Instalar dependencias necesarias

DESPUÉS DE LA MIGRACIÓN
☐ Reiniciar Odoo
☐ Instalar módulos en orden correcto
☐ Verificar funcionamiento básico
☐ Probar configuración de prueba
☐ Revisar que no haya errores

PARA CONTINUAR DESARROLLO
☐ Tener clara la siguiente tarea
☐ Revisar prompts proporcionados
☐ Seguir convenciones de código
☐ Documentar cambios nuevos
☐ Hacer commits regulares si usas Git
```

---

**FIN DE LA GUÍA**

Esta guía contiene toda la información necesaria para:
- ✅ Entender el proyecto completo
- ✅ Instalar los módulos existentes
- ✅ Configurar el sistema básico
- ✅ Migrar a otra PC
- ✅ Continuar el desarrollo
- ✅ Resolver problemas comunes

**Última actualización:** 2025-12-02 06:30 GMT
**Versión del documento:** 1.0.0
