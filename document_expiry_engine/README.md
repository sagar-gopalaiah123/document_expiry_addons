# Document Expiry Tracking Engine — Odoo 18

A generic, reusable engine to track documents with expiry dates (passports, licenses,
insurance, contracts, certificates, ...) against **any** business record — Employees,
Customers, Vendors, Vehicles, Contracts, or any custom model — from one centralized
module, with a configurable status engine, reminders, and a dashboard.

## 1. Module Structure

```
document_expiry_engine/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── document_type.py          # document.expiry.type, document.expiry.reminder.rule
│   ├── expiry_mixin.py           # document.expiry.mixin (reusable on any model)
│   ├── expiry_document.py        # document.expiry.document, .history
│   ├── reminder_log.py           # document.expiry.reminder.log
│   ├── res_config_settings.py    # expiring_soon_days setting
│   ├── hr_employee.py            # applies mixin to hr.employee
│   └── res_partner.py            # applies mixin to res.partner
├── security/
│   ├── document_expiry_security.xml   # 3 groups + record rules
│   └── ir.model.access.csv
├── data/
│   ├── ir_cron.xml               # daily status refresh + reminders
│   └── mail_template.xml         # reminder email
├── views/
│   ├── document_type_views.xml
│   ├── expiry_document_views.xml
│   ├── res_config_settings_views.xml
│   ├── hr_employee_views.xml     # smart button on Employee form
│   ├── res_partner_views.xml     # smart button on Contact form
│   ├── dashboard_views.xml       # client action registration
│   └── menu_views.xml
├── static/src/{js,xml,scss}      # OWL dashboard
└── demo/demo_data.xml
```

## 2. Data Model

### `document.expiry.document` (core model)
Generic — linked to **any** record via `res_model_id` (ir.model) + `res_id`
(`fields.Many2oneReference`), computed into a `resource_ref` (`fields.Reference`)
for a clickable smart-link in the UI. Fields cover everything in the spec: name,
type, number/reference, attachment, issue/expiry dates, remarks, computed
`status` + `days_remaining` (stored), uploaded_by/upload_date, responsible user.

**Status engine** (`_compute_status`, stored, depends on `expiry_date`/`has_expiry`):
- reads the threshold from `ir.config_parameter` (`document_expiry_engine.expiring_soon_days`, default 30)
- `expiry_date < today` → `expired`
- `0 <= days_remaining <= threshold` → `expiring_soon`
- `days_remaining > threshold` → `valid`
- no expiry date / type not expiry-applicable → `no_expiry`

Because "days remaining" changes with the calendar even when nothing is written,
a **daily cron** (`cron_update_status_and_reminders`) re-triggers the compute
every day rather than relying only on write-time recomputation.

### `document.expiry.type` (configuration)
Name, description, `is_expiry_applicable`, `default_validity_days` (auto-fills
`expiry_date` from `issue_date` on the document via onchange), default
responsible user/group, and a `reminder_rule_ids` One2many.

### `document.expiry.reminder.rule`
Per document type: `days_before`, and whether to fire an **activity** and/or an
**email** at that interval.

### `document.expiry.reminder.log`
One row per (document, days_before) sent — a SQL unique constraint plus an
existence check in `_send_expiry_reminders()` guarantees **no duplicate
reminders**.

### `document.expiry.mixin` (AbstractModel)
Drop this into any model to get a `expiry_document_ids` computed O2M, an
`expiry_document_count`, and `action_view_expiry_documents()` for a smart
button — without touching that model's table. Already applied to
`hr.employee` and `res.partner`; see the docstring in `expiry_mixin.py` for
how to add it to `fleet.vehicle`, `project.project`, etc. in two lines.

## 3. Security

Three groups (`Document User` → `Document Manager` → `Administrator`,
cumulative via `implied_ids`):

