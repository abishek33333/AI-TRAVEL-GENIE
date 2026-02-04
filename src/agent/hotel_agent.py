# This agent looks at a list of hotels and picks the best one by prioritizing higher rating and lower price

class HotelAgent:
    # this class job is compare , select, justify hotels
    """
    Evaluates hotel options and recommends best accommodation
    """

    def recommend(self, hotels: list) -> dict:
        if not hotels:
            return {"error": "No hotels available"}

        best = max(
            hotels,
            key=lambda h: (h["rating"] or 0, -h["price_per_night"])
        )

        return {
            "selected_hotel": best,
            "justification": (
                "Chosen hotel provides the best balance of high user rating "
                "and affordability within the given budget."
            )
        }
    # output : A dictionary containing:The selected hotel,A short explanation
