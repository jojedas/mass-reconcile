# Phase 1: Foundation Models & Data Layer - Research

**Researched:** 2026-02-12
**Domain:** Odoo 18.0 Community ORM, models, security, and accounting module extension
**Confidence:** HIGH

## Summary

Phase 1 establishes the data layer foundation for mass bank reconciliation in Odoo 18.0 Community. The research confirms that Odoo 18.0 provides robust patterns for creating models, implementing state machines, managing security, and optimizing performance through proper ORM usage. The key challenge is avoiding N+1 queries and ensuring upgrade compatibility by using only public Odoo APIs.

The Odoo ORM includes built-in prefetching, caching, and batch operation support. The security model uses a two-tier approach: ir.model.access.csv for model-level permissions and ir.rule records for row-level security. The OCA account-reconcile repository provides battle-tested patterns for extending bank reconciliation, particularly the account_reconcile_model_oca module which restores enterprise features to community edition.

**Primary recommendation:** Use models.Model for persistent data with proper ORM prefetching patterns, implement security via CSV access rights and XML record rules, validate with @api.constrains decorators, and leverage mail.thread mixin for audit trails. Structure models to minimize dependency chains in computed fields.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Odoo Community | 18.0 | ERP framework and ORM | Target platform specified in requirements |
| Python | 3.12 | Programming language | Odoo 18.0 compatible runtime |
| PostgreSQL | 15+ | Database backend | Odoo's required database |
| OCA account_reconcile_model_oca | 18.0.1.1.1 | Reconciliation model patterns | Restores enterprise reconciliation features to community, provides proven extension patterns |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| mail.thread mixin | 18.0 (built-in) | Audit trail and change tracking | For models requiring who/when/what change history |
| mail.activity.mixin | 18.0 (built-in) | Activity management | For user tasks and follow-ups (not needed in Phase 1) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| models.Model | models.TransientModel | TransientModel for temporary wizards only, not persistent data |
| OCA account_reconcile_model_oca | Custom reconciliation logic | OCA module provides enterprise features, tested patterns, and upgrade path |
| mail.thread tracking | Manual logging | Manual approach loses integration with chatter, notifications, and Odoo's audit infrastructure |

**Installation:**
```bash
# Odoo 18.0 Community already installed per project context
# Install OCA account-reconcile repository modules
pip install odoo-addon-account-reconcile-model-oca==18.0.1.1.1
```

## Architecture Patterns

### Recommended Project Structure
```
mass_reconcile/
├── __init__.py                     # Module initialization
├── __manifest__.py                 # Module metadata and dependencies
├── models/
│   ├── __init__.py                 # Model imports
│   ├── mass_reconcile_batch.py     # Batch model with state machine
│   ├── account_bank_statement_line.py  # Extension of bank statement lines
│   └── mass_reconcile_match.py     # Match proposal model
├── security/
│   ├── ir.model.access.csv         # Model-level access rights
│   └── mass_reconcile_security.xml # Record rules (row-level security)
├── data/                           # Optional: demo data
└── views/                          # Phase 2 concern
```

### Pattern 1: Model Definition with State Machine
**What:** Create persistent models inheriting from models.Model with Selection fields for state management
**When to use:** For batch tracking, workflow management, and any multi-state entity
**Example:**
```python
# Source: https://www.odoo.com/documentation/18.0/developer/tutorials/server_framework_101/03_basicmodel
# Source: https://www.odoo.com/documentation/18.0/developer/reference/backend/mixins
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MassReconcileBatch(models.Model):
    _name = 'mass.reconcile.batch'
    _description = 'Mass Reconciliation Batch'
    _inherit = ['mail.thread']  # For audit trail

    name = fields.Char(string='Batch Name', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('matching', 'Matching'),
        ('review', 'Review'),
        ('reconciled', 'Reconciled')
    ], default='draft', required=True, tracking=True)

    company_id = fields.Many2one('res.company', required=True,
                                  default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Responsible',
                              default=lambda self: self.env.user,
                              tracking=True)

    # Button methods for state transitions
    def action_start_matching(self):
        self.ensure_one()
        self.state = 'matching'

    def action_move_to_review(self):
        self.ensure_one()
        self.state = 'review'

    def action_reconcile(self):
        self.ensure_one()
        # Perform reconciliation logic here
        self.state = 'reconciled'
```

