import itertools
import pprint
import time
from ortools.sat.python import cp_model
from collections.abc import Iterable

def flatten(xs):
    for x in xs:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x

n_weeks = 4
project_hours = {'1': 140, '2': 20, '3': 300, '4':10}
# TODO also dict
employee_hours = [160,160,150,160,150,160,150,160,150,160,150] # employees [1,2,3]
max_weekly_hours = 40

total_employee_hours = sum(employee_hours)
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

vars = []
for u in range(len(employee_hours)):
    vars.append([])
    for w in range(n_weeks):
        vars[u].append([])
        for p in project_hours.keys():
            vars[u][w].append(model.NewIntVar(0, max_weekly_hours, f'u{u+1}_w{w+1}_p{p}'))


for u in range(len(employee_hours)):
    for w in range(n_weeks):
        model.Add(sum(vars[u][w]) <= max_weekly_hours)

    # limit sum of employee hours in a month
    model.Add(sum(sum(vars[u][w]) for w in range(n_weeks)) <= employee_hours[u])

for p in project_hours.keys():
    # restrict
    model.Add(sum(vars[u][w][int(p)-1] for w in range(n_weeks) for u in range(len(employee_hours))) == project_hours[p])


spans = []
old_spans = []
for u in range(len(employee_hours)):
    spans.append([])
    for w in range(n_weeks):
        # do not use multiplication, extremely slow (https://stackoverflow.com/questions/71961919/)ortools-cp-sat-solver-constraint-to-require-two-lists-of-variables-to-be-drawn
        # model.AddMaxEquality(employee_span, [vars[u][w][int(p)-1] for p in project_hours.keys()])
        spans[u].append([])
        for p in project_hours.keys():
            employee_span = model.NewBoolVar(f'span_u{u+1}_w{w+1}_p{p}')
            model.Add(vars[u][w][int(p)-1] > 0).OnlyEnforceIf(employee_span)
            model.Add(vars[u][w][int(p)-1] == 0).OnlyEnforceIf(employee_span.Not())
            spans[u][w].append(employee_span)
            old_spans.append(employee_span)

flattened_spans = flatten(spans)
model.Minimize(sum(flattened_spans)) #

# Solve the model
solver = cp_model.CpSolver()
status = solver.Solve(model, HourReportingPrinter())

if status == cp_model.INFEASIBLE:
    raise Exception("INFEASIBLE")
if status == cp_model.MODEL_INVALID:
    raise Exception("MODEL_INVALID")

print(f"Project billing hours: {project_hours}")

if status == cp_model.OPTIMAL:
    for u in range(len(employee_hours)):
        print(f"Employee {u+1}:")
        month_accum = 0
        for w in range(n_weeks):
            for p in project_hours.keys():
                hours = solver.Value(vars[u][w][int(p)-1])
                month_accum+=hours
                print(f"\tWeek {w+1}: {hours:<3}h on project {p:<4} Span bool={solver.Value(spans[u][w][int(p)-1])}")
        print("")
        print(f"\tAllocated hours: {month_accum}")
        print(f"\tUnallocated hours: {employee_hours[u] - month_accum}")
        print(f"\tTotal spans: {sum(solver.Value(span) for span in flatten(spans[u]))}")
        # ^ sum of spans[...]*vars[...]
        print("----")
    print(f"Total spans for all employees: {int(solver.ObjectiveValue())}")

elif status == cp_model.FEASIBLE:
    print("""Feasible solution found. TODO handle""")

print('Statistics')
print('  - conflicts : %i' % solver.NumConflicts())
print('  - branches  : %i' % solver.NumBranches())
print('  - wall time : %f s' % solver.WallTime())
