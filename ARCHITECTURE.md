# LinkedIn Post Agent Architecture

This document visualizes the execution flow of the agentic pipeline built with LangGraph.

## Workflow Diagram

```mermaid
flowchart TD
    Start((START)) --> Persona[PersonaLoader<br/><i>Reads persona.md + Caches Summary</i>]
    
    subgraph Research [Topic & Intel]
        Persona --> Researcher[TopicResearcher<br/><i>Scans existing posts + Web Search</i>]
    end

    Researcher --> Writer[PostWriter<br/><i>Drafts post in Wagner's voice</i>]
    
    Writer --> QA[QAReviewer<br/><i>Scores 1-10 + Actionable Feedback</i>]

    subgraph Loop [Quality Gate]
        QA --> Decision{Score >= Threshold<br/>OR Max Retries?}
        Decision -- No --> Refiner[PostRefiner<br/><i>Fixes issues from feedback</i>]
        Refiner --> QA
    end

    Decision -- Yes --> Saver[PostSaver<br/><i>Writes final .md file</i>]
    Saver --> End((END))

    %% Styling
    style Research fill:#f5f5f5,stroke:#333,stroke-width:1px
    style Loop fill:#f0f7ff,stroke:#0056b3,stroke-width:1px
    style Start fill:#d4edda,stroke:#28a745
    style End fill:#f8d7da,stroke:#dc3545
    style Decision fill:#fff3cd,stroke:#856404
```

## Component Details

- **PersonaLoader:** Analyzes the `persona.md` to extract a consistent voice and technical expertise. Results are cached in `.persona_cache.json` to reduce LLM latency.
- **TopicResearcher:** Evaluates the `config.yaml` queries against existing `.md` files in the output directory to ensure topic variety. Performs a DuckDuckGo search for current trends.
- **PostWriter:** Synthesizes research and persona into a Markdown post.
- **QAReviewer:** A structured output node that evaluates the post against Wagner's specific style rules and a quality threshold.
- **PostRefiner:** Iteratively improves the post based on specific reviewer feedback.
- **PostSaver:** Finalizes the publication by saving the markdown file and running any configured post-save hooks.
