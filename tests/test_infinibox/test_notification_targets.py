import pytest


def test_smtp_targets_query(smtp_target):  # pylint: disable=unused-argument
    pass


def test_snmp_define(snmp_target):  # pylint: disable=unused-argument
    pass


def test_snmp_modify(snmp_target):  # pylint: disable=unused-argument
    pass


def test_snmp_query(infinibox, snmp_target):
    assert snmp_target in infinibox.notification_targets.find(protocol='SNMP').to_list()


def test_snmp_remove(snmp_target):
    snmp_target.delete()
    assert not snmp_target.is_in_system()


def test_snmp_rename(snmp_target):
    snmp_target.update_name('new_name')
    assert snmp_target.get_name() == 'new_name'


def test_snmp_test(snmp_target):
    snmp_target.test()


def test_rsyslog_define(rsyslog_target):  # pylint: disable=unused-argument
    pass


def test_rsyslog_modify(rsyslog_target):  # pylint: disable=unused-argument
    pass


def test_rsyslog_query(infinibox, rsyslog_target):
    assert rsyslog_target in list(
        infinibox.notification_targets.find(protocol='SYSLOG'))


def test_rsyslog_remove(rsyslog_target):
    rsyslog_target.delete()
    assert not rsyslog_target.is_in_system()


def test_rsyslog_rename(rsyslog_target):
    rsyslog_target.update_name('new_name')
    assert rsyslog_target.get_name() == 'new_name'


def test_rsyslog_test(rsyslog_target):
    rsyslog_target.test()


@pytest.mark.parametrize('recipients', [
    'user@gmail.com',  # we support single recipients
    ['user@gmail.com', 'bla@domain.com'],  # as well as multiples
])
def test_smtp_target_test(smtp_target, recipients):
    smtp_target.test(recipients=recipients)


@pytest.fixture
def smtp_target(infinibox):
    return infinibox.notification_targets.find(protocol='SMTP').to_list()[0]


@pytest.fixture
def snmp_target(infinibox):
    return infinibox.notification_targets.create(
        protocol='SNMP', host='somehost', private_key='private',
        username='user', password='password',
        private_protocol='AES',
        version='SNMPv3', engine='0x1000000000', auth_type='AuthPriv', auth_protocol='MD5')


@pytest.fixture
def rsyslog_target(infinibox):
    return infinibox.notification_targets.create(
        host='hostname', protocol='SYSLOG', transport='TCP', facility='local0')
