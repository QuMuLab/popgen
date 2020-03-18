
import os, time

from krrt.utils import get_opts, run_experiment, match_value, get_value, load_CSV, write_file, append_file, read_file, get_file_list, run_command

from domains import DOMAINS, GOOD_DOMAINS, FORBIDDEN_DOMAINS
from settings import *


USAGE_STRING = """
Usage: python run_all.py <TASK> -domain <domain> ...

        Where <TASK> may be:
          ff: Solve all of the problems with FF.
          mp: Solve all of the problems with Mp.
          popf: Solve all of the problems with POPF2.
          mercury: Solve all of the problems with Mercury.
          allplanners: Solve all the problems with Mp, POPF2, and Mercury.
          encode: Try all of the encodings. (use "ulimit -v 1300000")
          encode-nocount: Try all of the encodings, but don't count the linearizations.
          mip: Solve the mip encodings
          solved-stats: Compute the number of problems solved by every planner
          merc-flex: Compute the flex values for the Mercury solutions, lifted with RX.
          popf-flex: Compute the flex values for the POPF solutions.
          mp-flex: Compute the flex values for the MP solutions.

        Additional Options:
          -solver <ff/mp/popf/mercury>: Only generate data for a given solver
          -domain ALL: Use all of the IPC STRIPS domains
        """

FF = 0

MP = 1
POPF = 2
MERCURY = 3

ALL = 4 # Will no longer include FF


def filter_solved_domains(domain, dom_probs, solver=ALL):
    toRet = []
    for (dom, prob) in dom_probs:
        prob_name = prob.split('/')[-1].split('.pddl')[0]

        if solver == FF:
            if os.path.exists("RESULTS/plans/%s/%s.ff" % (domain, prob_name)):
                toRet.append((dom, prob))

        elif solver == MP:
            if os.path.exists("RESULTS/plans/%s/%s.mp" % (domain, prob_name)):
                toRet.append((dom, prob))

        elif solver == POPF:
            if os.path.exists("RESULTS/plans/%s/%s.popf" % (domain, prob_name)):
                toRet.append((dom, prob))

        elif solver == MERCURY:
            if os.path.exists("RESULTS/plans/%s/%s.merc" % (domain, prob_name)):
                toRet.append((dom, prob))
        else:
            if os.path.exists("RESULTS/plans/%s/%s.mp" % (domain, prob_name)) and os.path.exists("RESULTS/plans/%s/%s.popf" % (domain, prob_name)) and os.path.exists("RESULTS/plans/%s/%s.merc" % (domain, prob_name)):
                toRet.append((dom, prob))

    return toRet


def solved_stats(domain):
    dom_probs = DOMAINS[domain]
    print(','.join(map(str, [domain,
                             len(dom_probs),
                             len(filter_solved_domains(domain, dom_probs, MERCURY)),
                             len(filter_solved_domains(domain, dom_probs, MP)),
                             len(filter_solved_domains(domain, dom_probs, POPF))])))


def popf_flex(domain):

    if domain in FORBIDDEN_DOMAINS:
        return

    total = [1.0, 0]
    count = 0

    for (d,p) in filter_solved_domains(domain, DOMAINS[domain], POPF):
        probname = p.split('/')[-1].split('.')[0]
        os.system("timeout 600 python lifter.py -domain %s -prob %s -popfout RESULTS/plans/%s/%s.popf STATS > OUT.lifter 2>&1" % (d, p, domain, probname))

        if match_value('OUT.lifter', "POP with ([0-9]+) actions"):
            lifted_actions = get_value('OUT.lifter', "POP with ([0-9]+) actions", int)
            lifted_orderings = get_value('OUT.lifter', "actions and ([0-9]+) causal links", int)

            if lifted_actions > 0:
                flex = 1.0 - (float(lifted_orderings) / float(sum(range(1,lifted_actions))))
                total[0] *= flex
                total[1] += flex
                count += 1
                append_file('popf-flex.csv', "\n%s,%s,%s,%d,%d,%f" % (domain, d, p, lifted_actions, lifted_orderings, flex))
            else:
                append_file('popf-flex.csv', "\n%s,%s,%s,E,E,E" % (domain, d, p))
        else:
            append_file('popf-flex.csv', "\n%s,%s,%s,E,E,E" % (domain, d, p))

    if count == 0:
        print('{:20s}'.format(domain) + " - / -")
    else:
        print('{:20s}'.format(domain) + " %f / %f" % ((total[0] ** (1.0 / float(count))), (total[1] / float(count))))

