#!/usr/bin/python

from krrt.utils import get_opts, write_file
from krrt.planning.strips.representation import parse_problem, generate_action, Action
from krrt.planning import parse_output_FF, parse_output_popf, parse_output_ipc
from krrt.sat.CNF import OptimizedLevelWeightedFormula

from popgen.linearizer import count_linearizations
from lifter import lift_POP, make_layered_POP
from popgen.pop import POP
from gurobipy import *
import time
import networkx as nx

USAGE_STRING = "\n\
Usage: python encoder.py -<option> <argument> -<option> <argument> ... <FLAG> <FLAG> ...\n\n\
\n\
        Where options are:\n\
          -domain <pddl domain file>\n\
          -prob <pddl problem file>\n\
          -ffout <captured FF output>\n\
          -mercout <captured Mercury output>\n\
        "



def encode_POP_v1(dom, prob, pop, flags, popfile):

    # For sanitization, make sure we close the pop
    pop.transativly_close()

    allF, allA, I, G = parse_problem(dom, prob)

    F = pop.F
    A = pop.A
    I = pop.I
    G = pop.G

    init = pop.init
    goal = pop.goal

    adders = {}
    deleters = {}
    needers = {}

    for f in F:
        adders[f] = set([])
        deleters[f] = set([])
        needers[f] = set([])

    for a in A:
        for f in a.adds:
            adders[f].add(a)
        for f in a.dels:
            deleters[f].add(a)
        for f in a.precond:
            needers[f].add(a)

    times = [time.time()]

    try:

        # Create a new model
        m = Model("min_reorder")
        m.Params.Threads = 1

        # Create support variables
        sup_vars = []
        sup_var_mapping = {}
        for f in F:
            sup_var_mapping[f] = {}
            for a2 in needers[f]:
                sup_var_mapping[f][a2] = {}
                for a1 in adders[f]:
                    if a1 != a2:
                        sup_vars.append(m.addVar(vtype=GRB.BINARY, name="X_%s_%s_%s" % (a1, a2, f)))
                        sup_var_mapping[f][a2][a1] = sup_vars[-1]

        # Create the promotion / demotion variables
        interference_vars = []
        interference_var_mapping = {}
        for f in F:

            interference_var_mapping[f] = {}

            for a1 in (needers[f] | adders[f]):
                for a2 in deleters[f]:

                    if a1 != a2:
                        if a1 not in interference_var_mapping[f]:
                            interference_var_mapping[f][a1] = {}
                        if a2 not in interference_var_mapping[f]:
                            interference_var_mapping[f][a2] = {}

                        if a2 not in interference_var_mapping[f][a1]:
                            interference_vars.append(m.addVar(vtype=GRB.BINARY, name="I_%s_%s_%s" % (a1, a2, f)))
                            interference_var_mapping[f][a1][a2] = interference_vars[-1]

                        if a1 not in interference_var_mapping[f][a2]:
                            interference_vars.append(m.addVar(vtype=GRB.BINARY, name="I_%s_%s_%s" % (a2, a1, f)))
                            interference_var_mapping[f][a2][a1] = interference_vars[-1]


        # Create the ordering variables
        order_vars = []
        order_var_mapping = {}
        for a1 in A:
            order_var_mapping[a1] = {}
            for a2 in A:
                order_vars.append(m.addVar(vtype=GRB.BINARY, name="O_%s_%s" % (a1, a2)))
                order_var_mapping[a1][a2] = order_vars[-1]

        # Integrate new variables
        m.update()

        # Set objective
        m.setObjective(quicksum(order_vars), GRB.MINIMIZE)


        #################
        ## Constraints ##
        #################
        # Mutual exclusion
        counter = 1
        for f in interference_var_mapping:
            for a1 in interference_var_mapping[f]:
                for a2 in interference_var_mapping[f][a1]:
                    if a1 != a2:
                        x = interference_var_mapping[f][a1][a2]
                        y = interference_var_mapping[f][a2][a1]
                        m.addConstr(x + y == 1, "mut_ex_%d" % counter)
                        counter += 1

        # Single supporter
        counter = 1
        for f in F:
            for a2 in sup_var_mapping[f]:
                m.addConstr(quicksum(list(sup_var_mapping[f][a2].values())) == 1, "sup_%d" % counter)
                counter += 1

        # Causal-link protection
        counter = 1
        for f in F:
            for a2 in sup_var_mapping[f]:
                for a1 in sup_var_mapping[f][a2]:
                    for ad in deleters[f]:
                        if a1 != a2 and a1 != ad and a2 != ad:
                            x = sup_var_mapping[f][a2][a1]
                            y = interference_var_mapping[f][ad][a1]
                            z = interference_var_mapping[f][a2][ad]
                            m.addConstr((1 - x) + (y + z) >= 1, "prom_dom_%d" % counter)
                            counter += 1

        # Link support with ordering
        counter = 1
        for f in F:
            for a2 in sup_var_mapping[f]:
                for a1 in sup_var_mapping[f][a2]:
                    if a1 != a2:
                        x = sup_var_mapping[f][a2][a1]
                        y = order_var_mapping[a1][a2]
                        m.addConstr(y - x >= 0, "order_sup_%d" % counter)
                        counter += 1

        # Link intereference with ordering
        counter = 1
        for f in interference_var_mapping:
            for a1 in interference_var_mapping[f]:
                for a2 in interference_var_mapping[f][a1]:
                    if a1 != a2:
                        x = interference_var_mapping[f][a1][a2]
                        y = order_var_mapping[a1][a2]
                        m.addConstr(y - x >= 0, "order_inter_%d" % counter)
                        counter += 1

        # Transitive closure
        counter = 1
        for a1 in A:
            for a2 in A:
                for a3 in A:
                    x = order_var_mapping[a1][a2]
                    y = order_var_mapping[a2][a3]
                    z = order_var_mapping[a1][a3]
                    m.addConstr((1 - x) + (1 - y) + z >= 1, "trans_%d" % counter)
                    counter += 1

        # Forbid self loops
        counter = 1
        for a in A:
            m.addConstr(order_var_mapping[a][a] == 0, "noloop_%d" % counter)
            counter += 1

        # Init and goal
        m.addConstr(order_var_mapping[init][goal] == 1)
        for a in A - set([init, goal]):
            m.addConstr(order_var_mapping[init][a] == 1)
            m.addConstr(order_var_mapping[a][goal] == 1)

        #############################

        times.append(time.time())

        m.optimize()

        #for v in m.getVars():
        #    print v.varName, v.x

        print('\nObj:', m.objVal)

        times.append(time.time())

        print("Encoding Time: %f" % (times[1] - times[0]))
        print("Solving Time: %f\n" % (times[2] - times[1]))

    except GurobiError as e:
        print('Error reported:', end=' ')
        print(e)


