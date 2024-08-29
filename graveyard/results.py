from krrt.utils import get_opts, write_file, load_CSV, get_lines
from krrt.stats.plots import plot_loglog, plot, create_time_profile
from numpy import std, mean, median, product, roots

from popgen.linearizer import count_linearizations
from popgen.pop import POP
from domains import GOOD_DOMAINS

import networkx as nx
from functools import reduce

USAGE_STRING = """
Usage: python results.py -<option> <argument> -<option> <argument> ... <FLAG> <FLAG> ...

        Where options are:
          -summary <domain or 'all'>
          -lcpstats <domain or 'all'>
          -plottiming <domain or 'all'>
          -plotlcplinears <domain or 'all'>
          -plotminrelinears <domain or 'all'>
          -plotlinears <domain or 'all'>
          -timing <domain or 'all'>
          -meanactconst <domain or 'all'>
          -compareplanners <domain or 'all'>
          -maxsat <domain or 'all'>
          -mipsat4j <domain or 'all'>

        And the flags include:
        """


GOOD = 0
TIMEOUT_LIFTER = 1
TIMEOUT_ENCODER = 2
TIMEOUT_MAXSAT = 3
TIMEOUT_POPANALYSIS = 4
MEMOUT_LIFTER = 5
MEMOUT_MAXSAT = 6

SETTINGS = [(False, False, False),
            (False, False, True),
            (False, True, False),
            (False, True, True),
            (True, False, False),
            (True, False, True),
            (True, True, False),
            (True, True, True)]

LCP = (False, False, False)
MIN_DEORDERING = (False, True, True)
MIN_REORDERING = (False, True, False)

def get_execution_status(line):
    if '0' != line[12]:
        return GOOD
    elif float(line[5]) > 600:
        return TIMEOUT_LIFTER
    elif float(line[6]) > 600:
        return TIMEOUT_ENCODER
    elif float(line[7]) > 1800:
        return TIMEOUT_MAXSAT
    elif float(line[8]) > 600:
        return TIMEOUT_POPANALYSIS
    elif float(line[7]) > 10:
        return MEMOUT_MAXSAT
    else:
        return MEMOUT_LIFTER

def get_mip_data(domain):
    return load_CSV("RESULTS/mip/mip_%s/%s.csv" % (domain, domain))[1:]

def get_all_mip_data():
    return reduce(lambda x,y: x+y, [get_mip_data(dom) for dom in GOOD_DOMAINS])

def get_data(domain, counted):
    if counted:
        #return (load_CSV("RESULTS/full/counted-encoded-ff-%s/%s.csv" % (domain, domain))[1:], load_CSV("RESULTS/full/counted-encoded-popf-%s/%s.csv" % (domain, domain))[1:])
        #return (load_CSV("RESULTS/full/counted-encoded-ff-%s/%s.csv" % (domain, domain))[1:], [])
        #return (load_CSV("RESULTS/maxhs/%s.csv" % (domain))[1:], [])
        return (load_CSV("RESULTS/sat4j/%s.csv" % (domain))[1:], [])
    else:
        #return (load_CSV("RESULTS/full/uncounted-encoded-ff-%s/%s.csv" % (domain, domain))[1:], load_CSV("RESULTS/full/uncounted-encoded-popf-%s/%s.csv" % (domain, domain))[1:])
        #return (load_CSV("RESULTS/full/uncounted-encoded-ff-%s/%s.csv" % (domain, domain))[1:], [])
        #return (load_CSV("RESULTS/maxhs/%s.csv" % (domain))[1:], [])
        return (load_CSV("RESULTS/sat4j/%s.csv" % (domain))[1:], [])

def filter_settings(data, setting):
    return [x for x in data if x[2] == str(setting[0]) and \
                            x[3] == str(setting[1]) and \
                            x[4] == str(setting[2])]

def print_setting(s):

    to_return = ''

    if s[0]:
        to_return += "Serial / "
    else:
        to_return += "Non-serial / "

    if s[1]:
        to_return += "All actions / "
    else:
        to_return += "Not all actions / "

    if s[2]:
        to_return += "Deordering"
    else:
        to_return += "Reordering"

    return to_return