def merc_flex(domain):

    if domain in FORBIDDEN_DOMAINS:
        return

    total = [1.0, 0]
    count = 0

    for (d,p) in filter_solved_domains(domain, DOMAINS[domain], MERCURY):
        probname = p.split('/')[-1].split('.')[0]
        os.system("timeout 600 python lifter.py -domain %s -prob %s -mercout RESULTS/plans/%s/%s.merc STATS > OUT.lifter 2>&1" % (d, p, domain, probname))

        if match_value('OUT.lifter', "POP with ([0-9]+) actions"):
            lifted_actions = get_value('OUT.lifter', "POP with ([0-9]+) actions", int)
            lifted_orderings = get_value('OUT.lifter', "actions and ([0-9]+) causal links", int)

            if lifted_actions > 0:
                flex = 1.0 - (float(lifted_orderings) / float(sum(range(1,lifted_actions))))
                total[0] *= flex
                total[1] += flex
                count += 1
                append_file('merc-flex.csv', "\n%s,%s,%s,%d,%d,%f" % (domain, d, p, lifted_actions, lifted_orderings, flex))
            else:
                append_file('merc-flex.csv', "\n%s,%s,%s,E,E,E" % (domain, d, p))
        else:
            append_file('merc-flex.csv', "\n%s,%s,%s,E,E,E" % (domain, d, p))

    if count == 0:
        print('{:20s}'.format(domain) + " - / -")
    else:
        print('{:20s}'.format(domain) + " %f / %f" % ((total[0] ** (1.0 / float(count))), (total[1] / float(count))))

def mp_flex(domain):

    if domain in FORBIDDEN_DOMAINS:
        return

    total = [1.0, 0]
    count = 0

    for (d,p) in filter_solved_domains(domain, DOMAINS[domain], MP):
        probname = p.split('/')[-1].split('.')[0]
        os.system("timeout 600 python lifter.py -domain %s -prob %s -mpout RESULTS/plans/%s/%s.mp STATS > OUT.lifter 2>&1" % (d, p, domain, probname))

        if match_value('OUT.lifter', "POP with ([0-9]+) actions"):
            lifted_actions = get_value('OUT.lifter', "POP with ([0-9]+) actions", int)
            lifted_orderings = get_value('OUT.lifter', "actions and ([0-9]+) causal links", int)

            if lifted_actions > 0:
                flex = 1.0 - (float(lifted_orderings) / float(sum(range(1,lifted_actions))))
                total[0] *= flex
                total[1] += flex
                count += 1
                append_file('mp-flex.csv', "\n%s,%s,%s,%d,%d,%f" % (domain, d, p, lifted_actions, lifted_orderings, flex))
            else:
                append_file('mp-flex.csv', "\n%s,%s,%s,E,E,E" % (domain, d, p))
        else:
            append_file('mp-flex.csv', "\n%s,%s,%s,E,E,E" % (domain, d, p))

    if count == 0:
        print('{:20s}'.format(domain) + " - / -")
    else:
        print('{:20s}'.format(domain) + " %f / %f" % ((total[0] ** (1.0 / float(count))), (total[1] / float(count))))



