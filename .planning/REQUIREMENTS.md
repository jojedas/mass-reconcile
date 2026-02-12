# Requirements: Mass Bank Reconciliation

**Defined:** 2026-02-12
**Core Value:** Reducir el tiempo de conciliación bancaria de horas a minutos mientras se minimiza el riesgo de matches incorrectos mediante un sistema de confianza dual (automático/manual).

## v1 Requirements

Requirements para el lanzamiento inicial. Cada uno mapea a fases del roadmap.

### Matching Engine

- [ ] **MATCH-01**: El motor de matching debe buscar candidatos por importe exacto usando account.move.line
- [ ] **MATCH-02**: El motor debe filtrar candidatos por partner (res.partner) cuando esté identificado
- [ ] **MATCH-03**: El motor debe comparar referencia/comunicado del extracto con payment_ref del movimiento
- [ ] **MATCH-04**: El motor debe validar rango de fechas configurable (+/- N días) entre fecha extracto y fecha movimiento
- [ ] **MATCH-05**: El motor debe identificar transferencias internas matching entre cuentas bancarias de la misma compañía
- [ ] **MATCH-06**: El sistema debe calcular score de confianza para cada match propuesto (0-100%)
- [ ] **MATCH-07**: Matches con score 100% (importe exacto + partner + referencia coincide) se clasifican como "seguros"
- [ ] **MATCH-08**: Matches con score 80-99% se clasifican como "probables" (requieren revisión)
- [ ] **MATCH-09**: Matches con score <80% se clasifican como "dudosos" (requieren revisión manual)
- [ ] **MATCH-10**: El sistema debe usar float_compare() para comparación de importes monetarios (evitar rounding errors)
- [ ] **MATCH-11**: El sistema debe validar que el movimiento no esté ya conciliado antes de proponerlo
- [ ] **MATCH-12**: El sistema debe integrar con account.reconcile.model (OCA) para matching basado en reglas recurrentes
- [ ] **MATCH-13**: El sistema debe incluir modelos pre-configurados para gastos recurrentes (alquiler, servicios públicos, salarios)

### Batch Processing

- [ ] **BATCH-01**: El sistema debe procesar líneas de extracto (account.bank.statement.line) en chunks de 80 líneas máximo
- [ ] **BATCH-02**: El usuario debe poder seleccionar líneas para batch por rango de fechas
- [ ] **BATCH-03**: El batch debe tener estados: draft → matching → review → reconciled
- [ ] **BATCH-04**: El sistema debe mostrar indicador de progreso durante procesamiento ("42/80 procesadas — 85% completo")
- [ ] **BATCH-05**: El sistema debe mostrar estadísticas de matching (% automático, % manual, % sin match)
- [ ] **BATCH-06**: El batch debe almacenar todas las propuestas de matching para auditoría
- [ ] **BATCH-07**: El sistema debe usar SELECT FOR UPDATE locking para evitar race conditions en conciliación concurrente

### Manual Review Interface

- [ ] **REVIEW-01**: El usuario debe poder revisar lista de matches propuestos con información clara (línea bancaria, candidato, score)
- [ ] **REVIEW-02**: El usuario debe poder marcar líneas como "To Check" para revisión posterior
- [ ] **REVIEW-03**: El usuario debe poder hacer write-off de diferencias pequeñas con umbral configurable (default $10)
- [ ] **REVIEW-04**: El sistema debe mostrar preview de todas las conciliaciones antes de aplicar
- [ ] **REVIEW-05**: El usuario debe confirmar explícitamente antes de aplicar batch de conciliaciones
- [ ] **REVIEW-06**: El usuario debe poder deshacer (unreconcile) conciliaciones aplicadas con cleanup completo
- [ ] **REVIEW-07**: El sistema debe mostrar mensajes de error claros y accionables cuando falla una conciliación
- [ ] **REVIEW-08**: El sistema debe usar códigos de color para visualizar niveles de confianza (verde=seguro, amarillo=probable, rojo=dudoso)