def print_summary(counted_data, uncounted_data):

    good_counted_data = [x for x in counted_data if GOOD == get_execution_status(x)]
    good_uncounted_data = [x for x in uncounted_data if GOOD == get_execution_status(x)]

    # Totals
    print("")
    print("Total trials (LCP): %d (%d)" % (len(uncounted_data), len(filter_settings(uncounted_data, LCP))))
    print("Total success (LCP): %d (%d)" % (len(good_uncounted_data), len(filter_settings(good_uncounted_data, LCP))))
    print("Total linears success (LCP): %d (%d)" % (len(good_counted_data), len(filter_settings(good_counted_data, LCP))))

    # How many times each setting mem'd out
    print("\n  -{ Number of Encoding Mem-outs }-")
    for s in SETTINGS:
        print("%s: %d" % (print_setting(s), len([x for x in filter_settings(uncounted_data, s) if MEMOUT_LIFTER == get_execution_status(x)])))

    # How many times each setting mem'd out
    print("\n  -{ Number of MAXSAT Mem-outs }-")
    for s in SETTINGS:
        print("%s: %d" % (print_setting(s), len([x for x in filter_settings(uncounted_data, s) if MEMOUT_MAXSAT == get_execution_status(x)])))

    # How many times each timed out on encoding
    print("\n  -{ Number of MAXSAT timeouts }-")
    for s in SETTINGS:
        print("%s: %d" % (print_setting(s), len([x for x in filter_settings(uncounted_data, s) if TIMEOUT_MAXSAT == get_execution_status(x)])))

    # Non-setting specific info
    print("")

    print("Number of times Lifted == Minimum Deordering: >= %d" % len([x for x in filter_settings(good_counted_data, MIN_DEORDERING) if int(x[9]) == int(x[10]) and \
                                                                                    int(x[11]) == int(x[12]) and \
                                                                                    int(x[13]) == int(x[14])]))

    print("Number of times Lifted == Minimum Reordering: >= %d" % len([x for x in filter_settings(good_counted_data, MIN_REORDERING) if int(x[9]) == int(x[10]) and \
                                                                                    int(x[11]) == int(x[12]) and \
                                                                                    int(x[13]) == int(x[14])]))

    print("Number of times Lifted == LCP: >= %d" % len([x for x in filter_settings(good_counted_data, LCP) if int(x[9]) == int(x[10]) and \
                                                                     int(x[11]) == int(x[12]) and \
                                                                     int(x[13]) == int(x[14])]))

    print("\nNumber of times Actions & Constraints matched, but linears didn't: >= %d" % len([x for x in good_counted_data if x[9] == x[10] and \
                                                                                                         x[11] == x[12] and \
                                                                                                         x[13] != x[14]]))

    print("\nNumber of times Minimum Deordering > Lifted (constraints): %d / %d" % (len([x for x in filter_settings(good_uncounted_data, MIN_DEORDERING) if int(x[11]) > int(x[12])]), len(filter_settings(good_uncounted_data, MIN_DEORDERING))))
    print("Number of times Minimum Reordering > Lifted (constraints): %d / %d" % (len([x for x in filter_settings(good_uncounted_data, MIN_REORDERING) if int(x[11]) > int(x[12])]), len(filter_settings(good_uncounted_data, MIN_REORDERING))))
    print("Number of times LCP > Lifted (actions): %d / %d" % (len([x for x in filter_settings(good_uncounted_data, LCP) if int(x[9]) > int(x[10])]), len(filter_settings(good_uncounted_data, LCP))))
    print("Number of times LCP > Lifted (constraints or actions): %d / %d" % (len([x for x in filter_settings(good_uncounted_data, LCP) if int(x[11]) > int(x[12]) or int(x[9]) > int(x[10])]), len(filter_settings(good_uncounted_data, LCP))))
    print("")

def lcp_stats(counted_data, uncounted_data):

    good_counted_data = [x for x in counted_data if GOOD == get_execution_status(x)]
    good_uncounted_data = [x for x in uncounted_data if GOOD == get_execution_status(x)]

    print("")
    print("Number of times LCP reduced the # of actions: %d" % len([x for x in filter_settings(good_uncounted_data, LCP) if int(x[10]) < int(x[9])]))
    print("Number of times LCP reduced the orderings, but not actions: %d" % len([x for x in filter_settings(good_uncounted_data, LCP) if x[10] == x[9] and int(x[12]) < int(x[11])]))
    print("Number of times LCP improved the # of linearizations: >= %d" % len([x for x in filter_settings(good_counted_data, LCP) if int(x[15]) > 0]))
    print("")

def plot_relinears(counted_data, setting, disable_ones = True):

    good_data = [x for x in filter_settings(counted_data, setting) if GOOD == get_execution_status(x)]

    xs = [float(line[13]) for line in good_data]
    ys = [float(line[14]) for line in good_data]

    if disable_ones:
        new_y = [x for x in sorted([ys[i] / xs[i] for i in range(len(xs))]) if x != 1.0]
    else:
        new_y = sorted([ys[i] / xs[i] for i in range(len(xs))])

    if LCP == setting:
        new_y = [x for x in new_y if x >= 1]

    new_x = [i+1 for i in range(len(new_y))]

    print("\nComputing linearization comparison for setting: %s" % print_setting(setting))
    print("Data points: %d" % len(xs))
    print("Same linearizations: %d" % (len(xs) - len(new_x)))
    print("Different linearizations: %d" % len(new_x))
    print("Mean / std linearization ratio: %f +- %f" % (mean(sorted([ys[i] / xs[i] for i in range(len(xs))])),
                                                        std(sorted([ys[i] / xs[i] for i in range(len(xs))]))))
    print("Min / Max: %f / %f" % (sorted([ys[i] / xs[i] for i in range(len(xs))])[0], sorted([ys[i] / xs[i] for i in range(len(xs))])[-1]))
    print("")

    if LCP == setting:
        ylabel = 'Ratio of Linearizations'
    else:
        ylabel = 'MR / RX'

    plot([new_x, [0,max(new_x) + 1]], [new_y, [1, 1]], x_label = 'Problem Instance', y_label = ylabel, col = False, x_log = False, y_log = True, xyline = False, no_scatter = True)


