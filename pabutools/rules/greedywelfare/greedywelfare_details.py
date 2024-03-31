from __future__ import annotations


from pabutools.election.instance import Project
from pabutools.rules.budgetallocation import AllocationDetails
from pabutools.utils import Numeric


class GreedyWelfareAllocationDetails(AllocationDetails):
    def __init__(self):
        self.projects: list[GreedyWelfareProjectDetails] = []
        super().__init__()

    def mark_as_selected(self, project: Project, remaining_budget: Numeric):
        """Marks the project as selected and records the remaining budget."""
        proj = self.projects[self.projects.index(GreedyWelfareProjectDetails(project))]
        proj.remaining_budget = remaining_budget
        proj.discarded = False

class GreedyWelfareProjectDetails:
    def __init__(
        self,
        project: Project,
        score: Numeric = None,
        discarded: bool = True,
        remaining_budget: Numeric = None,
    ):
        self.project: Project = project
        self.score = score
        self.discarded: bool = discarded
        self.remaining_budget: Numeric = remaining_budget

    def __eq__(self, other):
        return self.project == other.project

    def __str__(self):
        return f"GreedyWelfareProjectDetails[Project: {self.project.name}, Discarded: {self.discarded}, Remaining Budget: {self.remaining_budget}]"

    def __repr__(self):
        return f"GreedyWelfareProjectDetails[Project: {self.project.name}, Discarded: {self.discarded}, Remaining Budget: {self.remaining_budget}]"
