# This file is part electronic_mail_wizard module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.utils import formatdate, make_msgid
from email import Encoders, charset
from email.header import Header
from time import sleep
from trytond.model import ModelView, fields
from trytond.wizard import Wizard, StateTransition, StateView, Button
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.pyson import Eval
from trytond.modules.electronic_mail_template.template import styles_dir
import threading
import logging
import mimetypes

__all__ = ['TemplateEmailStart', 'TemplateEmailResult',
    'GenerateTemplateEmail']

logger = logging.getLogger(__name__)


class TemplateEmailStart(ModelView):
    'Template Email Start'
    __name__ = 'electronic.mail.wizard.templateemail.start'

    from_ = fields.Char('From', readonly=True)
    sender = fields.Char('Sender', required=True)
    to = fields.Char('To', required=True)
    cc = fields.Char('CC')
    bcc = fields.Char('BCC')
    subject = fields.Char('Subject', required=True,
        states={
            'readonly': Eval('multi_lang', True),
        }, depends=['multi_lang'])
    plain = fields.Text('Plain Text Body', required=True,
        states={
            'readonly': Eval('multi_lang', True),
        }, depends=['multi_lang'])
    send_html = fields.Boolean('Send HTML',
        help='Send email with text and html')
    html = fields.Text('HTML Text Body',
        states={
            'invisible': ~Eval('send_html', True),
            'required': Eval('send_html', True),
            'readonly': Eval('multi_lang', True),
        }, depends=['send_html', 'multi_lang'])
    total = fields.Integer('Total', readonly=True,
        help='Total emails to send')
    message_id = fields.Char('Message-ID')
    in_reply_to = fields.Char('In Repply To')
    template = fields.Many2One("electronic.mail.template", 'Template')
    multi_lang = fields.Boolean('Multi Lang',
        help='Email records have multi languages.')
    queue = fields.Boolean('Queue',
        help='Put these messages in the output mailbox instead of sending '
            'them immediately.')

    @staticmethod
    def default_multi_lang():
        return False


class TemplateEmailResult(ModelView):
    'Template Email Result'
    __name__ = 'electronic.mail.wizard.templateemail.result'

    name = fields.Char('Name', help='Name of Header Field')


