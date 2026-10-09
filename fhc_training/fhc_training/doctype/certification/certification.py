import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_months, getdate, today


class Certification(Document):
    def validate(self):
        self.set_expiry_date()
        self.validate_dates()
        self.validate_duplicate()
        self.update_status()

    def set_expiry_date(self):
        if self.expiry_date:
            return
        validity = frappe.db.get_value("Training Course", self.course, "validity_months") or 0
        if validity:
            self.expiry_date = add_months(self.issue_date, validity)

    def validate_dates(self):
        if self.expiry_date and getdate(self.expiry_date) < getdate(self.issue_date):
            frappe.throw(_("Expiry Date cannot be before Issue Date."))

    def validate_duplicate(self):
        existing = frappe.db.exists(
            "Certification",
            {
                "training_session": self.training_session,
                "participant_id": self.participant_id,
                "status": ["!=", "Revoked"],
                "name": ["!=", self.name or ""],
            },
        )
        if existing:
            frappe.throw(
                _("Participant {0} already holds certificate {1} for this session.").format(self.participant_id, existing)
            )

    def update_status(self):
        if self.status == "Active" and self.expiry_date and getdate(self.expiry_date) < getdate(today()):
            self.status = "Expired"

    @frappe.whitelist()
    def revoke(self, reason):
        frappe.only_for(("System Manager", "Training Manager"))
        if self.status == "Revoked":
            frappe.throw(_("This certificate is already revoked."))
        self.status = "Revoked"
        self.revoked_reason = reason
        self.save()
