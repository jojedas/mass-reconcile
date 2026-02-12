# Phase 2: Matching Engine & Auto-Reconciliation - Research

**Researched:** 2026-02-12
**Domain:** Odoo 18.0 Bank Reconciliation / Matching Algorithms
**Confidence:** MEDIUM-HIGH

## Summary

This phase implements the core matching engine for bank reconciliation in Odoo 18.0 Community. The research reveals that Odoo provides strong foundational patterns for reconciliation matching, including native account.move.line search capabilities, float comparison utilities (float_compare, float_is_zero), and reconciliation state tracking via full_reconcile_id. The OCA (Odoo Community Association) provides account.reconcile.model modules that restore Enterprise reconciliation features to Community edition, enabling rule-based matching for recurring transactions.

The matching algorithm should follow a multi-stage approach: exact amount matching (using float_compare with currency precision), filtered by partner and account type, with reference comparison (payment_ref matching statement line labels), and date range validation. Confidence scoring should be weighted based on multiple factors: amount match (highest weight 50-60%), partner match (20-30%), reference match (15-25%), and date proximity (5-10%). Industry best practices suggest thresholds of 100% for automatic reconciliation, 80-99% for "probable" requiring review, and below 80% for manual intervention.

**Primary recommendation:** Implement a weighted scoring algorithm using Odoo's native ORM patterns, float_compare for monetary precision, and integrate with OCA's account.reconcile.model for recurring expense patterns. Use batch searching with proper prefetching to avoid N+1 queries when scanning account.move.line candidates.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Odoo Community | 18.0 | ERP framework with accounting module | Required base, provides account.move.line, float comparison utilities |
| account.reconcile.model.oca | 18.0.1.1.1 | Reconciliation rules engine (OCA) | Restores Enterprise reconciliation model features to Community |
| account.reconcile.oca | 18.0.1.1.7 | Core reconciliation for Odoo CE | Enhanced reconciliation capabilities for Community edition |
| Python standard library | 3.10+ | Core language features | Odoo 18 runs on Python 3.10+ |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| account.reconcile.oca.queue | 18.0.1.1.0 | Auto-reconcile via queue jobs | For large batch processing (future phases) |
| account_partner_reconcile | 18.0.1.0.0 | Partner-level reconciliation tools | When implementing partner-specific matching rules |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| OCA modules | Native Odoo Enterprise | Enterprise has built-in reconciliation models, but requires license |
| Weighted scoring | Simple rule-based | Rule-based is simpler but less flexible for partial matches |
| Python loops | SQL aggregation | SQL is faster but harder to maintain and test |

**Installation:**
```bash
# OCA modules are installed via Odoo Apps or manual git clone
cd /path/to/odoo/addons
git clone -b 18.0 https://github.com/OCA/account-reconcile.git
# Then install via Odoo Apps menu: account_reconcile_model_oca, account_reconcile_oca
```

## Architecture Patterns

### Recommended Project Structure
```
models/
├── mass_reconcile_batch.py          # Existing: batch orchestration
├── mass_reconcile_match.py          # Existing: match proposals
├── account_bank_statement_line.py   # Existing: statement line extensions
├── mass_reconcile_engine.py         # NEW: matching engine logic
└── mass_reconcile_scorer.py         # NEW: confidence scoring algorithm
```

