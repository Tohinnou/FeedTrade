# FeedTrade — Roadmap IA / LLM

> Verdict + plan structuré établi le 2026-05-04.
> Élève : William.Z (dev backend, licence maths, freelance IA en préparation).
> Posture pédagogique : prof intransigeant, pas sentimental, références concrètes.

---

## VERDICT — État actuel du projet

### Points forts (à conserver)
- Architecture clean / hexagonale (ports & adapters) — domain / application / infrastructure / api correctement séparés.
- Async partout (FastAPI, aiohttp, SQLAlchemy async).
- Patterns production : circuit breaker, semaphore (max_concurrent), cache LRU.
- DI via classe `Container` (même si imparfaite, l'intention est là).
- Pipeline sentiment fonctionnel : RSS → LLM → JSON pair/sentiment/reason.

### A. CRITIQUE — à corriger avant tout

#### A1. Pas de tests
- Les fichiers `test_rag_*.py` à la racine sont des scripts d'exploration, pas des tests.
- Aucun `pytest`, aucune assertion, aucun mock du LLM ou du repo.
- **Action** : `tests/` avec `pytest`, `pytest-asyncio`, fixtures pour `LLMClient` (mock), `respx` pour mocker HTTP. Coverage cible ≥ 70 % sur `domain/` et `application/`.

#### A2. Pas de mesure du RAG
- Aucun dataset d'évaluation, aucune métrique (faithfulness, context precision, answer relevancy).
- **Règle absolue** : on n'améliore pas ce qu'on ne mesure pas.
- **Action** : intégrer **Ragas** (https://github.com/explodinggradients/ragas) + golden set de 30-50 questions Forex avec réponses validées.

#### A3. Data leakage sémantique dans les embeddings
- `test_rag_retrieval.py:28-34` indexe `Title + Sentiment + Pair + Reason` ensemble.
- Mettre le label dans le doc encodé → recherche sémantique = keyword search déguisé.
- **Action** :
  - Encoder uniquement `title + summary` (la sémantique vraie de la news).
  - Stocker `pair`, `sentiment`, `source`, `published` en **metadata** Chroma → utiliser en `where` filter au query time.
  - Pour "which pairs are bullish?" : `where={"sentiment": "BULLISH"}` puis tri par recency, pas du retrieval sémantique.

#### A4. `AskRAG()` instancié dans `register_routes`
- `src/api/routes.py:60` casse l'archi hexagonale.
- Import en milieu de fonction (ligne 59) = dette technique immédiate.
- **Action** :
  - `AskRAG` rejoint `Container.deps`.
  - `EmbeddingClient` et `VectorStore` deviennent des interfaces `domain/interfaces/`.
  - Implémentations dans `infrastructure/embeddings/` et `infrastructure/vectorstore/`.

#### A5. Container muté après init
- `main.py:34-36` mute `container.deps["repo"]` et `container._get_sentiment.repo` post-construction.
- C'est exactement ce que la DI sert à éviter.
- **Action** : factory `async def build(app)` qui ouvre la session **dans** le lifespan, construit tout, retourne `deps`. Pas de mutation post-init.

#### A6. Pas de migrations DB
- `main.py:28` utilise `Base.metadata.create_all` — bombe à retardement en prod.
- **Action** : **Alembic**, dès maintenant. `alembic init` + 1ʳᵉ migration baseline.

### B. IMPORTANT — limite supérieure sans ces points

#### B1. Modèle d'embedding mal choisi
- `all-MiniLM-L6-v2` = baseline généraliste 2021. Plafonne sur du financial English.
- Alternatives à benchmarker :
  | Modèle | Pourquoi |
  |---|---|
  | `BAAI/bge-base-en-v1.5` | Top du MTEB pour sa taille |
  | `BAAI/bge-m3` | Multilingue + dense + sparse + colbert |
  | `intfloat/e5-large-v2` | Excellent retrieval général |
  | `nomic-embed-text-v1.5` | 768d, contexte 8k |
- **Action** : benchmarker 3 modèles sur le golden set Ragas, choix justifié par les chiffres.

#### B2. Pas de re-ranking
- Top-k cosine = retrieval naïf.
- **Action** : ajouter `cross-encoder/ms-marco-MiniLM-L-6-v2` — bi-encoder retrieve top 20-50, cross-encoder rerank top 5. Gain typique : +10-20 points sur les métriques.

#### B3. Pas de hybrid search
- Dense seul rate les noms propres et tickers (EUR/USD, GBP).
- **Action** : combiner BM25 (`rank_bm25`) ou migrer vers **Qdrant** (https://github.com/qdrant/qdrant) qui supporte hybrid natif.

#### B4. Output structuré fragile
- `groq_client.py:127-145` : regex + `json.loads` + `re.sub` pour patcher virgules trailing = rustine.
- **Action** : **Instructor** (https://github.com/jxnl/instructor) — Pydantic `Sentiment` injecté avec retry auto. Ou **Outlines** pour grammar-constrained generation.

#### B5. Pas d'observabilité IA
- Pas de tracing prompts/réponses/tokens/latence/coûts.
- **Action** : **Phoenix Arize** (https://github.com/Arize-ai/phoenix) gratuit local OU **Langfuse** (https://github.com/langfuse/langfuse) self-hosted.

#### B6. Roadmap fine-tuning prématurée
- 50-100 exemples = sous-fitting garanti.
- Hiérarchie correcte AVANT fine-tune :
  1. Prompt engineering rigoureux (system, few-shot, CoT)
  2. RAG amélioré (retrieval + rerank + hybrid)
  3. **DSPy** — optimisation automatique de prompts (https://github.com/stanfordnlp/dspy)
  4. Distillation (gros modèle → petit) avec 1k+ exemples synthétiques
  5. **Puis seulement** LoRA fine-tuning si métriques le justifient
- **Action** : raye le fine-tuning de la semaine 4. Reviens-y semaine 11+ si Ragas montre un plafond.

### C. Hygiène (moins grave)

- `circuit_breaker` utilise `asyncio.get_event_loop().time()` (deprecated 3.10+) → utiliser `asyncio.get_running_loop().time()` ou `time.monotonic()`.
- Pas de `ruff` / `mypy` / `pre-commit` — honteux pour un dev backend confirmé.
- `requirements.txt` non vu → passer à `pyproject.toml` + `uv` (https://github.com/astral-sh/uv) ou `poetry`.
- `ask_rag.py:13` charge `SentenceTransformer` à chaque instanciation → singleton.
- Pas de rate limiter sur `/ask` — un user peut griller le quota Groq en 30 secondes (`slowapi`).
- Pas de mécanisme de feedback utilisateur (signaler une réponse fausse).

---

## PLAN STRUCTURÉ — 12 semaines

### Semaine 0 (immédiat) — Stop the bleeding
- [ ] Suite de tests `pytest` sur `domain/` et `application/` (mocks LLM/repo). Cible : 70 % coverage.
- [ ] `ruff` + `mypy --strict` + `pre-commit` configurés et **passing**.
- [ ] Alembic + 1ʳᵉ migration baseline.
- [ ] `pyproject.toml` avec `uv` ou `poetry`.
- [ ] Refactor `Container` : suppression des mutations post-init, `AskRAG` injecté proprement.
- **Livrable** : CI GitHub Actions verte sur `main`.

### Semaine 1 — RAG : fondations propres
- Lecture obligatoire :
  - "Building RAG-based LLM Applications for Production" — Anyscale (https://www.anyscale.com/blog/a-comprehensive-guide-for-building-rag-based-llm-applications-part-1)
  - **Anthropic cookbook** RAG : https://github.com/anthropics/anthropic-cookbook/tree/main/skills/retrieval_augmented_generation
- Indexation **uniquement** `title + summary`, metadata pour `pair/sentiment/source/published`.
- `EmbeddingClient` interface `domain/`, implémentation `SentenceTransformersEmbedder` `infrastructure/`.
- `VectorStore` interface (`upsert`, `query`, `delete`).
- **Livrable** : `/ask` qui utilise filter metadata correctement.

### Semaine 2 — Évaluation Ragas
- Lecture : doc Ragas + paper "RAGAS: Automated Evaluation of Retrieval Augmented Generation" (https://arxiv.org/abs/2309.15217).
- **Golden set** : 30 questions / réponses validées manuellement (tu connais le Forex).
- Pipeline d'éval : `pytest` + Ragas → JSON résultats versionnés.
- Benchmarks : `all-MiniLM-L6-v2` vs `bge-base-en-v1.5` vs `bge-m3`.
- **Livrable** : tableau `faithfulness / context_precision / answer_relevancy` pour 3 embedders, choix justifié.

### Semaine 3 — Retrieval avancé
- Hybrid search : dense + BM25 (`rank_bm25`) ou migration **Qdrant** (`docker run -p 6333:6333 qdrant/qdrant`).
- Reranker : `cross-encoder/ms-marco-MiniLM-L-6-v2`. Top-50 → top-5.
- Multi-query expansion : LLM réécrit la question en 3 variantes, retrieve les 3, dedup.
- **Livrable** : Ragas en hausse de ≥ 15 % vs semaine 2.

### Semaine 4 — Structured output & prompt engineering
- Migration **Instructor** : `Sentiment` Pydantic injecté, retry auto, plus de regex.
- Lecture : Anthropic Prompt Engineering tutorial (https://github.com/anthropics/courses/tree/master/prompt_engineering_interactive_tutorial) — **fait-le en entier**.
- Prompt RAG amélioré : few-shot, "if context insufficient → say so", citations forcées.
- A/B test deux prompts sur Ragas.
- **Livrable** : taux de `PARSE_ERR` à zéro + scores Ragas en hausse.

### Semaine 5 — Observabilité
- Phoenix ou Langfuse self-hosted, intégré dans `GroqClient`, `OllamaClient`, `AskRAG`.
- Tracing complet : prompt → retrieval docs → réponse → tokens → latence → coût.
- Dashboard interne sur `/admin/traces`.
- **Livrable** : capture d'écran d'un trace complet d'un appel `/ask`.

### Semaine 6 — Agents avec LangGraph
- Lecture : LangGraph academy (https://academy.langchain.com/courses/intro-to-langgraph) — **gratuit**.
- Graphe :
  ```
  question → router → [direct_answer | rag | fetch_fresh_news | refuse]
  ```
- Tool calling natif Groq (`tools=[...]`). Pas de LangChain agent legacy.
- État conversationnel : memory par session.
- **Livrable** : `/chat` multi-tour, mémoire courte, choix d'outil visible dans la trace.

### Semaine 7 — DSPy
- Lecture : DSPy intro (https://dspy.ai/learn/) + paper "DSPy" (https://arxiv.org/abs/2310.03714).
- Convertir le RAG en `dspy.Module` (Signature + ChainOfThought + Retrieve).
- Compilation **BootstrapFewShot** sur le golden set → DSPy choisit les meilleurs few-shots automatiquement.
- **Livrable** : RAG DSPy battant le RAG manuel sur Ragas.

### Semaine 8 — Production patterns
- **Redis** au lieu de LRU in-memory (cache partagé multi-worker).
- **Celery** ou **arq** pour ingestion RSS périodique (worker + beat).
- Streaming SSE sur `/ask` (Groq supporte le stream).
- Rate limiting `slowapi`.
- Cost tracking par user.
- **Livrable** : Docker Compose complet (api + worker + redis + qdrant + phoenix).

### Semaines 9-10 — Fundamentals (en parallèle)
Avantage licence maths à exploiter. Non optionnel pour freelance IA crédible :

1. **Andrej Karpathy — Neural Networks: Zero to Hero** (https://github.com/karpathy/nn-zero-to-hero) — 8 vidéos avec notebooks. **Non négociable.** À la fin tu auras codé GPT from scratch.
2. **Hugging Face NLP course** (https://huggingface.co/learn/nlp-course) — chapitres 1-7.
3. **Smol Course** (https://github.com/huggingface/smol-course) — 5h, fine-tuning et alignment.

### Semaine 11 — Fine-tuning (légitime maintenant)
- **Si et seulement si** Ragas montre un plafond clair après prompt + DSPy.
- Génération de **1000+ exemples synthétiques** via Groq llama-3.3-70b ou Claude Sonnet (qualité supérieure).
- LoRA avec **unsloth** (https://github.com/unslothai/unsloth) — 2-5× plus rapide que HF natif sur petit GPU.
- Eval : modèle fine-tuné vs baseline Groq sur Ragas.
- **Livrable** : modèle déployé, scores comparés.

### Semaine 12 — Portfolio freelance
- README impeccable avec architecture diagram (Mermaid).
- Demo live (Render, Fly.io, ou VPS).
- Article LinkedIn / blog : "Construire un RAG financier production-ready : eval-driven, hybrid search, agents".
- Code public sur GitHub avec tests verts, CI, docs.
- **Livrable** : premier asset freelance crédible.

---

## Ressources à bookmarker

### Repos GitHub à étudier (lire le code, pas juste le README)
- https://github.com/karpathy/nn-zero-to-hero — fondations
- https://github.com/run-llama/llama_index — patterns RAG production
- https://github.com/langchain-ai/langgraph — orchestration agents
- https://github.com/stanfordnlp/dspy — optimisation prompts
- https://github.com/explodinggradients/ragas — eval RAG
- https://github.com/jxnl/instructor — structured output
- https://github.com/Arize-ai/phoenix — observabilité
- https://github.com/qdrant/qdrant — vector DB prod
- https://github.com/BerriAI/litellm — multi-provider routing
- https://github.com/unslothai/unsloth — fine-tuning LoRA rapide
- https://github.com/anthropics/anthropic-cookbook — patterns Anthropic
- https://github.com/openai/openai-cookbook — patterns OpenAI

### Cours / tutoriels gratuits (par ordre de priorité)
1. Karpathy "Zero to Hero" — fondations transformer
2. Anthropic prompt engineering interactive tutorial — prompt rigoureux
3. LangChain Academy "Intro to LangGraph" — agents
4. HuggingFace NLP Course — généraliste
5. DeepLearning.AI — courses Andrew Ng courtes (1-2h chacune)

### Papers à lire (1h chacun, dans l'ordre)
1. "Attention Is All You Need" — Vaswani 2017
2. "Retrieval-Augmented Generation for Knowledge-Intensive NLP" — Lewis 2020
3. "RAGAS" — Es 2023
4. "DSPy" — Khattab 2023
5. "Self-RAG" — Asai 2023

---

## Règles non négociables

1. **Eval-first.** Pas un changement sans avant/après mesuré.
2. **Un concept = un commit avec test.** Si tu peux pas le tester, t'as pas compris.
3. **Pas de fine-tuning avant que prompt + RAG soient optimaux.**
4. **Pas d'abstraction LangChain inutile.** Connais les primitives (embedding → vector store → LLM call) avant les frameworks.
5. **Lire le code des libs utilisées.** ChromaDB, sentence-transformers, Groq SDK : pouvoir expliquer en 3 phrases comment chacun marche.
6. **Forex = ton domaine, exploite-le.** En freelance, le moat c'est IA + domaine, pas IA générale. Tu as les deux.

---

## Action concrète — prochaine session

1. Branche `chore/foundations`.
2. `uv add --dev pytest pytest-asyncio respx ruff mypy pre-commit` (ou poetry/pip équivalent).
3. Premier test : `tests/application/test_get_sentiment.py` avec mock `LLMClient` + `RSSFetcher`. Vérifier que `GetSentiment.execute()` retourne `AnalysisResult` avec `total_analyzed == nombre de sentiments valides`.
4. Quand il passe → push → on enchaîne sur le suivant.

Pas de saut d'étape. L'apprentissage théorique (semaines 9-10) se fait **en parallèle**, pas avant. Maintenant on construit.
