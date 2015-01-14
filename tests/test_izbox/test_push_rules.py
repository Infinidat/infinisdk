import pytest


def test_push_rule_get_name(izbox, rule, rule_name):
    assert rule.get_name() == rule_name


def test_push_rule_enabled(izbox, rule):
    pytest.skip()
    assert rule.get_field('enabled')
    rule.update_field("enabled", False)
    assert (not rule.get_field('enabled'))


@pytest.fixture
def rule(izbox, rule_name):
    return izbox.pushrules.create(name=rule_name)


@pytest.fixture
def rule_name():
    return "rule_name"
