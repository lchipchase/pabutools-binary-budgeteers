"""
The method of equal shares.
"""
from __future__ import annotations

from copy import copy, deepcopy
from collections.abc import Collection, Iterable

from pabutools.rules.budgetallocation import BudgetAllocation
from pabutools.utils import Numeric

from pabutools.election import AbstractApprovalProfile
from pabutools.election.satisfaction.satisfactionmeasure import GroupSatisfactionMeasure
from pabutools.election.ballot.ballot import AbstractBallot
from pabutools.election.instance import Instance, Project
from pabutools.election.profile import AbstractProfile
from pabutools.election.satisfaction import SatisfactionMeasure
from pabutools.tiebreaking import lexico_tie_breaking
from pabutools.fractions import frac
from pabutools.tiebreaking import TieBreakingRule
from pabutools.visualisation.mes_data_store import MESDataStore


class MESVoter:
    """
    Class used to summarise a voter during a run of the method of equal shares.

    Parameters
    ----------
        index: Numeric
            The index of the voter in the voter list
        ballot: :py:class:`~pabutools.election.ballot.ballot.AbstractBallot`
            The ballot of the voter.
        sat: SatisfactionMeasure
            The satisfaction measure corresponding to the ballot.
        budget: Numeric
            The budget of the voter.
        multiplicity: int
            The multiplicity of the ballot.

    Attributes
    ----------
        index: int
            The index of the voter in the list of voters MES maintains
        ballot: :py:class:`~pabutools.election.ballot.ballot.AbstractBallot`
            The ballot of the voter.
        sat: SatisfactionMeasure
            The satisfaction measure corresponding to the ballot.
        budget: Numeric
            The budget of the voter.
        multiplicity: int
            The multiplicity of the ballot.
        budget_over_sat_map: dict[Numeric, Numeric]
            Maps values of the budget to values of the budget divided by the total satisfaction.
    """

    def __init__(
        self,
        index: Numeric,
        ballot: AbstractBallot,
        sat: SatisfactionMeasure,
        budget: Numeric,
        multiplicity: int,
    ):
        self.index: int = index
        self.ballot: AbstractBallot = ballot
        self.sat: SatisfactionMeasure = sat
        self.budget: Numeric = budget
        self.multiplicity: int = multiplicity
        self.budget_over_sat_map: dict[tuple[Project, Numeric], Numeric] = dict()

    def total_sat_project(self, proj: Project) -> Numeric:
        """
        Returns the total satisfaction of a given project. It is equal to the satisfaction for the project,
        multiplied by the multiplicity.

        Parameters
        ----------
            proj: :py:class:`~pabutools.election.instance.Project`
                The project.

        Returns
        -------
            Numeric
                The total satisfaction.
        """
        return self.multiplicity * self.sat.sat_project(proj)

    def total_budget(self) -> Numeric:
        """
        Returns the total budget of the voters. It is equal to the budget multiplied by the multiplicity.

        Returns
        -------
            Numeric
                The total budget.
        """
        return self.multiplicity * self.budget

    def budget_over_sat_project(self, proj):
        """
        Returns the budget divided by the satisfaction for a given project.

        Parameters
        ----------
            proj: :py:class:`~pabutools.election.instance.Project`
                The collection of projects.

        Returns
        -------
            Numeric
                The total satisfaction.
        """
        res = self.budget_over_sat_map.get((proj, self.budget), None)
        if res is None:
            res = frac(self.budget, self.sat.sat_project(proj))
            self.budget_over_sat_map[(proj, self.budget)] = res
        return res

    def __str__(self):
        return f"MESVoter[{self.budget}]"

    def __repr__(self):
        return f"MESVoter[{self.budget}]"


class MESProject(Project):
    """
    Class used to summarise the projects in a run of MES. Mostly use to store details that can be retrieved
    efficiently.
    """

    def __init__(self, project):
        Project.__init__(self, project.name, project.cost)
        self.project = project
        self.total_sat = None
        self.sat_supporter_map = dict()
        self.unique_sat_supporter = None
        self.supporter_indices = []
        self.initial_affordability = None
        self.affordability = None

    def supporters_sat(self, supporter: MESVoter):
        if self.unique_sat_supporter:
            return self.unique_sat_supporter
        return supporter.sat.sat_project(self)

    def __str__(self):
        return f"MESProject[{self.name}, {float(self.affordability)}]"

    def __repr__(self):
        return f"MESProject[{self.name}, {float(self.affordability)}]"


