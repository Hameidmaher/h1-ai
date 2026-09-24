.PHONY: help setup backend-install mobile-install ollama-setup seed-data 
        \ backend-run mobile-run backend-test backend-test-cov eval \ 
        v4-test v4-bench v4-demo health lint clean
cd ~/h1-ai PYTHON := python3 BACKEND := backend MOBILE := mobile find . 
-type d -name "__pycache__" -not -path "./node_modules/*" -exec rm -rf 
{} + 2>/dev/null help: find . -type d -name ".pytest_cache" -not -path 
"./node_modules/*" -exec rm -rf {} + 2>/dev/null @echo "🏥 H1-AI — 
Assistant Pharmacy v4.0" find . -type d -name ".ruff_cache" -not -path 
"./node_modules/*" -exec rm -rf {} + 2>/dev/null @echo " make setup - 
Install Backend + Mobile" find . -type d -name ".mypy_cache" -not -path 
"./node_modules/*" -exec rm -rf {} + 2>/dev/null @echo " make 
ollama-setup - Start Ollama + model" echo "تم" @echo " make seed-data - 
Initialize knowledge base"
	@echo "  make backend-run     - Run FastAPI"
	@echo "  make mobile-run      - Run Flutter"
	@echo "  make backend-test    - Run tests"
	@echo "  make eval            - Evaluate Router"
	@echo "  make v4-test         - Test Advisory Engine"
	@echo "  make clean           - Clean temp files"

setup: backend-install mobile-install

backend-install:
	cd $(BACKEND) && $(PYTHON) -m venv .venv && \
	. .venv/bin/activate && pip install --upgrade pip && \
	pip install -r requirements.txt -r requirements-dev.txt
	@echo "✅ Backend installed"

mobile-install:
	cd $(MOBILE) && flutter pub get
	@echo "✅ Mobile installed"

ollama-setup:
	@which ollama > /dev/null || (echo "Ollama not installed" && exit 1)
	@ollama list | grep -q "llama3.1:8b" || ollama pull llama3.1:8b
	@curl -s http://localhost:11434/api/tags > /dev/null || \
		(echo "Starting Ollama..." && (ollama serve > /tmp/ollama.log 2>&1 &) && sleep 3)
	@echo "✅ Ollama ready"

seed-data:
	cd $(BACKEND) && . .venv/bin/activate && python -m scripts.seed_knowledge

backend-run:
	cd $(BACKEND) && . .venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000

mobile-run:
	cd $(MOBILE) && flutter run

backend-test:
	cd $(BACKEND) && . .venv/bin/activate && pytest --no-cov

backend-test-cov:
	cd $(BACKEND) && . .venv/bin/activate && pytest

eval:
	cd $(BACKEND) && . .venv/bin/activate && python -m scripts.evaluate_router

v4-test:
	cd $(BACKEND) && . .venv/bin/activate && pytest tests/knowledge/ -v

v4-bench:
	cd $(BACKEND) && . .venv/bin/activate && python -m scripts.benchmark_engine

v4-demo:
	cd $(BACKEND) && . .venv/bin/activate && python -m scripts.demo_advisory

health:
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "Backend not running"

lint:
	cd $(BACKEND) && . .venv/bin/activate && ruff check . || true
	cd $(MOBILE) && flutter analyze || true

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(BACKEND)/htmlcov $(BACKEND)/.coverage
	cd $(MOBILE) && flutter clean 2>/dev/null || true
