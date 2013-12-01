from ..utils import TestCase

class PushRulesTest(TestCase):

    def setUp(self):
        super(PushRulesTest, self).setUp()
        self.rule_name = "push_rule1"
        self.rule = self.system.pushrules.create(name=self.rule_name)
        self.addCleanup(self.rule.delete)

    def test_push_rule_get_name(self):
        self.assertEquals(self.rule.get_name(), self.rule_name)

    def test_push_rule_enabled(self):
        self.assertTrue(self.rule.get_field('enabled'))
        self.rule.update_field("enabled", False)
        self.assertFalse(self.rule.get_field('enabled'))
