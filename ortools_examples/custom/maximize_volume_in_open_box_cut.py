from ortools.linear_solver import pywraplp
from ortools.init import pywrapinit

"""
Determine the dimensions of an open box of maximum volume
that can be constructed from an A4 sheet 210 mm × 297 mm by cutting four
squares of side x from the corners and folding and gluing the edges as shown
in Fig. E2.4.

"""

# Volume V = (297 – 2x)(210 – 2x)x
#          = 62370x + 1014x^2 + 4x^3

def main():
    # Create the linear solver with the GLOP backend.
    solver: pywraplp.Solver = pywraplp.Solver.CreateSolver('GLOP')
    if not solver:
        return

    # Create the variables x and y.
    x: pywraplp.Variable = solver.NumVar(0, solver.infinity(), 'x')

    print('Number of variables =', solver.NumVariables())

    # # Create a linear constraint, 0 <= x + y <= 2.
    # ct: pywraplp.Constraint = solver.Constraint(0, 2, 'ct')
    # ct.SetCoefficient(x, 1)
    # ct.SetCoefficient(y, 1)

    print('Number of constraints =', solver.NumConstraints())

    # Create the objective function, 3 * x + y.
    # objective: pywraplp.Objective  = solver.Objective()
    # objective.SetCoefficient(x, 3)
    # objective.SetMaximization()

    solver.Maximize(62370*x + 1014*x*x + 4*x*x*x) # product not linear, raises TypeError

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        print('Solution:')
        print('Objective value =', solver.Objective().Value())
        print('x =', x.solution_value())
    else:
        print('The problem does not have an optimal solution.')


if __name__ == '__main__':
    pywrapinit.CppBridge.InitLogging('basic_example.py')
    cpp_flags = pywrapinit.CppFlags()
    cpp_flags.logtostderr = True
    cpp_flags.log_prefix = False
    pywrapinit.CppBridge.SetFlags(cpp_flags)

    main()
