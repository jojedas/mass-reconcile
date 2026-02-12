# Project Research Summary

**Project:** Mass Bank Reconciliation for Odoo 18.0 Community
**Domain:** Bank reconciliation module for ERP accounting systems
**Researched:** 2026-02-12
**Confidence:** HIGH

## Executive Summary

Mass bank reconciliation for Odoo 18.0 Community is a well-established domain with clear technical patterns and documented pitfalls. The recommended approach is to build on Odoo's native reconciliation infrastructure using the ORM extensively, leverage OCA's `account_reconcile_model_oca` module to restore reconciliation models moved to Enterprise in v17, and implement a batch processing engine that chunks operations to 80 lines for optimal performance. The core differentiator is efficient bulk processing with confidence scoring—standard Odoo handles reconciliation one-by-one, but experts batch operations with user review of uncertain matches.

The primary technical risks are N+1 query performance degradation (iterate through 80 lines without proper ORM prefetching), race conditions from concurrent reconciliation attempts (multiple users or automated processes conflicting), and false positive matches from insufficient validation. These are mitigated by: using ORM batch queries with explicit prefetching, implementing SELECT FOR UPDATE locking with transaction isolation, and building multi-factor matching (amount + partner + reference + date range) with configurable confidence thresholds. The architecture follows a service-pattern separation: models for data persistence, service classes for matching algorithms, TransientModel wizards for manual flows, and OWL 2 widgets for interactive batch UI.

Build order should follow dependencies strictly: foundation models first (batch tracking, extended statement lines), then matching engine (can be tested independently), then manual wizard flow (validates end-to-end), then OWL batch widget (complex UI built on proven backend), finally automation layer (cron jobs, queue processing). This sequence ensures each layer validates before the next is built, reducing integration risks.

## Key Findings

### Recommended Stack

Odoo 18.0 Community provides the foundation with Python 3.10-3.12 and PostgreSQL 15+. The stack is mature and well-documented with high confidence in version requirements and framework patterns.

**Core technologies:**
- **Odoo 18.0 Community**: Provides `account.bank.statement.line` model, ORM, accounting infrastructure, and reconciliation APIs
- **OCA account_reconcile_model_oca**: Restores reconciliation models moved to Enterprise in v17; essential for rule-based matching
- **OWL 2 (built-in)**: Modern reactive JavaScript framework for batch reconciliation widget; replaces deprecated jQuery/Backbone
- **Python 3.12**: Recommended for performance (minimum 3.10); service classes for matching engine
- **PostgreSQL 15+**: Required database with ACID compliance; use indexes on partner_id, amount, payment_ref for search performance

**Critical version dependencies:**
- Odoo 18.0 explicitly requires Python 3.10+ and PostgreSQL 12+ (15+ recommended)
- OWL 2 is built-in to Odoo 18 with automatic reactivity (breaking change from v17)
- Translation pattern changed in v18: prefer `self.env._('text')` over `_('text')`

**Development patterns by phase:**
- Phase 1 (Core): models.Model for configuration, pure Python matching, unittest.TransactionCase, ORM-only (no SQL)
- Phase 2 (Batch): models.TransientModel for wizards, server-side batch processing (no async yet)
- Phase 3 (Enhanced UI): OWL 2 components, QWeb templates, client-side validation
- Phase 4 (Production): account_reconcile_oca_queue for async, browser tests, pre-commit hooks

### Expected Features

Research identified clear table stakes vs. differentiators based on standard Odoo capabilities and market gaps.

**Must have (table stakes):**
- **Exact amount + reference matching** — Core algorithm; handles 60-80% of transactions automatically
- **Partner-based filtering** — Essential for facturas clientes/proveedores workflow
- **Manual reconciliation UI** — Handles 20-40% that automation misses
- **"To Check" workflow** — Critical for edge cases without blocking reconciliation
- **Write-off small differences** — Rounding errors (<$10) must be handled to complete reconciliation
- **Undo/unreconcile** — Errors happen; must be reversible with complete cleanup
- **CSV import** — Users won't manually enter 80 transactions
- **Validate/confirm action** — Explicit confirmation prevents accidental reconciliation

