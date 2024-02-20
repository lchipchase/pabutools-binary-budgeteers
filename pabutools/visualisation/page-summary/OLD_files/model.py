from __future__ import annotations
from pathlib import Path
import csv

class Voter:
    def __init__(self,
            id : str,
            sex : str = None,
            age : int = None,
            subunits : set[str] = set()
            ):
        self.id = id #unique id
        self.sex = sex
        self.age = age
        self.subunits = subunits

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, v):
        return self.id == v.id

    def __repr__(self):
        return f"v({self.id})"

class Candidate:
    def __init__(self,
            id : str,
            cost : int,
            name : str = None,
            subunit : str = None
            ):
        self.id = id #unique id
        self.cost = cost
        self.name = name
        self.subunit = subunit #None for citywide projects

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, c):
        return self.id == c.id

    def __repr__(self):
        return f"c({self.id})"

class Election:
    def __init__(self,
            name : str = None,
            voters : set[Voter] = None,
            profile : dict[Candidate, dict[Voter, int]] = None,
            budget : int = 0,
            subunits : set[str] = None
            ):
        self.name = name
        self.voters = voters if voters else set()
        self.profile = profile if profile else {} #dict: candidates -> voters -> score
        self.budget = budget
        self.subunits = subunits if subunits else set()

    def binary_to_cost_utilities(self) -> Election:
        assert all((self.profile[c][v] == 1) for c in self.profile for v in self.profile[c])
        return self.score_to_cost_utilities()

    def cost_to_binary_utilities(self) -> Election:
        assert all((self.profile[c][v] == c.cost) for c in self.profile for v in self.profile[c])
        return self.cost_to_score_utilities()

    def score_to_cost_utilities(self) -> Election:
        for c in self.profile:
            for v in self.profile[c]:
                self.profile[c][v] *= c.cost
        return self

    def cost_to_score_utilities(self) -> Election:
        for c in self.profile:
            for v in self.profile[c]:
                self.profile[c][v] /= c.cost * 1.0
        return self

    def read_from_files(self, pattern : str): #assumes Pabulib data format
        cnt = 0
        for filename in Path(".").glob(pattern):
            cnt += 1
            cand_id_to_obj = {}
            with open(filename, 'r', newline='', encoding="utf-8") as csvfile:
                section = ""
                header = []
                reader = csv.reader(csvfile, delimiter=';')
                subunit = None
                meta = {}
                for i, row in enumerate(reader):
                    if len(row) == 0: #skip empty lines
                        continue
                    if str(row[0]).strip().lower() in ["meta", "projects", "votes"]:
                        section = str(row[0]).strip().lower()
                        header = next(reader)
                    elif section == "meta":
                        field, value  = row[0], row[1].strip()
                        meta[field] = value
                        if field == "subunit":
                            subunit = value
                            self.subunits.add(subunit)
                        if field == "budget":
                            self.budget += int(value.split(",")[0])
                    elif section == "projects":
                        project = {}
                        for it, key in enumerate(header[1:]):
                            project[key.strip()] = row[it+1].strip()
                        c_id = row[0]
                        c = Candidate(c_id, int(project["cost"]), project["name"], subunit=subunit)
                        self.profile[c] = {}
                        cand_id_to_obj[c_id] = c
                    elif section == "votes":
                        vote = {}
                        for it, key in enumerate(header[1:]):
                            vote[key.strip()] = row[it+1].strip()
                        v_id = row[0]
                        v_age = vote.get("age", None)
                        v_sex = vote.get("sex", None)
                        v = Voter(v_id, v_sex, v_age)
                        self.voters.add(v)
                        v_vote = [cand_id_to_obj[c_id] for c_id in vote["vote"].split(",")]
                        v_points = [1 for c in v_vote]
                        if meta["vote_type"] == "ordinal":
                            v_points = [int(meta["max_length"]) - i for i in range(len(v_vote))]
                        elif "points" in vote:
                            v_points = [int(points) for points in vote["points"].split(",")]
                        v_vote_points = zip(v_vote, v_points)
                        for (vote, points) in v_vote_points:
                            self.profile[vote][v] = points
        if cnt == 0:
            raise Exception("Invalid pattern: 0 files found")
        for c in set(c for c in self.profile):
            if c.cost > self.budget or sum(self.profile[c].values()) == 0: #nobody voted for the project; usually means the project was withdrawn
                del self.profile[c]

        return self
