import itertools
import pprint
import time
from typing import Dict, List
from ortools.sat.python import cp_model

from collections.abc import Iterable
import pandas as pd

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


Employee = str
Project = str
Vars = Dict[Employee,Dict[Project,List[cp_model.IntVar]]]
Spans = Dict[Employee,Dict[Project,List[cp_model.IntVar]]]

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

for e in employee_hours.keys():
    vars[e] = {}
    for p in project_hours.keys():
        vars[e][p] = []
        for w in range(n_weeks):
            vars[e][p].append(model.NewIntVar(0, max_weekly_hours, f'var_u_{e}_p_{p}_w_{w+1}'))
pprint.pprint(vars)


# {'Alice': {'Project 1': [var_u_Alice_p_Project 1_w_1(0..40),
#                          var_u_Alice_p_Project 1_w_2(0..40),
#                          var_u_Alice_p_Project 1_w_3(0..40),
#                          var_u_Alice_p_Project 1_w_4(0..40)],
#            'Project 2': [var_u_Alice_p_Project 2_w_1(0..40),
#                          var_u_Alice_p_Project 2_w_2(0..40),
#                          var_u_Alice_p_Project 2_w_3(0..40),
#                          var_u_Alice_p_Project 2_w_4(0..40)],
#            'Project 3': [var_u_Alice_p_Project 3_w_1(0..40),
#                          var_u_Alice_p_Project 3_w_2(0..40),
#                          var_u_Alice_p_Project 3_w_3(0..40),
#                          var_u_Alice_p_Project 3_w_4(0..40)],
#            'Project 4': [var_u_Alice_p_Project 4_w_1(0..40),
#                          var_u_Alice_p_Project 4_w_2(0..40),
#                          var_u_Alice_p_Project 4_w_3(0..40),
#                          var_u_Alice_p_Project 4_w_4(0..40)]},
for e in employee_hours.keys():
    for p in project_hours.keys():
            model.Add(sum(vars[e][p]) <= max_weekly_hours)

    # upper limit sum of employee hours in a month for all projects
    model.Add(sum(sum(vars[e][p]) for p in project_hours.keys()) <= employee_hours[e])

for p in project_hours.keys():
    # all project billing hours must be allocated in the end
    model.Add(sum(sum(vars[e][p]) for e in employee_hours.keys()) == project_hours[p])

spans: Spans = {}
for e in employee_hours.keys():
    spans[e] = {}
    for p in project_hours.keys():
        spans[e][p] = []
        for w in range(n_weeks):
            # do not use multiplication, extremely slow (https://stackoverflow.com/questions/71961919/ortools-cp-sat-solver-constraint-to-require-two-lists-of-variables-to-be-drawn)
            employee_span = model.NewBoolVar(f'span_u_{e}_p_{p}_w_{w+1}')
            model.Add(vars[e][p][w] > 0).OnlyEnforceIf(employee_span)
            model.Add(vars[e][p][w] == 0).OnlyEnforceIf(employee_span.Not())
            spans[e][p].append(employee_span)

pprint.pprint(spans)
pprint.pprint(vars)

flattened_spans = flatten(flatten(j) for i in spans.values() for j in i.values())
model.Minimize(sum(flattened_spans))
# TODO minimize number of different projects per user (addition with less weight than span)

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
    for e in employee_hours.keys():
        print(f"Employee {e}:")
        month_accum = 0
        for w in range(n_weeks):
            for p in project_hours.keys():
                hours = solver.Value(vars[e][p][w])
                month_accum+=hours
                print(f"\tWeek {w+1}: {hours:<3}h on project {p:<20} Span bool={solver.Value(spans[e][p][w])}")
        print("")
        print(f"\tAllocated hours: {month_accum}")
        print(f"\tUnallocated hours: {employee_hours[e] - month_accum}")
        print(f"\tTotal spans: {sum(solver.Value(span) for span in flatten_dict(spans))}")
        # ^ sum of spans[...]*vars[...]
        print("----")
    print(f"Total spans for all employees: {int(solver.ObjectiveValue())}")

elif status == cp_model.FEASIBLE:
    print("""Feasible solution found. TODO handle""")

print('Statistics')
print('  - conflicts : %i' % solver.NumConflicts())
print('  - branches  : %i' % solver.NumBranches())
print('  - wall time : %f s' % solver.WallTime())

project_cols = project_hours.keys()
employee_cols = employee_hours.keys()
df = pd.DataFrame(columns=project_cols, index=employee_cols)

for employee, projects in vars.items():
    for project, weeks in projects.items():
        for week, var in enumerate(weeks, start=1):
            col = f'{project} (Week {project})'
            df.loc[employee, project] = solver.Value(var) or 0
            df.rename(columns={project: col}, inplace=True)
    # print(df.loc[employee])

print(df)
df.to_excel("billing.xlsx")
