#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import common_setup
from common_setup import CartesianExperiment

import os
from pathlib import Path

from lab.reports import Attribute

from scatterMulti import ScatterMultiPlotReport 

from downward.reports.absolute import AbsoluteReport

from lab.environments import LocalEnvironment, BaselSlurmEnvironment

from parser import get_parser

"""
Experiment script for cartesian experiments
"""

MEMORY_LIMIT = 6144
MEMORY_PADDING = 6354 - MEMORY_LIMIT # infai_2 has 6354 MB per cpu
TIME_LIMIT = 5 * 60

DIR = os.path.dirname(os.path.abspath(__file__))
BENCHMARKS_DIR = os.environ["DOWNWARD_BENCHMARKS"]
PLANNER_DIR = os.environ["SCORPION_MATYAS"]
DRIVER_OPTIONS = ["--overall-time-limit", f"{TIME_LIMIT}s", "--overall-memory-limit", f"{MEMORY_LIMIT}M"]

if common_setup.is_running_on_cluster():
    #SUITE = common_setup.DEFAULT_OPTIMAL_SUITE
    SUITE = common_setup.DEFAULT_TEST_SUITE
    ENVIRONMENT = BaselSlurmEnvironment(
        partition="infai_2",
        email="m.bartha@stud.unibas.ch",
        memory_per_cpu="3947M",
        export=["PATH"],
    )
else:
    #SUITE = common_setup.CartesianExperiment.DEFAULT_TEST_SUITE
    SUITE = common_setup.CartesianExperiment.DEFAULT_TEST_SUITE
    ENVIRONMENT = LocalEnvironment(processes=4)
    DRIVER_OPTIONS = ["--overall-time-limit", "30s"]


CONFIGS = []
CONFIGS += [
    common_setup.Config(
        f"original-cegar",
        "original-scorpion",
        ["--search", "astar(cegar(subtasks=[original()],pick_flawed_abstract_state=first_on_shortest_path))"],
        driver_options=DRIVER_OPTIONS,
    ),
    common_setup.Config(
        f"random-optimal-path",
        "random-path",
        ["--search", "astar(cegar(subtasks=[original()],pick_flawed_abstract_state=first_on_shortest_path))"],
        driver_options=DRIVER_OPTIONS,
    ),
    common_setup.Config(
        f"master-cegar",
        "scorpion",
        ["--search", "astar(cegar(subtasks=[original()],pick_flawed_abstract_state=first_on_shortest_path))"],
        driver_options=DRIVER_OPTIONS,
    ),
]


exp = common_setup.CartesianExperiment(
    repo_base=PLANNER_DIR,
    configs=CONFIGS,
    environment=ENVIRONMENT,
)

def domain_as_category(run1, run2):
    return run1["domain"]


def algorithm_as_category(run1, run2):
    return run2["algorithm"]

exp.add_suite(BENCHMARKS_DIR, SUITE)

exp.add_parser(exp.EXITCODE_PARSER)
exp.add_parser(exp.TRANSLATOR_PARSER)
exp.add_parser(exp.SINGLE_SEARCH_PARSER)
exp.add_parser(exp.PLANNER_PARSER)
exp.add_parser(get_parser())


ATTRIBUTES = CartesianExperiment.DEFAULT_TABLE_ATTRIBUTES


exp.add_step("build", exp.build)
exp.add_step("start", exp.start_runs)
exp.add_step("parse", exp.parse)
exp.add_fetcher(name="fetch")
"""
exp.add_report(
    AbsoluteReport(attributes=ATTRIBUTES, filter_algorithm=[x.nick for x in CONFIGS]),
    outfile="report6.html",
)
"""
# Add report step (AbsoluteReport is the standard report).
CARTESIAN_ATTRIBUTES = ["total_time","cartesian_states", "run_dir", "flaw_search_time", "additive_cartesian_heuristic_build_time", "search_start_time", "search_start_memory", "cartesian_states_if_cs", "additive_cartesian_heuristic_build_time_if_cs", Attribute("cegar_found_concrete_solution", min_wins=False), Attribute("cegar_proved_unsolvability", min_wins=False), "cegar_reached_time_limit", "cegar_reached_memory_limit", "cegar_outcome", "expansions_until_last_jump", "cost", Attribute("coverage", min_wins=False),"error","expansions", "search_time", "split_computing_time", Attribute("initial_h_value", min_wins=False), "memory", "cegar_reached_time_limit_in_flaw_search", "cegar_reached_memory_limit_in_flaw_search", "num_state_expansions_in_flaw_search", "max_num_state_expansions_in_flaw_search", "pick_computing_time", "max_expansion_with_flaw", "max_expansion_without_flaw"]

exp.add_report(AbsoluteReport(attributes=CARTESIAN_ATTRIBUTES), outfile='final_report.html')

"""
#
plot_configs = ["final_min_h_batch_multi_split_max_cover", "final_single_path_max_refined", "final_max_h_single_max_refined", "final_min_h_single_max_refined", "final_min_h_single_max_cover"]
#
for att in ["cartesian_states_if_cs", "additive_cartesian_heuristic_build_time_if_cs", "expansions_until_last_jump", "initial_h_value"]:
    exp.add_report(ScatterMultiPlotReport(relative=False,attributes=att,get_category=algorithm_as_category,filter_algorithm=plot_configs,format="tex",show_missing=True),name=att)

"""



exp.run_steps()