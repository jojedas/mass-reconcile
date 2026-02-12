# Roadmap: Mass Bank Reconciliation

## Overview

This roadmap delivers a mass bank reconciliation module for Odoo 18.0 Community that reduces reconciliation time from hours to minutes. The journey follows dependency-driven architecture: foundation models establish data structures and ORM patterns, matching engine implements the core algorithm with confidence scoring, batch processing adds chunking and state management, and manual review interface provides the final UI layer for user approval. Each phase validates independently before the next begins, mitigating risks early.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation Models & Data Layer** - Data structures, security, and ORM patterns
- [x] **Phase 2: Matching Engine & Auto-Reconciliation** - Core matching algorithm with confidence scoring
- [ ] **Phase 3: Batch Processing & State Management** - Chunking, progress tracking, and orchestration
- [ ] **Phase 4: Manual Review Interface** - User interface for approval and correction

## Phase Details

### Phase 1: Foundation Models & Data Layer
**Goal**: Establish data structures and architectural patterns for mass reconciliation
**Depends on**: Nothing (first phase)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, DATA-07
**Success Criteria** (what must be TRUE):
  1. Mass reconciliation batch model exists with state machine (draft → matching → review → reconciled)
  2. Bank statement lines can be associated with batches and store match scores
  3. Match proposals are stored with audit trail (who suggested, when, what score)
  4. Security rules prevent unauthorized access to reconciliation data
  5. ORM queries use proper prefetching and batch patterns (no N+1 query degradation)
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md — Module scaffold + data models (batch, statement line extension, match proposal)
- [x] 01-02-PLAN.md — Security layer (access rights CSV, record rules XML, manifest update)

### Phase 2: Matching Engine & Auto-Reconciliation
**Goal**: Core matching algorithm that proposes reconciliation candidates with confidence scoring
**Depends on**: Phase 1
**Requirements**: MATCH-01, MATCH-02, MATCH-03, MATCH-04, MATCH-05, MATCH-06, MATCH-07, MATCH-08, MATCH-09, MATCH-10, MATCH-11, MATCH-12, MATCH-13
**Success Criteria** (what must be TRUE):
  1. System finds matching candidates by exact amount from account.move.line
  2. System filters candidates by partner and validates date ranges
  3. System compares payment references between statement and moves
  4. System identifies internal transfers between company bank accounts
  5. Each match has confidence score (100% exact, 80-99% probable, <80% doubtful)
  6. System uses float_compare for monetary amounts (no rounding errors)
  7. System validates moves are not already reconciled before proposing
  8. System integrates with account.reconcile.model for recurring expenses
**Plans**: 2 plans

Plans:
- [ ] 02-01-PLAN.md — Core matching engine + confidence scorer (TDD: candidate search, weighted scoring, internal transfer detection)
- [ ] 02-02-PLAN.md — Batch orchestration wiring + reconcile model integration (connect engine to batch flow, account.reconcile.model support)

### Phase 3: Batch Processing & State Management
**Goal**: Process reconciliation in 80-line chunks with progress tracking and state management
**Depends on**: Phase 2
**Requirements**: BATCH-01, BATCH-02, BATCH-03, BATCH-04, BATCH-05, BATCH-06, BATCH-07
**Success Criteria** (what must be TRUE):
  1. User can select up to 80 statement lines for batch processing by date range
  2. Batch moves through states: draft → matching → review → reconciled
  3. System shows progress indicator during processing ("42/80 processed — 85% complete")
  4. System displays matching statistics (% automatic, % manual, % unmatched)
  5. All match proposals are stored in batch for audit trail
  6. System prevents concurrent reconciliation conflicts with proper locking
**Plans**: 2 plans

Plans:
- [ ] 03-01-PLAN.md — Line loading with 80-line limit + date range selection, SELECT FOR UPDATE locking, state validation guards, reset cleanup
- [ ] 03-02-PLAN.md — Matching statistics computed fields (_read_group) + progress tracking text fields

### Phase 4: Manual Review Interface
**Goal**: User interface for reviewing, approving, and correcting match proposals
**Depends on**: Phase 3
**Requirements**: REVIEW-01, REVIEW-02, REVIEW-03, REVIEW-04, REVIEW-05, REVIEW-06, REVIEW-07, REVIEW-08, UI-01, UI-02, UI-03, UI-04, UI-05
**Success Criteria** (what must be TRUE):
  1. User can review list of proposed matches with line details, candidate, and score
  2. User can approve safe matches (score 100%) in bulk with one button
  3. User can approve or reject individual matches from tree view
  4. User can mark lines as "To Check" for later review without blocking reconciliation
  5. User can write-off small differences with configurable threshold (default $10)
  6. User sees preview of all reconciliations before applying batch
  7. User must explicitly confirm before batch reconciliation is applied
  8. User can undo reconciliations with complete cleanup
  9. System shows clear error messages when reconciliation fails
  10. Interface uses color coding: green (safe), yellow (probable), red (doubtful)
**Plans**: TBD

Plans:
- TBD (to be created during plan-phase)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation Models & Data Layer | 2/2 | Complete | 2026-02-12 |
| 2. Matching Engine & Auto-Reconciliation | 2/2 | Complete | 2026-02-12 |
| 3. Batch Processing & State Management | 0/2 | Not started | - |
| 4. Manual Review Interface | 0/TBD | Not started | - |