def encode_POP_v2(dom, prob, pop, flags, popfile):

    # For sanitization, make sure we close the pop
    pop.transativly_close()

    allF, allA, I, G = parse_problem(dom, prob)

    F = pop.F
    A = pop.A
    I = pop.I
    G = pop.G

    init = pop.init
    goal = pop.goal

    adders = {}
    deleters = {}
    needers = {}

    for f in F:
        adders[f] = set([])
        deleters[f] = set([])
        needers[f] = set([])

    for a in A:
        for f in a.adds:
            adders[f].add(a)
        for f in a.dels:
            deleters[f].add(a)
        for f in a.precond:
            needers[f].add(a)

    times = [time.time()]

    # Create a new model
    m = Model("min_reorder")
    m.Params.Threads = 1

    # Create the vars for each action
    v2a = {}
    a2v = {}
    for a in A:
        a2v[a] = m.addVar(vtype=GRB.BINARY, name="act_%s" % str(a))
        m.update()
        v2a[a2v[a]] = a

    # Create the vars for each action ordering
    v2o = {}
    o2v = {}
    for a1 in A:
        for a2 in A:
            o2v[(a1,a2)] = m.addVar(vtype=GRB.BINARY, name="ord_%s_%s" % (str(a1), str(a2)))
            m.update()
            v2o[o2v[(a1,a2)]] = (a1,a2)

    # Create the vars for each possible action support
    v2s = {}
    s2v = {}
    for a2 in A:
        for p in a2.precond:
            for a1 in adders[p]:
                s2v[(a1,p,a2)] = m.addVar(vtype=GRB.BINARY, name="sup_%s_%s_%s" % (str(a1), str(p), str(a2)))
                m.update()
                v2s[s2v[(a1,p,a2)]] = (a1,p,a2)


    # Integrate new variables
    m.update()

    order_count = 1 + len(list(o2v.keys()))

    # Set objective
    # Use the first if only optimizing for the number of ordering constraints
    m.setObjective(quicksum(list(v2o.keys())), GRB.MINIMIZE)
    #m.setObjective(quicksum(v2o.keys() + [order_count * var for var in v2a.keys()]), GRB.MINIMIZE)



    #################
    ## Constraints ##
    #################

    # Uncomment the following if every action should be included
    for a in A:
        m.addConstr(a2v[a] == 1)

    # Add the antisymmetric ordering constraints
    for a in A:
        m.addConstr(o2v[(a,a)] == 0)

    # Add the transitivity constraints
    for a1 in A:
        for a2 in A:
            for a3 in A:
                x = o2v[(a1,a2)]
                y = o2v[(a2,a3)]
                z = o2v[(a1,a3)]
                m.addConstr((1 - x) + (1 - y) + z >= 1)

    # Add the ordering -> actions constraints
    for a1 in A:
        for a2 in A:
            m.addConstr(o2v[(a1,a2)] <= a2v[a1])
            m.addConstr(o2v[(a1,a2)] <= a2v[a2])

    # Init and goal
    m.addConstr(o2v[(init,goal)] == 1)
    for a in A - set([init, goal]):
        m.addConstr((1 - a2v[a]) + o2v[(init,a)] == 1)
        m.addConstr((1 - a2v[a]) + o2v[(a,goal)] == 1)

    # Orderings exclude one another
    for a1 in A:
        for a2 in A:
            m.addConstr(o2v[(a1,a2)] + o2v[(a2,a1)] <= 1)

    # Ensure that we have a goal and init action.
    m.addConstr(a2v[init] == 1)
    m.addConstr(a2v[goal] == 1)

    # Satisfy all the preconditions
    for a2 in A:
        for p in a2.precond:
            m.addConstr((1 - a2v[a2]) + quicksum([s2v[(a1,p,a2)] for a1 in [x for x in adders[p] if x is not a2]]) >= 1)

    # Create unthreatened support
    for a2 in A:
        for p in a2.precond:

            # Can't support yourself (not strictly neccessary, but useful for visualizing output)
            if (a2, p, a2) in s2v:
                m.addConstr(s2v[(a2, p, a2)] == 0)

            for a1 in [x for x in adders[p] if x is not a2]:

                # Support implies ordering
                m.addConstr((1 - s2v[(a1,p,a2)]) + o2v[(a1,a2)] >= 1)

                # Forbid threats
                #print "\n%s--%s-->%s: %s" % (str(a1), str(p), str(a2), str(deleters[p]))
                for ad in [x for x in deleters[p] if x not in set([a1,a2])]:
                    #print "...%s--%s-->%s: %s" % (str(a1), str(p), str(a2), str(ad))
                    m.addConstr((1 - s2v[(a1,p,a2)]) + (1 - a2v[ad]) + o2v[(ad,a1)] + o2v[(a2,ad)] >= 1)


    #############################

    times.append(time.time())

    m.optimize()

    #for v in m.getVars():
    #    print v.varName, v.x

    print('\nObj:', m.objVal)
    print("Actions: %d / %d" % (sum([int(v.x) for v in list(v2a.keys())]), len(A)))
    print('Orderings:', sum([int(v.x) for v in list(v2o.keys())]))

    times.append(time.time())

    print("Encoding Time: %f" % (times[1] - times[0]))
    print("Solving Time: %f\n" % (times[2] - times[1]))

    if popfile:
        p = POP()
        for act in A:
            p.add_action(act)

        for v in list(v2s.keys()):
            if 1 == int(v.x):
                p.link_actions(v2s[v][0], v2s[v][2], str(v2s[v][1]))

        for v in list(v2o.keys()):
            if 1 == int(v.x):
                p.link_actions(v2o[v][0], v2o[v][1], '')






        ######################
        ##  OUTPUT SETTINGS ##
        ######################

        # Comment out if you want to see all of the edges in the closure
        p.transitivly_reduce()

        # Comment out if you want the initial state dummy action to be included
        p.remove_action(p.init)

        # Change to True if you want just the nodes / edges and not the labels
        write_file(popfile, p.dot(False))





if __name__ == '__main__':
    import os
    myargs, flags = get_opts()

    if '-domain' not in myargs:
        print("Must include domain to lift:")
        print(USAGE_STRING)
        os._exit(1)

    dom = myargs['-domain']

    if '-prob' not in myargs:
        print("Must include problem to lift:")
        print(USAGE_STRING)
        os._exit(1)

    prob = myargs['-prob']

    if '-ffout' not in myargs and '-mercout' not in myargs:
        print("Must include FF or Mercury output to parse:")
        print(USAGE_STRING)
        os._exit(1)

    if '-version' not in myargs:
        encode_POP = encode_POP_v2
    elif '1' == myargs['-version']:
        encode_POP = encode_POP_v1
    elif '2' == myargs['-version']:
        encode_POP = encode_POP_v2

    popfile = ''
    if '-popfile' in myargs:
        popfile = myargs['-popfile']

    if '-ffout' in myargs:
        plan = parse_output_FF(myargs['-ffout'])
    elif '-mercout' in myargs:
        plan = parse_output_ipc(myargs['-mercout'])
    else:
        assert False, "How did you even get here?!?"

    pop = lift_POP(dom, prob, plan, True)

    encode_POP(dom, prob, pop, flags, popfile)

