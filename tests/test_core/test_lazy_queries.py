from ..utils import TestCase

class LazyQueryTest(TestCase):
    PAGE_SIZE = 10

    def setUp(self):
        super(LazyQueryTest, self).setUp()
        self.result = self.system.components.find().page_size(self.PAGE_SIZE)

    def test_lazy_query_out_of_bounds_with_first_checking_length(self):
        self.assertGreater(len(self.result), self.PAGE_SIZE)
        with self.assertRaises(IndexError):
            self.result[len(self.result) + 1]

    def test_lazy_query_out_of_bounds_without_first_checking_length(self):
        with self.assertRaises(IndexError):
            self.result[len(self.result) + 1]

    def test_lazy_query(self):
        self.PAGE_SIZE = 10
        pages_total = (len(self.result) // self.PAGE_SIZE)
        if float(len(self.result)) / self.PAGE_SIZE != 0:
            pages_total += 1

        self.assertGreater(len(self.result), self.PAGE_SIZE)


        self.assert_fetched([0])

        self.assertIsNotNone(self.result[self.PAGE_SIZE+1])

        self.assert_fetched([0, 1])

    def assert_fetched(self, pages):
        for i in range(0, len(self.result), self.PAGE_SIZE):
            if i // self.PAGE_SIZE in pages:
                self.assertIsNotNone(self.result._fetched[i], "Object {} not fetched as expected".format(i))
            else:
                self.assertIsNone(self.result._fetched.get(i), "Object {} unexpectedly fetched".format(i))
