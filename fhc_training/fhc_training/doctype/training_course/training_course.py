import frappe
from frappe import _
from frappe.model.document import Document


class TrainingCourse(Document):
    def validate(self):
        if self.duration_hours is not None and self.duration_hours <= 0:
            frappe.throw(_("Duration must be greater than zero."))
        if not 0 < (self.passing_score or 0) <= 100:
            frappe.throw(_("Passing Score must be between 1 and 100."))
        if (self.validity_months or 0) < 0:
            frappe.throw(_("Certificate Validity cannot be negative."))
        if self.course_code:
            self.course_code = self.course_code.strip().upper()
