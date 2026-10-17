import json
import unittest

from langchain_core.messages import ToolMessage

from travel_graph import (
    extract_budget_result,
    route_after_validation,
    validate_request,
)


class TravelGraphTests(unittest.TestCase):
    def test_budget_is_summed_deterministically(self) -> None:
        from travel_graph import calculate_trip_budget

        result = json.loads(
            calculate_trip_budget.invoke(
                {
                    "days": 3,
                    "nights": 2,
                    "hotel_per_night": 300,
                    "food_per_day": 100,
                    "transport_per_day": 50,
                    "tickets_total": 200,
                }
            )
        )
        self.assertEqual(result["total"], 1250)
        self.assertEqual(result["breakdown"]["hotel"], 600)

    def test_invalid_request_stops_before_model(self) -> None:
        state = {
            "messages": [],
            "destination": "",
            "num_days": 3,
            "error": "",
        }
        validation = validate_request(state)
        state.update(validation)
        self.assertIn("目的地", validation["error"])
        self.assertEqual(route_after_validation(state), "__end__")

    def test_budget_is_read_from_tool_message(self) -> None:
        message = ToolMessage(
            content=json.dumps(
                {
                    "total": 800,
                    "breakdown": {
                        "hotel": 400,
                        "food": 200,
                        "transport": 100,
                        "tickets": 100,
                    },
                }
            ),
            tool_call_id="budget-1",
            name="calculate_trip_budget",
        )
        total, breakdown = extract_budget_result([message])
        self.assertEqual(total, 800)
        self.assertEqual(breakdown["hotel"], 400)


if __name__ == "__main__":
    unittest.main()
