# -*- coding: utf-8 -*-
from odoo import models


class AccountAsset(models.Model):
    _name = 'account.asset'
    _inherit = ['account.asset', 'document.expiry.mixin']
