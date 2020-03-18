
import os
import time
import random

CACHE = {}

def linearize(pop, number = 0):
    if number:
        return compute_bounded_plans(pop, number)
    else:
        return compute_plans(pop, set(), set([pop.init]))

def count_linearizations_sat(pop):
    from krrt.sat.CNF import Formula, Not

    F = Formula()
    A = pop.network.nodes()

    # Add the original orderings
    for e in pop.ordering_edges:
        F.addClause([e])

    # Make it serial
    for a1 in A:
        for a2 in A:
            if a1 != a2:
                F.addClause([(a1,a2), (a2,a1)])

    # Make it transitive
    for a1 in A:
        F.addClause([Not((a1,a1))])
        for a2 in A:
            for a3 in A:
                F.addClause([Not((a1,a2)), Not((a2,a3)), (a1,a3)])

    # Solve!
    F.writeCNF("count-linears.cnf")
    os.system("./sharpSAT count-linears.cnf")
    return 0

def count_linearizations(pop):
    global CACHE
    CACHE = {}
    degrees = pop.network.in_degree()
    for a in degrees:
        if pop.network.has_edge(a,a):
            degrees[a] = degrees[a] - 1
    return count_plans(pop, set(), set(filter(lambda a: degrees[a] == 0, pop.network.nodes())))

def compute_linflex(pop):

    acts = pop.network.number_of_nodes()

    if pop.init and pop.goal:
        acts -= 2

    if 1 == acts:
        return 0.0

    linears = float(count_linearizations(pop))
    possible_linears = float(reduce(lambda x,y: x*y, range(1, acts+1), 1.0))

    #print "LinFlex: %f / %f = %f" % (linears, possible_linears, linears / possible_linears)

    return linears / possible_linears

def check_successor(pop, seen, successor):
    return set([item[0] for item in pop.network.in_edges(successor)]) - set([successor]) <= seen

def compute_plans(pop, seen, possible):
    if 0 == len(possible):
        return [[]]

    #print "Call:\n Seen: %s\n Possible: %s\n\n" % (str(seen), str(possible))
    #time.sleep(1)

    plans = []

    for action in possible:

        new_possible = set()

        for successor in [item[1] for item in pop.network.out_edges(action)]:
            if successor != action and check_successor(pop, seen | set([action]), successor):
                new_possible.add(successor)

        new_plans = compute_plans(pop, seen | set([action]), (possible - set([action])) | new_possible)
        plans.extend([[action] + item for item in new_plans])

    #print "Returning Plans: %s" % str(plans)
    #time.sleep(1)

    return plans

def count_plans(pop, seen, possible):
    global CACHE

    #print "Call:\n Seen: %s\n Possible: %s\n" % (str(seen), str(possible))

    hash_val = '/'.join(sorted([str(hash(item)) for item in list(seen)]))

    if hash_val in CACHE:
        return CACHE[hash_val]

    if 0 == len(possible):
        return 1

    total = 0
    for action in possible:
        new_possible = set()
        for successor in [item[1] for item in pop.network.out_edges(action)]:
            if successor != action and check_successor(pop, seen | set([action]), successor):
                new_possible.add(successor)

        #print "New Possible for %s: %s\n\n" % (str(action), str(new_possible))

        total += count_plans(pop, seen | set([action]), (possible - set([action])) | new_possible)

    CACHE[hash_val] = total

    return total

def compute_bounded_plans(pop, bound):
    plans = []
    seen = set()
    while len(plans) < bound:
        new_plan = generate_random_plan(pop, set(), set([pop.init]))
        hash_val = ','.join([str(hash(item)) for item in new_plan])
        if hash_val not in seen:
            seen.add(hash_val)
            plans.append(new_plan)

    return plans

def generate_random_plan(pop, seen, possible):
    if 0 == len(possible):
        return []

    next_action = random.choice(list(possible))

    new_possible = set()

    for successor in [item[1] for item in pop.network.out_edges(next_action)]:
        if check_successor(pop, seen | set([next_action]), successor):
            new_possible.add(successor)

    return [next_action] + generate_random_plan(pop, seen | set([next_action]), (possible - set([next_action])) | new_possible)
