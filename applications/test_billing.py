import dataclasses
from typing import ContextManager, Dict, List
import pytest
from billing import Employee, EmployeeHours, EmployeeProjects, Project, ProjectHours, minimize_employee_reporting
from contextlib import nullcontext


@dataclasses.dataclass(frozen=True)
class BillingTestCase:
    name: str
    project_hours: ProjectHours
    employee_hours: EmployeeHours
    employee_projects: EmployeeProjects
    expected_raises: ContextManager
    expected_unallocated_hours: int
    weekly_hours_constraints: Dict[Employee, List[int]]
    expected_spans: int
    expected_employee_project_count: int | None

    def pytest_id(self):
        return f"BillingTestCase({self.name})"  # usually something custom


class TestBilling:
    n_weeks = 4
    max_weekly_hours = 40

    @pytest.mark.parametrize(
        "p",
        [

            BillingTestCase(
                name="minimize number of projects a user allocates to in a month",
                project_hours={
                    Project("Project 1"): max_weekly_hours * n_weeks,
                    Project("Project 2"): max_weekly_hours * n_weeks,
                    Project("Project 3"): max_weekly_hours * n_weeks,
                    Project("Project 4"): max_weekly_hours * n_weeks,
                },
                employee_hours={
                    Employee("Martin"): max_weekly_hours * n_weeks,
                    Employee("Jane"): max_weekly_hours * n_weeks,
                    Employee("Bob"): max_weekly_hours * n_weeks,
                    Employee("Alice"): max_weekly_hours * n_weeks,
                },
                employee_projects={},
                expected_raises=nullcontext(),
                expected_spans=n_weeks * 4,
                expected_unallocated_hours=0,
                expected_employee_project_count=4,
                weekly_hours_constraints=None
            ),
            BillingTestCase(
                name="reporting with excess employee hours",
                project_hours={
                    Project("Project 1"): 140,
                    Project("Project 2"): 20,
                    Project("Project 3"): 300,
                    Project("Project 4"): 10,
                },
                employee_hours={
                    Employee("Martin"): 160,
                    Employee("Jane"): 160,
                    Employee("Bob"): 150,
                    Employee("Alice"): 10,
                },
                employee_projects={},
                expected_raises=nullcontext(),
                expected_spans=14,
                expected_unallocated_hours=10,
                expected_employee_project_count=None,
                weekly_hours_constraints=None
            ),
            BillingTestCase(
                name="reporting with employee project restrictions",
                project_hours={
                    Project("Project 1"): 140,
                    Project("Project 2"): 20,
                    Project("Project 3"): 300,
                    Project("Project 4"): 10,
                },
                employee_hours={
                    Employee("Martin"): 160,
                    Employee("Jane"): 160,
                    Employee("Bob"): 150,
                    Employee("Alice"): 10,
                },
                employee_projects={
                    Employee("Martin"): [Project("Project 1"), Project("Project 2")],
                    Employee("Jane"): [Project("Project 3")],
                },
                expected_raises=nullcontext(),
                expected_spans=14,
                expected_unallocated_hours=10,
                expected_employee_project_count=None,
                weekly_hours_constraints=None
            ),
            BillingTestCase(
                name="infeasible assignment due to employee project restrictions",
                project_hours={
                    Project("Project 1"): 140,
                    Project("Project 2"): 20,
                    Project("Project 3"): 300,
                    Project("Project 4"): 10,
                },
                employee_hours={
                    Employee("Martin"): 160,
                    Employee("Jane"): 160,
                    Employee("Bob"): 150,
                    Employee("Alice"): 10,
                },
                employee_projects={
                    Employee("Martin"): [
                        Project("Project 1")
                    ],  # needs 10 more hours from employees by restricting only to P1
                    Employee("Jane"): [Project("Project 3")],
                },
                expected_raises=pytest.raises(Exception),
                expected_spans=0,
                expected_unallocated_hours=0,
                expected_employee_project_count=None,
                weekly_hours_constraints=None
            ),
            BillingTestCase(
                name="reporting with weekly hours constraints",
                project_hours={
                    Project("Project 1"): 140,
                    Project("Project 2"): 20,
                    Project("Project 3"): 300,
                    Project("Project 4"): 10,
                },
                employee_hours={
                    Employee("Martin"): 160,
                    Employee("Jane"): 160,
                    Employee("Bob"): 150,
                    Employee("Alice"): 10,
                },
                employee_projects={},
                expected_raises=nullcontext(),
                expected_spans=15, # 14 + 1 extra from alice weekly hour constraints
                expected_unallocated_hours=10,
                expected_employee_project_count=None,
                weekly_hours_constraints={
                    Employee("Alice"): [5, 5, 0, 0],
                },
            ),
        ],
    )
    def test_allow_employee_reporting(
        self,
        p: BillingTestCase,
    ):
        with p.expected_raises:
            employee_reporting = minimize_employee_reporting(
                employee_hours=p.employee_hours,
                project_hours=p.project_hours,
                employee_projects=p.employee_projects,
                n_weeks=self.n_weeks,
                max_weekly_hours=self.max_weekly_hours,
                weekly_hours_constraints=p.weekly_hours_constraints,
            )

            res_employee_hours = employee_reporting.df.sum(0).sum()
            res_project_hours = employee_reporting.df.sum(1).sum()

            assert res_employee_hours <= sum(h for h in p.employee_hours.values())
            assert res_employee_hours == sum(h for h in p.project_hours.values())
            assert res_project_hours == sum(h for h in p.project_hours.values())
            assert employee_reporting.spans == p.expected_spans
            assert sum(employee_reporting.unallocated_hours.values()) == p.expected_unallocated_hours

            if p.expected_employee_project_count is not None:
                assert (
                    employee_reporting.employee_project_count == p.expected_employee_project_count
                )  # projects per user are minimized in subsequent optimization run
