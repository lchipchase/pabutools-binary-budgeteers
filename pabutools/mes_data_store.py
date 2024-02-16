import jinja2
import os
import pandas as pd

class MESDataStore:

    pairwise_dict = {}

    def __init__(self, profile, instance):
        self.profile = profile
        self.instance = instance
        self.rounds = []
        self.projects = {}

    def record_round_start(self, projects):
        # Could move most of this to a later calculate method that can be called during render to avoid taking up too much time during MES loop
        round = {
            "effective_vote_count": {
                p.name: float(1/p.affordability) for p in projects
            }
        }
        if len(self.rounds) > 0: 
            self.rounds[-1]["name"] = (self.rounds[-1]["effective_vote_count"].keys() - round["effective_vote_count"].keys()).pop()
            if self.rounds[-1]["name"] in self.rounds[-1]["effective_vote_count_reduction"]:
                del self.rounds[-1]["effective_vote_count_reduction"][self.rounds[-1]["name"]]
        self.rounds.append(round)

    def record_round_end(self, projects):
        self.rounds[-1]["effective_vote_count_reduction"] = {
            p.name: float(self.rounds[-1]["effective_vote_count"][p]-1/p.affordability) for p in projects
        }

    def __get_project_counts(self):
        # Creating a dictionary to count the occurrences
        project_votes = {}

        # Function to update the project_votes dictionary
        def update_votes(project_list):
            for project_id in project_list:
                if project_id in project_votes:
                    project_votes[project_id] += 1
                else:
                    project_votes[project_id] = 1

        for prof in self.profile:
            update_votes(list(prof))

        return project_votes


    def __get_pairwise_matrix(self, id_to_index_dict):
        # Initialize a dictionary to store pairwise interactions
        pairwise_interactions = pairwise_interactions = [[0 for _ in range(len(id_to_index_dict))] for _ in range(len(id_to_index_dict))]
        # Function to update pairwise interactions
        def update_interactions(vote_list):
            for i in range(len(vote_list)):
                for j in range(i + 1, len(vote_list)):
                    if vote_list[i] != vote_list[j]:
                        pairwise_interactions[id_to_index_dict[vote_list[i]]][id_to_index_dict[vote_list[j]]] += 1
                        pairwise_interactions[id_to_index_dict[vote_list[j]]][id_to_index_dict[vote_list[i]]] += 1
                    else:
                        pairwise_interactions[id_to_index_dict[vote_list[i]]][id_to_index_dict[vote_list[j]]] += 1

        # Process each vote list
        for vote in self.profile:
            update_interactions(list(vote))

        return pairwise_interactions


    def __calculate_pairwise(self):
        id_to_index_dict = {}
        pairwise_dict = {}
        projectsList = list(self.instance)
        for i in range(len(projectsList)):
            id_to_index_dict[projectsList[i]] = i

        pairwise_project_matrix = self.__get_pairwise_matrix(id_to_index_dict)
        for project in projectsList:
            pairwise_dict["proj" +str(project)] = str(project)
            for projectPair in projectsList:
                pairCount = pairwise_project_matrix[id_to_index_dict[project]][id_to_index_dict[projectPair]]
                myString = "proj"+str(project)+"to"+str(projectPair)
                pairwise_dict[myString] = pairCount
        return pairwise_dict 
    
    def __filter_voter_flows(self, voter_flow, projects_to_remove):
        # This function is not currently used, but will be vital when we have to filter out projects that have been removed
        # And projects that are not as relevant
        filtered_dict = {
            outer_key: {inner_key: value for inner_key, value in outer_value.items() if inner_key not in projects_to_remove}
            for outer_key, outer_value in voter_flow.items() if outer_key not in projects_to_remove
        }

        return filtered_dict

    def __calculate_voter_flow(self):
        voter_flow = {}
        projectsList = list(self.instance)

        for project in projectsList:
            voter_flow[str(project)] = {}
            for other_project in projectsList:
                voter_flow[str(project)][str(other_project)] = 0

        def update_voter_flow(vote_list):
            for i in range(len(vote_list)):
                for j in range(i + 1, len(vote_list)):
                    voter_flow[str(vote_list[i])][str(vote_list[j])] += 1
                    voter_flow[str(vote_list[j])][str(vote_list[i])] += 1
            if len(vote_list) == 1:
                voter_flow[str(vote_list[0])][str(vote_list[0])] += 1

        for vote in self.profile:
            update_voter_flow(list(vote))
        
        return voter_flow
    
    def __calculate_voters(self, project, selected, vote_flow, projectVotes):
        round_voters = vote_flow[project.name][selected]
        non_round_voters = projectVotes - round_voters
        return round_voters, non_round_voters

    def __calculate_pie_charts(self, projectVotes):
        winners = []

        for round in self.rounds:
            pie_chart_items = []

            # The last round does not have a name
            if "name" in round:
                round["id"] = round["name"]
                selected = round["name"]
                winners.append(selected)

                for project in self.instance:
                    if project.name not in winners:
                        round_voters, non_round_voters = self.__calculate_voters(project, selected, round["voter_flow"], projectVotes[project.name])
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

    def __calculate(self, outcome):
        projectVotes = self.__get_project_counts()
        for project in self.instance:
            print("Project", project.name, "of cost", project.cost, "has", projectVotes[project.name], "votes")
        print(self.__calculate_pairwise())

        projects = []
        for project in self.instance:
            projectDict = {}
            projectDict["id"] = project.name
            projectDict["name"] = project.name
            projectDict["totalvotes"] = projectVotes[project.name]
            if project.name in outcome:   
                projectDict["elected"] = True
            else:
                projectDict["elected"] = False
            projects.append(projectDict)
        
        self.projects = projects
        print(self.projects)

        for round in self.rounds:
            round["voter_flow"] = self.__calculate_voter_flow()
        
        self.__calculate_pie_charts(projectVotes)
           

    def render(self, outputName, outcome):
        self.__calculate(outcome)

        # Load the render thing
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(os.path.abspath(__file__))))
        template = env.get_template('./visualisation/mes_template.html')

        spent = 0

        for project in self.instance:
            if project.name in outcome:
                spent += project.cost

        for r in self.rounds:
            print(r)

        rendered_output = template.render(
            election_name=self.instance.meta["description"] if "description" in self.instance.meta else "No description provided.", 
            rounds=[self.rounds[0]], 
            projects=list(self.instance),
            number_of_elected_projects=len(outcome),
            number_of_unelected_projects=len(self.instance) - len(outcome),
            spent=spent,
            budget=self.instance.meta["budget"]
        )

        file_path = os.path.abspath(os.path.dirname("mes_data_store.py"))
        open(file_path + "/output.html", "w").write(rendered_output)

        # print(self.rounds)