**Should have (competitive advantage):**
- **Mass/bulk reconciliation (80+ lines)** — **PRIMARY DIFFERENTIATOR**: reduces hours to minutes; standard Odoo is one-by-one
- **Confidence scoring** — Shows match quality (100% exact, 90% probable, 50% possible); users review uncertain matches first
- **Progress indicators** — "427/500 transactions reconciled (85%)" with time estimates; prevents user anxiety during batch processing
- **Basic reconciliation models** — Pre-configured rules for recurring expenses (rent, utilities, salaries)
- **Internal transfer matching** — Automatically matches transfers between company bank accounts
- **Search month limits** — Configurable date range tolerance (match within +/- 7 days) for timing differences

**Defer (v2+):**
- **Queue-based auto-reconciliation** — Complex; v1 manual validation sufficient (add when processing 200+ lines regularly)
- **Smart pattern learning (ML)** — Requires significant training data; rule-based models sufficient initially
- **Multi-company support** — Target users are single-company SMEs; enterprise feature can wait
- **Real-time bank sync** — API integrations complex; manual/scheduled imports sufficient initially

**Anti-features to avoid:**
- **Automatic reconciliation without review** — 20-40% of matches need human judgment; creates more cleanup work
- **Fuzzy matching on all fields** — Too many false positives; use only for partner names with narrow date ranges
- **Auto-write-off large amounts** — Hides errors; require manual approval for write-offs >$10
- **Reconcile without partner verification** — Same $1000 matches wrong customer's invoice; creates AR/AP chaos

### Architecture Approach

The architecture follows a layered service pattern with clear separation of concerns: models for data persistence, service classes for business logic, TransientModel for temporary workflow, and OWL 2 for interactive UI.

**Major components:**

1. **Model Layer** — Data persistence and basic business rules
   - `account.bank.statement.line` (extended): Add batch_id, match_score, suggested_move_id fields
   - `mass.reconcile.batch` (new): Manages batch state machine (draft → matching → review → reconciled)
   - `mass.reconcile.match` (new): Stores match suggestions with confidence scores for audit trail

2. **Business Logic Layer** — Matching engine as service class
   - `MatchingEngine` service: Core algorithm separated from models for testability
   - Methods: `find_matches()`, `_get_candidates()`, `_score_match()`, `_filter_by_threshold()`
   - Multi-factor scoring: amount match (40 points) + partner match (30 points) + reference similarity (30 points)
   - Implements validation: check account.reconcile flag, posted state, not already reconciled

3. **Presentation Layer** — Dual interface strategy
   - `MassReconcileWizard` (TransientModel): Multi-step manual flow for simple cases; server-side validation
   - `BatchReconcileWidget` (OWL 2): Interactive bulk approval for 80-line batches; real-time client-side interaction
   - Decision: Wizard for sequential guided flow; Widget for bulk operations with complex state management

4. **Integration Layer** — Account module bridges
   - Uses `account.reconcile.model._apply_rules()` for rule-based matching
   - Links via `account.move` foreign keys and `reconcile()` method calls
   - Never bypasses ORM; always uses Odoo reconciliation APIs for audit trail integrity

**Key architectural patterns:**
- **Model inheritance** (`_inherit`) for extending `account.bank.statement.line` without core modifications
- **Service class** (not models.Model) for matching engine to enable independent testing and reuse
- **State machine** for batch processing with explicit validation at transitions (draft → matching → review → reconciled)
- **Wizard vs Widget**: TransientModel for simple flows; OWL for complex interactive UI

**Data flow (batch reconciliation):**
```
[User Selects 80 Lines] → [Create Batch] → [MatchingEngine.find_matches()]
→ [Store Suggestions] → [Present in OWL Widget] → [User Confirms/Modifies]
→ [Batch.action_reconcile()] → [For Each: statement_line.reconcile_with_move()]
→ [Creates journal entries] → [Updates is_reconciled = True] → [Batch State = Done]
```

### Critical Pitfalls

Research uncovered 7 critical pitfalls with high impact potential. Top 5 require architecture-level prevention from Phase 1:

1. **N+1 Query Performance Degradation** — Transforms 2-second batch operation into 2-minute operation
   - **Cause**: Iterating through recordsets without prefetching; accessing relational fields in loops
   - **Prevention**: Browse entire recordsets before loops; use `_read_group` for aggregations; leverage automatic prefetching
   - **Warning signs**: Processing time scales linearly (10 lines = 5s, 80 lines = 40s); hundreds of similar SELECT queries
   - **Phase to address**: Phase 1 (Core Architecture) — build with proper ORM patterns from start

