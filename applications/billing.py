"""

Redistribute total hours to bill for n total employees from all teams in a project so that individual
employee time entries (forcefully manual) are minimized.

Inputs:
  - Employee monthly billable hours to report (excluding holidays, etc.) for every
    client. Extracted from external time tracking systems, it would be nonsensical to input as is in
    the official time reporting software.

    >For proper
    >optimization, knowing each non-billable hours count and day of the month for every
    >employee would be necessary. In this example all non-billable employee hours are ignored.
  - A month can be composed of either 4 or 5 weeks. Selectable on demand.

Constraints:
  - 8 hours/day for reporting application
  - 40 hour/week maximum span of reported project hours.


The objective is to minimize total created spans by all employees.

Extras:
    - Minimize set of projects a employee allocates to in a month, meaning less cognitive overhead.

Example:

    4 week month, 3 employees with 160,160,150 respective billable hours to distribute between
    projects:

    - 1: 140h
    - 2: 20h
    - 3: 310h

    should output something like:

    |        | Week 1 | Week 2 | Week 3 |   Week 4    | Spans |
    | ------ | ------ | ------ | ------ | ----------- | ----- |
    | user 1 | 40#3   | 40#3   | 40#3   | 40#3        | 4     |
    | user 3 | 40#3   | 40#3   | 40#3   | 30#3        | 4     |
    | user 2 | 40#1   | 40#1   | 40#1   | 20#1 + 20#2 | 5     |
    * {hours}#{project}

"""


import copy
import dataclasses
import itertools
import pprint
import time
from typing import Any, Dict, List, Union, cast
import typing
from ortools.sat.python import cp_model
from xlsxwriter import Workbook

from collections.abc import Iterable
import pandas as pd

# import polars as pl


def flatten(xs):
    for x in xs:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x


def flatten_dict(a):
    lst = []
    for i in a.values():
        if isinstance(i, dict):
            lst.extend(flatten_dict(i))
        elif isinstance(i, list):
            lst.extend(i)
        else:
            lst.append(i)
    return lst


class Employee(str):
    def __init__(self, string) -> None:
        super().__init__()


class Project(str):
    def __init__(self, string) -> None:
        super().__init__()


Vars = Dict[Employee, Dict[Project, List[cp_model.IntVar]]]
Spans = Dict[Employee, Dict[Project, List[cp_model.IntVar]]]
EmployeeProjectCounts = Dict[Employee, List[cp_model.IntVar]]
Results = Dict[Employee, Dict[Project, int]]
ProjectHours = Dict[Project, int]
EmployeeHours = Dict[Employee, int]
EmployeeProjects = Dict[Employee, List[Project]]

EXCEL_SOLUTION_FILE = "billing.xlsx"


@dataclasses.dataclass
class EmployeeReporting:
    df: pd.DataFrame
    spans: int
    employee_project_count: int
    unallocated_hours: Dict[Employee, int]


