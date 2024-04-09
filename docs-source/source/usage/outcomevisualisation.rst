Outcome Visualisation
=====================

For reference, see the module :py:mod:`~pabutools.visualisation`.

We provide the visualisation for the outcomes of :py:func:`~pabutools.rules.greedywelfare.greedy_utilitarian_welfare` and :py:func:`~pabutools.rules.mes.method_of_equal_shares`. This explains in depth the outcome of the election based on the chosen rule. This includes which projects were selected or rejected, summary statistics about the election, and rule specific information such as effective vote count in :py:func:`~pabutools.rules.method_of_equal_shares.method_of_equal_shares`.

Note that selecting the visualisation option will increase the runtime of the election, however without this option, the runtime will remain the same.

Greedy Utilitarian Welfare
--------------------------

The visualisation for the Greedy Utilitarian Welfare currently works only on additive utility functions.

We provide a way to visualise the results using the class :py:class:`~pabutools.visualisation.visualisation.GreedyWelfareVisualiser`. Note the analytics flag in the function :py:func:`~pabutools.rules.greedywelfare.greedy_utilitarian_welfare` must be set to True to generate the visualisation.

.. code-block:: python

    from pabutools.visualisation import GreedyWelfareVisualiser
    from pabutools.rules.greedywelfare import greedy_utilitarian_welfare
    from pabutools import election
    from pabutools.election import Cost_Sat

    instance, profile = election.parse_pabulib("./{path_to_election_file}.pb")
    outcome = greedy_utilitarian_welfare(instance, profile, sat_class=Cost_Sat, analytics=True)

    visualiser = GreedyWelfareVisualiser(profile, instance, outcome.details)
    visualiser.render("./{path_to_output_file}/")

The visualisation will be saved in the specified path. 

Note that the visualisation is only available for additive utility functions.