### Pattern 1: Multi-Stage Matching Pipeline
**What:** Search for candidates in stages, from most specific to least specific, to optimize performance
**When to use:** When matching bank statement lines against large account.move.line datasets
**Example:**
```python
# Source: Industry best practices + Odoo ORM patterns
class MassReconcileEngine(models.Model):
    _name = 'mass.reconcile.engine'

    def find_candidates(self, statement_line):
        """Multi-stage matching pipeline."""
        # Stage 1: Exact amount + partner (highest confidence)
        candidates = self._search_exact_amount_partner(statement_line)
        if candidates:
            return self._score_candidates(statement_line, candidates)

        # Stage 2: Exact amount + reference
        candidates = self._search_exact_amount_reference(statement_line)
        if candidates:
            return self._score_candidates(statement_line, candidates)

        # Stage 3: Exact amount + date range
        candidates = self._search_exact_amount_date(statement_line)
        return self._score_candidates(statement_line, candidates)

    def _search_exact_amount_partner(self, line):
        """Search unreconciled move lines by amount and partner."""
        domain = [
            ('full_reconcile_id', '=', False),  # Not already reconciled
            ('account_id.reconcile', '=', True),  # Account allows reconciliation
            ('partner_id', '=', line.partner_id.id),
            ('parent_state', '=', 'posted'),  # Only posted moves
        ]
        # Amount filtering with precision
        precision = line.currency_id.rounding or 0.01
        candidates = self.env['account.move.line'].search(domain)
        # Filter by amount using float_compare
        return candidates.filtered(
            lambda ml: fields.Float.is_zero(
                abs(ml.balance) - abs(line.amount),
                precision_rounding=precision
            )
        )
```

### Pattern 2: Weighted Confidence Scoring
**What:** Calculate match confidence by combining multiple weighted factors
**When to use:** When evaluating match quality for user review decisions
**Example:**
```python
# Source: Bank reconciliation industry patterns
class MassReconcileScorer(models.Model):
    _name = 'mass.reconcile.scorer'

    WEIGHTS = {
        'amount': 0.50,      # 50% - most critical
        'partner': 0.25,     # 25% - strong indicator
        'reference': 0.20,   # 20% - good confirmation
        'date': 0.05,        # 5% - weak signal
    }

    def calculate_score(self, statement_line, move_line):
        """Calculate weighted confidence score (0-100)."""
        scores = {
            'amount': self._score_amount(statement_line, move_line),
            'partner': self._score_partner(statement_line, move_line),
            'reference': self._score_reference(statement_line, move_line),
            'date': self._score_date(statement_line, move_line),
        }

        total = sum(score * self.WEIGHTS[factor]
                   for factor, score in scores.items())
        return round(total, 2)

    def _score_amount(self, st_line, mv_line):
        """Score amount match (0-100)."""
        precision = st_line.currency_id.rounding or 0.01
        comparison = fields.Float.compare(
            abs(st_line.amount),
            abs(mv_line.balance),
            precision_rounding=precision
        )
        return 100.0 if comparison == 0 else 0.0
```

### Pattern 3: Batch Search with Prefetching
**What:** Search move lines in batch to avoid N+1 queries, using Odoo's prefetch mechanism
**When to use:** When processing multiple statement lines (always in mass reconciliation)
**Example:**
```python
# Source: Odoo 18.0 Performance Documentation
def process_batch(self, statement_line_ids):
    """Process multiple statement lines efficiently."""
    lines = self.env['account.bank.statement.line'].browse(statement_line_ids)

    # Prefetch related fields in one query
    lines._read(['amount', 'partner_id', 'payment_ref', 'date'])
    lines.mapped('partner_id.name')  # Prefetch partner names
    lines.mapped('currency_id.rounding')  # Prefetch currency precision

    # Build domain for all amounts at once
    amounts = lines.mapped('amount')
    precision = lines[0].currency_id.rounding or 0.01

    # Single search for all candidates
    all_candidates = self.env['account.move.line'].search([
        ('full_reconcile_id', '=', False),
        ('account_id.reconcile', '=', True),
        ('parent_state', '=', 'posted'),
        # Use SQL-level filtering where possible
    ])

    # Match in memory with prefetched data
    for line in lines:
        candidates = all_candidates.filtered(
            lambda ml: self._matches_line(ml, line, precision)
        )
        self._create_match_proposals(line, candidates)
```

