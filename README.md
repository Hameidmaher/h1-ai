# H1-AI

**Assistant Pharmacy** - Next generation pharmacy assistant.

## Features

| Feature | Description |
|---------|-------------|
| Advisory Engine | Fast search (<100ms, no LLM) |
| Agent AI | Independent expert |
| ChatBot | Smart manager (optional) |
| Orchestrator | Never-fail coordinator |
| WhatsApp | 3 modes integration |
| Admin Dashboard | Visual management |
| Config-Driven | Everything from YAML |

## Quick Start

Run these commands:

    make setup
    make ollama-setup
    make seed-data
    make backend-run
    make mobile-run

## Test Users

| User | Password | Role |
|------|----------|------|
| customer1 | customer123 | Customer |
| pharmacist1 | pharma123 | Pharmacist |

## Architecture

User -> ChatBot -> Advisory Engine -> Agent

## License

MIT - see LICENSE
