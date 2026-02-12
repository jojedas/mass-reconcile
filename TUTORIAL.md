# Tutorial Completo: Mass Reconciliation para Odoo 18.0

## 📚 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Instalación desde GitHub](#instalación-desde-github)
3. [Configuración Inicial](#configuración-inicial)
4. [Uso del Módulo](#uso-del-módulo)
5. [Casos de Uso Comunes](#casos-de-uso-comunes)
6. [Desarrollo y Contribución](#desarrollo-y-contribución)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

---

## Introducción

### ¿Qué es Mass Reconciliation?

Mass Reconciliation es un módulo avanzado para Odoo 18.0 que automatiza la conciliación bancaria masiva, reduciendo el tiempo de conciliación de **horas a minutos**.

### Características Principales

✅ **Matching Inteligente**: Algoritmos de coincidencia con scoring de confianza
✅ **Dual Mode**: Modo automático y manual para máximo control
✅ **Batch Processing**: Procesa miles de transacciones en lotes
✅ **3-Tier Confidence**: Clasificación Safe/Probable/Doubtful
✅ **OCA Compatible**: Integrado con account-reconcile framework

### Requisitos

- 🐳 **Docker** y **Docker Compose** instalados
- 💻 **4GB RAM** mínimo recomendado
- 🌐 **Puertos libres**: 8069, 8071, 8072, 5432
- 🐙 **Git** para clonar el repositorio

---

## Instalación desde GitHub

### Paso 1: Clonar el Repositorio

```bash
# Clonar el repositorio
git clone https://github.com/jojedas/mass-reconcile.git

# Entrar al directorio
cd mass-reconcile
```

### Paso 2: Ejecutar Setup Automático

El script `setup.sh` configura todo automáticamente:

```bash
# Dar permisos de ejecución (si es necesario)
chmod +x setup.sh install-modules.sh

# Ejecutar setup completo
./setup.sh
```

**¿Qué hace setup.sh?**
- ✅ Descarga imágenes Docker (Odoo 18.0 + PostgreSQL 15)
- ✅ Crea directorios de datos persistentes
- ✅ Clona repositorios OCA necesarios
- ✅ Inicia los contenedores Docker
- ✅ Espera a que Odoo esté listo

**Tiempo estimado**: 5-10 minutos (primera vez)

### Paso 3: Crear Base de Datos

1. Abre tu navegador en: **http://localhost:8069**
2. Verás la pantalla de creación de base de datos
3. Rellena los campos:
   - **Database Name**: `jumo` (o el que prefieras)
   - **Master Password**: `jumo`
   - **Email**: tu email
   - **Password**: tu contraseña de admin
   - **Phone Number**: (opcional)
   - **Language**: Spanish (o tu idioma)
   - **Country**: Spain (o tu país)
   - **Demo data**: ❌ Desmarcado (para producción)

4. Haz clic en **Create Database**

⏱️ **Espera 2-3 minutos** mientras Odoo inicializa la base de datos.

### Paso 4: Instalar Módulos

```bash
# Instalar módulos OCA y mass_reconcile
./install-modules.sh
```

**¿Qué hace install-modules.sh?**
- ✅ Instala `account_reconcile_oca`
- ✅ Instala `account_reconcile_model_oca`
- ✅ Instala `mass_reconcile` (este módulo)
- ✅ Reinicia Odoo

**Tiempo estimado**: 2-3 minutos

### Paso 5: Verificar Instalación

1. Recarga la página en tu navegador
2. Ve a **Apps** (Aplicaciones)
3. Busca "Mass Reconcile"
4. Debería aparecer como **Instalado** ✅

---

## Configuración Inicial

### Activar Modo Desarrollador

Para acceder a todas las funcionalidades:

1. Ve a **Settings** (Configuración)
2. Desplázate hasta el final
3. Haz clic en **Activate the developer mode**

### Configurar Modelos de Conciliación

Los modelos de conciliación definen las reglas de matching:

1. Ve a **Accounting** → **Configuration** → **Reconciliation Models**
2. Crea un nuevo modelo:
   - **Name**: "Matching Facturas"
   - **Type**: "Invoice Matching"
   - **Rule Type**: "invoice_matching"
   - **Auto-validate**: ✅ (para matches seguros)

### Configurar Permisos de Usuario

1. Ve a **Settings** → **Users & Companies** → **Users**
2. Selecciona un usuario
3. En **Accounting**, asigna:
   - **Accountant**: Para uso general
   - **Adviser**: Para gestión completa (incluye eliminación)

---

## Uso del Módulo

### 1. Importar Extracto Bancario

**Opción A: Vía UI de Odoo**

1. Ve a **Accounting** → **Bank** → **Bank Statements**
2. Crea un nuevo extracto o importa desde CSV/OFX
3. Verifica que las líneas se hayan importado correctamente

**Opción B: Vía API**

```python
# Ejemplo de importación programática
statement = env['account.bank.statement'].create({
    'name': 'ST/2024/001',
    'journal_id': journal.id,
    'date': '2024-01-01',
})

# Crear líneas
env['account.bank.statement.line'].create({
    'statement_id': statement.id,
    'payment_ref': 'INV/2024/001',
    'amount': 1500.00,
    'date': '2024-01-01',
})
```

### 2. Crear Batch de Conciliación

1. Ve a **Accounting** → **Bank** → **Mass Reconciliation Batches**
2. Haz clic en **Create**
3. Rellena los campos:
   - **Name**: Nombre descriptivo (ej: "Enero 2024 - Banco BBVA")
   - **Statement Lines**: Selecciona las líneas a procesar
   - **Reconcile Model**: (Opcional) Modelo de reglas de matching
   - **Chunk Size**: `80` (recomendado)
   - **Auto Mode**: ✅ (para matching automático de líneas seguras)

### 3. Ejecutar el Matching

```bash
# Opción 1: Vía UI (recomendado para empezar)
# Haz clic en el botón "Process Batch" en la vista del batch

# Opción 2: Vía código (para automatización)
batch.action_process()
```

**¿Qué sucede durante el procesamiento?**

1. **Chunk Division**: Divide las líneas en chunks de 80 (configurable)
2. **Matching**: Por cada chunk:
   - Busca matches exactos (importe + referencia)
   - Busca matches por partner (partner + importe)
   - Aplica reglas de reconciliation model
   - Calcula score de confianza (0-100)
3. **Classification**:
   - **Safe** (100): Auto-concilia si `auto_mode=True`
   - **Probable** (80-99): Requiere revisión manual
   - **Doubtful** (<80): Requiere revisión manual
4. **Proposal Creation**: Crea registros de `mass.reconcile.match`

### 4. Revisar y Aprobar Matches

#### Vista del Batch

1. Abre el batch procesado
2. Verás 3 pestañas:
   - **Info**: Información general
   - **Statement Lines**: Líneas del extracto
   - **Match Proposals**: Propuestas de matching

#### Vista de Match Proposals

Cada propuesta muestra:
- **Statement Line**: Línea del extracto bancario
- **Move Line**: Línea contable candidata
- **Match Type**: Tipo de matching (exact, partner, invoice)
- **Confidence Score**: Score de confianza (0-100)
- **Classification**: Safe/Probable/Doubtful
- **Reconcile Model**: Regla aplicada (si aplica)
- **State**: draft/validated/rejected

#### Aprobar Manualmente

```python
# Aprobar una propuesta
match.action_validate()

# Rechazar una propuesta
match.action_reject()

# Aprobar todas las "safe"
safe_matches = batch.match_ids.filtered(lambda m: m.classification == 'safe')
safe_matches.action_validate()
```

### 5. Monitorear Progreso

El batch mantiene contadores en tiempo real:

```python
batch.total_lines         # Total de líneas
batch.matched_count       # Líneas con al menos 1 match
batch.unmatched_count     # Líneas sin matches
batch.reconciled_count    # Líneas ya conciliadas
batch.progress_percent    # Porcentaje de progreso (0-100)
```

**Visualización en UI**: Barra de progreso automática en la vista del batch.

---

## Casos de Uso Comunes

### Caso 1: Conciliación Mensual Automatizada

**Escenario**: Tienes 1000 líneas bancarias del mes de enero que necesitas conciliar.

```python
# 1. Crear batch
batch = env['mass.reconcile.batch'].create({
    'name': 'Enero 2024 - Automatizado',
    'statement_line_ids': [(6, 0, line_ids)],
    'auto_mode': True,
    'chunk_size': 100,
})

# 2. Procesar
batch.action_process()

# 3. Verificar resultados
print(f"Conciliadas automáticamente: {batch.reconciled_count}")
print(f"Requieren revisión: {batch.matched_count - batch.reconciled_count}")
print(f"Sin match: {batch.unmatched_count}")

# 4. Revisar solo las "probable"
probable_matches = batch.match_ids.filtered(
    lambda m: m.classification == 'probable' and m.state == 'draft'
)
for match in probable_matches:
    # Revisar manualmente en UI o aprobar programáticamente
    if match.confidence_score >= 90:
        match.action_validate()
```

### Caso 2: Matching de Facturas con Referencia

**Escenario**: Clientes pagan facturas indicando el número en la referencia bancaria.

```python
# Configurar modelo de conciliación
model = env['account.reconcile.model'].create({
    'name': 'Matching por Referencia de Factura',
    'rule_type': 'invoice_matching',
    'match_total_amount': True,
    'match_total_amount_param': 100,  # Tolerancia 100%
})

# Crear batch con el modelo
batch = env['mass.reconcile.batch'].create({
    'name': 'Pagos de Facturas - Febrero 2024',
    'statement_line_ids': [(6, 0, line_ids)],
    'reconcile_model_id': model.id,
    'auto_mode': False,  # Revisión manual
})

batch.action_process()
```

### Caso 3: Conciliación por Partner

**Escenario**: Pagos recurrentes de clientes conocidos sin referencia.

```python
# El engine automáticamente busca:
# 1. Partner en statement line (bank_partner_id)
# 2. Invoices abiertas del mismo partner
# 3. Mismo importe exacto

# Crear batch
batch = env['mass.reconcile.batch'].create({
    'name': 'Pagos Recurrentes - Partner Match',
    'statement_line_ids': [(6, 0, partner_payment_lines)],
    'auto_mode': True,  # Auto-concilia matches exactos
})

batch.action_process()

# Resultados
exact_matches = batch.match_ids.filtered(
    lambda m: m.match_type == 'partner_amount' and m.confidence_score == 100
)
print(f"Matches exactos por partner: {len(exact_matches)}")
```

### Caso 4: Auditoría de Matches

**Escenario**: Necesitas auditar qué matches se hicieron y por qué.

```python
# Obtener todos los matches de un período
matches = env['mass.reconcile.match'].search([
    ('create_date', '>=', '2024-01-01'),
    ('create_date', '<=', '2024-01-31'),
    ('state', '=', 'validated'),
])

# Generar reporte
for match in matches:
    print(f"""
    Match ID: {match.id}
    Línea: {match.statement_line_id.payment_ref}
    Importe: {match.statement_line_id.amount}
    Match Type: {match.match_type}
    Confidence: {match.confidence_score}
    Clasificación: {match.classification}
    Validado por: {match.write_uid.name}
    Fecha: {match.write_date}
    """)
```

---

## Desarrollo y Contribución

### Setup para Desarrollo

```bash
# Clonar repo
git clone https://github.com/jojedas/mass-reconcile.git
cd mass-reconcile

# Crear branch de desarrollo
git checkout -b feature/mi-nueva-funcionalidad

# Levantar ambiente
./setup.sh

# Activar modo debug en Odoo
# Editar config/odoo.conf y agregar:
# log_level = debug
```

### Estructura del Código

```
mass_reconcile/
├── models/                          # Modelos de negocio
│   ├── mass_reconcile_batch.py     # Gestor de batches
│   ├── mass_reconcile_match.py     # Propuestas de matching
│   ├── mass_reconcile_engine.py    # Lógica de matching (AbstractModel)
│   ├── mass_reconcile_scorer.py    # Scoring de confianza (AbstractModel)
│   └── account_bank_statement_line.py  # Extensión de líneas bancarias
├── security/                        # Control de acceso
│   ├── ir.model.access.csv         # Permisos por modelo
│   └── mass_reconcile_security.xml # Grupos y reglas
├── tests/                          # Tests unitarios
│   └── test_matching_engine.py     # Tests del engine
└── __manifest__.py                 # Metadatos del módulo
```

### Ejecutar Tests

```bash
# Método 1: Usando Makefile
make test

# Método 2: Docker directo
docker-compose run --rm odoo odoo \
    --database=jumo \
    --test-enable \
    --stop-after-init \
    --update=mass_reconcile \
    --log-level=test
```

### Agregar Nuevos Tipos de Matching

```python
# En models/mass_reconcile_engine.py

def _find_custom_matches(self, line, candidates):
    """
    Tu lógica de matching personalizada.

    :param line: account.bank.statement.line
    :param candidates: account.move.line recordset
    :return: [(move_line, score, match_type), ...]
    """
    matches = []

    # Tu lógica aquí
    for candidate in candidates:
        if self._tu_condicion(line, candidate):
            score = self._calculate_score(line, candidate)
            matches.append((candidate, score, 'custom_type'))

    return matches

# Registrar en _find_matches()
def _find_matches(self, line):
    all_matches = []

    # Matches existentes
    all_matches.extend(self._find_exact_amount_matches(line, candidates))
    all_matches.extend(self._find_partner_amount_matches(line, candidates))
    all_matches.extend(self._find_invoice_reference_matches(line, candidates))

    # Tu nuevo tipo
    all_matches.extend(self._find_custom_matches(line, candidates))

    return all_matches
```

### Modificar Scoring

```python
# En models/mass_reconcile_scorer.py

# Ajustar pesos (deben sumar 100)
WEIGHT_AMOUNT = 60      # Era 50
WEIGHT_PARTNER = 20     # Era 25
WEIGHT_REFERENCE = 15   # Era 20
WEIGHT_DATE = 5         # Mismo

# Ajustar umbrales de clasificación
THRESHOLD_SAFE = 95      # Era 100
THRESHOLD_PROBABLE = 75  # Era 80
```

### Crear Pull Request

```bash
# 1. Hacer commit de cambios
git add .
git commit -m "feat: añadir matching por código de cliente"

# 2. Push a GitHub
git push origin feature/mi-nueva-funcionalidad

# 3. Crear PR en GitHub
gh pr create --title "Add customer code matching" \
             --body "Añade matching basado en código de cliente en campo notes"
```

---

## Troubleshooting

### Problema: Contenedores no inician

```bash
# Verificar puertos en uso
sudo lsof -i :8069
sudo lsof -i :5432

# Si están ocupados, matar procesos o cambiar puertos en docker-compose.yml

# Verificar logs
docker-compose logs -f odoo
docker-compose logs -f db
```

### Problema: Módulo no aparece en Apps

```bash
# Actualizar lista de aplicaciones
docker-compose run --rm odoo odoo \
    --database=jumo \
    --db_host=db \
    --db_user=odoo \
    --db_password=jumo \
    -u base \
    --stop-after-init

docker-compose restart odoo

# Luego en Odoo UI: Apps → Update Apps List
```

### Problema: Tests fallan

```bash
# Ver logs detallados
make test | grep -A 20 "FAIL\|ERROR"

# Ejecutar test específico
docker-compose run --rm odoo odoo \
    --database=jumo \
    --test-enable \
    --test-tags=mass_reconcile \
    --stop-after-init
```

### Problema: Matching no encuentra nada

**Verificaciones**:

1. ¿Las líneas tienen `partner_id` o `bank_partner_id`?
   ```python
   line.partner_id or line.bank_partner_id
   ```

2. ¿Hay invoices abiertas del partner?
   ```python
   env['account.move.line'].search([
       ('partner_id', '=', partner.id),
       ('account_id.reconcile', '=', True),
       ('reconciled', '=', False),
   ])
   ```

3. ¿El importe coincide?
   ```python
   from odoo.tools import float_compare
   float_compare(line.amount, invoice_amount, precision_digits=2) == 0
   ```

### Problema: Performance lento con muchas líneas

**Optimizaciones**:

```python
# 1. Reducir chunk size
batch.chunk_size = 50  # Era 80

# 2. Limitar candidatos por fecha
# Editar _get_candidates() para agregar filtro de rango de fechas

# 3. Índices en base de datos (ya están creados)
# account.move.line tiene índices en:
# - partner_id
# - account_id
# - reconciled
# - date

# 4. Procesar en horario de baja carga
# Usar cron job nocturno
```

### Problema: Permisos denegados

```bash
# Dar permisos a directorios de datos
sudo chown -R $USER:$USER data/
chmod -R 755 data/

# Reiniciar contenedores
docker-compose restart
```

---

## FAQ

### ¿Puedo usar esto en producción?

✅ **Sí**, pero:
- Prueba exhaustivamente en ambiente de staging primero
- Empieza con `auto_mode=False` para revisar manualmente
- Monitorea los primeros batches de cerca
- Ten backup de la base de datos

### ¿Funciona con Odoo Enterprise?

✅ **Sí**, es compatible. Sin embargo, Odoo Enterprise ya tiene su propio módulo de conciliación bancaria. Este módulo está diseñado para Community Edition con OCA modules.

### ¿Puedo personalizar los tipos de matching?

✅ **Sí**, ver sección [Agregar Nuevos Tipos de Matching](#agregar-nuevos-tipos-de-matching).

### ¿Cómo afecta el chunk_size al performance?

- **Chunk pequeño (20-50)**: Más requests a BD, más lento, pero más granular
- **Chunk grande (100-200)**: Menos requests, más rápido, pero menos control
- **Recomendado (80)**: Balance óptimo para la mayoría de casos

### ¿Qué pasa si tengo 10,000 líneas?

El batch las divide automáticamente:
- 10,000 líneas / 80 chunk_size = 125 chunks
- Procesa chunk por chunk (evita memory overflow)
- Tiempo estimado: 5-10 minutos (depende del hardware)

### ¿Puedo integrar con mi banco directamente?

⚠️ Este módulo **no** se conecta directamente a APIs bancarias. Necesitas:
1. Exportar extracto bancario desde tu banco (CSV/OFX/CAMT)
2. Importar en Odoo vía módulo `account_bank_statement_import`
3. Luego usar mass_reconcile para matching

### ¿Hay soporte comercial disponible?

Este es un proyecto open-source. Para soporte comercial:
- Contrata a un partner certificado de Odoo
- Contacta a la comunidad OCA
- Abre issues en GitHub para bugs

### ¿Cómo contribuyo?

1. Fork el repositorio
2. Crea un branch (`git checkout -b feature/awesome-feature`)
3. Commit tus cambios (`git commit -m 'Add awesome feature'`)
4. Push al branch (`git push origin feature/awesome-feature`)
5. Abre un Pull Request

---

## Recursos Adicionales

### Documentación

- [README.md](README.md) - Overview general
- [QUICKSTART.md](QUICKSTART.md) - Setup rápido en 5 minutos
- [SETUP.md](SETUP.md) - Guía detallada de instalación
- [DOCKER_COMMANDS.md](DOCKER_COMMANDS.md) - Referencia de comandos Docker
- [TEST_ENVIRONMENT.md](TEST_ENVIRONMENT.md) - Setup de ambiente de testing

### Enlaces Externos

- [Odoo 18.0 Documentation](https://www.odoo.com/documentation/18.0/)
- [OCA account-reconcile](https://github.com/OCA/account-reconcile)
- [Odoo Developer Guide](https://www.odoo.com/documentation/18.0/developer.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/15/)

### Comunidad

- **GitHub Issues**: https://github.com/jojedas/mass-reconcile/issues
- **OCA Community**: https://odoo-community.org/
- **Odoo Forum**: https://www.odoo.com/forum

### Videos y Tutoriales

*(Por agregar - contribuciones bienvenidas)*

---

## Licencia

Este módulo se distribuye bajo licencia **LGPL-3** (compatible con Odoo Community).

---

## Changelog

### v1.0.0 (2024-02-12) - Initial Release

**Features:**
- ✅ Batch processing con chunk management
- ✅ Matching engine con 3 tipos (exact, partner, invoice)
- ✅ Confidence scoring con clasificación 3-tier
- ✅ Auto-mode para conciliación automática de matches seguros
- ✅ Integración con OCA account-reconcile
- ✅ Tests unitarios completos
- ✅ Docker development environment
- ✅ Documentación completa

**Known Issues:**
- Ninguno reportado

---

## Créditos

**Desarrollado por**: Juan Ojeda (jojedas)
**Framework**: OCA account-reconcile
**Built with**: Claude Code (Anthropic)

---

## Soporte

¿Problemas? ¿Preguntas?

1. 📖 Lee la documentación en [SETUP.md](SETUP.md)
2. 🔍 Revisa [issues existentes](https://github.com/jojedas/mass-reconcile/issues)
3. 🆕 Abre un [nuevo issue](https://github.com/jojedas/mass-reconcile/issues/new)
4. 💬 Pregunta en el [Odoo Forum](https://www.odoo.com/forum)

---

**¡Gracias por usar Mass Reconciliation!** 🎉

Si te resulta útil, considera:
- ⭐ Dar una estrella al repo
- 🐛 Reportar bugs
- 💡 Sugerir mejoras
- 🤝 Contribuir con código

---

*Última actualización: 2024-02-12*
