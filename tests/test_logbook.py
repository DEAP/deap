import unittest

from deap import tools


class LogbookTest(unittest.TestCase):

    def setUp(self):
        self.logbook = tools.Logbook()
        print()

    def test_slice_deletion(self):
        slices = (slice(None, 3), slice(2, 7), slice(None, None, 2),
                  slice(None, None, -1), slice(7, 1, -2), slice(4, 4),
                  slice(-7, -1), slice(None, None, -3))
        for key in slices:
            with self.subTest(key=key):
                log = tools.Logbook()
                for gen in range(5):
                    log.record(gen=gen, fitness={'detail': {'avg': gen * 2}})
                for chapter in (log, log.chapters['fitness'],
                                log.chapters['fitness'].chapters['detail']):
                    chapter.stream
                for gen in range(5, 10):
                    log.record(gen=gen, fitness={'detail': {'avg': gen * 2}})
                expected = list(range(10))
                del expected[key]
                consumed = [gen for gen in expected if gen < 5]

                del log[key]

                self.assertEqual(log.select("gen"), expected)
                self.assertEqual(log.chapters['fitness'].select("gen"), expected)
                detail = log.chapters['fitness'].chapters['detail']
                self.assertEqual(detail.select("gen"), expected)
                self.assertEqual(detail.select("avg"), [gen * 2 for gen in expected])
                for chapter in (log, log.chapters['fitness'], detail):
                    self.assertEqual(chapter.buffindex, len(consumed))
                if expected:
                    self.assertEqual(len(log.stream.splitlines()),
                                     len(expected) - len(consumed))

    def test_multi_chapters(self):
        self.logbook.record(gen=0, evals=100, fitness={'obj 1': {'avg': 1.0, 'max': 10},
                                                       'obj 2': {'avg': 1.0, 'max': 10}},
                            length={'avg': 1.0, 'max': 30},
                            test={'avg': 1.0, 'max': 20})
        self.logbook.record(gen=0, evals=100, fitness={'obj 1': {'avg': 1.0, 'max': 10},
                                                       'obj 2': {'avg': 1.0, 'max': 10}},
                            length={'avg': 1.0, 'max': 30},
                            test={'avg': 1.0, 'max': 20})
        print(self.logbook.stream)

    def test_one_chapter(self):
        self.logbook.record(gen=0, evals=100, fitness={'avg': 1.0, 'max': 10})
        self.logbook.record(gen=0, evals=100, fitness={'avg': 1.0, 'max': 10})
        print(self.logbook.stream)

    def test_one_big_chapter(self):
        self.logbook.record(gen=0, evals=100, fitness={'obj 1': {'avg': 1.0, 'max': 10}, 'obj 2': {'avg': 1.0, 'max': 10}})
        self.logbook.record(gen=0, evals=100, fitness={'obj 1': {'avg': 1.0, 'max': 10}, 'obj 2': {'avg': 1.0, 'max': 10}})
        print(self.logbook.stream)

    def test_no_chapters(self):
        self.logbook.record(gen=0, evals=100, **{'avg': 1.0, 'max': 10})
        self.logbook.record(gen=0, evals=100, **{'avg': 1.0, 'max': 10})
        print(self.logbook.stream)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(LogbookTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
