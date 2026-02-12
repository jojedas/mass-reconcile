# Pitfalls Research

**Domain:** Odoo 18.0 Bank Reconciliation Module
**Researched:** 2026-02-12
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: N+1 Query Performance Degradation in Batch Processing

**What goes wrong:**
When processing large batches of bank statement lines (80+ lines), developers often iterate through recordsets without proper prefetching, causing one database query per record instead of batching queries. This transforms a 80-line reconciliation from a 2-second operation into a 2-minute operation.

**Why it happens:**
- Using `browse(record_id)` inside loops instead of browsing the entire recordset
- Accessing relational fields (partner_id, account_id, move_line_ids) without prefetching
- Not using `_read_group` for aggregations, causing individual `search_count` calls per record

**How to avoid:**
- Always browse entire recordsets before loops: `records = model.browse(record_ids)`
- Use `_read_group` for counting related records instead of individual `search_count` calls
- Leverage Odoo's automatic prefetching for relational fields by accessing them consistently
- Monitor SQL query counts during development (Odoo profiler shows SQL overhead)
- Use upgrade utilities like `util.iter_browse()` for extremely large datasets with chunk processing

**Warning signs:**
- Reconciliation widget freezes or shows "connection lost" messages
- Server logs show hundreds of similar SELECT queries
- Processing time scales linearly with number of lines (10 lines = 5s, 80 lines = 40s)
- High database CPU usage during reconciliation
- Profiler shows `create()` or field access methods consuming most time

**Phase to address:**
Phase 1 (Core Architecture) - Build with proper ORM patterns from the start. Adding batch optimization later requires refactoring entire query patterns.

---

### Pitfall 2: Race Conditions and Concurrent Update Conflicts

**What goes wrong:**
When multiple users reconcile bank statements simultaneously, or automated reconciliation runs while users work manually, concurrent updates to `account.move.line` records cause PostgreSQL serialization errors. The reconciliation appears successful in the UI but silently fails to create reconciliation entries. Additionally, updating partner balances during concurrent reconciliations raises internal errors.

**Why it happens:**
- Reconciliation process locks `account.move.line` records for updates
- Multiple transactions attempting to modify the same move lines simultaneously
- Partner balance updates triggering concurrent writes to the same partner record
- Odoo's transaction isolation causing serialization failures under high concurrency
- No optimistic locking mechanism for reconciliation operations

**How to avoid:**
- Implement record-level locking using `SELECT FOR UPDATE` when fetching move lines for reconciliation
- Add retry logic with exponential backoff for serialization failures
- Process batch reconciliations in smaller chunks with commits between chunks
- Use queue-based processing (message queue) to serialize automated reconciliations
- Add explicit database transaction management with proper error handling
- Display clear user feedback when reconciliation fails due to conflicts
- Prevent UI from showing "success" until database transaction commits

**Warning signs:**
- "Concurrent update" errors in server logs
- Reconciliation shows as complete but bank statement lines remain unmatched
- Partner balance discrepancies appear intermittently
- Increased `OperationalError` or `TransactionRollbackError` exceptions
- Multiple workers or users experiencing "loading page" messages during reconciliation
- Reconciliations mysteriously disappearing after appearing successful

**Phase to address:**
Phase 2 (Auto-matching Engine) - Add transaction management and locking when building the matching algorithm. Retrofitting locking later risks breaking existing reconciliations.

---

### Pitfall 3: False Positive Matches Due to Insufficient Validation

**What goes wrong:**
Auto-matching algorithms reconcile the wrong transactions, creating phantom balances and requiring time-consuming manual corrections. Common scenarios include matching invoices to wrong payments when amounts are identical, matching based on partial partner name matches, or ignoring date ranges that would eliminate invalid matches.

**Why it happens:**
- Relying solely on amount matching without additional context (partner, date range, reference)
- Odoo's built-in 3% tolerance for merchant fees being too permissive
- Short reference numbers (<5 characters) being ignored by Odoo's default matching rules
- Not validating that move lines are available for reconciliation (already reconciled or from wrong account)
- Trusting bank statement descriptions that contain ambiguous information
- Not checking account types compatibility (mixing balance sheet and P&L accounts)

