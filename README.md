# 📌 Whatsapp Saudi — v2.1

Integration with **Saudi WhatsApp providers** for **ERPNext**.  
Supports **4Whats.net**, **Rasayel**, and **Bevatel** out of the box.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](license.txt)
[![Python ≥3.10](https://img.shields.io/badge/python-%3E%3D3.10-blue)](pyproject.toml)

---

## 🔧 Installation

### Prerequisites
- **ERPNext** v13 or later (tested on v13, v14, v15).
- **Python ≥ 3.10** and **Frappe Framework**.
- `bench` CLI available on the server.

### Steps

```bash
# 1. Add the app to your bench
bench get-app https://github.com/AmirAhmed0s/whatsapp_saudi.git

# 2. Install on your site
bench --site your-site-name install-app whatsapp_saudi

# 3. Migrate and restart
bench --site your-site-name migrate
bench restart
```

> **Dependency**: `pikepdf ≥ 8.0.0` is required for PDF/A-3 generation and is installed automatically via `pyproject.toml`.

---

## ⚙️ Configuration

Open **ERPNext → Whatsapp Saudi** (single-document form) and:

1. Select your **WhatsApp Provider** from the dropdown.
2. Fill in the credentials for the selected provider tab (see sections below).
3. Enter a phone number in **To Number (for testing)** and click **Send Test Message** to verify.
4. Use **Validate Config** to check that all required fields are filled before going live.

---

## 🔌 Provider Setup

### 1️⃣ Whats.net

| Field | Description |
|-------|-------------|
| File URL | Default: `https://api.4whats.net/sendFile` |
| Message URL | Default: `https://api.4whats.net/sendMessage` |
| Token | Your Whats.net API token |
| Instance ID | Your Whats.net instance ID |

**Supported features:**
- ✅ Plain text messages
- ✅ PDF / file sending
- ✅ Incoming webhook handling

**Webhook URL** (paste in your Whats.net dashboard):
```
https://your-erpnext-site.com/api/method/whatsapp_saudi.overrides.whtatsapp_notification.receive_whatsapp_message
```

![Whats.net configuration](assets/whatsnet.png)

---

### 2️⃣ Rasayel

| Field | Description |
|-------|-------------|
| File Upload URL | Rasayel file-upload endpoint |
| Rasayel File API | GraphQL endpoint for file messages |
| Rasayel Message API | REST endpoint for template messages |
| Authorization Token | `Bearer <your-token>` |
| Channel ID | Numeric channel identifier |
| Message Template ID | Default template ID for text messages |

**Supported features:**
- ✅ Template text messages (with dynamic body variables)
- ✅ PDF / document file messages
- ✅ PDF/A-3 compliant documents (embedded XML)
- ✅ Automatic conversation closure after send

![Rasayel configuration](assets/rasayel.png)

---

### 3️⃣ Bevatel

| Field | Description |
|-------|-------------|
| Bevatel File URL | Bevatel API endpoint (e.g. `https://chat.bevatel.com/developer/api/v1/messages`) |
| Account ID | `api_account_id` from your Bevatel profile |
| Access Token | `api_access_token` from your Bevatel profile |
| Inbox ID | Target inbox identifier |
| Template Name | WhatsApp template name (e.g. `invoice_ready`) |
| Language | Template language code (e.g. `ar`, `en`) |

**Supported features:**
- ✅ Template text messages
- ✅ PDF document messages
- ✅ PDF/A-3 compliant documents

![Bevatel configuration](assets/bevatel.png)

---

## 🚀 Features — Version 2.1

### ✅ Core

| Feature | Description |
|---------|-------------|
| Multi-provider | Switch between **Whats.net**, Rasayel, and Bevatel from a single setting |
| Notification channel | `Whatsapp Saudi` channel appears in the standard Frappe **Notification** doctype |
| Dynamic recipients | Resolve phone numbers from linked Customer / Supplier / Employee / Contact / Lead records automatically |
| Role-based recipients | Send to all users who hold a specific ERPNext role |
| Async sending | All sends are enqueued in the `long` background-job queue (no UI freeze) |
| Success log | Every send/failure is recorded in **Whatsapp Saudi Success Log** with reference to the source document |
| Incoming messages | Webhook stores every inbound message in **Whatsapp Responses** |

### ✅ Document Sending

| Feature | Description |
|---------|-------------|
| PDF via Sales Invoice | *Send PDF through WhatsApp* menu item on the Sales Invoice form |
| PDF/A-3 via Sales Invoice | *Send PDF-A3 through WhatsApp* — embeds the ZATCA XML into the PDF |
| Multi-format | Choose print format, letterhead, and language from a dialog |
| Print PDF-A3 locally | *Print PDF-A3* menu item generates and opens the PDF/A-3 in the browser |

### ✅ New in v2.1

| Improvement | Description |
|-------------|-------------|
| **Message Statistics API** | `get_message_statistics` — returns Sent/Failed totals and active provider |
| **Config Validator API** | `validate_whatsapp_config` — returns missing required fields for the active provider before you go live |
| **Bulk Text Send API** | `send_whatsapp_text_bulk` — send a single message to multiple phone numbers in one API call |
| **Bug fix: NameError** | Fixed unbound `e` variable in `rasayel_whatsapp_file_message_pdf` except block |
| **Bug fix: duplicate function** | Removed duplicate `rasayel_whatsapp_file_message_pdfa3` definition that silently overrode the first |
| **Bug fix: redundant guards** | Removed doubled `if "error" in upload_response` and doubled `if not blob_id` checks |
| **Bug fix: Single doctype** | `send_bevatel_message` now correctly uses `frappe.get_doc("Whatsapp Saudi")` (single doc, no name arg) |
| **Bug fix: hardcoded template** | `send_bevatel_*` functions now read `template_name` and `language` from the Whatsapp Saudi config instead of hardcoding `"ivoice11"` / `"ar"` |
| **Bug fix: hardcoded URL** | `send_bevatel_message` now reads `bavatel_file_url` from config instead of hardcoding the URL |

---

## 🧩 Template Message Format

When the notification channel is **Whatsapp Saudi** the *Message* field uses a key=value block:

```
message_template_id = "42"
language            = "en"
var1                = "{{ doc.customer_name }}"
var2                = "{{ doc.grand_total }}"
```

- `message_template_id` — numeric ID of the WhatsApp template.
- `language` — BCP 47 language tag (`en`, `ar`, …).
- `var1`, `var2`, … — body parameters rendered with the Frappe Jinja context (`doc`, `frappe`, …).

---

## 🔑 Phone Number Normalisation

All phone numbers are normalised to **`966XXXXXXXXX`** (Saudi format, no leading `+`) before sending:

| Input | Result |
|-------|--------|
| `+966 50 123 4567` | `966501234567` |
| `0501234567` | `966501234567` |
| `00966501234567` | `966501234567` |
| `966501234567` | `966501234567` |

---

## 📊 Utility APIs

All endpoints require an authenticated Frappe session (or a valid API key) unless noted.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `whatsapp_saudi.overrides.whtatsapp_notification.send_whatsapp_text` | GET/POST | Send plain text to one number |
| `whatsapp_saudi.overrides.whtatsapp_notification.send_whatsapp_text_bulk` | POST | Send plain text to multiple numbers |
| `whatsapp_saudi.overrides.whtatsapp_notification.get_message_statistics` | GET | Sent/Failed counts + active provider |
| `whatsapp_saudi.overrides.whtatsapp_notification.validate_whatsapp_config` | GET | Validate active-provider credentials |
| `whatsapp_saudi.overrides.whtatsapp_notification.get_whatsapp_pdf` | POST | Send PDF via active provider |
| `whatsapp_saudi.overrides.whtatsapp_notification.get_whatsapp_pdf_a3` | POST | Send PDF/A-3 via active provider |
| `whatsapp_saudi.whatsapp_saudi.doctype.whatsapp_saudi.whatsapp_saudi.receive_whatsapp_message` | POST (guest) | Incoming-message webhook |

---

## 🔒 Permissions

- **Whatsapp Saudi** settings: `System Manager` only.
- **Whatsapp Saudi Success Log**: `System Manager` (read, write, create, delete, export, report).
- **Manager Permissions** module restricts HR documents (Leave Application, Loan Application, Clearance Form, Visit Form, Permission Application) so that managers see only records for their assigned employees.

---

## 👤 Author

Aysha Sithara — [ERPGulf.com](https://erpgulf.com)

---

## 📄 License

MIT — see [license.txt](license.txt)

