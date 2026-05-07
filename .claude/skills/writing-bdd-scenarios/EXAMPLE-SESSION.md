# Example Session — Invoice Matching (ETL Service)

Compressed walkthrough showing all phases. This is how the AI guides the session.

---

## DETECT

**AI:** Are we adding a new feature, modifying existing behavior, or deprecating something?
**Team:** New feature — we need invoice matching for our I2P system.

## ANALYZE

**AI:** I've read the existing scenarios in `services/invoices/features/`. Currently there
are scenarios for invoice ingestion and validation. No matching scenarios exist yet.

## DISCOVER

**AI:** What triggers the matching process?
- A) Batch job on a schedule
- B) On invoice arrival
- C) Manual trigger by a user

**Team:** A — nightly batch job.

**AI:** What does "matching" mean here? What's being matched to what?
**Team:** Invoices matched to purchase orders by PO number and amount (within 5% tolerance).

**AI:** What happens to unmatched invoices?
**Team:** Flagged for manual review by the AP clerk.

**AI:** Are there any constraints — e.g., an invoice can match multiple POs, or strictly one-to-one?
**Team:** One-to-one only.

## DRAFT ROUND 1

**AI proposes:**

```gherkin
Feature: Invoice matching

  The nightly matching job pairs incoming invoices with purchase orders.
  Matched invoices proceed to payment. Unmatched invoices are flagged for review.

  Scenario: Invoice matches a purchase order exactly
    Given an invoice for $1,000 referencing PO-123
    And PO-123 exists for $1,000
    When the matching job runs
    Then the invoice is matched to PO-123

  Scenario: Invoice within tolerance matches
    Given an invoice for $1,040 referencing PO-456
    And PO-456 exists for $1,000
    When the matching job runs
    Then the invoice is matched to PO-456

  Scenario: Unmatched invoice is flagged
    Given an invoice referencing PO-789
    And PO-789 does not exist
    When the matching job runs
    Then the invoice is flagged for manual review by the AP clerk
```

**Team:** Looks good. Approved.

## DRAFT ROUND 2

**AI:** What if an invoice exceeds the 5% tolerance?
**Team:** Add it — flagged for review.

**AI:** What if two invoices reference the same PO?
**Team:** First one matches, second is flagged. Add it.

**AI:** What if the PO is already matched to another invoice?
**Team:** Same — flagged. Add it.

**AI:** What about an invoice with amount zero or negative?
**Team:** Out of scope — validation catches that upstream.

## REVIEW

**AI:** Final set: 6 scenarios. No contradictions with existing features. Language is
consistent ("flagged for manual review" used uniformly). Each scenario is self-contained.

## WRITE

**AI:** Written to `services/invoices/features/matching.feature` and
`docs/decisions-log/1746612345-invoice-matching.md`. Committed.

Requirements are captured. Implementation can proceed separately.