def plot_linears(counted_data):

    from operator import itemgetter

    good_data = [x for x in counted_data if GOOD == get_execution_status(x)]

    # Only keep the data that has a solution for all parts
    solved_by_lcp = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, LCP)])
    solved_by_md = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, MIN_DEORDERING)])
    solved_by_mr = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, MIN_REORDERING)])

    solved_by_all = solved_by_lcp & solved_by_md & solved_by_mr

    good_data = [x for x in good_data if "%s/%s" % (x[0], x[1]) in solved_by_all]

    lcp_mapping = {}
    md_mapping = {}
    mr_mapping = {}
    prob_time_list = []

    for prob in solved_by_all:
        lcp_mapping[prob] = float([x for x in filter_settings(good_data, LCP) if "%s/%s" % (x[0], x[1]) == prob][0][14])
        md_mapping[prob] = float([x for x in filter_settings(good_data, MIN_DEORDERING) if "%s/%s" % (x[0], x[1]) == prob][0][14])
        mr_mapping[prob] = float([x for x in filter_settings(good_data, MIN_REORDERING) if "%s/%s" % (x[0], x[1]) == prob][0][14])
        #prob_time_list.append((prob, lcp_mapping[prob]))
        prob_time_list.append((prob, md_mapping[prob]))

    sorted_problem_list = [pair[0] for pair in sorted(prob_time_list, key=itemgetter(1))]

    MD_lins = [md_mapping[prob] for prob in sorted_problem_list]
    MR_lins = [mr_mapping[prob] for prob in sorted_problem_list]
    LCP_lins = [lcp_mapping[prob] for prob in sorted_problem_list]

    x = list(range(len(sorted_problem_list)))

    #plot([x], [LCP_lins], x_label = "Problem Instance", y_label = "Linearizations", col = True, x_log = False, y_log = True, names = None, graph_name = None, legend_name = None, xyline = False, disable_x_tics = True, no_scatter = True, nosymbols = False)
    plot([x,x,x], [MD_lins, MR_lins, LCP_lins], x_label = "Problem Instance", y_label = "Linearizations", col = True, x_log = False, y_log = True, names = ['MD', 'MR', 'LCP'], graph_name = None, legend_name = None, xyline = False, disable_x_tics = True, no_scatter = False, nosymbols = False)


def plot_timing(uncounted_data):

    from operator import itemgetter

    good_data = [x for x in uncounted_data if GOOD == get_execution_status(x)]

    # Only keep the data that has a solution for all parts
    solved_by_lcp = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, LCP)])
    solved_by_md = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, MIN_DEORDERING)])
    solved_by_mr = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, MIN_REORDERING)])

    solved_by_all = solved_by_lcp & solved_by_md & solved_by_mr

    good_data = [x for x in good_data if "%s/%s" % (x[0], x[1]) in solved_by_all]

    lcp_mapping = {}
    md_mapping = {}
    mr_mapping = {}
    rx_mapping = {}
    prob_time_list = []

    for prob in solved_by_all:
        lcp_mapping[prob] = float([x for x in filter_settings(good_data, LCP) if "%s/%s" % (x[0], x[1]) == prob][0][7])
        md_mapping[prob] = float([x for x in filter_settings(good_data, MIN_DEORDERING) if "%s/%s" % (x[0], x[1]) == prob][0][7])
        mr_mapping[prob] = float([x for x in filter_settings(good_data, MIN_REORDERING) if "%s/%s" % (x[0], x[1]) == prob][0][7])
        rx_mapping[prob] = float([x for x in filter_settings(good_data, LCP) if "%s/%s" % (x[0], x[1]) == prob][0][5])
        prob_time_list.append((prob, rx_mapping[prob]))


    sorted_problem_list = [pair[0] for pair in sorted(prob_time_list, key=itemgetter(1))]
    #sorted_problem_list = sorted(list(solved_by_all))

    RX_times = [rx_mapping[prob] for prob in sorted_problem_list]
    MD_times = [md_mapping[prob] for prob in sorted_problem_list]
    MR_times = [mr_mapping[prob] for prob in sorted_problem_list]
    LCP_times = [lcp_mapping[prob] for prob in sorted_problem_list]

    x = list(range(len(sorted_problem_list)))

    plot([x,x], [RX_times, MD_times], x_label = "Problem Instance", y_label = "Time to Solve", col = True, x_log = False, y_log = True, names = ['RX', 'MD'], graph_name = None, legend_name = None, xyline = False, disable_x_tics = True, no_scatter = False, nosymbols = False)
    #plot([x,x,x,x], [RX_times, MD_times, MR_times, LCP_times], x_label = "Problem Instance", y_label = "Time to Solve", col = True, x_log = False, y_log = True, names = ['RX', 'MD', 'MR', 'LCP'], graph_name = None, legend_name = None, xyline = False, disable_x_tics = True, no_scatter = False, nosymbols = False)

def compute_timing(uncounted_data):

    good_data = [x for x in uncounted_data if GOOD == get_execution_status(x)]

    print("")
    print("  -{ Mean / std for (encoding time) and (maxsat time) }-")

    for s in SETTINGS:
        print("%s: (%f +- %f) / (%f +- %f)" % (print_setting(s), mean([float(item[6]) for item in filter_settings(good_data, s)]),
                                                                median([float(item[6]) for item in filter_settings(good_data, s)]),
                                                                mean([float(item[7]) for item in filter_settings(good_data, s)]),
                                                                median([float(item[7]) for item in filter_settings(good_data, s)])))
    print("")
    print("Min maxsat time: %f" % min([float(item[7]) for item in good_data]))
    print("Max maxsat time: %f" % max([float(item[7]) for item in good_data]))
    print("")

