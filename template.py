#This file is part electronic_mail_wizard module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Template']
__metaclass__ = PoolMeta

class Template:
    'Email Template'
    __name__ = 'electronic.mail.template'

    wizard = fields.Many2One("ir.action.wizard", 'Wizard')

