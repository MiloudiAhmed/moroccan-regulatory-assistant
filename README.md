# Moroccan Regulatory Assistant

An agentic RAG assistant that answers questions about Moroccan regulation (laws, decrees, the Bulletin Officiel, internal circulars) from a corpus of Arabic documents.

## What it does

- Answers questions asked in Arabic, French or Darija, in standard Arabic or French.
- Splits complex questions into sub-questions, searches the corpus, checks that the passages are relevant, and searches again with other words when they are not.
- Backs every claim of the answer with a citation (document, article, page, excerpt), each one checked against the source text.
- Gives a confidence score, and says it doesn't know when the documents available to the user don't cover the question.
- Shows its reasoning live while it works.

## Access and sovereignty

- Three roles: citizens see public law and their own uploads, jurists also see internal documents, administrators manage accounts and never see document content.
- Access rules are enforced inside the search itself, before any document is retrieved.
- Everything runs locally (language models, embeddings, databases); the system works with the internet off.
- An optional web search only ever receives a generic rewording of the question, checked by a filter that blocks any text from internal documents.

## Architecture

| Part | Role |
|---|---|
| Ingestion | Extracts and cleans Arabic text (with OCR for scans) and splits documents by article |
| Retrieval | Hybrid search (vectors + BM25) with re-ranking and the access filter |
| Orchestration | The agent graph: planning, grading, reformulation, web decision |
| Answer | Writes the cited answer, verifies every claim, computes the confidence |
| Identity and access | API, authentication, roles, document rights, audit log |
| Sovereignty | Local models, web isolation, leak filter, Docker setup |
| Interface | Chat, document management and administration screens, right-to-left display |

Details: [`docs/architecture.md`](docs/architecture.md).