### Pattern 2: Extending Existing Models
**What:** Use _inherit without _name to add fields to existing Odoo models
**When to use:** Adding fields to account.bank.statement.line or other core accounting models
**Example:**
```python
# Source: https://www.odoo.com/documentation/18.0/developer/tutorials/server_framework_101/12_inheritance
from odoo import models, fields

class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    batch_id = fields.Many2one('mass.reconcile.batch',
                               string='Reconciliation Batch',
                               index=True,
                               ondelete='set null')
    match_score = fields.Float(string='Match Score',
                               help='Confidence score for suggested match')
    suggested_move_id = fields.Many2one('account.move',
                                        string='Suggested Move',
                                        help='Suggested accounting move for reconciliation')
```

### Pattern 3: ORM Prefetching for Performance
**What:** Use browse on entire recordset before iteration to enable batch prefetching
**When to use:** Any loop over records where you access fields, especially relational fields
**Example:**
```python
# Source: https://www.odoo.com/documentation/18.0/developer/reference/backend/performance
# BAD - N+1 queries
for record_id in record_ids:
    record = model.browse(record_id)
    print(record.name)  # One query per record

# GOOD - Single batch query
records = model.browse(record_ids)
for record in records:
    print(record.name)  # One query for all records
```

### Pattern 4: Batch Operations with _read_group
**What:** Replace individual search_count calls with single _read_group query
**When to use:** Computing counts or aggregates on related records
**Example:**
```python
# Source: https://www.odoo.com/documentation/18.0/developer/reference/backend/performance
# BAD - Individual queries
def _compute_match_count(self):
    for batch in self:
        domain = [('batch_id', '=', batch.id)]
        batch.match_count = self.env['mass.reconcile.match'].search_count(domain)

# GOOD - Single batch query
def _compute_match_count(self):
    domain = [('batch_id', 'in', self.ids)]
    counts_data = self.env['mass.reconcile.match']._read_group(
        domain, ['batch_id'], ['__count'])
    mapped_data = dict(counts_data)
    for batch in self:
        batch.match_count = mapped_data.get(batch, 0)
```

### Pattern 5: Validation with @api.constrains
**What:** Use @api.constrains decorator for Python constraints, _sql_constraints for database-level rules
**When to use:** Enforcing business rules and data integrity before database writes
**Example:**
```python
# Source: https://www.odoo.com/documentation/18.0/developer/tutorials/server_framework_101/10_constraints
from odoo import api, models, fields
from odoo.exceptions import ValidationError

class MassReconcileMatch(models.Model):
    _name = 'mass.reconcile.match'

    match_score = fields.Float(required=True)

    _sql_constraints = [
        ('check_score_range',
         'CHECK(match_score >= 0 AND match_score <= 100)',
         'Match score must be between 0 and 100')
    ]

    @api.constrains('match_score')
    def _check_match_score(self):
        for record in self:
            if record.match_score < 0 or record.match_score > 100:
                raise ValidationError("Match score must be between 0 and 100")
```

### Pattern 6: Security Model Implementation
**What:** Define model-level access in CSV, row-level access in XML record rules
**When to use:** Every model needs access rights; use record rules for data isolation
**Example:**
```csv
# Source: https://www.odoo.com/documentation/18.0/developer/tutorials/server_framework_101/04_securityintro
# security/ir.model.access.csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_mass_reconcile_batch_user,mass.reconcile.batch.user,model_mass_reconcile_batch,account.group_account_user,1,1,1,0
access_mass_reconcile_batch_manager,mass.reconcile.batch.manager,model_mass_reconcile_batch,account.group_account_manager,1,1,1,1
access_mass_reconcile_match_user,mass.reconcile.match.user,model_mass_reconcile_match,account.group_account_user,1,1,1,0
```

```xml
<!-- Source: https://www.odoo.com/documentation/18.0/developer/tutorials/backend -->
<!-- security/mass_reconcile_security.xml -->
<odoo>
    <record id="mass_reconcile_batch_company_rule" model="ir.rule">
        <field name="name">Mass Reconcile Batch: multi-company</field>
        <field name="model_id" ref="model_mass_reconcile_batch"/>
        <field name="domain_force">[('company_id', 'in', company_ids)]</field>
    </record>
</odoo>
```

