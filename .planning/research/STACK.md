# Stack Research

**Domain:** Odoo 18.0 Community Bank Reconciliation Module
**Researched:** 2026-02-12
**Confidence:** HIGH

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Odoo Community | 18.0 | ERP framework and base accounting module | Standard for Odoo development; provides account.bank.statement.line model, ORM, and accounting infrastructure. Version 18.0 is the target platform with active development and OCA support. |
| Python | 3.10 - 3.12 | Backend language | Minimum Python 3.10 required by Odoo 18.0. Python 3.12 recommended for best performance and security. Odoo 18.0 supports 3.10, 3.11, 3.12; experimental support for 3.13. |
| PostgreSQL | 15+ | Database | PostgreSQL 15+ is highly recommended for Odoo 18/19 (minimum 12.0 supported). Required for all Odoo installations; provides ACID compliance and advanced query features used by Odoo ORM. |

**Confidence:** HIGH - All versions verified via official Odoo 18.0 documentation and GitHub repository.

### Backend Framework Components

| Component | Version/Pattern | Purpose | Why Recommended |
|-----------|-----------------|---------|-----------------|
| Odoo ORM (models.Model) | Built-in | Data models for persistent storage | Standard Odoo pattern for business logic. Use for reconciliation result storage, configuration models. Integrates with existing account module. |
| Odoo TransientModel | Built-in | Wizard/temporary forms | Standard pattern for multi-step wizards. Auto-vacuumed data (no long-term storage). Use for batch processing wizard, manual review interface. |
| Odoo RecordSet API | Built-in | ORM query interface | High-level abstraction over SQL. Use for querying bank statements, invoices, matching logic. Provides search(), filtered(), mapped(), etc. |
| Module Structure | Standard Odoo | Module organization | Required __manifest__.py with metadata, /models for Python, /views for XML, /security for access rules, /data for seed data. |

**Confidence:** HIGH - Official Odoo 18.0 developer documentation patterns.

### Frontend Framework

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| OWL 2 (Odoo Web Library) | Built-in Odoo 18 | JavaScript component framework | Native Odoo 18 framework. Replaces legacy jQuery/Backbone. Provides reactive components (~20kb gzipped). Inspired by React/Vue with automatic reactivity. |
| JavaScript ES6+ | Modern | Client-side logic | Required for OWL 2 components. Use for batch processing widgets, real-time matching preview. |
| QWeb Templates | Built-in | XML-based templating | Odoo's standard for both server-side and client-side rendering. Use with OWL components via t-name attributes. |

**Confidence:** HIGH - Verified via Odoo 18.0 official documentation and PySquad analysis.

**OWL 2 Key Features:**
- Automatic reactivity (no manual render() calls)
- Enhanced lifecycle hooks (onMounted, onWillStart, onWillUnmount)
- Reactive state via useState() and reactive()
- Class-based components with TypeScript support

### View Types

| View Type | XML Tag | Purpose | When to Use |
|-----------|---------|---------|-------------|
| Form View | `<form>` | Single record editing | Configuration screens, reconciliation result details |
| Tree View | `<tree>` | List/table display | Bank statement line lists, invoice search results |
| Wizard View | `<form>` with TransientModel | Multi-step processes | Batch reconciliation wizard, manual review workflow |
| Kanban View | `<kanban>` | Card-based display | Optional: visual reconciliation status board |
| Search View | `<search>` | Filter/group/search | Required for filtering statements by date range, amount, status |

**Confidence:** HIGH - Standard Odoo view architecture from official documentation.

### Python Dependencies

| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| psycopg2 | 2.9.9+ | PostgreSQL adapter | Required for Odoo database access. Version depends on Python version (2.9.9 for 3.12+). |
| Werkzeug | 3.0.1+ | WSGI web framework | Odoo's HTTP layer. Use 3.0.1+ for Python 3.12+. |
| lxml | 5.2.1+ | XML processing | Required for view definitions, data files. Use 5.2.1+ for Python 3.12+. |
| Pillow | 10.2.0+ | Image processing | May be needed if module includes reports with images. |
| Babel | 2.10.3+ | Internationalization | Required for multi-language support in reconciliation messages. |

