app_name = "fhc_training"
app_title = "FHC Training"
app_publisher = "FHC"
app_description = "Training and Certification Management System"
app_email = "candidate@example.com"
app_license = "mit"

# ---------------------------------------------------------------------------
# Fixtures: configuration that lives in the DATABASE (roles, workflow) but must
# travel with the app so it installs on any other site (requirement 13).
# Order matters: Role / Workflow State / Action Master must exist before Workflow.
# ---------------------------------------------------------------------------
fixtures = [
    {"dt": "Role", "filters": [["name", "in", ["Training Manager", "Training Officer", "Trainer"]]]},
    {"dt": "Workflow State", "filters": [["name", "in", ["Draft", "Pending Approval", "Approved", "Rejected", "Completed", "Cancelled"]]]},
    {"dt": "Workflow Action Master", "filters": [["name", "in", ["Submit for Approval", "Approve", "Reject", "Revise", "Complete", "Cancel Session"]]]},
    {"dt": "Workflow", "filters": [["name", "in", ["Training Session Approval"]]]},
]

# Row-level security: a Trainer only sees sessions assigned to them.
permission_query_conditions = {
    "Training Session": "fhc_training.fhc_training.doctype.training_session.training_session.get_permission_query_conditions",
}
has_permission = {
    "Training Session": "fhc_training.fhc_training.doctype.training_session.training_session.has_permission",
}

# Nightly job: flip Active certificates to Expired once their expiry date passes.
scheduler_events = {
    "daily": ["fhc_training.tasks.mark_expired_certifications"],
}
