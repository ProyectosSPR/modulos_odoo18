# Guía para Actualizar Módulos SaaS y Solucionar Problema de Wizard

## Problema
Al hacer clic en "Nuevo" en las vistas de SaaS Core (Customer, Instance, K8s), se abre un wizard en lugar del formulario normal.

## Causa
Este problema es causado por caché de vistas en Odoo. Las vistas están cacheadas incorrectamente.

## Solución Paso a Paso

### Opción 1: Actualizar Módulo desde la Interfaz (RECOMENDADO)

1. **Ir a Aplicaciones** en Odoo
   ```
   Menú → Aplicaciones
   ```

2. **Remover filtro "Apps"**
   - Hacer clic en el filtro "Apps" para ver todos los módulos

3. **Buscar y actualizar cada módulo:**
   ```
   - Buscar: "Odoo SaaS Core"
   - Hacer clic en "Actualizar"

   - Buscar: "Odoo Subscription"
   - Hacer clic en "Actualizar"

   - Buscar: "SaaS Licensing"
   - Hacer clic en "Actualizar"
   ```

4. **Limpiar caché del navegador:**
   - **Chrome/Edge**: Ctrl+Shift+Delete → Seleccionar "Imágenes y archivos en caché" → Borrar
   - **Firefox**: Ctrl+Shift+Delete → Seleccionar "Caché" → Limpiar ahora
   - O simplemente: **Ctrl+F5** en la página de Odoo

5. **Recargar la página completamente:**
   ```
   Ctrl + F5 (forzar recarga sin caché)
   ```

6. **Probar crear un nuevo registro:**
   - SaaS Management → Customers → Nuevo
   - Debería abrir el formulario normal ahora

---

### Opción 2: Actualizar desde Terminal (MÁS RÁPIDO)

```bash
# Reiniciar Odoo con actualización de módulos
sudo systemctl restart odoo

# O si ejecutas Odoo manualmente:
odoo-bin -u odoo_saas_core,odoo_subscription,odoo_saas_licensing -d nombre_de_tu_base_de_datos
```

---

### Opción 3: Modo Desarrollador + Limpiar Assets

1. **Activar Modo Desarrollador:**
   ```
   Configuración → Activar modo de desarrollador
   ```

2. **Limpiar Assets:**
   ```
   Configuración → Técnico → Base de Datos → Limpiar assets
   ```

3. **Actualizar lista de módulos:**
   ```
   Aplicaciones → Actualizar Lista de Aplicaciones
   ```

4. **Actualizar módulos SaaS:**
   ```
   Buscar cada módulo y hacer clic en "Actualizar"
   ```

---

## Verificación

Después de aplicar cualquiera de las soluciones:

1. ✅ **Probar Customer**: SaaS Management → Customers → Nuevo
   - Debe abrir formulario con campos: Name, Company Name, Tax Code, Email, etc.

2. ✅ **Probar Instance**: SaaS Management → Instances → Nuevo
   - Debe abrir formulario con campos: Instance Name, Subdomain, Customer, etc.

3. ✅ **Probar K8s Cluster**: SaaS Management → Infrastructure → Kubernetes Clusters → Nuevo
   - Debe abrir formulario con campos: Cluster Name, API Server, etc.

---

## Si el Problema Persiste

Si después de todo esto sigue abriendo un wizard, ejecuta esto en terminal:

```bash
# Ver qué wizard se está abriendo
cd /home/user/modulos_odoo18
grep -r "binding_model.*saas\\.customer" . 2>/dev/null
grep -r "binding_model.*saas\\.instance" . 2>/dev/null

# Verificar acciones activas
psql -d nombre_bd -c "SELECT id, name, res_model, view_mode FROM ir_actions_act_window WHERE res_model LIKE 'saas.%';"
```

Y envíame el output de estos comandos.

---

## Debugging Adicional

Si quieres ver exactamente qué está pasando:

1. **Abrir consola del navegador** (F12)
2. **Ir a pestaña Network**
3. **Hacer clic en "Nuevo"**
4. **Ver qué acción se está ejecutando**
5. **Buscar la request que empieza con `/web/action/load`**
6. **Copiar el response y enviármelo**

---

## Problema Conocido en Odoo 18

Si estás usando Odoo 18.0.0 (versión inicial), puede haber un bug conocido con el caché de vistas. Actualiza a Odoo 18.0.1+ si es posible:

```bash
# Verificar versión de Odoo
odoo-bin --version

# O desde Python
python3 -c "import odoo; print(odoo.release.version)"
```

---

## Contacto

Si ninguna solución funciona, por favor proporciona:
- Versión de Odoo
- Navegador y versión
- Screenshot del wizard que se abre
- Log de Odoo (`/var/log/odoo/odoo.log`) líneas recientes
