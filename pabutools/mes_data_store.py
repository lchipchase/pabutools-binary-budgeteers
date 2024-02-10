class MESDataStore:

    pairwise_dict = {}

    def __init__(self, profile, instance):
        self.profile = profile
        self.instance = instance
        self.rounds = []

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
                        pairwise_interactions[id_to_index_dict[vote_list[i]]][id_to_index_dict[vote_list[j]]] += 1
                        pairwise_interactions[id_to_index_dict[vote_list[j]]][id_to_index_dict[vote_list[i]]] += 1

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


    def __calculate(self, outcome):
        """
        TODO: Add "pie_chart_items" and "voter_flow" to each round dictionary in self.rounds
        {
            "...",
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
            }
        }
        """
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
        print(projects)
           

    def render(self, outputName, outcome):
        self.__calculate(outcome)
        print(self.rounds)
