from __future__ import annotations
import os

from pabutools.rules.mes.mes_details import MESAllocationDetails

try:
    import jinja2
except ImportError:
    raise ImportError("You need to install jinja2 to use this visualisation module")

from pabutools.analysis.profileproperties import votes_count_by_project, voter_flow_matrix
from pabutools.election.instance import total_cost

ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(os.path.abspath(__file__))))

class Visualiser:
    # TODO: A future base class which can be used to define the interface for all visualisers
    pass

class MESVisualiser(Visualiser):
    # TODO make sure the variable name 'p' isn't used both in an outer loop and an inner loop at the same time.
    template = ENV.get_template('./templates/mes_round_analysis_template.html') 
    page_summary_template = ENV.get_template('./templates/mes_page_summary_template.html')

    def __init__(self, profile, instance, mes_details: MESAllocationDetails, verbose=False):
        self.profile = profile
        self.instance = instance
        self.verbose = verbose
        self.details = mes_details
        self.mes_iterations = mes_details.iterations
        if not self.mes_iterations:
            raise ValueError("No projects were selected in this election.")
        self.rounds = []

    def _calculate_rounds_dictinary(self):
        initial_budget_per_voter = float(self.instance.meta["budget"]) / float(self.instance.meta["num_votes"])
        budgetSpent = 0 
        for i in range(len(self.mes_iterations)-1):
            round = dict()
            current_iteration = self.mes_iterations[i]
            next_iteration = self.mes_iterations[i+1]
            round["_current_iteration"] = current_iteration # will be deleted before passed into the template
            round["id"] = current_iteration.selected_project.name
            round["name"] = current_iteration.selected_project.name # TODO Remove this and keep round["id"]
            data = {
                p.name: float(1/p.affordability) for p in current_iteration.get_all_projects()
            }
            round["effective_vote_count"] =  dict(sorted(data.items(), key=lambda item: item[1], reverse=True))
            round["effective_vote_count_reduction"] = {
                p.name: float(round["effective_vote_count"][p]-1/p.affordability) for p in next_iteration.get_all_projects()
            }

            # Statistics for Page Summary page
            # Get cost of winning project
            round["cost"] = current_iteration.selected_project.cost
            # Number of votes for winning project
            round["totalvotes"] = len(current_iteration.selected_project.supporter_indices)
            # Initial voter funding - the funds the supporters could've had if they hadn't spent on previous selected projects
            round["initial_voter_funding"] = initial_budget_per_voter * len(current_iteration.selected_project.supporter_indices)

            # Funding lost per round (unsorted) - A list of the total funding lost by the selected project's supporters during the previous (i-1) rounds.
            unsorted_funding_lost_per_round = {
                r: (
                    float(sum(self.mes_iterations[r].voters_budget[p] for p in current_iteration.selected_project.supporter_indices))       # Sum of supporter funds for selected project at the start of round r
                    - float(sum(self.mes_iterations[r+1].voters_budget[p] for p in current_iteration.selected_project.supporter_indices))   # Sum of supporter funds for selected project at the end of round r
                ) for r in range(0, i)
            }
            # Sort the funding lost by decreasing cost.
            round["funding_lost_per_round"] = dict(sorted(unsorted_funding_lost_per_round.items(), key = lambda x: x[1], reverse = True))

            # Final voter funding - the funds the supporters actually have (or available budget)
            round["final_voter_funding"] = float(sum(current_iteration.voters_budget[p] for p in current_iteration.selected_project.supporter_indices))
            # Get dropped projects
            dropped_projects = []
            for p in current_iteration:
                if p.discarded:
                    unsorted_funding_lost_per_round = {
                        r: (
                            float(sum(self.mes_iterations[r].voters_budget[p] for p in p.project.supporter_indices))
                            - float(sum(self.mes_iterations[r+1].voters_budget[p] for p in p.project.supporter_indices))
                        ) for r in range(0, i)
                    }

                    rejected = {
                        "id": p.project.name,
                        "cost": p.project.cost,
                        "effective_vote_count": float(1/p.project.affordability),
                        "totalvotes": len(p.project.supporter_indices),
                        "initial_voter_funding": initial_budget_per_voter * len(p.project.supporter_indices),
                        "funding_lost_per_round": dict(sorted(unsorted_funding_lost_per_round.items(), key = lambda x: x[1], reverse = True)),
                        "final_voter_funding": float(sum(current_iteration.voters_budget[p] for p in p.project.supporter_indices))
                    }
                    dropped_projects.append(rejected)
            round["dropped_projects"] = dropped_projects
            budgetSpent += current_iteration.selected_project.cost
            round["remaining_budget"] = float(self.instance.meta["budget"]) - budgetSpent
            self.rounds.append(round)

        # Final round
        unsorted_funding_lost_per_round = {
            r: (
                float(sum(self.mes_iterations[r].voters_budget[p] for p in self.mes_iterations[-1].selected_project.supporter_indices))
                - float(sum(self.mes_iterations[r+1].voters_budget[p] for p in self.mes_iterations[-1].selected_project.supporter_indices))
            ) for r in range(0, len(self.mes_iterations) - 1)
        }
            
        dropped_projects = []
        for p in self.mes_iterations[-1]:
            if p.discarded:
                unsorted_funding_lost_per_round = {
                    r: (
                        float(sum(self.mes_iterations[r].voters_budget[p] for p in p.project.supporter_indices))
                        - float(sum(self.mes_iterations[r+1].voters_budget[p] for p in p.project.supporter_indices))
                    ) for r in range(0, len(self.mes_iterations) - 1)
                }
                
                rejected = {
                    "id": p.project.name,
                    "cost": p.project.cost,
                    "effective_vote_count": float(1/p.project.affordability),
                    "totalvotes": len(p.project.supporter_indices),
                    "initial_voter_funding": initial_budget_per_voter * len(p.project.supporter_indices),
                    "funding_lost_per_round": dict(sorted(unsorted_funding_lost_per_round.items(), key = lambda x: x[1], reverse = True)),
                    "final_voter_funding": float(sum(self.mes_iterations[-1].voters_budget[p] for p in p.project.supporter_indices))
                }
                dropped_projects.append(rejected)
        
        budgetSpent += self.mes_iterations[-1].selected_project.cost
        data = {
                p.name: float(1/p.affordability) for p in self.mes_iterations[-1].get_all_projects()
            }
        self.rounds.append({
            "name": self.mes_iterations[-1].selected_project.name,
            "_current_iteration": self.mes_iterations[-1],
            "effective_vote_count": dict(sorted(data.items(), key=lambda item: item[1], reverse=True)),
            "effective_vote_count_reduction": {p.name: 0 for p in self.mes_iterations[-1].get_all_projects()},
            "cost": self.mes_iterations[-1].selected_project.cost,
            "totalvotes": len(self.mes_iterations[-1].selected_project.supporter_indices),
            "initial_voter_funding": initial_budget_per_voter * len(self.mes_iterations[-1].selected_project.supporter_indices),
            "funding_lost_per_round": dict(sorted(unsorted_funding_lost_per_round.items(), key = lambda x: x[1], reverse = True)),
            "final_voter_funding": float(sum(self.mes_iterations[-1].voters_budget[p] for p in self.mes_iterations[-1].selected_project.supporter_indices)),
            "dropped_projects": dropped_projects,
            "remaining_budget": float(self.instance.meta["budget"]) - budgetSpent
        })

    def _calculate_pie_charts(self, projectVotes):
        winners = []
        for round in self.rounds:
            pie_chart_items = []
            round["id"] = round["name"] # TODO: Remove either 'id' or 'name' from the data structure
            selected = round["name"]
            winners.append(selected)
            for project in projectVotes:
                if project.name not in winners:
                    round_voters = round["voter_flow"][project.name][selected]
                    non_round_voters = projectVotes[project.name] - round_voters
                    reduction = self._calculate_avg_voter_budget(round["_current_iteration"].voters_budget, self._get_voters_for_project(project)) - self._calculate_avg_voter_budget(round["_current_iteration"].voters_budget_after_selection, self._get_voters_for_project(project))
                    pie_chart_item = {
                        "project": project.name,
                        "roundVoters": round_voters,
                        "nonRoundVoters": non_round_voters,
                        "reduction": reduction
                    }
                    pie_chart_items.append(pie_chart_item)

            pie_chart_items = sorted(pie_chart_items, key=lambda x: x["roundVoters"], reverse=True)
            round["pie_chart_items"] = [pie_chart_items]
            round["pie_chart_triplet"] = [pie_chart_items[i:i + 3] for i in range(0, len(pie_chart_items), 3)]

    def _calculate_avg_voter_budget(self, voters_budget, supporters):
        return sum(voters_budget[s] for s in supporters) / len(supporters)

    def _get_voters_for_project(self, project):
        for project_details in self.details.get_all_project_details():
            if project_details.project == project:
                return project_details.project.supporter_indices

    def _calculate(self):
        self._calculate_rounds_dictinary()
        projectVotes = votes_count_by_project(self.profile)
        for round in self.rounds:
            round["voter_flow"] = voter_flow_matrix(self.instance, self.profile)
        self._calculate_pie_charts(projectVotes)

    def render(self, outcome, output_folder_path):
        self._calculate()
        for round in self.rounds:
            del round["_current_iteration"]
        if self.verbose:
            print(self.rounds)

        # Round by Round
        round_analysis_page_output = MESVisualiser.template.render( # TODO: Some redudant data is being passed to the template that can be calculated within template directly
            election_name=self.instance.meta["description"] if "description" in self.instance.meta else "No description provided.", 
            # total_votes=sum(votes_count_by_project(self.profile).values()),
            rounds=self.rounds, 
            projects=self.instance.project_meta,
            number_of_elected_projects=len(outcome),
            number_of_unelected_projects=len(self.instance) - len(outcome),
            spent=total_cost(p for p in self.instance if p.name in outcome),
            currency=self.instance.meta["currency"] if "currency" in self.instance.meta else "CUR",
            budget=self.instance.meta["budget"],
            total_votes=self.instance.meta["num_votes"]
        )

        # Page Summary
        summary_page_output = MESVisualiser.page_summary_template.render( # TODO: Some redudant data is being passed to the template that can be calculated within template directly
            election_name=self.instance.meta["description"] if "description" in self.instance.meta else "No description provided.", 
            rounds=self.rounds, 
            projects=self.instance.project_meta,
            number_of_elected_projects=len(outcome),
            number_of_unelected_projects=len(self.instance) - len(outcome),
            spent=total_cost(p for p in self.instance if p.name in outcome),
            budget=self.instance.meta["budget"],
            total_votes=self.instance.meta["num_votes"]
        )
        if not os.path.exists(output_folder_path):
            os.makedirs(output_folder_path)
        with open(f"{output_folder_path}/round_analysis.html", "w", encoding="utf-8") as o:
            o.write(round_analysis_page_output)
        with open(f"{output_folder_path}/summary.html", "w", encoding="utf-8") as o:
            o.write(summary_page_output)