**Confidence:** HIGH - Extracted from odoo/odoo requirements.txt for 18.0 branch.

### Supporting OCA Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| account_reconcile_model_oca | 18.0.1.1.1 | Reconciliation models logic | Core dependency - restores reconciliation models moved from Community to Enterprise in v17. Essential for pattern-based matching. |
| account_reconcile_oca | 18.0.1.1.7 | Enhanced reconciliation UI | Optional but recommended - provides better reconciliation interface for Community edition. Use if replacing default reconciliation UI. |
| account_statement_base | 18.0.1.2.0 | Bank statement base functionality | May be required dependency for advanced statement processing. |
| account_reconcile_oca_queue | 18.0.1.1.0 | Background job reconciliation | Optional - use if processing 200+ lines and need async processing via queue_job module. |

**Confidence:** HIGH - Verified via OCA GitHub account-reconcile repository 18.0 branch.

**OCA Module Maturity:** All listed modules are available for 18.0 with version >= 1.0.0, indicating production readiness.

### Testing Framework

| Tool | Purpose | Why Recommended |
|------|---------|-----------------|
| unittest (Python stdlib) | Base test framework | Standard Odoo testing approach. Use odoo.tests.TransactionCase for model tests. Each test method runs in sub-transaction (savepoint). |
| pytest-odoo | Test runner | Optional but recommended for TDD. Provides pytest CLI comfort for Odoo tests. Supports pytest-xdist for parallel test execution. |
| Odoo Test Tags | Test categorization | Use @tagged('post_install', 'at_install', '-standard') to control test execution. Standard Odoo pattern for filtering tests. |
| Browser Tests (Tours) | Integration testing | Use for testing wizard flows, batch processing UI. Odoo provides tour framework for automated browser interactions. |

**Confidence:** HIGH - Official Odoo 18.0 testing documentation and pytest-odoo GitHub.

**Test Execution:**
```bash
# Native Odoo
odoo-bin -d test_db --test-enable --test-tags=mass_reconcile

# pytest-odoo (recommended for TDD)
pytest --odoo-database=test_db addons/mass_reconcile/tests/
```

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Ruff | Python linting/formatting | Extremely fast linter written in Rust. OCA supports via ruff-odoo fork adapted for Odoo. Use as pre-commit hook. |
| ESLint | JavaScript linting | Required for OWL component code quality. Copy eslint config to repo root, install node modules, configure git hooks. |
| pre-commit | Git hooks manager | Use OCA/odoo-pre-commit-hooks for Odoo-specific checks (prefer-env-translation for >=18.0, unused logger detection). |

**Confidence:** MEDIUM - Based on OCA best practices and community tooling. Official Odoo doesn't mandate specific linters.

## Installation

