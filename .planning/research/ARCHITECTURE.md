# Architecture Research

**Domain:** Odoo Bank Reconciliation Module
**Researched:** 2026-02-12
**Confidence:** MEDIUM

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                           │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ OWL Widget   │  │ Wizard Views │  │ List/Form    │               │
│  │ (Batch UI)   │  │ (Manual Mode)│  │ Views        │               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
│         │                 │                 │                        │
├─────────┴─────────────────┴─────────────────┴────────────────────────┤
│                         BUSINESS LOGIC LAYER                         │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────┐      │
│  │              Reconciliation Engine/Service                 │      │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │      │
│  │  │ Matching     │  │ Rule Engine  │  │ Batch        │    │      │
│  │  │ Algorithm    │  │ (Models)     │  │ Processor    │    │      │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │      │
│  └───────────────────────────────────────────────────────────┘      │
├─────────────────────────────────────────────────────────────────────┤
│                            MODEL LAYER                               │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ Statement    │  │ Reconcile    │  │ Account      │               │
│  │ Line Model   │  │ Model        │  │ Move         │               │
│  │ (Extended)   │  │              │  │              │               │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │
│         │                 │                 │                        │
├─────────┴─────────────────┴─────────────────┴────────────────────────┤
│                       DATA/INTEGRATION LAYER                         │
│  ┌─────────────────────────────────────────────────────────┐         │
│  │                  account Module Integration              │         │
│  │  (account.move, account.journal, account.payment)       │         │
│  └─────────────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **OWL Widget** | Batch UI for 80-line approval interface | JavaScript component extending Component class, communicates via RPC to backend |
| **Wizard (Transient Model)** | Manual reconciliation flow, temporary session data | models.TransientModel with form view, executes reconciliation actions |
| **Statement Line Extension** | Enhanced account.bank.statement.line with batch metadata | _inherit on account.bank.statement.line, adds batch_id, match_score fields |
| **Reconciliation Model** | Rule-based matching logic and counterpart generation | account.reconcile.model (standard) or custom matching service |
| **Matching Engine** | Core algorithm to match statement lines with moves | Python class/service with _match_lines(), _score_candidates() methods |
| **Batch Processor** | Orchestrates 80-line batches, manages queue | Regular model or service class, handles batch state machine |
| **Account Move Integration** | Links to existing journal entries and payments | Direct relationship via foreign keys, reconcile() method calls |

## Recommended Project Structure

```
addons/mass_bank_reconcile/
├── models/
│   ├── __init__.py
│   ├── account_bank_statement_line.py      # Extends core statement line model
│   ├── mass_reconcile_batch.py             # Batch management model
│   ├── mass_reconcile_rule.py              # Matching rules (optional, or use account.reconcile.model)
│   └── account_move.py                     # Extension if needed for batch reconciliation
├── wizards/
│   ├── __init__.py
│   └── mass_reconcile_wizard.py            # Manual mode wizard (TransientModel)
├── services/
│   ├── __init__.py
│   └── matching_engine.py                  # Core matching algorithm service
├── views/
│   ├── account_bank_statement_line_views.xml
│   ├── mass_reconcile_batch_views.xml
│   ├── mass_reconcile_wizard_views.xml
│   └── templates.xml                       # QWeb templates for OWL widget
├── static/
│   └── src/
│       ├── components/
│       │   └── batch_reconcile_widget/
│       │       ├── batch_reconcile_widget.js    # OWL component
│       │       ├── batch_reconcile_widget.xml   # OWL template
│       │       └── batch_reconcile_widget.scss
│       └── js/
│           └── field_registry.js           # Widget registration
├── security/
│   ├── ir.model.access.csv
│   └── security.xml
├── data/
│   └── default_reconcile_rules.xml         # Default matching rules
├── __manifest__.py
└── __init__.py
```

### Structure Rationale

