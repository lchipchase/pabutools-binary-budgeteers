from __future__ import annotations
#pabutools version: 0.12
from model import Election, Candidate
import random
import math
import pdb

def excl_ratio(e, W):
    satisfied_voters = len(set([v for c in W for v in e.profile[c]]))
    n = len(e.voters)
    return (n - satisfied_voters) / n * 100

def avg_util(e, W):
    util = sum(len(e.profile[c]) for c in W)
    return util / len(e.voters)

# Utilitarian Greedy procedure
# W: initial outcome
# Assumes cost utilities
def utilitarian_greedy(e : Election, tie_break : Dict[Candidate, int], conflicts : Dict[Candidate, Set[Candidate]], W : Set[Candidate] = None, projects_order = None) -> set[Candidate]:
    if W is None:
        W = set()
    if projects_order is None:
        projects_order = {}
    costW = sum(c.cost for c in W)
    remaining = set(c for c in e.profile)
    ranked = sorted(remaining, key=lambda c : (-sum(e.profile[c].values()) / c.cost, tie_break[c]))
    for c in ranked:
        if c in W or (conflicts[c] & set(W)):
            continue
        if costW + c.cost <= e.budget:
            W.add(c)
            costW += c.cost
    return W, projects_order

# Equal Shares procedure for fixed endowments
# Assumes cost utilities
# One candidate may be "skipped" - it is used while computing the effective support for this candidate
# Returns a pair (committee, effective support of skipped_candidate or None if skipped candidate is not specified)
# If the elected committee would exceed real_budget, the procedure breaks immediately and returns None
def mes_internal(e : Election, tie_break : Dict[Candidate, int], conflicts : Dict[Candidate, Set[Candidate]], skipped_candidate : Optional[Candidate] = None, real_budget : int = 0) -> (list[Candidate], Dict[Candidate, int]):
    W = []
    projects_order = {}
    costW = 0
    res = None
    remaining = set(c for c in e.profile)
    money_behind_candidates = {c : [] for c in e.profile}
    if skipped_candidate:
        remaining.remove(skipped_candidate)
        res = 0
    endow = {i : 1.0 * e.budget / len(e.voters) for i in e.voters}
    while True:
        next_candidate = None
        lowest_rho = math.inf
        for c in remaining:
            money = sum(endow[i] for i in e.profile[c])
            money_behind_candidates[c].append(money)
            if money >= c.cost:
                supporters_sorted = sorted(e.profile[c], key=lambda i: endow[i] / e.profile[c][i])
                price = c.cost
                util = sum(e.profile[c].values())
                for i in supporters_sorted:
                    if endow[i] * util >= price * e.profile[c][i]:
                        break
                    price -= endow[i]
                    util -= e.profile[c][i]
                rho = price / util
                if rho < lowest_rho or (rho == lowest_rho and tie_break[c] < tie_break[next_candidate]):
                    next_candidate = c
                    lowest_rho = rho
        if next_candidate is None:
            break
        else:
            W.append(next_candidate)
            projects_order[next_candidate] = len(W)
            costW += next_candidate.cost
            remaining.remove(next_candidate)
            remaining -= conflicts[next_candidate]
            if skipped_candidate:
                cover = 0
                for i in e.profile[skipped_candidate]:
                    cover += min(endow[i], lowest_rho * e.profile[skipped_candidate][i])
                new_res = int(cover / skipped_candidate.cost * 100)
                if new_res > res:
                    res = max(res, new_res)
                    projects_order[skipped_candidate] = len(W) - 0.1
            for i in e.profile[next_candidate]:
                endow[i] -= min(endow[i], lowest_rho * e.profile[next_candidate][i])
            if real_budget:
                if costW > real_budget:
                    return None
    if skipped_candidate:
        cover = sum(endow[i] for i in e.profile[skipped_candidate])
        new_res = int(cover / skipped_candidate.cost * 100)
        if new_res > res:
            res = new_res
            projects_order[skipped_candidate] = len(W) - 0.1
    return W, projects_order, money_behind_candidates, res

# Whether or not given committee is exhaustive
def is_exhaustive(e : Election, W : list[Candidate], conflicts: Dict[Candidate, Set[Candidate]]) -> bool:
    costW = sum(c.cost for c in W)
    conflicted = set(c_ for c in W for c_ in conflicts[c])
    minRemainingCost = min([c.cost for c in e.profile if c not in set(W) | conflicted], default=math.inf)
    return costW + minRemainingCost > e.budget

