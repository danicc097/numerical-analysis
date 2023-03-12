import dataclasses
from typing import ContextManager
import pytest
from billing import EmployeeHours, EmployeeProjects, ProjectHours, minimize_employee_reporting
from contextlib import nullcontext


@dataclasses.dataclass(frozen=True)
class BillingParams:
    project_hours: ProjectHours
    employee_hours: EmployeeHours
    employee_projects: EmployeeProjects
    expected_raises: ContextManager
    unallocated_hours: int
    spans: int

    def pytest_id(self):
        return repr(self)  # usually something custom


class TestBilling:
    @pytest.mark.parametrize(
        "p",
        [
            BillingParams(
                project_hours={
                    "Project 1": 140,
                    "Project 2": 20,
                    "Project 3": 300,
                    "Project 4": 10,
                },
                employee_hours={
                    "Martin": 160,
                    "Jane": 160,
                    "Bob": 150,
                    "Alice": 10,
                },
                employee_projects={},
                expected_raises=nullcontext(),
                spans=14,
                unallocated_hours=10,
            ),
            BillingParams(
                project_hours={
                    "Project 1": 140,
                    "Project 2": 20,
                    "Project 3": 300,
                    "Project 4": 10,
                },
                employee_hours={
                    "Martin": 160,
                    "Jane": 160,
                    "Bob": 150,
                    "Alice": 10,
                },
                employee_projects={
                    "Martin": ["Project 1", "Project 2"],
                    "Jane": ["Project 3"],
                },
                expected_raises=nullcontext(),
                spans=14,
                unallocated_hours=10,
            ),
            BillingParams(
                project_hours={
                    "Project 1": 140,
                    "Project 2": 20,
                    "Project 3": 300,
                    "Project 4": 10,
                },
                employee_hours={
                    "Martin": 160,
                    "Jane": 160,
                    "Bob": 150,
                    "Alice": 10,
                },
                employee_projects={
                    "Martin": ["Project 1"],  # needs 10 more hours from employees by restricting only to P1
                    "Jane": ["Project 3"],
                },
                expected_raises=pytest.raises(Exception),
                spans=0,
                unallocated_hours=0,
            ),
        ],
    )
    def test_allow_employee_reporting_with_project_restriction(
        self,
        p: BillingParams,
    ):
        n_weeks = 4
        max_weekly_hours = 40

        with p.expected_raises:
            employee_reporting = minimize_employee_reporting(
                employee_hours=p.employee_hours,
                project_hours=p.project_hours,
                employee_projects=p.employee_projects,
                n_weeks=n_weeks,
                max_weekly_hours=max_weekly_hours,
            )

            res_employee_hours = employee_reporting.df.sum(0).sum()
            res_project_hours = employee_reporting.df.sum(1).sum()

            assert res_employee_hours <= sum(h for h in p.employee_hours.values())
            assert res_employee_hours == sum(h for h in p.project_hours.values())

            assert res_project_hours == sum(h for h in p.project_hours.values())

            assert employee_reporting.spans == p.spans
            assert sum(employee_reporting.unallocated_hours.values()) == p.unallocated_hours
