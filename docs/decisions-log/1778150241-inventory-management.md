# Inventory Item Management

- **Date:** 2025-05-07
- **Type:** new

## Context

Adding basic CRUD capabilities to the inventory service for consumption by other internal services (orders, users).

## Decisions

- SKU must be unique per item — prevents duplicate tracking of the same physical product
- Quantity must be non-negative — negative stock is physically meaningless
- Lookup by ID, search by name — ID for precise lookups, name for discovery
- ID is immutable — stable references for consuming services
- Hard delete only — no soft delete; simplifies state management for in-memory service
- Cannot delete items with remaining stock — prevents accidental loss of stock tracking
- Quantity supports both absolute set and relative adjustment — relative adjustments prevent race conditions across services
- Relative adjustment cannot bring quantity below zero — maintains non-negative invariant
- Empty search returns empty list, not error — absence of results is not exceptional

## Out of Scope

- Pagination for search results
- Filtering/searching by location or SKU
- Soft delete / archival
- Concurrency control (optimistic locking, versioning)
- Audit trail of quantity changes
- Reorder thresholds / low-stock alerts

## Affected Scenarios

- `services/inventory/features/inventory_management.feature` (created)