2. **Race Conditions and Concurrent Update Conflicts** — Reconciliation appears successful but silently fails
   - **Cause**: Multiple users/processes modifying same `account.move.line` records simultaneously; PostgreSQL serialization errors
   - **Prevention**: SELECT FOR UPDATE locking when fetching move lines; retry logic with exponential backoff; smaller chunks with commits
   - **Warning signs**: "Concurrent update" errors; reconciliations mysteriously disappearing; partner balance discrepancies
   - **Phase to address**: Phase 2 (Auto-matching Engine) — add transaction management when building matching algorithm

3. **False Positive Matches Due to Insufficient Validation** — Wrong transactions reconciled; creates phantom balances
   - **Cause**: Relying solely on amount matching; ignoring date ranges; not validating move line availability
   - **Prevention**: Multi-factor matching (amount + partner + date + reference); confidence scoring; validate account.reconcile flag, posted state
   - **Warning signs**: Users frequently reverting reconciliations; balance sheet showing unexpected balances; customer statements not matching
   - **Phase to address**: Phase 2 (Auto-matching Engine) — build validation into core algorithm

4. **Cache Invalidation Causing Performance Collapse** — 5-second operation becomes 5-minute operation
   - **Cause**: Calling `invalidate_cache()` without parameters; `mail.thread` inheritance invalidating all caches on every write
   - **Prevention**: Specify fields when invalidating: `invalidate_model(['state', 'reconciled'])`; avoid `mail.thread` on high-volume models
   - **Warning signs**: Same SELECT queries executed multiple times; performance degrading non-linearly; workers becoming unresponsive
   - **Phase to address**: Phase 1 (Core Architecture) — establish proper cache management patterns early

5. **Floating Point Rounding Errors in Multi-Currency** — 0.01 differences prevent automatic reconciliation
   - **Cause**: Python float arithmetic loses precision; Odoo rounds each line individually then sums
   - **Prevention**: Use `float_compare(amount1, amount2, precision_rounding=currency.rounding)`; never use direct `==` for money
   - **Warning signs**: Reconciliations failing with 0.01 differences; exchange difference amounts accumulating unexpectedly
   - **Phase to address**: Phase 2 (Auto-matching Engine) — build rounding tolerance into matching

**Additional critical pitfalls:**
- **Breaking Odoo's Accounting Constraints** — Bypassing validation with SQL/sudo() corrupts financial reports; always use ORM
- **Upgrade and Migration Compatibility Failures** — Depending on private Odoo APIs breaks on upgrade; use only public APIs with version checks

## Implications for Roadmap

Based on combined research, recommend 4-phase structure following strict dependency order with early risk mitigation.

### Phase 1: Foundation Models & Core Architecture
**Rationale:** Data layer and architectural patterns must be established before business logic can operate. N+1 query patterns and cache management baked in from start; retrofitting later requires complete refactoring.

**Delivers:**
- `mass.reconcile.batch` model with state machine (draft → matching → review → reconciled)
- Extended `account.bank.statement.line` with batch_id, match_score fields
- `mass.reconcile.match` model for storing suggestions with audit trail
- Security model (ir.model.access.csv, record rules)
- Proper ORM patterns: recordset batching, prefetching, field-specific cache invalidation

**Addresses features:**
- Foundation for mass/bulk reconciliation capability
- Undo/unreconcile infrastructure (state tracking for reversal)
- Audit trail storage (who reconciled what when)

**Avoids pitfalls:**
- Pitfall #1 (N+1 queries): Build with batch ORM queries from start
- Pitfall #4 (cache invalidation): Establish field-specific invalidation patterns
- Pitfall #6 (accounting constraints): Implement validation layer with @api.constrains
- Pitfall #7 (upgrade compatibility): Use only public Odoo APIs; add version checks

**Research needs:** None — well-documented Odoo model patterns

---

### Phase 2: Matching Engine & Auto-Reconciliation
**Rationale:** Core business logic must work correctly before building UI. Service-pattern separation enables independent testing of matching algorithms before integration complexity.

