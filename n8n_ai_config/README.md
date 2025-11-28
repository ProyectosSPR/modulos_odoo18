# N8N AI Configurator

Módulo de Odoo para configurar Agentes de IA que serán consumidos por N8N.

## 🎯 Características

- **Multi-tenant**: Configuraciones por empresa y usuario
- **Templates compartidos**: Automateai puede compartir configuraciones base con todos
- **Sistema de activación**: Múltiples configs, activa la que quieras usar
- **Gestión de acciones**: Define qué acciones puede ejecutar tu IA
- **Logs y analytics**: Tracking de uso, costos y performance
- **API nativa de Odoo**: Consume con XML-RPC/JSON-RPC

## 📊 Modelos

### `ai.agent.profile`
Configuración principal del agente IA.

**Campos importantes:**
- `name`: Nombre del agente
- `code`: Código único (usado por N8N)
- `system_prompt`: Prompt principal
- `model_provider`: openai, anthropic, google
- `shared_globally`: Si es True, todos lo ven (solo admin)
- `is_default`: Marca como config por defecto
- `active`: Activar/desactivar

### `ai.action`
Acciones que el agente puede ejecutar.

**Campos importantes:**
- `code`: Código único (N8N lo usa para ejecutar)
- `description`: Qué hace (la IA lee esto)
- `when_to_use`: Cuándo usarla (la IA decide)
- `required_parameters`: Parámetros obligatorios
- `optional_parameters`: Parámetros opcionales

### `ai.execution.log`
Logs de ejecuciones para analytics.

## 🚀 Uso desde Odoo

### 1. Crear tu Configuración

```
Menú: Configuración IA > Perfiles de Agente > Crear
```

O clonar un template compartido:
```
1. Ir a "Perfiles de Agente"
2. Filtrar por "Templates Compartidos"
3. Abrir un template
4. Clic en "Clonar Template"
5. Personalizar a tu gusto
```

### 2. Añadir Acciones

En tu perfil, pestaña "Acciones":
```python
Nombre: Crear Lead en CRM
Código: create_crm_lead
Descripción: Crea un nuevo lead en el CRM de Odoo
Cuándo usar: Cuando el cliente muestra interés en comprar
Parámetros obligatorios: name, email
Parámetros opcionales: phone, company, notes
```

### 3. Marcar como Activa y Por Defecto

- Activa el toggle "Activo"
- Clic en "Usar por Defecto"

## 🔌 Consumo desde N8N (XML-RPC)

### Opción 1: N8N HTTP Request Node

```javascript
// 1. Autenticar
POST {{odoo_url}}/xmlrpc/2/common
Content-Type: text/xml

<?xml version="1.0"?>
<methodCall>
  <methodName>authenticate</methodName>
  <params>
    <param><value><string>{{db_name}}</string></value></param>
    <param><value><string>{{username}}</string></value></param>
    <param><value><string>{{password}}</string></value></param>
    <param><value><struct></struct></value></param>
  </params>
</methodCall>

// 2. Obtener Config
POST {{odoo_url}}/xmlrpc/2/object
Content-Type: text/xml

<?xml version="1.0"?>
<methodCall>
  <methodName>execute_kw</methodName>
  <params>
    <param><value><string>{{db_name}}</string></value></param>
    <param><value><int>{{uid}}</int></value></param>
    <param><value><string>{{password}}</string></value></param>
    <param><value><string>ai.agent.profile</string></value></param>
    <param><value><string>get_config_for_api</string></value></param>
    <param><value><array><data>
      <value><int>1</int></value>  <!-- company_id -->
      <value><int>5</int></value>  <!-- partner_id -->
    </data></array></value></param>
  </params>
</methodCall>
```

### Opción 2: Usar librería xmlrpc (Python en Code Node)

```python
import xmlrpc.client

# Conectar
url = "https://automateai.com.mx"
db = "odoo18"
username = "admin@automateai.com.mx"
password = "tu_password"

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Obtener configuración
config = models.execute_kw(
    db, uid, password,
    'ai.agent.profile',
    'get_config_for_api',
    [1, 5]  # company_id, partner_id
)

# config contiene:
# {
#   "agent_profile": {...},
#   "actions": [...]
# }

print(config['agent_profile']['system_prompt'])
print(config['actions'])
```

### Opción 3: JSON-RPC (más simple)

```bash
curl -X POST https://automateai.com.mx/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "service": "object",
      "method": "execute",
      "args": [
        "odoo18",
        1,
        "tu_password",
        "ai.agent.profile",
        "get_config_for_api",
        [1, 5]
      ]
    },
    "id": 1
  }'
```

## 📝 Guardar Logs desde N8N

```python
models.execute_kw(
    db, uid, password,
    'ai.execution.log',
    'create_log',
    [{
        'agent_profile_id': 1,
        'partner_id': 5,
        'company_id': 1,
        'action_code': 'create_crm_lead',
        'input_message': '¿Cómo comprar?',
        'ai_response': 'Te ayudo con eso...',
        'action_executed': True,
        'success': True,
        'tokens_used': 234,
        'execution_time_ms': 1200,
        'cost': 0.002
    }]
)
```

## 🔒 Seguridad Multi-tenant

El módulo automáticamente filtra:
- **Usuarios normales**: Ven solo sus configs + templates compartidos
- **Administradores**: Ven todo
- **Escritura**: Solo configs propias

## 🎨 Flujo Completo en N8N

```
[Webhook] → Recibe mensaje
    ↓
[Get Odoo Config] → XML-RPC call a get_config_for_api
    ↓
[Build AI Prompt] → Arma prompt con system_prompt + actions
    ↓
[Call AI (Claude/GPT)] → LLM responde
    ↓
[Parse Response] → ¿Quiere ejecutar acción?
    ↓
[Execute Action] → Ejecuta en Odoo/otro sistema
    ↓
[Log to Odoo] → Guarda log con create_log
    ↓
[Return] → Responde al usuario
```

## 📈 Analytics

Ver analytics de uso:
```python
analytics = models.execute_kw(
    db, uid, password,
    'ai.execution.log',
    'get_analytics',
    [1, 5, 30]  # company_id, partner_id, días
)

# Retorna:
# {
#   'total_executions': 150,
#   'total_tokens': 45000,
#   'total_cost_usd': 0.50,
#   'success_rate': 98.5,
#   'top_actions': [...]
# }
```

## 💡 Tips

1. **Usa códigos descriptivos**: `create_crm_lead` mejor que `action1`
2. **System Prompt claro**: Define bien el formato de respuesta
3. **Templates compartidos**: Automateai puede crear templates base
4. **Testing**: Usa logs para mejorar prompts
5. **Costos**: Tracking automático de tokens y costos

## 🆘 Soporte

- **Issues**: GitHub repo
- **Email**: soporte@automateai.com.mx
