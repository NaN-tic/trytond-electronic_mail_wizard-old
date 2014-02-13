#:after:electronic_mail/electronic_mail:section:configuration#

===============================
Asistente de correo electrónico
===============================

Permite relacionar asistentes con plantillas de correo electrónico.

Configuración
=============

Cuando añada una nueva plantilla si marca la opción `Crear Acción` se creará
una acción en el modelo de la plantilla que permite el envío del correo
electrónico para los registros seleccionados.

.. note:: Una vez generado el asistente, para que esté visible, deberemos
          cerrar el cliente GTK y volver a identificarnos. Esto es debido a que
          los botones de la cabezera se encuentran en memória para ir más
          rápido en las aperturas de las vistas.

Si selecciona un solo registro, se mostrarà la previsualización previa del
correo a enviar que podrà modificar. Si se selecciona mas de un registro se
mostrará una previsualización del correo, con los campos de la plantilla que se
evaluarán para cada registro.
