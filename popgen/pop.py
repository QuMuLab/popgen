import networkx as nx

def create_serial_pop(plan):
    pop = POP()
    for action in plan:
        pop.add_action(action)

    for i in range(len(plan) - 1):
        pop.link_actions(plan[i], plan[i+1], 'serial')

    return pop

class POP(object):

    def __init__(self):
        self.network = nx.DiGraph()
        self.link_reasons = {}
        self.num_links = 0
        self.init = None
        self.goal = None
        self.ordering_edges = set()
        self.causal_edges = set()

    @property
    def flex(self):

        acts = self.network.number_of_nodes()
        orders = len(set(self.network.edges()) - set([(a,a) for a in self.network.nodes()]))

        # Don't count the init and goal actions
        if self.init and self.goal:
            acts -= 2
            orders -= 2*(acts+1)

        if 1 == acts:
            return 0.0

        return 1.0 - (float(orders) / float(sum(range(1, acts))))

    def add_action(self, a):
        self.network.add_node(a)

        if str(a) == 'init':
            self.init = a
        if str(a) == 'goal':
            self.goal = a

    def link_actions(self, a1, a2, reason):

        if '' == reason:
            self.ordering_edges.add((a1,a2))
        else:
            self.causal_edges.add((a1,a2))

        if self.network.has_edge(a1, a2):
            self.link_reasons[(a1,a2)].add(reason)
        else:
            self.network.add_edge(a1, a2)
            self.link_reasons[(a1,a2)] = set([reason])
        self.num_links += 1

    def unlink_actions(self, a1, a2, reason):
        self.link_reasons[(a1, a2)].remove(reason)

        if 0 == len(self.link_reasons[(a1,a2)]):
            del self.link_reasons[(a1, a2)]
            self.network.remove_edge(a1, a2)
        self.num_links -= 1

    def transitivly_reduce(self):
        for (x, y) in self.ordering_edges - self.causal_edges:
            self.network.remove_edge(x, y)
            if not nx.has_path(self.network, x, y):
                self.network.add_edge(x, y)

    def transativly_close(self):
        all_pairs = dict(nx.all_pairs_shortest_path_length(self.network))
        for a1 in self.network.nodes():
            for a2 in self.network.nodes():
                if a1 != a2:
                    if not self.network.has_edge(a1, a2):
                        if a2 in set(all_pairs[a1].keys()):
                            self.link_actions(a1, a2, 'trans')

    def compute_causal_links(self):
        all_pairs = dict(nx.all_pairs_shortest_path_length(self.network))
        count = 0
        for a1 in self.network.nodes():
            for a2 in self.network.nodes():
                if a1 != a2:
                    if a2 in set(all_pairs[a1].keys()):
                        count += 1
        return count

    def remove_action(self, a):
        self.network.remove_node(a)

    def get_links(self):
        return list(self.link_reasons.keys())

    def analyze_independence(self):

        causal_dependent_count = 0
        reachability = nx.all_pairs_shortest_path(self.network)

        for a1 in self.network.nodes():
            for a2 in self.network.nodes():
                if (a2 not in reachability[a1]) and (a1 not in reachability[a2]):
                    if a1.adds & a2.precond:
                        causal_dependent_count += len(a1.adds & a2.precond)
                        #print "%s can add %s for %s" % (str(a1), str(a1.adds & a2.precond), str(a2))

        return causal_dependent_count

    def __str__(self):
        return "POP with %d actions and %d causal links / ordering constraints" % (self.network.number_of_nodes(), self.compute_causal_links())

    def dot(self, compact=False):

        nodes = self.network.nodes()
        edges = self.network.edges()

        dot_string = "digraph POP {\n    rankdir=LR;\n"

        mapping = {}

        for i, node in enumerate(nodes):
            if compact:
                if node == 'init':
                    dot_string += "    %d [label=\"I\"];\n" % i
                elif node== 'goal':
                    dot_string += "    %d [label=\"G\"];\n" % i
                else:
                    dot_string += "    %d;\n" % i
            else:
                dot_string += "    %d [label=\"%s\"];\n" % (i, node)
            mapping[node] = i

        for edge in edges:
            if compact:
                dot_string += "    %d -> %d;\n" % (mapping[edge[0]], mapping[edge[1]])
            else:
                for reason in self.link_reasons[edge]:
                    if '' == str(reason) and (edge[0], edge[1]) in self.causal_edges:
                        continue
                    if reason.__class__ == str:
                        dot_string += "    %d -> %d [style=dotted label=\"%s\"];\n" % (mapping[edge[0]], mapping[edge[1]], str(reason))
                    else:
                        dot_string += "    %d -> %d [label=\"%s\"];\n" % (mapping[edge[0]], mapping[edge[1]], str(reason))

        dot_string += "}"

        return dot_string

    def __repr__(self):
        return self.__str__()



##############################
##############################
##############################