| Group | Access |
|---|---|
| Document User | read all; create/edit only documents they uploaded or are responsible for (record rule); cannot delete |
| Document Manager | full CRUD on documents; manage document types, thresholds, reminders; dashboard |
| Administrator | everything, incl. Settings |

## 4. Dashboard

`ir.actions.client` (`document_expiry_dashboard`) rendering an OWL component
(`static/src/js/dashboard.js` + `dashboard_templates.xml`). It shows:
- KPI cards: Total, Valid, Expiring Soon, Expired, Expiring Today/7d/30d
- Status-wise analysis, Document Type analysis, Expiry Timeline (Today/7/15/30/60/90 days)
- Every card/row is clickable and drills down into a filtered list view via
  `action.doAction`, exactly matching the spec's "KPI → filtered list → record" flow.

## 5. Installation

1. Copy the `document_expiry_engine` folder into your Odoo 18 `addons` path
   (e.g. alongside your other Prixgen custom modules).
2. Restart the Odoo service, or if already running:
   `odoo-bin -u document_expiry_engine -d <your_db> --stop-after-init`
   (or restart + Update Apps List from Settings → Apps if installing for the first time).
3. Go to **Apps**, search "Document Expiry Tracking Engine", click **Install**.
4. (Optional) Install with demo data for a quick look at sample documents.

## 6. Testing Checklist

1. **Settings** → Document Expiry app → set "Expiring Soon Threshold" (e.g. 30 days).
2. **Configuration → Document Types**: create/edit a type, set a default validity
   and add reminder rules (e.g. 30/15/7/1 days before).
3. **Documents** menu → create a document, pick a type, set Issue Date — confirm
   Expiry Date auto-fills from the type's default validity (onchange).
4. Set an Expiry Date 5 days from today → Status should compute to `Expiring Soon`
   once threshold >= 5; set it in the past → `Expired`.
5. On an **Employee** form / **Contact** form, confirm the "Documents" smart
   button appears and opens a pre-filtered list scoped to that record
   (`res_model`/`res_id`).
6. Trigger the cron manually: Settings → Technical → Scheduled Actions →
   "Document Expiry: Update Status & Send Reminders" → **Run Manually**.
   Confirm activities/emails fire once per (document, interval) and are **not**
   duplicated on a second run (check `document.expiry.reminder.log`).
7. Open the **Dashboard** menu, confirm KPI counts match the Documents list,
   and click a KPI/status/type/timeline row to confirm it opens the correctly
   filtered list.
8. As a user only in the **Document User** group, confirm they can only edit
   documents where they are `uploaded_by` or `responsible_user_id`, and cannot
   delete or access Configuration/Settings.
9. Replace a document's attachment → open the "Versions" smart button on the
   document form and confirm the previous attachment was archived to
   `document.expiry.document.history`.

## 7. Extending to Another Model (e.g. Vehicles)

```python
class FleetVehicle(models.Model):
    _name = 'fleet.vehicle'
    _inherit = ['fleet.vehicle', 'document.expiry.mixin']
```
```xml
<button name="action_view_expiry_documents" type="object"
        class="oe_stat_button" icon="fa-file-text-o">
    <field name="expiry_document_count" widget="statinfo" string="Documents"/>
</button>
```
No changes are needed to `document.expiry.document` — it already links to
*any* model via `res_model_id`/`res_id`.

## 8. Notes / Things to Confirm With Your Team Before Go-Live

- Reminder rules currently live on `document.expiry.type` (shared by all
  documents of that type). If you need **per-document** overrides, add a
  `reminder_rule_ids` O2M directly on `document.expiry.document` and merge it
  with the type-level rules in `_send_expiry_reminders()`.
- Email sending uses `responsible_user_id.email`; if a document has no
  responsible user, only the activity (if enabled) fires — consider a
  fallback to `document_type_id.responsible_user_id` or a distribution list.
- `department_id` on the document is a plain field for filtering; wire it via
  an onchange from `resource_ref` if you want it auto-populated from the
  linked employee.