def maxsat_stats(uncounted_data):

    good_data = [x for x in uncounted_data if (TIMEOUT_MAXSAT == get_execution_status(x)) or (GOOD == get_execution_status(x))]

    # Only keep the data that has a solution for all parts
    solved_by_lcp = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, LCP)])
    solved_by_md = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, MIN_DEORDERING)])
    solved_by_mr = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, MIN_REORDERING)])

    solved_by_all = solved_by_lcp & solved_by_md & solved_by_mr

    good_data = [x for x in good_data if "%s/%s" % (x[0], x[1]) in solved_by_all]

    relaxing_times = [float(item[5]) for item in filter_settings(good_data, LCP)]

    maxsat_times_md = [float(item[7]) for item in filter_settings(good_data, MIN_DEORDERING)]
    maxsat_times_mr = [float(item[7]) for item in filter_settings(good_data, MIN_REORDERING)]
    maxsat_times_lcp = [float(item[7]) for item in filter_settings(good_data, LCP)]

    maxsat_vars = [float(item[13]) for item in filter_settings(good_data, LCP)]
    maxsat_clauses_md = [float(item[14]) for item in filter_settings(good_data, MIN_DEORDERING)]
    maxsat_clauses_mr = [float(item[14]) for item in filter_settings(good_data, MIN_REORDERING)]
    maxsat_clauses_lcp = [float(item[14]) for item in filter_settings(good_data, LCP)]

    print("")
    print("%.2f & %.2f & %.2f & %.2f & %.2f & %.2f & %.2f & %.2f & %.2f & %.2f & %.2f & %.2f" % ( \
                            mean(relaxing_times), mean(maxsat_times_md), mean(maxsat_times_mr), mean(maxsat_times_lcp),
                            median(relaxing_times), median(maxsat_times_md), median(maxsat_times_mr), median(maxsat_times_lcp),
                            mean(maxsat_vars), mean(maxsat_clauses_md), mean(maxsat_clauses_mr), mean(maxsat_clauses_lcp)))
    print("")
    print("STD of vars: %.2f" % std(maxsat_vars))
    print("Under 5 seconds: %d / %d" % (len([x for x in good_data if float(x[7]) < 5.0]), len(good_data)))
    print("Max Relaxer Time: %.2f" % max(relaxing_times))
    print("")

def compute_timing_relative(uncounted_data):

    good_data = [x for x in uncounted_data if GOOD == get_execution_status(x)]

    # Only keep the data that has a solution for all parts
    solved_by_lcp = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, LCP)])
    solved_by_md = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, MIN_DEORDERING)])
    solved_by_mr = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, MIN_REORDERING)])

    solved_by_all = solved_by_lcp & solved_by_md & solved_by_mr

    good_data = [x for x in good_data if "%s/%s" % (x[0], x[1]) in solved_by_all]

    lcp_mapping = {}
    md_mapping = {}
    mr_mapping = {}

    for prob in solved_by_all:
        lcp_mapping[prob] = [x for x in filter_settings(good_data, LCP) if "%s/%s" % (x[0], x[1]) == prob][0]
        md_mapping[prob] = [x for x in filter_settings(good_data, MIN_DEORDERING) if "%s/%s" % (x[0], x[1]) == prob][0]
        mr_mapping[prob] = [x for x in filter_settings(good_data, MIN_REORDERING) if "%s/%s" % (x[0], x[1]) == prob][0]

    lcp_maxsat_increase = [float(lcp_mapping[prob][7]) / float(lcp_mapping[prob][7]) for prob in solved_by_all]
    md_maxsat_increase = [float(md_mapping[prob][7]) / float(lcp_mapping[prob][7]) for prob in solved_by_all]
    mr_maxsat_increase = [float(mr_mapping[prob][7]) / float(lcp_mapping[prob][7]) for prob in solved_by_all]

    print("\nData Size: %d\n" % len(solved_by_all))
    print("  -{ Mean / std for (maxsat time) }-")

    print("lcp: (%f +- %f)" % (mean(lcp_maxsat_increase), std(lcp_maxsat_increase)))
    print("md: (%f +- %f)" % (mean(md_maxsat_increase), std(md_maxsat_increase)))
    print("mr: (%f +- %f)" % (mean(mr_maxsat_increase), std(mr_maxsat_increase)))

    print("")
    print("Min maxsat time: %f" % min([float(item[7]) for item in good_data]))
    print("Max maxsat time: %f" % max([float(item[7]) for item in good_data]))
    print("")

