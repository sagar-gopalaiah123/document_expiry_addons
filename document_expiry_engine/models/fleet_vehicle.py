# -*- coding: utf-8 -*-
from odoo import models


class FleetVehicle(models.Model):
    _name = 'fleet.vehicle'
    _inherit = ['fleet.vehicle', 'document.expiry.mixin']
