#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import common_setup
from common_setup import CartesianExperiment
import top_k_parser

import os
from pathlib import Path

from downward.reports.absolute import AbsoluteReport

from lab.environments import LocalEnvironment, BaselSlurmEnvironment

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
        f"master-cartesian",
        "cartesian",
        ["--search", "astar(cegar(subtasks=[original()],pick_flawed_abstract_state=first_on_shortest_path))"],
        driver_options=DRIVER_OPTIONS,
    ),
]


exp = common_setup.CartesianExperiment(
    repo_base=PLANNER_DIR,
    configs=CONFIGS,
    environment=ENVIRONMENT,
)

exp.add_suite(BENCHMARKS_DIR, SUITE)

exp.add_parser(exp.EXITCODE_PARSER)
exp.add_parser(exp.TRANSLATOR_PARSER)
exp.add_parser(exp.SINGLE_SEARCH_PARSER)
exp.add_parser(exp.PLANNER_PARSER)
exp.add_parser(top_k_parser.get_parser())

ATTRIBUTES = CartesianExperiment.DEFAULT_TABLE_ATTRIBUTES
"""
SYM_ATTRIBUTES = ["domain_sizes",
                  "max_domain_size",
                  "min_domain_size",
                  "median_domain_size",
                  "num_vars",
                  "num_bin_vars",
                  "num_bdd_nodes",
                  "num_peak_bdd_nodes"]
"""

exp.add_step("build", exp.build)
exp.add_step("start", exp.start_runs)
exp.add_step("parse", exp.parse)
exp.add_fetcher(name="fetch")
exp.add_report(
    AbsoluteReport(attributes=ATTRIBUTES """ + SYM_ATTRIBUTES""", filter_algorithm=[x.nick for x in CONFIGS]),
    outfile="report6.html",
)



exp.run_steps()