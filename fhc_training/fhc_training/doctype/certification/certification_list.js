frappe.listview_settings["Certification"] = {
	add_fields: ["status", "expiry_date"],
	get_indicator(doc) {
		const colors = { Active: "green", Expired: "red", Revoked: "gray" };
		return [__(doc.status), colors[doc.status] || "gray", "status,=," + doc.status];
	},
};