### Anti-Patterns to Avoid
- **Looping with individual browse calls:** Always browse the entire recordset first
- **Computing fields without store=True when searchable/groupable needed:** Use store=True but be aware of recomputation cascades
- **Deep computed field dependency chains:** Minimize dependencies between stored computed fields to avoid performance degradation
- **Using _cr.execute without flush/invalidate:** Always flush before raw SQL, invalidate cache after
- **Skipping @api.constrains for business rules:** Server-side validation is essential even with UI readonly attributes

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Audit trail (who changed what when) | Custom logging tables | mail.thread mixin with tracking=True | Integrates with chatter, handles create_uid/write_uid, message formatting, notifications |
| Access control | Custom permission checks | ir.model.access.csv + ir.rule | Odoo's security framework is tested, handles groups, multi-company, and is upgrade-safe |
| State machine workflows | Custom state validation | Selection fields + @api.constrains + button methods | Leverages Odoo's native field tracking, UI widgets (state_selection, label_selection) |
| Batch query optimization | Manual SQL joins | ORM prefetch + _read_group | ORM handles caching, permissions, field computation automatically |
| Field-level caching | Custom cache dictionaries | ORM's built-in cache with proper @api.depends | Framework manages cache invalidation, multi-record prefetch, and memory |

**Key insight:** Odoo's ORM and framework provide solutions for common ERP patterns that handle edge cases like multi-company isolation, access rights, audit trails, and caching. Custom solutions miss these integrations and create upgrade compatibility issues.

## Common Pitfalls

### Pitfall 1: N+1 Query Performance Degradation
**What goes wrong:** Looping over records and accessing fields/relationships triggers one database query per iteration instead of batching
**Why it happens:** Forgetting to browse entire recordset first, or using search_count/search in loops
**How to avoid:**
- Always `records = model.browse(ids)` before looping
- Use `_read_group` for aggregations instead of looping with search_count
- Check query count in debug mode or logs
**Warning signs:** Slow performance on large datasets, database connection pool exhaustion, many similar queries in logs

### Pitfall 2: Cache Invalidation Issues
**What goes wrong:** Cached field values become stale after raw SQL updates or external changes
**Why it happens:** Using _cr.execute without proper flush/invalidate calls
**How to avoid:**
- Always flush field before raw SQL: `record._flush_recordset(['field_name'])`
- Invalidate cache after SQL: `record.invalidate_recordset(['field_name'])`
- Be specific about which fields to invalidate (performance)
**Warning signs:** Users see outdated data, computed fields don't recalculate, inconsistent values between records

### Pitfall 3: Breaking Accounting Constraints
**What goes wrong:** Reconciliation creates unbalanced journal entries or violates accounting rules
**Why it happens:** Not validating debit/credit balance, missing constraints on account types, skipping period lock checks
**How to avoid:**
- Use @api.constrains to validate accounting rules before writes
- Check account.move._check_balanced() patterns in core accounting
- Validate move_line balancing before reconciliation
- Test with locked periods and fiscal year transitions
**Warning signs:** Unbalanced entries in reports, constraint violations in production, accounting audit failures

### Pitfall 4: Upgrade Compatibility Breaking
**What goes wrong:** Custom module breaks on Odoo version upgrade
**Why it happens:** Using private APIs (underscore-prefixed methods not documented), modifying core models without super(), hardcoding IDs
**How to avoid:**
- Only use documented public APIs from official Odoo documentation
- Always call super() in overridden methods
- Use XML IDs (ref()) instead of hardcoded database IDs
- Avoid monkey-patching; use proper inheritance
**Warning signs:** Module works in 18.0 but fails in upgrade, warnings about deprecated methods, compatibility issues with other modules

### Pitfall 5: Stored Computed Field Recomputation Cascades
**What goes wrong:** Changing one field triggers massive recomputation chains, causing timeouts
**Why it happens:** Multiple stored computed fields depending on each other create cascading updates
**How to avoid:**
- Minimize use of store=True on computed fields
- Keep dependency chains shallow (avoid computed depending on computed)
- Use non-stored computed fields when grouping/searching not required
- Test performance with large datasets
**Warning signs:** Timeouts on record saves, high CPU during form edits, database locks during batch operations

## Code Examples

