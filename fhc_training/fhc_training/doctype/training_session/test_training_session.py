import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, add_months, today

from fhc_training.fhc_training.doctype.training_session.training_session import (
    get_permission_query_conditions,
    issue_certificates,
)


def make_course(**kw):
    return frappe.get_doc(
        {
            "doctype": "Training Course",
            "course_name": kw.get("course_name") or f"Test Course {frappe.generate_hash(length=6)}",
            "category": "Technical",
            "duration_hours": 8,
            "passing_score": 60,
            "validity_months": kw.get("validity_months", 12),
            "is_active": kw.get("is_active", 1),
        }
    ).insert()


def make_trainer(user=None, status="Active"):
    return frappe.get_doc(
        {
            "doctype": "Trainer",
            "trainer_name": f"Trainer {frappe.generate_hash(length=5)}",
            "status": status,
            "user": user,
        }
    ).insert()


def make_session(course, trainer, start=None, end=None, participants=None, insert=True, **kw):
    doc = frappe.get_doc(
        {
            "doctype": "Training Session",
            "course": course.name,
            "trainer": trainer.name,
            "start_date": start or add_days(today(), 5),
            "end_date": end or add_days(today(), 6),
            "max_participants": kw.get("max_participants", 20),
            "participants": participants
            if participants is not None
            else [{"participant_id": "E001", "participant_name": "Abebe", "attendance": "Present", "score": 80}],
        }
    )
    return doc.insert() if insert else doc


class TestTrainingSession(FrappeTestCase):
    def setUp(self):
        self.course = make_course()
        self.trainer = make_trainer()

    # ---- success cases
    def test_create_valid_session(self):
        s = make_session(self.course, self.trainer)
        self.assertEqual(s.workflow_state, "Draft")
        self.assertEqual(s.total_participants, 1)
        self.assertEqual(s.passing_score, 60)

    def test_results_and_certificate_issue(self):
        s = make_session(
            self.course,
            self.trainer,
            participants=[
                {"participant_id": "E001", "participant_name": "Pass One", "attendance": "Present", "score": 80},
                {"participant_id": "E002", "participant_name": "Fail One", "attendance": "Present", "score": 40},
                {"participant_id": "E003", "participant_name": "Absent One", "attendance": "Absent"},
            ],
        )
        # Simulate a session that has finished and been marked Completed.
        frappe.db.set_value(
            "Training Session",
            s.name,
            {"start_date": add_days(today(), -3), "end_date": add_days(today(), -1), "workflow_state": "Completed"},
        )
        s.reload()
        s.save()
        self.assertEqual([r.result for r in s.participants], ["Pass", "Fail", ""])
        self.assertEqual(s.passed_count, 1)

        created = issue_certificates(s.name)
        self.assertEqual(len(created), 1)
        cert = frappe.get_doc("Certification", created[0])
        self.assertEqual(str(cert.expiry_date), str(add_months(s.end_date, 12)))
        # Running it again must not create duplicates.
        self.assertEqual(issue_certificates(s.name), [])

    # ---- error cases
    def test_end_before_start_fails(self):
        with self.assertRaises(frappe.ValidationError):
            make_session(self.course, self.trainer, start=add_days(today(), 5), end=add_days(today(), 3))

    def test_past_start_date_fails(self):
        with self.assertRaises(frappe.ValidationError):
            make_session(self.course, self.trainer, start=add_days(today(), -2), end=add_days(today(), -1))

    def test_too_many_participants_fails(self):
        rows = [{"participant_id": f"E{i}", "participant_name": f"P{i}"} for i in range(3)]
        with self.assertRaises(frappe.ValidationError):
            make_session(self.course, self.trainer, participants=rows, max_participants=2)

    def test_capacity_above_policy_limit_fails(self):
        with self.assertRaises(frappe.ValidationError):
            make_session(self.course, self.trainer, max_participants=31)    
            
    def test_duplicate_participant_fails(self):
        rows = [
            {"participant_id": "E001", "participant_name": "A"},
            {"participant_id": "e001", "participant_name": "A again"},
        ]
        with self.assertRaises(frappe.ValidationError):
            make_session(self.course, self.trainer, participants=rows)

    def test_inactive_course_fails(self):
        inactive = make_course(is_active=0)
        with self.assertRaises(frappe.ValidationError):
            make_session(inactive, self.trainer)

    def test_inactive_trainer_fails(self):
        with self.assertRaises(frappe.ValidationError):
            make_session(self.course, make_trainer(status="Inactive"))

    def test_trainer_double_booking_fails(self):
        first = make_session(self.course, self.trainer)
        frappe.db.set_value("Training Session", first.name, "workflow_state", "Approved")
        with self.assertRaises(frappe.ValidationError):
            make_session(self.course, self.trainer)  # same dates, same trainer

    def test_cannot_complete_before_end_date(self):
        s = make_session(self.course, self.trainer)
        s.workflow_state = "Completed"
        with self.assertRaises(frappe.ValidationError):
            s.save()

    def test_submit_for_approval_needs_participants(self):
        s = make_session(self.course, self.trainer, participants=[])
        s.workflow_state = "Pending Approval"
        with self.assertRaises(frappe.ValidationError):
            s.save()

    # ---- permissions
    def test_trainer_sees_only_own_sessions(self):
        email = "trainer.test@example.com"
        if not frappe.db.exists("User", email):
            frappe.get_doc(
                {"doctype": "User", "email": email, "first_name": "Trainer", "send_welcome_email": 0,
                 "roles": [{"role": "Trainer"}]}
            ).insert()
        mine = make_trainer(user=email)
        own = make_session(self.course, mine)
        other = make_session(self.course, self.trainer, start=add_days(today(), 20), end=add_days(today(), 21))

        frappe.set_user(email)
        try:
            visible = frappe.get_list("Training Session", pluck="name")
            self.assertIn(own.name, visible)
            self.assertNotIn(other.name, visible)
            self.assertFalse(frappe.has_permission("Training Session", doc=other, ptype="read"))
        finally:
            frappe.set_user("Administrator")

    def test_staff_has_no_row_filter(self):
        self.assertEqual(get_permission_query_conditions("Administrator"), "")