**How to avoid:**
- Implement multi-factor matching: amount + partner + date range + reference
- Add configurable matching confidence scores (high/medium/low confidence)
- Require manual review for matches below high-confidence threshold
- Validate move line reconciliation constraints before matching:
  - Same account on all move lines
  - Account marked as reconcilable (`account.reconcile = True`)
  - Move lines not already reconciled
  - Move lines from posted journal entries only
- Add date tolerance configuration (e.g., match within +/- 7 days)
- Store matching rationale for audit trail ("matched on: invoice #12345, amount exact, partner exact, date within 2 days")
- Implement undo/revert functionality that's easily accessible
- Add preview mode showing proposed matches before applying

**Warning signs:**
- Users frequently clicking "Revert reconciliation"
- Balance sheet accounts showing unexpected balances
- Customer/vendor statements not matching Odoo balances
- Audit logs showing high volume of reconciliation reversals
- Users complaining about spending more time fixing auto-matches than doing manual reconciliation
- Invoices being marked paid when they shouldn't be

**Phase to address:**
Phase 2 (Auto-matching Engine) - Build validation into the core matching algorithm. Phase 3 (Manual Review Interface) - Add confidence scores and review workflow.

---

### Pitfall 4: Cache Invalidation Causing Performance Collapse

**What goes wrong:**
During batch reconciliation, the system repeatedly invalidates the entire model cache instead of just specific records, causing subsequent operations to re-fetch data from the database unnecessarily. This transforms a 5-second batch operation into a 5-minute operation as cache thrashing occurs. Additionally, mail.thread inheritance on accounting models triggers cache invalidation on every write operation.

**Why it happens:**
- Calling `invalidate_cache()` without parameters, clearing all environments
- Account models inheriting from `mail.thread`, which invalidates all caches on every create/write/unlink
- Not flushing pending updates before raw SQL queries with `flush_model(['field'])`
- Not properly invalidating cache after direct SQL UPDATE statements
- Cache coherence mechanisms in multi-worker environments causing cascading invalidations

**How to avoid:**
- Always specify fields when invalidating: `invalidate_model(['state', 'reconciled'])`
- Flush specific fields before SQL queries: `self.env['account.move.line'].flush_model(['state'])`
- After SQL updates, invalidate only affected fields: `records.invalidate_recordset(['state']); records.modified(['state'])`
- Avoid inheriting from `mail.thread` on high-volume reconciliation models unless absolutely necessary
- Process in chunks with explicit flush/invalidate between chunks: use `util.iter_browse()` with `strategy='flush'`
- Monitor cache invalidation frequency in production logs
- Disable prefetching judiciously for specific operations: `with_prefetch(False)` when batching isn't practical

**Warning signs:**
- Logs showing "Invalidating all model caches after database signaling"
- Query profiler showing same SELECT queries executed multiple times
- Performance degrading as batch size increases non-linearly
- Workers becoming unresponsive during large reconciliations
- Database connection pool exhaustion
- Reconciliation performance varying wildly between identical operations

**Phase to address:**
Phase 1 (Core Architecture) - Establish proper cache management patterns early. Phase 2 (Auto-matching Engine) - Apply specifically to batch operations.

---

### Pitfall 5: Floating Point Rounding Errors in Multi-Currency Reconciliation

**What goes wrong:**
When reconciling foreign currency transactions, rounding errors create 0.01 differences that prevent automatic reconciliation. For example, two bills of $2,025.00 USD each converted to EUR at 1.0683 rate individually equal 3,791.06 EUR, but the combined amount ($4,050) divided by the rate equals 3,791.07 EUR—a 0.01 EUR difference due to rounding each line individually versus rounding the sum.

**Why it happens:**
- Python float arithmetic loses precision in decimal calculations
- Odoo rounds each line individually then sums, versus summing then rounding
- Exchange rates stored with limited decimal precision
- Multiple conversion operations within single account move
- Currency precision settings (typically 2 decimals) amplifying rounding errors

**How to avoid:**
- Use Odoo's `float_utils.py` functions for currency comparisons: `float_compare(amount1, amount2, precision_rounding=currency.rounding)`
- Never use direct `==` comparison for monetary amounts
- Implement configurable rounding tolerance for reconciliation matching (e.g., 0.02 currency units)
- For multi-currency operations, create separate account moves and reconcile them (avoid multiple conversions in one entry)
- Validate that rounding precision matches currency decimal accuracy: `currency.decimal_places`
- Store amounts in currency's base units when possible (cents for USD/EUR)
- Add explicit exchange difference handling for remaining fractional amounts
- Document expected rounding behavior in matching algorithm

