# Phase 3: Batch Processing & State Management - Research

**Researched:** 2026-02-12
**Domain:** Odoo ORM batch processing, state machine workflows, PostgreSQL row locking, progress tracking
**Confidence:** HIGH

## Summary

Phase 3 implements batch processing for bank statement reconciliation with chunking (80 lines max), state transitions (draft → matching → review → reconciled), progress tracking, and concurrency control. The research reveals that Odoo provides robust ORM utilities for batch processing (`util.iter_browse`, `util.chunks`), transaction management with savepoints for error isolation, and raw SQL support for PostgreSQL row locking (`SELECT FOR UPDATE`). The existing code from Phase 2 already implements most core patterns: the batch model exists with state machine, the matching engine is operational, and match proposals are stored. Phase 3 focuses on adding date range selection for line loading, progress indicators during processing, matching statistics display, and SELECT FOR UPDATE locking to prevent concurrent reconciliation conflicts.

**Primary recommendation:** Use Odoo's built-in batch utilities (`util.iter_browse` with chunking) for processing 80-line batches, implement progress tracking via `self.env['ir.cron']._notify_progress()` for scheduled actions (or computed fields for synchronous UI), and add PostgreSQL SELECT FOR UPDATE with savepoint error handling for row locking during reconciliation operations.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Odoo ORM | 18.0 | Batch processing, state management | Native framework with proven patterns for large-scale operations |
| PostgreSQL | 10+ | Row-level locking (SELECT FOR UPDATE) | Default database for Odoo, required for transaction management |
| Python stdlib datetime | 3.x | Date range filtering and calculations | Standard library, zero dependencies |
| odoo.tools.float_utils | 18.0 | Monetary amount comparisons | Essential for avoiding float precision issues (already in use) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| odoo.upgrade.util | 18.0 | Batch iteration (`iter_browse`, `chunks`) | Processing large recordsets with auto-flush/commit |
| odoo.exceptions | 18.0 | ValidationError, UserError | User-facing validation and error messages |
| psycopg2 (via cr) | 2.x | Raw SQL execution for SELECT FOR UPDATE | When ORM locking is insufficient |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| util.iter_browse | Manual chunking with search(limit=N, offset=M) | Loses automatic flushing/committing; more error-prone |
| SELECT FOR UPDATE | Optimistic locking (check write_date) | Higher collision rate in concurrent scenarios |
| State Selection field | Separate status table | Over-engineering for simple linear workflow |
| Computed fields for stats | Stored fields updated on write | N+1 query risk if not using _read_group pattern (already avoided in Phase 1) |

**Installation:**
```bash
# No additional packages needed - all utilities are built into Odoo 18.0
# Odoo dependencies already include psycopg2 for PostgreSQL
```

## Architecture Patterns

### Recommended Project Structure
```
mass_reconcile/
├── models/
│   ├── mass_reconcile_batch.py          # State machine, line loading, locking
│   ├── account_bank_statement_line.py   # Extended with batch_id, match_state
│   ├── mass_reconcile_match.py          # Match proposals with audit trail
│   ├── mass_reconcile_engine.py         # Candidate search (Phase 2 - DONE)
│   └── mass_reconcile_scorer.py         # Confidence scoring (Phase 2 - DONE)
├── wizards/
│   └── mass_reconcile_line_selector.py  # (Future) Date range selection wizard
└── views/
    └── mass_reconcile_batch_views.xml   # Form view with progress indicators
```

### Pattern 1: Batch Date Range Selection
**What:** User selects statement lines by date range for batch processing (up to 80 lines)
**When to use:** Initial batch creation in draft state
**Example:**
```python
# Source: Existing code in mass_reconcile_batch.py + Odoo domain patterns
# Method to add statement lines to batch by date range
def action_load_statement_lines(self):
    """Load statement lines into batch based on date range filters."""
    self.ensure_one()

    if self.state != 'draft':
        raise ValidationError("Can only load lines in draft state")

    # Build domain for line selection
    domain = [
        ('journal_id', '=', self.journal_id.id),
        ('is_reconciled', '=', False),
        ('batch_id', '=', False),  # Not already in a batch
    ]

    if self.date_from:
        domain.append(('date', '>=', self.date_from))
    if self.date_to:
        domain.append(('date', '<=', self.date_to))

    # Search and limit to 80 lines
    lines = self.env['account.bank.statement.line'].search(domain, limit=80, order='date asc')

    if not lines:
        raise UserError("No unreconciled statement lines found in date range")

    # Assign lines to batch
    lines.write({'batch_id': self.id})

    return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
            'message': f'{len(lines)} statement lines loaded into batch',
            'type': 'success',
            'sticky': False,
        }
    }
```