**Delivers:**
- `MatchingEngine` service class with scoring algorithm
- Multi-factor matching: amount (40 pts) + partner (30 pts) + reference (30 pts) + date range validation
- Confidence score calculation (exact/probable/possible thresholds)
- Transaction isolation with SELECT FOR UPDATE locking
- Floating-point comparison using `float_compare()` for currency precision
- Validation: account.reconcile flag, posted state, not already reconciled, same account on all lines

**Uses stack:**
- Python 3.12 for service classes
- OCA account_reconcile_model_oca for rule-based matching integration
- PostgreSQL indexes on partner_id, amount, payment_ref for candidate search
- Odoo ORM RecordSet API for batch queries

**Implements architecture:**
- Business Logic Layer: MatchingEngine service
- Integration Layer: account.reconcile.model._apply_rules() bridge

**Addresses features:**
- Exact amount + reference matching (table stakes)
- Partner-based filtering (table stakes)
- Confidence scoring (differentiator)
- Basic reconciliation models integration (table stakes)
- Internal transfer matching (table stakes)
- Search month limits (date tolerance)

**Avoids pitfalls:**
- Pitfall #2 (race conditions): Add SELECT FOR UPDATE locking and transaction management
- Pitfall #3 (false positives): Multi-factor validation with confidence thresholds
- Pitfall #5 (rounding errors): Use float_compare with currency.rounding precision
- Pitfall #11 (duplicates): Check reconciled field before matching

**Research needs:** SKIP — standard Odoo reconciliation patterns well-documented

---

### Phase 3: Manual Review Interface & Wizard Flow
**Rationale:** Simpler UI pattern (wizard) validates full flow end-to-end before building complex batch widget. Handles 20-40% of transactions automation misses.

**Delivers:**
- `MassReconcileWizard` TransientModel with multi-step form
- Step 1: Select lines (80 line limit) with date range filtering
- Step 2: Review matches with confidence scores and approve/reject
- Write-off small differences UI (<$10 configurable threshold)
- Validate/confirm action with preview before commit
- "To Check" workflow for flagging uncertain matches
- Clear error messages with actionable guidance
- Reversal/undo functionality with complete cleanup

**Uses stack:**
- models.TransientModel for wizard data (auto-vacuumed)
- Form views with standard Odoo view architecture
- Server-side validation and processing

**Implements architecture:**
- Presentation Layer: Wizard views (sequential flow)
- Integration with MatchingEngine: call find_matches(), action_reconcile()

**Addresses features:**
- Manual reconciliation UI (table stakes)
- "To Check" workflow (table stakes)
- Validate/confirm action (table stakes)
- Write-off small differences (table stakes)
- Undo/unreconcile (table stakes)
- Date range filtering (table stakes)

**Avoids pitfalls:**
- Pitfall #10 (error handling): Structured error messages with user notifications
- Pitfall #15 (partial reconciliations): Proper partial reconciliation workflow with clear UI

**Research needs:** SKIP — standard TransientModel wizard patterns

---

### Phase 4: Batch UI Widget & Progress Indicators
**Rationale:** Complex interactive UI built last, after validating business logic works. Delivers the primary differentiator (mass 80-line processing) with optimal UX.

**Delivers:**
- `BatchReconcileWidget` OWL 2 component with reactive state
- Batch loading and display (80 lines with pagination)
- Real-time progress indicators ("42/80 processed — 85% complete")
- Color-coded confidence levels (green = exact, yellow = probable, red = review needed)
- Keyboard shortcuts for bulk operations
- Selection and approval UI with drag-to-group
- Preview mode showing all proposed matches before commit
- No page refresh interaction (full client-side state management)

**Uses stack:**
- OWL 2 (built-in Odoo 18) with useState() for reactive state
- JavaScript ES6+ for client-side logic
- QWeb templates for component rendering
- RPC calls via orm service for backend communication

**Implements architecture:**
- Presentation Layer: OWL Widget (interactive bulk operations)
- Widget just calls Python backend methods; no business logic in JS

**Addresses features:**
- **Mass/bulk reconciliation (80+ lines)** — PRIMARY DIFFERENTIATOR
- Progress indicators (differentiator)
- Confidence scoring visualization
- One-click batch operations

**Avoids pitfalls:**
- Pitfall #8 (anti-pattern): Keep business logic in Python; widget only presentation layer via RPC

