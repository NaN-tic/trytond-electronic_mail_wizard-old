#This file is part electronic_mail_wizard module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.

from trytond.model import ModelView, ModelSQL, fields

class Template(ModelSQL, ModelView):
    _name = 'electronic.mail.template'

    wizard = fields.Many2One("ir.action.wizard", 'Wizard')

Template()