# Return a dict candidate -> value, ties are broken in favor of lower values
def get_tie_break_dict(e : Election) -> Dict[Candidate, Any]:
    cands = [c for c in e.profile]
    random.shuffle(cands)
    ret = {}
    for i, c in enumerate(cands):
        ret[c] = (-len(e.profile[c]), c.cost, i)
    return ret

# Main function for equal shares
# Assumes cost utilties
# Returns a pair (committee, effective supports of all candidates)
def equal_shares(e : Election, tie_break : Dict[Candidate, int], conflicts: Dict[Candidate, Set[Candidate]]) -> (set[Candidate], Dict[Candidate, int]):
    final_budget = 0
    W_mes, projects_order, money_behind_candidates, _ = mes_internal(e, tie_break, conflicts)
    initial_budget = e.budget
    while not is_exhaustive(e, W_mes, conflicts):
        e.budget += len(e.voters) #each voter gets 1 dollar more
        res_nxt = mes_internal(e, tie_break, conflicts, real_budget=initial_budget)
        if res_nxt is None:
            e.budget -= len(e.voters)
            break
        W_mes, projects_order, money_behind_candidates, _ = res_nxt

    final_budget = e.budget
    res_mes = {}
    for skipped_candidate in e.profile:
        _, projects_order_for_skipped, _, res_mes[skipped_candidate] = mes_internal(e, tie_break, conflicts, skipped_candidate=skipped_candidate)
        if skipped_candidate not in W_mes:
            projects_order[skipped_candidate] = projects_order_for_skipped[skipped_candidate]

    e.budget = initial_budget
    for c in W_mes:
        assert res_mes[c] >= 99, (skipped_candidate, res_mes[c])
        res_mes[c] = max(res_mes[c], 100)

    W_mes, projects_order = utilitarian_greedy(e, tie_break, conflicts, W_mes, projects_order)
    for c in e.profile:
        if c in W_mes and res_mes[c] < 100: # projects elected in the utilitarian greedy phase
            res_mes[c] = 100
        elif c not in W_mes:
            assert res_mes[c] <= 100, (c, res_mes[c])
            res_mes[c] = min(res_mes[c], 99)

    return W_mes, projects_order, money_behind_candidates, final_budget, res_mes

# Whether more voters prefer W1 to W2 or not
def prefer(e : Election, W1 : set[Candidate], W2 : set[Candidate]) -> bool:
    satisfaction1 = {v : len([c for c in W1 if v in e.profile[c]]) for v in e.voters}
    satisfaction2 = {v : len([c for c in W2 if v in e.profile[c]]) for v in e.voters}
    prefer1 = len([v for v in e.voters if satisfaction1[v] > satisfaction2[v]])
    prefer2 = len([v for v in e.voters if satisfaction2[v] > satisfaction1[v]])
    return prefer1 > prefer2

def print_result(file : str):
    e = Election().read_from_files(file).score_to_cost_utilities()
    votes = []
    conflicts = {c : set() for c in e.profile}
    tie_break = get_tie_break_dict(e)
    W_mes, projects_order, money_behind_candidates, budget, res = equal_shares(e, tie_break, conflicts)
    W_greedy, _ = utilitarian_greedy(e, tie_break, conflicts)
    if prefer(e, W_mes, W_greedy):
        print("projekt;koszt;liczba głosów;efektywne poparcie (%);wybrany")
        for c in sorted([c for c in e.profile], key=lambda c: -res[c]):
            print(f"{c.id};{c.cost};{round(sum(e.profile[c].values()) / c.cost)};{res[c]};{'TAK' if c in W_mes else 'NIE'}")
    else:
        print("projekt;koszt;liczba głosów;wybrany")
        for c in sorted([c for c in e.profile], key=lambda c: -round(sum(e.profile[c].values()) / c.cost)):
            print(f"{c.id};{c.cost};{round(sum(e.profile[c].values()) / c.cost)};{'TAK' if c in W_greedy else 'NIE'}")

if __name__ == '__main__':
    print_result("swiecie2023.pb")
