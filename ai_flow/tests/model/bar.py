from ai_flow.tests.model import foo


class Bar(object):
    def method_2(self):
        tmp = foo.Foo()
        return tmp.method_1()