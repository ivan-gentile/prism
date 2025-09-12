# FastWeb Integration for PRISM-AD System

## Overview

This document describes the FastWeb model integration into the PRISM-AD multi-agent system for the hackathon. The integration allows seamless switching between OpenAI and FastWeb models for different agents, enabling performance benchmarking and cost optimization.

## Architecture

### Multi-Provider Support

The system now supports multiple LLM providers through a flexible abstraction layer:

```
┌─────────────────┐
│   PRISM-AD      │
│  Agent System   │
└────────┬────────┘
         │
┌────────▼────────┐
│ Provider Factory│
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│OpenAI │ │FastWeb│
└───────┘ └───────┘
```

### Agent Provider Mapping

Each agent can be configured to use either OpenAI or FastWeb models:

| Agent | Default Provider | FastWeb Compatible | Notes |
|-------|-----------------|-------------------|-------|
| Parser | OpenAI | ✅ Yes | Can use FastWeb |
| Validator | OpenAI | ✅ Yes | Can use FastWeb |
| Classifier | FastWeb* | ✅ Yes | Uses FastWeb when enabled |
| Quant Model | OpenAI | ❌ No | Requires tool/function calling |
| Risk Calculator | FastWeb* | ✅ Yes | Uses FastWeb when enabled |
| Reporter | OpenAI | ✅ Yes | Can use FastWeb |

*When `FASTWEB_ENABLED=true`

## Configuration

### 1. Environment Setup

Copy the example environment file and configure your API keys:

```bash
cp env.example .env
```

Edit `.env` and add your credentials:

```env
# Enable FastWeb integration
FASTWEB_ENABLED=true

# FastWeb API credentials
FASTWEB_API_KEY=your_fastweb_api_key_here
FASTWEB_BASE_URL=https://api.ai-fastweb.it/v1
FASTWEB_MODEL=Llama-3.3-70B-Instruct

# OpenAI credentials (still required for some agents)
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Available FastWeb Models

Based on the FastWeb API documentation, the following models are available:
- `Llama-3.3-70B-Instruct` (default)
- Other models as specified in the FastWeb documentation

### 3. Custom Agent Mapping

You can override which provider each agent uses by modifying `prism_ad/config.py`:

```python
AGENT_MODEL_MAP = {
    "parser": "fastweb",  # Change to use FastWeb
    "validator": "primary",  # Keep using OpenAI
    "classifier": "fastweb",
    # ... etc
}
```

## Usage

### Running with FastWeb Integration

1. **Basic Usage**:
```python
from prism_ad.agents.prism_agents import PRISMAgentSystem

# System automatically uses configured providers
system = PRISMAgentSystem()
await system.initialize_agents()

# Process patient data
result = await system.process_patient(clinical_text)
```

2. **Testing FastWeb Integration**:
```bash
# Activate virtual environment
./prism_env/Scripts/activate  # Windows
# or
source prism_env/bin/activate  # Linux/Mac

# Run test suite
python prism_ad/test_fastweb_integration.py
```

3. **Benchmarking**:
The test script automatically generates benchmark reports comparing:
- Response times for each agent
- Overall pipeline performance
- Provider-specific metrics

### Benchmark Output

The system generates two types of reports:

1. **Benchmark Report** (`benchmark_fastweb_TIMESTAMP.json`):
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "fastweb_enabled": true,
  "agent_timings": {
    "parser": 1.2,
    "classifier": 0.8,
    ...
  },
  "agent_providers": {
    "parser": {
      "provider": "OpenAI",
      "model": "gpt-4o-mini",
      "time": 1.2
    },
    "classifier": {
      "provider": "FastWeb",
      "model": "Llama-3.3-70B-Instruct",
      "time": 0.8
    }
  }
}
```

2. **Clinical Report** (`clinical_report_fastweb_TIMESTAMP.json`):
Contains the full clinical analysis results.

## API Compatibility

FastWeb uses an OpenAI-compatible API format, which means:

### ✅ Supported Features
- Chat completions (`/v1/chat/completions`)
- System and user messages
- Temperature control
- Standard response format

### ⚠️ Limitations
- **Function/Tool Calling**: May not be supported (verify with FastWeb docs)
- **Embeddings**: Use OpenAI for RAG embeddings
- **Streaming**: Verify support with FastWeb documentation

## Performance Considerations

### Optimization Tips

1. **Agent Assignment**:
   - Use FastWeb for classification and aggregation tasks
   - Keep OpenAI for tool-calling agents (quant_model)
   - Balance based on latency requirements

2. **Batch Processing**:
   - Group similar requests to the same provider
   - Minimize provider switching overhead

3. **Caching**:
   - The system caches model clients per agent
   - Reuse system instances for multiple patients

### Expected Performance Gains

Based on the provider characteristics:
- **FastWeb**: Lower latency for inference-only tasks
- **OpenAI**: Better for complex reasoning and tool use
- **Hybrid**: Optimal balance of speed and capability

## Troubleshooting

### Common Issues

1. **FastWeb API Key Not Working**:
```python
# Check configuration
from prism_ad.config import PROVIDER_CONFIGS
print(PROVIDER_CONFIGS["fastweb"])
```

2. **Agent Using Wrong Provider**:
```python
# Verify agent mapping
from prism_ad.config import AGENT_MODEL_MAP
print(AGENT_MODEL_MAP)
```

3. **Connection Errors**:
- Verify `FASTWEB_BASE_URL` is correct
- Check API key permissions
- Ensure network connectivity

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run system to see provider assignments
system = PRISMAgentSystem()
await system.initialize_agents()
```

## Hackathon Submission Notes

### Key Features for Judges

1. **Seamless Integration**: Drop-in replacement for OpenAI models
2. **Flexible Configuration**: Per-agent provider selection
3. **Comprehensive Benchmarking**: Automated performance comparison
4. **Production Ready**: Error handling and fallback mechanisms
5. **Cost Optimization**: Use FastWeb for suitable tasks, OpenAI for complex ones

### Benchmark Metrics to Highlight

- **Latency Reduction**: Show % improvement with FastWeb
- **Cost Savings**: Calculate based on token usage
- **Throughput**: Requests per second comparison
- **Quality Metrics**: Maintain output quality across providers

### Demo Script

```python
# Quick demo for hackathon presentation
async def demo_fastweb():
    print("🚀 PRISM-AD with FastWeb Integration Demo")
    
    # Show configuration
    print(f"FastWeb Enabled: {FASTWEB_ENABLED}")
    
    # Initialize system
    system = PRISMAgentSystem()
    await system.initialize_agents()
    
    # Process sample patient
    result = await system.process_patient(sample_clinical_text)
    
    # Show results and timing
    print(f"✅ Processing complete!")
    print(f"⚡ FastWeb agents: classifier, risk_calculator")
    print(f"🎯 OpenAI agents: parser, validator, quant_model, reporter")
    
    await system.close()
```

## Future Enhancements

1. **Dynamic Provider Switching**: Based on load and availability
2. **Fallback Mechanisms**: Automatic failover between providers
3. **Advanced Benchmarking**: A/B testing framework
4. **Model-Specific Prompts**: Optimize prompts per provider
5. **Cost Tracking**: Real-time cost monitoring per provider

## Support

For questions about the FastWeb integration:
1. Check this documentation
2. Review test output from `test_fastweb_integration.py`
3. Check provider status in system initialization logs

## License

This integration maintains compatibility with the existing PRISM-AD license while incorporating FastWeb's API terms of service.
