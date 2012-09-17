#This file is part electronic_mail_wizard module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import mimetypes
import base64
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.utils import formatdate

from trytond.model import ModelView, ModelSQL, fields
from trytond.wizard import Wizard, StateTransition, StateView, Button
from trytond.transaction import Transaction
from trytond.pool import Pool

class TemplateEmailStart(ModelView):
    'Template Email Start'
    _name = 'electronic.mail.wizard.templateemail.start'
    _description = __doc__

    from_ = fields.Char('From', readonly=True)
    sender = fields.Char('Sender', required=True)
    to = fields.Char('To', required=True)
    cc = fields.Char('CC')
    bcc = fields.Char('BCC')
    subject = fields.Char('Subject', required=True)
    plain = fields.Text('Plain Text Body', required=True)
    total = fields.Integer('Total', readonly=True,
        help='Total emails to send')
    template = fields.Many2One("electronic.mail.template", 'Template')
    model = fields.Many2One(
        'ir.model', 'Model', required=True, select="1")

TemplateEmailStart()

class TemplateEmailResult(ModelView):
    'Template Email Result'
    _name = 'electronic.mail.wizard.templateemail.result'
    _description = __doc__

    name = fields.Char('Name', help='Name of Header Field')

TemplateEmailResult()

class GenerateTemplateEmail(Wizard):
    "Generate Email from template"
    _name = "electronic_mail_wizard.templateemail"

    start = StateView('electronic.mail.wizard.templateemail.start',
        'electronic_mail_wizard.templateemail_start', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Send', 'send', 'tryton-ok', default=True),
            ])
    send = StateTransition()

    def render(self, template, record, values):
        '''Renders the template and returns as email object
        :param template: Browse Record of the template
        :param record: Browse Record of the template
        :param values: Dicctionary values
        :return: 'email.message.Message' instance
        '''
        template_obj = Pool().get('electronic.mail.template')

        message = MIMEMultipart('alternative')
        message['date'] = formatdate(localtime=1)

        language = Transaction().context.get('language', 'en_US')
        if template.language:
            language = template_obj.eval(template, template.language, record)

        with Transaction().set_context(language = language):
            template = template_obj.browse(template.id)

            message['from_'] = template_obj.eval(template, values['from_'], record)
            message['to'] = template_obj.eval(template, values['to'], record)
            message['cc'] = template_obj.eval(template, values['cc'], record)
            message['bcc'] = template_obj.eval(template, values['bcc'], record)
            message['subject'] = template_obj.eval(template, values['subject'], record)

            # Attach reports
            if template.reports:
                reports = template_obj.render_reports(
                    template, record
                    )
                for report in reports:
                    ext, data, filename, file_name = report[0:5]
                    if file_name:
                        filename = template_obj.eval(template, file_name, record)
                    filename = ext and '%s.%s' % (filename, ext) or filename
                    content_type, _ = mimetypes.guess_type(filename)
                    maintype, subtype = (
                        content_type or 'application/octet-stream'
                        ).split('/', 1)

                    attachment = MIMEBase(maintype, subtype)
                    attachment.set_payload(base64.b64encode(data)) 

                    attachment.add_header(
                        'Content-Disposition', 'attachment', filename=filename)
                    attachment.add_header(
                        'Content-Transfer-Encoding', 'base64')
                    message.attach(attachment)

            # HTML & Text Alternate parts
            plain = template_obj.eval(template, values['plain'], record)
            if template.signature:
                user_obj = Pool().get('res.user')
                user = user_obj.browse(Transaction().user)
                if user.signature:
                    signature = user.signature.encode("ASCII", 'ignore')
                    plain = '%s\n--\n%s' % (plain, signature)
            html = re.sub('\n', '<br/>', plain) #html body email as same as plain but \n replaced by <br/>
            message.attach(MIMEText(plain, 'plain'))
            message.attach(MIMEText(html, 'html'))

            # Add headers
            for header in template.headers:
                message.add_header(
                    header.name,
                    unicode(self.eval(template, header.value, record))
                )

        return message

    def render_fields(self, name):
        '''Get the fields before render and return a dicc
        :param name: Str ir.action.wizard
        :return: dicc
        '''
        default = {}

        wizard_obj = Pool().get('ir.action.wizard')
        template_obj = Pool().get('electronic.mail.template')
        active_ids = Transaction().context.get('active_ids')

        wizards = wizard_obj.search(['wiz_name','=',name])
        if not len(wizards) > 0:
            return default
        wizard = wizard_obj.browse(wizards[0])
        template = wizard.template[0]
        total = len(active_ids)

        default['from_'] = template.from_
        default['total'] = total
        default['template'] = template.id
        default['model'] = template.model.id
        if total > 1: #show fields with tags
            default['to'] = template.to
            default['cc'] = template.cc
            default['bcc'] = template.bcc
            default['subject'] = template.subject
            default['plain'] = template.plain
        else: #show fields with rendered tags
            record = Pool().get(template.model.model).browse(active_ids[0]) 
            default['to'] = template_obj.eval(template, template.to, record)
            default['cc'] = template_obj.eval(template, template.cc, record)
            default['bcc'] = template_obj.eval(template, template.bcc, record)
            default['subject'] = template_obj.eval(template, template.subject, record)
            default['plain'] = template_obj.eval(template, template.plain, record)
        return default

    def render_and_send(self, session):
        email_obj = Pool().get('electronic.mail')
        template_obj = Pool().get('electronic.mail.template')

        template = session.start.template
        model = session.start.model

        for active_id in Transaction().context.get('active_ids'):
            record = Pool().get(model.model).browse(active_id)
            values = {}
            values['from_'] = session.start.from_
            values['to'] = session.start.to
            values['cc'] = session.start.cc
            values['bcc'] = session.start.bcc
            values['subject'] = session.start.subject
            values['plain'] = session.start.plain
            
            email_message = self.render(template, record, values)
            email_id = email_obj.create_from_email(
                email_message, template.mailbox.id)
            template_obj.send_email(email_id, template)

            Pool().get('electronic.mail.template').add_event(template, record, email_id, email_message) #add event

        return True

GenerateTemplateEmail()

class ExampleGenerateTemplateEmail(GenerateTemplateEmail):
    "Example Wizard to Generate Email from template"
    _name = "electronic_mail_wizard.example"

    def default_start(self, session, fields):
        default = self.render_fields(self._name)
        return default

    def transition_send(self, session):
        self.render_and_send(session)
        return 'end'

ExampleGenerateTemplateEmail()
