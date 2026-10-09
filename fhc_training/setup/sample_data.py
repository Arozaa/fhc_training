"""Optional demo data and demo users.

    bench --site fhc.local execute fhc_training.setup.sample_data.create_sample_data
    bench --site fhc.local execute fhc_training.setup.sample_data.create_demo_users \
        --kwargs "{'password': 'choose-a-password'}"

No password is stored in the repository: you pass one on the command line.
"""
import frappe
from frappe.utils import add_days, today

DEMO_USERS = {
    "manager@fhc.test": ("Training Manager", ["Training Manager"]),
    "officer@fhc.test": ("Training Officer", ["Training Officer"]),
    "trainer@fhc.test": ("Trainer One", ["Trainer"]),
}


def create_demo_users(password):
    for email, (first_name, roles) in DEMO_USERS.items():
        if frappe.db.exists("User", email):
            continue
        frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": first_name,
                "send_welcome_email": 0,
                "new_password": password,
                "roles": [{"role": r} for r in roles],
            }
        ).insert(ignore_permissions=True)
    frappe.db.commit()
    print("Created demo users:", ", ".join(DEMO_USERS))


def create_sample_data():
    courses = [
        ("Occupational Health and Safety", "Safety", 8, 70, 12),
        ("Project Management Basics", "Management", 16, 60, 24),
        ("Construction Quality Control", "Technical", 24, 65, 0),
    ]
    course_docs = []
    for name, category, hours, score, validity in courses:
        existing = frappe.db.get_value("Training Course", {"course_name": name})
        if existing:
            course_docs.append(frappe.get_doc("Training Course", existing))
            continue
        course_docs.append(
            frappe.get_doc(
                {"doctype": "Training Course", "course_name": name, "category": category,
                 "duration_hours": hours, "passing_score": score, "validity_months": validity}
            ).insert()
        )

    trainers = []
    for name, link_user in (("Trainer One", "trainer@fhc.test"), ("Trainer Two", None)):
        existing = frappe.db.get_value("Trainer", {"trainer_name": name})
        if existing:
            trainers.append(frappe.get_doc("Trainer", existing))
            continue
        user = link_user if link_user and frappe.db.exists("User", link_user) else None
        trainers.append(frappe.get_doc({"doctype": "Trainer", "trainer_name": name, "user": user}).insert())

    frappe.get_doc(
        {
            "doctype": "Training Session",
            "course": course_docs[0].name,
            "trainer": trainers[0].name,
            "start_date": add_days(today(), 7),
            "end_date": add_days(today(), 8),
            "venue": "Head Office - Training Hall",
            "max_participants": 20,
            "participants": [
                {"participant_id": "FHC-001", "participant_name": "Abebe Kebede", "department": "Engineering"},
                {"participant_id": "FHC-002", "participant_name": "Sara Tesfaye", "department": "Finance"},
                {"participant_id": "FHC-003", "participant_name": "Dawit Alemu", "department": "Procurement"},
            ],
        }
    ).insert()
    frappe.db.commit()
    print("Sample courses, trainers and one draft session created.")
