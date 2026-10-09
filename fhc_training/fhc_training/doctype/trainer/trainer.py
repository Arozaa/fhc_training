import frappe
from frappe import _
from frappe.model.document import Document


class Trainer(Document):
    def validate(self):
        if self.user and frappe.db.exists("Trainer", {"user": self.user, "name": ["!=", self.name or ""]}):
            frappe.throw(_("User {0} is already linked to another trainer.").format(self.user))