**Warning signs:**
- Reconciliations failing with 0.01 differences
- Exchange difference amounts accumulating unexpectedly
- Users manually creating journal entries to clear tiny differences
- Automated matching skipping foreign currency transactions
- Balance sheet showing small unexplained currency conversion differences
- Unit tests failing intermittently on currency calculations

**Phase to address:**
Phase 2 (Auto-matching Engine) - Build rounding tolerance into matching algorithm. Phase 4 (Multi-currency Support) if separating currency handling into later phase.

---

### Pitfall 6: Breaking Odoo's Accounting Constraints and Validation Rules

**What goes wrong:**
Custom reconciliation code bypasses Odoo's built-in validation constraints, creating invalid accounting states: reconciling move lines from different accounts, reconciling already-reconciled entries, mixing balance sheet and P&L accounts, or creating unbalanced journal entries. This corrupts financial reports and makes auditing impossible.

**Why it happens:**
- Using raw SQL or `sudo()` to bypass ORM constraints
- Not checking `account.reconcile` flag before attempting reconciliation
- Ignoring `account.move.line` state validation (only posted entries can be reconciled)
- Not validating debit/credit balance (must sum to zero)
- Reconciling lines from different partners without proper write-off entries
- Using wrong account types for reconciliation

**How to avoid:**
- Always use ORM methods instead of raw SQL for reconciliation operations
- Implement validation using `@api.constrains` decorators:
  ```python
  @api.constrains('move_line_ids')
  def _check_reconciliation_valid(self):
      for record in self:
          accounts = record.move_line_ids.mapped('account_id')
          if len(accounts) > 1:
              raise ValidationError(_("Cannot reconcile lines from different accounts"))
          if not accounts.reconcile:
              raise ValidationError(_("Account %s is not marked as reconcilable") % accounts.name)
  ```
- Check move line state before reconciliation: `if line.move_id.state != 'posted'`
- Validate balance: `if not float_is_zero(sum(debit - credit), precision_rounding=currency.rounding)`
- Never use `sudo()` for reconciliation—use proper access rights instead
- Validate constraints in both automated and manual reconciliation paths
- Add comprehensive unit tests covering constraint violations

**Warning signs:**
- ValidationError exceptions appearing in production
- Financial reports showing unbalanced accounts
- Audit trail showing impossible reconciliation states
- Database constraints failing on write operations
- Users able to reconcile draft journal entries
- Balance sheet not balancing
- Reconciliation records without proper `account.full_reconcile_id`

**Phase to address:**
Phase 1 (Core Architecture) - Implement validation layer from the beginning. Adding constraints later will break existing reconciliations.

---

### Pitfall 7: Upgrade and Migration Compatibility Failures

**What goes wrong:**
Custom reconciliation module breaks after Odoo version upgrades because it depends on internal APIs that changed, uses deprecated fields/methods, or conflicts with new reconciliation features. Bank synchronization breaks, custom reconciliation models become incompatible, or data migrations fail leaving orphaned reconciliation records.

**Why it happens:**
- Depending on private methods (prefixed with `_`) from `account` module
- Overriding Odoo core methods that have changed signatures in new versions
- Hard-coding field names or model structures that evolve between versions
- Not testing against Odoo upgrade path
- Custom modules not compatible with new reconciliation widget in Odoo 18+
- Database schema changes in account.move.line or account.bank.statement.line models

**How to avoid:**
- Only use public APIs from Odoo's account module
- Prefer composition over inheritance when extending core models
- Use XML-RPC or JSON-RPC compatible interfaces instead of internal Python APIs
- Implement adapter pattern for Odoo core interactions—isolate version-specific code
- Add version checks: `from odoo.release import version_info; if version_info[0] >= 18:`
- Never modify core Odoo tables directly—use Odoo's upgrade utilities
- Test against Odoo's migration path: install in v17, upgrade to v18, verify reconciliations intact
- Document all dependencies on Odoo core functionality
- Subscribe to Odoo release notes and breaking changes announcements
- Use OCA (Odoo Community Association) modules where possible—they follow upgrade best practices
- Implement data migration scripts in `pre-migration.py` and `post-migration.py`

