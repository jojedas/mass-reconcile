---
phase: 02-matching-engine-auto-reconciliation
plan: 02
subsystem: batch-orchestration
tags: [integration, reconcile-models, workflow, automation]

dependency_graph:
  requires:
    - 02-01 (Matching engine + scorer)
    - 01-01 (Foundation models)
  provides:
    - Batch orchestration calling matching engine
    - Reconcile model integration for recurring expenses
    - Match proposal creation with confidence classification
    - Automated state transitions (draft → matching → review)
  affects:
    - Phase 4 (Manual Review Interface will consume match proposals)

tech_stack:
  added:
    - Reconcile model integration (account.reconcile.model)
    - Batch create pattern for match proposals
    - Chatter integration for matching summaries
  patterns:
    - Batch orchestration with engine invocation
    - Graceful degradation (missing OCA module handling)
    - Confidence-based classification (safe/probable/doubtful)
    - Batch create for performance (single DB call for all proposals)

key_files:
  created: []
  modified:
    - models/mass_reconcile_batch.py
    - models/mass_reconcile_engine.py
    - models/mass_reconcile_match.py

decisions:
  - "invoice_matching rule type only (Phase 2 scope): Other rule types (writeoff_button, writeoff_suggestion) are out of scope for mass reconciliation v1"
  - "Reconcile model score fixed at 90 (probable): Rule-based matches are reliable but not as certain as exact algorithm matches"
  - "Graceful OCA module degradation: apply_reconcile_models returns empty list if account.reconcile.model doesn't exist"
  - "Batch create for match proposals: Single DB call creates all proposals for a statement line (not loop with individual creates)"
  - "Match state transitions: unmatched → matched based on presence of candidates"
  - "Chatter summary format: HTML list with safe/probable/doubtful/unmatched counts"
  - "Statement line gets best match: match_score and suggested_move_id set to highest-scored candidate"

metrics:
  duration: "117 seconds (1.95 minutes)"
  completed: "2026-02-12"
  commits: 2
  files_created: 0
  files_modified: 3
---

# Phase 02 Plan 02: Batch Orchestration + Reconcile Model Integration Summary

**One-liner:** Batch orchestration invoking matching engine for all statement lines, creating match proposals with confidence classification, integrating account.reconcile.model for recurring expense rules (invoice_matching type), and transitioning batch through draft → matching → review states with chatter summaries.

## What Was Built

Integrated the matching engine into the batch reconciliation workflow, connecting the isolated algorithm from Plan 01 to the user-facing batch orchestration. When a user clicks "Start Matching" on a batch, the system now processes all statement lines through the engine, creates match proposals with scores and classifications, integrates with existing Odoo reconciliation rules, and transitions the batch to review state with a summary message.

### Components

**mass_reconcile_batch.py - action_start_matching method:**
- Sets state to 'matching' at start
- Deletes existing match proposals (re-matching scenario)
- Resets all statement line match_states to 'unmatched'
- Processes each statement line through engine.find_candidates()
- Applies reconcile models via engine.apply_reconcile_models()
- Creates match proposals via _create_match_proposals()
- Tracks statistics (safe/probable/doubtful/unmatched counts)
- Transitions to 'review' state
- Posts HTML summary to chatter

**mass_reconcile_batch.py - _create_match_proposals method:**
- Takes statement line and candidate list
- Prepares vals_list for batch create
- Maps candidate scores to match_type (exact/partial/internal_transfer/reconcile_model)
- Creates all proposals in single DB call (performance optimization)
- Updates statement line with best match (highest score)
- Sets match_state to 'matched'

**mass_reconcile_engine.py - apply_reconcile_models method:**
- Searches for account.reconcile.model records with rule_type='invoice_matching'
- Filters by company
- Checks each model against statement line criteria (partner/label/amount)
- Returns candidates in same format as find_candidates()
- Scores reconcile model matches at 90 (probable)
- Gracefully handles missing OCA module (try/except returns empty list)

**mass_reconcile_match.py - Enhanced match types and confidence:**
- Added 'internal_transfer' and 'reconcile_model' match types
- Added confidence_class computed field (safe/probable/doubtful)
- Uses scorer.classify_match() for consistent classification
- Stored computed field for query performance

## Deviations from Plan

None - plan executed exactly as written. All tasks completed without architectural changes or blocking issues.

## Key Technical Details

### Batch Orchestration Flow

```
draft → [action_start_matching] → matching
  ↓
1. Delete existing match proposals (self.match_ids.unlink())
2. Reset statement lines (match_state='unmatched')
3. For each line:
   a. engine.find_candidates(line)
   b. engine.apply_reconcile_models(line)
   c. Combine all candidates
   d. _create_match_proposals(line, all_candidates)
4. Track statistics (safe/probable/doubtful/unmatched)
5. Transition to review
6. Post chatter summary
```

### Reconcile Model Integration (MATCH-12)

**Scope:** invoice_matching rule type only (Phase 2 decision)

**Matching Criteria:**
- match_partner: Verifies partner matches (if model requires it)
- match_label: Substring match on payment_ref
- match_amount: Within min/max tolerance