def affordability_poor_rich(voters: list[MESVoter], project: MESProject) -> Numeric:
    """Compute the affordability factor of a project using the "poor/rich" algorithm.

    Parameters
    ----------
        voters: list[MESVoter]
            The list of the voters, formatted for MES.
        project: MESProject
            The project under consideration.

    Returns
    -------
        Numeric
            The affordability factor of the project.

    """
    rich = set(project.supporter_indices)
    poor = set()
    while len(rich) > 0:
        poor_budget = sum(voters[i].total_budget() for i in poor)
        numerator = frac(project.cost - poor_budget)
        denominator = sum(voters[i].total_sat_project(project) for i in rich)
        affordability = frac(numerator, denominator)
        new_poor = {
            i
            for i in rich
            if voters[i].total_budget()
            < affordability * voters[i].sat.sat_project(project)
        }
        if len(new_poor) == 0:
            return affordability
        rich -= new_poor
        poor.update(new_poor)


def naive_mes(
    instance: Instance,
    profile: AbstractProfile,
    sat_class: type[SatisfactionMeasure],
    initial_budget_per_voter: Numeric,
) -> BudgetAllocation:
    """
    Naive implementation of the method of equal shares. Probably slow, but useful to test the correctness of
    other implementations.

    Parameters
    ----------
        instance: Instance
            The instance.
        profile: AbstractProfile
            The profile.
        sat_class: type[SatisfactionMeasure]
            The satisfaction measure used as a proxy of the satisfaction of the voters.
        initial_budget_per_voter: Numeric
            The initial budget allocated to the voters in the run of MES.

    Returns
    -------
        BudgetAllocation
            All the projects selected by the method of equal shares.

    """
    sat_profile = profile.as_sat_profile(sat_class)
    voters = []
    for index, sat in enumerate(sat_profile):
        voters.append(
            MESVoter(
                index,
                sat.ballot,
                sat,
                initial_budget_per_voter,
                sat_profile.multiplicity(sat),
            )
        )
        index += 1

    projects = set()
    for p in instance:
        mes_p = MESProject(p)
        total_sat = 0
        for i, v in enumerate(voters):
            indiv_sat = v.sat.sat_project(p)
            if indiv_sat > 0:
                total_sat += v.total_sat_project(p)
                mes_p.supporter_indices.append(i)
                mes_p.sat_supporter_map[v] = indiv_sat
        if total_sat > 0:
            if p.cost > 0:
                mes_p.total_sat = total_sat
                projects.add(mes_p)

    res = BudgetAllocation()
    affordabilities = dict()

    remaining_projects = deepcopy(projects)
    while True:
        to_remove = set()
        for project in remaining_projects:
            if (
                sum(voters[i].total_budget() for i in project.supporter_indices)
                < project.cost
            ):
                to_remove.add(project)
            afford = affordability_poor_rich(voters, project)
            if afford is not None:
                affordabilities[project] = afford
        for project in to_remove:
            remaining_projects.remove(project)
            if project in affordabilities:
                del affordabilities[project]
        if len(remaining_projects) == 0:
            return res
        min_afford = min(affordabilities.values())
        selected = [p for p in remaining_projects if affordabilities[p] == min_afford][
            0
        ]
        res.append(selected.project)
        remaining_projects.remove(selected)
        del affordabilities[selected]
        for i in selected.supporter_indices:
            voters[i].budget -= min(
                voters[i].budget, min_afford * voters[i].sat.sat_project(selected)
            )


