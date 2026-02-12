# Mass Bank Reconciliation

## What This Is

Un módulo para Odoo 18.0 Community edition que automatiza la conciliación bancaria masiva procesando extractos de 50-200 líneas en chunks de 80. El módulo propone matches automáticos basados en importe exacto y referencia del extracto, aplicando automáticamente los matches seguros y destacando los dudosos para revisión manual.

## Core Value

Reducir el tiempo de conciliación bancaria de horas a minutos mientras se minimiza el riesgo de matches incorrectos mediante un sistema de confianza dual (automático/manual).

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] El sistema debe procesar líneas de extracto bancario (`account.bank.statement.line`) en chunks de 80 líneas
- [ ] El motor de matching debe proponer emparejamientos para facturas de clientes (pagos entrantes)
- [ ] El motor de matching debe proponer emparejamientos para facturas de proveedores (pagos salientes)
- [ ] El motor de matching debe proponer emparejamientos para gastos recurrentes (alquiler, servicios, etc.)
- [ ] El motor de matching debe proponer emparejamientos para transferencias internas entre cuentas propias
- [ ] El matching debe usar importe exacto como criterio principal
- [ ] El matching debe usar la referencia/comunicado del extracto como criterio secundario
- [ ] El sistema debe clasificar matches como "seguros" (confianza 100%) cuando hay match perfecto de importe + referencia
- [ ] Los matches seguros deben poder aplicarse automáticamente sin intervención manual
- [ ] Los matches dudosos deben destacarse para revisión manual
- [ ] El widget debe mostrar propuestas de matching con información clara (línea bancaria, candidato propuesto, nivel de confianza)
- [ ] El widget debe permitir aprobar matches en bloque (aplicar todos los seguros de golpe)
- [ ] El widget debe permitir revisar y corregir matches dudosos antes de aplicar

### Out of Scope

- Matching aproximado de importes (diferencias de céntimos) — v1 solo importes exactos
- OCR o importación automática de PDFs bancarios — se asume extracto ya importado en Odoo
- Machine learning o IA para aprender patrones — v1 usa reglas determinísticas
- Configuración de reglas personalizadas por usuario — v1 usa lógica fija de matching
- Integración con APIs bancarias en tiempo real — scope solo conciliación manual

## Context

**Situación actual:**
- Ya se usa Odoo Community con las reglas básicas de conciliación (`account.reconcile.model`)
- Las reglas estándar son insuficientes para el volumen de transacciones
- El proceso manual actual toma horas y es propenso a errores
- Extractos típicos tienen 50-200 líneas bancarias

**Ecosistema técnico:**
- Odoo 18.0 Community Edition (no Enterprise)
- Módulo base de contabilidad (`account`) ya instalado
- Sistema de importación de extractos (`account_bank_statement_import`) funcional
- Familiaridad con el modelo `account.bank.statement.line` y `account.reconcile.model`

## Constraints

- **Tech stack**: Odoo 18.0 Community — no podemos usar funcionalidades Enterprise
- **Compatibilidad**: Debe funcionar con el flujo estándar de importación de extractos de Odoo
- **Performance**: Procesamiento por chunks de 80 líneas para mantener UI responsive
- **Tech stack**: Python 3.10+ (requisito de Odoo 18.0), JavaScript/XML para vistas Odoo

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Chunks de 80 líneas | Límite encontrado en práctica para mantener UI responsive | — Pending |
| Matching determinístico vs ML | v1 necesita ser predecible y debuggable, ML agrega complejidad | — Pending |
| Dual mode (auto/manual) | Balance entre velocidad y control - auto para obvios, manual para dudosos | — Pending |
| Importe exacto + referencia | Criterios que dan mayor confianza para matching automático sin riesgo | — Pending |

---
*Last updated: 2026-02-12 after initialization*