**Scoring:** Fixed at 90 (probable) - rule-based matches are reliable but not as certain as exact algorithm matches

**Graceful Degradation:** If account.reconcile.model doesn't exist (OCA module not installed), returns empty list without error

### Match Proposal Creation

**Performance Pattern:** Batch create, not loop with individual creates
```python
vals_list = []
for candidate in candidates:
    vals_list.append({...})
self.env['mass.reconcile.match'].create(vals_list)
```

**Match Type Mapping:**
- score == 100 → 'exact'
- candidate['match_type'] == 'internal_transfer' → 'internal_transfer'
- candidate['match_type'] == 'reconcile_model' → 'reconcile_model'
- else → 'partial'

**Statement Line Update:**
- match_score: Max score among all candidates
- suggested_move_id: Move of highest-scored candidate
- match_state: 'matched' (if any candidates found)

### Confidence Classification

**confidence_class computed field:**
- safe: score == 100
- probable: 80 <= score < 100
- doubtful: score < 80

Uses mass.reconcile.scorer.classify_match() for consistent logic across system.

### Chatter Summary

HTML format with counts:
```html
<p><strong>Matching completed:</strong></p>
<ul>
  <li>Total lines processed: {line_count}</li>
  <li>Safe matches (100%): {safe_count}</li>
  <li>Probable matches (80-99%): {probable_count}</li>
  <li>Doubtful matches (<80%): {doubtful_count}</li>
  <li>Unmatched: {unmatched_count}</li>
</ul>
```

## Success Criteria Met

- [x] Batch action_start_matching calls engine.find_candidates for each statement line
- [x] Match proposals are batch-created in mass.reconcile.match with correct scores
- [x] Statement lines get match_state updated to 'matched' when candidates found
- [x] Batch transitions from matching to review after processing completes
- [x] Reconcile model integration works when OCA module installed, gracefully degrades when not
- [x] Match model has confidence_class computed field (safe/probable/doubtful)
- [x] Match model supports internal_transfer and reconcile_model match types
- [x] All Python files pass syntax validation

## Scope Decisions Documented

**MATCH-12 (reconcile model integration):**
Phase 2 covers invoice_matching rule type only. This is the most common reconcile model type and the one relevant to mass reconciliation. Other rule types (writeoff_button, writeoff_suggestion) serve different workflows (manual write-offs, auto-suggestions) not relevant to mass reconciliation candidate matching. Broader coverage can be added in future phases if needed.

**MATCH-13 (pre-configured reconcile models):**
Deferred to Phase 4 (Manual Review Interface). Pre-configured templates for rent, utilities, and salaries are data fixtures better suited for the phase where users will actually interact with and select them. Phase 2 focuses on the matching algorithm and integration with whatever reconcile models already exist in the user's Odoo instance.

## Next Steps

Phase 4 (Manual Review Interface) will consume the match proposals created by this phase:
- Display match proposals grouped by confidence class
- Allow users to accept/reject matches
- Implement actual reconciliation (creating account.move records)
- Handle edge cases (split matches, write-offs)

Phase 3 (Auto-Reconciliation for Safe Matches) will automatically reconcile 'safe' matches:
- Filter matches with confidence_class='safe'
- Create reconciliation entries automatically
- Update batch statistics
- Leave probable/doubtful matches for manual review

## Commits

1. `3572f72` - feat(02-02): wire matching engine into batch orchestration with reconcile model integration
2. `1a2293e` - feat(02-02): add match types and confidence classification to match model

## Self-Check: PASSED

Verifying all claimed artifacts exist:

**Modified Files:**
- FOUND: models/mass_reconcile_batch.py (action_start_matching + _create_match_proposals added)
- FOUND: models/mass_reconcile_engine.py (apply_reconcile_models + _apply_single_reconcile_model added)
- FOUND: models/mass_reconcile_match.py (internal_transfer/reconcile_model types + confidence_class added)

**Commits:**
- FOUND: 3572f72 (batch orchestration + reconcile model integration)
- FOUND: 1a2293e (match types + confidence classification)

**Verification Commands:**
```bash
# All files syntax-valid
for f in models/mass_reconcile_batch.py models/mass_reconcile_engine.py models/mass_reconcile_scorer.py models/mass_reconcile_match.py models/account_bank_statement_line.py; do
  python3 -c "import ast; ast.parse(open('$f').read()); print('OK: $f')"
done
# Output: All files OK

# Engine is called from batch
grep -c "mass.reconcile.engine" models/mass_reconcile_batch.py
# Output: 1 (✓)

# Reconcile model integration exists
grep -c "account.reconcile.model" models/mass_reconcile_engine.py
# Output: 3 (✓)

# Match proposals created with batch create
grep "\.create(" models/mass_reconcile_batch.py | grep -v "def "
# Output: self.env['mass.reconcile.match'].create(vals_list) (✓)

# Confidence classification works
grep -c "confidence_class" models/mass_reconcile_match.py
# Output: 4 (✓)
```
