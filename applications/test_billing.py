import pytest

class TestBilling():
    def test_allow_unallocated_employee_hours(self):
        n_weeks = 4
        project_hours = {'Project 1': 140, 'Project 2': 20, 'Project 3': 300, 'Project 4':10}
        employee_hours = {'Martin': 160, 'Jane': 160, 'Bob': 150, 'Alice':10}
        max_weekly_hours = 40

        # expect 14 spans and 10 unallocated hours
