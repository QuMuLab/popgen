
import argparse
from bauhaus import Encoding, proposition, And, Or

from lifter import lift_POP

import tarskilite as tl


class Hashable:
    def __hash__(self):
        return hash(str(self))

    def __eq__(self, __value: object) -> bool:
        return hash(self) == hash(__value)

    def __repr__(self):
        return str(self)

def encode_POP(pop, cmdargs):

    # For sanitization, make sure we close the pop
    pop.transativly_close()

    F = pop.F
    A = pop.A

    init = pop.init
    goal = pop.goal

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

    E = Encoding()

    @proposition(E)
    class Action(Hashable):
        def __init__(self, name):
            self.name = name

        def __repr__(self):
            return f"Action({self.name})"

        def __str__(self):
            return self.name

        def __hash__(self) -> int:
            return hash(self.name)

    @proposition(E)
    class Order(Hashable):
        def __init__(self, a1, a2):
            self.a1 = a1
            self.a2 = a2

        def __repr__(self):
            return f"Order({self.a1}, {self.a2})"

        def __str__(self):
            return f"{self.a1} -> {self.a2}"

    @proposition(E)
    class Support(Hashable):
        def __init__(self, a1, p, a2):
            self.a1 = a1
            self.p = p
            self.a2 = a2

        def __repr__(self):
            return f"Support({self.a1}, {self.p}, {self.a2})"

        def __str__(self):
            return f"{self.a1} supports {self.p} for {self.a2}"

    actions = [Action(a) for a in A]
    orders = [Order(a1, a2) for a1 in A for a2 in A]
    supports = [Support(a1, p, a2) for a2 in A for p in a2.pres for a1 in adders[p]]

    v2a = {action: action.name for action in actions}
    a2v = {action.name: action for action in actions}

    v2o = {order: (order.a1, order.a2) for order in orders}
    o2v = {(order.a1, order.a2): order for order in orders}

    v2s = {support: (support.a1, support.p, support.a2) for support in supports}
    # s2v = {(support.a1, support.p, support.a2): support for support in supports}

    clauses = []

    # Add the antisymmetric ordering constraints
    clauses.extend([~Order(a, a) for a in A])

    # Add the transitivity constraints
    for a1 in A:
        for a2 in A:
            for a3 in A:
                clauses.append((Order(a1, a2) & Order(a2, a3)) >> Order(a1, a3))

    # Add the ordering -> actions constraints
    for a1 in A:
        for a2 in A:
            clauses.append(Order(a1, a2) >> (Action(a1) & Action(a2)))

    # Make sure everything comes after the init, and before the goal
    for a in A:
        if a is not init:
            clauses.append(Action(a) >> Order(init, a))
        if a is not goal:
            clauses.append(Action(a) >> Order(a, goal))

    # Ensure that we have a goal and init action.
    clauses.append(Action(init))
    clauses.append(Action(goal))

    # Satisfy all the preconditions
    for a2 in A:
        for p in a2.pres:
            clauses.append(Action(a2) >> Or([Support(a1, p, a2) for a1 in [x for x in adders[p] if x is not a2]]))

    # Create unthreatened support
    for a2 in A:
        for p in a2.pres:
            for a1 in [x for x in adders[p] if x is not a2]:

                # Support implies ordering
                clauses.append(Support(a1, p, a2) >> Order(a1, a2))

                # Forbid threats
                for ad in deleters[p]:
                    if ad not in [a1, a2]:
                        clauses.append(Support(a1, p, a2) >> (~Action(ad) | Order(ad, a1) | Order(a2, ad)))


    if cmdargs.serial:
        for a1 in A:
            for a2 in A:
                if a1 is not a2:
                    clauses.append((Action(a1) & Action(a2)) >> (Order(a1, a2) | Order(a2, a1)))

    if cmdargs.allact:
        for a in A:
            clauses.append(Action(a))

    if cmdargs.deorder:
        for (ai,aj) in pop.get_links():
            clauses.append(~Order(aj, ai))

    F = And(clauses).compile().simplify()
    assert False, "Made it!"

    # TODO: Figure out how to get the soft unit clauses into the patrially weighted CNF

    # Now add the soft clauses.
    for a1 in A:
        for a2 in A:
            formula.addClause([-o2v[(a1,a2)]], 1, 1)

        # formula.addClause([Not(a1)], COST, 2)
        formula.addClause([-a2v[a1]], 1, 2)

    formula.writeCNF(output+'.wcnf')
    formula.writeCNF(output+'.cnf', hard=True)
    mapping_lines = []
    for v in v2a:
        mapping_lines.append("%d %s in plan" % (v, str(v2a[v])))
    for v in v2o:
        mapping_lines.append("%d %s is ordered before %s" % (v, str(v2o[v][0]), str(v2o[v][1])))
    for v in v2s:
        mapping_lines.append("%d %s supports %s with %s" % (v, str(v2s[v][0]), str(v2s[v][2]), str(v2s[v][1])))
    write_file(output+'.map', mapping_lines)

    print('')
    print("Vars: %d" % formula.num_vars)
    print("Clauses: %d" % formula.num_clauses)
    print("Soft: %d" % len(formula.getSoftClauses()))
    print("Hard: %d" % len(formula.getHardClauses()))
    print("Max Weight: %d" % formula.top_weight)
    print('')

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Generate a wcnf file for a planning problem.')

    parser.add_argument('-d', '--domain', dest='domain', help='Domain file', required=True)

    parser.add_argument('-p', '--problem', dest='problem', help='Problem file', required=True)

    parser.add_argument('-s', '--plan', dest='plan', help='Plan file', required=True)

    parser.add_argument('-o', '--output', dest='output', help='Output file', required=True)

    parser.add_argument('--allact', dest='allact', action='store_true', help='Include all actions in the plan')
    parser.add_argument('--serial', dest='serial', action='store_true', help='Force it to be serial')
    parser.add_argument('--deorder', dest='deorder', action='store_true', help='Force it to be a deordering')

    args = parser.parse_args()
    pop = lift_POP(args.domain, args.problem, args.plan, True)

    encode_POP(pop, args)
