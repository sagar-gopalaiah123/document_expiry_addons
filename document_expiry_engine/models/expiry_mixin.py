# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DocumentExpiryMixin(models.AbstractModel):
    """Inherit this mixin on any model (hr.employee, res.partner, fleet.vehicle,
    project.project, ...) to expose a Documents smart button / tab backed by the
    generic document.expiry.document model, with zero changes to that model's
    own table (documents are linked generically via res_model/res_id).

    Usage on a new model:
        class FleetVehicle(models.Model):
            _name = 'fleet.vehicle'
            _inherit = ['fleet.vehicle', 'document.expiry.mixin']

    Then add to its form view:
        <button name="action_view_expiry_documents" type="object"
                class="oe_stat_button" icon="fa-file-text-o">
            <field name="expiry_document_count" widget="statinfo" string="Documents"/>
        </button>
    """
    _name = 'document.expiry.mixin'
    _description = 'Document Expiry Mixin'

    expiry_document_ids = fields.One2many(
        'document.expiry.document', compute='_compute_expiry_document_ids',
        string='Expiry Tracked Documents', search='_search_expiry_document_ids')
    expiry_document_count = fields.Integer(
        compute='_compute_expiry_document_ids', string='Document Count')

    def _compute_expiry_document_ids(self):
        Document = self.env['document.expiry.document']
        for rec in self:
            docs = Document.search([
                ('res_model', '=', rec._name),
                ('res_id', '=', rec.id),
            ])
            rec.expiry_document_ids = docs
            rec.expiry_document_count = len(docs)

    def _search_expiry_document_ids(self, operator, value):
        Document = self.env['document.expiry.document']
        docs = Document.search([('name', operator, value), ('res_model', '=', self._name)])
        return [('id', 'in', docs.mapped('res_id'))]

    def action_view_expiry_documents(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'document_expiry_engine.action_document_expiry_document')
        action['domain'] = [('res_model', '=', self._name), ('res_id', '=', self.id)]
        action['context'] = {
            'default_res_model': self._name,
            'default_res_id': self.id,
            'default_name': self.display_name,
        }
        return action
