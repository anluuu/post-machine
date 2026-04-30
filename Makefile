NAMESPACE   := posts-agent
API_IMAGE   := posts-api:local
UI_IMAGE    := posts-ui:local

.PHONY: build build-api build-ui \
        deploy deploy-langfuse forward-langfuse forward-api \
        logs-api logs-ui \
        clean clean-langfuse \
        dev

# ─── Build ────────────────────────────────────────────────────────────────────

build: build-api build-ui

build-api:
	docker build -t $(API_IMAGE) .

build-ui:
	docker build -t $(UI_IMAGE) ui/

# ─── Deploy ───────────────────────────────────────────────────────────────────

# Deploy Langfuse via Helm (first time only — use upgrade after)
deploy-langfuse:
	helm repo add langfuse https://langfuse.github.io/langfuse-k8s 2>/dev/null || true
	helm repo update
	helm upgrade --install langfuse langfuse/langfuse \
	  -n langfuse --create-namespace \
	  -f k8s/langfuse-values.yaml \
	  --wait --timeout 5m

# Deploy API + UI
deploy:
	kubectl apply -f k8s/00-namespace.yaml
	kubectl apply -f k8s/01-volumes.yaml
	kubectl apply -f k8s/02-secrets.yaml
	kubectl apply -f k8s/03-api.yaml
	kubectl apply -f k8s/04-ui.yaml
	kubectl rollout restart deployment/api deployment/ui -n $(NAMESPACE)

# ─── Port-forward (for local k8s without LoadBalancer) ────────────────────────

# UI already uses NodePort 30080 — open http://localhost:30080
# For Langfuse, forward port 3000 → localhost:30100
forward-langfuse:
	kubectl port-forward -n langfuse svc/langfuse-web 30100:3000

# Forward API directly (useful for debugging without the UI)
forward-api:
	kubectl port-forward -n $(NAMESPACE) svc/api 8000:8000

# ─── Logs ─────────────────────────────────────────────────────────────────────

logs-api:
	kubectl logs -n $(NAMESPACE) -l app=api -f

logs-ui:
	kubectl logs -n $(NAMESPACE) -l app=ui -f

# ─── Local dev (no k8s) ───────────────────────────────────────────────────────

# Runs API + UI locally. Requires two terminals or use & with cleanup.
dev:
	@echo "Start API:  uv run uvicorn agent.api:app --reload --port 8000"
	@echo "Start UI:   cd ui && npm run dev"
	@echo "Open:       http://localhost:5173"

# ─── Cleanup ──────────────────────────────────────────────────────────────────

clean:
	kubectl delete -f k8s/04-ui.yaml --ignore-not-found
	kubectl delete -f k8s/03-api.yaml --ignore-not-found
	kubectl delete -f k8s/02-secrets.yaml --ignore-not-found
	kubectl delete -f k8s/01-volumes.yaml --ignore-not-found

clean-langfuse:
	helm uninstall langfuse -n langfuse --ignore-not-found
