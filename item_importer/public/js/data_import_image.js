frappe.ui.form.on("Data Import", {
    refresh: function (frm) {
        if (frm.doc.reference_doctype !== "Item") {
            return;
        }

        if (frm.is_new()) {
            return;
        }

        frm.remove_custom_button("Attach Item Images");

        frm.add_custom_button("Attach Item Images", function () {
            frappe.call({
                method: "item_importer.item_importer.api.item_image_import.attach_images_from_data_import",
                args: {
                    data_import_name: frm.doc.name
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.msgprint(
                            "Total: " + r.message.total +
                            "<br>Success: " + r.message.success +
                            "<br>Failed: " + r.message.failed
                        );

                        frm.reload_doc();
                    }
                }
            });
        });
    }
});