# -*- coding: utf-8 -*-
from odoo import models, fields


class DocumentExpiryReminderLog(models.Model):
    _name = 'document.expiry.reminder.log'
    _description = 'Document Expiry - Reminder Log'
    _order = 'sent_date desc'

    document_id = fields.Many2one(
        'document.expiry.document', required=True, ondelete='cascade', index=True)
    days_before = fields.Integer(required=True)
    sent_date = fields.Datetime(default=fields.Datetime.now)

    _sql_constraints = [
        ('doc_days_uniq', 'unique(document_id, days_before)',
         'A reminder for this interval has already been logged for this document.'),
    ]
