Electronic Mail Wizard Module
#############################

The electronic_mail_wizard module generate wizard from template mail.

Add in your custom module a new class. For example:

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

In your template, add new wizard related by template at the name call this class.

* Replace ExampleGenerateTemplateEmail to your name class
* Replace electronic_mail_wizard.example to your wizard name

You can get more examples "electronic_mail_pyme" module.
