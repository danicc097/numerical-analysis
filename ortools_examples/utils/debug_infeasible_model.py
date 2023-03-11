from ortools.sat.python import cp_model

"""
Utilities from ortools to debug an infeasible model.

See https://github.com/google/or-tools/issues/973
"""

model = cp_model.CpModel()

v0 = model.NewBoolVar("buggyVarIndexToVarProto")
v1 = model.NewBoolVar("v1")
v2 = model.NewBoolVar("v2")

i1 = model.NewIntVar(0, 5, "i1")
i2 = model.NewIntVar(0, 5, "i2")

# Constraints
model.Add(i1+i2 >= 11).OnlyEnforceIf(v1) # v1 can't be satisfied
model.Add(i1+i2 <= 5).OnlyEnforceIf(v2)

# Assumptions
# model.Proto().assumptions are a list of literals. The model will be solved assuming all these literals are true.
# Compared to just fixing the domain of these literals, using this mechanism is slower but allows in case
# the model is INFEASIBLE to get a potentially small subset of them that can be used to explain the infeasibility.
model.Proto().assumptions.append(v1.Index())
model.Proto().assumptions.append(v2.Index())

# Creates a solver and solves the model.
solver = cp_model.CpSolver()
status = solver.Solve(model)

assert status == cp_model.INFEASIBLE
# should print v1
for var_index in solver.ResponseProto().sufficient_assumptions_for_infeasibility:
    # A subset of the model "assumptions" field. This will only be filled if the status is INFEASIBLE.
    # This subset of assumption will be enough to still get an infeasible problem.
    print("infeasible var index:", var_index)
    print("var info:")
    print(model.VarIndexToVarProto(var_index))
    print("-------------")