### Pattern 2: Batch Processing with Progress Tracking
**What:** Process 80-line chunks with progress indicators showing completion percentage
**When to use:** During matching state transition (draft → matching → review)
**Example:**
```python
# Source: Context7 /websites/odoo_18_0_developer - "Notify Progress in Scheduled Action Batching"
# Existing action_start_matching() enhanced with progress tracking
def action_start_matching(self):
    """Start the matching process with progress tracking."""
    self.ensure_one()

    if self.line_count == 0:
        raise ValidationError("Cannot start matching without statement lines")

    # Set state to matching
    self.write({'state': 'matching'})

    # Delete any existing match proposals (re-matching scenario)
    self.match_ids.unlink()

    # Reset all statement line match_states to unmatched
    self.statement_line_ids.write({'match_state': 'unmatched'})

    # Get the engine
    engine = self.env['mass.reconcile.engine'].sudo()

    # Track progress and statistics
    total_lines = self.line_count
    processed = 0
    safe_count = 0
    probable_count = 0
    doubtful_count = 0
    unmatched_count = 0

    # Process each statement line
    for line in self.statement_line_ids:
        # Find candidates
        candidates = engine.find_candidates(line)
        model_candidates = engine.apply_reconcile_models(line)
        all_candidates = candidates + model_candidates

        if all_candidates:
            self._create_match_proposals(line, all_candidates)
            best_score = max(c['score'] for c in all_candidates)
            if best_score == 100:
                safe_count += 1
            elif best_score >= 80:
                probable_count += 1
            else:
                doubtful_count += 1
        else:
            unmatched_count += 1

        processed += 1

        # Update progress (for UI computed field or scheduled action)
        # For scheduled actions: self.env['ir.cron']._notify_progress(done=processed, remaining=total_lines-processed)
        # For UI: use computed field based on processed/total ratio

    # Transition to review state
    self.write({'state': 'review'})

    # Post summary message to chatter (audit trail)
    summary_message = (
        f"<p><strong>Matching completed:</strong></p>"
        f"<ul>"
        f"<li>Total lines processed: {total_lines} — 100% complete</li>"
        f"<li>Safe matches (100%): {safe_count} ({safe_count/total_lines*100:.1f}%)</li>"
        f"<li>Probable matches (80-99%): {probable_count} ({probable_count/total_lines*100:.1f}%)</li>"
        f"<li>Doubtful matches (<80%): {doubtful_count} ({doubtful_count/total_lines*100:.1f}%)</li>"
        f"<li>Unmatched: {unmatched_count} ({unmatched_count/total_lines*100:.1f}%)</li>"
        f"</ul>"
    )
    self.message_post(body=summary_message, subject='Matching Complete')
```

### Pattern 3: SELECT FOR UPDATE Row Locking
**What:** Prevent concurrent reconciliation conflicts using PostgreSQL row locking
**When to use:** Before starting reconciliation to lock batch and statement lines
**Example:**
```python
# Source: Multiple sources including Odoo forum discussions and PostgreSQL docs
# https://www.odoo.com/forum/help-1/repeated-serialization-errorscould-not-serialize-access-due-to-concurrent-update-in-postgres-database-148511
# https://www.postgresql.org/docs/current/explicit-locking.html

def action_start_matching(self):
    """Start matching with row locking to prevent concurrent conflicts."""
    self.ensure_one()

    # LOCK PATTERN: Use savepoint for transaction isolation
    try:
        with self.env.cr.savepoint():
            # Lock the batch record to prevent concurrent processing
            self.env.cr.execute(
                "SELECT id FROM mass_reconcile_batch WHERE id = %s FOR UPDATE NOWAIT",
                (self.id,)
            )

            # Lock all statement lines in this batch
            if self.statement_line_ids:
                line_ids = tuple(self.statement_line_ids.ids)
                self.env.cr.execute(
                    "SELECT id FROM account_bank_statement_line WHERE id IN %s FOR UPDATE NOWAIT",
                    (line_ids,)
                )

            # Proceed with matching logic (existing code)
            # ... rest of action_start_matching implementation ...

    except Exception as e:
        # Handle lock timeout or serialization errors
        if 'could not obtain lock' in str(e).lower():
            raise UserError(
                "This batch is currently being processed by another user. "
                "Please try again in a few moments."
            )
        raise
```