Verified patterns from official sources:

### Complete Model Definition with Security and Validation
```python
# Source: Combination of Odoo 18.0 official documentation patterns
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MassReconcileBatch(models.Model):
    _name = 'mass.reconcile.batch'
    _description = 'Mass Reconciliation Batch'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Basic fields
    name = fields.Char(string='Batch Name', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('matching', 'Matching'),
        ('review', 'Review'),
        ('reconciled', 'Reconciled')
    ], default='draft', required=True, string='Status', tracking=True)

    # Relational fields
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        'res.users',
        string='Responsible',
        default=lambda self: self.env.user,
        tracking=True
    )
    statement_line_ids = fields.One2many(
        'account.bank.statement.line',
        'batch_id',
        string='Bank Statement Lines'
    )

    # Computed fields
    line_count = fields.Integer(
        string='Line Count',
        compute='_compute_line_count',
        store=True
    )

    # SQL constraints
    _sql_constraints = [
        ('name_company_unique',
         'UNIQUE(name, company_id)',
         'Batch name must be unique per company')
    ]

    # Computed field with proper dependencies
    @api.depends('statement_line_ids')
    def _compute_line_count(self):
        # Use _read_group for batch performance
        domain = [('batch_id', 'in', self.ids)]
        counts_data = self.env['account.bank.statement.line']._read_group(
            domain, ['batch_id'], ['__count']
        )
        mapped_data = dict(counts_data)
        for batch in self:
            batch.line_count = mapped_data.get(batch, 0)

    # Python constraints
    @api.constrains('state', 'line_count')
    def _check_reconcile_requirements(self):
        for batch in self:
            if batch.state == 'reconciled' and batch.line_count == 0:
                raise ValidationError(
                    "Cannot reconcile a batch with no statement lines"
                )

    # State transition methods
    def action_start_matching(self):
        self.ensure_one()
        if self.line_count == 0:
            raise ValidationError("Cannot start matching without statement lines")
        self.write({'state': 'matching'})

    def action_move_to_review(self):
        self.write({'state': 'review'})

    def action_reconcile(self):
        self.ensure_one()
        # Reconciliation logic here
        self.write({'state': 'reconciled'})
```

### Extending account.bank.statement.line
```python
# Source: https://www.odoo.com/documentation/18.0/developer/tutorials/server_framework_101/12_inheritance
from odoo import models, fields

class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    batch_id = fields.Many2one(
        'mass.reconcile.batch',
        string='Reconciliation Batch',
        index=True,
        ondelete='set null',
        help='Mass reconciliation batch this line belongs to'
    )
    match_score = fields.Float(
        string='Match Score',
        help='AI/rule-based confidence score for suggested match (0-100)'
    )
    suggested_move_id = fields.Many2one(
        'account.move',
        string='Suggested Move',
        help='Suggested accounting move for reconciliation'
    )
```

