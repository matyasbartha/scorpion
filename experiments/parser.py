#! /usr/bin/env python

import logging
import re
import sys

from lab.parser import Parser

class CustomParser(Parser):
    def __init__(self):
        Parser.__init__(self)

def add_additive_cartesian_heuristic_build_time_if_cs(content, props):
    if props["cegar_found_concrete_solution"] == 1:
        props["additive_cartesian_heuristic_build_time_if_cs"] = props["additive_cartesian_heuristic_build_time"]
    else:
        props["additive_cartesian_heuristic_build_time_if_cs"] = None

def add_cartesian_states_if_cs(content, props):
    if props["cegar_found_concrete_solution"] == 1:
        props["cartesian_states_if_cs"] = props["cartesian_states"]
    else:
        props["cartesian_states_if_cs"] = None

def no_search(content, props):
    if "search_start_time" not in props:
        error = props.get("error")
        if error is not None and error != "incomplete-search-found-no-plan":
            props["error"] = "no-search-due-to-" + error

def find_cegar_termination_criterion(content, props):
    outcomes = {
        "cegar_found_concrete_solution": "Found concrete solution.",
        "cegar_proved_unsolvability": "Abstract task is unsolvable.",
        "cegar_reached_states_limit": "Reached maximum number of states.",
        "cegar_reached_transitions_limit": "Reached maximum number of transitions.",
        "cegar_reached_time_limit": "Reached time limit.",
        "cegar_reached_time_limit_in_flaw_search": "Reached time limit in flaw search.",
        "cegar_reached_memory_limit": "Reached memory limit.",
        "cegar_reached_memory_limit_in_flaw_search": "Reached memory limit in flaw search.",
    }

    for outcome, text in outcomes.items():
        props[outcome] = int(text in content)
        if props[outcome]:
            if "cegar_outcome" in props:
                props["cegar_outcome"] = "mixed"
            else:
                props["cegar_outcome"] = outcome

def find_cegar_max_expansion_message(content, props):
        props["max_expansion_with_flaw"] = content.count("Max expansions reached with flaws!")
        props["max_expansion_without_flaw"] = content.count("Max expansions reached with no flaw!")

def main():
    parser = CustomParser()
    parser.add_pattern("num_flaw_searches", r"\] #Flaw searches: (.+)\n", type=float)
    #parser.add_pattern("num_flaw_refinments", r"\] #Flaws refined: (.+)\n", type=int)
    parser.add_pattern("num_state_expansions_in_flaw_search", r"\] #Expanded concrete states: (.+)\n", type=int)
    parser.add_pattern("max_num_state_expansions_in_flaw_search", r"\] #Max expanded concrete states in one flaw search: (.+)\n", type=int)
    parser.add_pattern("cartesian_states", r"\] Cartesian states: (.+)\n", type=int)
    parser.add_pattern("flaw_search_time", r"\] Flaw search time: (.+)s\n", type=float
    parser.add_pattern("split_computing_time", r"\] Time for computing splits: (.+)s\n", type=float)
    parser.add_pattern("pick_computing_time", r"\] Time for selecting splits: (.+)s\n", type=float)
    parser.add_pattern("additive_cartesian_heuristic_build_time", r"\] Time for initializing additive Cartesian heuristic: (.+)s\n", type=float)

    parser.add_pattern("search_start_time", r"\[t=(.+)s, \d+ KB\] g=0, 1 evaluated, 0 expanded", type=float)
    parser.add_pattern("search_start_memory", r"\[t=.+s, (\d+) KB\] g=0, 1 evaluated, 0 expanded", type=int)
    
    parser.add_function(find_cegar_termination_criterion)
    parser.add_function(add_cartesian_states_if_cs)
    parser.add_function(add_additive_cartesian_heuristic_build_time_if_cs)
    parser.add_function(no_search)
    parser.add_function(find_cegar_max_expansion_message)
    
    parser.parse()


if __name__ == "__main__":
    main()
