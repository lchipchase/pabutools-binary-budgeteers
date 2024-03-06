import os

try:
    import jinja2
except ImportError:
    raise ImportError("You need to install jinja2 to use the visualisation module")

from pabutools.analysis.profileproperties import votes_count_by_project, voter_flow_matrix
from pabutools.election.instance import total_cost
from pabutools.rules.explanation_data import MESData

ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(os.path.abspath(__file__))))

class Visualiser:
    # TODO: A future base class which will be used to define the interface for all visualisers
    pass

class MESVisualiser(Visualiser):
    template = ENV.get_template('./templates/mes_template.html') 
    
    def __init__(self, profile, instance, round_data: MESData, verbose=False):
        self.profile = profile
        self.instance = instance
        self.verbose = verbose
        self.rounds = round_data.rounds

    def _calculate_pie_charts(self, projectVotes):
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
            # if len(pie_chart_items) > 3:
            #     pie_chart_items = pie_chart_items[:3]
            round["pie_chart_items"] = [pie_chart_items]
            round["pie_chart_triplet"] = [pie_chart_items[i:i + 3] for i in range(0, len(pie_chart_items), 3)]

    def _calculate(self):
        del self.rounds[-1] # Remove the last round, as it is just empty
        projectVotes = votes_count_by_project(self.profile)
        for round in self.rounds:
            round["voter_flow"] = voter_flow_matrix(self.instance, self.profile)
        self._calculate_pie_charts(projectVotes)

    def render(self, outcome, output_file_path):
        self._calculate()
        if self.verbose:
            print(self.rounds)
        rendered_output = MESVisualiser.template.render( # TODO: Some redudant data is being passed to the template that can be calculated within template directly
            election_name=self.instance.meta["description"] if "description" in self.instance.meta else "No description provided.", 
            total_votes=sum(votes_count_by_project(self.profile).values()),
            rounds=self.rounds, 
            projects=list(self.instance),
            number_of_elected_projects=len(outcome),
            number_of_unelected_projects=len(self.instance) - len(outcome),
            spent=total_cost(p for p in self.instance if p.name in outcome),
            budget=int(self.instance.meta["budget"])
        )
        with open(output_file_path, "w") as o:
            o.write(rendered_output)