### Match Proposal Model with Audit Trail
```python
from odoo import models, fields, api

class MassReconcileMatch(models.Model):
    _name = 'mass.reconcile.match'
    _description = 'Mass Reconciliation Match Proposal'
    _order = 'match_score desc, create_date desc'

    batch_id = fields.Many2one(
        'mass.reconcile.batch',
        string='Batch',
        required=True,
        ondelete='cascade',
        index=True
    )
    statement_line_id = fields.Many2one(
        'account.bank.statement.line',
        string='Statement Line',
        required=True,
        ondelete='cascade'
    )
    suggested_move_id = fields.Many2one(
        'account.move',
        string='Suggested Move',
        required=True
    )
    match_score = fields.Float(
        string='Match Score',
        required=True,
        help='Confidence score (0-100)'
    )
    match_reason = fields.Text(
        string='Match Reason',
        help='Explanation of why this match was suggested'
    )

    # Audit fields (automatic via _log_access=True, which is default)
    create_uid = fields.Many2one('res.users', string='Suggested By', readonly=True)
    create_date = fields.Datetime(string='Suggested On', readonly=True)

    _sql_constraints = [
        ('check_score_range',
         'CHECK(match_score >= 0 AND match_score <= 100)',
         'Match score must be between 0 and 100'),
        ('unique_match',
         'UNIQUE(statement_line_id, suggested_move_id)',
         'Cannot suggest the same move multiple times for one statement line')
    ]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Reconciliation models in community | Enterprise-only in v17 | Odoo 17.0 | OCA account_reconcile_model_oca restores functionality |
| Manual cache management | ORM automatic prefetching | Odoo 8.0+ | Developers should rely on ORM batch patterns, not manual caching |
| _columns dictionary | fields.* API | Odoo 8.0 (new API) | All new code uses fields API; _columns deprecated |
| XML <field ref=""> | XML <field ref="" /> or eval | Ongoing | Self-closing tags preferred for consistency |

**Deprecated/outdated:**
- **_columns dictionary**: Use `fields.*` API for all field definitions
- **browse(ids) returning mixed types**: Modern browse always returns recordsets
- **Manual SQL for CRUD**: Use ORM methods (create, write, unlink) unless performance-critical bulk operations

## Open Questions

1. **What specific accounting constraints exist in account.move for reconciliation?**
   - What we know: account.move has _check_balanced() and fiscal period locks
   - What's unclear: Exact validation sequence for mass reconciliation, whether partial reconciliation allowed
   - Recommendation: Inspect account.move and account.move.line source code in Phase 1 implementation; follow patterns from account_reconcile_model_oca

2. **How does OCA account_reconcile_model_oca handle multi-company scenarios?**
   - What we know: Module exists and provides reconciliation patterns
   - What's unclear: Specific record rule implementation for company isolation
   - Recommendation: Install module in dev environment and inspect security/ir.rule definitions before implementing custom rules

3. **What is the performance impact of mail.thread on batch operations with thousands of statement lines?**
   - What we know: mail.thread adds create/write overhead for tracking
   - What's unclear: Whether tracking should be disabled during bulk imports
   - Recommendation: Benchmark with/without tracking on batch model; consider tracking=False on high-volume child models (statement_line_ids extensions)

## Sources

### Primary (HIGH confidence)
- [Odoo 18.0 Developer Documentation](https://www.odoo.com/documentation/18.0/developer/) - ORM API, model patterns, security
- [Context7: /websites/odoo_18_0_developer](https://www.odoo.com/documentation/18.0/developer/tutorials/server_framework_101/) - Server framework tutorials, compute fields, constraints, inheritance
- [Odoo 18.0 ORM API Reference](https://www.odoo.com/documentation/18.0/developer/reference/backend/orm.html) - Recordsets, caching, prefetching
- [Odoo 18.0 Performance Documentation](https://www.odoo.com/documentation/18.0/developer/reference/backend/performance.html) - N+1 query prevention, batch operations
- [Odoo 18.0 Security Reference](https://www.odoo.com/documentation/18.0/developer/reference/backend/security.html) - Access rights, record rules

### Secondary (MEDIUM confidence)
- [OCA account-reconcile GitHub](https://github.com/OCA/account-reconcile) - Module architecture, 18.0 branch patterns
- [account_reconcile_model_oca Odoo Apps](https://apps.odoo.com/apps/modules/18.0/account_reconcile_model_oca) - Module purpose, version 18.0.1.1.1
- [Odoo 18.0 Reconciliation Models Documentation](https://www.odoo.com/documentation/18.0/applications/finance/accounting/bank/reconciliation_models.html) - User perspective on reconciliation patterns
- [Common Odoo Development Mistakes](https://www.expertia.ai/career-tips/common-mistakes-odoo-developers-should-avoid-to-enhance-performance-87301p) - N+1 queries, caching pitfalls
- [Common Performance Pitfalls in Odoo apps](https://www.slideshare.net/slideshow/common-performance-pitfalls-in-odoo-apps/239050234) - Performance anti-patterns

### Tertiary (LOW confidence)
- Community forum discussions about model extension - Useful for edge cases but need verification against official docs
- Third-party blog posts about Odoo security - Cross-verify with official security documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official Odoo 18.0 documentation, OCA maintained modules verified
- Architecture: HIGH - All patterns from official Context7 documentation with code examples
- Pitfalls: HIGH - Performance documentation official, development mistakes verified across multiple sources

**Research date:** 2026-02-12
**Valid until:** 2026-04-12 (60 days - Odoo 18.0 is stable, patterns unlikely to change)

**Sources requiring verification:**
None - all critical patterns verified through official Odoo 18.0 documentation or Context7
