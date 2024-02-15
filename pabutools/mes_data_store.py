import jinja2
import os

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
                p.name: 1/p.affordability for p in projects
            }
        }
        if len(self.rounds) > 0: 
            self.rounds[-1]["name"] = (self.rounds[-1]["effective_vote_count"].keys() - round["effective_vote_count"].keys()).pop()
            if self.rounds[-1]["name"] in self.rounds[-1]["effective_vote_count_reduction"]:
                del self.rounds[-1]["effective_vote_count_reduction"][self.rounds[-1]["name"]]
        self.rounds.append(round)

    def record_round_end(self, projects):
        self.rounds[-1]["effective_vote_count_reduction"] = {
            p.name: self.rounds[-1]["effective_vote_count"][p]-1/p.affordability for p in projects
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
    
    def __calculate_voter_flow(self):
        # Initialize a dictionary to store voter flow
        voter_flow = {}
        projectsList = list(self.instance)

        # For each project
        for project in projectsList:
            # Initialize a dictionary to store voter flow for the project
            voter_flow[project] = {}
            # For each project
            for other_project in projectsList:
                # Initialize the voter flow for the project to the other project to 0
                voter_flow[project][other_project] = 0

        # Function to update voter flow
        def update_voter_flow(vote_list):
            for i in range(len(vote_list)):
                for j in range(i + 1, len(vote_list)):
                    voter_flow[vote_list[i]][vote_list[j]] += 1
                    voter_flow[vote_list[j]][vote_list[i]] += 1

        # Process each vote list
        for vote in self.profile:
            update_voter_flow(list(vote))
        
        return voter_flow
    
    def __calculate_voters(self, project, selected, vote_flow):
        round_voters = vote_flow[project.name][selected]
        non_round_voters = sum(vote_flow[project.name].values()) - round_voters
        return round_voters, non_round_voters

    def __calculate_pie_charts(self):
        for round in self.rounds:
            pie_chart_items = []

            # The last round does not have a name
            if "name" in round:
                selected = round["name"]

                for project in self.instance:
                    round_voters, non_round_voters = self.__calculate_voters(project, selected, round["voter_flow"])
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

                round["pie_chart_items"] = pie_chart_items

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

        for round in self.rounds:
            round["voter_flow"] = self.__calculate_voter_flow()
        
        self.__calculate_pie_charts()
           

    def render(self, outputName, outcome):
        self.__calculate(outcome)

        # Load the render thing
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(os.path.abspath(__file__))))
        template = env.get_template('./visualisation/mes_template.html')

        print(self.rounds[0])

        spent = 0

        for project in self.instance:
            if project.name in outcome:
                spent += project.cost

        








        election_name = "Random PB Election"
        number_of_projects = 5
        number_of_elected_projects = 2
        number_of_unelected_projects = 3
        budget = 1000
        spent = 1000

        projects = [
            {"id": "A", "name": "Project A", "description": "Adding a new hospital ward.", "totalvotes": 70, "elected": True},
            {"id": "B", "name": "Project B", "description": "Building a new school.", "totalvotes": 60, "elected": True},
            {"id": "C", "name": "Project C", "description": "Building a new library.", "totalvotes": 15, "elected": True},
            {"id": "D", "name": "Project D", "description": "Building a new park.", "totalvotes": 30, "elected": True},
            {"id": "E", "name": "Project E", "description": "Building a new swimming pool.", "totalvotes": 5, "elected": True}
        ]

        # What project is selected in each round of MES. Ordered in terms of what project was selected first.
        rounds = [ 
            {
                "name": "Project A", 
                "id": "A",
                "effective_vote_count": {
                    "A": 70,
                    "B": 60,
                    "C": 15,
                    "D": 30,
                    "E": 5
                },
                # BUG: Multiple visual bugs involving the pie charts:
                    # Pie chart visuals break after the first round (probably the same issue that is affecting the chord diagrams).
                    # Pie charts in carousels with less than 3 items expand to fill space in the wrapper, while textboxes don't.
                    # Pie charts currently display weirdly when any voter values are 0 (see output.html for an example).
                # BUG: Any reductions that are integers are displayed incorrectly (e.g. "1.0" instead of "1.00").

                "pie_chart_items": [ 
                    # Carousel has 3 pie charts per slide, so each list in this list 
                    # should have a max of 3 pie charts (to avoid having complex divide by 3 and dealing with remainder logic in HTML)
                    [
                        {"project": "Project B", "roundVoters": 10, "nonRoundVoters": 60, "reduction": 12.32}, 
                        {"project": "Project C", "roundVoters": 0, "nonRoundVoters": 70, "reduction": 9.11}, 
                        {"project": "Project D", "roundVoters": 35, "nonRoundVoters": 35, "reduction": 3.23}
                    ],
                    [
                        {"project": "Project E", "roundVoters": 40, "nonRoundVoters": 30, "reduction": 1.00}
                    ]
                ],
                "voter_flow": {
                    # How many voters who voted for a specific project also voted for all other projects
                    "A":{"A": 10, "B": 7, "C": 23, "D": 3, "E": 10},
                    "B":{"A": 7, "B": 21, "C": 3, "D": 9, "E": 11},
                    "C":{"A": 3, "B": 1, "C": 2, "D": 4, "E": 1},
                    "D":{"A": 5, "B": 3, "C": 3, "D": 5, "E": 10},
                    "E":{"A": 1, "B": 1, "C": 1, "D": 1, "E": 1},
                },
                "effective_vote_count_reduction": {
                    "B": 10,
                    "C": 1,
                    "D": 10,
                    "E": 1
                }
            },
            {
                "name": "Project B", 
                "id": "B",
                "effective_vote_count": {
                    "B": 50,
                    "C": 14,
                    "D": 20,
                    "E": 4
                },
                "pie_chart_items": [
                    [
                        {"project": "Project C", "roundVoters": 30, "nonRoundVoters": 20, "reduction": 12.32}, 
                        {"project": "Project D", "roundVoters": 6, "nonRoundVoters": 48, "reduction": 12.73}, 
                        {"project": "Project E", "roundVoters": 42, "nonRoundVoters": 8, "reduction": 12.35}
                    ]
                ],
                "voter_flow": {
                    "A":{"A": 10, "B": 7, "C": 23, "D": 3, "E": 10},
                    "B":{"A": 7, "B": 21, "C": 3, "D": 9, "E": 11},
                    "C":{"A": 3, "B": 1, "C": 2, "D": 4, "E": 1},
                    "D":{"A": 5, "B": 3, "C": 3, "D": 5, "E": 10},
                    "E":{"A": 1, "B": 1, "C": 1, "D": 1, "E": 1},
                },
                "effective_vote_count_reduction": {
                    "C": 0,
                    "D": 18,
                    "E": 1
                }
            },
            {
                "name": "Project C", 
                "id": "C",
                "effective_vote_count": {
                    "C": 14,
                    "D": 2,
                    "E": 3
                },
                "pie_chart_items": [
                    [
                        {"project": "Project D", "roundVoters": 7, "nonRoundVoters": 7, "reduction": 1.25}, 
                        {"project": "Project E", "roundVoters": 4, "nonRoundVoters": 10, "reduction": 9.45}, 
                    ],
                ],
                "voter_flow": {
                    "A":{"A": 10, "B": 7, "C": 23, "D": 3, "E": 10},
                    "B":{"A": 7, "B": 21, "C": 3, "D": 9, "E": 11},
                    "C":{"A": 3, "B": 1, "C": 2, "D": 4, "E": 1},
                    "D":{"A": 5, "B": 3, "C": 3, "D": 5, "E": 10},
                    "E":{"A": 1, "B": 1, "C": 1, "D": 1, "E": 1},
                },
                "effective_vote_count_reduction": {
                    "D": 0,
                    "E": 0
                }
            },
        ]

        rendered_output = template.render(
            election_name=self.instance.meta["description"] if "description" in self.instance.meta else "No description provided.", 
            rounds=rounds, 
            projects=list(self.instance),
            number_of_elected_projects=len(outcome),
            number_of_unelected_projects=len(self.instance) - len(outcome),
            spent=spent,
            budget=self.instance.meta["budget"]
        )

        file_path = os.path.abspath(os.path.dirname("mes_data_store.py"))
        open(file_path + "/output.html", "w").write(rendered_output)

        print(self.rounds)
