<!-- this file tells,If someone else runs my code, what do they need, how long will it take, and why might results still differ a little -->

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


<!-- Reproducibility Statement

This document explains how this project can be run again under similar conditions and why small differences in results may still occur. It is written to be understandable for beginners while remaining suitable for technical and academic review.

Execution Environment

This project was tested in two environments:

Hugging Face Spaces using a CPU-only (Basic) setup

A local Windows 11 machine

No GPU is required. The application uses less than 2GB of RAM because all large language model (LLM) inference is performed through external APIs rather than on local hardware. As a result, the system runs efficiently on standard consumer-grade CPUs.

Network and External Dependencies

A stable internet connection is required for correct operation. The application relies on third-party services for core functionality:

Groq is used for large language model inference.

SerpApi is used to retrieve real-time flight, hotel, and travel-related search data.

Offline execution is not supported due to these external dependencies.

Runtime Characteristics

The system exhibits a short initialization delay when starting for the first time:

Cold start time is approximately 15 seconds, during which the runtime environment and tools are loaded.

Once running:

Generating a complete travel itinerary for 3–5 days typically takes 20–40 seconds.

Runtime may vary depending on internet speed and third-party API response latency.

These delays are expected and normal for API-driven applications.

Determinism and Randomness Control

To improve reproducibility and reduce output variation:

The language model temperature is fixed at 0.1, which limits creative randomness and encourages consistent responses.

A fixed random seed (random.seed(42)) is applied wherever random operations are used, such as ordering synthetic or intermediate data.

These measures help ensure that repeated runs produce similar outputs under identical conditions.

Known Sources of Nondeterminism

Despite these controls, complete determinism cannot be guaranteed:

Travel data retrieved from SerpApi reflects live availability and may change daily.

Large language models may introduce minor variations in wording or formatting, even with low temperature settings.

Such variations are expected and do not indicate errors in the system.

Cost and Resource Considerations

The project operates entirely within the free usage tiers of Groq and SerpApi at the time of testing. No paid APIs, GPUs, or specialized infrastructure are required. All application logic runs efficiently on a standard dual-core CPU environment. -->