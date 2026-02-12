"""Tests for matching engine and scorer."""

from datetime import datetime, timedelta
from odoo.tests.common import TransactionCase
from odoo.tools import float_compare


class TestMatchingEngine(TransactionCase):
    """Test cases for mass.reconcile.engine and mass.reconcile.scorer."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        super().setUpClass()

        # Create test company
        cls.company = cls.env['res.company'].create({
            'name': 'Test Company',
        })

        # Create test currency
        cls.currency = cls.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        if not cls.currency:
            cls.currency = cls.env['res.currency'].create({
                'name': 'USD',
                'symbol': '$',
                'rounding': 0.01,
            })

        # Create test partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
            'company_id': cls.company.id,
        })

        # Create bank journals
        cls.bank_journal = cls.env['account.journal'].create({
            'name': 'Bank Journal 1',
            'code': 'BNK1',
            'type': 'bank',
            'company_id': cls.company.id,
            'currency_id': cls.currency.id,
        })

        cls.bank_journal_2 = cls.env['account.journal'].create({
            'name': 'Bank Journal 2',
            'code': 'BNK2',
            'type': 'bank',
            'company_id': cls.company.id,
            'currency_id': cls.currency.id,
        })

        # Create reconcilable account
        cls.account_receivable = cls.env['account.account'].create({
            'name': 'Test Receivable',
            'code': 'TEST_AR',
            'account_type': 'asset_receivable',
            'reconcile': True,
            'company_id': cls.company.id,
        })

        cls.account_bank = cls.env['account.account'].create({
            'name': 'Test Bank',
            'code': 'TEST_BNK',
            'account_type': 'asset_cash',
            'reconcile': True,
            'company_id': cls.company.id,
        })

        # Create test batch
        cls.batch = cls.env['mass.reconcile.batch'].create({
            'name': 'Test Batch',
            'company_id': cls.company.id,
            'journal_id': cls.bank_journal.id,
        })

        # Create bank statement
        cls.statement = cls.env['account.bank.statement'].create({
            'name': 'Test Statement',
            'journal_id': cls.bank_journal.id,
            'date': datetime.now().date(),
        })

        # Reference date for tests
        cls.test_date = datetime.now().date()

        # Initialize engine and scorer
        cls.engine = cls.env['mass.reconcile.engine']
        cls.scorer = cls.env['mass.reconcile.scorer']

    def _create_posted_move_line(self, amount, partner=None, payment_ref=None,
                                   date=None, account=None, journal=None):
        """Helper to create a posted move line."""
        if date is None:
            date = self.test_date
        if account is None:
            account = self.account_receivable
        if journal is None:
            journal = self.bank_journal

        move = self.env['account.move'].create({
            'journal_id': journal.id,
            'date': date,
            'state': 'draft',
            'move_type': 'entry',
            'company_id': self.company.id,
            'line_ids': [
                (0, 0, {
                    'account_id': account.id,
                    'partner_id': partner.id if partner else False,
                    'payment_ref': payment_ref,
                    'debit': amount if amount > 0 else 0,
                    'credit': -amount if amount < 0 else 0,
                }),
                (0, 0, {
                    'account_id': self.account_bank.id,
                    'debit': -amount if amount < 0 else 0,
                    'credit': amount if amount > 0 else 0,
                }),
            ],
        })
        move.action_post()
        # Return the reconcilable line
        return move.line_ids.filtered(lambda l: l.account_id.reconcile)

    def _create_statement_line(self, amount, partner=None, payment_ref=None, date=None):
        """Helper to create a bank statement line."""
        if date is None:
            date = self.test_date

        return self.env['account.bank.statement.line'].create({
            'statement_id': self.statement.id,
            'payment_ref': payment_ref or 'Test payment',
            'partner_id': partner.id if partner else False,
            'amount': amount,
            'date': date,
            'batch_id': self.batch.id,
        })

    def test_exact_amount_match(self):
        """Test that engine finds move line with exact matching amount."""
        # Create statement line with 1000.00
        st_line = self._create_statement_line(1000.00)

        # Create matching move line
        move_line = self._create_posted_move_line(1000.00)

        # Find candidates
        candidates = self.engine.find_candidates(st_line)

        # Verify candidate found
        self.assertTrue(len(candidates) > 0, "Should find at least one candidate")
        candidate_ids = [c['move_line_id'] for c in candidates]
        self.assertIn(move_line.id, candidate_ids, "Should find exact match candidate")

    def test_amount_mismatch(self):
        """Test that engine returns empty when no matching amount."""
        # Create statement line with 1000.00
        st_line = self._create_statement_line(1000.00)

        # Create move line with different amount
        self._create_posted_move_line(2000.00)

        # Find candidates
        candidates = self.engine.find_candidates(st_line)

        # Verify no candidates
        self.assertEqual(len(candidates), 0, "Should not find candidates with different amount")

    def test_float_precision(self):
        """Test that float_compare handles precision correctly (0.10 + 0.20 = 0.30)."""
        # Create statement line with 0.30
        st_line = self._create_statement_line(0.30)

        # Create move line with 0.30 (simulating float precision issue)
        move_line = self._create_posted_move_line(0.10 + 0.20)

        # Find candidates
        candidates = self.engine.find_candidates(st_line)

        # Verify candidate found using float_compare
        self.assertTrue(len(candidates) > 0, "Should find candidate despite float precision")
        candidate_ids = [c['move_line_id'] for c in candidates]
        self.assertIn(move_line.id, candidate_ids, "Should handle float precision correctly")

    def test_partner_filter(self):
        """Test that engine filters by partner when partner is set."""
        # Create statement line with partner
        st_line = self._create_statement_line(1000.00, partner=self.partner)

        # Create move line with matching partner
        matching_line = self._create_posted_move_line(1000.00, partner=self.partner)

        # Create move line with different partner
        other_partner = self.env['res.partner'].create({
            'name': 'Other Partner',
            'company_id': self.company.id,
        })
        non_matching_line = self._create_posted_move_line(1000.00, partner=other_partner)

        # Find candidates
        candidates = self.engine.find_candidates(st_line)

        # Verify only matching partner found
        candidate_ids = [c['move_line_id'] for c in candidates]
        self.assertIn(matching_line.id, candidate_ids, "Should find matching partner")
        self.assertNotIn(non_matching_line.id, candidate_ids, "Should not find other partner")

    def test_no_partner_wider_search(self):
        """Test that engine searches all partners when no partner set."""
        # Create statement line without partner
        st_line = self._create_statement_line(1000.00, partner=None)

        # Create move lines with different partners
        line1 = self._create_posted_move_line(1000.00, partner=self.partner)

        other_partner = self.env['res.partner'].create({
            'name': 'Other Partner',
            'company_id': self.company.id,
        })
        line2 = self._create_posted_move_line(1000.00, partner=other_partner)

        # Find candidates
        candidates = self.engine.find_candidates(st_line)

        # Verify both partners found
        candidate_ids = [c['move_line_id'] for c in candidates]
        self.assertIn(line1.id, candidate_ids, "Should find first partner")
        self.assertIn(line2.id, candidate_ids, "Should find second partner")

    def test_date_range_filter(self):
        """Test that engine excludes move lines outside date range."""
        st_line = self._create_statement_line(1000.00, date=self.test_date)

        # Create move line within range (same day)
        within_range = self._create_posted_move_line(1000.00, date=self.test_date)

        # Create move line outside range (60 days away, default range is 30)
        outside_range = self._create_posted_move_line(
            1000.00,
            date=self.test_date + timedelta(days=60)
        )

        # Find candidates
        candidates = self.engine.find_candidates(st_line)

        # Verify only within range found
        candidate_ids = [c['move_line_id'] for c in candidates]
        self.assertIn(within_range.id, candidate_ids, "Should find move within date range")
        self.assertNotIn(outside_range.id, candidate_ids, "Should exclude move outside date range")

    def test_reference_exact_match(self):
        """Test that exact payment_ref match scores 100 for reference factor."""
        st_line = self._create_statement_line(1000.00, payment_ref='INV-12345')
        move_line = self._create_posted_move_line(1000.00, payment_ref='INV-12345')

        # Calculate score
        score = self.scorer.calculate_score(st_line, move_line)

        # Verify reference contributes full 20 points (20% weight)
        # With exact amount (50%) + exact reference (20%) = at least 70
        self.assertGreaterEqual(score, 70.0, "Exact reference should contribute to score")

    def test_reference_substring_match(self):
        """Test that partial payment_ref match scores 75 for reference factor."""
        st_line = self._create_statement_line(1000.00, payment_ref='Payment for INV-12345')
        move_line = self._create_posted_move_line(1000.00, payment_ref='INV-12345')

        # Calculate score
        score = self.scorer.calculate_score(st_line, move_line)

        # Verify substring match contributes partial points
        # Should be less than exact match but more than no match
        self.assertGreater(score, 50.0, "Substring reference should contribute to score")

    def test_already_reconciled_excluded(self):
        """Test that move lines with full_reconcile_id are excluded."""
        st_line = self._create_statement_line(1000.00)

        # Create move line and reconcile it
        move_line = self._create_posted_move_line(1000.00)

        # Create a full reconcile record
        full_reconcile = self.env['account.full.reconcile'].create({
            'name': 'Test Reconcile',
        })
        move_line.write({'full_reconcile_id': full_reconcile.id})

        # Find candidates
        candidates = self.engine.find_candidates(st_line)

        # Verify reconciled line not in candidates
        candidate_ids = [c['move_line_id'] for c in candidates]
        self.assertNotIn(move_line.id, candidate_ids, "Should exclude already reconciled lines")

    def test_draft_move_excluded(self):
        """Test that moves in draft state are excluded."""
        st_line = self._create_statement_line(1000.00)

        # Create draft move (don't post it)
        draft_move = self.env['account.move'].create({
            'journal_id': self.bank_journal.id,
            'date': self.test_date,
            'state': 'draft',
            'move_type': 'entry',
            'company_id': self.company.id,
            'line_ids': [
                (0, 0, {
                    'account_id': self.account_receivable.id,
                    'debit': 1000.00,
                    'credit': 0,
                }),
                (0, 0, {
                    'account_id': self.account_bank.id,
                    'debit': 0,
                    'credit': 1000.00,
                }),
            ],
        })
        draft_line = draft_move.line_ids.filtered(lambda l: l.account_id.reconcile)

        # Find candidates
        candidates = self.engine.find_candidates(st_line)

        # Verify draft line not in candidates
        candidate_ids = [c['move_line_id'] for c in candidates]
        self.assertNotIn(draft_line.id, candidate_ids, "Should exclude draft move lines")

    def test_internal_transfer_detection(self):
        """Test that engine detects internal transfers between bank accounts."""
        # Create statement line in bank journal 1 (incoming)
        st_line = self._create_statement_line(1000.00, date=self.test_date)

        # Create opposite move in bank journal 2 (outgoing transfer)
        transfer_line = self._create_posted_move_line(
            -1000.00,  # Opposite amount
            date=self.test_date,
            journal=self.bank_journal_2
        )

        # Find candidates
        candidates = self.engine.find_candidates(st_line)

        # Verify internal transfer detected
        transfer_candidates = [c for c in candidates if c.get('match_type') == 'internal_transfer']
        self.assertTrue(len(transfer_candidates) > 0, "Should detect internal transfer")

    def test_score_safe_classification(self):
        """Test that score 100 is classified as 'safe'."""
        classification = self.scorer.classify_match(100.0)
        self.assertEqual(classification, 'safe', "Score 100 should be 'safe'")

    def test_score_probable_classification(self):
        """Test that score 85 is classified as 'probable'."""
        classification = self.scorer.classify_match(85.0)
        self.assertEqual(classification, 'probable', "Score 85 should be 'probable'")

    def test_score_doubtful_classification(self):
        """Test that score 60 is classified as 'doubtful'."""
        classification = self.scorer.classify_match(60.0)
        self.assertEqual(classification, 'doubtful', "Score 60 should be 'doubtful'")

    def test_weighted_score_calculation(self):
        """Test that weighted score calculation uses correct weights."""
        # Create perfect match: same amount, partner, reference, date
        st_line = self._create_statement_line(
            1000.00,
            partner=self.partner,
            payment_ref='INV-12345',
            date=self.test_date
        )
        move_line = self._create_posted_move_line(
            1000.00,
            partner=self.partner,
            payment_ref='INV-12345',
            date=self.test_date
        )

        # Calculate score
        score = self.scorer.calculate_score(st_line, move_line)

        # Verify perfect match = 100
        self.assertEqual(score, 100.0, "Perfect match should score 100")

        # Test partial match (amount + date only, no partner or reference)
        st_line2 = self._create_statement_line(500.00, date=self.test_date)
        move_line2 = self._create_posted_move_line(500.00, date=self.test_date)

        score2 = self.scorer.calculate_score(st_line2, move_line2)

        # Amount (50%) + Date (5%) = 55% minimum
        self.assertGreaterEqual(score2, 55.0, "Amount + date should score at least 55")
        self.assertLess(score2, 100.0, "Partial match should score less than 100")
