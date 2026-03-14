import frappe
from frappe.model.document import Document


DEFAULT_ACCESSIBLE_DOCTYPES = [
    {"doctype_name": "Loan Application", "employee_field": "applicant", "read_only": 1, "edit_access": 0},
    {"doctype_name": "Leave Application", "employee_field": "employee", "read_only": 1, "edit_access": 0},
    {"doctype_name": "Clearance Form", "employee_field": "employee", "read_only": 1, "edit_access": 0},
    {"doctype_name": "Visit Form", "employee_field": "employee", "read_only": 0, "edit_access": 1},
    {"doctype_name": "Permission Application", "employee_field": "employee", "read_only": 0, "edit_access": 1},
]


class ManagerPermissions(Document):
    def validate(self):
        self._validate_unique_employees()
        self._validate_unique_doctypes()

    def _validate_unique_employees(self):
        seen = set()
        for row in self.employees or []:
            if row.employee in seen:
                frappe.throw(
                    frappe._("Duplicate employee {0} in Manager Employees table").format(row.employee)
                )
            seen.add(row.employee)

    def _validate_unique_doctypes(self):
        seen = set()
        for row in self.accessible_documents or []:
            if row.doctype_name in seen:
                frappe.throw(
                    frappe._("Duplicate DocType {0} in Accessible Documents table").format(
                        row.doctype_name
                    )
                )
            seen.add(row.doctype_name)

    def on_update(self):
        frappe.cache().delete_value(f"manager_permissions_{self.manager}")


def _get_manager_permissions_for_user(user):
    """Return the Manager Permissions document for the given user, or None."""
    cache_key = f"manager_permissions_{user}"
    cached = frappe.cache().get_value(cache_key)
    if cached is not None:
        return cached

    name = frappe.db.get_value("Manager Permissions", {"manager": user}, "name")
    if not name:
        frappe.cache().set_value(cache_key, False, expires_in_sec=300)
        return None

    doc = frappe.get_doc("Manager Permissions", name)
    frappe.cache().set_value(cache_key, doc, expires_in_sec=300)
    return doc


def _get_accessible_doctype_config(doc, doctype):
    """Return the accessible-documents row for the given doctype, or None."""
    for row in doc.accessible_documents or []:
        if row.doctype_name == doctype:
            return row
    return None


def get_permission_query_conditions(user, doctype=None):
    """
    Called by Frappe permission engine for each configured doctype.
    Returns an SQL fragment that restricts rows to those belonging to the
    manager's allowed employees.
    """
    if not user:
        user = frappe.session.user

    if user == "Administrator":
        return None

    mgr_doc = _get_manager_permissions_for_user(user)
    if not mgr_doc:
        return None

    doc_config = _get_accessible_doctype_config(mgr_doc, doctype) if doctype else None
    if not doc_config:
        return None

    allowed_employees = [row.employee for row in mgr_doc.employees if row.employee]
    if not allowed_employees:
        return "1=0"

    employee_field = doc_config.employee_field or "employee"
    escaped = "', '".join(frappe.db.escape(e)[1:-1] for e in allowed_employees)
    return f"`tab{doctype}`.`{employee_field}` in ('{escaped}')"


def has_permission(doc, ptype, user):
    """
    Fine-grained permission check for individual document access.
    Returns True to allow, False to deny, None to fall through to standard checks.
    """
    if not user:
        user = frappe.session.user

    if user == "Administrator":
        return True

    mgr_doc = _get_manager_permissions_for_user(user)
    if not mgr_doc:
        return None

    doc_config = _get_accessible_doctype_config(mgr_doc, doc.doctype)
    if not doc_config:
        return None

    allowed_employees = [row.employee for row in mgr_doc.employees if row.employee]
    employee_field = doc_config.employee_field or "employee"
    employee_value = doc.get(employee_field)

    if employee_value not in allowed_employees:
        return False

    if ptype == "write" and not doc_config.edit_access:
        return False

    return True


@frappe.whitelist()
def get_manager_employees(manager=None):
    """Utility API: return the list of employees accessible to the given manager (or current user)."""
    user = manager or frappe.session.user
    mgr_doc = _get_manager_permissions_for_user(user)
    if not mgr_doc:
        return []
    return [row.employee for row in mgr_doc.employees if row.employee]
