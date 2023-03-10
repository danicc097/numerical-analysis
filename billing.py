import pprint
from ortools.sat.python import cp_model

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

# Add the constraints
for u in range(len(user_hours)):
    # for w in range(n_weeks):
    #     model.Add(sum(vars[u][w]) == sum(project_hours.values()))

    for p in project_hours.keys():
        # model.Add(sum(vars[u][w][int(p)-1] for u in range(len(user_hours))) == project_hours[p])
        pass

    model.Add(sum(vars[u][w]) == max_weekly_hours)

# Define the objective
spans = []
for u in range(len(user_hours)):
    for w in range(n_weeks):
        user_span = model.NewBoolVar(f'span_u{u+1}_w{w+1}')
        # model.AddMaxEquality(user_span, [vars[u][w][int(p)-1] for p in project_hours.keys()])
        spans.append(user_span)
model.Minimize(sum(spans))

pprint.pprint(spans)
pprint.pprint(vars)

# Solve the model
solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.INFEASIBLE:
    raise Exception("INFEASIBLE")
if status == cp_model.MODEL_INVALID:
    raise Exception("MODEL_INVALID")

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    for u in range(len(user_hours)):
        print(f"user {u+1}:")
        for w in range(n_weeks):
            for p in project_hours.keys():
                hours = solver.Value(vars[u][w][int(p)-1])
                print(f"Week {w+1}: {hours}h on project {p}")
        print(f"Total span for user {u+1}: {solver.Value(spans[u*n_weeks]):f}")
        print("----")
    print(f"Total span for all users: {solver.ObjectiveValue():f}")
else:
    print("No optimal or feasible solution found.")
