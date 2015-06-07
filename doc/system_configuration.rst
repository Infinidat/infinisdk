System Configuration
====================

SMTP Configuration
------------------

Querying SMTP notification targets:

.. code-block:: python
       
       >>> for smtp_config in system.notification_targets.find(protocol='SMTP'):
       ...     pass
       
Modifying SMTP notification targets:

.. code-block:: python
       
       >>> smtp_config = list(system.notification_targets.find(protocol='SMTP'))[0]
       >>> smtp_config.update_name('sample_config_1')

       >>> smtp_config.update_host('mailserver.lab.com')
       >>> smtp_config.update_port(25)
       >>> smtp_config.update_username('username')
       >>> smtp_config.update_password('password')
       >>> smtp_config.update_from_address('username@domain.com')
       >>> smtp_config.update_tls(True)

Testing SMTP notification targets:

      >>> smtp_config.test(recipients=['someuser@domain.com'])

.. seealso:: :class:`.NotificationTarget`
