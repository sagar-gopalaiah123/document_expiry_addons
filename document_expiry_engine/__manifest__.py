# -*- coding: utf-8 -*-
{
    'name': 'Document Expiry Tracking Engine',
    'version': '18.0.0.1',
    'category': 'Tools',
    'summary': 'Generic document expiry tracking, reminders and dashboard for any Odoo model',
    'description': """
Document Expiry Tracking Engine
================================
Centralized engine to track documents with expiry dates (passports, licenses,
insurance, contracts, certificates, etc.) attached to any business record
(Employee, Customer, Vendor, Vehicle, Contract, ...).

Features
--------
* Generic document model linked to any model via ir.model + res_id (no hardcoding).
* Configurable Document Types with default validity period and reminder rules.
* Automatic status engine: Valid / Expiring Soon / Expired / No Expiry.
* Configurable "Expiring Soon" threshold (Settings).
* Daily scheduled action to refresh status/days remaining and send reminders.
* Reminder engine (activities + email) with duplicate-send protection.
* Consolidated dashboard with KPI cards, status/type breakdown and expiry timeline.
* Reusable mixin (document.expiry.mixin) to add a Documents tab + smart button
  to any model (already applied to hr.employee and res.partner as examples).
* Security groups: Document User / Document Manager / Administrator.
    """,
    'author': 'Prixgen Tech Solutions Pvt. Ltd.',
    'website': 'https://www.prixgen.com',
    'license': 'LGPL-3',
    'depends': ['base', 'base_setup', 'mail', 'hr', 'fleet', 'account_asset'],
    'data': [
        'security/document_expiry_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'data/mail_template.xml',
        'views/document_type_views.xml',
        'views/expiry_document_views.xml',
        'views/res_config_settings_views.xml',
        'views/hr_employee_views.xml',
        'views/res_partner_views.xml',
        'views/fleet_vehicle_views.xml',
        'views/account_asset_views.xml',
        'views/dashboard_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'document_expiry_engine/static/src/js/dashboard.js',
            'document_expiry_engine/static/src/xml/dashboard_templates.xml',
            'document_expiry_engine/static/src/scss/dashboard.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}