**Warning signs:**
- Module fails to install after Odoo upgrade
- ImportError or AttributeError exceptions after upgrade
- Reconciliation widget shows blank screen or JavaScript errors
- "Field not found" errors in logs
- Bank synchronization stops working after upgrade
- Previously reconciled transactions showing as unreconciled
- Custom reconciliation models not appearing in Odoo 18+ interface

**Phase to address:**
Phase 1 (Core Architecture) - Design for upgradability from the start. Use abstraction layers for core integrations. Phase 5+ (Maintenance) - Establish upgrade testing process.

---

## Moderate Pitfalls

### Pitfall 8: Inadequate Access Rights and Security Model

**What goes wrong:**
Users without proper accounting permissions can view/modify reconciliations, automated processes bypass security checks using `sudo()`, or sensitive bank statement data is exposed to unauthorized users.

**Why it happens:**
- Over-using `sudo()` to bypass permission issues instead of fixing access rights
- Not defining proper record rules for multi-company scenarios
- Missing field-level access controls on sensitive data (bank account numbers)
- Not restricting reconciliation model configuration to accounting managers

**How to avoid:**
- Define granular access rights in `ir.model.access.csv`:
  - `account.reconcile.model` - only accounting managers can create/modify
  - `account.bank.statement.line` - accounting users can read/reconcile
- Implement record rules for multi-company data isolation
- Use public methods with proper access checks instead of `sudo()`
- Validate `self.env.user.has_group('account.group_account_user')` before sensitive operations
- Never concatenate user input in SQL queries—always use parameterized queries
- Log all reconciliation actions for audit trail

**Warning signs:**
- Users accessing other companies' bank statements
- Reconciliation modifications without audit trail
- SQL injection vulnerabilities in custom search filters
- Users bypassing workflow by directly modifying reconciliation records

**Phase to address:**
Phase 1 (Core Architecture) - Define security model early. Phase 3 (Manual Review Interface) - Implement UI-level access controls.

---

### Pitfall 9: Ignoring Odoo Community vs Enterprise Differences

**What goes wrong:**
Module developed for Community Edition fails when deployed to Enterprise, or vice versa. Features assumed to exist (like automated reconciliation) are missing in Community, or Enterprise-specific dependencies break Community installations.

**Why it happens:**
- Enterprise has built-in automated reconciliation; Community requires manual processes or OCA modules
- Bank synchronization APIs differ between editions
- Reconciliation widget UI completely different in Enterprise
- Multi-currency features more robust in Enterprise
- Assuming `account_reconcile_oca` module is installed in Community deployments

**How to avoid:**
- Detect edition at runtime: check for Enterprise-specific modules
- Make Enterprise features optional with graceful degradation
- Document minimum required OCA modules for Community Edition
- Test in both environments during development
- Use abstraction layer for edition-specific features
- Provide clear installation instructions per edition
- Consider targeting only one edition initially to reduce complexity

**Warning signs:**
- Module installs in one edition but not the other
- Features working in development (Enterprise) but failing in production (Community)
- Dependencies on unavailable modules
- UI rendering differently between editions

**Phase to address:**
Phase 1 (Core Architecture) - Decide target edition(s) and abstract differences. Document clearly in README.

---

### Pitfall 10: Insufficient Error Handling and User Feedback

**What goes wrong:**
When auto-matching fails or encounters errors, users see generic error messages or reconciliation silently fails. No visibility into why specific transactions weren't matched, making troubleshooting impossible.

**Why it happens:**
- Exception handling catches all errors and logs them without user notification
- No distinction between recoverable errors (no match found) and system errors (database failure)
- Matching algorithm doesn't track rejection reasons
- No user-facing logs or debugging interface

**How to avoid:**
- Implement structured error categorization:
  - No match found (expected, show in UI)
  - Validation failed (user can fix, provide actionable message)
  - System error (log and alert administrators)
- Store matching attempts and rejection reasons for each bank line
- Add debugging mode showing why specific matches were rejected
- Provide clear user messages: "Invoice #12345 not matched: amount differs by $0.50"
- Implement notification system for automated reconciliation failures
- Add reconciliation report showing success/failure statistics

**Warning signs:**
- Users constantly asking "why wasn't this matched?"
- Support tickets about failed reconciliations
- No visibility into automated reconciliation process
- Silent failures requiring database inspection to diagnose

**Phase to address:**
Phase 2 (Auto-matching Engine) - Build logging into algorithm. Phase 3 (Manual Review Interface) - Expose logs to users.

