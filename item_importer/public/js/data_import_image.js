frappe.ui.form.on("Data Import", {
    refresh: function (frm) {
        frm.trigger("setup_image_import_fields");
    },

    reference_doctype: function (frm) {
        frm.trigger("setup_image_import_fields");
    },

    setup_image_import_fields: function (frm) {
        frm.remove_custom_button("Attach Item Images");
        frm.remove_custom_button("Attach Images");

        if (!frm.doc.reference_doctype) {
            hide_image_import_fields(frm);
            return;
        }

        frappe.call({
            method: "item_importer.item_importer.api.item_image_import.get_image_import_options",
            args: {
                reference_doctype: frm.doc.reference_doctype
            },
            callback: function (r) {

                if (!r.message || !r.message.has_image_field) {
                    hide_image_import_fields(frm);
                    return;
                }

                show_image_import_fields(frm);

                let image_fields = r.message.image_fields || [];
                let select_options = [];

                image_fields.forEach(function (field) {
                    select_options.push(field.fieldname);
                });

                frm.set_df_property(
                    "custom_matched_field",
                    "options",
                    select_options.join("\n")
                );

                frm.refresh_field("custom_matched_field");

                if (
                    !frm.doc.custom_matched_field &&
                    select_options.length
                ) {
                    frm.set_value(
                        "custom_matched_field",
                        select_options[0]
                    );
                }

                if (!frm.doc.custom_image_match_by) {
                    frm.set_value("custom_image_match_by", "name");
                }

                if (!frm.is_new()) {
                    frm.add_custom_button("Attach Images", function () {
                        frappe.call({
                            method: "item_importer.item_importer.api.item_image_import.attach_images_from_data_import",
                            args: {
                                data_import_name: frm.doc.name
                            },
                            freeze: true,
                            freeze_message: "Attaching images...",
                            callback: function (res) {
                                if (res.message) {
                                    frappe.msgprint(
                                        "<br>Total: " + res.message.total +
                                        "<br>Success: " + res.message.success +
                                        "<br>Failed: " + res.message.failed
                                    );

                                    frm.reload_doc();
                                }
                            }
                        });
                    });
                }
            }
        });
    }
});


function show_image_import_fields(frm) {
    frm.set_df_property("custom_image_zip_file", "hidden", 0);
    frm.set_df_property("custom_image_match_by", "hidden", 0);
    frm.set_df_property("custom_matched_field", "hidden", 0);
    frm.set_df_property("custom_image_import_log", "hidden", 0);

    frm.set_df_property("custom_matched_field", "read_only", 0);

    frm.set_df_property(
        "custom_image_match_by",
        "description",
        "Enter fieldname from selected Doctype. Example: name, item_code, customer_name"
    );
}


function hide_image_import_fields(frm) {
    frm.set_df_property("custom_image_zip_file", "hidden", 1);
    frm.set_df_property("custom_image_match_by", "hidden", 1);
    frm.set_df_property("custom_matched_field", "hidden", 1);
    frm.set_df_property("custom_image_import_log", "hidden", 1);

    frm.set_value("custom_image_zip_file", "");
    frm.set_value("custom_image_match_by", "");
    frm.set_value("custom_matched_field", "");
    frm.set_value("custom_image_import_log", "");
}
