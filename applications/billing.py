import itertools
import pprint
import time
from typing import Dict, List
from ortools.sat.python import cp_model

from collections.abc import Iterable

def flatten(xs):
    for x in xs:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x

Employee = str
Project = str
Vars = Dict[Employee,List[Dict[Project,cp_model.IntVar]]]
Spans = Dict[Employee,List[Dict[Project,cp_model.IntVar]]]

n_weeks = 4
project_hours: Dict[Project, int] = {'Project 1': 140, 'Project 2': 20, 'Project 3': 300, 'Project 4':10}
employee_hours: Dict[Employee, int] = {'Martin': 160, 'Jane': 160, 'Bob': 150, 'Alice':10}
max_weekly_hours = 40

total_employee_hours = sum(employee_hours.values())
total_project_hours = sum(project_hours.values())
print(f"Total employee hours: {total_employee_hours}")
print(f"Total billable project hours: {total_project_hours}")

if total_employee_hours < total_project_hours:
    print("Cannot have project billing hours higher than total employee billable hours")
    exit(1)
elif total_employee_hours > total_project_hours:
    print("####")
    print("#### Unallocated billable hours:", total_employee_hours - total_project_hours)
    print("####")


# Initialize the CP-SAT model
model = cp_model.CpModel()

class HourReportingPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, dummy = None):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__solution_count = 0
        self.__start_time = time.time()
        self.__dummy = dummy

    def on_solution_callback(self):
        current_time = time.time()
        objective = self.ObjectiveValue()
        print("Solution %i, time = %f s, objective = %i" %
              (self.__solution_count, current_time - self.__start_time,
               objective))
        self.__solution_count += 1

        # show useful info...

    def num_solutions(self):
        return self.__solution_count


vars: Vars = dict()

for u in employee_hours.keys():
    vars[u] = []
    for w in range(n_weeks):
        vars[u].append(dict())
        for p in project_hours.keys():
            vars[u][w][p] = model.NewIntVar(0, max_weekly_hours, f'var_u_{u}_w_{w+1}_p_{p}')


for u in employee_hours.keys():
    for w in range(n_weeks):
        model.Add(sum(vars[u][w].values()) <= max_weekly_hours)

    # limit sum of employee hours in a month
    model.Add(sum(sum(vars[u][w].values()) for w in range(n_weeks)) <= employee_hours[u])

for p in project_hours.keys():
    # restrict
    model.Add(sum(vars[u][w][p] for w in range(n_weeks) for u in employee_hours.keys()) == project_hours[p])


spans: Spans = {}
for u in employee_hours.keys():
    spans[u] = []
    for w in range(n_weeks):
        # do not use multiplication, extremely slow (https://stackoverflow.com/questions/71961919/)ortools-cp-sat-solver-constraint-to-require-two-lists-of-variables-to-be-drawn
        # model.AddMaxEquality(employee_span, [vars[u][w][p] for p in project_hours.keys()])
        spans[u].append(dict())
        for p in project_hours.keys():
            employee_span = model.NewBoolVar(f'span_u_{u}_w_{w}_p_{p}')
            model.Add(vars[u][w][p] > 0).OnlyEnforceIf(employee_span)
            model.Add(vars[u][w][p] == 0).OnlyEnforceIf(employee_span.Not())
            spans[u][w][p] = employee_span

pprint.pprint(spans)
pprint.pprint(vars)

flattened_spans = flatten(flatten(j.values()) for i in spans.values() for j in i)
model.Minimize(sum(flattened_spans))

# Solve the model
solver = cp_model.CpSolver()
status = solver.Solve(model, HourReportingPrinter())

if status == cp_model.INFEASIBLE:
    raise Exception("INFEASIBLE")
if status == cp_model.MODEL_INVALID:
    raise Exception("MODEL_INVALID")

print(f"Project billing hours: {project_hours}")
print(f"Employee hours: {employee_hours}")
print("-------------------------------------------")

if status == cp_model.OPTIMAL:
    for u in employee_hours.keys():
        print(f"Employee {u}:")
        month_accum = 0
        for w in range(n_weeks):
            for p in project_hours.keys():
                hours = solver.Value(vars[u][w][p])
                month_accum+=hours
                print(f"\tWeek {w+1}: {hours:<3}h on project {p:<20} Span bool={solver.Value(spans[u][w][p])}")
        print("")
        print(f"\tAllocated hours: {month_accum}")
        print(f"\tUnallocated hours: {employee_hours[u] - month_accum}")
        print(f"\tTotal spans: {sum(solver.Value(span) for span in spans[u][w].values())}")
        # ^ sum of spans[...]*vars[...]
        print("----")
    print(f"Total spans for all employees: {int(solver.ObjectiveValue())}")

elif status == cp_model.FEASIBLE:
    print("""Feasible solution found. TODO handle""")

print('Statistics')
print('  - conflicts : %i' % solver.NumConflicts())
print('  - branches  : %i' % solver.NumBranches())
print('  - wall time : %f s' % solver.WallTime())