**Research needs:** SKIP — OWL 2 framework well-documented in Odoo 18

---

### Phase 5+ (Future/v2): Automation & Scale
**Rationale:** Automation layer sits on top of proven manual flow. Defer until core validated with real users.

**Future additions:**
- Queue-based auto-reconciliation (account_reconcile_oca_queue) for 200+ line batches
- Cron jobs for scheduled auto-matching
- Notification system for automated reconciliation results
- Reconciliation analytics dashboard
- Multi-currency support (if not included in Phase 2)

---

### Phase Ordering Rationale

**Dependency-driven sequence:**
1. **Models before logic** — Matching engine needs batch_id, match_score fields to exist
2. **Logic before UI** — Wizard and widget call matching engine methods; must work first
3. **Wizard before widget** — Simpler UI validates full flow; complex UI built on proven backend
4. **Manual before automation** — Automated processes use same reconciliation methods; validate manually first

**Risk mitigation priorities:**
- **Phase 1 addresses 4 of 7 critical pitfalls** — Architecture-level prevention (N+1 queries, cache, constraints, upgrades)
- **Phase 2 addresses remaining 3 critical pitfalls** — Algorithm-level prevention (race conditions, false positives, rounding)
- **Phase 3 addresses moderate pitfalls** — UX and workflow (error handling, partial reconciliations)

**Iterative validation:**
- Each phase produces testable artifact before next begins
- Phase 1: Test models in isolation with unit tests
- Phase 2: Test matching engine independently with mock data
- Phase 3: Test full manual flow end-to-end with wizard
- Phase 4: Add rich UI on top of proven backend

### Research Flags

**Phases with standard patterns (skip phase-specific research):**
- **Phase 1 (Foundation Models)**: Standard Odoo model inheritance patterns well-documented
- **Phase 2 (Matching Engine)**: Reconciliation APIs documented in Odoo 18.0 official docs
- **Phase 3 (Manual Interface)**: TransientModel wizard pattern is standard Odoo
- **Phase 4 (Batch Widget)**: OWL 2 framework documented in Odoo 18 reference

**No phases require `/gsd:research-phase`** — Domain research is comprehensive and high-confidence. Proceed directly to requirements definition.

**Validation checkpoints during implementation:**
- **Phase 1 completion**: Run profiler on 1,000 line batch — should execute <50 queries (validates N+1 prevention)
- **Phase 2 completion**: Test 5 concurrent users reconciling same statements — no errors (validates locking)
- **Phase 2 completion**: Manual review of 100 auto-matches — <2% error rate (validates matching algorithm)
- **Phase 4 completion**: Load widget with 1,000 unreconciled lines — <2 seconds (validates performance)

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | All versions verified via official Odoo 18.0 documentation and GitHub repository. OCA module maturity confirmed (versions >= 1.0.0). No conflicting sources. |
| Features | **HIGH** | Table stakes identified from official Odoo 18/19 reconciliation docs. Differentiators validated via OCA module analysis and community consensus. Anti-features grounded in documented pitfalls. |
| Architecture | **MEDIUM-HIGH** | Standard patterns well-documented in Odoo 18 developer docs. Service class pattern inferred from best practices (not explicit Odoo standard). OWL 2 architecture verified. State machine pattern is established Odoo convention. |
| Pitfalls | **HIGH** | Critical pitfalls sourced from Odoo GitHub issues with detailed reproduction cases. Performance issues (N+1, cache) documented in official Odoo 18 performance guide. Currency rounding and concurrent update issues have specific GitHub issue numbers. |

**Overall confidence: HIGH**

Research is comprehensive with primary sources (official Odoo 18 documentation, Odoo GitHub repository, OCA repositories) for all critical decisions. Architecture patterns inferred from best practices have medium confidence but are standard in Odoo community. No conflicting information across sources.

### Gaps to Address

**Minor gaps requiring validation during implementation:**

1. **Optimal batch size (80 lines)** — Research suggests 80 lines based on performance considerations and UI practicality, but exact threshold should be validated in testing
   - **Validation approach**: Performance test with 50, 80, 100, 150 lines; find point where UI becomes unwieldy or queries degrade
   - **Risk**: LOW — easy to make configurable if different threshold works better

