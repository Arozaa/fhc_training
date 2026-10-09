import frappe
from frappe import _
from frappe.utils import add_days, date_diff, today


def execute(filters=None):
    filters = frappe._dict(filters or {})
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": _("Certificate"), "fieldname": "name", "fieldtype": "Link", "options": "Certification", "width": 160},
        {"label": _("Participant ID"), "fieldname": "participant_id", "fieldtype": "Data", "width": 110},
        {"label": _("Participant"), "fieldname": "participant_name", "fieldtype": "Data", "width": 160},
        {"label": _("Course"), "fieldname": "course", "fieldtype": "Link", "options": "Training Course", "width": 150},
        {"label": _("Issue Date"), "fieldname": "issue_date", "fieldtype": "Date", "width": 100},
        {"label": _("Expiry Date"), "fieldname": "expiry_date", "fieldtype": "Date", "width": 100},
        {"label": _("Days Remaining"), "fieldname": "days_remaining", "fieldtype": "Int", "width": 120},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 90},
    ]


def get_data(filters):
    conditions = {}
    if filters.get("course"):
        conditions["course"] = filters.course
    if filters.get("status"):
        conditions["status"] = filters.status
    if filters.get("expiring_within_days"):
        conditions["expiry_date"] = ["between", [today(), add_days(today(), int(filters.expiring_within_days))]]

    rows = frappe.get_all(
        "Certification",
        filters=conditions,
        fields=["name", "participant_id", "participant_name", "course", "issue_date", "expiry_date", "status"],
        order_by="expiry_date asc",
    )
    for row in rows:
        row["days_remaining"] = date_diff(row.expiry_date, today()) if row.expiry_date else None
    return rows