def compute_mean_act_const(uncounted_data):
    return compute_mean_act_const_increase(uncounted_data)

    good_data = [x for x in uncounted_data if GOOD == get_execution_status(x)]

    # Only keep the data that has a solution for all parts
    solved_by_lcp = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, LCP)])
    solved_by_md = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, MIN_DEORDERING)])
    solved_by_mr = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, MIN_REORDERING)])

    solved_by_all = solved_by_lcp & solved_by_md & solved_by_mr

    good_data = [x for x in good_data if "%s/%s" % (x[0], x[1]) in solved_by_all]

    print("\n%f & %f & %f & %f & %f & %f" % (mean([float(item[9]) for item in filter_settings(good_data, LCP)]),
                                           mean([float(item[10]) for item in filter_settings(good_data, LCP)]),
                                           mean([float(item[11]) for item in filter_settings(good_data, LCP)]),
                                           mean([float(item[12]) for item in filter_settings(good_data, MIN_DEORDERING)]),
                                           mean([float(item[12]) for item in filter_settings(good_data, MIN_REORDERING)]),
                                           mean([float(item[12]) for item in filter_settings(good_data, LCP)])))

    print("\nData Size: %d / %d\n" % (len(solved_by_all), len(solved_by_lcp | solved_by_md | solved_by_mr)))

    print("  -{ Mean / std actions and constraints }-")

    print("relaxer: (%f +- %f) / (%f +- %f)" % (mean([float(item[9]) for item in filter_settings(good_data, LCP)]),
                                               std([float(item[9]) for item in filter_settings(good_data, LCP)]),
                                               mean([float(item[11]) for item in filter_settings(good_data, LCP)]),
                                               std([float(item[11]) for item in filter_settings(good_data, LCP)])))

    for s in [MIN_DEORDERING, MIN_REORDERING, LCP]:
        print("%s: (%f +- %f) / (%f +- %f)" % (print_setting(s), mean([float(item[10]) for item in filter_settings(good_data, s)]),
                                                                std([float(item[10]) for item in filter_settings(good_data, s)]),
                                                                mean([float(item[12]) for item in filter_settings(good_data, s)]),
                                                                std([float(item[12]) for item in filter_settings(good_data, s)])))
    print("")