- **models/**: Persistent business data - batch records, extended statement lines, rules. These are regular models (models.Model) stored in PostgreSQL.
- **wizards/**: Transient models for manual intervention UI. Use models.TransientModel - data auto-deleted after session.
- **services/**: Separation of complex matching logic from models following SRP. Not Odoo models, just Python classes/utilities.
- **static/src/components/**: OWL framework widgets for modern, reactive batch UI. Organized by component with JS/XML/SCSS co-located.
- **views/**: XML view definitions for forms, lists, wizards, and QWeb templates.

## Architectural Patterns

### Pattern 1: Model Inheritance for Extension

**What:** Extend account.bank.statement.line using _inherit to add batch reconciliation capabilities without modifying core Odoo.

**When to use:** When you need to add fields/methods to existing Odoo models while maintaining upgrade compatibility.

**Trade-offs:**
- PRO: Clean separation, no core modifications, survives upgrades
- CON: Cannot remove/significantly alter base model behavior

**Example:**
```python
# models/account_bank_statement_line.py
from odoo import models, fields, api

class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    # Add batch tracking
    batch_id = fields.Many2one('mass.reconcile.batch', string='Reconcile Batch')
    match_score = fields.Float(string='Match Confidence', compute='_compute_match_score')
    suggested_move_id = fields.Many2one('account.move', string='Suggested Match')

    @api.depends('amount', 'partner_id', 'payment_ref')
    def _compute_match_score(self):
        matching_service = self.env['mass.reconcile.matching']
        for line in self:
            line.match_score = matching_service.calculate_score(line)

    def action_mass_reconcile(self):
        """Batch reconciliation action"""
        return self.env['mass.reconcile.wizard'].create({
            'line_ids': [(6, 0, self.ids)]
        }).action_open_wizard()
```

### Pattern 2: Service Class for Complex Business Logic

**What:** Separate matching algorithm into a service class (not a model) to keep models focused on data and service focused on behavior.

**When to use:** When logic is complex, needs testing in isolation, or might be reused across multiple models.

**Trade-offs:**
- PRO: Testable, follows SRP, easier to understand
- CON: Adds indirection, requires understanding of when to use models vs services

**Example:**
```python
# services/matching_engine.py
from odoo import api, SUPERUSER_ID

class MatchingEngine:
    """Service for matching statement lines with account moves"""

    def __init__(self, env):
        self.env = env

    def find_matches(self, statement_lines, limit=80):
        """Find best matches for statement lines

        Args:
            statement_lines: recordset of account.bank.statement.line
            limit: maximum lines to process in batch

        Returns:
            dict mapping line_id -> [(move_id, score), ...]
        """
        matches = {}
        for line in statement_lines[:limit]:
            candidates = self._get_candidates(line)
            scored = [(c, self._score_match(line, c)) for c in candidates]
            matches[line.id] = sorted(scored, key=lambda x: x[1], reverse=True)
        return matches

    def _get_candidates(self, line):
        """Find potential matching moves"""
        domain = [
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
            '|', ('partner_id', '=', line.partner_id.id),
                 ('amount_total', '=', abs(line.amount))
        ]
        return self.env['account.move'].search(domain, limit=50)

    def _score_match(self, line, move):
        """Calculate match confidence score (0-100)"""
        score = 0
        # Amount exact match
        if abs(move.amount_total - abs(line.amount)) < 0.01:
            score += 40
        # Partner match
        if move.partner_id == line.partner_id:
            score += 30
        # Reference similarity
        if line.payment_ref and move.payment_reference:
            if line.payment_ref.lower() in move.payment_reference.lower():
                score += 30
        return score

# Usage in model
class MassReconcileBatch(models.Model):
    _name = 'mass.reconcile.batch'

    def action_find_matches(self):
        engine = MatchingEngine(self.env)
        matches = engine.find_matches(self.line_ids)
        # Process matches...
```

### Pattern 3: Wizard vs Widget Decision

**What:** Use TransientModel wizard for sequential, server-side flows; use OWL widget for interactive, client-side batch operations.

**When to use:**
- **Wizard**: User needs guided steps, server validation on each step, simple forms
- **Widget**: Real-time interaction, bulk operations, complex UI state management

**Trade-offs:**
- **Wizard**: Simpler to build, server-side validation, page refresh on actions, limited interactivity
- **Widget**: Rich UX, no page refresh, complex to build, requires JS knowledge

**Example (Wizard):**
```python
# wizards/mass_reconcile_wizard.py
from odoo import models, fields, api
from odoo.exceptions import UserError

class MassReconcileWizard(models.TransientModel):
    _name = 'mass.reconcile.wizard'
    _description = 'Mass Bank Reconciliation Wizard'

    # Step 1: Select lines
    line_ids = fields.Many2many('account.bank.statement.line', string='Statement Lines')
    mode = fields.Selection([('auto', 'Automatic'), ('manual', 'Manual')], default='auto')

    # Step 2: Review matches
    match_ids = fields.One2many('mass.reconcile.match.line', 'wizard_id', string='Matches')

    def action_find_matches(self):
        """Step 1 -> Step 2: Find matches"""
        self.ensure_one()
        engine = MatchingEngine(self.env)
        matches = engine.find_matches(self.line_ids)

        match_lines = []
        for line_id, candidates in matches.items():
            if candidates and candidates[0][1] >= 70:  # 70% threshold
                match_lines.append((0, 0, {
                    'statement_line_id': line_id,
                    'move_id': candidates[0][0].id,
                    'score': candidates[0][1]
                }))

        self.match_ids = match_lines
        return self._reopen_wizard()

    def action_reconcile(self):
        """Step 2 -> Complete: Execute reconciliation"""
        self.ensure_one()
        if not self.match_ids:
            raise UserError('No matches to reconcile')

        for match in self.match_ids:
            if match.confirmed:
                match.statement_line_id.reconcile_with_move(match.move_id)

        return {'type': 'ir.actions.act_window_close'}

    def _reopen_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

class MassReconcileMatchLine(models.TransientModel):
    _name = 'mass.reconcile.match.line'

    wizard_id = fields.Many2one('mass.reconcile.wizard', required=True, ondelete='cascade')
    statement_line_id = fields.Many2one('account.bank.statement.line', string='Statement Line')
    move_id = fields.Many2one('account.move', string='Matched Move')
    score = fields.Float(string='Confidence')
    confirmed = fields.Boolean(string='Confirm', default=True)
```

**Example (OWL Widget):**
```javascript
// static/src/components/batch_reconcile_widget/batch_reconcile_widget.js
/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class BatchReconcileWidget extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            lines: [],
            matches: {},
            selected: new Set(),
            loading: false
        });

        this.loadBatch();
    }

    async loadBatch() {
        this.state.loading = true;
        const lines = await this.orm.searchRead(
            "account.bank.statement.line",
            [["is_reconciled", "=", false]],
            ["amount", "partner_id", "payment_ref", "date"],
            { limit: 80 }
        );
        this.state.lines = lines;
        this.state.loading = false;
    }

    async findMatches() {
        this.state.loading = true;
        const result = await this.orm.call(
            "mass.reconcile.batch",
            "find_matches_for_lines",
            [this.state.lines.map(l => l.id)]
        );
        this.state.matches = result;
        this.state.loading = false;
    }

    toggleSelect(lineId) {
        if (this.state.selected.has(lineId)) {
            this.state.selected.delete(lineId);
        } else {
            this.state.selected.add(lineId);
        }
    }

    async reconcileSelected() {
        const selectedIds = Array.from(this.state.selected);
        await this.orm.call(
            "account.bank.statement.line",
            "mass_reconcile",
            [selectedIds]
        );
        await this.loadBatch();
        this.state.selected.clear();
    }
}

BatchReconcileWidget.template = "mass_bank_reconcile.BatchReconcileWidget";
```

### Pattern 4: Batch State Machine

**What:** Manage batch processing through explicit states (draft → matching → review → reconciled) with validation at transitions.

**When to use:** When operations have multiple stages with different rules and rollback requirements.

**Trade-offs:**
- PRO: Clear audit trail, can pause/resume, prevents invalid states
- CON: More complex than single-action, requires state transition logic

**Example:**
```python
# models/mass_reconcile_batch.py
from odoo import models, fields, api
from odoo.exceptions import UserError

class MassReconcileBatch(models.Model):
    _name = 'mass.reconcile.batch'
    _description = 'Mass Reconciliation Batch'

    name = fields.Char(required=True, default=lambda self: self.env['ir.sequence'].next_by_code('mass.reconcile.batch'))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('matching', 'Finding Matches'),
        ('review', 'Ready for Review'),
        ('reconciling', 'Reconciling'),
        ('done', 'Reconciled'),
        ('cancelled', 'Cancelled')
    ], default='draft', required=True)

    line_ids = fields.Many2many('account.bank.statement.line', string='Statement Lines')
    match_ids = fields.One2many('mass.reconcile.match', 'batch_id', string='Matches')

    def action_find_matches(self):
        """Draft -> Matching -> Review"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError('Can only find matches for draft batches')

        self.state = 'matching'
        engine = MatchingEngine(self.env)

        try:
            matches = engine.find_matches(self.line_ids)
            match_records = []
            for line_id, candidates in matches.items():
                for move, score in candidates[:3]:  # Top 3 matches
                    match_records.append((0, 0, {
                        'statement_line_id': line_id,
                        'move_id': move.id,
                        'score': score,
                        'is_best_match': score == candidates[0][1]
                    }))
            self.match_ids = match_records
            self.state = 'review'
        except Exception as e:
            self.state = 'draft'
            raise

    def action_reconcile(self):
        """Review -> Reconciling -> Done"""
        self.ensure_one()
        if self.state != 'review':
            raise UserError('Batch must be in review state')

        self.state = 'reconciling'

        try:
            confirmed_matches = self.match_ids.filtered('confirmed')
            for match in confirmed_matches:
                match.statement_line_id.reconcile_with_move(match.move_id)
            self.state = 'done'
        except Exception as e:
            self.state = 'review'
            raise

class MassReconcileMatch(models.Model):
    _name = 'mass.reconcile.match'
    _description = 'Reconciliation Match Suggestion'

    batch_id = fields.Many2one('mass.reconcile.batch', required=True, ondelete='cascade')
    statement_line_id = fields.Many2one('account.bank.statement.line')
    move_id = fields.Many2one('account.move')
    score = fields.Float()
    is_best_match = fields.Boolean()
    confirmed = fields.Boolean(default=lambda self: self.is_best_match and self.score >= 80)
```

## Data Flow

### Automatic Reconciliation Flow

```
[Import Statement Lines] (account.bank.statement.line)
    ↓
[Trigger Auto-Match] (on_create/cron)
    ↓
[Matching Engine] ← [Reconciliation Rules] (account.reconcile.model)
    ↓ (score candidates)
[Match Results] (confidence scores)
    ↓
[High Confidence?] (score >= threshold)
    ↓ YES                    ↓ NO
[Auto Reconcile]      [Queue for Manual Review]
    ↓                        ↓
[Create Journal Entry] [Batch Model Record]
    ↓                        ↓
[Link to Statement]    [Present in Widget/Wizard]
    ↓
[Reconciled State]
```

### Manual Batch Reconciliation Flow

```
[User Selects Lines] (80 line limit)
    ↓
[Create Batch] (mass.reconcile.batch)
    ↓
[Matching Engine.find_matches()]
    ↓
[Store Suggestions] (mass.reconcile.match)
    ↓
[Present in OWL Widget]
    ↓ (user interaction)
[User Confirms/Modifies Matches]
    ↓
[Batch.action_reconcile()]
    ↓
[For Each Match:]
    ↓
[statement_line.reconcile_with_move(move)]
    ↓
[Creates account.move (journal entry)]
    ↓
[Updates statement_line.is_reconciled = True]
    ↓
[Batch State = Done]
```

### Key Data Flows

1. **Statement Line → Account Move**: When reconciled, creates/updates journal entries linking bank statement to accounting records via account.partial.reconcile
2. **Reconciliation Model → Matching Logic**: Rules define conditions, matching engine executes logic, returns scored candidates
3. **Widget ↔ Backend**: OWL component uses RPC calls (orm.call, orm.searchRead) to fetch data and trigger server-side actions
4. **Batch Processing**: Lines chunked in 80-line batches, processed via state machine, results stored for audit trail

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| < 1,000 lines/day | Simple wizard flow sufficient, synchronous processing, no queue needed |
| 1,000-10,000 lines/day | Implement batch model with state machine, add OWL widget for better UX, consider basic caching of matching candidates |
| 10,000+ lines/day | Add job queue for async processing (account_reconcile_oca_queue pattern), implement matching result cache, consider database indexing on partner_id, amount, payment_ref fields |

### Scaling Priorities

1. **First bottleneck:** Matching algorithm performance with many candidates
   - **Solution:** Add database indexes on commonly searched fields, limit candidate search domain, cache reconciliation model evaluations

2. **Second bottleneck:** UI responsiveness with large batches
   - **Solution:** Implement pagination in OWL widget, use virtual scrolling for line lists, move to async job queue for batch processing

## Anti-Patterns

### Anti-Pattern 1: Storing Business Logic in Widget

**What people do:** Implement matching algorithms and reconciliation logic in JavaScript OWL components

**Why it's wrong:**
- No server-side validation
- Can't be reused by other interfaces (API, cron jobs)
- Testing requires browser automation
- Business rules scattered across Python and JS

**Do this instead:** Keep widget as presentation layer only. All business logic in Python models/services. Widget makes RPC calls to execute actions.

```python
# WRONG: Logic in JS
async reconcileLine(lineId, moveId) {
    // Complex matching logic in JavaScript
    if (this.validateMatch(line, move)) {
        // Direct database writes via ORM
    }
}

# RIGHT: Logic in Python, widget just calls it
class AccountBankStatementLine(models.Model):
    def reconcile_with_move(self, move_id):
        # All logic here, validated server-side
        pass

// Widget just calls Python method
async reconcileLine(lineId, moveId) {
    await this.orm.call("account.bank.statement.line", "reconcile_with_move", [lineId, moveId]);
}
```

### Anti-Pattern 2: Many2one from Regular Model to TransientModel

**What people do:** Try to create Many2one field from account.bank.statement.line to wizard/transient model

**Why it's wrong:**
- Transient records are auto-deleted, creates orphaned foreign keys
- Violates data integrity constraints
- Odoo explicitly forbids this relationship direction

**Do this instead:**
- For temporary associations: Use Many2many from TransientModel to regular model
- For persistent tracking: Create regular model for batches (not transient)

```python
# WRONG
class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'
    wizard_id = fields.Many2one('mass.reconcile.wizard')  # Will fail!

# RIGHT - Transient points to permanent
class MassReconcileWizard(models.TransientModel):
    line_ids = fields.Many2many('account.bank.statement.line')

# OR - Use regular model for tracking
class MassReconcileBatch(models.Model):  # Not TransientModel
    _name = 'mass.reconcile.batch'
    line_ids = fields.Many2many('account.bank.statement.line')
```

### Anti-Pattern 3: Direct SQL for Reconciliation

**What people do:** Use raw SQL to update reconciliation fields and create journal entries, bypassing Odoo ORM

**Why it's wrong:**
- Skips Odoo's reconciliation hooks and validation
- Breaks audit trail and access rights
- Misses computed field updates and triggers
- Can create inconsistent accounting data

**Do this instead:** Use Odoo's reconciliation API methods (reconcile(), auto_reconcile(), etc.)

```python
# WRONG
self.env.cr.execute("""
    UPDATE account_bank_statement_line
    SET is_reconciled = true
    WHERE id = %s
""", (line_id,))

# RIGHT - Use Odoo reconciliation methods
line.reconcile_with_move(move)
# OR
lines._check_reconcile_validity()
lines.reconcile([move], write_off_vals)
```

### Anti-Pattern 4: Monolithic Matching Method

**What people do:** Create single 500-line method that handles all matching logic, scoring, filtering, and reconciliation

**Why it's wrong:**
- Impossible to test individual rules
- Cannot customize/override specific matching behaviors
- Hard to debug when specific rule fails
- Violates Single Responsibility Principle

**Do this instead:** Break into focused methods: _get_candidates(), _score_match(), _filter_by_threshold(), _execute_reconciliation()

```python
# WRONG - Monolithic
def find_and_reconcile(self, lines):
    # 500 lines of mixed concerns
    for line in lines:
        # candidate search
        # scoring logic
        # threshold checks
        # reconciliation execution
        # error handling
        pass

# RIGHT - Separated concerns
class MatchingEngine:
    def find_matches(self, lines):
        candidates = self._get_candidates(lines)
        scored = self._score_candidates(lines, candidates)
        return self._filter_by_threshold(scored)

    def _get_candidates(self, lines):
        # Just candidate retrieval
        pass

    def _score_candidates(self, lines, candidates):
        # Just scoring logic
        return [(c, self._score_single(line, c)) for c in candidates]

    def _score_single(self, line, candidate):
        # Individual scoring components
        score = 0
        score += self._score_amount_match(line, candidate)
        score += self._score_partner_match(line, candidate)
        score += self._score_reference_match(line, candidate)
        return score
```

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **account.reconcile.model** | Call _apply_rules() method or inherit to add custom rule types | Standard Odoo reconciliation models, use for rule-based matching |
| **account.move** | Foreign key relationships + reconcile() method calls | Core accounting module, handles journal entries |
| **account.payment** | Search/match via domain filters, link through account.move | Payment records often the target of reconciliation |
| **account.partial.reconcile** | Created automatically when reconciling, don't manipulate directly | Core Odoo reconciliation linking table |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **Widget ↔ Backend** | RPC calls via orm service (searchRead, call) | Widget requests data, triggers actions; backend validates and executes |
| **Wizard ↔ Models** | Direct ORM method calls, action returns | Wizard orchestrates flow, delegates business logic to models |
| **Matching Engine ↔ Models** | Service instantiated with env, calls search/read/write on models | Service pattern: engine doesn't inherit models.Model |
| **Extended Models ↔ Core** | _inherit pattern, super() calls for base functionality | Maintain compatibility with core account module methods |

## Build Order and Dependencies

### Recommended Build Sequence

**Phase 1: Foundation (Models)**
1. Create `mass.reconcile.batch` model (state machine, basic fields)
2. Extend `account.bank.statement.line` with batch_id, match_score fields
3. Create `mass.reconcile.match` model for storing suggestions
4. Set up security (ir.model.access.csv)

**Rationale:** Data layer must exist before business logic can operate on it

---

**Phase 2: Matching Logic**
5. Implement `MatchingEngine` service class with basic scoring
6. Add candidate retrieval methods (_get_candidates)
7. Implement scoring algorithms (_score_match)
8. Add threshold filtering and ranking

**Rationale:** Core business logic can be tested independently before UI

---

**Phase 3: Manual Flow (Wizard)**
9. Create `mass.reconcile.wizard` (TransientModel)
10. Build wizard views (form with steps)
11. Implement action_find_matches() integration with engine
12. Implement action_reconcile() to execute matches

**Rationale:** Simpler UI pattern to validate full flow works end-to-end

---

**Phase 4: Batch UI (Widget)**
13. Create OWL component structure (JS/XML/SCSS)
14. Implement batch loading and display
15. Add match finding and display
16. Implement selection and approval UI
17. Add reconciliation execution

**Rationale:** Complex UI built last, after validating business logic works

---

**Phase 5: Automation**
18. Add cron job for auto-matching
19. Implement queue integration (if needed for scale)
20. Add notification system for results

**Rationale:** Automation layer sits on top of proven manual flow

### Key Dependencies

- **Matching Engine depends on:** Statement line model extension (needs fields to score)
- **Wizard depends on:** Matching engine, batch model
- **Widget depends on:** All backend components (calls their methods)
- **Queue system depends on:** Full reconciliation flow working synchronously first

## Sources

### Official Odoo Documentation
- [Bank Reconciliation — Odoo 18.0](https://www.odoo.com/documentation/18.0/applications/finance/accounting/bank/reconciliation.html)
- [Reconciliation Models — Odoo 18.0](https://www.odoo.com/documentation/18.0/applications/finance/accounting/bank/reconciliation_models.html)
- [Reconciliation Models — Odoo 19.0](https://www.odoo.com/documentation/19.0/applications/finance/accounting/bank/reconciliation_models.html)

### OCA Community Modules
- [OCA/account-reconcile Repository](https://github.com/OCA/account-reconcile)
- [account_reconcile_oca Module](https://apps.odoo.com/apps/modules/16.0/account_reconcile_oca)
- [account_mass_reconcile Module](https://apps.odoo.com/apps/modules/12.0/account_mass_reconcile)

### Technical Implementation
- [Model Types in Odoo: Model vs. TransientModel vs. AbstractModel](https://medium.com/@ahmedmuhumed/model-types-in-odoo-model-vs-transientmodel-vs-abstractmodel-47526091b386)
- [A Complete Guide to Transient Models (Wizards) in Odoo 19](https://www.zbeanztech.com/blog/general-11/a-complete-guide-to-transient-models-wizards-in-odoo-19-212)
- [Odoo Wizards: The Complete Guide](https://medium.com/@aymenfarhani28/odoo-wizards-the-complete-guide-9e453e8c282a)

### OWL Framework
- [GitHub - OWL Framework](https://github.com/odoo/owl)
- [OWL Framework Official Documentation](https://odoo.github.io/owl/)
- [Introduction to Odoo OWL Framework](https://www.cybrosys.com/blog/introduction-to-odoo-owl-framework)

### Community Resources
- [How to Inherit account.bank.statement.line Model](https://www.odoo.com/forum/help-1/how-can-i-inherit-accountbankstatementline-model-61976)
- [Odoo Bank Reconciliation Made Simple](https://theledgerlabs.com/odoo-bank-reconciliation-guide/)
- [Odoo 18 Accounting Reconciliation Models Overview](https://www.cybrosys.com/blog/overview-of-odoo-18-accounting-reconciliation-models)

---
*Architecture research for: Mass Bank Reconciliation Module (Odoo 18.0)*
*Researched: 2026-02-12*
