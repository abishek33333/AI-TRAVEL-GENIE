# Reproducibility Statement

## Hardware Assumptions
* **Environment**: Tested on Hugging Face Spaces (CPU Basic) and local Windows 11.
* **Resources**: Minimal; requires < 2GB RAM as LLM inference is handled via API.
* **Internet**: A stable connection is required to reach Groq and SerpApi endpoints.

## Runtime Estimates
* **Cold Start**: ~15 seconds to load the LangChain environment and tools.
* **Inference**: A full trip itinerary (3-5 days) typically takes 20-40 seconds depending on API latency.

## Random Seed Handling
* **LLM Determinism**: The `temperature` is pinned to `0.1` in `src/config/config_loader.py` to minimize creative drift.
* **System Seed**: Where applicable, `random.seed(42)` is utilized for synthetic data ordering.

## Known Sources of Nondeterminism
* **Search Results**: Real-time flight and hotel data from SerpApi will change daily based on live availability.
* **LLM Variability**: Even with low temperature, Llama-3 models may exhibit slight variations in formatting across identical runs.

## Cost Considerations
* **API Usage**: The project operates entirely within the Free Tier of Groq and SerpApi.
* **Compute**: No GPU is required; all logic runs efficiently on a standard dual-core CPU.