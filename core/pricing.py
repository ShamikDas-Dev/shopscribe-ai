from __future__ import annotations


def calculate_discount_percent(mrp: float | None, selling_price: float | None) -> float | None:
    """Calculate discount percentage. Returns None if either price is missing."""
    if mrp is None or selling_price is None:
        return None
    if mrp <= 0:
        raise ValueError("MRP must be greater than zero.")
    if selling_price <= 0:
        raise ValueError("Selling price must be greater than zero.")
    if selling_price > mrp:
        raise ValueError("Selling price cannot be greater than MRP.")
    return round(((mrp - selling_price) / mrp) * 100, 2)
