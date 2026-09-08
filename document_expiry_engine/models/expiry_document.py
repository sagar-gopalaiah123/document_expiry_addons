# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ExpiryDocument(models.Model):
    _name = 'document.expiry.document'
    _description = 'Expiry Tracked Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expiry_date asc, id desc'
    _rec_name = 'name'

    name = fields.Char(required=True, tracking=True)
    document_type_id = fields.Many2one(
        'document.expiry.type', string='Document Type', tracking=True, ondelete='restrict')
    document_number = fields.Char(string='Document Number / Reference')

    attachment_id = fields.Many2one(
        'ir.attachment', string='Attachment', ondelete='set null', copy=False)
    attachment_datas = fields.Binary(
        string='File', related='attachment_id.datas', readonly=False, related_sudo=False)
    attachment_name = fields.Char(
        string='File Name', related='attachment_id.name', readonly=False, related_sudo=False)
    history_ids = fields.One2many(
        'document.expiry.document.history', 'document_id', string='Document History')
    history_count = fields.Integer(compute='_compute_history_count')

    issue_date = fields.Date(string='Issue Date', tracking=True)
    expiry_date = fields.Date(string='Expiry Date', tracking=True)
    has_expiry = fields.Boolean(string='Has Expiry', default=True)

    remarks = fields.Text(string='Remarks / Notes')

    status = fields.Selection([
        ('valid', 'Valid'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired', 'Expired'),
        ('no_expiry', 'No Expiry'),
    ], string='Status', compute='_compute_status', store=True, tracking=True)
    days_remaining = fields.Integer(
        string='Days Remaining', compute='_compute_status', store=True)

    uploaded_by = fields.Many2one(
        'res.users', default=lambda self: self.env.user, string='Uploaded By', readonly=True)
    upload_date = fields.Datetime(default=fields.Datetime.now, readonly=True, string='Upload Date')
    responsible_user_id = fields.Many2one('res.users', string='Responsible User', tracking=True)

    # ---- Generic link to any business record (Employee, Customer, Vehicle, ...) ----
    res_model_id = fields.Many2one(
        'ir.model', string='Related Document Model', ondelete='cascade',
        domain=[('transient', '=', False)])
    res_model = fields.Char(
        string='Related Model', related='res_model_id.model', store=True, index=True)
    res_id = fields.Many2oneReference(
        string='Related Record ID', model_field='res_model', index=True)
    resource_ref = fields.Reference(
        selection='_selection_target_model', compute='_compute_resource_ref',
        string='Related Record', readonly=True)

    department_id = fields.Many2one('hr.department', string='Department')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    reminder_log_ids = fields.One2many(
        'document.expiry.reminder.log', 'document_id', string='Reminder Log')

    @api.model
    def _selection_target_model(self):
        models_ = self.env['ir.model'].sudo().search([('transient', '=', False)])
        return [(m.model, m.name) for m in models_]

    @api.depends('res_model', 'res_id')
    def _compute_resource_ref(self):
        for rec in self:
            if rec.res_model and rec.res_id and rec.res_model in self.env:
                rec.resource_ref = '%s,%s' % (rec.res_model, rec.res_id)
            else:
                rec.resource_ref = False

    def _compute_history_count(self):
        for rec in self:
            rec.history_count = len(rec.history_ids)

    @api.onchange('document_type_id')
    def _onchange_document_type_id(self):
        for rec in self:
            if rec.document_type_id:
                rec.has_expiry = rec.document_type_id.is_expiry_applicable
                if not rec.responsible_user_id and rec.document_type_id.responsible_user_id:
                    rec.responsible_user_id = rec.document_type_id.responsible_user_id
                if (rec.document_type_id.default_validity_days and rec.issue_date
                        and not rec.expiry_date):
                    rec.expiry_date = fields.Date.add(
                        rec.issue_date, days=rec.document_type_id.default_validity_days)

    @api.onchange('issue_date')
    def _onchange_issue_date(self):
        for rec in self:
            if (rec.issue_date and rec.document_type_id
                    and rec.document_type_id.default_validity_days and not rec.expiry_date):
                rec.expiry_date = fields.Date.add(
                    rec.issue_date, days=rec.document_type_id.default_validity_days)

    @api.depends('expiry_date', 'has_expiry')
    def _compute_status(self):
        threshold = int(self.env['ir.config_parameter'].sudo().get_param(
            'document_expiry_engine.expiring_soon_days', default='30'))
        today = fields.Date.context_today(self)
        for rec in self:
            if not rec.has_expiry or not rec.expiry_date:
                rec.status = 'no_expiry'
                rec.days_remaining = 0
                continue
            delta = (rec.expiry_date - today).days
            rec.days_remaining = delta
            if delta < 0:
                rec.status = 'expired'
            elif delta <= threshold:
                rec.status = 'expiring_soon'
            else:
                rec.status = 'valid'

    @api.constrains('issue_date', 'expiry_date')
    def _check_dates(self):
        for rec in self:
            if rec.issue_date and rec.expiry_date and rec.expiry_date < rec.issue_date:
                raise ValidationError(_('Expiry Date cannot be earlier than Issue Date.'))

    def write(self, vals):
        if 'attachment_id' in vals:
            for rec in self:
                if rec.attachment_id and rec.attachment_id.id != vals.get('attachment_id'):
                    self.env['document.expiry.document.history'].sudo().create({
                        'document_id': rec.id,
                        'attachment_id': rec.attachment_id.id,
                        'changed_by': self.env.user.id,
                    })
        return super().write(vals)

    def action_view_history(self):
        self.ensure_one()
        return {
            'name': _('Document History'),
            'type': 'ir.actions.act_window',
            'res_model': 'document.expiry.document.history',
            'view_mode': 'list,form',
            'domain': [('document_id', '=', self.id)],
        }

    # ---------------------------------------------------------------
    # Cron: refresh status/days-remaining and dispatch reminders
    # ---------------------------------------------------------------
    @api.model
    def cron_update_status_and_reminders(self):
        docs = self.search([])
        # Stored computed fields (status/days_remaining) are recalculated as part
        # of the ORM's normal recompute mechanism whenever they are marked dirty;
        # calling the compute explicitly guarantees a daily refresh even though
        # no field the compute depends on was written to.
        docs._compute_status()
        self.env.flush_all()
        docs.filtered(lambda d: d.has_expiry and d.expiry_date)._send_expiry_reminders()
        return True

    def _send_expiry_reminders(self):
        template = self.env.ref(
            'document_expiry_engine.mail_template_document_expiry_reminder',
            raise_if_not_found=False)
        ReminderLog = self.env['document.expiry.reminder.log']
        for rec in self:
            rules = rec.document_type_id.reminder_rule_ids if rec.document_type_id else \
                self.env['document.expiry.reminder.rule']
            if not rules or rec.status == 'no_expiry':
                continue
            for rule in rules:
                if rec.days_remaining != rule.days_before:
                    continue
                already_sent = ReminderLog.search_count([
                    ('document_id', '=', rec.id),
                    ('days_before', '=', rule.days_before),
                ])
                if already_sent:
                    continue
                if rule.notify_activity and rec.responsible_user_id:
                    rec.activity_schedule(
                        'mail.mail_activity_data_todo',
                        summary=_('Document Expiry Reminder: %s', rec.name),
                        note=_('Document "%(doc)s" expires in %(days)s day(s) on %(date)s.',
                               doc=rec.name, days=rule.days_before, date=rec.expiry_date),
                        user_id=rec.responsible_user_id.id,
                    )
                if rule.notify_email and template and rec.responsible_user_id:
                    template.send_mail(rec.id, force_send=True, email_values={
                        'email_to': rec.responsible_user_id.email,
                    })
                ReminderLog.create({
                    'document_id': rec.id,
                    'days_before': rule.days_before,
                })


class ExpiryDocumentHistory(models.Model):
    _name = 'document.expiry.document.history'
    _description = 'Document Expiry - Attachment History'
    _order = 'changed_date desc'

    document_id = fields.Many2one(
        'document.expiry.document', required=True, ondelete='cascade')
    attachment_id = fields.Many2one('ir.attachment', string='Previous Attachment')
    changed_by = fields.Many2one('res.users', default=lambda self: self.env.user)
    changed_date = fields.Datetime(default=fields.Datetime.now)
