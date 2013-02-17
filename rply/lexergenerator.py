import re

try:
    import rpython
    from rpython.annotator import model
    from rpython.annotator.bookkeeper import getbookkeeper
    from rpython.rtyper.extregistry import ExtRegistryEntry
    from rpython.tool.pairtype import pairtype
except ImportError:
    rpython = None

from rply.lexer import Lexer


class Rule(object):
    def __init__(self, name, pattern):
        self.name = name
        self.re = re.compile(pattern)

    def _freeze_(self):
        return True

    def matches(self, s, pos):
        m = self.re.match(s, pos)
        return Match(*m.span(0)) if m is not None else None


class Match(object):
    _attrs_ = ["start", "end"]

    def __init__(self, start, end):
        self.start = start
        self.end = end


class LexerGenerator(object):
    def __init__(self):
        self.rules = []

    def add(self, name, pattern):
        self.rules.append(Rule(name, pattern))

    def build(self):
        return Lexer(self.rules)

if rpython:
    class RuleEntry(ExtRegistryEntry):
        _type_ = Rule

        def compute_annotation(self, *args):
            return SomeRule()

    class SomeRule(model.SomeObject):
        def method_matches(self, s_s, s_pos):
            assert model.SomeString().contains(s_s)
            assert model.SomeInteger().contains(s_pos)

            bk = getbookkeeper()
            init_pbc = bk.immutablevalue(Match.__init__)
            bk.emulate_pbc_call((self, "match_init"), init_pbc, [
                model.SomeInstance(bk.getuniqueclassdef(Match)),
                model.SomeInteger(nonneg=True),
                model.SomeInteger(nonneg=True)
            ])
            return model.SomeInstance(getbookkeeper().getuniqueclassdef(Match), can_be_None=True)

    class __extend__(pairtype(SomeRule, SomeRule)):
        def union((self, other)):
            return self