def compute_mean_act_const_increase(uncounted_data):

    good_data = [x for x in uncounted_data if GOOD == get_execution_status(x)]

    # Only keep the data that has a solution for all parts
    #solved_by_lcp = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, LCP)])
    #solved_by_md = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, MIN_DEORDERING)])
    #solved_by_mr = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, MIN_REORDERING)])

    #solved_by_all = solved_by_lcp & solved_by_md & solved_by_mr

    #good_data = filter(lambda x: "%s/%s" % (x[0], x[1]) in solved_by_all, good_data)

    #lcp_mapping = {}
    #md_mapping = {}
    #mr_mapping = {}

    #for prob in solved_by_all:
    #    lcp_mapping[prob] = filter(lambda x: "%s/%s" % (x[0], x[1]) == prob, filter_settings(good_data, LCP))[0]
    #    md_mapping[prob] = filter(lambda x: "%s/%s" % (x[0], x[1]) == prob, filter_settings(good_data, MIN_DEORDERING))[0]
    #    mr_mapping[prob] = filter(lambda x: "%s/%s" % (x[0], x[1]) == prob, filter_settings(good_data, MIN_REORDERING))[0]

    #lcp_action_increase = [float(lcp_mapping[prob][9]) / float(lcp_mapping[prob][10]) for prob in solved_by_all]
    #lcp_ordering_increase = [float(lcp_mapping[prob][11]) / float(lcp_mapping[prob][12]) for prob in solved_by_all]
    #md_ordering_increase = [float(md_mapping[prob][11]) / float(md_mapping[prob][12]) for prob in solved_by_all]
    #mr_ordering_increase = [float(mr_mapping[prob][11]) / float(mr_mapping[prob][12]) for prob in solved_by_all]


    # Alternative -- compute the statistics on a per solver basis
    all_problems = set(["%s/%s" % (item[0], item[1]) for item in good_data])
    solved_by_lcp = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, LCP)])
    solved_by_md = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, MIN_DEORDERING)])
    solved_by_mr = set(["%s/%s" % (item[0], item[1]) for item in filter_settings(good_data, MIN_REORDERING)])

    solved_by_some = solved_by_lcp | solved_by_md | solved_by_mr
    solved_by_all = solved_by_lcp & solved_by_md & solved_by_mr

    lcp_mapping = {}
    md_mapping = {}
    mr_mapping = {}
    rx_mapping = {}

    for prob in solved_by_lcp:
        lcp_mapping[prob] = [x for x in filter_settings(good_data, LCP) if "%s/%s" % (x[0], x[1]) == prob][0]

    for prob in solved_by_md:
        md_mapping[prob] = [x for x in filter_settings(good_data, MIN_DEORDERING) if "%s/%s" % (x[0], x[1]) == prob][0]

    for prob in solved_by_mr:
        mr_mapping[prob] = [x for x in filter_settings(good_data, MIN_REORDERING) if "%s/%s" % (x[0], x[1]) == prob][0]

    for prob in solved_by_md:
        rx_mapping[prob] = [x for x in filter_settings(good_data, MIN_DEORDERING) if "%s/%s" % (x[0], x[1]) == prob][0]

    solved_action_increase = [prob for prob in solved_by_lcp if float(lcp_mapping[prob][9]) > float(lcp_mapping[prob][10])]
    lcp_action_decrease = [1 - (float(lcp_mapping[prob][10]) / float(lcp_mapping[prob][9])) for prob in solved_action_increase]
    lcp_action_decrease_all = [1 - (float(lcp_mapping[prob][10]) / float(lcp_mapping[prob][9])) for prob in solved_by_lcp]

    def flex(num_acts, num_orders):
        def nCr(n,r):
            import math
            f = math.factorial
            return f(n) / f(r) / f(n-r)
        return 1.0 - (float(num_orders) / float(nCr(int(num_acts), 2)))

    lcp_flex = [flex(float(lcp_mapping[prob][10]), float(lcp_mapping[prob][12])) for prob in solved_by_lcp]
    md_flex = [flex(float(md_mapping[prob][10]), float(md_mapping[prob][12])) for prob in solved_by_md]
    mr_flex = [flex(float(mr_mapping[prob][10]), float(mr_mapping[prob][12])) for prob in solved_by_mr]
    rx_flex = [flex(float(rx_mapping[prob][9]), float(rx_mapping[prob][11])) for prob in solved_by_md]
    #lcp_flex = [flex(float(lcp_mapping[prob][10]), float(lcp_mapping[prob][12])) for prob in solved_by_all]
    #md_flex = [flex(float(md_mapping[prob][10]), float(md_mapping[prob][12])) for prob in solved_by_all]
    #mr_flex = [flex(float(mr_mapping[prob][10]), float(mr_mapping[prob][12])) for prob in solved_by_all]
    #rx_flex = [flex(float(rx_mapping[prob][9]), float(rx_mapping[prob][11])) for prob in solved_by_all]

    lcp_opt = [{'True':1,'False':0}[lcp_mapping[prob][13]] for prob in solved_by_lcp]
    md_opt = [{'True':1,'False':0}[md_mapping[prob][13]] for prob in solved_by_md]
    mr_opt = [{'True':1,'False':0}[mr_mapping[prob][13]] for prob in solved_by_mr]

    print("\nAll problems:\t %d" % len(all_problems))
    print("Solved by all:\t %d" % len(solved_by_all))

    print("  -{ Action Improvement (only improvements) }-")
    print("Occurrences:\t %d / %d = %f" % (len(solved_action_increase),
                                           len(solved_by_lcp),
                                           float(len(solved_action_increase)) / float(len(solved_by_lcp))))
    print("Arith. mean:\t %f +/- %f" % (mean(lcp_action_decrease), std(lcp_action_decrease)))
    print("Geometric mean:\t %f" % product(lcp_action_decrease)**(1.0 / len(lcp_action_decrease)))

    print("\n  -{ Action Improvement (all) }-")
    print("Occurrences:\t %d" % len(solved_by_lcp))
    print("Arith. mean:\t %f +/- %f" % (mean(lcp_action_decrease_all), std(lcp_action_decrease_all)))
    print("Geometric mean:\t %f" % product(lcp_action_decrease_all)**(1.0 / len(lcp_action_decrease_all)))

    print("\n  -{ Average Flex (Arithmetic) }-")
    print("LCP (%d): %f +/- %f" % (len(lcp_flex), mean(lcp_flex), std(lcp_flex)))
    print("MR (%d):  %f +/- %f" % (len(mr_flex), mean(mr_flex), std(mr_flex)))
    print("MD (%d):  %f +/- %f" % (len(md_flex), mean(md_flex), std(md_flex)))
    print("RX (%d):  %f +/- %f" % (len(rx_flex), mean(rx_flex), std(rx_flex)))

    print("\n  -{ Average Flex (Geometric) }-")
    print("LCP (%d): %f" % (len(lcp_flex), product(lcp_flex)**(1.0 / len(lcp_flex))))
    print("MR (%d):  %f" % (len(mr_flex), product(mr_flex)**(1.0 / len(mr_flex))))
    print("MD (%d):  %f" % (len(md_flex), product(md_flex)**(1.0 / len(md_flex))))
    print("RX (%d):  %f" % (len(rx_flex), product(rx_flex)**(1.0 / len(rx_flex))))

    print("\n  -{ Instances Proved Optimal }-")
    print("LCP: %d / %d = %f" % (sum(lcp_opt), len(lcp_flex), float(sum(lcp_opt)) / float(len(lcp_flex))))
    print("MR: %d / %d = %f" % (sum(mr_opt), len(mr_flex), float(sum(mr_opt)) / float(len(mr_flex))))
    print("MD: %d / %d = %f" % (sum(md_opt), len(md_flex), float(sum(md_opt)) / float(len(md_flex))))

    #print "  -{ Mean increase actions and constraints }-"

    #print "lcp: (%f +- %f) / (%f +- %f)" % (mean(lcp_action_increase),
    #                                       std(lcp_action_increase),
    #                                       mean(lcp_ordering_increase),
    #                                       std(lcp_ordering_increase))

    #print "md: (%f +- %f)" % (mean(md_ordering_increase),
    #                         std(md_ordering_increase))

    #print "mr: (%f +- %f)" % (mean(mr_ordering_increase),
    #                         std(mr_ordering_increase))

    print()


