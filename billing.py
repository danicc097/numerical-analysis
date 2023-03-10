import itertools
import pprint
from ortools.sat.python import cp_model
from collections.abc import Iterable

def flatten(xs):
    for x in xs:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x

# Define the input parameters
n_weeks = 4
project_hours = {'1': 140, '2': 20, '3': 300, '4':10} # , '4':10
hours_per_day = 8
max_weekly_hours = 40

# Initialize the CP-SAT model
model = cp_model.CpModel()

# Create the decision variables
user_hours = [160,160,150] # users [1,2,3]


print(f"Total user hours: {sum(user_hours)}")
print(f"Total billable project hours: {sum(project_hours.values())}")

if sum(user_hours) != sum(project_hours.values()):
    print("Cannot have project billing hours different than total user billable hours")
    exit(1)

vars = []
for u in range(len(user_hours)):
    vars.append([])
    for w in range(n_weeks):
        vars[u].append([])
        for p in project_hours.keys():
            vars[u][w].append(model.NewIntVar(0, max_weekly_hours, f'u{u+1}_w{w+1}_p{p}'))


for u in range(len(user_hours)):
    for w in range(n_weeks):
        model.Add(sum(vars[u][w]) <= max_weekly_hours)

    # TODO limit sum of user hours in a month
    model.Add(sum(sum(vars[u][w]) for w in range(n_weeks)) == user_hours[u])

# looks good, get all project i vars
for p in project_hours.keys():
    # pprint.pprint([vars[u][w][int(p)-1] for w in range(n_weeks) for u in range(len(user_hours))])
    model.Add(sum(vars[u][w][int(p)-1] for w in range(n_weeks) for u in range(len(user_hours))) == project_hours[p])


spans = []
old_spans = []
for u in range(len(user_hours)):
    spans.append([])
    for w in range(n_weeks):
        # do not use multiplication, extremely slow (https://stackoverflow.com/questions/71961919/)ortools-cp-sat-solver-constraint-to-require-two-lists-of-variables-to-be-drawn
        # model.AddMaxEquality(user_span, [vars[u][w][int(p)-1] for p in project_hours.keys()])
        spans[u].append([])
        for p in project_hours.keys():
            user_span = model.NewBoolVar(f'span_u{u+1}_w{w+1}_p{p}')
            model.Add(vars[u][w][int(p)-1] > 0).OnlyEnforceIf(user_span)
            model.Add(vars[u][w][int(p)-1] == 0).OnlyEnforceIf(user_span.Not())
            spans[u][w].append(user_span)
            old_spans.append(user_span)

flattened_spans = flatten(spans)
model.Minimize(sum(flattened_spans)) #

# Solve the model
solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.INFEASIBLE:
    raise Exception("INFEASIBLE")
if status == cp_model.MODEL_INVALID:
    raise Exception("MODEL_INVALID")

print(f"Project billing hours: {project_hours}")

if status == cp_model.OPTIMAL:
    for u in range(len(user_hours)):
        print(f"user {u+1}:")
        month_accum = 0
        for w in range(n_weeks):
            for p in project_hours.keys():
                hours = solver.Value(vars[u][w][int(p)-1])
                month_accum+=hours
                print(f"\tWeek {w+1}: {hours:<3}h on project {p:<4} Span bool={solver.Value(spans[u][w][int(p)-1])}")
        print(f"Total hours for user {u+1}: {month_accum}")
        print(f"Total spans for user {u+1}: {sum(solver.Value(span) for span in flatten(spans[u]))}")
        # ^ sum of spans[...]*vars[...]
        print("----")
    print(f"Total spans for all users: {int(solver.ObjectiveValue())}")
elif status == cp_model.FEASIBLE:
    print("""Feasible solution found. TODO handle""")

print('\nAdvanced usage:')
print('Problem solved in %f milliseconds' % solver.WallTime())
print(f"Solution info: {solver.SolutionInfo()}")
