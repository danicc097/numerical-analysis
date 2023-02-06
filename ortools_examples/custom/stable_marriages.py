# from https://github.com/google/or-tools/issues/1182
# not vetted at all

"""
expected:

Man 0 should marry woman 1
Woman 0 should marry man 1
Man 1 should marry woman 0
Woman 1 should marry man 0
Man 2 should marry woman 4
Woman 2 should marry man 3
Man 3 should marry woman 2
Woman 3 should marry man 4
Man 4 should marry woman 3
Woman 4 should marry man 2

"""


from ortools.sat.python import cp_model

model = cp_model.CpModel()


rank_women = [[1, 2, 4, 3, 5],
             [3, 5, 1, 2, 4],
             [5, 4, 2, 1, 3],
             [1, 3, 5, 4, 2],
             [4, 2, 3, 5, 1]]

rank_men = [[5, 1, 2, 4, 3],
           [4, 1, 3, 2, 5],
           [5, 3, 2, 4, 1],
           [1, 5, 4, 3, 2],
           [4, 3, 2, 1, 5]]


assert len(rank_women) == len(rank_men)
assert all([len(i) == len(j) for i,j in zip(rank_men, rank_women)])

n = len(rank_women)

wives = [model.NewIntVar(0, n - 1, "wives[%i]" % i) for i in range(n)]
husbands = [model.NewIntVar(0, n - 1, "husbands[%i]" % i) for i in range(n)]

for person_idx in range(n):
    model.AddElement(wives[person_idx], husbands, person_idx)
    model.AddElement(husbands[person_idx], wives, person_idx)

    man_rank_wife = model.NewIntVar(1, n, "Man rank her wife")
    model.AddElement(wives[person_idx], rank_men[person_idx], man_rank_wife)

    woman_rank_husband = model.NewIntVar(1, n, "Woman rank her husband")
    model.AddElement(husbands[person_idx], rank_women[person_idx], woman_rank_husband)

    for typ in ("husband", "wife"):
        for rank_idx in range(n):
            typ_rank, other_typ_rank = (rank_men, rank_women) if typ == "husband" else (rank_women, rank_men)
            person_rank = man_rank_wife if typ == "husband" else woman_rank_husband
            typ_var = husbands if typ == "husband" else wives

            person_prefers_other = model.NewBoolVar(f"{typ} prefer other")
            model.Add(typ_rank[person_idx][rank_idx] < person_rank).OnlyEnforceIf(person_prefers_other)
            model.Add(typ_rank[person_idx][rank_idx] >= person_rank).OnlyEnforceIf(person_prefers_other.Not())

            other_rank = model.NewIntVar(1, n, f"Other rank its {typ}")
            model.AddElement(typ_var[rank_idx], other_typ_rank[rank_idx], other_rank)

            other_prefers_partner = model.NewBoolVar(f"Other prefer its {typ}")
            model.Add(other_rank < other_typ_rank[rank_idx][person_idx]).OnlyEnforceIf(other_prefers_partner)
            model.Add(other_rank >= other_typ_rank[rank_idx][person_idx]).OnlyEnforceIf(other_prefers_partner.Not())

            model.AddImplication(person_prefers_other, other_prefers_partner)

solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.FEASIBLE:
    print("Could not find all solutions")
elif status == cp_model.OPTIMAL:
    for person_idx in range(n):
        print(f"Man {person_idx} should marry woman {solver.Value(wives[person_idx])}")
        print(f"Woman {person_idx} should marry man {solver.Value(husbands[person_idx])}")
else:
    print("Could not solve")

