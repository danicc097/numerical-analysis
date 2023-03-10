import itertools
import pprint
from ortools.sat.python import cp_model

def flatten(l):
    return [item for sublist in l for item in sublist]

# Define the input parameters
n_weeks = 4
project_hours = {'1': 140, '2': 20, '3': 310}
hours_per_day = 8
max_weekly_hours = 40

# Initialize the CP-SAT model
model = cp_model.CpModel()

# Create the decision variables
user_hours = [160,160,150] # users [1,2,3]
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

# looks good, get all project i vars
for p in project_hours.keys():
    # pprint.pprint([vars[u][w][int(p)-1] for w in range(n_weeks) for u in range(len(user_hours))])
    model.Add(sum(vars[u][w][int(p)-1] for w in range(n_weeks) for u in range(len(user_hours))) == project_hours[p])

spans = []
old_spans = []
for u in range(len(user_hours)):
    spans.append([])
    for w in range(n_weeks):
        user_span = model.NewBoolVar(f'span_u{u+1}_w{w+1}')
        # TODO bool var true based on project hour allocation if allocation > 0
        # see https://stackoverflow.com/questions/65500478/or-tools-how-to-set-the-value-of-a-boolvar-if-the-sum-of-some-intvars-is-great
        # do not use multiplication, extremely slow (https://stackoverflow.com/questions/71961919/)ortools-cp-sat-solver-constraint-to-require-two-lists-of-variables-to-be-drawn
        # model.AddMaxEquality(user_span, [vars[u][w][int(p)-1] for p in project_hours.keys()])
        model.Add(sum(vars[u][w]) > 0).OnlyEnforceIf(user_span)
        model.Add(sum(vars[u][w]) == 0).OnlyEnforceIf(user_span.Not())
        spans[u].append(user_span)
        old_spans.append(user_span)

flattened_spans = list(itertools.chain(*spans))
print(flattened_spans)
print(old_spans)
model.Minimize(sum(flattened_spans)) #

# Solve the model
solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.INFEASIBLE:
    raise Exception("INFEASIBLE")
if status == cp_model.MODEL_INVALID:
    raise Exception("MODEL_INVALID")

# pprint.pprint(spans)
# pprint.pprint(vars)
print(f"Project billing hours: {project_hours}")

# can access by var name
print([solver.Value(span) for span in list(itertools.chain(*spans))])

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    for u in range(len(user_hours)):
        print(f"user {u+1}:")
        month_accum = 0
        for w in range(n_weeks):
            for p in project_hours.keys():
                hours = solver.Value(vars[u][w][int(p)-1])
                month_accum+=hours
                print(f"\tWeek {w+1}: {hours:<3}h on project {p:<4} Span bool={solver.Value(spans[u][w])}")
        print(f"Total hours for user {u+1}: {month_accum}")
        print(f"Total spans for user {u+1}: {sum(solver.Value(spans[u][w]) for w in range(n_weeks))}")
        # ^ sum of spans[...]*vars[...]
        print("----")
    print(f"Total span for all users: {solver.ObjectiveValue():f}")
else:
    print("No optimal or feasible solution found.")