```bash
# Core Odoo 18.0 Community (from source)
git clone --depth 1 --branch 18.0 https://github.com/odoo/odoo.git
cd odoo
pip install -r requirements.txt

# OCA Dependencies (optional but recommended)
pip install git+https://github.com/OCA/account-reconcile.git@18.0#subdirectory=account_reconcile_model_oca
pip install git+https://github.com/OCA/account-reconcile.git@18.0#subdirectory=account_reconcile_oca

# Testing Tools
pip install pytest-odoo  # Optional, for TDD workflow

# Development Tools
pip install ruff pre-commit
npm install -g eslint prettier  # For JavaScript linting
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Odoo ORM | Raw SQL | Never for this use case - bypasses Odoo security, recordset API, and breaks ORM abstractions. Use ORM for all data access. |
| OWL 2 Components | Legacy jQuery/Backbone | Never - deprecated in Odoo 14+. All new development must use OWL. |
| TransientModel | models.Model for wizards | Never - TransientModel auto-vacuums data. Using models.Model for temporary data creates database bloat. |
| unittest/pytest-odoo | Manual testing | Never for production - automated tests required for bank reconciliation due to financial data sensitivity. |
| Python 3.12 | Python 3.10/3.11 | Use 3.10/3.11 only if deployment environment constrains Python version. Otherwise prefer 3.12 for performance. |
| account_reconcile_oca | Custom reconciliation UI | Use custom only if OCA module doesn't meet specific requirements. OCA module is battle-tested and maintained. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Odoo Enterprise features | Not available in Community edition. Module must run on Community only. | Use OCA account_reconcile_model_oca to restore Enterprise features moved in v17. |
| Python < 3.10 | Not supported by Odoo 18.0. Will fail on import. | Python 3.10 minimum, 3.12 recommended. |
| PostgreSQL < 12.0 | Not supported by Odoo 18.0. May have compatibility issues. | PostgreSQL 15+ recommended. |
| Direct database manipulation | Bypasses Odoo ORM, security rules, computed fields, and audit trails. Financial data requires full audit. | Always use Odoo ORM (self.env['model.name']). |
| jQuery for new code | Deprecated in Odoo 14+. Not compatible with OWL architecture. | Use OWL 2 components exclusively. |
| models.Model for wizards | Creates permanent records, database bloat. Not auto-vacuumed. | Use models.TransientModel for all temporary/wizard data. |
| Synchronous batch processing | Blocks HTTP worker for large batches (200+ lines). Poor UX. | Use account_reconcile_oca_queue with queue_job module for async processing. |
| Python 3.13 | Experimental support in Odoo 18.0. Some packages not fully compatible (cgi module deprecated). | Stick to Python 3.10-3.12 for production until 3.13 fully supported. |

## Stack Patterns by Project Phase

**Phase 1: Core Reconciliation Engine**
- models.Model for configuration (reconciliation rules, thresholds)
- Pure Python matching logic (no UI)
- unittest.TransactionCase for matching algorithm tests
- ORM only - no SQL

**Phase 2: Batch Processing**
- models.TransientModel for batch wizard
- Form view with batch selection
- Tree view for statement line display
- Server-side batch processing (no async yet)

**Phase 3: Enhanced UI**
- OWL 2 components for interactive widgets
- QWeb templates for real-time preview
- Search views for advanced filtering
- JavaScript for client-side validation

**Phase 4: Production Hardening**
- account_reconcile_oca_queue for async processing
- Browser tests (tours) for wizard flows
- Performance optimization (batch ORM queries)
- Pre-commit hooks for code quality

## Version Compatibility

| Odoo Version | Python | PostgreSQL | OWL | OCA Modules |
|--------------|--------|------------|-----|-------------|
| 18.0 | 3.10-3.12 (3.13 experimental) | 12.0+ (15+ recommended) | OWL 2 (built-in) | account-reconcile 18.0 branch |

**Breaking Changes from Odoo 17:**
- Reconciliation models moved from Community to Enterprise in v17 (restored in OCA account_reconcile_model_oca)
- OWL 2 automatic reactivity (no more manual render() calls)
- Prefer self.env._('text') over _('text') for translations (>=18.0)

## Odoo-Specific Patterns

### ORM Query Patterns
```python
# Good - Efficient batch query
statement_lines = self.env['account.bank.statement.line'].search([
    ('state', '=', 'unreconciled'),
    ('amount', '>', 0),
    ('date', '>=', date_from),
    ('date', '<=', date_to)
], limit=80)

# Bad - N+1 query problem
for line in statement_lines:
    partner = self.env['res.partner'].search([('name', '=', line.partner_name)])  # Queries in loop