def do_mercury(domain):
    dom_probs = DOMAINS[domain]
    args = ["%s %s sol" % (item[0], item[1]) for item in dom_probs]

    results = run_experiment(
        base_command = MERCURY_LOCATION,
        single_arguments = {'domprob': args},
        time_limit = TIME_LIMIT, # 30minute time limit (1800 seconds)
        memory_limit = MEM_LIMIT, # 1gig memory limit (1000 megs)
        results_dir = domain,
        sandbox = 'merc',
        progress_file = None,
        processors = CORES # You've got 8 cores, right?
    )

    timeouts = 0
    memouts = 0
    for res_id in results.get_ids():
        result = results[res_id]
        if os.path.isfile("%s/%d-sandbox-merc/plan_numbers_and_cost" % (domain, res_id)):
            solfile = read_file("%s/%d-sandbox-merc/plan_numbers_and_cost" % (domain, res_id))[-1].split()[0]
            os.system("mv %s/%d-sandbox-merc/sol.%s %s/%s.merc" % (domain, res_id, solfile, domain, result.single_args['domprob'].split(' ')[1].split('/')[-1].split('.pddl')[0]))
        elif result.timed_out:
            timeouts += 1
        elif match_value(result.error_file, 'bad_alloc'):
            memouts += 1

    print("\nTimed out %d times." % timeouts)
    print("Ran out of memory %d times.\n" % memouts)

def do_mp(domain):
    dom_probs = DOMAINS[domain]
    args = ["%s %s -o sol -P 1" % (item[0], item[1]) for item in dom_probs]

    results = run_experiment(
        base_command = MP_LOCATION,
        single_arguments = {'domprob': args},
        time_limit = TIME_LIMIT, # 30minute time limit (1800 seconds)
        memory_limit = MEM_LIMIT, # 1gig memory limit (1000 megs)
        results_dir = domain,
        sandbox = 'mp',
        progress_file = None,
        processors = CORES # You've got 8 cores, right?
    )

    timeouts = 0
    memouts = 0
    for res_id in results.get_ids():
        result = results[res_id]
        if os.path.isfile("%s/%d-sandbox-mp/sol" % (domain, res_id)):
            os.system("mv %s/%d-sandbox-mp/sol %s/%s.mp" % (domain, res_id, domain, result.single_args['domprob'].split(' ')[1].split('/')[-1].split('.pddl')[0]))
        elif result.timed_out:
            timeouts += 1
        elif match_value(result.error_file, 'bad_alloc'):
            memouts += 1

    print("\nTimed out %d times." % timeouts)
    print("Ran out of memory %d times.\n" % memouts)

def do_ff(domain):

    dom_probs = DOMAINS[domain]

    args = ["-o %s -f %s" % (item[0], item[1]) for item in dom_probs]

    results = run_experiment(
        base_command = "ff",
        single_arguments = {'domprob': args},
        time_limit = TIME_LIMIT, # 30minute time limit (1800 seconds)
        memory_limit = MEM_LIMIT, # 1gig memory limit (1000 megs)
        results_dir = domain,
        progress_file = None,
        processors = CORES # You've got 8 cores, right?
    )

    timeouts = 0
    memouts = 0
    for res_id in results.get_ids():
        result = results[res_id]
        if result.timed_out:
            if match_value(result.output_file, 'MemoryError'):
                memouts += 1
            else:
                timeouts += 1
        else:
            os.system("mv %s %s/%s.ff" % (result.output_file, domain, result.single_args['domprob'].split(' ')[-1].split('/')[-1].split('.pddl')[0]))

    print("\nTimed out %d times." % timeouts)
    print("Ran out of memory %d times.\n" % memouts)