---

### Pitfall 11: Not Handling Duplicate Reconciliations and Reversals

**What goes wrong:**
System allows reconciling the same bank statement line twice, or reversing a reconciliation leaves orphaned records causing balance discrepancies.

**Why it happens:**
- Not checking `reconciled` field before attempting reconciliation
- Reversal process incomplete—doesn't clean up all related records
- No safeguards preventing duplicate bank statement imports
- Partial reconciliation state not properly handled

**How to avoid:**
- Add database constraints preventing duplicate reconciliations
- Check `line.reconciled == True` before matching
- Implement proper reversal:
  ```python
  def action_undo_reconciliation(self):
      # Remove full reconcile record
      full_reconcile = self.move_line_ids.mapped('full_reconcile_id')
      full_reconcile.unlink()
      # Clear partial reconcile
      self.move_line_ids.remove_move_reconcile()
      # Reset statement line state
      self.write({'is_reconciled': False})
  ```
- Detect duplicate statement imports by checking date + amount + reference
- Provide clear UI indication of already-reconciled lines
- Store reconciliation history for audit purposes

**Warning signs:**
- "Already reconciled" errors appearing frequently
- Balance sheet accounts mysteriously out of balance
- Users needing to manually delete reconciliation records
- Same bank transaction appearing multiple times

**Phase to address:**
Phase 2 (Auto-matching Engine) - Add duplicate detection. Phase 3 (Manual Review Interface) - Implement reversal functionality.

---

### Pitfall 12: Poor Exchange Rate Timing Management

**What goes wrong:**
Foreign currency reconciliations use wrong exchange rates when payment and invoice are dated differently, or exchange difference entries are not created automatically when expected.

**Why it happens:**
- Not updating currency rates before posting transactions
- Partial reconciliations preventing exchange difference calculation
- Using MISC journal type instead of payment journal for currency transactions
- Exchange rate effective date not matching transaction date

**How to avoid:**
- Update currency rates before processing foreign currency reconciliations
- Validate exchange rate exists for transaction date
- Require full reconciliation to trigger exchange difference calculation
- Use proper journal types (Bank/Cash) for payment reconciliations
- Store both foreign currency amount and base currency amount
- Create exchange difference journal entries in dedicated exchange difference account
- Document exchange rate source and update frequency

**Warning signs:**
- Foreign currency reconciliations showing unexpected gain/loss amounts
- Partial reconciliations never completing
- Exchange difference account showing unusual balances
- Manually-posted exchange rate adjustments accumulating

**Phase to address:**
Phase 4 (Multi-currency Support) if separated, otherwise Phase 2 (Auto-matching Engine).

---

## Minor Pitfalls

### Pitfall 13: Inefficient Search and Filtering Implementation

**What goes wrong:**
Custom search filters for finding matching transactions use inefficient domain queries, causing slow performance with large datasets.

**Prevention:**
- Use indexed fields in domain filters (partner_id, account_id, date)
- Limit search results with reasonable date ranges
- Avoid complex calculated fields in search domains
- Use `name_search` instead of `search` + `read` for relational fields

---

### Pitfall 14: Missing Transaction Locking During Reconciliation

**What goes wrong:**
User starts reconciling a bank statement, another user modifies the underlying move lines, first user's reconciliation uses stale data.

**Prevention:**
- Lock bank statement lines during reconciliation: `SELECT FOR UPDATE NOWAIT`
- Show warning if underlying data changed since page load
- Implement optimistic locking with version fields
- Add transaction isolation level configuration

---

### Pitfall 15: Not Handling Partial Reconciliations Properly

**What goes wrong:**
Reconciling a payment against multiple invoices fails when amounts don't match exactly, leaving partial reconciliation records that confuse reporting.

**Prevention:**
- Implement proper partial reconciliation workflow
- Allow write-off entries for small differences
- Create payment allocation records tracking which invoice portions are paid
- Clear UI indication of partially-reconciled status

---

### Pitfall 16: Hardcoded Configuration Values

**What goes wrong:**
Matching tolerances, date ranges, and account configurations hardcoded in Python instead of user-configurable.

