# 🚀 GUÍA DE INSTALACIÓN RÁPIDA - Módulos SaaS Odoo 18

## 📋 ORDEN DE INSTALACIÓN

**IMPORTANTE**: Instalar en este orden exacto para evitar errores de dependencias.

### 1️⃣ Módulo Base (Primero)
```
subscription_package
```
- Módulo base de Cybrosys para suscripciones genéricas
- No tiene dependencias especiales

### 2️⃣ SaaS Core (Segundo)
```
odoo_saas_core
```
- Núcleo de gestión SaaS
- Incluye Kubernetes integration

### 3️⃣ Extensión de Suscripciones (Tercero)
```
odoo_subscription
```
- Depende de: `subscription_package` + `odoo_saas_core`

### 4️⃣ Licensing (Cuarto)
```
odoo_saas_licensing
```
- Depende de: `odoo_saas_core` + `odoo_subscription`

### 5️⃣ N8N Sales (Opcional - Quinto)
```
n8n-sales
```
- Depende de: `odoo_saas_core`
- Solo si vas a vender automatizaciones N8N

---

## 🔧 PASOS DE INSTALACIÓN

### Opción A: Desde la Interfaz de Odoo

1. **Ir a Aplicaciones**
   ```
   Menú > Aplicaciones
   ```

2. **Actualizar Lista de Aplicaciones**
   - Click en "Actualizar lista de aplicaciones"
   - Confirmar la actualización

3. **Buscar e Instalar en Orden**:

   **Paso 1**: Buscar `subscription_package`
   - Click en "Instalar"
   - Esperar a que termine

   **Paso 2**: Buscar `odoo_saas_core` (o "SaaS Core")
   - Click en "Instalar"
   - Esperar a que termine

   **Paso 3**: Buscar `odoo_subscription` (o "Odoo Subscription Management")
   - Click en "Instalar"
   - Esperar a que termine

   **Paso 4**: Buscar `odoo_saas_licensing` (o "SaaS Licensing")
   - Click en "Instalar"
   - Esperar a que termine

   **Paso 5 (Opcional)**: Buscar `n8n-sales` (o "N8N Sales")
   - Click en "Instalar"

### Opción B: Desde la Línea de Comandos

```bash
# Navegar al directorio de Odoo
cd /path/to/odoo

# Instalar módulos en orden
./odoo-bin -d tu_base_de_datos -i subscription_package --stop-after-init
./odoo-bin -d tu_base_de_datos -i odoo_saas_core --stop-after-init
./odoo-bin -d tu_base_de_datos -i odoo_subscription --stop-after-init
./odoo-bin -d tu_base_de_datos -i odoo_saas_licensing --stop-after-init
./odoo-bin -d tu_base_de_datos -i n8n-sales --stop-after-init

# Reiniciar Odoo
./odoo-bin -d tu_base_de_datos
```

---

## 🎯 GUÍA DE USO RÁPIDA

### 📍 ESTRUCTURA DEL MENÚ

Después de instalar, encontrarás:

```
SaaS Management (Menú Principal)
├── Customers
│   ├── Customers (Lista de clientes SaaS)
│   └── Instances (Instancias Odoo desplegadas)
├── Infrastructure (⭐ NUEVO)
│   ├── Kubernetes Clusters
│   └── Deployment Templates
└── Configuration
    └── Service Packages
```

---

## 🔥 FLUJO DE TRABAJO KUBERNETES

### PASO 1: Configurar Kubernetes Cluster

**Ir a**: `SaaS Management > Infrastructure > Kubernetes Clusters`

**Click en "Crear"** y completar:

#### Tab "Connection Settings":
- **Cluster Name**: `Production Cluster` (ejemplo)
- **Provider**: Seleccionar (GKE, EKS, AKS, etc.)
- **API Server URL**: `https://tu-cluster.example.com:6443`
- **Auth Method**: Seleccionar uno:
  - **Bearer Token**: Pegar token de service account
  - **Certificate**: Pegar certificados cliente
  - **Kubeconfig**: Pegar archivo kubeconfig completo

#### Tab "Default Settings":
- **Default Namespace**: `odoo-saas` (recomendado)
- **Default Storage Class**: `standard` o el de tu cluster
- **Ingress Class**: `nginx` (o el que uses)
- **Base Domain**: `saas.tuempresa.com` (importante!)
- **Enable TLS**: ✅ Marcar
- **Cert-Manager Issuer**: `letsencrypt-prod` (si usas cert-manager)

