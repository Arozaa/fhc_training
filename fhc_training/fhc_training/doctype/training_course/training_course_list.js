frappe.listview_settings["Training Course"] = {
	add_fields: ["is_active"],
	get_indicator(doc) {
		return doc.is_active
			? [__("Active"), "green", "is_active,=,1"]
			: [__("Inactive"), "gray", "is_active,=,0"];
	},
};