2. **Confidence score thresholds** — Proposed 100% exact / 90% probable / 50% possible scoring needs calibration with real data
   - **Validation approach**: Test with sample bank statements and invoices; tune thresholds to achieve <2% false positive rate
   - **Risk**: LOW — can adjust post-launch based on user feedback

3. **OCA module compatibility** — Assumed account_reconcile_model_oca works as documented; should verify integration in dev environment
   - **Validation approach**: Install OCA module in Phase 1; test reconciliation model functionality before building matching engine
   - **Risk**: LOW — OCA module is production-ready (v18.0.1.1.1) with active maintenance

4. **Multi-currency handling** — Research identified rounding pitfall but deferred full multi-currency support to v2; may need earlier if users require it
   - **Validation approach**: Ask during requirements if users need foreign currency reconciliation immediately
   - **Risk**: MEDIUM — adding later requires refactoring matching algorithm for currency precision

**No blocking gaps.** All gaps have clear validation approaches and low-to-medium risk. Proceed to roadmap creation.

## Sources

### Primary (HIGH confidence)

**Official Odoo Documentation:**
- [Odoo 18.0 Developer Documentation](https://www.odoo.com/documentation/18.0/developer/) — Framework overview, ORM, views, OWL components, testing
- [Odoo 18.0 Bank Reconciliation](https://www.odoo.com/documentation/18.0/applications/finance/accounting/bank/reconciliation.html) — User-facing reconciliation workflows
- [Odoo 18.0 Reconciliation Models](https://www.odoo.com/documentation/18.0/applications/finance/accounting/bank/reconciliation_models.html) — Rule-based matching patterns
- [Odoo 18.0 Performance Guide](https://www.odoo.com/documentation/18.0/developer/reference/backend/performance) — ORM optimization, cache management
- [Odoo 18.0 ORM Reference](https://www.odoo.com/documentation/18.0/developer/reference/backend/orm) — RecordSet API, prefetching, transactions

**Odoo Repository Sources:**
- [odoo/odoo GitHub - 18.0 branch](https://github.com/odoo/odoo/tree/18.0) — requirements.txt, module structure, accounting models
- [odoo/odoo GitHub Issues](https://github.com/odoo/odoo/issues) — Issue #30934 (performance), #91873 (concurrency), #13846 (partner updates), #23172 (cache invalidation)
- [OCA/account-reconcile GitHub - 18.0 branch](https://github.com/OCA/account-reconcile) — account_reconcile_model_oca, account_reconcile_oca modules

**Context7:**
- /websites/odoo_18_0_developer — Verified form views, OWL components, ORM patterns

### Secondary (MEDIUM confidence)

**Community Resources:**
- [PySquad: Odoo 18 OWL JS Improvements](https://pysquad.com/blogs/odoo-18-owl-js-key-improvements-over-odoo-17) — OWL 2 features
- [The Ledger Labs - Odoo Bank Reconciliation Guide](https://theledgerlabs.com/odoo-bank-reconciliation-guide/) — Workflow best practices
- [Cybrosys: Odoo 18 Reconciliation Models](https://www.cybrosys.com/blog/overview-of-odoo-18-accounting-reconciliation-models) — Reconciliation patterns
- [HSX Tech - Best Practices for Reconciliation](https://hsxtech.net/best-practices-for-reconciliation-in-odoo-accounting/) — Common pitfalls

**Development Tools:**
- [GitHub: camptocamp/pytest-odoo](https://github.com/camptocamp/pytest-odoo) — pytest integration
- [GitHub: OCA/odoo-pre-commit-hooks](https://github.com/OCA/odoo-pre-commit-hooks) — Linting hooks

### Tertiary (LOW confidence)

**Industry Analysis:**
- [12 Best Reconciliation Tools: Ultimate Guide 2026](https://www.solvexia.com/blog/5-best-reconciliation-tools-complete-guide) — Market feature comparison
- [The 10 best account reconciliation software in 2026 | Prophix](https://www.prophix.com/blog/the-10-best-account-reconciliation-software/) — Competitive landscape

**Odoo Apps Store:**
- [account_reconcile_model_oca](https://apps.odoo.com/apps/modules/18.0/account_reconcile_model_oca) — OCA reconciliation models
- Commercial reconciliation apps (various) — Feature inspiration (not implementation guidance)

---
*Research completed: 2026-02-12*
*Ready for roadmap: yes*
