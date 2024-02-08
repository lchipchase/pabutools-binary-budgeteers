import jinja2
import os

env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(os.path.abspath(__file__))))
template = env.get_template('template_summary.html')

election_name = "Random PB Election"
number_of_projects = 5
number_of_elected_projects = 2
number_of_unelected_projects = 3
budget = 1000
spent = 1000

projects = [
    {"id": "A", "name": "Project A", "description": "Adding a new hospital ward.", "cost": 500, "totalvotes": 70, "elected": True},
    {"id": "B", "name": "Project B", "description": "Building a new school.", "cost": 300, "totalvotes": 60, "elected": True},
    {"id": "C", "name": "Project C", "description": "Building a new library.", "cost": 200, "totalvotes": 15, "elected": True},
    {"id": "D", "name": "Project D", "description": "Building a new park.", "cost": 100, "totalvotes": 30, "elected": True},
    {"id": "E", "name": "Project E", "description": "Building a new swimming pool.", "cost": 300, "totalvotes": 5, "elected": True}
]

# What project is selected in each round of MES. Ordered in terms of what project was selected first.
rounds = [ 
    {
        "name": "Project A", 
        "id": "A",
        "cost": 500,
        "totalvotes": 70,
        "cost_percent": 50,
        "initial_voter_funding": 800,
        "initial_voter_funding_percent": (800/budget) * 100,
        "final_voter_funding": 600,
        "final_voter_funding_percent": (600/budget) * 100,
        "funding_lost": 200,
        "funding_lost_percent": (200/budget) * 100,

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
        "cost": 300,
        "totalvotes": 60,
        "cost_percent": 30,
        "initial_voter_funding": 700,
        "initial_voter_funding_percent": (700/budget) * 100,
        "final_voter_funding": 500,
        "final_voter_funding_percent": (500/budget) * 100,
        "funding_lost": 200,
        "funding_lost_percent": (200/budget) * 100,

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
        "cost": 200,
        "totalvotes": 60,
        "cost_percent": 20,
        "initial_voter_funding": 450,
        "initial_voter_funding_percent": (450/budget) * 100,
        "final_voter_funding": 200,
        "final_voter_funding_percent": (200/budget) * 100,
        "funding_lost": 250,
        "funding_lost_percent": (250/budget) * 100,

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
    election_name=election_name, 
    rounds=rounds, 
    projects=projects,
    number_of_elected_projects=number_of_elected_projects,
    number_of_unelected_projects=number_of_unelected_projects,
    spent=spent,
    budget=budget
)

file_path = os.path.abspath(os.path.dirname("render_summary.py"))
open(file_path + "/output_summary.html", "w").write(rendered_output)