def do_popf(domain):

    dom_probs = DOMAINS[domain]

    args = ["%s %s sol" % (item[0], item[1]) for item in dom_probs]

    results = run_experiment(
        base_command = POPF_LOCATION,
        single_arguments = {'domprob': args},
        time_limit = TIME_LIMIT, # 30minute time limit (1800 seconds)
        memory_limit = MEM_LIMIT, # 1gig memory limit (1000 megs)
        results_dir = domain,
        sandbox = 'popf',
        progress_file = None,
        processors = CORES # You've got 8 cores, right?
    )

    timeouts = 0
    memouts = 0
    for res_id in results.get_ids():
        result = results[res_id]
        sols = get_file_list("%s/%d-sandbox-popf/" % (domain, res_id), match_list=['sol'])
        if len(sols) > 0:
            solfile = sorted(map(int, [f.split('.')[-1] for f in sols]))[-1]
            os.system("mv %s/%d-sandbox-popf/sol.%d %s/%s.popf" % (domain, res_id, solfile, domain, result.single_args['domprob'].split(' ')[1].split('/')[-1].split('.pddl')[0]))
        elif result.timed_out:
            timeouts += 1
        elif match_value(result.error_file, 'bad_alloc'):
            memouts += 1

    print("\nTimed out %d times." % timeouts)
    print("Ran out of memory %d times.\n" % memouts)


