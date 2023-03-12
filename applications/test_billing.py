from typing import ContextManager
import pytest
from billing import EmployeeHours, EmployeeProjects, ProjectHours, minimize_employee_reporting
from contextlib import nullcontext


class TestBilling:
    def test_allow_employee_reporting_with_unallocated_hours(self):
        n_weeks = 4
        project_hours = {
            "Project 1": 140,
            "Project 2": 20,
            "Project 3": 300,
            "Project 4": 10,
        }
        employee_hours = {"Martin": 160, "Jane": 160, "Bob": 150, "Alice": 10}
        max_weekly_hours = 40

        employee_reporting = minimize_employee_reporting(
            employee_hours=employee_hours,
            project_hours=project_hours,
            n_weeks=n_weeks,
            max_weekly_hours=max_weekly_hours,
        )

        res_employee_hours = employee_reporting.df.sum(0).sum()
        res_project_hours = employee_reporting.df.sum(1).sum()

        assert res_employee_hours <= sum(h for h in employee_hours.values())
        assert res_employee_hours == sum(h for h in project_hours.values())

        assert res_project_hours == sum(h for h in project_hours.values())

        assert employee_reporting.spans == 14
        assert sum(employee_reporting.unallocated_hours.values()) == 10

    @pytest.mark.parametrize(
        "project_hours, employee_hours, employee_projects, expected_raises",
        [
            (
                {
                    "Project 1": 140,
                    "Project 2": 20,
                    "Project 3": 300,
                    "Project 4": 10,
                },
                {
                    "Martin": 160,
                    "Jane": 160,
                    "Bob": 150,
                    "Alice": 10,
                },
                {
                    "Martin": ["Project 1", "Project 2"],
                    "Jane": ["Project 3"],
                },
                nullcontext(),
            ),
            (
                {
                    "Project 1": 140,
                    "Project 2": 20,
                    "Project 3": 300,
                    "Project 4": 10,
                },
                {
                    "Martin": 160,
                    "Jane": 160,
                    "Bob": 150,
                    "Alice": 10,
                },
                {
                    "Martin": ["Project 1"],  # will need more available employee hours -> infeasible
                    "Jane": ["Project 3"],
                },
                pytest.raises(Exception),
            ),
        ],
    )
    def test_allow_employee_reporting_with_project_restriction(
        self,
        project_hours: ProjectHours,
        employee_hours: EmployeeHours,
        employee_projects: EmployeeProjects,
        expected_raises: ContextManager,
    ):
        n_weeks = 4
        max_weekly_hours = 40

        with expected_raises:
            employee_reporting = minimize_employee_reporting(
                employee_hours=employee_hours,
                project_hours=project_hours,
                employee_projects=employee_projects,
                n_weeks=n_weeks,
                max_weekly_hours=max_weekly_hours,
            )

            res_employee_hours = employee_reporting.df.sum(0).sum()
            res_project_hours = employee_reporting.df.sum(1).sum()

            assert res_employee_hours <= sum(h for h in employee_hours.values())
            assert res_employee_hours == sum(h for h in project_hours.values())

            assert res_project_hours == sum(h for h in project_hours.values())

            assert employee_reporting.spans == 14
            assert sum(employee_reporting.unallocated_hours.values()) == 10
