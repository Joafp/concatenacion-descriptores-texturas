# AI Disclosure Statement

This thesis used AI-assisted tools during its development:

- **Claude Code (Anthropic, MiniMax-M3 model)** was used as a coding assistant for:
  - Implementation of feature extraction pipelines (Python scripts in `src/`)
  - Implementation of baseline and progressive concatenation experiments
  - Implementation of analysis and figure generation scripts
  - Debugging of installation issues (HuggingFace, timm, classical descriptors)
  - Generation of boilerplate for experimental infrastructure (configuration, logging)

- **Deep Research skill (multi-agent web search)** was used once to verify the state-of-the-art of visual feature extractors as of June 2026, with adversarial verification of 25 claims (6 confirmed, 19 refuted).

**Scope of AI assistance:**
- Code: implementation and debugging only. All design decisions (which models to compare, which datasets, which evaluation protocol) were made by the author.
- Experiments: the author designed the experimental protocol; the AI helped with implementation and orchestration.
- Writing: the AI was used to assist with the drafting of Cap. 4-6. The author reviewed and is responsible for all scientific content, claims, and interpretations.
- AI did not generate any empirical results. All numbers in tables and figures come from the experiments run by the author.

**The author takes full responsibility for:**
- The selection of the 10 extractors, 5 datasets, and 3 classifiers.
- The choice of evaluation protocol (5-fold CV, macro-F1 as primary metric, L2 normalization before concat).
- The scientific interpretation of results in Chapters 4-6.
- All limitations and future work declarations.

Date: 2026-06-05
Author: [Author Name]
