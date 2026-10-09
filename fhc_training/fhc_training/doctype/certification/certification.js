frappe.ui.form.on("Certification", {
	setup(frm) {
		// Only completed sessions can be linked.
		frm.set_query("training_session", () => ({ filters: { workflow_state: "Completed" } }));
	},

	refresh(frm) {
		if (frm.is_new()) return;

		const colors = { Active: "green", Expired: "red", Revoked: "gray" };
		frm.dashboard.add_indicator(__(frm.doc.status), colors[frm.doc.status]);

		if (frm.doc.expiry_date && frm.doc.status === "Active") {
			const days = frappe.datetime.get_diff(frm.doc.expiry_date, frappe.datetime.get_today());
			frm.dashboard.add_indicator(__("Expires in {0} day(s)", [days]), days <= 30 ? "orange" : "blue");
		}

		if (frm.doc.status === "Active" && frappe.user.has_role("Training Manager")) {
			frm.add_custom_button(__("Revoke"), () => {
				frappe.prompt(
					[{ fieldname: "reason", label: __("Reason"), fieldtype: "Small Text", reqd: 1 }],
					(values) => {
						frm.call({ doc: frm.doc, method: "revoke", args: { reason: values.reason } }).then(() =>
							frm.reload_doc()
						);
					},
					__("Revoke Certification"),
					__("Revoke")
				);
			});
		}
	},
});
