import pytest
from ..conftest import relevant_from_version


@relevant_from_version('2.0')
def test_smtp_targets_query(infinibox, smtp_target):
    pass


@relevant_from_version('2.0')
def test_snmp_define(infinibox, snmp_target):
    pass


@relevant_from_version('2.0')
def test_snmp_modify(infinibox, snmp_target):
    pass


@relevant_from_version('2.0')
def test_snmp_query(infinibox, snmp_target):
    assert snmp_target in list(
        infinibox.notification_targets.find(protocol='SNMP'))


@relevant_from_version('2.0')
def test_snmp_remove(infinibox, snmp_target):
    snmp_target.delete()
    assert not snmp_target.is_in_system()


@relevant_from_version('2.0')
def test_snmp_rename(infinibox, snmp_target):
    snmp_target.update_name('new_name')
    assert snmp_target.get_name() == 'new_name'


@relevant_from_version('2.0')
def test_snmp_test(infinibox, snmp_target):
    snmp_target.test()


@relevant_from_version('2.0')
def test_rsyslog_define(infinibox, rsyslog_target):
    pass


@relevant_from_version('2.0')
def test_rsyslog_modify(infinibox, rsyslog_target):
    pass


@relevant_from_version('2.0')
def test_rsyslog_query(infinibox, rsyslog_target):
    assert rsyslog_target in list(
        infinibox.notification_targets.find(protocol='SYSLOG'))


@relevant_from_version('2.0')
def test_rsyslog_remove(infinibox, rsyslog_target):
    rsyslog_target.delete()
    assert not rsyslog_target.is_in_system()


@relevant_from_version('2.0')
def test_rsyslog_rename(infinibox, rsyslog_target):
    rsyslog_target.update_name('new_name')
    assert rsyslog_target.get_name() == 'new_name'


@relevant_from_version('2.0')
def test_rsyslog_test(infinibox, rsyslog_target):
    rsyslog_target.test()


@relevant_from_version('2.0')
@pytest.mark.parametrize('recipients', [
    'user@gmail.com',  # we support single recipients
    ['user@gmail.com', 'bla@domain.com'],  # as well as multiples
])
def test_smtp_target_test(infinibox, smtp_target, recipients):
    smtp_target.test(recipients=recipients)


@pytest.fixture
def smtp_target(infinibox):
    return list(infinibox.notification_targets.find(protocol='SMTP'))[0]


@pytest.fixture
def snmp_target(infinibox):
    return infinibox.notification_targets.create(
        name='snmp_target', protocol='SNMP', host='somehost', private_key='private',
        username='user', password='password',
        private_protocol='AES',
        version='SNMPv3', engine='engine', auth_type='AuthPriv', auth_protocol='MD5')


@pytest.fixture
def rsyslog_target(infinibox):
    return infinibox.notification_targets.create(
        host='hostname',
        name='syslog_target', protocol='SYSLOG', transport='TCP', facility='local0')