### Pattern 4: Batch State Machine with Validation
**What:** State transitions with validation guards (draft → matching → review → reconciled)
**When to use:** All state transition methods
**Example:**
```python
# Source: Existing code + Odoo forum patterns
# https://numla.com/blog/odoo-development-18/advanced-odoo-workflow-logic-with-python

# State field with tracking (already exists)
state = fields.Selection(
    selection=[
        ('draft', 'Draft'),
        ('matching', 'Matching'),
        ('review', 'Review'),
        ('reconciled', 'Reconciled')
    ],
    default='draft',
    required=True,
    string='Status',
    tracking=True,
    help='Current state of the reconciliation batch'
)

# State transition with validation
def action_start_matching(self):
    """Transition: draft → matching → review."""
    self.ensure_one()

    # Validation: can only start matching from draft
    if self.state != 'draft':
        raise ValidationError("Can only start matching from draft state")

    if self.line_count == 0:
        raise ValidationError("Cannot start matching without statement lines")

    # State transition
    self.write({'state': 'matching'})

    # ... processing logic ...

    # Auto-transition to review when complete
    self.write({'state': 'review'})

def action_reconcile(self):
    """Transition: review → reconciled."""
    self.ensure_one()

    # Validation: can only reconcile from review
    if self.state != 'review':
        raise ValidationError("Can only reconcile from review state")

    # Lock for concurrent access prevention
    with self.env.cr.savepoint():
        self.env.cr.execute(
            "SELECT id FROM mass_reconcile_batch WHERE id = %s FOR UPDATE NOWAIT",
            (self.id,)
        )

        # Perform reconciliation
        # ... reconciliation logic ...

        # Final state transition
        self.write({'state': 'reconciled'})
```

### Pattern 5: Computed Statistics with _read_group
**What:** Efficient matching statistics calculation without N+1 queries
**When to use:** Displaying batch progress and match distribution
**Example:**
```python
# Source: Existing code in mass_reconcile_batch.py (Phase 1 pattern)
# Already implemented - this pattern is PROVEN in current codebase

# Computed fields for statistics
matched_percentage = fields.Float(
    string='Matched Percentage',
    compute='_compute_matched_percentage',
    help='Percentage of lines with matches'
)

safe_match_count = fields.Integer(
    string='Safe Matches',
    compute='_compute_match_statistics',
    help='Lines with 100% confidence matches'
)

probable_match_count = fields.Integer(
    string='Probable Matches',
    compute='_compute_match_statistics',
    help='Lines with 80-99% confidence matches'
)

@api.depends('match_ids.confidence_class')
def _compute_match_statistics(self):
    """Use _read_group for batch performance to avoid N+1 queries."""
    if not self.ids:
        for batch in self:
            batch.safe_match_count = 0
            batch.probable_match_count = 0
        return

    # Group matches by batch and confidence class
    domain = [('batch_id', 'in', self.ids)]
    counts_data = self.env['mass.reconcile.match']._read_group(
        domain, ['batch_id', 'confidence_class'], ['__count']
    )

    # Initialize all batches to 0
    stats = {batch.id: {'safe': 0, 'probable': 0, 'doubtful': 0} for batch in self}

    # Populate from query results
    for (batch, confidence_class), count in counts_data:
        if batch and confidence_class:
            stats[batch.id][confidence_class] = count

    # Assign to records
    for batch in self:
        batch.safe_match_count = stats[batch.id]['safe']
        batch.probable_match_count = stats[batch.id]['probable']
```

### Anti-Patterns to Avoid

