from ortools.sat.python import cp_model

"""
Consider three numbers.
Each can be either 0, 1, or 2.
The first two numbers are the same.
What are the different possibilities for the three numbers?
"""

model = cp_model.CpModel()
num_vals = 3
a = model.NewIntVar(0, num_vals - 1, 'a')
b = model.NewIntVar(0, num_vals - 1, 'b')
c = model.NewIntVar(0, num_vals - 1, 'c')
model.Add(a == b)
solver = cp_model.CpSolver()
printer = cp_model.VarArraySolutionPrinter([a,b,c])
solver.parameters.enumerate_all_solutions = True
status = solver.Solve(model, printer)
if status == cp_model.OPTIMAL:
    print('\n' + "All solutions found!" + '\n')
elif status == cp_model.FEASIBLE:
    print('\n' + "Some solutions found!" + '\n')
else:
    print('\n' + "No solution could be found!" +
'\n')