def do_encode(domain, solver, disable_linears = False):

    if ALL == solver:
        print("Error: Cannot encode both solvers at once (do them separately)")
        return

    if domain in FORBIDDEN_DOMAINS:
        print("Skipping forbidden domain %s" % domain)
        return

    dom_probs = filter_solved_domains(domain, DOMAINS[domain], solver)

    ID = "%s-%s-%s" % (domain, solver, disable_linears)

    os.system("mkdir %s" % ID)
    #os.system("cp ubcsat %s/" % ID)
    os.chdir("./%s" % ID)
    os.system("cp -rf ../RESULTS/plans/%s ." % domain)



    if disable_linears:
        csv_data = "Domain,Prob,Serial,All Actions,Deordering,Time-Lift,Time-Encode,Time-Maxsat,Time-POPAnalysis,Lifted Actions,Encoded Actions,Lifted Constraints,Encoded Constraints,Lifted Optimal,MAXSAT Vars,MAXSAT Clauses,MAXSAT Top Weight\n"
    else:
        csv_data = "Domain,Prob,Serial,All Actions,Deordering,Time-Lift,Time-Encode,Time-Maxsat,Time-POPAnalysis,Lifted Actions,Encoded Actions,Lifted Constraints,Encoded Constraints,Lifted Optimal,Lifted Linears,Encoded Linears,Linear Increase,MAXSAT Vars,MAXSAT Clauses,MAXSAT Top Weight\n"

    write_file("%s.csv" % domain, csv_data)

    for dom,prob in dom_probs:
        # for serial in ['', 'SERIAL']:
        for serial in ['']:
            #for allact in ['', 'ALLACT']:
            for allact in ['ALLACT']:
                for deorder in ['', 'DEORDER']:

                    print("\nDomain: %s" % dom)
                    print("Problem: %s" % prob)
                    #print "Serial: %s" % str(serial == 'SERIAL')
                    #print "All Act.: %s" % str(allact == 'ALLACT')
                    print("Deorder: %s" % str(deorder == 'DEORDER'))

                    prev_time = time.time()
                    prob_name = prob.split('/')[-1].split('.pddl')[0]

                    dir_name = "encoded.%s.%s.%s.%s" % (allact, deorder, domain, prob_name)
                    os.system("mkdir %s" % dir_name)

                    # Run the lifter
                    if MERCURY == solver:
                        solver_opts = "-mercout %s/%s.merc" % (domain, prob_name)
                    elif POPF == solver:
                        solver_opts = "-popfout %s/%s.popf" % (domain, prob_name)
                    elif MP == solver:
                        solver_opts = "-mpout %s/%s.mp" % (domain, prob_name)
                    elif FF == solver:
                        solver_opts = "-ffout %s/%s.ff" % (domain, prob_name)
                    else:
                        assert False, "Error: Bad solver: %s" % str(solver)

                    if disable_linears:
                        run_command("python ../lifter.py -domain %s -prob %s %s STATS" % (dom, prob, solver_opts),
                                    output_file='OUT.lifter', MEMLIMIT=MEM_LIMIT, TIMELIMIT=600)
                        #os.system("timeout 600 python ../lifter.py -domain %s -prob %s %s STATS > OUT.lifter" % (dom, prob, solver_opts))
                    else:
                        run_command("python ../lifter.py -domain %s -prob %s %s STATS COUNT" % (dom, prob, solver_opts),
                                    output_file='OUT.lifter', MEMLIMIT=MEM_LIMIT, TIMELIMIT=600)
                        #os.system("timeout 600 python ../lifter.py -domain %s -prob %s %s STATS COUNT > OUT.lifter" % (dom, prob, solver_opts))

                    lifter_time = time.time() - prev_time
                    prev_time = time.time()


                    # Run the encoder
                    run_command("python ../encoder.py -domain %s -prob %s %s -output foo %s %s %s" % (dom, prob, solver_opts, serial, allact, deorder),
                                output_file='OUT.maxsat', MEMLIMIT=MEM_LIMIT, TIMELIMIT=600)
                    #os.system("timeout 600 python ../encoder.py -domain %s -prob %s %s -output foo %s %s %s > OUT.maxsat" % (dom, prob, solver_opts, serial, allact, deorder))
                    encoder_time = time.time() - prev_time
                    prev_time = time.time()


                    # Run the maxsat
                    # First line is for sat4j output / second is for MaxHS
                    os.system("java -Xmx4096m -jar ../sat4j-maxsat.jar -i -t 1800 foo.wcnf > OUT.minimax 2>&1")
                    #os.system("timeout 1800 ~/MaxHS/bin/maxhs foo.wcnf > OUT.minimax")
                    maxsat_time = time.time() - prev_time
                    prev_time = time.time()


                    # Run the POP analysis
                    if disable_linears:
                        run_command("python ../analyzer.py -map foo.map -popstats OUT.minimax NOCOUNT",
                                    output_file='OUT.popstats', MEMLIMIT=MEM_LIMIT, TIMELIMIT=600)
                        #os.system("timeout 600 python ../analyzer.py -map foo.map -popstats OUT.minimax NOCOUNT > OUT.popstats")
                    else:
                        run_command("python ../analyzer.py -map foo.map -popstats OUT.minimax",
                                    output_file='OUT.popstats', MEMLIMIT=MEM_LIMIT, TIMELIMIT=600)
                        #os.system("timeout 600 python ../analyzer.py -map foo.map -popstats OUT.minimax > OUT.popstats")

                    popstat_time = time.time() - prev_time

                    # Lift all the data #
                    lifted_actions = get_value('OUT.lifter', "POP with ([0-9]+) actions", int)
                    lifted_orderings = get_value('OUT.lifter', "actions and ([0-9]+) causal links", int)
                    if not disable_linears:
                        lifted_linears = get_value('OUT.lifter', "Linearizations: ([0-9]+)", int)

                    msat_vars = get_value('OUT.maxsat', "Vars: ([0-9]+)", int)
                    msat_clauses = get_value('OUT.maxsat', "Clauses: ([0-9]+)", int)
                    msat_soft = get_value('OUT.maxsat', "Soft: ([0-9]+)", int)
                    msat_hard = get_value('OUT.maxsat', "Hard: ([0-9]+)", int)
                    msat_wt = get_value('OUT.maxsat', "Max Weight: ([0-9]+)", int)

                    encoded_actions = get_value('OUT.popstats', "POP with ([0-9]+) actions", int)
                    encoded_orderings = get_value('OUT.popstats', "actions and ([0-9]+) causal links", int)
                    if not disable_linears:
                        encoded_linears = get_value('OUT.popstats', "Linearizations: ([0-9]+)", int)
                    encoded_optimal = match_value('OUT.popstats', 'Optimal: True')


                    # Write the data #
                    if disable_linears:
                        csv_data = "%s,%s,%s,%s,%s,%f,%f,%f,%f,%d,%d,%d,%d,%s,%d,%d,%d\n" % (domain, prob_name,
                                    str(serial == 'SERIAL'), str(allact == 'ALLACT'), str(deorder == 'DEORDER'),
                                    lifter_time, encoder_time, maxsat_time, popstat_time,
                                    lifted_actions, encoded_actions, lifted_orderings, encoded_orderings, encoded_optimal,
                                    msat_vars, msat_clauses, msat_wt)
                    else:
                        csv_data = "%s,%s,%s,%s,%s,%f,%f,%f,%f,%d,%d,%d,%d,%s,%d,%d,%d,%d,%d,%d\n" % (domain, prob_name,
                                    str(serial == 'SERIAL'), str(allact == 'ALLACT'), str(deorder == 'DEORDER'),
                                    lifter_time, encoder_time, maxsat_time, popstat_time,
                                    lifted_actions, encoded_actions, lifted_orderings, encoded_orderings, encoded_optimal,
                                    lifted_linears, encoded_linears, (encoded_linears - lifted_linears),
                                    msat_vars, msat_clauses, msat_wt)

                    append_file("%s.csv" % domain, csv_data)

                    # Clean up the mess #
                    os.system("mv OUT.* %s" % dir_name)
                    os.system("mv foo.* %s" % dir_name)
                    #os.system("rm none")

    os.system("rm -rf %s" % domain)
    #os.system("rm ubcsat")

    if disable_linears:
        res_dir = "uncounted-"
    else:
        res_dir = "counted-"

    if POPF == solver:
        res_dir += "encoded-popf-%s" % domain
    elif FF == solver:
        res_dir += "encoded-ff-%s" % domain
    elif MERCURY == solver:
        res_dir += "encoded-merc-%s" % domain
    elif MP == solver:
        res_dir += "encoded-mp-%s" % domain
    else:
        res_dir += "encoded-unknown-%s" % domain
        print("Warning: Unknown solver, %s" % str(solver))

    os.system("mkdir %s" % res_dir)
    os.system("mv encoded.* %s" % res_dir)
    os.system("mv %s.csv %s" % (domain, res_dir))
    os.system("mv %s ../" % res_dir)
    os.chdir("../")
    os.system("rmdir %s" % ID)