- **Iterating without chunking:** Processing 1000+ records in a single loop causes memory errors. Use `util.iter_browse` with chunk_size=80 or manual LIMIT/OFFSET with flush.
- **Calling cr.commit() in model methods:** NEVER commit explicitly unless in a scheduled action or background job context. Use savepoint for error isolation instead.
- **Using == for float comparisons:** Python float equality fails for monetary amounts. Always use `float_compare` from `odoo.tools.float_utils` (already implemented in Phase 2).
- **Forgetting to flush before raw SQL:** ORM changes are buffered. Always call `self.env['model'].flush_model(['field1', 'field2'])` before executing raw SQL UPDATE/SELECT.
- **Holding locks too long:** Keep SELECT FOR UPDATE blocks minimal. Lock, validate, process quickly, release. Don't hold locks while waiting for user input or external APIs.
- **N+1 queries in statistics:** Don't loop over batches calling `batch.match_ids.filtered()`. Use `_read_group` pattern (already implemented correctly in Phase 1).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Batch iteration with auto-flush | Custom loop with manual commit/flush | `odoo.upgrade.util.iter_browse(recordset, chunk_size=80, strategy='flush')` | Handles PostgreSQL savepoint limits (64 max), memory management, transaction boundaries |
| Progress tracking for scheduled actions | Custom progress table + polling | `self.env['ir.cron']._notify_progress(done=N, remaining=M)` | Built-in scheduler integration prevents worker timeouts, enables batching UI |
| Row locking for concurrency | Write_date comparison + retry loop | `SELECT id FROM table WHERE id=%s FOR UPDATE NOWAIT` | Prevents serialization errors, atomic locking, PostgreSQL-native |
| Date range widget | Custom JavaScript date picker | Odoo date fields with domain filters `[('date','>=',from),('date','<=',to)]` | Built-in calendar popup, localization, timezone handling |
| State transition validation | Separate workflow table | Selection field + constrains decorators | Simpler, trackable via mail.thread, sufficient for linear workflows |

**Key insight:** Odoo's ORM and PostgreSQL provide battle-tested primitives for concurrency, batching, and transaction management. Custom solutions for these problems invariably hit edge cases around deadlocks, memory exhaustion, and partial commit failures that took years to solve in the framework.

## Common Pitfalls

### Pitfall 1: Ignoring the 64 Savepoint Limit
**What goes wrong:** PostgreSQL slows down dramatically after 64 savepoints in a single transaction. If you process 100 records with savepoint-per-record, performance degrades exponentially after record #64.
**Why it happens:** Developers use `with self.env.cr.savepoint():` inside loops without awareness of PostgreSQL's internal savepoint tracking overhead.
**How to avoid:**
- Limit batch size to 80 lines (already planned) - keeps savepoints under threshold
- Use `util.iter_browse` with `strategy='flush'` instead of savepoint-per-iteration
- For Phase 3, process all 80 lines in a single transaction with ONE savepoint around the entire batch
**Warning signs:**
- Processing time increases non-linearly (first 50 records fast, next 50 slow)
- PostgreSQL logs show: "WARNING: there are already N open savepoints"

### Pitfall 2: SELECT FOR UPDATE Deadlock
**What goes wrong:** Two users start matching different batches simultaneously, each locks their batch, then both try to lock shared partners → deadlock.
**Why it happens:** Inconsistent lock ordering. User A locks batch→lines→partners in that order. User B locks batch→partners→lines. Both wait for each other's locks.
**How to avoid:**
- Lock in consistent order: always batch first, then lines, then related records
- Use `FOR UPDATE NOWAIT` instead of `FOR UPDATE` - fail fast with clear error instead of waiting
- Lock as late as possible - only before actual reconciliation, not during candidate search
- Keep locked sections small - lock, validate, update, release within seconds
**Warning signs:**
- Users report "operation timed out" or "frozen" UI
- PostgreSQL logs show: "ERROR: deadlock detected"
- Multiple concurrent batches processing same date ranges

### Pitfall 3: Flushing Too Late Before Raw SQL
**What goes wrong:** You update records via ORM, then immediately run raw SQL that doesn't see the changes. Results are stale or incorrect.
**Why it happens:** ORM buffers changes in memory until flush (auto-flush happens at transaction boundaries, before search, or explicit flush_model call). Raw SQL bypasses the buffer and queries database directly.
**How to avoid:**
```python
# WRONG
self.statement_line_ids.write({'match_state': 'matched'})
self.env.cr.execute("SELECT id FROM account_bank_statement_line WHERE match_state='matched'")
# ^ Won't see the 'matched' writes yet!

# RIGHT
self.statement_line_ids.write({'match_state': 'matched'})
self.env['account.bank.statement.line'].flush_model(['match_state'])
self.env.cr.execute("SELECT id FROM account_bank_statement_line WHERE match_state='matched'")
# ^ Now sees the updated state
```
**Warning signs:**
- SQL queries return empty results when ORM sees data
- Inconsistent behavior between test runs
- "Record not found" errors after ORM create/write