### Pattern 4: Internal Transfer Detection
**What:** Identify transfers between bank accounts of same company
**When to use:** When matching statement lines that might be internal transfers
**Example:**
```python
# Source: Odoo bank reconciliation patterns
def _detect_internal_transfer(self, statement_line):
    """Detect if line is an internal transfer."""
    # Search for opposite amount in other bank journals same company
    opposite_amount = -statement_line.amount
    date_range_days = 7  # Configurable
    date_from = statement_line.date - timedelta(days=date_range_days)
    date_to = statement_line.date + timedelta(days=date_range_days)

    domain = [
        ('journal_id.type', '=', 'bank'),
        ('journal_id', '!=', statement_line.journal_id.id),
        ('company_id', '=', statement_line.company_id.id),
        ('date', '>=', date_from),
        ('date', '<=', date_to),
        ('is_reconciled', '=', False),
    ]

    precision = statement_line.currency_id.rounding or 0.01
    candidates = self.env['account.bank.statement.line'].search(domain)

    return candidates.filtered(
        lambda line: fields.Float.is_zero(
            line.amount - opposite_amount,
            precision_rounding=precision
        )
    )
```

### Anti-Patterns to Avoid
- **Don't use Python `==` for float comparison:** Always use `float_compare()` or `float_is_zero()` with precision_rounding to avoid floating-point precision errors
- **Don't search move lines in loops:** Use batch search with prefetching, or build comprehensive domain filters upfront
- **Don't ignore reconciliation state:** Always filter by `full_reconcile_id = False` to exclude already reconciled items
- **Don't hardcode precision:** Always use `currency_id.rounding` for monetary comparisons
- **Don't score without normalization:** Always normalize confidence scores to 0-100 range for consistent UI presentation

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Reconciliation rules for recurring expenses | Custom pattern matcher | account.reconcile.model (OCA) | Handles complex matching conditions, configurable per expense type, tested by community |
| Float comparison with precision | Custom rounding logic | `fields.Float.compare()` and `fields.Float.is_zero()` | Handles edge cases, currency-aware, consistent with Odoo conventions |
| Batch ORM queries | Manual SQL queries | Odoo ORM with `search()`, `_read_group()`, prefetch | Maintains security rules, handles access rights, automatic SQL injection protection |
| Date range queries | Python date filtering | Domain filters with `>=` and `<=` | Executes in database, much faster for large datasets |
| Currency precision lookup | Hardcoded decimals | `res.currency.rounding` field | Respects currency-specific precision (JPY has 0 decimals, most have 2) |

**Key insight:** Odoo's ORM and float utilities handle edge cases that are easy to miss in custom implementations (security, performance, precision, currency-specific rules). Reconciliation models from OCA provide proven patterns for common scenarios (rent, utilities, salaries) that would take weeks to develop and debug from scratch.

## Common Pitfalls

### Pitfall 1: Float Precision Errors
**What goes wrong:** Using Python's native `==` or direct subtraction for monetary comparisons results in false negatives due to floating-point representation errors (0.1 + 0.2 != 0.3)
**Why it happens:** Binary floating-point cannot exactly represent many decimal values
**How to avoid:** Always use `fields.Float.compare()` with `precision_rounding=currency.rounding`
**Warning signs:**
- Exact amount matches being missed
- Test failures on monetary comparisons
- Different results between test and production environments

### Pitfall 2: N+1 Query Performance Degradation
**What goes wrong:** Searching for candidates inside a loop over statement lines causes one SQL query per line (81 queries for 80 lines + 1 batch query)
**Why it happens:** Each `search()` call executes immediately without batching
**How to avoid:** Build domain filters that capture all statement line amounts, or use `_read_group()` for aggregations. Always prefetch related fields before loops.
**Warning signs:**
- SQL query count proportional to record count
- Performance degrades with batch size
- Database CPU spikes during matching

### Pitfall 3: Matching Already Reconciled Lines
**What goes wrong:** Proposing move lines that are already reconciled, causing constraint violations or duplicate reconciliation attempts
**Why it happens:** Forgetting to filter by `full_reconcile_id = False` in search domains
**How to avoid:** Always include `('full_reconcile_id', '=', False)` in all move line searches
**Warning signs:**
- Errors during reconciliation: "Line already reconciled"
- Match proposals that cannot be applied
- Constraint violations on full_reconcile_id

### Pitfall 4: Ignoring Posted State
**What goes wrong:** Matching against draft or cancelled move lines that should not be reconciled
**Why it happens:** Not filtering by `parent_state = 'posted'` (the state of the parent account.move)
**How to avoid:** Include `('parent_state', '=', 'posted')` in all move line searches
**Warning signs:**
- Matches against draft invoices
- Reconciliation of cancelled entries
- Accounting inconsistencies