def compare_planners(counted_data, uncounted_data):

    uncounted_ff = filter_settings(uncounted_data[0], LCP)
    uncounted_popf = filter_settings(uncounted_data[1], LCP)

    _solved_ff = set(["%s-%s" % (item[0], item[1]) for item in [x for x in uncounted_ff if GOOD == get_execution_status(x)]])
    _solved_popf = set(["%s-%s" % (item[0], item[1]) for item in [x for x in uncounted_popf if GOOD == get_execution_status(x)]])

    mutual_solved = _solved_ff & _solved_popf
    solved_ff = [x for x in uncounted_ff if ("%s-%s" % (x[0], x[1])) in mutual_solved]
    solved_popf = [x for x in uncounted_popf if ("%s-%s" % (x[0], x[1])) in mutual_solved]

    ff_results = {}
    popf_results = {}
    for line in solved_ff:
        ff_results["%s-%s" % (line[0], line[1])] = line
    for line in solved_popf:
        popf_results["%s-%s" % (line[0], line[1])] = line

    action_total = 0.0
    ordering_total = 0.0

    action_total_ff = 0.0
    action_total_popf = 0.0
    ordering_total_ff = 0.0
    ordering_total_popf = 0.0

    print("")

    popf_bet = 0
    ff_bet = 0

    for prob in mutual_solved:
        if float(popf_results[prob][12]) > float(ff_results[prob][12]):
            ff_bet += 1
        if float(popf_results[prob][12]) < float(ff_results[prob][12]):
            popf_bet += 1

        action_total += float(ff_results[prob][10]) / float(popf_results[prob][10])
        ordering_total += float(ff_results[prob][12]) / float(popf_results[prob][12])

        action_total_ff += float(ff_results[prob][10]) / float(ff_results[prob][9])
        action_total_popf += float(popf_results[prob][10]) / float(popf_results[prob][9])

        ordering_total_ff += float(ff_results[prob][12]) / float(ff_results[prob][11])
        ordering_total_popf += float(popf_results[prob][12]) / float(popf_results[prob][11])

    print("\nMean Relative Action: %f" % (action_total / float(len(mutual_solved))))
    print("Mean Relative Ordering: %f" % (ordering_total / float(len(mutual_solved))))
    print("POPF better / worse: %d / %d" % (popf_bet, ff_bet))
    print("Mean Relative FF Action: %f" % (action_total_ff / float(len(mutual_solved))))
    print("Mean Relative POPF Action: %f" % (action_total_popf / float(len(mutual_solved))))
    print("Mean Relative FF Ordering: %f" % (ordering_total_ff / float(len(mutual_solved))))
    print("Mean Relative POPF Ordering: %f" % (ordering_total_popf / float(len(mutual_solved))))

    print("")
    print("FF Solved: %d / %d" % (len(_solved_ff), len(set(["%s-%s" % (item[0], item[1]) for item in uncounted_ff]))))
    print("POPF Solved: %d / %d" % (len(_solved_popf), len(set(["%s-%s" % (item[0], item[1]) for item in uncounted_popf]))))
    print("Mutually Solved: %d" % len(mutual_solved))
    print("")


def do_plotalltimes():
    all_data = fetch_all_data()[1][0]
    good_data = [x for x in all_data if GOOD == get_execution_status(x)]
    kk_data = [x for x in [float(item[5]) for item in filter_settings(all_data, LCP)] if x <= 600]
    md_data = [x for x in [float(item[7]) + float(item[6]) for item in filter_settings(good_data, MIN_DEORDERING)] if x <= 1801]
    mr_data = [x for x in [float(item[7]) + float(item[6]) for item in filter_settings(good_data, MIN_REORDERING)] if x <= 1801]
    lcp_data = [x for x in [float(item[7]) + float(item[6]) for item in filter_settings(good_data, LCP)] if x <= 1801]

    print("Under 10: %d / %d" % (len([x for x in md_data + mr_data + lcp_data if x < 10]), len(md_data + mr_data + lcp_data)))

    x1,y1 = create_time_profile(kk_data)
    x2,y2 = create_time_profile(md_data)
    x3,y3 = create_time_profile(mr_data)
    x4,y4 = create_time_profile(lcp_data)

    plot([x1,x2,x4,x3], [y1,y2,y4,y3], x_label = "Time (s)", y_label = "Problems Solved", no_scatter = True,
         xyline = False, names = ['RX', 'MD', 'MCLCP', 'MR'], x_log = True, col = False)


def mip_vs_sat4j(sat4j_data, mip_data):

    good_data = [x for x in sat4j_data if GOOD == get_execution_status(x)]
    mr_data = [float(item[7]) + float(item[6]) for item in filter_settings(good_data, MIN_REORDERING)]
    mip_data = [float(item[2]) + float(item[3]) for item in [x for x in mip_data if float(x[3]) > 0]]

    x1,y1 = create_time_profile(mr_data)
    x2,y2 = create_time_profile(mip_data)

    #print len(x1)
    #print len(x2)
    print("x1 = %s" % str(x1))
    print("y1 = %s" % str(y1))
    print("x2 = %s" % str(x2))
    print("y2 = %s" % str(y2))
    print('plot([x1,x2], [y1,y2], x_label = "Time (s)", y_label = "Problems Solved", no_scatter = True, xyline = False, names = ["MR", "MIP"], x_log = True, col = False)')
    for i in range(len(x1)):
        print("MR,%f,%f" % (x1[i], y1[i]))
    for i in range(len(x2)):
        print("MIP,%f,%f" % (x2[i], y2[i]))

    plot([x1,x2], [y1,y2], x_label = "Time (s)", y_label = "Problems Solved", no_scatter = True,
         xyline = False, names = ['MR', 'MILP'], x_log = True, col = False)