def mes_inner_algo(
    instance: Instance,
    profile: AbstractProfile,
    voters: list[MESVoter],
    projects: set[MESProject],
    tie_breaking_rule: TieBreakingRule,
    current_alloc: list[Project],
    all_allocs: list[list[Project]],
    resoluteness: bool,
    verbose: bool = False,
    mes_data_store: MESDataStore = None
) -> None:
    """
    The inner algorithm used to compute the outcome of the Method of Equal Shares (MES). See the website
    `equalshares.net <https://equalshares.net/>`_ for details about how to compute the outcome of the rule.

    Parameters
    ----------
        instance: :py:class:`~pabutools.election.instance.Instance`
            The instance.
        profile : :py:class:`~pabutools.election.profile.profile.AbstractProfile`
            The profile.
        voters: list[MESVoter]
            The list of MESVoters, already instantiated with the necessary inner values.
        projects: set[MESProject]
            The set of MESProjects to take into account, already instantiated with the necessary inner
            values.
        tie_breaking_rule : :py:class:`~pabutools.tiebreaking.TieBreakingRule`
            The tie-breaking rule used.
        current_alloc: list[Project]
            The budget allocation that is currently being built. Only populated via side effects.
        all_allocs: list[list[Project]]
            The set of all budget allocations returned so far. Only populated via side effects.
        resoluteness : bool, optional
            Set to `False` to obtain an irresolute outcome, where all tied budget allocations are returned.
            Defaults to True.
        verbose : bool, optional
            (De)Activate the display of additional information.
    Returns
    -------
        :py:class:`~pabutools.rules.budgetallocation.BudgetAllocation` | list[:py:class:`~pabutools.rules.budgetallocation.BudgetAllocation`]
            The selected projects if resolute (`resoluteness` = True), or the set of selected projects if irresolute
            (`resoluteness = False`).

    """
    tied_projects = []
    best_afford = float("inf")
    if verbose:
        print("========================")
    if mes_data_store is not None:
        mes_data_store.record_round_start(projects)
    for project in sorted(projects, key=lambda p: p.affordability):
        if verbose:
            print(f"\tConsidering: {project}")
        if (
            sum(voters[i].total_budget() for i in project.supporter_indices)
            < project.cost
        ):  # unaffordable, can delete
            if verbose:
                print(
                    f"\t\t Removed for lack of budget: "
                    f"{float(sum(voters[i].total_budget() for i in project.supporter_indices))} < {float(project.cost)}"
                )
            projects.remove(project)
            continue
        if (
            project.affordability > best_afford
        ):  # best possible afford for this round isn't good enough
            if verbose:
                print(
                    f"\t\t Skipped as affordability is too high: {float(project.affordability)} > {float(best_afford)}"
                )
            break
        project.supporter_indices.sort(
            key=lambda i: voters[i].budget_over_sat_project(project)
        )
        current_contribution = 0
        denominator = project.total_sat
        for i in project.supporter_indices:
            supporter = voters[i]
            afford_factor = frac(project.cost - current_contribution, denominator)
            if verbose:
                print(
                    f"\t\t\t {project.cost} - {current_contribution} / {denominator} = {afford_factor} * "
                    f"{project.supporters_sat(supporter)} ?? {supporter.budget}"
                )
            if afford_factor * project.supporters_sat(supporter) <= supporter.budget:
                # found the best afford_factor for this project
                project.affordability = afford_factor
                if verbose:
                    eff_vote_count = frac(
                        denominator, project.cost - current_contribution
                    )
                    print(
                        f"\t\tFactor: {float(afford_factor)} = ({float(project.cost)} - {float(current_contribution)})/{float(denominator)}"
                    )
                    print(f"\t\tEff: {float(eff_vote_count)}")
                if afford_factor < best_afford:
                    best_afford = afford_factor
                    tied_projects = [project]
                elif afford_factor == best_afford:
                    tied_projects.append(project)
                break
            current_contribution += supporter.total_budget()
            denominator -= supporter.multiplicity * project.supporters_sat(supporter)
    if verbose:
        print(f"{tied_projects}")
    if not tied_projects:
        if resoluteness:
            all_allocs.append(current_alloc)
        else:
            current_alloc.sort()
            if current_alloc not in all_allocs:
                all_allocs.append(current_alloc)
    else:
        if len(tied_projects) > 1:
            tied_projects = tie_breaking_rule.order(instance, profile, tied_projects)
            if resoluteness:
                tied_projects = tied_projects[:1]
        for selected_project in tied_projects:
            if mes_data_store is not None:
                mes_data_store.record_round_end(projects, selected_project.project)
            if resoluteness:
                new_alloc = current_alloc
                new_projects = projects
                new_voters = voters
            else:
                new_alloc = copy(current_alloc)
                new_projects = deepcopy(projects)
                new_voters = deepcopy(voters)
            new_alloc.append(selected_project.project)
            new_projects.remove(selected_project)
            if verbose:
                print(
                    f"Price is {best_afford * selected_project.supporters_sat(selected_project.supporter_indices[0])}"
                )
            for i in selected_project.supporter_indices:
                supporter = new_voters[i]
                supporter.budget -= min(
                    supporter.budget,
                    best_afford * selected_project.supporters_sat(supporter),
                )
            mes_inner_algo(
                instance,
                profile,
                new_voters,
                new_projects,
                tie_breaking_rule,
                new_alloc,
                all_allocs,
                resoluteness,
                verbose=verbose,
                mes_data_store=mes_data_store
            )


