# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DocumentExpiryType(models.Model):
    _name = 'document.expiry.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Document Expiry - Document Type'
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    description = fields.Text()
    is_expiry_applicable = fields.Boolean(
        string='Has Expiry', default=True,
        help='If unchecked, documents of this type will always be considered "No Expiry".')
    default_validity_days = fields.Integer(
        string='Default Validity (Days)',
        help='If set, expiry date is auto-computed from the issue date when a document of '
             'this type is created.')
    responsible_user_id = fields.Many2one('res.users', string='Default Responsible User')
    responsible_group_id = fields.Many2one('res.groups', string='Default Responsible Group')
    reminder_rule_ids = fields.One2many(
        'document.expiry.reminder.rule', 'document_type_id', string='Reminder Rules', copy=True)
    document_count = fields.Integer(compute='_compute_document_count', string='Documents')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)',
         'A document type with this name already exists for this company.'),
    ]

    def _compute_document_count(self):
        grouped = self.env['document.expiry.document']._read_group(
            [('document_type_id', 'in', self.ids)], ['document_type_id'], ['__count'])
        counts = {dt.id: count for dt, count in grouped}
        for rec in self:
            rec.document_count = counts.get(rec.id, 0)

    def action_view_documents(self):
        self.ensure_one()
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'document.expiry.document',
            'view_mode': 'list,form',
            'domain': [('document_type_id', '=', self.id)],
            'context': {'default_document_type_id': self.id},
        }


class DocumentExpiryReminderRule(models.Model):
    _name = 'document.expiry.reminder.rule'
    _description = 'Document Expiry - Reminder Rule'
    _order = 'days_before desc'

    document_type_id = fields.Many2one(
        'document.expiry.type', required=True, ondelete='cascade', string='Document Type')
    days_before = fields.Integer(
        required=True, string='Days Before Expiry',
        help='Number of days before the expiry date on which the reminder should fire.')
    notify_activity = fields.Boolean(default=True, string='Create Activity')
    notify_email = fields.Boolean(default=True, string='Send Email')

    _sql_constraints = [
        ('days_before_positive', 'CHECK(days_before >= 0)',
         'Days Before Expiry must be zero or a positive number.'),
    ]