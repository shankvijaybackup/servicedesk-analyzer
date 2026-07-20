# Local AI Setup and Boundaries

Local AI is optional. The deterministic analyzer, reports, grounded executive
summary, pilot selection, metrics, and decisions work without it.

## Supported role

The local model may draft pilot wording from approved aggregate evidence. Its
output is labeled advisory and requires human review.

It cannot:

- Read raw ticket descriptions
- Read requester identities or ticket IDs
- Read source filenames
- Compute or replace metrics
- Classify tickets
- Select the final pilot
- Generate the authoritative executive summary
- Decide `widen`, `correct`, `continue_measuring`, or `stop`

## Install llama.cpp on macOS

```bash
brew install llama.cpp
```

## Start the tested CPU model

```bash
llama-server \
  -hf Qwen/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M \
  --host 127.0.0.1 \
  --port 8080 \
  --ctx-size 4096
```

The first run downloads the model from Qwen's official Hugging Face repository.
No model weights are stored in this Git repository.

## Start the application

```bash
streamlit run sda/app.py
```

In the Local AI tab use:

- Endpoint: `http://127.0.0.1:8080`
- Model: `Qwen/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M`

## Evidence boundary

The provider builds an explicit allowlist containing only:

- Data-quality aggregates
- Overall MTTR aggregates
- The five largest themes
- The five largest opportunity records
- Planning-estimate ranges

Generated citations must resolve to the approved `data_quality`, `mttr`,
`themes`, or `opportunities` evidence roots. Unsupported citations and
incomplete JSON fail closed.

## Model limitation

Live testing showed that the 1.5B model is not reliable enough to rewrite
factual executive summaries. It confused median and p90 values and sometimes
turned planning estimates into observed outcomes. The product therefore uses a
deterministic executive narrative and reserves the model for human-reviewed
pilot wording.

## Availability behavior

If the server is not running, the UI displays an unavailable state. Core
analysis continues normally.
