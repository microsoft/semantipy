from semantipy.dispatch_utils import get_overloaded_types_and_args
from semantipy import Semantics


def test_dispatch_utils():

    def return_self(self, *args, **kwargs):
        return self

    def return_not_implemented(self, *args, **kwargs):
        return NotImplemented

    class A:
        __semantic_function__ = return_self

    class B(A):
        __semantic_function__ = return_self

    class C(A):
        __semantic_function__ = return_self

    class D:
        __semantic_function__ = return_self

    a = A()
    b = B()
    c = C()
    d = D()

    def get_overloaded_args(relevant_args):
        types, args = get_overloaded_types_and_args(relevant_args)
        return args

    assert get_overloaded_args([1]) == []
    assert get_overloaded_args([a]) == [a]
    assert get_overloaded_args([a, 1]) == [a]
    assert get_overloaded_args([a, a, a]) == [a]
    assert get_overloaded_args([a, d, a]) == [a, d]
    assert get_overloaded_args([a, b]) == [b, a]
    assert get_overloaded_args([b, a]) == [b, a]
    assert get_overloaded_args([a, b, c]) == [b, c, a]
    assert get_overloaded_args([a, c, b]) == [c, b, a]

    class SubSemantics(Semantics):
        __semantic_function__ = return_self

    array = Semantics()
    assert get_overloaded_types_and_args([array]) == ([Semantics], [])
    assert get_overloaded_types_and_args([a, array, 1]) == ([A, Semantics], [a])

    subarray = SubSemantics()
    assert get_overloaded_args([array, subarray]) == [subarray]
    assert get_overloaded_args([subarray, array]) == [subarray]


if __name__ == "__main__":
    test_dispatch_utils()
