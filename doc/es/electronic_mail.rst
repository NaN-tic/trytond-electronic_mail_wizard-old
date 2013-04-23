#:after:electronic_mail/electronic_mail:section:electronic_email#

===============================
Asistente de correo electrónico
===============================

Permite relacionar asistentes con plantillas de correo electrónico. Es un módulo
genérico para que otros módulos usen su API.

Configuración
=============

Cuando añada un nuevo asistente deberá añadir en su módulo personalizado una
nueva clase. Por ejemplo

.. code:: python

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

* Example Generate Template Email: Por el nombre de su clase.
* electronic_mail_wizard.example: Por el nombre del asistente.

No olvide que el nombre del asistente use el mismo nombre que el definido en el
**_name** de esta clase.

Los ficheros XML's puede definirlos en su propio módulo, asi no deberá crearlos
a mano. Por ejemplo:

.. code::

    <record model="ir.action.wizard" id="wizard_emailtemplate_party">
        <field name="name">Email Party</field>
        <field name="wiz_name">electronic_mail_wizard.party</field>
        <field name="model">party.party</field>
    </record>
    <record model="ir.action.keyword" id="emailtemplate_party_keyword">
        <field name="keyword">form_action</field>
        <field name="model">party.party,-1</field>
        <field name="action" ref="wizard_emailtemplate_party"/>
    </record>

Recuerde una vez instalado/actualizado su módulo, debe relacionar la plantilla
con el asistente en el apartado **Avanzado** de su plantilla.

.. note:: Una vez generado el asistente, para que esté visible, deberemos
          cerrar el cliente GTK y volver a identificarnos. Esto es debido a que
          los botones de la cabezera se encuentran en memória para ir más
          rápido en las aperturas de las vistas.
