from src.utils.expense_calculator import Calculator
from typing import List
from langchain.tools import tool
from pydantic import BaseModel, Field

# Schema to ensure the AI passes 'costs' correctly as a list of numbers
class CalculatorInput(BaseModel):
    costs: List[float] = Field(description="List of numerical costs to sum up")

class CalculatorTool:
    def __init__(self):
        self.calculator = Calculator()
        self.calculator_tool_list = self._setup_tools()

    def _setup_tools(self) -> List:
        """Setup all tools for the calculator tool"""

        @tool
        def estimate_total_hotel_cost(price_per_night: float, total_days: int) -> float:
            """
            Calculate total hotel cost.
            """
            try:
                # Ensure inputs are numbers
                return self.calculator.multiply(float(price_per_night), int(total_days))
            except Exception as e:
                raise ValueError(f"Hotel cost calculation failed: {e}")

        # Apply the explicit schema here to fix the "unexpected keyword argument" error
        @tool(args_schema=CalculatorInput)
        def calculate_total_expense(costs: List[float]) -> float:
            """
            Calculate total expense of the trip by summing a list of costs.
            """
            try:
                numeric_costs = [float(c) for c in costs]
                return self.calculator.calculate_total(*numeric_costs)
            except Exception as e:
                raise ValueError(f"Total expense calculation failed: {e}")

        @tool
        def calculate_daily_expense_budget(total_cost: float, days: int) -> float:
            """
            Calculate daily expense budget.
            """
            try:
                return self.calculator.calculate_daily_budget(float(total_cost), int(days))
            except Exception as e:
                raise ValueError(f"Daily budget calculation failed: {e}")

        return [
            estimate_total_hotel_cost,
            calculate_total_expense,
            calculate_daily_expense_budget,
        ]



# -----------------------------------------------------------------------------------------------------






# from src.utils.expense_calculator import Calculator
# from typing import List
# from langchain.tools import tool


# class CalculatorTool:
#     def __init__(self):
#         self.calculator = Calculator()
#         self.calculator_tool_list = self._setup_tools()

#     def _setup_tools(self) -> List:
#         """Setup all tools for the calculator tool"""

#         @tool
#         def estimate_total_hotel_cost(price_per_night, total_days) -> float:
#             """
#             Calculate total hotel cost.

#             Args:
#                 price_per_night: Cost per night (can be string or number)
#                 total_days: Number of days (can be string or number)

#             Returns:
#                 float: Total hotel cost
#             """
#             try:
#                 price = float(price_per_night)
#                 days = int(float(total_days))
#                 return self.calculator.multiply(price, days)
#             except Exception as e:
#                 raise ValueError(f"Hotel cost calculation failed: {e}")

#         @tool
#         def calculate_total_expense(*costs) -> float:
#             """
#             Calculate total expense of the trip.

#             Args:
#                 costs: Variable list of costs (strings or numbers)

#             Returns:
#                 float: Total cost
#             """
#             try:
#                 numeric_costs = [float(c) for c in costs]
#                 return self.calculator.calculate_total(*numeric_costs)
#             except Exception as e:
#                 raise ValueError(f"Total expense calculation failed: {e}")

#         @tool
#         def calculate_daily_expense_budget(total_cost, days) -> float:
#             """
#             Calculate daily expense budget.

#             Args:
#                 total_cost: Total trip cost
#                 days: Number of days

#             Returns:
#                 float: Daily budget
#             """
#             try:
#                 total = float(total_cost)
#                 days = int(float(days))
#                 return self.calculator.calculate_daily_budget(total, days)
#             except Exception as e:
#                 raise ValueError(f"Daily budget calculation failed: {e}")

#         return [
#             estimate_total_hotel_cost,
#             calculate_total_expense,
#             calculate_daily_expense_budget,
#         ]
