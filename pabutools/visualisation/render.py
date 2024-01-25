import jinja2
import os

env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(os.path.abspath(__file__))))
template = env.get_template('mes_template.html')

election_name = "Random PB Election"
number_of_projects = 5
number_of_elected_projects = 2
number_of_unelected_projects = 3
budget = 1000
spent = 1000

projects = [
    {"id": "ProjectA", "name": "Project A", "description": "Adding a new hostpital ward.", "totalvotes": 70, "elected": True},
    {"id": "ProjectB", "name": "Project B", "description": "Building a new school.", "totalvotes": 60, "elected": True},
    {"id": "ProjectC", "name": "Project C", "description": "Building a new library.", "totalvotes": 15, "elected": True},
    {"id": "ProjectD", "name": "Project D", "description": "Building a new park.", "totalvotes": 30, "elected": True},
    {"id": "ProjectE", "name": "Project E", "description": "Building a new swimming pool.", "totalvotes": 5, "elected": True}
]

# What project is selected in each round of MES. Ordered in terms of what project was selected first.
rounds = [ 
    {
        "name": "Project A", 
        "id": "ProjectA",
        "effective_vote_count": {
            "A": 70,
            "B": 60,
            "C": 15,
            "D": 30,
            "E": 5
        },
        "pie_chart_items": [ 
            # Carousel has 3 pie charts per slide, so each list in this list 
            # should have a max of 3 pie charts (to avoid having complex divide by 3 and dealing with remainder logic in HTML)
            # TODO are the items in this list correct (first two items have same name)? 
            ["ProjAvsBData", "ProjAvsBData", "ProjAvsCData"], # TODO: Replace strings with dictionary with pie chart data
            ["ProjAvsDData"]
        ],
        "chord_diagram_items":
            # How many voters who voted for a specific project also voted for all other projects
            {
                "projA": "A", "ProjAtoA": 10, "ProjAtoB": 7, "ProjAtoC": 23, "ProjAtoD": 3, "ProjAtoE": 10,
                "projB": "B", "ProjBtoA": 7, "ProjBtoB": 21, "ProjBtoC": 3, "ProjBtoD": 9, "ProjBtoE": 11,
                "projC": "C", "ProjCtoA": 3, "ProjCtoB": 1, "ProjCtoC": 2, "ProjCtoD": 4, "ProjCtoE": 1,
                "projD": "D", "ProjDtoA": 5, "ProjDtoB": 3, "ProjDtoC": 3, "ProjDtoD": 5, "ProjDtoE": 10,
                "projE": "E", "ProjEtoA": 1, "ProjEtoB": 1, "ProjEtoC": 1, "ProjEtoD": 1, "ProjEtoE": 1
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
        "id": "ProjectB",
        "effective_vote_count": {
            "B": 50,
            "C": 14,
            "D": 20,
            "E": 4
        },
        "pie_chart_items": [
            # TODO are the items in this list correct (first two items have same name, "B vs B data" doesn't make sense, etc.)? 
            ["ProjBvsBData", "ProjBvsBData", "ProjBvsCData"],
        ],
        "chord_diagram_items": 
            {
                "projA": "A", "ProjAtoA": 10, "ProjAtoB": 7, "ProjAtoC": 23, "ProjAtoD": 3, "ProjAtoE": 10,
                "projB": "B", "ProjBtoA": 7, "ProjBtoB": 21, "ProjBtoC": 3, "ProjBtoD": 9, "ProjBtoE": 11,
                "projC": "C", "ProjCtoA": 3, "ProjCtoB": 1, "ProjCtoC": 2, "ProjCtoD": 4, "ProjCtoE": 1,
                "projD": "D", "ProjDtoA": 5, "ProjDtoB": 3, "ProjDtoC": 3, "ProjDtoD": 5, "ProjDtoE": 10,
                "projE": "E", "ProjEtoA": 1, "ProjEtoB": 1, "ProjEtoC": 1, "ProjEtoD": 1, "ProjEtoE": 1
            },
        "effective_vote_count_reduction": {
            "C": 0,
            "D": 18,
            "E": 1
        }
    },
    {
        "name": "Project C", 
        "id": "ProjectC",
        "effective_vote_count": {
            "C": 14,
            "D": 2,
            "E": 3
        },
        "pie_chart_items": [
            # TODO are the items in this list correct (first two items have same name)? 
            ["ProjCvsBData", "ProjCvsBData", "ProjCvsCData"],
            ["ProjCvsDData", "ProjCvsEData", "ProjCvsFData"],
        ],
        "chord_diagram_items":
            {
                "projA": "A", "ProjAtoA": 10, "ProjAtoB": 7, "ProjAtoC": 23, "ProjAtoD": 3, "ProjAtoE": 10,
                "projB": "B", "ProjBtoA": 7, "ProjBtoB": 21, "ProjBtoC": 3, "ProjBtoD": 9, "ProjBtoE": 11,
                "projC": "C", "ProjCtoA": 3, "ProjCtoB": 1, "ProjCtoC": 2, "ProjCtoD": 4, "ProjCtoE": 1,
                "projD": "D", "ProjDtoA": 5, "ProjDtoB": 3, "ProjDtoC": 3, "ProjDtoD": 5, "ProjDtoE": 10,
                "projE": "E", "ProjEtoA": 1, "ProjEtoB": 1, "ProjEtoC": 1, "ProjEtoD": 1, "ProjEtoE": 1
            },
        "effective_vote_count_reduction": {
            "D": 0,
            "E": 0
        }
    },
]

rendered_output = template.render(
    election_name=election_name, 
    rounds=rounds, 
    projects=projects,
    number_of_elected_projects=number_of_elected_projects,
    number_of_unelected_projects=number_of_unelected_projects,
    spent=spent,
    budget=budget
)

open("output.html", "w").write(rendered_output)
