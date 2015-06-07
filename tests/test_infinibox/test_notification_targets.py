import pytest


def test_smtp_targets_query(infinibox, smtp_target):
    pass


def test_snmp_define(infinibox, snmp_target):
    pass


def test_snmp_modify(infinibox, snmp_target):
    pass


def test_snmp_query(infinibox, snmp_target):
    assert snmp_target in list(
        infinibox.notification_targets.find(protocol='SNMP'))


def test_snmp_remove(infinibox, snmp_target):
    snmp_target.delete()
    assert not snmp_target.is_in_system()


def test_snmp_rename(infinibox, snmp_target):
    snmp_target.update_name('new_name')
    assert snmp_target.get_name() == 'new_name'


def test_snmp_test(infinibox, snmp_target):
    snmp_target.test()


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
