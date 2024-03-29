from __future__ import annotations


from pabutools.election.instance import Project
from pabutools.rules.budgetallocation import AllocationDetails
from pabutools.utils import Numeric


class GreedyWelfareAllocationDetails(AllocationDetails):
    def __init__(self, voter_multiplicity: list[int]):
        super().__init__()
        self.voter_multiplicity: list[int] = voter_multiplicity
        self.iterations: list[GreedyWelfareIteration] = []

    def get_all_project_details(self) -> list["GreedyWelfareProjectDetails"]:
        res = []
        for iteration in self.iterations:
            for proj_detail in iteration:
                if proj_detail not in res:
                    res.append(proj_detail)
        return res
    
    def get_all_selected_projects(self) -> list[Project]:
        return [iteration.selected_project for iteration in self.iterations]

class GreedyWelfareProjectDetails:
    def __init__(
        self,
        project: Project,
        iteration: "GreedyWelfareIteration",
        discarded: bool = None,
        effective_vote_count_reduced: bool = None,
    ):
        self.project: Project = project
        self.iteration: "GreedyWelfareIteration" = iteration
        self.discarded: bool = discarded

    def was_picked(self):
        if self.iteration.selected_project != None:
            return self.project == self.iteration.selected_project
        return None

    def __eq__(self, other):
        return self.project == other.project

    def __str__(self):
        return f"GreedyWelfareProjectDetails[Project: {self.project.name}]"

    def __repr__(self):
        return f"GreedyWelfareProjectDetails[Project: {self.project.name}]"


class GreedyWelfareIteration(list[GreedyWelfareProjectDetails]):
    def __init__(
        self,
        selected_project: Project | None = None,
    ):
        self.selected_project: Project | None = selected_project
        super().__init__()

    def update_project_details_as_discarded(self, project: Project):
        """Updates the project details as discarded during this iteration."""
        project_details = self[self.index(project)]
        project_details.discarded = True  

    def get_all_projects(self):
        return [project_details.project for project_details in self]

    def __str__(self):
        return f"GreedyWelfareIteration[{[project for project in self]}]"

    def __repr__(self):
        return f"GreedyWelfareIteration[{[project for project in self]}]"
