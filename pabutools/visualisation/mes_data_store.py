import os

import jinja2

from pabutools.analysis.profileproperties import votes_count_by_project, voter_flow_matrix
from pabutools.election.instance import total_cost

ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(os.path.abspath(__file__))))

class DataStore:
    # TODO: Once we support multiple voting rules we can move shared calculations to the parent
    pass

class MESDataStore(DataStore):
    template = ENV.get_template('./templates/mes_template.html') 
    
    def __init__(self, profile, instance, verbose=False):
        self.profile = profile
        self.instance = instance
        self.verbose = verbose
        self.rounds = []

    def record_round_start(self, projects):
        round = {
            "effective_vote_count": {
                p.name: float(1/p.affordability) for p in projects
            }
        }
        self.rounds.append(round)

    def record_round_end(self, projects, winner):
        self.rounds[-1]["effective_vote_count_reduction"] = {
            p.name: float(self.rounds[-1]["effective_vote_count"][p]-1/p.affordability) for p in projects
        }
        self.rounds[-1]["name"] = winner.name

    def __calculate_pie_charts(self, projectVotes):
        winners = []
        for round in self.rounds:
            pie_chart_items = []
            round["id"] = round["name"] # TODO: Remove either 'id' or 'name' from the data structure
            selected = round["name"]
            winners.append(selected)
            for project in self.instance:
                if project.name not in winners:
                    round_voters = round["voter_flow"][project.name][selected]
                    non_round_voters = projectVotes[project.name] - round_voters
                    reduction = 0
                    if  project.name in round["effective_vote_count_reduction"]:
                        reduction = round["effective_vote_count_reduction"][project.name]
                    pie_chart_item = {
                        "project": project.name,
                        "roundVoters": round_voters,
                        "nonRoundVoters": non_round_voters,
                        "reduction": reduction
                    }
                    pie_chart_items.append(pie_chart_item)

            pie_chart_items = sorted(pie_chart_items, key=lambda x: x["roundVoters"], reverse=True)
            if len(pie_chart_items) > 3:
                pie_chart_items = pie_chart_items[:3]
            round["pie_chart_items"] = [pie_chart_items]

    def __calculate(self):
        del self.rounds[-1] # Remove the last round, as it is just empty
        projectVotes = votes_count_by_project(self.profile)
        for round in self.rounds:
            round["voter_flow"] = voter_flow_matrix(self.instance, self.profile)
        self.__calculate_pie_charts(projectVotes)

    def render(self, outcome, output_file_path):
        self.__calculate()
        if self.verbose:
            print(self.rounds)
        rendered_output = MESDataStore.template.render( # TODO: Some redudant data is being passed to the template that can be calculated within template directly
            election_name=self.instance.meta["description"] if "description" in self.instance.meta else "No description provided.", 
            rounds=self.rounds, 
            projects=list(self.instance),
            number_of_elected_projects=len(outcome),
            number_of_unelected_projects=len(self.instance) - len(outcome),
            spent=total_cost(p for p in self.instance if p.name in outcome),
            budget=self.instance.meta["budget"]
        )
        with open(output_file_path, "w") as o:
            o.write(rendered_output)