### Pitfall 5: Incorrect Confidence Score Thresholds
**What goes wrong:** Setting threshold too low (auto-reconcile risky matches) or too high (everything requires manual review)
**Why it happens:** Not calibrating thresholds against real transaction data
**How to avoid:** Use industry-standard thresholds: 100% = exact match (auto), 80-99% = probable (review), <80% = doubtful (manual). Make thresholds configurable.
**Warning signs:**
- High error rate in automatic reconciliations
- Users complaining about too many manual reviews
- Reconciliation errors discovered during month-end close

### Pitfall 6: Not Handling Multi-Currency Scenarios
**What goes wrong:** Comparing amounts in different currencies without conversion
**Why it happens:** Assuming all transactions are in company currency
**How to avoid:** Always use currency-aware comparisons, respect `currency_id` on both statement lines and move lines
**Warning signs:**
- Foreign currency transactions never match
- Incorrect matches when amounts numerically equal but currencies differ
- Exchange rate differences causing false positives

## Code Examples

Verified patterns from official sources:

### Float Comparison with Currency Precision
```python
# Source: Odoo 18.0 ORM Documentation
# https://www.odoo.com/documentation/18.0/developer/reference/backend/orm
from odoo import fields

# Compare two amounts with currency precision
precision = statement_line.currency_id.rounding or 0.01
comparison = fields.Float.compare(
    statement_line.amount,
    move_line.balance,
    precision_rounding=precision
)
# Returns: -1 (less), 0 (equal), 1 (greater)

# Check if difference is effectively zero
difference = abs(statement_line.amount) - abs(move_line.balance)
is_match = fields.Float.is_zero(
    difference,
    precision_rounding=precision
)
```

### Searching Unreconciled Move Lines
```python
# Source: Odoo GitHub - account.move.line patterns
# Based on: https://github.com/odoo/odoo (multiple versions)
domain = [
    # Core reconciliation filters
    ('full_reconcile_id', '=', False),      # Not already reconciled
    ('account_id.reconcile', '=', True),    # Account allows reconciliation
    ('parent_state', '=', 'posted'),        # Only posted moves
    ('company_id', '=', statement_line.company_id.id),

    # Optional: filter by amount residual (for partial payments)
    ('amount_residual', '!=', 0),
]

# Add partner filter if known
if statement_line.partner_id:
    domain.append(('partner_id', '=', statement_line.partner_id.id))

# Add date range filter (configurable days)
date_range_days = 30
date_from = statement_line.date - timedelta(days=date_range_days)
date_to = statement_line.date + timedelta(days=date_range_days)
domain.extend([
    ('date', '>=', date_from),
    ('date', '<=', date_to),
])

candidates = self.env['account.move.line'].search(domain)
```

### Reference Matching Pattern
```python
# Source: Odoo reconciliation models documentation + OCA patterns
# https://www.odoo.com/documentation/18.0/applications/finance/accounting/bank/reconciliation_models.html
def _score_reference(self, statement_line, move_line):
    """
    Compare payment references between statement and move.
    Odoo matches: statement line 'payment_ref' vs move 'payment_ref' or 'ref'
    """
    st_ref = (statement_line.payment_ref or '').strip().upper()
    mv_ref = (move_line.payment_ref or move_line.ref or '').strip().upper()

    if not st_ref or not mv_ref:
        return 0.0  # No reference to compare

    # Exact match
    if st_ref == mv_ref:
        return 100.0

    # Substring match (one contains the other)
    if st_ref in mv_ref or mv_ref in st_ref:
        return 75.0

    # Could add fuzzy matching here (Levenshtein distance, etc.)
    return 0.0
```