**Prevention:**
- Create configuration model: `account.reconcile.config`
- Make all thresholds configurable: amount tolerance, date range, confidence thresholds
- Allow per-company configuration in multi-company setups
- Provide sensible defaults but allow customization

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Using `sudo()` to bypass permissions | Reconciliation works immediately | Security vulnerabilities, audit trail gaps | Never - fix access rights instead |
| Direct SQL instead of ORM | Faster queries | Breaks on upgrade, bypasses validations | Only for read-only reporting queries, never for reconciliation logic |
| Skipping cache invalidation after SQL | Simpler code | Stale data causing wrong reconciliations | Never - always invalidate after SQL writes |
| Hardcoding matching rules | Faster development | Users can't adapt to business changes | Only for MVP prototype, refactor before Phase 2 |
| Single-threaded batch processing | Simple implementation | Can't scale to large datasets | Acceptable for <100 lines, refactor for production |
| Ignoring floating point precision | Exact matches work | Fails on currency conversions | Never - use float_compare from start |
| No transaction rollback on errors | Happy path works | Partial reconciliations corrupt data | Never - wrap in proper transactions |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Bank feeds (Enterprise) | Assuming synchronization always succeeds | Add error handling for sync failures, store last sync timestamp, retry logic |
| Payment acquirers | Not handling currency conversion in acquirer reconciliation | Validate currencies match before auto-reconciliation |
| Invoice imports | Reconciling against draft invoices | Only reconcile posted (`state='posted'`) move lines |
| Third-party bank APIs | Hardcoding bank formats | Use adapter pattern, support multiple formats |
| Multi-company | Sharing reconciliation models across companies | Create per-company reconciliation models with record rules |
| OCA modules (Community) | Assuming `account_reconcile_oca` is installed | Check module installed, provide fallback or installation instructions |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Fetching all move lines at once | High memory usage, server crashes | Use chunked processing with `iter_browse()` | >10,000 move lines in single account |
| No database indices on custom fields | Slow search filters | Add `index=True` to frequently-queried fields | >50,000 bank statement lines |
| Computing balances on every record | Reconciliation freezes | Use `_read_group` for aggregations | >1,000 lines in batch |
| Not limiting date ranges | Loading years of transactions | Default to last 90 days, make configurable | >100,000 total transactions |
| Triggering automated actions on every line | Slow batch import | Defer automated actions until batch complete | >50 lines per batch |
| Deep inheritance chains | Slow record creation | Composition over inheritance | >5 levels of model inheritance |
| Unoptimized reconciliation widget queries | Widget takes minutes to load | Add SQL EXPLAIN analysis, optimize queries | >1,000 unreconciled lines |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| SQL injection in search filters | Complete database compromise | Always use parameterized queries, validate input |
| Exposing bank account numbers in logs | PCI compliance violation | Mask sensitive fields in logs, use separate audit log |
| No rate limiting on API endpoints | DoS attacks on reconciliation API | Implement rate limiting (e.g., 100 requests/minute) |
| Storing reconciliation rules without encryption | Exposure of business logic | Use Odoo's encryption for sensitive config |
| Allowing reconciliation without authentication | Fraudulent reconciliations | Require login, validate session, check user groups |
| Not logging reconciliation modifications | No audit trail for compliance | Log all reconciliation actions with user, timestamp, before/after state |
| Trusting bank feed data without validation | Malicious data injection | Validate all imported data, sanitize descriptions |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No visual distinction between auto/manual matches | Users can't trust automation | Color-code by confidence level, show matching rationale |
| Requiring multiple clicks per reconciliation | Slow manual workflow | Keyboard shortcuts, batch operations, smart defaults |
| No undo functionality | Fear of making mistakes | Prominent "Revert" button, show confirmation before commit |
| Cryptic error messages | Users can't self-serve | Plain language errors with solutions: "Invoice #12345 already reconciled. Click here to view." |
| No progress indicator for batch operations | Users think system froze | Real-time progress bar showing "Processed 45/80 lines" |
| Mixing reconciled and unreconciled lines | Visual clutter | Filter to show only unreconciled by default |
| No preview before applying matches | Surprises after commit | Preview mode showing all proposed matches with approve/reject |

## "Looks Done But Isn't" Checklist