### User Interface

- [ ] **UI-01**: El sistema debe usar Form view estándar de Odoo para configuración de batch
- [ ] **UI-02**: El sistema debe usar Tree view estándar de Odoo para lista de líneas y matches propuestos
- [ ] **UI-03**: El usuario debe poder aprobar matches seguros (score 100%) en bloque con un botón
- [ ] **UI-04**: El usuario debe poder aprobar/rechazar matches individuales desde la tree view
- [ ] **UI-05**: La interfaz debe mostrar claramente: línea bancaria, match propuesto, score, y botones de acción

### Data Models & Integration

- [ ] **DATA-01**: El sistema debe crear modelo mass.reconcile.batch para tracking de batches
- [ ] **DATA-02**: El sistema debe extender account.bank.statement.line con campos: batch_id, match_score, suggested_move_id
- [ ] **DATA-03**: El sistema debe crear modelo mass.reconcile.match para almacenar propuestas con scores
- [ ] **DATA-04**: El sistema debe usar ORM de Odoo con prefetching para evitar N+1 queries
- [ ] **DATA-05**: El sistema debe implementar security model (ir.model.access.csv, record rules) para permisos adecuados
- [ ] **DATA-06**: El sistema debe validar constraints contables (@api.constrains) antes de conciliar
- [ ] **DATA-07**: El sistema debe usar solo APIs públicas de Odoo para compatibilidad con upgrades

## v2 Requirements

Funcionalidades diferidas a versión futura. No en roadmap actual.

### Advanced Automation

- **AUTO-01**: Queue-based auto-reconciliation usando account_reconcile_oca_queue para batches >200 líneas
- **AUTO-02**: Cron jobs para matching automático programado
- **AUTO-03**: Sistema de notificaciones para resultados de conciliación automática

### Enhanced UI

- **UI-ADV-01**: Widget OWL 2 interactivo con drag-to-group y estado reactivo
- **UI-ADV-02**: Atajos de teclado configurables para operaciones batch
- **UI-ADV-03**: Dashboard de analytics de conciliación con métricas históricas

### Multi-Currency

- **CURR-01**: Soporte completo multi-moneda con conversión automática
- **CURR-02**: Handling de diferencias de tipo de cambio

### Smart Matching

- **SMART-01**: Machine learning para aprender patrones de matching por partner
- **SMART-02**: Fuzzy matching de referencias con similitud de texto (Levenshtein distance)
- **SMART-03**: Matching aproximado de importes con tolerancia de céntimos configurable

## Out of Scope

Explícitamente excluido. Documentado para prevenir scope creep.

| Feature | Reason |
|---------|--------|
| Conciliación automática sin revisión | 20-40% de matches necesitan juicio humano; crear más trabajo de cleanup que ahorra |
| Fuzzy matching en todos los campos | Demasiados falsos positivos; solo usar para partner names con rango de fechas estrecho |
| Auto write-off de importes grandes | Oculta errores; requerir aprobación manual para write-offs >$10 |
| Conciliar sin verificación de partner | Mismo $1000 puede emparejar factura de cliente incorrecto; crea caos AR/AP |
| OCR/importación automática de PDFs bancarios | Scope separado; se asume extracto ya importado en Odoo |
| Integración con APIs bancarias en tiempo real | Complejidad alta; importación manual/programada suficiente para v1 |
| Soporte multi-company | Target son SMEs single-company; feature enterprise puede esperar |
| Widget OWL 2 complejo (v1) | Riesgo alto; form/tree views estándar suficientes, diferir a v2 |

## Traceability

Qué fases cubren qué requirements. Se actualizará durante creación de roadmap.

| Requirement | Phase | Status |
|-------------|-------|--------|
| (Pending roadmap creation) | - | - |

**Coverage:**
- v1 requirements: 33 total
- Mapped to phases: 0
- Unmapped: 33 ⚠️

---
*Requirements defined: 2026-02-12*
*Last updated: 2026-02-12 after initial definition*
