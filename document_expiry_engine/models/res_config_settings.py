# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    expiring_soon_days = fields.Integer(
        string='Expiring Soon Threshold (Days)',
        config_parameter='document_expiry_engine.expiring_soon_days',
        default=30,
        help='A document is flagged "Expiring Soon" when its expiry date is within this '
             'many days from today.')
