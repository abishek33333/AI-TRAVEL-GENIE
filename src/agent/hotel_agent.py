class HotelAgent:
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
