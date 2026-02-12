# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned Features
- Views UI implementation (tree, form, kanban views)
- Wizard for batch creation
- Reports and analytics
- Dashboard with KPIs
- API REST endpoints
- Multi-currency support
- Performance optimizations for large datasets (>100k lines)
- Fuzzy matching algorithm
- Machine learning confidence scoring

## [1.0.0] - 2024-02-12

### Added

#### Core Features
- **Batch Processing**: Process thousands of statement lines in configurable chunks
- **Matching Engine**: Three matching types (exact amount, partner amount, invoice reference)
- **Confidence Scoring**: Weighted algorithm (amount 50%, partner 25%, reference 20%, date 5%)
- **Three-Tier Classification**: Safe (100), Probable (80-99), Doubtful (<80)
- **Dual Mode**: Auto-reconcile safe matches or manual review
- **Progress Tracking**: Real-time progress monitoring with counters

#### Models
- `mass.reconcile.batch`: Batch management with state machine
  - States: draft → processing → done
  - Chunk-based processing
  - Progress counters (total, matched, unmatched, reconciled)
  - Auto-mode configuration
- `mass.reconcile.match`: Match proposals with validation
  - States: draft → validated/rejected
  - Match type classification
  - Confidence scoring
  - Reconcile model integration
- `mass.reconcile.engine`: Matching logic (AbstractModel)
  - Exact amount matching
  - Partner + amount matching
  - Invoice reference matching
  - Reconcile model rule application
- `mass.reconcile.scorer`: Confidence calculation (AbstractModel)
  - Component-based scoring
  - Weighted aggregation
  - Classification thresholds
- `account.bank.statement.line`: Extended model
  - `match_state`: unmatched/matched/reconciled tracking
  - Batch relationship

#### Security
- Access rights for Accountant and Manager groups
- Multi-company record rules
- CSV and XML security files

#### Testing
- Comprehensive test suite for matching engine
- Confidence scoring tests
- Classification threshold validation
- Float comparison edge case tests
- Test coverage: Core matching and scoring logic

#### Development Environment
- **Docker Compose**: Odoo 18.0 + PostgreSQL 15 stack
- **Automated Setup**: `setup.sh` script
  - Docker image pulling
  - OCA repository cloning (account-reconcile, account-financial-tools)
  - Database initialization
- **Module Installation**: `install-modules.sh` script
- **Makefile**: 20+ commands for common operations
  - Container management
  - Log viewing
  - Module upgrades
  - Database operations
  - Shell access

#### Documentation
- **README.md**: Project overview and quick start
- **QUICKSTART.md**: 5-minute getting started guide
- **SETUP.md**: Detailed setup and configuration guide
- **TUTORIAL.md**: Comprehensive Spanish tutorial
  - Installation from GitHub
  - Usage examples
  - Common use cases
  - Development guide
  - Troubleshooting
  - FAQ
- **CONTRIBUTING.md**: Contribution guidelines
  - Code style guide
  - Testing requirements
  - PR workflow
  - Review process
- **DOCKER_COMMANDS.md**: Docker command reference
- **TEST_ENVIRONMENT.md**: Test data setup guide
- **INDEX.md**: Complete file index
- **CHANGELOG.md**: This file

#### Planning Artifacts (GSD)
- **PROJECT.md**: Vision, success metrics, key decisions
- **ROADMAP.md**: 4-phase implementation plan
- **REQUIREMENTS.md**: Functional and technical requirements
- **Phase Plans**: Detailed execution plans for Phases 1-3
- **Research**: Architecture patterns, features, pitfalls, stack decisions

### Technical Decisions

#### Architecture
- Built on OCA account-reconcile framework
- AbstractModel for engine and scorer (no DB tables, pure logic)
- Extension of account.bank.statement.line (vs. inheritance)
- Batch-oriented processing (vs. line-by-line)

#### Data Handling
- `float_compare()` for all monetary comparisons (precision safety)
- Computed fields use `_read_group` pattern (N+1 query prevention)
- Audit fields via ORM `_log_access` (automatic tracking)
- Batch create pattern for match proposals (single DB call)

#### Scoring & Classification
- Deterministic matching (vs. ML, for predictability and debuggability)
- Fixed reconcile model score: 90 (probable tier)
- Chunk size: 80 lines (UI responsiveness vs. performance balance)
- Three-tier classification for clear decision boundaries

#### Security
- CSV before XML in manifest (security context requirement)
- `company_ids` plural field (Odoo 18.0 multi-company pattern)
- Group-based access control (Accountant/Manager)

### Dependencies

#### Python
- Python 3.11+ (included in Odoo Docker image)
- Odoo 18.0 Community Edition

#### Odoo Modules
- `base`: Odoo base module
- `account`: Base accounting module
- `account_reconcile_oca`: OCA advanced reconciliation (from account-reconcile repo)
- `account_reconcile_model_oca`: OCA reconciliation models (from account-reconcile repo)

#### Infrastructure
- Docker 20.10+
- Docker Compose 2.0+
- PostgreSQL 15

### Performance Metrics

#### Development Velocity
- Phase 1 (Foundation): 2 plans, 3 min total (1.5 min avg)
- Phase 2 (Matching Engine): 2 plans, 4.9 min total (2.45 min avg)
- Overall: 4 plans in 0.23 hours (1.9 min avg)

#### Project Stats
- Total commits: 28
- Files created: 44
- Lines of code: ~2000 (Python)
- Test coverage: Core logic (engine, scorer)

### Known Limitations

1. **Views Not Implemented**: No UI views yet (tree, form, kanban)
   - Workaround: Use developer mode and manual record creation
   - Planned: Phase 3 implementation

2. **Single Currency**: No multi-currency support
   - Workaround: Process each currency separately
   - Planned: Future enhancement

3. **No Wizard**: Batch creation requires manual record creation
   - Workaround: Use XML-RPC or Python shell
   - Planned: Phase 3 implementation

4. **Limited Match Types**: Only 3 match types (exact, partner, invoice)
   - Workaround: Extend engine with custom matching methods
   - Planned: Fuzzy matching, partial amount matching

5. **Performance**: Not optimized for >100k lines in single batch
   - Workaround: Split into multiple smaller batches
   - Planned: Database query optimization, batch parallelization

### Migration Guide

Not applicable (initial release).

### Breaking Changes

Not applicable (initial release).

---

## Version History

- **1.0.0** (2024-02-12): Initial release

---

## Upgrade Guide

### From 0.x to 1.0.0

Not applicable (initial release).

---

## Contributors

- Juan Ojeda ([@jojedas](https://github.com/jojedas)) - Initial development
- Claude Code (Anthropic) - Development assistance

---

## Acknowledgments

- **OCA Community**: For account-reconcile framework
- **Odoo SA**: For Odoo platform
- **PostgreSQL Team**: For robust database engine

---

## Support

For questions and issues:
- GitHub Issues: https://github.com/jojedas/mass-reconcile/issues
- Documentation: [TUTORIAL.md](TUTORIAL.md), [SETUP.md](SETUP.md)
- OCA Forum: https://odoo-community.org/

---

[Unreleased]: https://github.com/jojedas/mass-reconcile/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/jojedas/mass-reconcile/releases/tag/v1.0.0
