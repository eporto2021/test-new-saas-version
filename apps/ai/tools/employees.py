from pydantic import BaseModel
from pydantic_ai import RunContext
from pydantic_ai.toolsets import FunctionToolset

from apps.ai.types import UserDependencies
from pegasus.apps.employees.models import Employee


class EmployeeData(BaseModel):
    """Employee information."""

    id: int | None = None
    name: str
    department: str
    salary: int

    @classmethod
    def from_employee(cls, employee: Employee) -> "EmployeeData":
        return cls(id=employee.id, name=employee.name, department=employee.department, salary=employee.salary)


async def list_employees(ctx: RunContext["UserDependencies"]) -> list[EmployeeData]:
    """List all employees.

    Args:
        user: The logged in user.
    """
    employees = []
    async for employee in Employee.objects.filter(user=ctx.deps.user).aiterator():
        employees.append(employee)
    return [EmployeeData.from_employee(employee) for employee in employees]


def create_employee(ctx: RunContext["UserDependencies"], employee_data: EmployeeData) -> EmployeeData:
    """Create an employee.

    Args:
        employee_data: The employee data.
    """
    employee = Employee.objects.create(user=ctx.deps.user, **employee_data.model_dump(exclude={"id"}))
    return EmployeeData.from_employee(employee)


def update_employee(ctx: RunContext["UserDependencies"], employee_data: EmployeeData) -> EmployeeData:
    """Update an employee.

    Args:
        employee_data: The employee data.
    """
    employee = Employee.objects.get(id=employee_data.id, user=ctx.deps.user)
    employee.name = employee_data.name
    employee.department = employee_data.department
    employee.salary = employee_data.salary
    employee.save()
    return EmployeeData.from_employee(employee)


def delete_employee(ctx: RunContext["UserDependencies"], employee_data: EmployeeData) -> EmployeeData:
    """Delete an employee.

    Args:
        employee_data: The employee data.
    """
    employee = Employee.objects.get(id=employee_data.id, user=ctx.deps.user)
    data = EmployeeData.from_employee(employee)
    employee.delete()
    return data


employee_toolset = FunctionToolset(
    tools=[
        list_employees,
        create_employee,
        update_employee,
        delete_employee,
    ]
)