def method_of_equal_shares_scheme(
    instance: Instance,
    profile: AbstractProfile,
    sat_profile: GroupSatisfactionMeasure,
    initial_budget_per_voter: Numeric,
    initial_budget_allocation: BudgetAllocation,
    tie_breaking: TieBreakingRule,
    resoluteness=True,
    voter_budget_increment=None,
    binary_sat=False,
    verbose: bool = False,
) -> BudgetAllocation | list[BudgetAllocation]:
    """
    The main wrapper to compute the outcome of the Method of Equal Shares (MES). This is where the
    iterated method is implemented.
    Parameters
    ----------
        instance: :py:class:`~pabutools.election.instance.Instance`
            The instance.
        profile : :py:class:`~pabutools.election.profile.profile.AbstractProfile`
            The profile.
        sat_profile : :py:class:`~pabutools.election.satisfaction.satisfactionmeasure.GroupSatisfactionMeasure`
            The profile of satisfaction functions.
        initial_budget_per_voter: Numeric
            The initial budget of a voter.
        initial_budget_allocation : list[:py:class:`~pabutools.election.instance.Project`]
            An initial budget allocation, typically empty.
        tie_breaking : :py:class:`~pabutools.tiebreaking.TieBreakingRule`
            The tie-breaking rule used.
        resoluteness : bool, optional
            Set to `False` to obtain an irresolute outcome, where all tied budget allocations are returned.
            Defaults to True.
        voter_budget_increment : Numeric, optional
            Any value that is not `None` will lead to the iterated variant of MES where `voter_budget_increment` units
            of budget are added to the initial budget of the voters until an exhaustive budget allocation is found, or
            one that is no longer feasible with the initial budget constraint.
        binary_sat : bool, optional
            Uses the inner algorithm for binary satisfaction if set to `True`. Should typically be used with approval
            ballots to gain on the runtime. Automatically set to `True` if an approval profile is given.
        verbose : bool, optional
            (De)Activate the display of additional information.
    Returns
    -------
        :py:class:`~pabutools.rules.budgetallocation.BudgetAllocation` | list[:py:class:`~pabutools.rules.budgetallocation.BudgetAllocation`]
            The selected projects if resolute (`resoluteness` = True), or the set of selected projects if irresolute
            (`resoluteness = False`).
    """
    if verbose:
        print(f"Initial budget per voter is: {initial_budget_per_voter}")
    voters = []
    for index, sat in enumerate(sat_profile):
        voters.append(
            MESVoter(
                index,
                sat.ballot,
                sat,
                initial_budget_per_voter,
                sat_profile.multiplicity(sat),
            )
        )
        index += 1

    projects = set()
    for p in instance.difference(set(initial_budget_allocation)):
        mes_p = MESProject(p)
        total_sat = 0
        for i, v in enumerate(voters):
            indiv_sat = v.sat.sat_project(p)
            if indiv_sat > 0:
                total_sat += v.total_sat_project(p)
                mes_p.supporter_indices.append(i)
                if binary_sat:
                    mes_p.unique_sat_supporter = indiv_sat
                else:
                    mes_p.sat_supporter_map[v] = indiv_sat
        if total_sat > 0:
            if p.cost > 0:
                mes_p.total_sat = total_sat
                afford = frac(p.cost, total_sat)
                mes_p.initial_affordability = afford
                mes_p.affordability = afford
                projects.add(mes_p)
            else:
                initial_budget_allocation.append(p)

    previous_outcome: BudgetAllocation | list[BudgetAllocation] = initial_budget_allocation

    while True:
        all_budget_allocations: list[BudgetAllocation] = []
        mes_inner_algo(
            instance,
            profile,
            voters,
            copy(projects),
            tie_breaking,
            copy(initial_budget_allocation),
            all_budget_allocations,
            resoluteness,
            verbose,
            mes_data_store
        )
        if resoluteness:
            outcome = all_budget_allocations[0]
            if voter_budget_increment is None:
                return outcome
            if not instance.is_feasible(outcome):
                return previous_outcome
            if instance.is_exhaustive(outcome, available_projects=projects):
                return outcome
            initial_budget_per_voter += voter_budget_increment
            previous_outcome = outcome
        else:
            if voter_budget_increment is None:
                return all_budget_allocations
            if any(not instance.is_feasible(o) for o in all_budget_allocations):
                return previous_outcome
            if any(
                instance.is_exhaustive(o, available_projects=projects)
                for o in all_budget_allocations
            ):
                return all_budget_allocations
            initial_budget_per_voter += voter_budget_increment
            previous_outcome = all_budget_allocations
        for voter in voters:
            voter.budget = initial_budget_per_voter
        for p in projects:
            p.affordability = p.initial_affordability


