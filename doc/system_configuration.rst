System Configuration
====================

SMTP Configuration
------------------

Querying SMTP notification targets:

.. code-block:: python
       
       >>> for smtp_target in system.notification_targets.find(protocol='SMTP'):
       ...     pass
       
Modifying SMTP notification targets:

.. code-block:: python
       
       >>> smtp_target = system.notification_targets.find(protocol='SMTP').to_list()[0]
       >>> smtp_target.update_name('sample_config_1')

       >>> smtp_target.update_host('mailserver.lab.com')
       >>> smtp_target.update_port(25)
       >>> smtp_target.update_username('username')
       >>> smtp_target.update_password('password')
       >>> smtp_target.update_from_address('username@domain.com')
       >>> smtp_target.enable_tls()

Testing SMTP notification targets:

      >>> resp = smtp_target.test(recipients=['someuser@domain.com'])


SNMP Configuration
------------------

Creating SNMP targets:

.. code-block:: python
       
       >>> snmp_target = system.notification_targets.create(
       ...    name='snmp_target', protocol='SNMP', host='somehost', private_key='private',
       ...    username='user', password='password',
       ...    private_protocol='AES',
       ...    version='SNMPv3', engine='0x1000000000', auth_type='AuthPriv', auth_protocol='MD5')

Querying SNMP targets:

.. code-block:: python

      >>> for snmp_target in system.notification_targets.find(protocol='SNMP'):
      ...     pass

Modifying SNMP targets:

.. code-block:: python
       
       >>> snmp_target.update_host('hostname')
       >>> snmp_target.update_username('username')
       >>> snmp_target.update_password('password')
       >>> snmp_target.update_version('SNMPv3')
       >>> snmp_target.update_auth_protocol('MD5')
       >>> snmp_target.update_auth_type('AuthPriv')

Testing SNMP target:

.. code-block:: python
       
       >>> resp = snmp_target.test()

Deleting SNMP targets:

.. code-block:: python
       
       >>> snmp_target.delete()

RSyslog Configuration
---------------------

Creating RSyslog target:

.. code-block:: python
       
       >>> rsyslog_target = system.notification_targets.create(
       ...    host='hostname',
       ...    name='syslog_target', protocol='SYSLOG', transport='TCP', facility='local0')

Querying RSyslog targets:

.. code-block:: python
       
       >>> for rsyslog_target in system.notification_targets.find(protocol='SYSLOG'):
       ...     pass

Modifying RSyslog targets:

.. code-block:: python
       
       >>> rsyslog_target.update_name('some_target')
       >>> rsyslog_target.update_host('hostname')
       >>> rsyslog_target.update_transport('UDP')
       >>> rsyslog_target.update_facility('local1')

Testing RSyslog targets:

.. code-block:: python
       
       >>> resp = rsyslog_target.test()

Deleting RSyslog targets:

.. code-block:: python
       
       >>> rsyslog_target.delete()


.. seealso:: :class:`.NotificationTarget`
