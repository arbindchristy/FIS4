"""Explicit external-reference boundary; portable runs never load legacy sources."""
import unittest


def is_external(test):
    name = test.id()
    return (".LegacyParityTests." in name or
            name.endswith(".MetricTests.test_true_null_commands_do_not_reconcile_and_match_legacy"))


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def select(suite, mode):
    tests = list(flatten(suite))
    external = [test for test in tests if is_external(test)]
    portable = [test for test in tests if not is_external(test)]
    return unittest.TestSuite(portable if mode == "Portable" else tests), len(portable), len(external)