- [ ] **Auto-matching:** Often missing confidence thresholds—verify matches require minimum confidence score, not just "any match found"
- [ ] **Multi-currency:** Often missing exchange difference accounting—verify exchange gain/loss entries created automatically
- [ ] **Batch processing:** Often missing transaction isolation—verify all-or-nothing commits, no partial failures
- [ ] **Reversal:** Often missing cleanup of related records—verify full_reconcile_id and partial_reconcile cleared
- [ ] **Access rights:** Often missing record rules—verify users can't see other companies' data in multi-company setup
- [ ] **Performance:** Often missing indices—verify custom fields have `index=True` for search performance
- [ ] **Error handling:** Often missing user notifications—verify failed reconciliations notify users, not just log
- [ ] **Testing:** Often missing multi-user scenarios—verify concurrent reconciliation doesn't corrupt data
- [ ] **Audit trail:** Often missing changelog—verify who reconciled what when is stored
- [ ] **Upgrade path:** Often missing migration scripts—verify module upgrades without data loss

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| False positive matches | MEDIUM | 1. Identify incorrect reconciliations via balance sheet review 2. Revert using UI or SQL 3. Adjust matching rules 4. Re-run with corrected algorithm |
| Race condition data corruption | HIGH | 1. Identify affected transactions via audit log 2. Manually reverse corrupted reconciliations 3. Add database locking 4. Re-process transactions 5. Validate balances |
| Cache invalidation performance | LOW | 1. Identify broad invalidation calls in code 2. Add field-specific invalidation 3. Restart workers to clear stuck caches 4. Re-deploy fixed code |
| Rounding errors accumulated | MEDIUM | 1. Create manual journal entries for differences 2. Implement float_compare in matching 3. Re-deploy and test with historical data |
| Broken after upgrade | HIGH | 1. Restore from backup if critical 2. Review Odoo upgrade notes for breaking changes 3. Refactor to use public APIs 4. Test thoroughly before re-deployment |
| Missing access rights | LOW | 1. Define proper access rights in security files 2. Remove sudo() calls 3. Upgrade module to apply new security 4. Verify users have correct groups |
| Duplicate reconciliations | MEDIUM | 1. Identify duplicates via SQL: `SELECT bank_line_id, COUNT(*) FROM reconcile GROUP BY bank_line_id HAVING COUNT(*) > 1` 2. Manually choose correct reconciliation 3. Delete duplicates 4. Add uniqueness constraint |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| N+1 Query Performance | Phase 1: Core Architecture | Run profiler on 1,000 line batch - should execute <50 queries |
| Race Conditions | Phase 2: Auto-matching Engine | Test 5 concurrent users reconciling same statements - no errors |
| False Positive Matches | Phase 2: Auto-matching Engine | Manual review of 100 auto-matches - <2% error rate |
| Cache Invalidation | Phase 1: Core Architecture | Monitor cache hit rate - should be >90% for repeated operations |
| Floating Point Errors | Phase 2: Auto-matching Engine | Test multi-currency reconciliation - no 0.01 differences |
| Accounting Constraints | Phase 1: Core Architecture | Unit tests covering all constraint validations - 100% pass |
| Upgrade Compatibility | Phase 1: Core Architecture | Test upgrade from Odoo 17→18 - module installs and works |
| Access Rights | Phase 1: Core Architecture | Test multi-company, multi-user scenarios - no unauthorized access |
| Community vs Enterprise | Phase 1: Core Architecture | Test installation on both editions - document differences |
| Error Handling | Phase 3: Manual Review Interface | Trigger known errors - users see actionable messages |
| Duplicate Reconciliations | Phase 2: Auto-matching Engine | Attempt duplicate reconciliation - system prevents it |
| Exchange Rate Timing | Phase 4: Multi-currency Support | Reconcile payment 30 days after invoice - correct exchange diff |
| Inefficient Search | Phase 2: Auto-matching Engine | Search 100,000 move lines with filters - <2 seconds |
| Transaction Locking | Phase 2: Auto-matching Engine | Test concurrent modification - proper lock wait or error |
| Partial Reconciliations | Phase 3: Manual Review Interface | Reconcile payment to multiple invoices - clean partial state |
| Hardcoded Config | Phase 3: Manual Review Interface | All thresholds configurable via UI |

## Sources