def do_mip(domain):

    if domain in FORBIDDEN_DOMAINS:
        print("Skipping forbidden domain %s" % domain)
        return

    ID = "mip_%s" % (domain)

    dom_probs = filter_solved_domains(domain, DOMAINS[domain], MERCURY)

    os.system("mkdir %s" % ID)
    os.chdir("./%s" % ID)
    os.system("cp -rf ../RESULTS/plans/%s ." % domain)

    csv_data = "Domain,Prob,Time-Encode,Time-Solve,Encoded Constraints\n"

    write_file("%s.csv" % domain, csv_data)

    for dom,prob in dom_probs:

        print("\nDomain: %s" % dom)
        print("Problem: %s" % prob)

        prob_name = prob.split('/')[-1].split('.pddl')[0]

        dir_name = "%s.%s" % (domain, prob_name)
        os.system("mkdir %s" % dir_name)

        # Run the encoder
        run_command("python ../mip.py -version 1 -domain %s -prob %s -mercout %s/%s.merc > OUT.mip" % (dom, prob, domain, prob_name),
                                            output_file='OUT.mip', MEMLIMIT=MEM_LIMIT, TIMELIMIT=1800)

        mip_encode_time = get_value('OUT.mip', "Encoding Time: ([0-9]+\.?[0-9]+)", float)
        mip_solve_time = get_value('OUT.mip', "Solving Time: ([0-9]+\.?[0-9]+)", float)
        mip_quality = get_value('OUT.mip', "Obj: ([0-9]+)\.", int)

        # Write the data #
        csv_data = "%s,%s,%f,%f,%d\n" % (domain, prob_name, mip_encode_time, mip_solve_time, mip_quality)
        append_file("%s.csv" % domain, csv_data)

        # Clean up the mess #
        os.system("mv OUT.* %s" % dir_name)

    os.system("rm -rf %s" % domain)
    os.chdir("../")


