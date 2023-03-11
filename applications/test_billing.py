import pytest
from billing import minimize_employee_reporting


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