### Batch Processing with Prefetch
```python
# Source: Odoo 18.0 Performance Documentation
# https://www.odoo.com/documentation/18.0/developer/reference/backend/performance.html
def process_batch_efficient(self, batch_id):
    """Process batch with proper prefetching to avoid N+1 queries."""
    batch = self.env['mass.reconcile.batch'].browse(batch_id)

    # Prefetch all statement lines and related data
    lines = batch.statement_line_ids
    lines._read(['amount', 'payment_ref', 'date', 'partner_id', 'currency_id'])

    # Prefetch relational fields
    lines.mapped('partner_id.name')
    lines.mapped('currency_id.rounding')

    # Build aggregated search criteria
    partner_ids = lines.mapped('partner_id.id')
    min_date = min(lines.mapped('date'))
    max_date = max(lines.mapped('date'))

    # Single query for all potential candidates
    candidates = self.env['account.move.line'].search([
        ('full_reconcile_id', '=', False),
        ('account_id.reconcile', '=', True),
        ('parent_state', '=', 'posted'),
        ('company_id', '=', batch.company_id.id),
        ('date', '>=', min_date - timedelta(days=30)),
        ('date', '<=', max_date + timedelta(days=30)),
        ('partner_id', 'in', partner_ids),
    ])

    # Prefetch candidate fields
    candidates._read(['balance', 'payment_ref', 'date', 'partner_id'])

    # Now match in memory with all data cached
    matches = []
    for line in lines:
        line_candidates = self._filter_candidates(line, candidates)
        scored = self._score_candidates(line, line_candidates)
        matches.extend(scored)

    # Batch create all matches
    self.env['mass.reconcile.match'].create(matches)
```