def example0():
    from krrt.planning.strips.representation import Action, Fluent

    # Fluents
    p1 = Fluent('p1')
    p2 = Fluent('p2')
    g1 = Fluent('g1')
    g2 = Fluent('g2')

    # Actions
    INIT = Action(set(), set([p1, p2]), set(), "init")
    GOAL = Action(set([g1, g2]), set(), set(), "goal")
    a1 = Action(set([p1]), set([g1]), set(), "a1")
    a2 = Action(set([p2]), set([g2]), set(), "a2")

    # POP
    pop = POP()
    pop.add_action(INIT)
    pop.add_action(GOAL)
    pop.add_action(a1)
    pop.add_action(a2)

    pop.link_actions(INIT, a1, p1)
    pop.link_actions(INIT, a2, p2)
    pop.link_actions(a1, GOAL, g1)
    pop.link_actions(a2, GOAL, g2)

    return pop

def example1():
    from krrt.planning.strips.representation import Action, Fluent

    # Fluents
    p1 = Fluent('p1')
    p2 = Fluent('p2')
    p3 = Fluent('p3')
    g1 = Fluent('g1')
    g2 = Fluent('g2')
    g3 = Fluent('g3')

    # Actions
    INIT = Action(set(), set([p1, p2, p3]), set(), "init")
    GOAL = Action(set([g1, g2, g3]), set(), set(), "goal")
    a1 = Action(set([p1]), set([g1]), set(), "a1")
    a2 = Action(set([p2]), set([g2]), set(), "a2")
    a3 = Action(set([p3]), set([g3]), set(), "a3")

    # POP
    pop = POP()
    pop.add_action(INIT)
    pop.add_action(GOAL)
    pop.add_action(a1)
    pop.add_action(a2)
    pop.add_action(a3)

    pop.link_actions(INIT, a1, p1)
    pop.link_actions(INIT, a2, p2)
    pop.link_actions(INIT, a3, p3)
    pop.link_actions(a1, GOAL, g1)
    pop.link_actions(a2, GOAL, g2)
    pop.link_actions(a3, GOAL, g3)

    return pop

def example2():
    from krrt.planning.strips.representation import Action, Fluent

    # Fluents
    p1 = Fluent('p1')
    p2 = Fluent('p2')
    g1 = Fluent('g1')
    g2 = Fluent('g2')

    # Actions
    INIT = Action(set(), set([p1]), set(), "init")
    GOAL = Action(set([g1, g2]), set(), set(), "goal")
    a1 = Action(set([p1]), set([p2,g2]), set(), "a1")
    a2 = Action(set([p2]), set([g1]), set(), "a2")

    # POP
    pop = POP()
    pop.add_action(INIT)
    pop.add_action(GOAL)
    pop.add_action(a1)
    pop.add_action(a2)

    pop.link_actions(INIT, a1, p1)
    pop.link_actions(a1, a2, p2)
    pop.link_actions(a1, GOAL, g2)
    pop.link_actions(a2, GOAL, g1)

    return pop

def example3():
    from krrt.planning.strips.representation import Action, Fluent

    # Fluents
    p1 = Fluent('p1')
    p2 = Fluent('p2')
    p3 = Fluent('p3')
    g = Fluent('g')

    # Actions
    INIT = Action(set(), set([p1]), set(), "init")
    GOAL = Action(set([g]), set(), set(), "goal")
    a1 = Action(set([p1]), set([p2]), set(), "a1")
    a2 = Action(set([p2]), set([p3]), set(), "a2")
    a3 = Action(set([p3]), set([g]), set(), "a3")

    # POP
    pop = POP()
    pop.add_action(INIT)
    pop.add_action(GOAL)
    pop.add_action(a1)
    pop.add_action(a2)
    pop.add_action(a3)

    pop.link_actions(INIT, a1, p1)
    pop.link_actions(a1, a2, p2)
    pop.link_actions(a2, a3, p3)
    pop.link_actions(a3, GOAL, g)

    return pop

def example4():
    from krrt.planning.strips.representation import Action, Fluent

    # Fluents
    p1 = Fluent('p1')
    p2 = Fluent('p2')
    p3 = Fluent('p3')
    g2 = Fluent('g2')
    g3 = Fluent('g3')

    # Actions
    INIT = Action(set(), set([p1, p3]), set(), "init")
    GOAL = Action(set([g2, g3]), set(), set(), "goal")
    a1 = Action(set([p1]), set([p2]), set(), "a1")
    a2 = Action(set([p2]), set([g2]), set(), "a2")
    a3 = Action(set([p3]), set([g3]), set(), "a3")

    # POP
    pop = POP()
    pop.add_action(INIT)
    pop.add_action(GOAL)
    pop.add_action(a1)
    pop.add_action(a2)
    pop.add_action(a3)

    pop.link_actions(INIT, a1, p1)
    pop.link_actions(INIT, a3, p3)
    pop.link_actions(a1, a2, p2)
    pop.link_actions(a2, GOAL, g2)
    pop.link_actions(a3, GOAL, g3)

    return pop

