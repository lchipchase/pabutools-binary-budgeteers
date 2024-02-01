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
    {"id": "ProjectA", "name": "Project A", "label": "A", "description": "Adding a new hostpital ward.", "totalvotes": 70, "elected": True},
    {"id": "ProjectB", "name": "Project B", "label": "B", "description": "Building a new school.", "totalvotes": 60, "elected": True},
    {"id": "ProjectC", "name": "Project C", "label": "C", "description": "Building a new library.", "totalvotes": 15, "elected": True},
    {"id": "ProjectD", "name": "Project D", "label": "D", "description": "Building a new park.", "totalvotes": 30, "elected": True},
    {"id": "ProjectE", "name": "Project E", "label": "E", "description": "Building a new swimming pool.", "totalvotes": 5, "elected": True}
]

# What project is selected in each round of MES. Ordered in terms of what project was selected first.
rounds = [ 
    {
        "name": "Project A", 
        "id": "ProjectA",
        "label": "A",
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
            [{"project": "Project E", "roundVoters": 40, "nonRoundVoters": 30, "reduction": 1.00}]
        ],
        "sankey_diagram_items": {
            "B": 7, "C": 23, "D": 3, "E": 10,
        },
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
        "label": "B",
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
        "sankey_diagram_items": {
            "C": 3, "D": 9, "E": 11
        },
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
        "label": "C",
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
        "sankey_diagram_items": {
            "D": 4, "E": 1
        },
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

# TODO: Change location where output.html is created (currently created in directory where file is ran).
open("output.html", "w").write(rendered_output)