def get_coverage(domain):

    dom_probs = filter_solved_domains(domain, DOMAINS[domain])
    mapping = {}

    for (dom, prob) in dom_probs:
        prob_name = prob.split('/')[-1].split('.')[0]
        os.system("python executer.py analytic -domain %s -prob %s -ffout %s/%s/FF.out -policy %s/%s/policy.txt > tmp" % (dom, prob, domain, prob_name, domain, prob_name))
        policy_coverage = get_value('tmp', "POP Policy:\t ([0-9]+)", int)
        fritz_coverage = get_value('tmp', "Fritz Policy:\t ([0-9]+)", int)
        ratio = get_value('tmp', "Ratio: ([0-9]+\.?[0-9]+)", float)

        mapping[prob_name] = ratio

    os.system('rm tmp')

    return mapping


if __name__ == '__main__':
    myargs, flags = get_opts()

    if '-domain' not in myargs:
        print("Error: Must choose a domain:")
        print(USAGE_STRING)
        os._exit(1)

    solver = ALL

    if '-solver' in myargs:
        if myargs['-solver'] == 'ff':
            solver = FF
        elif myargs['-solver'] == 'popf':
            solver = POPF
        elif myargs['-solver'] == 'mercury':
            solver = MERCURY
        elif myargs['-solver'] == 'mp':
            solver = MP

    if 'solved-stats' in flags:

        if myargs['-domain'] == 'ALL':
            doms = GOOD_DOMAINS
        else:
            doms = [myargs['-domain']]

        print("Domain,Problems,Merc,MP,POPF")

        for dom in doms:
            solved_stats(dom)

    if 'allplanners' in flags:
        if myargs['-domain'] == 'ALL':
            doms = GOOD_DOMAINS
        else:
            doms = [myargs['-domain']]

        for dom in doms:
            print("\n\n -{ %s }-\n" % dom)
            print("Running MP")
            do_mp(dom)

            print("Running POPF")
            do_popf(dom)

            print("Running Mercury")
            do_mercury(dom)

            os.system("mv %s PLANS" % dom)

    if 'ff' in flags:
        do_ff(myargs['-domain'])

    if 'mp' in flags:
        do_mp(myargs['-domain'])

    if 'popf' in flags:
        do_popf(myargs['-domain'])

    if 'mercury' in flags:
        do_mercury(myargs['-domain'])

    if 'merc-flex' in flags:
        print("\nComputing the Mercury Relaxer Flex...")
        write_file('merc-flex.csv', 'Domain,DFile,PFile,Acts,Orders,Flex')
        if 'all' == myargs['-domain'].lower():
            for d in GOOD_DOMAINS:
                merc_flex(d)
        else:
            merc_flex(myargs['-domain'])

    if 'popf-flex' in flags:
        print("\nComputing the POPF Flex...")
        write_file('popf-flex.csv', 'Domain,DFile,PFile,Acts,Orders,Flex')
        if 'all' == myargs['-domain'].lower():
            for d in GOOD_DOMAINS:
                popf_flex(d)
        else:
            popf_flex(myargs['-domain'])

    if 'mp-flex' in flags:
        print("\nComputing the MP Flex...")
        write_file('mp-flex.csv', 'Domain,DFile,PFile,Acts,Orders,Flex')
        if 'all' == myargs['-domain'].lower():
            for d in GOOD_DOMAINS:
                mp_flex(d)
        else:
            mp_flex(myargs['-domain'])

    if 'mip' in flags:
        if 'all' == myargs['-domain'].lower():
            for d in GOOD_DOMAINS:
                do_mip(d)
        else:
            do_mip(myargs['-domain'])

    if 'encode' in flags:
        if 'all' == myargs['-domain'].lower():
            for d in GOOD_DOMAINS:
                do_encode(d, solver)
        else:
            do_encode(myargs['-domain'], solver)

    if 'encode-nocount' in flags:
        if 'all' == myargs['-domain'].lower():
            for d in GOOD_DOMAINS:
                do_encode(d, solver, True)
        else:
            do_encode(myargs['-domain'], solver, True)

