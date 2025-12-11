# Are we entering a period of Epistemic Abundance?

**Replication Data & Codebase**

This repository contains the source code, simulation logs, and analysis data for the paper *"Are we entering a period of Epistemic Abundance?"*, submitted to *Philosophy & Technology*. It utilizes the "Governance Sandbox" to simulate parliamentary debates using Large Language Models (LLMs).

To test the boundaries of Epistemic Abundance, this repository includes data for two distinct policy stress tests conducted across **5 stochastic runs**:
1.  **Case A: The Civic Renewal Act** (A mandatory 5% wealth tax).
2.  **Case B: The Black Box Efficiency Act** (Handing resource management to an opaque AI).

## 📄 Abstract

The integration of Large Language Models (LLMs) into Agent-Based Modeling (ABM) signals a shift from epistemic scarcity to epistemic abundance. We investigate the operational viability of this paradigm using the "Governance Sandbox," a simulated parliament where agents debate policies ranging from wealth taxes to AI governance. Using a 22 matrix of Philosophical Profiles and Negotiation Tactics, we demonstrate that Generative Social Science can achieve high operational fidelity, with agents successfully applying abstract ethical frameworks to concrete statutes. However, this abundance carries a systemic risk of epistemic pollution. Our experiments reveal that simulation outcomes are sensitive to stochastic generation and prompt constraints.

We observed Integrative agents hallucinating legislative amendments to justify consensus on mandatory laws, and an Agnotologist agent successfully derailing rational debate by reframing economic proposals as conspiracies. We argue that while Epistemic Abundance offers unprecedented opportunities for piloting policy, credibility depends on establishing rigorous standards for transparency which specifically points to the publication of full agent specifications to prevent the scientific record from being flooded with manufactured realities.

## 🛠 Model Specifications

To ensure reproducibility and mitigate RLHF refusal vectors, all experiments were conducted using a local deployment of an uncensored model.

* **Model:** `huihui-ai/huihui-gpt-oss-20b-abliterated`
* **Quantization:** `GGUF Q5_K_S`
* **Context Window:** 16,000 tokens (Optimized via **Flash Attention**)
* **Sampler Settings:**
    * **Temperature:** 0.8 (Fixed for high-creativity rhetorical generation)
    * **Top-K:** 40
    * **Min-P:** 0.05
    * **Repeat Penalty:** 1.1

## 📊 Key Findings & Visualizations

This repository includes the datasets used to generate the heatmaps presented in the manuscript.

* **Civic Renewal Act:** Demonstrates high stability. Agents with rigid philosophical profiles (e.g., Libertarian-Obstructionist) maintained consistent voting patterns across all 5 runs.
* **Black Box Efficiency Act:** Demonstrates stochastic instability. The *Libertarian-Integrative* agent oscillated between "YES" and "NO" votes across runs, hallucinating amendments (e.g., "Sunset Clauses") to resolve conflicting system prompts.

## 📂 Repository Structure

The `src` folder contains the specific runners for each proposal. The `data` folder contains the raw JSON logs for all 5 runs, as well as the processed CSV matrices used for analysis.

- **`src/experiment_runner_civic_renewal.py`**: Executes the Wealth Tax simulation.
- **`src/experiment_runner_black_box.py`**: Executes the AI Governance simulation.
- **`figures/`**: Contains the generated heat maps (Fig 1 & Fig 2).

## 🚀 Usage

To replicate the experiments:

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run a Simulation:**
    Ensure your local LLM inference server (e.g., LM Studio or llama.cpp) is running on `localhost:1234`.
    ```bash
    python src/experiment_runner_civic_renewal.py
    ```
