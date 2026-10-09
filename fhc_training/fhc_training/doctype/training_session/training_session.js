const RESULT_STATES = ["Approved", "Completed"];

frappe.ui.form.on("Training Session", {
	setup(frm) {
		// Only active courses and active trainers can be picked.
		frm.set_query("course", () => ({ filters: { is_active: 1 } }));
		frm.set_query("trainer", () => ({ filters: { status: "Active" } }));
	},

	refresh(frm) {
		if (frm.is_new()) return;

		// Summary indicators at the top of the form.
		frm.dashboard.add_indicator(__("Participants: {0}", [frm.doc.total_participants || 0]), "blue");
		if (RESULT_STATES.includes(frm.doc.workflow_state)) {
			frm.dashboard.add_indicator(__("Passed: {0}", [frm.doc.passed_count || 0]), "green");
		}

		// "Issue Certificates" appears only for completed sessions with un-certified passers.
		const can_issue = frappe.user.has_role("Training Manager") || frappe.user.has_role("Training Officer");
		const pending = (frm.doc.participants || []).some((r) => r.result === "Pass" && !r.certificate);
		if (frm.doc.workflow_state === "Completed" && can_issue && pending) {
			frm.add_custom_button(__("Issue Certificates"), () => {
				frappe.confirm(__("Issue certificates to all participants who passed?"), () => {
					frappe.call({
						method: "fhc_training.fhc_training.doctype.training_session.training_session.issue_certificates",
						args: { session_name: frm.doc.name },
						freeze: true,
						callback(r) {
							frappe.show_alert({
								message: __("{0} certificate(s) issued", [(r.message || []).length]),
								indicator: "green",
							});
							frm.reload_doc();
						},
					});
				});
			}).addClass("btn-primary");
		}
	},

	// Keep end date consistent when the start date moves.
	start_date(frm) {
		if (frm.doc.start_date && (!frm.doc.end_date || frm.doc.end_date < frm.doc.start_date)) {
			frm.set_value("end_date", frm.doc.start_date);
		}
	},

	participants_add: update_summary,
	participants_remove: update_summary,
});

frappe.ui.form.on("Training Participant", {
	score: recalc_row,
	attendance: recalc_row,
});

function recalc_row(frm, cdt, cdn) {
	// Mirrors the server-side rule in calculate_results().
	const row = locals[cdt][cdn];
	let result = "";
	if (RESULT_STATES.includes(frm.doc.workflow_state) && row.attendance === "Present") {
		result = flt(row.score) >= flt(frm.doc.passing_score) ? "Pass" : "Fail";
	}
	frappe.model.set_value(cdt, cdn, "result", result);
	update_summary(frm);
}

function update_summary(frm) {
	const rows = frm.doc.participants || [];
	frm.set_value("total_participants", rows.length);
	frm.set_value("passed_count", rows.filter((r) => r.result === "Pass").length);
	if (frm.doc.max_participants && rows.length > frm.doc.max_participants) {
		frappe.show_alert({ message: __("Participant limit ({0}) exceeded", [frm.doc.max_participants]), indicator: "red" });
	}
}
