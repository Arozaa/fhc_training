import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, add_months, today

from fhc_training.fhc_training.doctype.training_session.test_training_session import (
    make_course,
    make_session,
    make_trainer,
)
from fhc_training.tasks import mark_expired_certifications


class TestCertification(FrappeTestCase):
    def setUp(self):
        self.course = make_course(validity_months=6)
        self.session = make_session(self.course, make_trainer())

    def _cert(self, **kw):
        data = {
            "doctype": "Certification",
            "participant_id": "E100",
            "participant_name": "Test Person",
            "course": self.course.name,
            "training_session": self.session.name,
            "issue_date": today(),
        }
        data.update(kw)
        return frappe.get_doc(data)

    def test_expiry_calculated_from_course_validity(self):
        cert = self._cert().insert()
        self.assertEqual(str(cert.expiry_date), str(add_months(today(), 6)))

    def test_duplicate_certificate_blocked(self):
        self._cert().insert()
        with self.assertRaises(frappe.ValidationError):
            self._cert().insert()

    def test_expiry_before_issue_blocked(self):
        with self.assertRaises(frappe.ValidationError):
            self._cert(expiry_date=add_days(today(), -1)).insert()

    def test_revoke_requires_reason_and_sets_status(self):
        cert = self._cert().insert()
        cert.revoke("Issued in error")
        self.assertEqual(cert.status, "Revoked")
        with self.assertRaises(frappe.ValidationError):
            cert.revoke("again")  # already revoked

    def test_scheduler_marks_expired(self):
        cert = self._cert().insert()
        frappe.db.set_value("Certification", cert.name, "expiry_date", add_days(today(), -1))
        mark_expired_certifications()
        self.assertEqual(frappe.db.get_value("Certification", cert.name, "status"), "Expired")
