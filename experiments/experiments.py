#! /usr/bin/env python3

import os
import os.path
import platform

from lab.environments import SlurmEnvironment
from lab.reports import Attribute

from downward.experiment import FastDownwardExperiment
from downward.reports.absolute import AbsoluteReport
from downward.reports.scatter import ScatterPlotReport
from downward.reports.compare import ComparativeReport

from scatterMulti import ScatterMultiPlotReport 

class FreiburgSlurmEnvironment(SlurmEnvironment):
    """Environment for Freiburg's AI group."""

    def __init__(self, **kwargs):
        SlurmEnvironment.__init__(self, **kwargs)
        #SlurmEnvironment.__init__(self, extra_options='#SBATCH --exclude=kisexe[06]', **kwargs)

    DEFAULT_PARTITION =  "gki_cpu-cascadelake"
    #DEFAULT_PARTITION =  "gki_gpu-ti"
    DEFAULT_QOS = "normal"
    DEFAULT_MEMORY_PER_CPU = "4096M"

def domain_as_category(run1, run2):
    return run1["domain"]

def algorithm_as_category(run1, run2):
    return run2["algorithm"]


# Experiment Setup
SUITE = ['agricola-opt18-strips', 'airport', 'barman-opt11-strips',
    'barman-opt14-strips', 'blocks', 'childsnack-opt14-strips',
    'data-network-opt18-strips', 'depot', 'driverlog',
    'elevators-opt08-strips', 'elevators-opt11-strips',
    'floortile-opt11-strips', 'floortile-opt14-strips', 'freecell',
    'ged-opt14-strips', 'grid', 'gripper', 'hiking-opt14-strips',
    'logistics00', 'logistics98', 'miconic', 'movie', 'mprime',
    'mystery', 'nomystery-opt11-strips', 'openstacks-opt08-strips',
    'openstacks-opt11-strips', 'openstacks-opt14-strips',
    'openstacks-strips', 'organic-synthesis-opt18-strips',
    'organic-synthesis-split-opt18-strips', 'parcprinter-08-strips',
    'parcprinter-opt11-strips', 'parking-opt11-strips',
    'parking-opt14-strips', 'pathways-noneg', 'pegsol-08-strips',
    'pegsol-opt11-strips', 'petri-net-alignment-opt18-strips',
    'pipesworld-notankage', 'pipesworld-tankage', 'psr-small', 'rovers',
    'satellite', 'scanalyzer-08-strips', 'scanalyzer-opt11-strips',
    'snake-opt18-strips', 'sokoban-opt08-strips',
    'sokoban-opt11-strips', 'spider-opt18-strips', 'storage',
    'termes-opt18-strips', 'tetris-opt14-strips',
    'tidybot-opt11-strips', 'tidybot-opt14-strips', 'tpp',
    'transport-opt08-strips', 'transport-opt11-strips',
    'transport-opt14-strips', 'trucks-strips', 'visitall-opt11-strips',
    'visitall-opt14-strips', 'woodworking-opt08-strips',
    'woodworking-opt11-strips', 'zenotravel']

OVERALL_TIME_LIMIT = "30m"
OVERALL_MEMORY_LIMIT = "4000M"


# Use path to your Fast Downward repository.
REPO = "/home/speckd/git/scorpion/"
BENCHMARKS_DIR = "/home/speckd/benchmarks/downward-benchmarks/"
REVISION_CACHE = os.path.expanduser('~/lab/revision-cache')

ENV = FreiburgSlurmEnvironment()
exp = FastDownwardExperiment(environment=ENV, revision_cache=REVISION_CACHE)

# Add built-in parsers to the experiment.
exp.add_parser(exp.EXITCODE_PARSER)
exp.add_parser(exp.SINGLE_SEARCH_PARSER)
exp.add_parser(exp.PLANNER_PARSER)
exp.add_parser("parser.py")

exp.add_suite(BENCHMARKS_DIR, SUITE)

rev = "final_"

