from ..utils import InfiniBoxTestCase

class EventsTest(InfiniBoxTestCase):

    def test_create_custom_event(self):
        description = 'test events'
        event_from_post = self.system.events.create_custom_event(description=description)
        event_from_list = self.system.events.get_last_events(1)[0].get_fields()
        self.assertEquals(event_from_post['description'], description)
        self.assertEquals(event_from_list['description'], description)
        self.assertEquals(event_from_list['code'], "CUSTOM_INFO_EVENT")

    def test_create_custom_event_with_data(self):
        description = 'test events - {param}'
        event_data = dict(name='param', value='bla', type="string")
        event_from_post = self.system.events.create_custom_event(description=description,
                                                                 data=[event_data])

        data_from_post = event_from_post['data'][0]
        self.assertEqual(event_data['name'], data_from_post['name'])
        self.assertEqual(event_data['type'], data_from_post['type'])
        self.assertEqual(event_data['value'], data_from_post['value'])

        event_from_list = self.system.events.get_last_event().get_fields()
        description = description.replace("{param}", event_data["value"])
        self.assertEquals(event_from_post['description'], description)
        self.assertEquals(event_from_list['description'], description)
        self.assertEquals(event_from_list['code'], "CUSTOM_INFO_EVENT")

class EmailRuleTest(InfiniBoxTestCase):
    def setUp(self):
        super(EmailRuleTest, self).setUp()
        self.rule = self.system.emailrules.create()
        self.addCleanup(self.rule.delete)

    def test_get_name(self):
        self.assertTrue(self.rule.get_name().startswith('rule_'))

    def test_get_all(self):
        self.assertIn(self.rule, self.system.emailrules.get_all())
