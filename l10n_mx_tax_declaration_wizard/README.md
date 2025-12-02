# Wizard de Declaraciones Fiscales SAT México

## Descripción

Wizard multi-paso para crear declaraciones fiscales ante el SAT de manera guiada y sencilla.

## Características

### ✅ Wizard Guiado en 6 Pasos

1. **Configuración**: Selección de período y obligaciones fiscales
2. **Facturas**: Revisión y selección de facturas a incluir
3. **Conciliación**: Integración con conciliación bancaria (opcional)
4. **Cálculos**: Ejecución automática de reglas de cálculo
5. **Revisión**: Validación de resultados antes de guardar
6. **Completado**: Generación de declaración permanente

### 📊 Modelo de Declaración Permanente

- **Estados**: Borrador → Calculado → Revisado → Presentado → Pagado
- **Seguimiento**: Con Chatter (mail.thread) y actividades
- **Líneas de facturas**: Detalle de todas las facturas incluidas
- **Resultados de cálculos**: Almacenamiento de todos los cálculos ejecutados
- **Fechas importantes**: Fecha límite, presentación y pago
- **Multi-compañía**: Soporte completo

### 🔐 Seguridad

- **Grupos de usuario**:
  - Usuario de Declaraciones: Ver y usar wizard
  - Contador/Manager: Crear, editar y eliminar
- **Reglas de registro**: Por compañía
- **Permisos**: Configurables por grupo

### 🎨 Vistas

- **List**: Con decoradores por estado
- **Form**: Completo con notebook (Facturas, Cálculos, Totales, Reportes, Notas)
- **Kanban**: Agrupado por estado
- **Search**: Con filtros rápidos (vencidas, por vencer, etc.)

### 📋 Menús

```
Declaraciones Fiscales
├── Declaraciones
│   ├── Todas las Declaraciones
│   ├── Crear Declaración (Wizard)
│   ├── Borradores
│   ├── Pendientes de Presentar
│   ├── Presentadas
│   └── Vencidas
```

## Instalación

1. Copiar el módulo a tu directorio de addons:
```bash
cd /home/dml/modulos_odoo18/
```

2. Reiniciar Odoo:
```bash
sudo systemctl restart odoo18
```

3. Actualizar lista de aplicaciones en Odoo:
   - Apps > Actualizar lista de aplicaciones

4. Buscar e instalar "México - Wizard de Declaraciones Fiscales SAT"

## Dependencias

- `l10n_mx_tax_declaration_base` (requerido)
- `account` (requerido)
- `mail` (requerido)
- `account_reconcile_oca` (opcional, para conciliación bancaria)

## Uso

### Crear una Declaración con el Wizard

1. Ir a: **Declaraciones Fiscales > Declaraciones > Crear Declaración (Wizard)**

2. **Paso 1 - Configuración**:
   - Seleccionar período (inicio y fin)
   - Seleccionar obligaciones fiscales
   - Clic en "Siguiente"

3. **Paso 2 - Facturas**:
   - Revisar facturas cargadas automáticamente
   - Filtrar por tipo si es necesario
   - Agregar/quitar facturas manualmente
   - Clic en "Siguiente"

4. **Paso 3 - Conciliación**:
   - Revisar estado de conciliación
   - Abrir herramienta de conciliación (opcional)
   - O marcar "Omitir Conciliación"
   - Clic en "Siguiente"

5. **Paso 4 - Cálculos**:
   - Clic en "Ejecutar Cálculos"
   - Revisar resultados por obligación
   - Clic en "Siguiente"

6. **Paso 5 - Revisión**:
   - Revisar resumen completo
   - Verificar totales
   - Agregar notas si es necesario
   - Clic en "Crear Declaración"

7. **Paso 6 - Completado**:
   - Ver mensaje de éxito
   - Clic en "Ver Declaración"

### Gestionar Declaraciones

#### Estados de la Declaración

```
Borrador → Calculado → Revisado → Presentado → Pagado
```

#### Acciones Disponibles

- **Borrador**: Calcular
- **Calculado**: Revisar / Regresar a Borrador
- **Revisado**: Presentada al SAT / Regresar a Borrador
- **Presentado**: Registrar Pago
- **Pagado**: (Estado final)

#### Cancelar Declaración

- Se puede cancelar en cualquier momento excepto si está "Pagada"
- Las facturas volverán a estado "Pendiente"

## Modelos Creados

### `mx.tax.declaration`
Cabecera de la declaración fiscal con todos los datos principales.

**Campos principales**:
- `period_start`, `period_end`: Período fiscal
- `obligation_ids`: Obligaciones fiscales
- `state`: Estado del flujo
- `invoice_line_ids`: Líneas de facturas
- `calculation_result_ids`: Resultados de cálculos
- `total_payable`: Total a pagar al SAT

### `mx.tax.declaration.invoice.line`
Líneas de facturas incluidas en la declaración.

**Campos principales**:
- `declaration_id`: Relación a declaración
- `invoice_id`: Relación a factura
- `included`: Si está incluida o excluida
- Campos denormalizados (fecha, partner, montos, etc.)

### `mx.tax.declaration.calculation.result`
Resultados de cálculos fiscales almacenados.

**Campos principales**:
- `declaration_id`: Relación a declaración
- `calculation_rule_id`: Relación a regla de cálculo
- `obligation_id`: Relación a obligación
- `result`: Resultado del cálculo
- `is_final_amount`: Si es monto final a pagar

### `mx.tax.declaration.wizard` (Transient)
Wizard multi-paso para crear declaraciones.

**Campos por paso**:
- Paso 1: `period_start`, `period_end`, `obligation_ids`
- Paso 2: `invoice_ids`, `filter_move_type`
- Paso 3: `skip_reconciliation`, `reconciled_count`
- Paso 4: `calculation_ids`, `calculations_executed`
- Paso 5: `total_payable`, `notes`
- Paso 6: `declaration_id`

## Próximas Mejoras

- [ ] Integración completa con `account_reconcile_oca`
- [ ] Generación de reportes PDF (módulo separado)
- [ ] Generación de Excel (módulo separado)
- [ ] Dashboard de declaraciones
- [ ] Alertas automáticas por fechas límite
- [ ] Envío por correo electrónico
- [ ] Firma electrónica

## Soporte

Para dudas o problemas:
1. Revisar esta documentación
2. Revisar logs de Odoo: `/var/log/odoo/odoo.log`
3. Activar modo debug en Odoo
4. Contactar al desarrollador

## Versión

- **Versión**: 18.0.1.0.0
- **Odoo**: 18.0
- **Autor**: IT Admin
- **Licencia**: OPL-1

---

**Última actualización**: 2025-12-02