# TODO precomputation to show meaningful error and exit early when restricting users to projects makes it infeasible
# TODO more deterministic allocations, maybe with arbitrary weights for sorted employees
def minimize_employee_reporting(
    n_weeks=4,
    project_hours: ProjectHours = {},
    employee_hours: EmployeeHours = {},
    employee_projects: EmployeeProjects = {},
    max_weekly_hours=40,
    save_excel=False,
) -> EmployeeReporting:
    def get_total_employee_project_count():
        return sum(solver.Value(i) for i in flatten(employee_project_counts.values()))

    projects = list(project_hours.keys())
    employees = list(employee_hours.keys())
    total_employee_hours = sum(employee_hours.values())
    total_project_hours = sum(project_hours.values())
    print(f"Total employee hours: {total_employee_hours}")
    print(f"Total billable project hours: {total_project_hours}")

    if total_employee_hours < total_project_hours:
        raise Exception("Cannot have project billing hours higher than total employee billable hours")
    elif total_employee_hours > total_project_hours:
        print("####")
        print(
            "#### Total unallocated employee billable hours:",
            total_employee_hours - total_project_hours,
        )
        print("####")

    # Initialize the CP-SAT model
    model = cp_model.CpModel()

    class HourReportingPrinter(cp_model.CpSolverSolutionCallback):
        """Print intermediate solutions."""

        def __init__(self, dummy=None):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self.__solution_count = 0
            self.__start_time = time.time()
            self.__dummy = dummy

        def on_solution_callback(self):
            current_time = time.time()
            objective = self.ObjectiveValue()
            print(
                "Solution %i, time = %f s, objective = %i"
                % (self.__solution_count, current_time - self.__start_time, objective)
            )
            self.__solution_count += 1

        # show useful info...

        def num_solutions(self):
            return self.__solution_count

    vars: Vars = {}
    # bool vars that indicate if an employee has allocated time to a project a given week
    spans: Spans = {}
    # bool vars that indicate if an employee has allocated time to a project any week
    employee_project_counts: EmployeeProjectCounts = {}

    for e in employees:
        vars[e] = {}
        spans[e] = {}
        employee_project_counts[e] = []

        allowed_projects = projects
        if employee_projects.get(e) is not None:
            allowed_projects = employee_projects[e]

        # initialize decision variables
        for p in projects:
            project_max_weekly_hours = max_weekly_hours
            if p not in allowed_projects:
                project_max_weekly_hours = 0

            vars[e][p] = []
            for w in range(n_weeks):
                vars[e][p].append(model.NewIntVar(0, project_max_weekly_hours, f"var_e_{e}_p_{p}_w_{w+1}"))

            spans[e][p] = []
            for w in range(n_weeks):
                # do not use multiplication, extremely slow (https://stackoverflow.com/questions/71961919/ortools-cp-sat-solver-constraint-to-require-two-lists-of-variables-to-be-drawn)
                employee_span = model.NewBoolVar(f"span_e_{e}_p_{p}_w_{w+1}")
                model.Add(vars[e][p][w] > 0).OnlyEnforceIf(employee_span)
                model.Add(vars[e][p][w] == 0).OnlyEnforceIf(employee_span.Not())
                spans[e][p].append(employee_span)

            employee_project_count = model.NewBoolVar(f"employee_project_count_e_{e}_p_{p}")
            model.Add(sum(vars[e][p]) > 0).OnlyEnforceIf(employee_project_count)
            model.Add(sum(vars[e][p]) == 0).OnlyEnforceIf(employee_project_count.Not())
            employee_project_counts[e].append(employee_project_count)

        for w in range(n_weeks):
            model.Add(sum(vars[e][p][w] for p in projects) <= max_weekly_hours)

        # an employee cannot allocate more hours than allowed
        model.Add(sum(sum(vars[e][p]) for p in projects) <= employee_hours[e])

    for p in projects:
        # all project billing hours must be allocated in the end
        model.Add(sum(sum(vars[e][p]) for e in employees) == project_hours[p])

    flattened_spans = flatten(flatten(j) for i in spans.values() for j in i.values())
    model.Minimize(sum(flattened_spans))

    solver = cp_model.CpSolver()
    status = solver.Solve(model, HourReportingPrinter())

    if status == cp_model.INFEASIBLE:
        raise Exception("INFEASIBLE")
    if status == cp_model.MODEL_INVALID:
        raise Exception("MODEL_INVALID")

    print(f"Project billing hours: {project_hours}")
    print(f"Employee hours: {employee_hours}")
    print("-------------------------------------------")

    total_spans = round(solver.ObjectiveValue())
    total_employee_project_count = get_total_employee_project_count()
    print(f"Spans (1st run): {total_spans}")
    print(f"Distinct projects/hour count (1st run): {total_employee_project_count}")

    model.AddHint(sum(flattened_spans), total_spans)  # faster solving with hint
    model.Add(sum(flattened_spans) <= total_spans)  # restrict to previous solution
    model.Minimize(sum(flatten(employee_project_counts.values())))
    solver = cp_model.CpSolver()
    status = solver.Solve(model, HourReportingPrinter())

    if status == cp_model.OPTIMAL:
        for e in employees:
            print(f"Employee {e}:")
            month_accum = 0
            for w in range(n_weeks):
                for p in projects:
                    hours = solver.Value(vars[e][p][w])
                    month_accum += hours
                    print(f"\tWeek {w+1}: {hours:<3}h on project {p:<20} Span bool={solver.Value(spans[e][p][w])}")
            print("")
            print(f"\tAllocated hours: {month_accum}")
            print(f"\tUnallocated hours: {employee_hours[e] - month_accum}")
            print(f"\tTotal spans: {sum(solver.Value(span) for span in flatten_dict(spans[e]))}")
            print("----")
        print(f"Total spans for all employees: {total_spans}")
        total_employee_project_count = get_total_employee_project_count()
        print(f"Distinct projects/hour count (optimized): {total_employee_project_count}")

    elif status == cp_model.FEASIBLE:
        print("""Feasible solution found. TODO handle""")

    print("Statistics")
    print("  - conflicts : %i" % solver.NumConflicts())
    print("  - branches  : %i" % solver.NumBranches())
    print("  - wall time : %f s" % solver.WallTime())

    unallocated_hours = {}

    results: Results = {}
    for e in employees:
        results[e] = {}

    for e, _projects in vars.items():
        for p in _projects.keys():
            results[e][p] = sum(solver.Value(vars[e][p][w]) for w in range(n_weeks))
        e_unallocated_hours = abs(sum(monthly_hours for monthly_hours in results[e].values()) - employee_hours[e])
        if e_unallocated_hours > 0:
            unallocated_hours[e] = e_unallocated_hours
    df = pd.DataFrame(results)

    if len(unallocated_hours) > 0:
        print("\nUnallocated employee billable hours:")
        [print("{:<25} {:<10}".format(e, f"{h}h")) for e, h in unallocated_hours.items()]

    if save_excel:
        print(f"\nSaving results to {EXCEL_SOLUTION_FILE}...")
        df.to_excel(EXCEL_SOLUTION_FILE)

    return EmployeeReporting(
        df=df,
        spans=total_spans,
        unallocated_hours=unallocated_hours,
        employee_project_count=total_employee_project_count,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Employee time reporting optimizer")
    parser.add_argument(
        "-e", "--export", action=argparse.BooleanOptionalAction, help=f"Exports solution to {EXCEL_SOLUTION_FILE}"
    )

    args = parser.parse_args()

    n_weeks = 4
    project_hours = {
        Project("Project 1"): 160,
        Project("Project 2"): 160,
        Project("Project 3"): 160,
        Project("Project 4"): 160,
    }
    employee_hours = {
        Employee("Martin"): 160,
        Employee("Jane"): 160,
        Employee("Bob"): 160,
        Employee("Alice"): 160,
    }
    employee_projects = {
        Employee("Martin"): [Project("Project 1"), Project("Project 2")],
        Employee("Jane"): [Project("Project 3")],
    }
    max_weekly_hours = 40

    employee_reporting = minimize_employee_reporting(
        project_hours=project_hours,
        employee_hours=employee_hours,
        employee_projects=employee_projects,
        max_weekly_hours=max_weekly_hours,
        n_weeks=n_weeks,
        save_excel=args.export,
    )

    # employee_hours_df = employee_reporting.df.sum(0)
    # projects_hours_df = employee_reporting.df.sum(1)
    # for project in projects:
    #     print(f"{project}: {projects_hours_df.loc[project]}")
    # for employee in employees:
    #     print(f"{employee}: {employee_hours_df.loc[employee]}")

    # polars
    # with Workbook("billing.xlsx") as wb:
    #     employee_reporting.df.write_excel(
    #         workbook = wb,
    #       worksheet = "data",)