def fetch_all_data():
    all_counted_data = ([], [])
    all_uncounted_data = ([], [])
    for dom in GOOD_DOMAINS:
        new_data = get_data(dom, True)
        all_counted_data[0].extend(new_data[0])
        all_counted_data[1].extend(new_data[1])

        new_data = get_data(dom, False)
        all_uncounted_data[0].extend(new_data[0])
        all_uncounted_data[1].extend(new_data[1])

    return all_counted_data, all_uncounted_data

if __name__ == '__main__':
    import os
    myargs, flags = get_opts()

    if '-summary' in myargs:
        if 'all' == myargs['-summary']:

            all_counted_data, all_uncounted_data = fetch_all_data()

            print("\n    { FF }")
            print_summary(all_counted_data[0], all_uncounted_data[0])
            #print "\n\n    { POPF }"
            #print_summary(all_counted_data[1], all_uncounted_data[1])

        else:
            print("\n    { FF }")
            print_summary(get_data(myargs['-summary'], True)[0], get_data(myargs['-summary'], False)[0])
            #print "\n\n    { POPF }"
            #print_summary(get_data(myargs['-summary'], True)[1], get_data(myargs['-summary'], False)[1])

    elif '-lcpstats' in myargs:
        if 'all' == myargs['-lcpstats']:

            all_counted_data, all_uncounted_data = fetch_all_data()

            print("\n    { FF }")
            lcp_stats(all_counted_data[0], all_uncounted_data[0])
            print("\n\n    { POPF }")
            lcp_stats(all_counted_data[1], all_uncounted_data[1])

        else:

            print("\n    { FF }")
            lcp_stats(get_data(myargs['-lcpstats'], True)[0], get_data(myargs['-lcpstats'], False)[0])
            print("\n\n    { POPF }")
            lcp_stats(get_data(myargs['-lcpstats'], True)[1], get_data(myargs['-lcpstats'], False)[1])

    elif '-plotlcplinears' in myargs:
        if 'all' == myargs['-plotlcplinears']:
            all_counted_data, all_uncounted_data = fetch_all_data()
            plot_relinears(all_counted_data[0], LCP, disable_ones = False)
        else:
            plot_relinears(get_data(myargs['-plotlcplinears'], True)[0], LCP, disable_ones = False)

    elif '-plotlinears' in myargs:
        if 'all' == myargs['-plotlinears']:
            all_counted_data, all_uncounted_data = fetch_all_data()
            plot_linears(all_counted_data[0])
        else:
            plot_linears(get_data(myargs['-plotlinears'], True)[0])

    elif '-plottiming' in myargs:
        if 'all' == myargs['-plottiming']:
            all_counted_data, all_uncounted_data = fetch_all_data()
            plot_timing(all_uncounted_data[0])
        else:
            plot_timing(get_data(myargs['-plottiming'], False)[0])

    elif '-plotminrelinears' in myargs:
        if 'all' == myargs['-plotminrelinears']:
            all_counted_data, all_uncounted_data = fetch_all_data()
            plot_relinears(all_counted_data[0], MIN_REORDERING)
        else:
            plot_relinears(get_data(myargs['-plotminrelinears'], True)[0], MIN_REORDERING)

    elif '-timing' in myargs:
        if 'all' == myargs['-timing']:
            all_counted_data, all_uncounted_data = fetch_all_data()
            compute_timing(all_uncounted_data[0])
        else:
            compute_timing(get_data(myargs['-timing'], False)[0])

    elif '-meanactconst' in myargs:
        if 'all' == myargs['-meanactconst']:
            all_counted_data, all_uncounted_data = fetch_all_data()
            compute_mean_act_const(all_uncounted_data[0])
        else:
            compute_mean_act_const(get_data(myargs['-meanactconst'], False)[0])

    elif '-compareplanners' in myargs:
        if 'all' == myargs['-compareplanners']:
            all_counted_data, all_uncounted_data = fetch_all_data()
            compare_planners(all_counted_data, all_uncounted_data)
        else:
            compare_planners(get_data(myargs['-compareplanners'], True), get_data(myargs['-compareplanners'], False))

    elif '-maxsat' in myargs:
        if 'all' == myargs['-maxsat']:
            all_counted_data, all_uncounted_data = fetch_all_data()
            maxsat_stats(all_uncounted_data[0])
        else:
            maxsat_stats(get_data(myargs['-maxsat'], False)[0])

    elif '-mipvssat4j' in myargs:
        if 'all' == myargs['-mipvssat4j']:
            _, all_uncounted_data = fetch_all_data()
            mip_vs_sat4j(all_uncounted_data[0], get_all_mip_data())
        else:
            mip_vs_sat4j(get_data(myargs['-mipvssat4j'], False)[0], get_mip_data(myargs['-mipvssat4j']))

    elif 'plotalltimes' in flags:
        do_plotalltimes()

    else:
        print(USAGE_STRING)

