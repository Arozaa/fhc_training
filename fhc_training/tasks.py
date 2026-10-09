import frappe
from frappe.utils import today


def mark_expired_certifications():
    """Scheduled daily: mark Active certifications whose expiry date has passed as Expired."""
    names = frappe.get_all(
        "Certification",
        filters={"status": "Active", "expiry_date": ["<", today()]},
        pluck="name",
    )
    for name in names:
        frappe.db.set_value("Certification", name, "status", "Expired")
    return len(names)