def method_of_equal_shares(
    instance: Instance,
    profile: AbstractProfile,
    sat_class: type[SatisfactionMeasure] | None = None,
    sat_profile: GroupSatisfactionMeasure | None = None,
    tie_breaking: TieBreakingRule | None = None,
    resoluteness: bool = True,
    initial_budget_allocation: Iterable[Project] | None = None,
    voter_budget_increment=None,
    binary_sat=None,
    verbose: bool = False,
) -> BudgetAllocation | list[BudgetAllocation]:
    """
    The Method of Equal Shares (MES). See the website
    `equalshares.net <https://equalshares.net/>`_ for details about how to compute the outcome of the rule. Note that
    the satisfaction measure is asssumed to be additive.

    Parameters
    ----------
        instance: :py:class:`~pabutools.election.instance.Instance`
            The instance.
        profile : :py:class:`~pabutools.election.profile.profile.AbstractProfile`
            The profile.
        sat_class : type[:py:class:`~pabutools.election.satisfaction.satisfactionmeasure.SatisfactionMeasure`]
            The class defining the satisfaction function used to measure the social welfare. It should be a class
            inhereting from pabutools.election.satisfaction.satisfactionmeasure.SatisfactionMeasure.
            If no satisfaction is provided, a satisfaction profile needs to be provided. If a satisfation profile is
            provided, the satisfaction argument is disregarded.
        sat_profile : :py:class:`~pabutools.election.satisfaction.satisfactionmeasure.GroupSatisfactionMeasure`
            The satisfaction profile corresponding to the instance and the profile. If no satisfaction profile is
            provided, but a satisfaction function is, the former is computed from the latter.
        initial_budget_allocation : Iterable[:py:class:`~pabutools.election.instance.Project`]
            An initial budget allocation, typically empty.
        tie_breaking : :py:class:`~pabutools.tiebreaking.TieBreakingRule`, optional
            The tie-breaking rule used.
            Defaults to the lexicographic tie-breaking.
        resoluteness : bool, optional
            Set to `False` to obtain an irresolute outcome, where all tied budget allocations are returned.
            Defaults to True.
        voter_budget_increment : Numeric, optional
            Any value that is not `None` will lead to the iterated variant of MES where `voter_budget_increment` units
            of budget are added to the initial budget of the voters until an exhaustive budget allocation is found, or
            one that is no longer feasible with the initial budget constraint.
        binary_sat : bool, optional
            Uses the inner algorithm for binary satisfaction if set to `True`. Should typically be used with approval
            ballots to gain on the runtime. Automatically set to `True` if an approval profile is given.
        verbose : bool, optional
            (De)Activate the display of additional information.

    Returns
    -------
        :py:class:`~pabutools.rules.budgetallocation.BudgetAllocation` | list[:py:class:`~pabutools.rules.budgetallocation.BudgetAllocation`]
            The selected projects if resolute (`resoluteness` = True), or the set of selected projects if irresolute
            (`resoluteness = False`).
    """
    if tie_breaking is None:
        tie_breaking = lexico_tie_breaking
    if initial_budget_allocation is not None:
        budget_allocation = BudgetAllocation(initial_budget_allocation)
    else:
        budget_allocation = BudgetAllocation()
    if sat_class is None:
        if sat_profile is None:
            raise ValueError("sat_class and sat_profile cannot both be None")
    else:
        if sat_profile is None:
            sat_profile = profile.as_sat_profile(sat_class=sat_class)

    if binary_sat is None:
        binary_sat = isinstance(profile, AbstractApprovalProfile)

    return method_of_equal_shares_scheme(
        instance,
        profile,
        sat_profile,
        frac(instance.budget_limit, profile.num_ballots()),
        budget_allocation,
        tie_breaking,
        resoluteness=resoluteness,
        voter_budget_increment=voter_budget_increment,
        binary_sat=binary_sat,
        verbose=verbose,
        mes_data_store=mes_data_store
    )