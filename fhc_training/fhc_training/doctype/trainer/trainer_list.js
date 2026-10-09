frappe.listview_settings["Trainer"] = {
	add_fields: ["status"],
	get_indicator(doc) {
		return doc.status === "Active"
			? [__("Active"), "green", "status,=,Active"]
			: [__("Inactive"), "gray", "status,=,Inactive"];
	},
};
