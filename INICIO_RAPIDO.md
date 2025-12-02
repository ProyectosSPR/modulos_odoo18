# 🚀 Inicio Rápido - Declaraciones Fiscales SAT

## ✅ Lo que ya está hecho

### Módulo 1: `l10n_mx_tax_declaration_base`
- ✅ 6 modelos Python (obligaciones, reglas, extensiones)
- ✅ 5 vistas XML completas
- ✅ 22+ tipos de obligaciones fiscales del SAT
- ✅ Motor de cálculo dinámico (visual + Python)
- ✅ Auto-marcado de facturas
- ✅ Sistema de seguridad multi-usuario

### Módulo 2: `l10n_mx_tax_declaration_sat_sync`
- ✅ Integración con importación SAT
- ✅ Auto-marcado al importar XML
- ✅ Botones de acción rápida
- ✅ Auto-instalación

**Total:** 24 archivos creados | 2 módulos funcionales

---

## 📦 Instalación (5 minutos)

```bash
# 1. Los módulos ya están en tu directorio
cd /home/sergio/modulos_odoo18/

# 2. Reinicia Odoo
sudo systemctl restart odoo18

# 3. En Odoo Web:
# Apps > Actualizar Lista de Aplicaciones
# Buscar: "Declaraciones Fiscales"
# Instalar
```

---

## ⚙️ Configuración Básica (10 minutos)

### Paso 1: Crear Obligación IVA
```
Menú: Declaraciones Fiscales > Obligaciones Fiscales > Crear

Tipo: IVA - Declaración Mensual
Periodicidad: Mensual
Día Límite: 17
Auto-incluir: ✓
```

### Paso 2: Crear Reglas de Cálculo

**IVA Causado:**
```
Nombre: IVA Causado
Tipo: Suma con Filtros
Campo: Impuestos
Filtro: [('move_type', '=', 'out_invoice')]
```

**IVA Acreditable:**
```
Nombre: IVA Acreditable
Tipo: Suma con Filtros
Campo: Impuestos
Filtro: [('move_type', '=', 'in_invoice')]
```

**IVA a Pagar:**
```
Nombre: IVA a Pagar
Tipo: Resta Simple
Operando 1: IVA Causado
Operando 2: IVA Acreditable
Monto Final: ✓
```

### Paso 3: Importar Facturas
```
Al importar XML del SAT:
☑ Auto-marcar para Declaración
```

---

## 🎯 Próximos 3 Módulos a Crear

### 1. Wizard de Declaraciones (2-3 días)
- Proceso paso a paso
- Selección de facturas
- Cálculos automáticos
- Generación de reporte

### 2. Conciliación Avanzada (2-3 días)
- Reglas de match automático
- Match por relaciones (SO/PO)
- Pagos sin factura

### 3. Reportes Fiscales (1-2 días)
- PDF imprimible
- Excel exportable
- Formato SAT

---

## 📖 Documentación Completa

Ver: `DECLARACIONES_FISCALES_README.md`

---

**¿Listo para continuar?** Dime cuál módulo quieres que desarrolle primero.
