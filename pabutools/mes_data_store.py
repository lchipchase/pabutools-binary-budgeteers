

class MESDataStore:

    pairwise_dict = {}

    def __init__(self, profile, instance):
        self.profile = profile
        self.instance = instance     

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

        # project_votes = get_project_counts(profile)
        # pairwise_project_votes = get_pairwise_project_votes(profile)
        pairwise_project_matrix = self.__get_pairwise_matrix(id_to_index_dict)
        for project in projectsList:
            pairwise_dict["proj" +str(project)] = str(project)
            for projectPair in projectsList:
                pairCount = pairwise_project_matrix[id_to_index_dict[project]][id_to_index_dict[projectPair]]
                myString = "proj"+str(project)+"to"+str(projectPair)
                pairwise_dict[myString] = pairCount
        return pairwise_dict 

    def __calculate(self):
       print(self.__calculate_pairwise())
       print(self.__get_project_counts())



    def render(self, outputName):
        self.__calculate()
        print("")