class GenerateTemplateEmail(Wizard):
    "Generate Email from template"
    __name__ = "electronic_mail_wizard.templateemail"

    start = StateView('electronic.mail.wizard.templateemail.start',
        'electronic_mail_wizard.templateemail_start', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Send', 'send', 'tryton-ok', default=True),
            ])
    send = StateTransition()

    @classmethod
    def __setup__(cls):
        super(GenerateTemplateEmail, cls).__setup__()
        cls._error_messages.update({
            'template_deleted': 'This template has been deactivated or '
                'deleted.',
            })

    def default_start(self, fields):
        default = self.render_fields(self.__name__)
        return default

    def transition_send(self):
        self.render_and_send()
        return 'end'

    def render(self, template, record, values):
        '''Renders the template and returns as email object
        :param template: Object of the template
        :param record: Object of the template
        :param values: Dicctionary values
        :return: 'email.message.Message' instance
        '''
        Template = Pool().get('electronic.mail.template')

        message = MIMEMultipart()
        messageid = template.eval(values['message_id'], record)
        message['message_id'] = messageid or make_msgid()
        message['date'] = formatdate(localtime=1)
        message['in_reply_to'] = ""
        if values.get('in_reply_to'):
            message['in_reply_to'] = template.eval(values['in_reply_to'],
                record)

        language = Transaction().context.get('language', 'en_US')
        if template.language:
            language = template.eval(template.language, record)

        with Transaction().set_context(language=language):
            template = Template(template.id)
            message['from'] = template.eval(values['from_'], record)
            message['to'] = template.eval(values['to'], record)
            message['cc'] = template.eval(values['cc'], record)
            #~ message['bcc'] = template.eval(values['bcc'], record)
            message['subject'] = Header(template.eval(values['subject'],
                    record), 'utf-8')

            plain = template.eval(values['plain'], record)

            signature_html = None
            if template.signature:
                User = Pool().get('res.user')
                user = User(Transaction().user)
                if user.signature:
                    signature = user.signature.encode('utf-8')
                    plain = '%s\n--\n%s' % (plain, signature)
                if user.signature_html:
                    signature_html = user.signature_html.encode('utf-8')

            # HTML
            send_html = values.get('send_html')
            if send_html:
                html = template.eval(values['html'], record)
                if template.signature and signature_html:
                    html = '%s<br/>--<br/>%s' % (html, signature_html)

                style = ''
                if template.style:
                    fname = '%s/%s' % (styles_dir(), template.style)
                    with open(fname) as f:
                        style = f.read()
                    if template.custom_style:
                        style += '\n%s' % template.custom_style
                elif template.custom_style:
                    style = '%s' % template.custom_style

                html = """
                    <html>
                    <head><head>
                    <style>
                    %s
                    </style>
                    <body>
                    %s
                    </body>
                    </html>
                    """ % (style, html)

            # MIME HTML or Text
            if send_html:
                body = MIMEMultipart('alternative')
                body.attach(MIMEText(plain, 'plain', _charset='utf-8'))
                body.attach(MIMEText(html, 'html', _charset='utf-8'))
                message.attach(body)
            else:
                message.attach(MIMEText(plain, _charset='utf-8'))
            charset.add_charset('utf-8', charset.QP, charset.QP)

            # Attach reports
            if template.reports:
                reports = template.render_reports(record)
                for report in reports:
                    ext, data, filename, file_name = report[0:5]
                    if file_name:
                        filename = template.eval(file_name, record)
                    filename = ext and '%s.%s' % (filename, ext) or filename
                    content_type, _ = mimetypes.guess_type(filename)
                    maintype, subtype = (
                        content_type or 'application/octet-stream'
                        ).split('/', 1)

                    attachment = MIMEBase(maintype, subtype)
                    attachment.set_payload(data)
                    Encoders.encode_base64(attachment)
                    attachment.add_header(
                        'Content-Disposition', 'attachment', filename=filename)
                    attachment.add_header(
                        'Content-Transfer-Encoding', 'base64')
                    message.attach(attachment)

        return message

    def render_fields(self, name):
        '''Get the fields before render and return a dicc
        :param name: Str ir.action.wizard
        :return: dicc
        '''
        default = {}

        pool = Pool()
        Wizard = pool.get('ir.action.wizard')
        Template = pool.get('electronic.mail.template')
        active_ids = Transaction().context.get('active_ids')

        context = Transaction().context
        action_id = context.get('action_id', None)
        wizard = Wizard(action_id)
        template = (wizard.template and wizard.template[0]
            or self.raise_user_error('template_deleted'))

        total = len(active_ids)
        records = Pool().get(template.model.model).browse(active_ids)

        # Control how many language records are selected
        langs = set()
        if template.language:
            for record in records:
                lang = template.eval(template.language, record)
                langs.add(lang)
                if len(langs) > 1: # not continue; multi lang is True
                    break
            if len(langs) == 1:
                lang, = langs
                with Transaction().set_context(language=lang):
                    template = Template(template.id)
        multi_lang = True if len(langs) > 1 else False
        
        default['total'] = total
        default['multi_lang'] = multi_lang
        default['queue'] = True if template.queue else False
        default['template'] = template.id
        if total > 1:  # show fields with tags
            default['from_'] = template.from_
            default['message_id'] = template.message_id
            default['in_reply_to'] = template.in_reply_to
            default['to'] = template.to
            default['cc'] = template.cc
            default['bcc'] = template.bcc
            default['subject'] = template.subject
            default['plain'] = template.plain
            default['html'] = template.html
        else:  # show fields with rendered tags
            record, = records
            default['from_'] = template.eval(template.from_, record)
            default['message_id'] = template.eval(template.message_id, record)
            default['in_reply_to'] = template.eval(template.in_reply_to,
                record)
            default['to'] = template.eval(template.to, record)
            default['cc'] = template.eval(template.cc, record)
            default['bcc'] = template.eval(template.bcc, record)
            default['subject'] = template.eval(template.subject,
                record)
            default['plain'] = template.eval(template.plain, record)
            default['html'] = template.eval(template.html, record)
        return default

    def render_and_send(self):
        pool = Pool()
        Mail = pool.get('electronic.mail')
        Template = pool.get('electronic.mail.template')
        EmailConfiguration = pool.get('electronic.mail.configuration')
        email_configuration = EmailConfiguration(1)

        template = self.start.template
        if self.start.queue:
            mailbox = template.mailbox_outbox \
                if template.mailbox_outbox else email_configuration.outbox
        else:
            mailbox = template.mailbox if template.mailbox \
                else email_configuration.sent

        active_ids = Transaction().context.get('active_ids')
        total = len(active_ids)
        multi_lang = self.start.multi_lang

        electronic_emails = set()
        activities = []
        for record in pool.get(template.model.model).browse(active_ids):
            values = {}
            values['message_id'] = self.start.message_id
            if self.start.in_reply_to:
                values['in_reply_to'] = self.start.in_reply_to
            values['from_'] = self.start.from_
            values['to'] = self.start.to
            values['cc'] = self.start.cc
            values['bcc'] = self.start.bcc
            values['send_html'] = self.start.send_html

            # multi records and one language
            if not multi_lang and total > 1:
                values['subject'] = template.eval(self.start.subject, record)
                values['plain'] = template.eval(self.start.plain, record)
                values['html'] = template.eval(self.start.html, record)
            # multiple records and multiple language
            elif multi_lang and total > 1 and template.language:
                language = template.eval(template.language, record)
                with Transaction().set_context(language=language):
                    template = Template(template.id)
                values['subject'] = template.eval(template.subject, record)
                values['plain'] = template.eval(template.plain, record)
                values['html'] = template.eval(template.html, record)
            # multiple records and multiple language and not template language
            elif multi_lang and total > 1:
                values['subject'] = template.eval(template.subject, record)
                values['plain'] = template.eval(template.plain, record)
                values['html'] = template.eval(template.html, record)
            # a simple email
            else:
                values['subject'] = self.start.subject
                values['plain'] = self.start.plain
                values['html'] = self.start.html

            emails = []
            if self.start.from_:
                emails += template.eval(self.start.from_, record).split(',')
            if self.start.to:
                emails += template.eval(self.start.to, record).split(',')
            if self.start.cc:
                emails += template.eval(self.start.cc, record).split(',')
            if self.start.bcc:
                emails += template.eval(self.start.bcc, record).split(',')

            email_message = self.render(template, record, values)

            context = {}
            if values.get('bcc'):
                context['bcc'] = values.get('bcc')

            electronic_email = Mail.create_from_email(email_message,
                mailbox, context)
            if not electronic_email: # not configured mailbox
                return
            electronic_emails.add(electronic_email)

            activities = [{
                'record': record,
                'template': template,
                'mail': electronic_email,
                }]

        if activities:
            template.add_activities(activities)  # add activities

        Transaction().commit()
        if not self.start.queue:
            electronic_email_ids = list({e.id for e in electronic_emails})
            db_name = Transaction().database.name
            context = Transaction().context
            thread1 = threading.Thread(target=self.render_and_send_thread,
                args=(db_name, Transaction().user, electronic_email_ids, context))
            thread1.start()

    def render_and_send_thread(self, db_name, user_id, electronic_email_ids, context):
        with Transaction().start(db_name, user_id) as transaction:
            pool = Pool()
            Email = pool.get('electronic.mail')
            EmailConfiguration = pool.get('electronic.mail.configuration')

            with transaction.set_context(context):
                email_configuration = EmailConfiguration(1)
                draft_mailbox = email_configuration.draft

                sleep(5)

                for electronic_email in Email.browse(electronic_email_ids):
                    success = electronic_email.send_email()
                    if success:
                        logger.info('Send email: %s' % (electronic_email.rec_name))
                    else:
                        electronic_email.mailbox = draft_mailbox
                        electronic_email.save()

            transaction.commit()