### Pitfall 4: Displaying Progress in Long-Running Synchronous Operations
**What goes wrong:** User clicks "Start Matching" button, UI shows loading spinner for 30 seconds with no feedback, user thinks it's frozen and refreshes page.
**Why it happens:** Odoo button actions are synchronous - UI blocks until method returns. Progress updates via computed fields don't render until transaction commits.
**How to avoid:**
- For 80-line batches (fast, <10 seconds): Show completion message with statistics in chatter after processing
- For larger batches (>10 seconds): Convert to scheduled action with `_notify_progress()` and show "Processing in background" notification
- For Phase 3: Use post-processing chatter message (already implemented in action_start_matching)
- Alternative: Use server actions with `type='ir.actions.server'` and `state='code'` for background processing
**Warning signs:**
- Users report "frozen" or "stuck" UI during matching
- Duplicate batch processing attempts (user clicked button multiple times)
- Browser timeout errors for large batches

### Pitfall 5: Concurrent Batch Reconciliation Race Condition
**What goes wrong:** Two accountants open the same batch, both click "Start Matching", both run matching engine simultaneously, duplicate match proposals created or partial results lost.
**Why it happens:** No row-level locking before state transition checks. Both transactions read `state='draft'`, both pass validation, both proceed to matching.
**How to avoid:**
```python
# WRONG - No locking
def action_start_matching(self):
    if self.state != 'draft':  # Both transactions see 'draft' simultaneously
        raise ValidationError("Can only start matching from draft state")
    self.write({'state': 'matching'})
    # ... Both proceed to create match proposals

# RIGHT - Lock first, then validate
def action_start_matching(self):
    self.ensure_one()
    try:
        with self.env.cr.savepoint():
            self.env.cr.execute(
                "SELECT id FROM mass_reconcile_batch WHERE id = %s FOR UPDATE NOWAIT",
                (self.id,)
            )
            # Only ONE transaction acquires lock, other gets immediate error
            self.env.cr.execute("SELECT state FROM mass_reconcile_batch WHERE id = %s", (self.id,))
            current_state = self.env.cr.fetchone()[0]
            if current_state != 'draft':
                raise ValidationError("Batch is already being processed")
            # ... Safe to proceed
    except Exception as e:
        if 'could not obtain lock' in str(e).lower():
            raise UserError("This batch is currently being processed by another user.")
        raise
```
**Warning signs:**
- Duplicate match proposals for same statement line + move pair
- SQL constraint violations: "UNIQUE(statement_line_id, suggested_move_id)"
- Users report "another user changed the record" errors

### Pitfall 6: Loading More Than 80 Lines Without User Warning
**What goes wrong:** User selects date range spanning 6 months, system loads 500 lines into batch, breaks 80-line limit constraint.
**Why it happens:** Validation happens after search rather than before, or search has no LIMIT clause.
**How to avoid:**
```python
# Add validation and clear user feedback
def action_load_statement_lines(self):
    # ... build domain ...

    # Count first before loading
    total_available = self.env['account.bank.statement.line'].search_count(domain)

    if total_available == 0:
        raise UserError("No unreconciled statement lines found in date range")

    # Load with limit, but warn user if there are more
    lines = self.env['account.bank.statement.line'].search(domain, limit=80, order='date asc')

    lines.write({'batch_id': self.id})

    # Inform user if there are more lines than the limit
    if total_available > 80:
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Loaded first 80 of {total_available} available lines. Create additional batches for remaining lines.',
                'type': 'warning',
                'sticky': True,
            }
        }
    else:
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'{len(lines)} statement lines loaded into batch',
                'type': 'success',
            }
        }
```
**Warning signs:**
- Batch has >80 lines
- UI performance degrades with large batches
- Users confused about which lines were loaded

## Code Examples

Verified patterns from official sources:

### Batch Iteration with Auto-Flush
```python
# Source: Context7 /websites/odoo_18_0_developer - "Iterate Recordsets Safely with ORM Utilities"
from odoo.upgrade import util

# Process large recordset in chunks with automatic flushing
statement_lines = self.env['account.bank.statement.line'].search([...])

for line in util.iter_browse(statement_lines, chunk_size=80, strategy='flush'):
    # Process each line
    # After each 80-line chunk, changes are automatically flushed to DB
    engine.process_line(line)
```