# Good - Prefetch using mapped()
invoices = statement_lines.mapped('partner_id.invoice_ids')
```

### Reconciliation Model Pattern
```python
class MassReconcileWizard(models.TransientModel):
    _name = 'mass.reconcile.wizard'
    _description = 'Mass Bank Reconciliation Wizard'

    statement_line_ids = fields.Many2many('account.bank.statement.line')

    def action_reconcile(self):
        # Use account_reconcile_model_oca for matching
        reconcile_model = self.env['account.reconcile.model']
        for line in self.statement_line_ids:
            matches = reconcile_model._apply_rules(line, line.partner_id)
            if matches:
                line.reconcile(matches)
```

### OWL 2 Component Pattern
```javascript
// Good - OWL 2 with automatic reactivity
import { Component, useState } from "@odoo/owl";

export class ReconcileWidget extends Component {
    static template = "mass_reconcile.ReconcileWidget";

    setup() {
        this.state = useState({
            matches: [],
            selectedMatch: null
        });
    }

    selectMatch(match) {
        this.state.selectedMatch = match;  // Automatically triggers re-render
    }
}
```

## Sources

### Official Documentation (HIGH confidence)
- [Odoo 18.0 Developer Documentation](https://www.odoo.com/documentation/18.0/developer/) - Framework overview, ORM, views
- [Odoo 18.0 Module Manifests](https://www.odoo.com/documentation/18.0/developer/reference/backend/module.html) - Module structure
- [Odoo 18.0 Testing Documentation](https://www.odoo.com/documentation/18.0/developer/reference/backend/testing.html) - unittest patterns
- [Odoo 18.0 OWL Components](https://www.odoo.com/documentation/18.0/developer/reference/frontend/owl_components.html) - OWL 2 framework
- [Odoo 18.0 Bank Reconciliation](https://www.odoo.com/documentation/18.0/applications/finance/accounting/bank/reconciliation.html) - User-facing reconciliation docs
- [Odoo 18.0 Reconciliation Models](https://www.odoo.com/documentation/18.0/applications/finance/accounting/bank/reconciliation_models.html) - Reconciliation model patterns

### Repository Sources (HIGH confidence)
- [odoo/odoo GitHub - 18.0 requirements.txt](https://github.com/odoo/odoo/blob/18.0/requirements.txt) - Python dependency versions
- [OCA/account-reconcile GitHub - 18.0 branch](https://github.com/OCA/account-reconcile) - Community reconciliation modules
- [odoo/owl GitHub](https://github.com/odoo/owl) - OWL framework repository

### Context7 (HIGH confidence)
- /websites/odoo_18_0_developer - Verified form views, OWL components, ORM patterns

### Community Resources (MEDIUM confidence)
- [PySquad: Odoo 18 OWL JS Improvements](https://pysquad.com/blogs/odoo-18-owl-js-key-improvements-over-odoo-17) - OWL 2 features
- [Cybrosys: Odoo 18 Module Structure](https://www.cybrosys.com/blog/an-overview-of-the-module-structure-in-odoo-18) - Module organization
- [Cybrosys: Odoo 18 Reconciliation Models](https://www.cybrosys.com/blog/overview-of-odoo-18-accounting-reconciliation-models) - Reconciliation patterns

### Development Tools (MEDIUM confidence)
- [GitHub: camptocamp/pytest-odoo](https://github.com/camptocamp/pytest-odoo) - pytest integration
- [GitHub: OCA/odoo-pre-commit-hooks](https://github.com/OCA/odoo-pre-commit-hooks) - Odoo linting hooks
- [GitHub: fda-odoo/ruff-odoo](https://github.com/fda-odoo/ruff-odoo) - Ruff for Odoo

### Odoo Apps Store (MEDIUM confidence)
- [account_reconcile_model_oca](https://apps.odoo.com/apps/modules/18.0/account_reconcile_model_oca) - OCA reconciliation models
- [OCA Module Installation Guide](https://oec.sh/guides/oca-modules-guide) - OCA best practices

---
*Stack research for: Odoo 18.0 Community Bank Reconciliation*
*Researched: 2026-02-12*
*Overall Confidence: HIGH (core stack), MEDIUM (development tooling)*
