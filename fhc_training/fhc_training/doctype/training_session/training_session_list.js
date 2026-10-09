frappe.listview_settings["Training Session"] = {
	add_fields: ["workflow_state"],
	get_indicator(doc) {
		const colors = {
			Draft: "gray",
			"Pending Approval": "orange",
			Approved: "blue",
			Completed: "green",
			Rejected: "red",
			Cancelled: "darkgrey",
		};
		return [__(doc.workflow_state), colors[doc.workflow_state] || "gray", "workflow_state,=," + doc.workflow_state];
	},
};