### Progress Notification for Scheduled Actions
```python
# Source: Context7 /websites/odoo_18_0_developer - "Notify Progress in Scheduled Action Batching"
# Use in scheduled actions to prevent worker timeouts
total = len(statement_lines)
for i, line in enumerate(statement_lines):
    process_line(line)
    if i % 10 == 0:  # Update every 10 records
        self.env['ir.cron']._notify_progress(done=i, remaining=total-i)
```

### Transaction Management with Savepoint
```python
# Source: WebSearch - http://blog.odooist.com/posts/working-with-savepoint/
# Isolate errors per iteration - if one fails, others succeed
for batch in batches:
    try:
        with self.env.cr.savepoint():
            batch.action_start_matching()
    except Exception as e:
        # Log error, continue with next batch
        _logger.error(f"Batch {batch.name} matching failed: {e}")
        continue
```

### Flush Before Raw SQL
```python
# Source: Context7 /websites/odoo_18_0_developer - "Flush Model and Use RETURNING in UPDATE Query"
# Make sure 'state' is up-to-date in database
self.env['mass.reconcile.batch'].flush_model(['state'])

# Use RETURNING clause to retrieve which rows have changed
self.env.cr.execute(
    "UPDATE mass_reconcile_batch SET state=%s WHERE state=%s RETURNING id",
    ['matching', 'draft']
)
ids = [row[0] for row in self.env.cr.fetchall()]

# Invalidate 'state' from the cache
self.env['mass.reconcile.batch'].invalidate_model(['state'])
```