### Using account.reconcile.model (OCA)
```python
# Source: OCA account-reconcile repository patterns
# https://github.com/OCA/account-reconcile
def apply_reconcile_models(self, statement_line):
    """
    Apply reconciliation models (rules) to find matches.
    This integrates with account.reconcile.model from OCA.
    """
    # Get applicable reconciliation models
    models = self.env['account.reconcile.model'].search([
        ('rule_type', '=', 'invoice_matching'),
        ('company_id', '=', statement_line.company_id.id),
    ])

    for model in models:
        # Each model has match_type, match_amount, match_label, etc.
        if model.match_partner and statement_line.partner_id:
            # Model requires partner match
            if model.match_partner == 'exact':
                # Continue with this model's other criteria
                pass

        if model.match_amount:
            # Model checks amount within tolerance
            tolerance = model.amount_tolerance or 0.0
            # Apply amount matching logic
            pass

        if model.match_label:
            # Model uses regex or substring matching on label/reference
            # Apply reference matching logic
            pass

    # Models can also generate automatic journal items (write-offs, fees)
    # That's for later phases (manual review interface)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual reconciliation | Auto-matching with confidence scoring | ~2015-2018 | Reduces hours to minutes for routine reconciliation |
| Simple rule-based (exact match only) | Weighted multi-factor scoring | ~2020 | Better handling of partial matches, references |
| Reconciliation models in Community | Moved to Enterprise (v17+) | Odoo 17.0 (2023) | OCA restored via account.reconcile.model.oca |
| 3-pane reconciliation widget | Kanban-based widget | Odoo 18.0 (2024) | Simplified UI, but less customizable |
| Python string comparison | Fuzzy matching algorithms | 2023-2025 | Better handling of vendor name variations |

**Deprecated/outdated:**
- **account.bank.statement.import**: Replaced by direct API integrations and account.online.link
- **Simple reconciliation button**: Replaced by reconciliation models and automatic matching
- **Manual journal entry creation for fees**: Now handled by reconciliation models with automatic counterpart entries

## Open Questions

1. **Should we use fuzzy string matching for reference comparison?**
   - What we know: Exact and substring matching covers most cases
   - What's unclear: Whether Levenshtein distance or other fuzzy algorithms add value vs complexity
   - Recommendation: Start with exact/substring, add fuzzy matching in Phase 4 if users request it

2. **What date range tolerance should be default?**
   - What we know: Industry uses 7-30 days typically
   - What's unclear: What range suits our specific user base
   - Recommendation: Make configurable (default 30 days), users can adjust per batch

3. **Should internal transfer detection be automatic or user-triggered?**
   - What we know: Internal transfers are common and high-confidence when amounts + dates match
   - What's unclear: Whether to show as separate match type or include in regular proposals
   - Recommendation: Include in regular matching with specific match_type='internal_transfer' and high confidence score

4. **How to handle partial payments and multi-invoice reconciliation?**
   - What we know: One statement line can match multiple invoices (partial payments)
   - What's unclear: Should Phase 2 support this or defer to Phase 4?
   - Recommendation: Phase 2 focuses on 1:1 matching, Phase 4 adds 1:many and many:1 scenarios

5. **Should we integrate with AI/ML for pattern learning?**
   - What we know: Some modern tools use ML to learn from user corrections
   - What's unclear: Complexity vs benefit for Community edition users
   - Recommendation: Not for initial release; consider for future enhancement if user feedback indicates value

## Sources

### Primary (HIGH confidence)
- [Odoo 18.0 Developer Documentation - ORM API](https://www.odoo.com/documentation/18.0/developer/reference/backend/orm) - Float comparison methods, search domains
- [Odoo 18.0 Developer Documentation - Performance](https://www.odoo.com/documentation/18.0/developer/reference/backend/performance.html) - Batch operations, prefetching patterns
- [Odoo 18.0 Documentation - Bank Reconciliation](https://www.odoo.com/documentation/18.0/applications/finance/accounting/bank/reconciliation.html) - Reconciliation process
- [Odoo 18.0 Documentation - Reconciliation Models](https://www.odoo.com/documentation/18.0/applications/finance/accounting/bank/reconciliation_models.html) - Model configuration
- [OCA account-reconcile GitHub Repository](https://github.com/OCA/account-reconcile) - Module versions and features for Odoo 18.0
- [Context7: Odoo 18.0 Developer](https://www.odoo.com/documentation/18.0/developer/reference/backend/orm) - Float operations, ORM patterns

### Secondary (MEDIUM confidence)
- [Odoo Apps Store - account_reconcile_model_oca](https://apps.odoo.com/apps/modules/17.0/account_reconcile_model_oca) - Module description (v17, extrapolated to v18)
- [Cybrosys - Float Operations in Odoo](https://www.cybrosys.com/blog/float-operations-in-odoo) - Tutorial on float_compare, float_is_zero
- [HSX Tech - Best Practices For Reconciliation in Odoo](https://hsxtech.net/best-practices-for-reconciliation-in-odoo-accounting/) - Best practices guide
- [Odoo GitHub Issues](https://github.com/odoo/odoo/issues/12095) - account.move.line field discussions
- [Vraja Technologies - float_is_zero and float_compare Implementation](https://www.vrajatechnologies.com/how-to-implement-float-is-zero-and-float-compare-in-odoo) - Implementation examples

### Tertiary (LOW confidence - industry patterns, not Odoo-specific)
- [Midday.ai - Automatic Reconciliation Engine](https://midday.ai/updates/automatic-reconciliation-engine/) - Weighted scoring example (50% embedding, 35% amount, 10% currency, 5% date)
- [Cashbook - Auto-Matching Algorithms](https://www.cashbook.com/auto-matching-algorithms-in-accounts-reconciliation/) - General reconciliation challenges
- [SolvexIA - Transaction Matching Using AI](https://www.solvexia.com/blog/transaction-matching-using-ai) - ML approaches to matching
- [Docyt - AI Bank Reconciliation](https://docyt.com/article/how-to-fully-automate-bank-reconciliations-with-machine-learning/) - Machine learning patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - OCA modules verified for Odoo 18.0, float utilities documented in official docs
- Architecture patterns: MEDIUM-HIGH - Patterns based on Odoo conventions + industry best practices, not all verified in Odoo 18 source
- Pitfalls: HIGH - Common issues documented in Odoo GitHub issues and community forums
- Code examples: MEDIUM-HIGH - Float comparison and search patterns from official docs, batch patterns from performance guide, scoring algorithm from industry sources

**Research date:** 2026-02-12
**Valid until:** ~60 days (2026-04-12) - Stable domain, Odoo 18.0 is mature, patterns unlikely to change rapidly