#### Tab "Database Configuration":
- **DB Host Template**: `postgres-{instance_id}.default.svc.cluster.local`
- **DB Port**: `5432`
- **DB User Template**: `odoo_{instance_id}`

**Guardar** ✅

**Click en "Test Connection"** (actualmente es placeholder, no falla)

---

### PASO 2: Crear Deployment Template

**Ir a**: `SaaS Management > Infrastructure > Deployment Templates`

**Click en "Crear"** y completar:

#### Basic Information:
- **Template Name**: `Odoo 18 Standard`
- **Code**: `odoo-18-std`
- **Cluster**: Seleccionar el cluster creado en Paso 1
- **Template Type**: `Deployment`
- **Odoo Version**: `18.0`
- **Odoo Image**: `odoo:18.0` (o tu imagen custom)

#### Tab "Resources":
- **CPU Request**: `500m`
- **CPU Limit**: `2`
- **Memory Request**: `1Gi`
- **Memory Limit**: `2Gi`
- **Replicas**: `1`

#### Tab "Storage":
- **Enable Persistent Storage**: ✅ Marcar
- **Storage Size**: `10Gi`
- **Storage Class**: Dejar vacío (usa default del cluster)

#### Tab "Networking":
- **Service Type**: `ClusterIP`
- **Service Port**: `8069`
- **Enable Ingress**: ✅ Marcar
- **Enable TLS**: ✅ Marcar

#### Tab "YAML Templates":
**Click en "Generate Default YAMLs"**
- Esto auto-genera plantillas YAML básicas
- Puedes personalizar los YAMLs después

**Guardar** ✅

---

### PASO 3: Crear Cliente SaaS

**Ir a**: `SaaS Management > Customers > Customers`

**Click en "Crear"**:
- **Customer Name**: `Empresa Demo`
- **Related Partner**: Seleccionar o crear partner
- **Email**: `admin@empresademo.com`
- **Contact Name**: `Juan Pérez`
- **Contact Email**: `juan@empresademo.com`

**Guardar** ✅

---

### PASO 4: Crear Instancia SaaS

**Ir a**: `SaaS Management > Customers > Instances`

**Click en "Crear"**:

#### Basic Information:
- **Instance Name**: `Empresa Demo - Producción`
- **Subdomain**: `empresademo` (será: empresademo.saas.tuempresa.com)
- **Customer**: Seleccionar el cliente creado
- **Service Package**: Seleccionar un paquete (o crear uno nuevo)
- **Status**: `Trial` (para empezar)
- **Odoo Version**: `18.0`

#### Tab "Kubernetes Configuration":
- **Kubernetes Cluster**: Seleccionar cluster del Paso 1
- **Deployment Template**: Seleccionar template del Paso 2

#### Campos Auto-completables (opcionales por ahora):
- **K8s Namespace**: `odoo-saas` (o dejar que se auto-genere)
- **Database Host**: `postgres-empresademo.default.svc.cluster.local`
- **Database Port**: `5432`
- **Database Name**: `odoo_empresademo`
- **Database User**: `odoo_empresademo`
- **Database Password**: `GENERAR_PASSWORD_SEGURO`

**Guardar** ✅

---

### PASO 5: Explorar Acciones de Kubernetes (Placeholders)

Una vez guardada la instancia, en el Tab "Kubernetes Configuration" verás botones:

#### ⚠️ NOTA: Estos botones son PLACEHOLDERS (no ejecutan acciones reales aún)

- **🚀 Deploy to Kubernetes**:
  - Click → Muestra notificación "Deployment logic pending implementation"
  - En Fase 2 esto creará todos los recursos en K8s

- **📊 Check Status**:
  - Solo disponible si k8s_deployed = True
  - Placeholder para verificar estado de pods

- **📄 View Manifests**:
  - Abre la vista del formulario
  - En Fase 2 mostrará YAMLs generados

- **🔄 Restart Pods**:
  - Placeholder para reiniciar pods

- **🗑️ Undeploy**:
  - Placeholder para eliminar recursos

---

## 🧪 FUNCIONALIDADES ACTUALES (FASE 1)

### ✅ LO QUE FUNCIONA:
1. ✅ Crear y gestionar Kubernetes Clusters
2. ✅ Configurar credenciales de conexión (se guardan)
3. ✅ Crear Deployment Templates
4. ✅ Generar YAMLs por defecto (botón "Generate Default YAMLs")
5. ✅ Editar YAMLs manualmente con editor ACE
6. ✅ Asociar clusters y templates a instancias
7. ✅ Guardar configuración de DB para cada instancia
8. ✅ Visualizar toda la configuración K8s en la instancia
9. ✅ Navegación por menús y vistas
10. ✅ Relación correcta entre modelos

