#This file is part electronic_mail_wizard module for Tryton.
#The COPYRIGHT file at the top level of this repository contains 
#the full copyright notices and license terms.
{
    'name': 'Electronic Mail Wirzard',
    'name_ca_ES': 'Assistent Correu electrònic',
    'name_es_ES': 'Asistente Correo electrónico',
    'version': '2.4.0',
    'author': 'Zikzakmedia',
    'email': 'zikzak@zikzakmedia.com',
    'website': 'http://www.zikzakmedia.com/',
    'description': '''Electronic Mail Wirzard''',
    'description_ca_ES': '''Asistent Correu electrònic''',
    'description_es_ES': '''Asistente Correo electrónico''',
    'depends': [
        'ir',
        'res',
        'electronic_mail_template',
    ],
    'xml': [
        'electronic_mail_wizard.xml',
        'template.xml',
    ],
    'translation': [
        # 'locale/ca_ES.po',
        # 'locale/es_ES.po',
    ]
}