pick_split = 'max_cover'
tiebreak_split = "max_refined"
max_expansions = "1000000"
for pick_flaw in ["min_h_batch_multi_split", "min_h_single"]:
    exp.add_algorithm(rev + pick_flaw + '_' + pick_split, REPO, "flaw_search", ['--search', 'astar(cegar(subtasks=[original()], max_states=infinity, max_transitions=infinity, max_time=900, pick_split=' + pick_split + ', tiebreak_split=' + tiebreak_split +  ', pick_flaw=' + pick_flaw + ',max_state_expansions=' + max_expansions + ', use_general_costs=true, debug=false, transform=no_transform(), cache_estimates=true, random_seed=-1))'], driver_options=["--overall-time-limit", OVERALL_TIME_LIMIT, "--overall-memory-limit", OVERALL_MEMORY_LIMIT])

pick_split = 'max_refined'
tiebreak_split = 'min_cg'
max_expansions = "1000000"
for pick_flaw in ["min_h_single", "max_h_single"]:
    exp.add_algorithm(rev + pick_flaw + '_' + pick_split, REPO, "flaw_search", ['--search', 'astar(cegar(subtasks=[original()], max_states=infinity, max_transitions=infinity, max_time=900, pick_split=' + pick_split + ', tiebreak_split=' + tiebreak_split +  ', pick_flaw=' + pick_flaw + ',max_state_expansions=' + max_expansions + ', use_general_costs=true, debug=false, transform=no_transform(), cache_estimates=true, random_seed=-1))'], driver_options=["--overall-time-limit", OVERALL_TIME_LIMIT, "--overall-memory-limit", OVERALL_MEMORY_LIMIT])


pick_flaw = "single_path"
pick_split = "max_refined"
exp.add_algorithm(rev + pick_flaw + '_' + pick_split, REPO, "flaw_search", ['--search', 'astar(cegar(subtasks=[original()], max_states=infinity, max_transitions=infinity, max_time=900, pick_split=' + pick_split + ', pick_flaw=' + pick_flaw + ', use_general_costs=true, debug=false, transform=no_transform(), cache_estimates=true, random_seed=-1))'], driver_options=["--overall-time-limit", OVERALL_TIME_LIMIT, "--overall-memory-limit", OVERALL_MEMORY_LIMIT])


# Add step that writes experiment files to disk.
exp.add_step('build', exp.build)

# Add step that executes all runs.
exp.add_step('start', exp.start_runs)

#exp.add_parse_again_step()

# Add step that collects properties from run directories and
# writes them to *-eval/properties.
exp.add_fetcher(name='fetch')

# Add report step (AbsoluteReport is the standard report).
ATTRIBUTES = ["total_time","cartesian_states", "run_dir", "flaw_search_time", "additive_cartesian_heuristic_build_time", "search_start_time", "search_start_memory", "cartesian_states_if_cs", "additive_cartesian_heuristic_build_time_if_cs", Attribute("cegar_found_concrete_solution", min_wins=False), Attribute("cegar_proved_unsolvability", min_wins=False), "cegar_reached_time_limit", "cegar_reached_memory_limit", "cegar_outcome", "expansions_until_last_jump", "cost", Attribute("coverage", min_wins=False),"error","expansions", "search_time", "split_computing_time", Attribute("initial_h_value", min_wins=False), "memory", "cegar_reached_time_limit_in_flaw_search", "cegar_reached_memory_limit_in_flaw_search", "num_state_expansions_in_flaw_search", "max_num_state_expansions_in_flaw_search", "pick_computing_time", "max_expansion_with_flaw", "max_expansion_without_flaw"]

exp.add_report(AbsoluteReport(attributes=ATTRIBUTES,filter_algorithm=["final_single_path_max_refined", "final_max_h_single_max_refined", "final_min_h_single_max_refined", "final_min_h_single_max_cover", "final_min_h_batch_multi_split_max_cover"]), outfile='final_report.html')
#
plot_configs = ["final_min_h_batch_multi_split_max_cover", "final_single_path_max_refined", "final_max_h_single_max_refined", "final_min_h_single_max_refined", "final_min_h_single_max_cover"]
#
for att in ["cartesian_states_if_cs", "additive_cartesian_heuristic_build_time_if_cs", "expansions_until_last_jump", "initial_h_value"]:
    exp.add_report(ScatterMultiPlotReport(relative=False,attributes=att,get_category=algorithm_as_category,filter_algorithm=plot_configs,format="tex",show_missing=True),name=att)

# Parse the commandline and show or run experiment steps.
exp.run_steps()
