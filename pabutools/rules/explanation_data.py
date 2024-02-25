class ExplanationData:
    pass

class MESData(ExplanationData):
    def __init__(self):
        self.rounds = []

    def record_round_start(self, projects):
        round = {
            "effective_vote_count": {
                p.name: float(1/p.affordability) for p in projects
            }
        }
        self.rounds.append(round)

    def record_round_end(self, projects, selected_project):
        self.rounds[-1]["effective_vote_count_reduction"] = {
            p.name: float(self.rounds[-1]["effective_vote_count"][p]-1/p.affordability) for p in projects
        }
        self.rounds[-1]["name"] = selected_project.name