Notification Rules
==================

A **notification rule** defines which events should trigger a notification
and to which target they should be sent.

Creating Rules
--------------

Create a rule that sends all Critical/Warning events to an existing target:

.. code-block:: pycon

   >>> target = system.notification_targets.find(name="example").to_list()[0]
   >>> rule = system.notification_rules.create(
   ...     name="send_critical_and_warning",
   ...     target=target,
   ...     event_level=["CRITICAL", "WARNING"],
   ... )

Create a rule for a specific event code:

.. code-block:: pycon

   >>> target = system.notification_targets.find(protocol="SNMP").to_list()[0]
   >>> rule = system.notification_rules.create(
   ...     name="only_disk_full",
   ...     target=target,
   ...     event_code="DISK_SPACE_LOW",
   ...     event_level=["CRITICAL"],
   ... )

Filtering Events
----------------

Restrict events for an existing rule:

.. code-block:: pycon

   >>> rule = system.notification_rules.find(name="send_critical_and_warning").to_list()[0]
   >>> rule.update_include_events(["LINK_DOWN", "LINK_UP"])


Modifying Rules
---------------

.. code-block:: pycon

   >>> rule = system.notification_rules.find(name="send_critical_and_warning").to_list()[0]
   >>> rule.update_name("send_crit_only")
   >>> rule.update_event_level(["CRITICAL"])
   >>> rule.update_event_code("HOST_DOWN")
   >>> new_target = system.notification_targets.find(protocol="SYSLOG").to_list()[0]
   >>> rule.update_target(new_target)

Deleting Rules
--------------

.. code-block:: pycon

   >>> rule.delete()