# Logs & Events RCA Multi-Agent Copilot

A simple production-style Python project for **Root Cause Analysis (RCA)** from uploaded log/event files using:

- **Streamlit** for UI
- **LangGraph** for agent workflow orchestration
- **LangChain** for LLM calls
- **Qwen open-source LLM** served through **vLLM OpenAI-compatible endpoint**

## Folder Structure

```text
RCA/
├── agents/
│   ├── __init__.py
│   ├── agent1.py        # Log ingestion and normalization agent
│   ├── agent2.py        # RCA and category agent using Qwen via vLLM
│   ├── agent3.py        # SOP/remediation agent using Qwen via vLLM
│   └── workflow.py      # LangGraph workflow
├── ui/
│   └── streamlitUI.py   # Streamlit upload and results UI
├── requirements.txt
└── README.md
```

## Workflow

```text
User uploads txt/csv/json/jsonl file
        ↓
Streamlit UI saves temporary file
        ↓
Agent1 parses and normalizes logs/events
        ↓
Agent2 identifies category, root cause, severity, confidence, evidence
        ↓
Agent3 generates SOP, triage steps, remediation, approval requirement
        ↓
UI displays RCA and SOP to user
```

## 1. Create Python Environment

```bash
cd RCA
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
cd RCA
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Start Qwen with vLLM

Start a local vLLM server with Qwen:

```bash
vllm serve Qwen/Qwen2.5-7B-Instruct \
  --dtype bfloat16 \
  --max-model-len 4096 \
  --host 0.0.0.0 \
  --port 8000
```

For AMD ROCm / MI300X, you can use a ROCm-enabled vLLM container if available in your environment:

```bash
docker run --rm -it \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --ipc=host \
  --shm-size 16G \
  -p 8000:8000 \
  vllm/vllm-openai-rocm:latest \
  --model Qwen/Qwen2.5-7B-Instruct \
  --dtype bfloat16 \
  --max-model-len 4096 \
  --host 0.0.0.0 \
  --port 8000
```

## 3. Configure Environment Variables

Optional:

```bash
export VLLM_BASE_URL="http://localhost:8000/v1"
export VLLM_MODEL="Qwen/Qwen2.5-7B-Instruct"
export VLLM_API_KEY="dummy-key"
export LLM_TEMPERATURE="0.1"
export LLM_MAX_TOKENS="800"
```

## 4. Run the UI

```bash
streamlit run ui/streamlitUI.py
```

Then upload a `.txt`, `.log`, `.csv`, `.json`, or `.jsonl` file.

## Expected Output

The UI returns:

- Category: Application / Database / Network / Storage / Compute / Security / Deployment / Unknown
- Root cause
- Confidence
- Severity
- Evidence
- Impacted services
- Recommended next steps
- SOP ID and SOP title
- Triage steps
- Remediation steps
- Human approval requirement
- Validation checks
- Prevention recommendations

## Sample Log Snippet

You can test with a `.txt` file containing:

```text
2026-06-15T10:05:00Z INFO service=payment-api deployment v2.3.7 completed DB_POOL_MAX_CONNECTIONS=20
2026-06-15T10:08:00Z ERROR service=payment-api DBConnectionTimeout endpoint=/api/v1/checkout/pay timeout_ms=3000
2026-06-15T10:09:00Z ERROR service=payment-api status=500 error=DBConnectionTimeout customer_impact=true
2026-06-15T10:10:00Z WARN service=payment-api DB connection pool saturation pool_used_pct=98 max_connections=20
```

Expected RCA should identify a deployment/database configuration issue.

## Notes

- This project uses vLLM's OpenAI-compatible API through `langchain-openai`.
- Agent1 is deterministic Python logic.
- Agent2 and Agent3 are LLM-powered.
- FastAPI is included in requirements but not required for the basic Streamlit workflow.
- For hackathon GPU showcase, run multiple RCA analyses concurrently or extend `workflow.py` with parallel branches.