def example5():
    from krrt.planning.strips.representation import Action, Fluent

    # Fluents
    p1 = Fluent('p1')
    p2 = Fluent('p2')
    p31 = Fluent('p31')
    p32 = Fluent('p32')
    p4 = Fluent('p4')
    p5 = Fluent('p5')
    g1 = Fluent('g1')
    g2 = Fluent('g2')

    # Actions
    INIT = Action(set(), set([p1, p2]), set(), "init")
    GOAL = Action(set([g1, g2]), set(), set(), "goal")
    a1 = Action(set([p1]), set([p31]), set(), "a1")
    a2 = Action(set([p2]), set([p32]), set(), "a2")
    a3 = Action(set([p31,p32]), set([p4,p5]), set(), "a3")
    a4 = Action(set([p4]), set([g1]), set(), "a4")
    a5 = Action(set([p5]), set([g2]), set(), "a5")

    # POP
    pop = POP()
    pop.add_action(INIT)
    pop.add_action(GOAL)
    pop.add_action(a1)
    pop.add_action(a2)
    pop.add_action(a3)
    pop.add_action(a4)
    pop.add_action(a5)

    pop.link_actions(INIT, a1, p1)
    pop.link_actions(INIT, a2, p2)
    pop.link_actions(a1, a3, p31)
    pop.link_actions(a2, a3, p32)
    pop.link_actions(a3, a4, p4)
    pop.link_actions(a3, a5, p5)
    pop.link_actions(a4, GOAL, g1)
    pop.link_actions(a5, GOAL, g2)

    return pop

def example6():
    from krrt.planning.strips.representation import Action, Fluent

    # Fluents
    p1 = Fluent('p1')
    p2 = Fluent('p2')
    p3 = Fluent('p3')
    p41 = Fluent('p41')
    p42 = Fluent('p42')
    g1 = Fluent('g1')
    g2 = Fluent('g2')

    # Actions
    INIT = Action(set(), set([p1, p3]), set(), "init")
    GOAL = Action(set([g1, g2]), set(), set(), "goal")
    a1 = Action(set([p1]), set([p2,p41]), set(), "a1")
    a2 = Action(set([p2]), set([g1]), set(), "a2")
    a3 = Action(set([p3]), set([p42]), set(), "a3")
    a4 = Action(set([p41,p42]), set([g2]), set(), "a4")

    # POP
    pop = POP()
    pop.add_action(INIT)
    pop.add_action(GOAL)
    pop.add_action(a1)
    pop.add_action(a2)
    pop.add_action(a3)
    pop.add_action(a4)

    pop.link_actions(INIT, a1, p1)
    pop.link_actions(INIT, a3, p3)
    pop.link_actions(a1, a2, p2)
    pop.link_actions(a1, a4, p41)
    pop.link_actions(a3, a4, p42)
    pop.link_actions(a2, GOAL, g1)
    pop.link_actions(a4, GOAL, g2)

    return pop

def example7():
    from krrt.planning.strips.representation import Action, Fluent

    # Fluents
    p1 = Fluent('p1')
    p2 = Fluent('p2')
    p3 = Fluent('p3')
    g1 = Fluent('g1')
    g2 = Fluent('g2')

    # Actions
    INIT = Action(set(), set([p1, p3]), set(), "init")
    GOAL = Action(set([g1, g2]), set(), set(), "goal")
    a1 = Action(set([p1]), set([p2]), set(), "a1")
    a2 = Action(set([p2]), set([g1]), set(), "a2")
    a3 = Action(set([p3]), set([p2,g2]), set(), "a3")

    # POP
    pop = POP()
    pop.add_action(INIT)
    pop.add_action(GOAL)
    pop.add_action(a1)
    pop.add_action(a2)
    pop.add_action(a3)

    pop.link_actions(INIT, a1, p1)
    pop.link_actions(INIT, a3, p3)
    pop.link_actions(a1, a2, p2)
    pop.link_actions(a2, GOAL, g1)
    pop.link_actions(a3, GOAL, g2)

    return pop

def example8():
    from krrt.planning.strips.representation import Action, Fluent

    # Fluents
    p1 = Fluent('p1')
    p2 = Fluent('p2')
    p3 = Fluent('p3')
    p4 = Fluent('p4')
    g = Fluent('g')

    # Actions
    INIT = Action(set(), set([p4]), set(), "init")
    GOAL = Action(set([g]), set(), set(), "goal")
    a1 = Action(set([p1,p2,p3]), set([g]), set(), "a1")
    a2 = Action(set([p1,p4]), set([p2,p3]), set(), "a2")
    a3 = Action(set([p2]), set([p1,p4]), set(), "a3")
    a4 = Action(set([p3]), set([p2]), set(), "a4")
    a5 = Action(set([p4]), set([p3]), set(), "a5")

    # POP
    pop = POP()
    pop.add_action(INIT)
    pop.add_action(GOAL)
    pop.add_action(a1)
    pop.add_action(a2)
    pop.add_action(a3)
    pop.add_action(a4)
    pop.add_action(a5)

    pop.link_actions(INIT, a5, p4)
    pop.link_actions(a5, a4, p3)
    pop.link_actions(a4, a3, p2)
    pop.link_actions(a3, a2, p1)
    pop.link_actions(a3, a2, p4)
    pop.link_actions(a3, a1, p1)
    pop.link_actions(a2, a1, p2)
    pop.link_actions(a2, a1, p3)
    pop.link_actions(a1, GOAL, g)

    return pop
