import pytest


def test_smtp_targets_query(infinibox, smtp_target):
    pass

@pytest.mark.parametrize('recipients', [
    'user@gmail.com', # we support single recipients
    ['user@gmail.com', 'bla@domain.com'], # as well as multiples
])
def test_smtp_target_test(infinibox, smtp_target, recipients):
    smtp_target.test(recipients=recipients)

@pytest.fixture
def smtp_target(infinibox):
    return list(infinibox.notification_targets.find(protocol='SMTP'))[0]
