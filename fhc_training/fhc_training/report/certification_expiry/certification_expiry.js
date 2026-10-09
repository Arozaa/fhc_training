frappe.query_reports["Certification Expiry"] = {
	filters: [
		{ fieldname: "course", label: __("Course"), fieldtype: "Link", options: "Training Course" },
		{ fieldname: "status", label: __("Status"), fieldtype: "Select", options: "\nActive\nExpired\nRevoked", default: "Active" },
		{ fieldname: "expiring_within_days", label: __("Expiring Within (Days)"), fieldtype: "Int" },
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "days_remaining" && data && data.days_remaining !== null) {
			if (data.days_remaining < 0) value = `<span style="color:red">${value}</span>`;
			else if (data.days_remaining <= 30) value = `<span style="color:orange">${value}</span>`;
		}
		return value;
	},
};