**Performance and Technical Issues:**
- [Odoo Issue #30934 - Performance problem at reconciliation widget](https://github.com/odoo/odoo/issues/30934)
- [Odoo Issue #91873 - Concurrency errors in account.move](https://github.com/odoo/odoo/issues/91873)
- [Odoo Issue #13846 - Partner concurrent update during reconciliation](https://github.com/odoo/odoo/issues/13846)
- [Odoo Issue #23172 - Performance issues when clearing model cache](https://github.com/odoo/odoo/issues/23172)
- [Odoo Documentation 18.0 - Performance](https://www.odoo.com/documentation/18.0/developer/reference/backend/performance)
- [Odoo Documentation 18.0 - ORM](https://www.odoo.com/documentation/18.0/developer/reference/backend/orm)

**Reconciliation Best Practices:**
- [The Ledger Labs - Common Errors in Odoo Accounting](https://theledgerlabs.com/how-to-fix-errors-in-odoo-accounting/)
- [The Ledger Labs - Odoo Bank Reconciliation Guide](https://theledgerlabs.com/odoo-bank-reconciliation-guide/)
- [HSX Tech - Best Practices for Reconciliation](https://hsxtech.net/best-practices-for-reconciliation-in-odoo-accounting/)
- [Odoo Forum - Critical Flaws in Bank Reconciliation](https://www.odoo.com/forum/help-1/critical-flaws-in-odoo-bank-reconciliation-functionality-280877)

**Currency and Rounding Issues:**
- [Odoo Forum - Rounding issue during reconciling](https://www.odoo.com/forum/help-1/rounding-issue-during-reconciling-227644)
- [Odoo Issue #9500 - Monetary field ignores precision](https://github.com/odoo/odoo/issues/9500)
- [Odoo Documentation 18.0 - Multi-currency system](https://www.odoo.com/documentation/18.0/applications/finance/accounting/get_started/multi_currency.html)
- [Odoo Forum - Exchange Rate issues](https://www.odoo.com/forum/help-1/exchange-rate-issues-in-odoo-accounting-257352)

**Upgrade and Compatibility:**
- [Ksolves - Odoo 19 Guide 2025](https://www.ksolves.com/guides/odoo-19)
- [Ariashaw - Upgrade Odoo 17 to 18](https://ariashaw.com/guides/upgrade-odoo-17-to-18)
- [OdooVizion - Odoo Migration Guide 2025](https://odoovizion.com/blog/odoo-migration-guide/)
- [Navabrindsol - Odoo 18 Migration Challenges](https://navabrindsol.com/odoo/odoo-18-migration-challenges-and-best-practices/)

**Security and Validation:**
- [Odoo Documentation 18.0 - Security](https://www.odoo.com/documentation/18.0/developer/reference/backend/security)
- [Odoo Issue #2527 - Reconcile entries with different accounts](https://github.com/odoo/odoo/issues/2527)
- [CrossClassify - Odoo Security Best Practices](https://www.crossclassify.com/resources/articles/odoo-security-best-practices/)

**Community vs Enterprise:**
- [Technaureus - Odoo Community vs Enterprise Accounting](https://www.technaureus.com/blog-detail/comparison-between-odoo-community-accounting-and-e)
- [Port Cities - Odoo Enterprise vs Community Differences](https://portcities.net/blog/erp-and-odoo-insights-2/odoo-enterprise-vs-odoo-community-edition-what-are-the-differences-40)
- [OCA Discussion #181 - Community vs Enterprise in Odoo 17](https://github.com/orgs/OCA/discussions/181)

**Testing and Development:**
- [Odoo Documentation 18.0 - Testing](https://www.odoo.com/documentation/18.0/developer/reference/backend/testing)
- [Arsalan Yasin - Writing Tests for Odoo Modules](https://arsalanyasin.com.au/writing-robust-unit-and-integration-tests-for-odoo-modules-using-pytest/)

**Reconciliation Features and Matching:**
- [Odoo Documentation 18.0 - Bank Reconciliation](https://www.odoo.com/documentation/18.0/applications/finance/accounting/bank/reconciliation.html)
- [Odoo Documentation 18.0 - Reconciliation Models](https://www.odoo.com/documentation/18.0/applications/finance/accounting/bank/reconciliation_models.html)
- [Odoo Forum - Already Reconciled Error](https://www.odoo.com/forum/help-1/a-selected-move-line-was-already-reconciled-160428)
- [Odoo Forum - Re-reconciling Bank Statement Line](https://www.odoo.com/forum/help-1/re-reconciling-a-bank-statement-line-after-it-has-been-reconciled-incorrectly-186219)

---
*Pitfalls research for: Odoo 18.0 Community Mass Bank Reconciliation Module*
*Researched: 2026-02-12*
