# This class looks at many flight options, scores each one using price,
#  travel time, and layovers, then ranks them to recommend the best flight.

from typing import List, Dict
# this class compares, scores, recommends
class FlightAgent:
    """
    Evaluates flight options and recommends the optimal one based on weighted criteria.
    Weights: Price (50%), Duration (30%), Layovers (20%).
    """
    
    # Scoring Weights
    WEIGHT_PRICE = 0.50
    WEIGHT_DURATION = 0.30
    WEIGHT_LAYOVERS = 0.20

    def evaluate(self, flights: List[Dict]) -> List[Dict]:
        # it returns best flights which hav best scored,ranked,best one
        """
        Filters, scores, and ranks a list of flight options.
        Returns the list sorted by best score (ascending).
        """
        if not flights:
            return []

        # 1. Determine ranges for normalization
        prices = [f["price"] for f in flights]
        durations = [f["duration_minutes"] for f in flights]
        
        min_price, max_price = min(prices), max(prices)
        min_duration, max_duration = min(durations), max(durations)
        
        # Avoid division by zero
        price_range = max_price - min_price if max_price > min_price else 1
        duration_range = max_duration - min_duration if max_duration > min_duration else 1
        # Normalization converts everything into 0.0 → 1.0 scale

        scored_flights = []
        
        for f in flights:
            # Each flight is evaluated one by one.
            # 2. Normalize Metrics (0.0 = Best, 1.0 = Worst)
            norm_price = (f["price"] - min_price) / price_range
            norm_duration = (f["duration_minutes"] - min_duration) / duration_range
            
            # Layovers: 0.0 for direct, 0.5 for 1 stop, 1.0 for 2+ stops
            norm_layovers = min(f["layovers"] * 0.5, 1.0)

            # 3. Calculate Weighted Score (Lower is Better)
            score = (
                (norm_price * self.WEIGHT_PRICE) +
                (norm_duration * self.WEIGHT_DURATION) +
                (norm_layovers * self.WEIGHT_LAYOVERS)
            )
            
            f["score"] = round(score, 4)
            f["recommendation_reason"] = self._generate_reason(f, norm_price, norm_duration)
            scored_flights.append(f)

        # 4. Sort by Score (Ascending)
        ranked_flights = sorted(scored_flights, key=lambda x: x["score"])
        # Lowest score → top of list,Best flight always comes first.

        # 5. Tag the best option
        if ranked_flights:
            ranked_flights[0]["tags"] = ["AI Recommended", "Best Value"]
            
        return ranked_flights

    def _generate_reason(self, flight: Dict, n_price: float, n_time: float) -> str:
        """Generates a human-readable justification for the choice."""
        reasons = []
        
        if n_price == 0.0: reasons.append("Lowest Price")
        elif n_price <= 0.2: reasons.append("Great Value")
        
        if n_time == 0.0: reasons.append("Fastest Route")
        elif n_time <= 0.2: reasons.append("Quick Flight")
        
        if flight["layovers"] == 0: reasons.append("Non-stop")
        elif flight["layovers"] == 1: reasons.append("1 Short Stop")
        
        if not reasons: return "Balanced Option"
        return ", ".join(reasons)




# ---------------------------------------------------------------------------------------------------



# class FlightAgent:
#     """
#     Evaluates flight options and recommends the optimal one
#     """

#     def recommend(self, flights: list) -> dict:
#         if not flights:
#             return {"error": "No flights available"}

#         best = min(
#             flights,
#             key=lambda f: (f["price"], f["layovers"], f["duration_minutes"])
#         )

#         return {
#             "selected_flight": best,
#             "justification": (
#                 "Selected flight offers the lowest price with minimal layovers "
#                 "and shortest travel duration."
#             )
#         }