### Date Range Domain Filter
```python
# Source: WebSearch - https://www.odoo.com/documentation/18.0/applications/essentials/search.html
# Domain pattern for date range selection (Odoo standard)
domain = [
    ('journal_id', '=', self.journal_id.id),
    ('is_reconciled', '=', False),
    ('batch_id', '=', False),
]

if self.date_from:
    domain.append(('date', '>=', self.date_from))
if self.date_to:
    domain.append(('date', '<=', self.date_to))

lines = self.env['account.bank.statement.line'].search(domain, limit=80, order='date asc')
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual commit/rollback in model methods | Savepoint context managers | Odoo 13+ | Safer error isolation, automatic rollback |
| Custom progress tracking tables | `ir.cron._notify_progress()` | Odoo 15+ | Native scheduler integration, no custom tables |
| Odoo workflows (workflow.xml) | State Selection fields + button methods | Odoo 11+ | Workflows deprecated, simpler model-based state machines |
| Manual chunking with LIMIT/OFFSET loops | `util.iter_browse` with strategies | Odoo 14+ | Automatic savepoint limit handling, memory management |
| String SQL with % formatting | SQL() wrapper with parameterization | Odoo 16+ | SQL injection protection, composable queries |
| write_date optimistic locking | SELECT FOR UPDATE pessimistic locking | PostgreSQL 9.1+ | Prevents serialization errors in high-concurrency scenarios |

**Deprecated/outdated:**
- **workflow.xml**: Removed in Odoo 11+, replaced by Selection state fields + button methods
- **manual cr.commit()**: Discouraged in Odoo 13+, use savepoint contexts instead
- **OpenUpgradeLib**: Use `odoo.upgrade.util` in Odoo 15+

## Open Questions

1. **Progress UI Pattern for Synchronous Processing**
   - What we know: Phase 3 processes 80 lines (fast, ~5-10 seconds), existing code posts chatter message with statistics after completion
   - What's unclear: Should we add real-time progress bar for 80-line batches, or is post-completion message sufficient?
   - Recommendation: Use existing chatter message pattern (already implemented in action_start_matching). Real-time progress bars require JavaScript + polling, not justified for <10 second operations. Reserve for Phase 4 if needed.

2. **Lock Granularity: Batch-Level vs Line-Level**
   - What we know: SELECT FOR UPDATE can lock batch record OR all statement lines OR both
   - What's unclear: What's the optimal locking strategy? Locking all 80 lines adds overhead but prevents partial conflicts.
   - Recommendation: Lock batch record only (lightweight, fast). If serialization errors occur in testing, escalate to locking statement lines. Start minimal, add locks if needed.

3. **Handling Lock Timeouts in User-Facing Actions**
   - What we know: NOWAIT fails immediately if lock unavailable, default FOR UPDATE waits indefinitely
   - What's unclear: Should we use NOWAIT (immediate failure) or FOR UPDATE with custom timeout?
   - Recommendation: Use NOWAIT for better UX (fail fast with "batch is being processed" message). Indefinite waiting creates poor user experience.

4. **Batch Statistics: Computed vs Stored Fields**
   - What we know: Phase 1 uses _read_group pattern for efficient stats, but stats are computed (not stored)
   - What's unclear: Should statistics (safe_count, probable_count, etc.) be stored fields for performance, or remain computed?
   - Recommendation: Keep computed for Phase 3 (80 lines = trivial performance impact). Consider storing in Phase 4 if dashboard views show performance issues.

5. **Transaction Boundaries: Single Transaction vs Per-Line Commits**
   - What we know: Processing 80 lines in one transaction is atomic (all-or-nothing), but large transaction holds locks longer
   - What's unclear: Should we commit after each line (more granular, faster lock release) or after entire batch (atomic, simpler rollback)?
   - Recommendation: Single transaction for entire 80-line batch. Atomicity is more important than lock granularity at this scale. Savepoint the entire matching operation.

## Sources

### Primary (HIGH confidence)
- Context7 /websites/odoo_18_0_developer - ORM patterns, batch processing utilities, transaction management
- PostgreSQL Documentation 18.0: 13.3. Explicit Locking - https://www.postgresql.org/docs/current/explicit-locking.html
- Existing codebase (Phase 1 & 2) - Proven patterns for _read_group, state machines, match proposals

### Secondary (MEDIUM confidence)
- [Odoo Forum: Repeated Serialization Errors in Postgres Database](https://www.odoo.com/forum/help-1/repeated-serialization-errorscould-not-serialize-access-due-to-concurrent-update-in-postgres-database-148511) - SELECT FOR UPDATE pattern for reconciliation
- [Odoo Forum: What is the cr.commit() risk](https://www.odoo.com/forum/help-1/what-is-the-crcommit-risk-how-to-safe-db-write-60885) - Transaction management best practices
- [Working with Savepoint | Odoo Open Treasures](http://blog.odooist.com/posts/working-with-savepoint/) - Savepoint error handling patterns
- [Numla: Advanced Odoo Workflow Logic with Python](https://numla.com/blog/odoo-development-18/advanced-odoo-workflow-logic-with-python-216) - State machine validation patterns
- [Odoo Documentation 18.0: Search, filter, and group records](https://www.odoo.com/documentation/18.0/applications/essentials/search.html) - Date range domain patterns
- [Odoo Documentation 18.0: Reconciliation models](https://www.odoo.com/documentation/18.0/applications/finance/accounting/bank/reconciliation_models.html) - Invoice matching patterns
- [Cybrosys: Batch Processing & Multiprocessing in Odoo 16](https://www.cybrosys.com/blog/an-overview-of-batch-processing-and-multiprocessing-in-odoo-16) - Batch size best practices

### Tertiary (LOW confidence)
- [CockroachLabs Blog: SELECT FOR UPDATE in SQL](https://www.cockroachlabs.com/blog/select-for-update/) - Row locking concepts (non-Odoo, general SQL)
- [Scalable Architect: PostgreSQL Row-Level Locks Guide](https://scalablearchitect.com/postgresql-row-level-locks-a-complete-guide-to-for-update-for-share-skip-locked-and-nowait/) - NOWAIT and SKIP LOCKED patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All tools are built into Odoo 18.0, verified via Context7 and existing codebase
- Architecture: HIGH - Patterns are proven in Phase 1/2 code and Odoo official docs
- Pitfalls: HIGH - Based on official warnings (savepoint limit, flush requirement) and community-documented issues (deadlocks, serialization errors)
- SELECT FOR UPDATE: MEDIUM - Pattern is well-documented but not in official Odoo docs (PostgreSQL standard, community-verified)
- Progress UI: MEDIUM - Official _notify_progress() exists but real-time UI patterns vary by implementation

**Research date:** 2026-02-12
**Valid until:** 2026-03-14 (30 days for stable Odoo 18.0 LTS release)
