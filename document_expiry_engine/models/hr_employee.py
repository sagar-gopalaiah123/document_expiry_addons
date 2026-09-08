# -*- coding: utf-8 -*-
from odoo import models


class HrEmployee(models.Model):
    _name = 'hr.employee'
    _inherit = ['hr.employee', 'document.expiry.mixin']