### ⏳ LO QUE ES PLACEHOLDER (FASE 2):
1. ⏳ Conexión real al API de Kubernetes
2. ⏳ Deploy automático de manifiestos
3. ⏳ Creación de bases de datos
4. ⏳ Health checks reales
5. ⏳ Restart de pods
6. ⏳ Undeploy de recursos
7. ⏳ Generación dinámica de manifiestos con placeholders

---

## 🎨 VISTAS DISPONIBLES

### Kubernetes Clusters:
- **Kanban**: Cards visuales con estado del cluster
- **Tree**: Lista tabular
- **Form**: Formulario completo con tabs

### Deployment Templates:
- **Kanban**: Cards por template
- **Tree**: Lista tabular
- **Form**: Formulario con editor YAML

### Instances:
- **Tree**: Lista de instancias
- **Form**: Con tab "Kubernetes Configuration"

---

## 🔍 EXPLORAR DATOS DE EJEMPLO

### Ver Template YAML Generado:
1. Ir a `Deployment Templates`
2. Abrir un template
3. Tab "YAML Templates"
4. Click "Generate Default YAMLs"
5. Ver los YAMLs generados (Deployment, Service, Ingress, PVC)

### Ver Placeholders Disponibles:
En el formulario de Deployment Template > Tab "YAML Templates", scroll down para ver la lista completa de placeholders:
- `{instance_id}`
- `{namespace}`
- `{odoo_image}`
- `{replicas}`
- `{cpu_request}`, `{cpu_limit}`
- `{memory_request}`, `{memory_limit}`
- etc.

---

## 📊 REPORTES Y ESTADÍSTICAS

### Clusters:
- **Stat Button**: "X Instances" → Click para ver instancias en ese cluster

### Templates:
- **Stat Button**: "X Instances" → Click para ver instancias usando ese template

---

## ⚠️ TROUBLESHOOTING

### Error: "Module not found"
**Solución**: Verificar orden de instalación. Desinstalar en orden inverso y reinstalar.

### Error: "Field X does not exist"
**Solución**: Actualizar módulo con `-u nombre_modulo`

### No veo el menú "Infrastructure"
**Solución**:
1. Refrescar navegador (Ctrl+F5)
2. Verificar que odoo_saas_core está instalado
3. Verificar permisos de usuario

### Los botones de K8s no hacen nada
**Solución**: Es normal, son placeholders para Fase 2. Muestran notificaciones informativas.

---

## 📝 DATOS DE PRUEBA SUGERIDOS

### Cluster de Prueba:
```
Name: Local Minikube
Provider: On-Premise
API Server: https://192.168.49.2:8443
Auth Method: Kubeconfig
Default Namespace: odoo-saas
Base Domain: saas.local
```

### Template de Prueba:
```
Name: Odoo 18 Minimal
Code: odoo-18-min
Odoo Image: odoo:18.0
CPU Request: 500m
Memory Request: 512Mi
Storage: 5Gi
```

---

## 🎓 PRÓXIMOS PASOS

1. **Familiarízate con la interfaz** creando clusters y templates
2. **Prueba generar YAMLs** y revisar el contenido
3. **Edita YAMLs manualmente** para personalizar
4. **Crea instancias** y asócialas con clusters/templates
5. **Documenta tu configuración** específica de K8s

---

## 🆘 SOPORTE

Si encuentras errores durante la instalación:
1. Revisar logs de Odoo: `/var/log/odoo/odoo-server.log`
2. Verificar permisos del usuario de base de datos
3. Asegurar que las rutas de los módulos están en `--addons-path`

---

## ✨ FEATURES DESTACADAS

### 🔒 Seguridad:
- Campos sensibles (tokens, passwords) tienen `groups='base.group_system'`
- Solo usuarios System pueden ver credenciales

### 🎯 Validaciones:
- Environment variables validan formato KEY=VALUE
- Límite de instancias por cluster
- Unicidad de subdomains

### 📱 UI/UX:
- Stat buttons interactivos
- Badges de estado con colores
- Formularios organizados en tabs
- Editor YAML con syntax highlighting (ACE)

---

**¡Listo para probar! 🚀**
