
# from krrt.utils import get_opts
# from krrt.planning.strips.representation import parse_problem, generate_action, Action
# from krrt.planning import parse_output_FF, parse_output_popf, parse_output_ipc, parse_output_mp


import argparse
import networkx as nx

import popgen.tarskilite as tl


from popgen.pop import POP
from popgen.linearizer import count_linearizations


def make_layered_POP(layered_plan, domain = 'domain.pddl', problem = 'prob.pddl', popfout = 'POPF.out'):
    raise NotImplementedError("Modern Layered POP not implemented yet")

    prob = tl.STRIPS(domain, problem)
    allF = prob.fluents
    allA = prob.actions
    I = prob.init
    G = prob.goal

    pop = POP()
    F = set([])
    A = set([])
    action_names = set()
    a_index = 1

    # Init action
    init = Action(set([]), I, set([]), "init")
    pop.add_action(init)
    F |= init.adds
    A.add(init)

    new_layered_plan = []

    # Normal actions
    for layer in layered_plan:
        new_layered_plan.append([])
        for act in layer:
            #a = generate_action(allA[act.operator], act)
            a = allA[str(act)[1:-1]].copy()
            pop.add_action(a)
            F |= a.adds | a.precond | a.dels

            act_name = str(a)
            if act_name in action_names:
                a.operator = a.operator + ("-%d" % a_index)
                a_index += 1

            assert a not in A

            A.add(a)
            new_layered_plan[-1].append(a)
            action_names.add(str(a))


    layered_plan = new_layered_plan

    # Goal action
    goal = Action(G, set([]), set([]), "goal")
    pop.add_action(goal)
    F |= goal.precond
    A.add(goal)

    pop.F = F
    pop.A = A
    pop.I = I
    pop.G = G

    pop.init = init
    pop.goal = goal

    # Add links from the initial action and the goal action
    for act in layered_plan[0]:
        pop.link_actions(init, act, "init")
    for act in layered_plan[-1]:
        pop.link_actions(act, goal, "goal")

    # Add links in between all of the layers
    for i in range(len(layered_plan) - 1):
        for acti in layered_plan[i]:
            for actj in layered_plan[i+1]:
                pop.link_actions(acti, actj, "")

    return pop

def lift_POP(domain, problem, pfile, serialized = False):

    prob = tl.STRIPS(domain, problem)
    allF = prob.fluents
    allA = {str(a): a for a in prob.actions}
    I = prob.init
    G = prob.goal

    # parse the plan file
    with open(pfile, 'r') as f:
        lines = [l.strip() for l in f.readlines()]
        plan = [l for l in lines if l.startswith('(')]

    pop = POP()

    F = set()
    A = set()
    action_names = set()
    a_index = 1

    indices = {None: 99999} # Should be larger than any plan we need to deal with
    reverse_indices = {}
    index = 1

    # Init action
    init = tl.Action("init", set(), I, set())
    pop.add_action(init)
    F |= init.adds
    A.add(init)
    indices[init] = 0
    reverse_indices[0] = init

    # Normal actions
    for act in plan:
        orig_act = allA[act[1:-1]]
        a = tl.Action(orig_act.name, orig_act.pres, orig_act.adds, orig_act.dels)
        pop.add_action(a)
        F |= a.adds | a.pres | a.dels

        if act in action_names:
            a.name = a.name + ("-%d" % a_index)
            a_index += 1

        assert a not in A

        A.add(a)
        indices[a] = index
        reverse_indices[index] = a
        index += 1
        action_names.add(str(a))

    # Goal action
    goal = tl.Action("goal", G, set(), set())
    pop.add_action(goal)
    F |= goal.pres
    A.add(goal)
    indices[goal] = index
    reverse_indices[index] = goal

    pop.F = F
    pop.A = A
    pop.I = I
    pop.G = G

    pop.init = init
    pop.goal = goal

    assert len(A) == len(set([str(item) for item in A]))

    # If a serialized plan was called for, make sure the actions are in their original order
    if serialized:
        for i in range(index):
            pop.link_actions(reverse_indices[i], reverse_indices[i+1], "serial")
        return pop

    adders = {}
    deleters = {}

    for f in F:
        adders[f] = set([])
        deleters[f] = set([])

    for a in A:
        for f in a.adds:
            adders[f].add(a)
        for f in a.dels:
            deleters[f].add(a)

    for act in A:
        for p in act.pres:
            # Find the earliest adder of p that isn't threatened
            dels_before = set([x for x in deleters[p] if indices[x] < indices[act]])
            dels_after = (deleters[p] - dels_before) - set([act])

            latest_deleter = -1

            for deleter in dels_before:
                if indices[deleter] > latest_deleter:
                    latest_deleter = indices[deleter]

            assert 0 == len(dels_before) or latest_deleter > -1
            assert latest_deleter < indices[act]

            earliest_adder = None

            for adder in adders[p]:
                if indices[adder] >= latest_deleter and indices[adder] < indices[earliest_adder]:
                    earliest_adder = adder

            err_info = "\n\nDom:  %s\nProb: %s\nProp: %s" % (domain, problem, str(p))
            assert earliest_adder is not None, err_info
            assert indices[earliest_adder] < indices[act], "%s\n\n%s\n%s\n\n" % (err_info, str(earliest_adder), str(act))
            assert latest_deleter <= indices[earliest_adder], err_info

            # We now have an unthreatened adder of fluent p for action act
            #  - Add the causal link
            pop.link_actions(earliest_adder, act, p)

            #  - Forbid the threatening actions
            for deleter in dels_before:
                #pop.link_actions(deleter, earliest_adder, (earliest_adder, act, p))
                if deleter != earliest_adder:
                    pop.link_actions(deleter, earliest_adder, "! %s" % str(p))

            for deleter in dels_after:
                #pop.link_actions(act, deleter, (adder, act, p))
                pop.link_actions(act, deleter, "! %s" % str(p))

    # Ensure an ordering of all actions after the initial state, and before the goal state
    shortest_paths = dict(nx.all_pairs_shortest_path_length(pop.network))
    for act in A:

        if act not in shortest_paths[init]:
            pop.link_actions(init, act, "init")

        if goal not in shortest_paths[act]:
            pop.link_actions(act, goal, "goal")

    assert nx.is_directed_acyclic_graph(pop.network)

    return pop



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Lift a plan to a POP')
    parser.add_argument('--domain', type=str, help='PDDL domain file', required=True)
    parser.add_argument('--problem', type=str, help='PDDL problem file', required=True)
    parser.add_argument('--plan', type=str, help='Classical plan file', required=True)
    parser.add_argument('--stats', action='store_true', help='Print POP stats')
    parser.add_argument('--dot', action='store_true', help='Print the expressive dot format')
    parser.add_argument('--smalldot', action='store_true', help='Print the concise dot format')
    parser.add_argument('--count', action='store_true', help='Print the number of linearizations')
    args = parser.parse_args()

    pop = lift_POP(args.domain, args.problem, args.plan)

    # if 'COUNT' in flags:
    if args.count:
        print("\nLinearizations: %d\n" % count_linearizations(pop))
    if args.stats:
        print("\n%s\n" % str(pop))
    if args.dot:
        print(pop.dot())
    if args.smalldot:
        print(pop.dot(True))
