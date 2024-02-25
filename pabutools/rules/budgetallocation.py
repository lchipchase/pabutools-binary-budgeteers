from collections.abc import Iterable

from pabutools.election.instance import Project
from pabutools.rules.explanation_data import ExplanationData


class BudgetAllocation(list[Project]):
    """
    A budget allocation is the outcome of rule. It simply corresponds to a list of projects.
    Additional information can also be stored in this class, for instance for explanation purposes.

    Parameters
    ----------
        init : Iterable[:py:class:`~pabutools.election.instance.Project`], optional
            An iterable of :py:class:`~pabutools.election.instance.Project` that is used an
            initializer for the list.
        explanation_data
            An object representing additional information that has been gathered when running the rule. This can take
            any form.

    Attributes
    ----------
        explanation_data
            An object representing additional information that has been gathered when running the rule. This can take
            any form.
    """

    def __init__(
        self,
        init: Iterable[Project] = (),
        explanation_data: ExplanationData = None
    ) -> None:
        list.__init__(self, init)
        if explanation_data is None:
            if isinstance(init, BudgetAllocation):
                explanation_data = init.explanation_data
        self.explanation_data = explanation_data

    # Ensures that methods returning copies of sets cast back into BudgetAllocation
    @classmethod
    def _wrap_methods(cls, methods):
        def wrap_method_closure(method):
            def inner_method(self, *args):
                result = getattr(super(cls, self), method)(*args)
                if isinstance(result, list) and not isinstance(result, cls):
                    result = cls(init=result, explanation_data=self.explanation_data)
                return result

            inner_method.fn_name = method
            setattr(cls, method, inner_method)

        for m in methods:
            wrap_method_closure(m)


BudgetAllocation._wrap_methods(
    [
        "__add__",
        "__iadd__",
        "__imul__",
        "__mul__",
        "__reversed__",
        "__rmul__",
        "copy",
        "reverse",
        # "__getitem__",
    ]
)
