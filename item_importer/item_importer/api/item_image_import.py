import os
import csv
import zipfile
import tempfile

import frappe
from frappe.utils.file_manager import get_file_path, save_file
from openpyxl import load_workbook


@frappe.whitelist()
def attach_images_from_data_import(data_import_name):
    data_import = frappe.get_doc("Data Import", data_import_name)

    if data_import.reference_doctype != "Item":
        frappe.throw("This works only for Item Data Import")

    if not data_import.import_file:
        frappe.throw("Please attach Excel/CSV file")

    if not data_import.custom_image_zip_file:
        frappe.throw("Please attach Image ZIP file")

    if not data_import.custom_image_match_by:
        frappe.throw("Please select Image Match By")

    import_file_path = get_file_path(data_import.import_file)
    zip_file_path = get_file_path(data_import.custom_image_zip_file)

    rows = read_import_file(import_file_path)

    image_folder = extract_zip_file(zip_file_path)
    image_map = get_image_map(image_folder)

    total = 0
    success = 0
    failed = 0
    logs = []

    match_by = data_import.custom_image_match_by

    for row in rows:
        total += 1

        try:
            match_value = row.get(match_by)

            if not match_value:
                failed += 1
                logs.append(f"Row {total}: {match_by} missing")
                continue

            item = get_item(match_by, match_value)

            if not item:
                failed += 1
                logs.append(f"Row {total}: Item not found for {match_value}")
                continue

            image_key = normalize(match_value)

            if image_key not in image_map:
                failed += 1
                logs.append(f"{item.name}: Image not found for {match_value}")
                continue

            image_path = image_map[image_key]

            with open(image_path, "rb") as f:
                content = f.read()

            saved_file = save_file(
                fname=os.path.basename(image_path),
                content=content,
                dt="Item",
                dn=item.name,
                is_private=0
            )

            frappe.db.set_value("Item", item.name, "image", saved_file.file_url)

            success += 1
            logs.append(f"{item.name}: Image attached successfully")

        except Exception as e:
            failed += 1
            logs.append(f"Row {total}: Failed - {str(e)}")

    log_text = (
        f"Total Rows: {total}\n"
        f"Success: {success}\n"
        f"Failed: {failed}\n\n"
        + "\n".join(logs)
    )

    data_import.db_set("custom_image_import_log", log_text)
    frappe.db.commit()

    return {
        "total": total,
        "success": success,
        "failed": failed,
        "logs": logs
    }


def read_import_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".csv":
        return read_csv(file_path)

    if ext in [".xlsx", ".xlsm"]:
        return read_excel(file_path)

    frappe.throw("Only CSV or XLSX file is supported")


def read_csv(file_path):
    rows = []

    with open(file_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            clean_row = {}

            for key, value in row.items():
                if key:
                    clean_row[key.strip()] = str(value).strip() if value else ""

            if any(clean_row.values()):
                rows.append(clean_row)

    return rows


def read_excel(file_path):
    workbook = load_workbook(file_path)
    sheet = workbook.active

    headers = []
    rows = []

    for cell in sheet[1]:
        headers.append(str(cell.value).strip() if cell.value else "")

    for row in sheet.iter_rows(min_row=2, values_only=True):
        row_data = {}

        for index, value in enumerate(row):
            if index < len(headers):
                fieldname = headers[index]
                row_data[fieldname] = str(value).strip() if value else ""

        if any(row_data.values()):
            rows.append(row_data)

    return rows


def extract_zip_file(file_path):
    if not zipfile.is_zipfile(file_path):
        frappe.throw("Uploaded file is not a valid ZIP file")

    extract_folder = tempfile.mkdtemp()

    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall(extract_folder)

    return extract_folder


def get_image_map(folder):
    image_map = {}

    allowed_extensions = [".png", ".jpg", ".jpeg", ".webp"]

    for root, dirs, files in os.walk(folder):
        for file_name in files:
            name_without_ext, ext = os.path.splitext(file_name)

            if ext.lower() not in allowed_extensions:
                continue

            key = normalize(name_without_ext)
            image_map[key] = os.path.join(root, file_name)

    return image_map


def get_item(match_by, match_value):
    if match_by == "item_code":
        filters = {"item_code": match_value}

    elif match_by == "item_name":
        filters = {"item_name": match_value}

    elif match_by == "custom_image_name":
        filters = {"custom_image_name": match_value}

    else:
        frappe.throw("Invalid Image Match By")

    return frappe.db.get_value(
        "Item",
        filters,
        ["name", "item_code", "item_name", "image"],
        as_dict=True
    )


def normalize(value):
    value = str(value).strip().lower()

    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        if value.endswith(ext):
            value = value[:-len(ext)]

    return (
        value
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )