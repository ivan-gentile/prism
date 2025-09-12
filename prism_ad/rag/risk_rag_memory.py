# prism_ad/rag/risk_rag_memory.py

import chromadb
from typing import List, Optional
from dataclasses import dataclass
from sentence_transformers import CrossEncoder
import openai
import os

from autogen_core.memory import Memory, MemoryContent, MemoryMimeType

@dataclass
class RiskRAGConfig:
    chroma_base_path: str
    collection_name: str
    embedding_model_name: str = "text-embedding-3-small"  # OpenAI's default embedding model
    cross_encoder_name: str = "cross-encoder/ms-marco-MiniLM-L6-v2"
    k_initial: int = 18
    k_final: int = 8
    min_year: Optional[int] = 2018
    type_filter: Optional[str] = None   # e.g., "text" or "table"
    score_threshold: float = 0.35

class RiskRAGMemory(Memory):
    """
    AutoGen Memory that retrieves and injects Alzheimer’s evidence for the Risk Calculator.
    Indexing is preprocessed; this component only queries an existing ChromaDB collection.
    """

    def __init__(self, config: RiskRAGConfig):
        super().__init__()
        self.config = config
        self._client = chromadb.PersistentClient(path=f"{config.chroma_base_path}/{config.collection_name}")
        self._collection = self._client.get_collection(config.collection_name)
        # Use OpenAI embeddings instead of SentenceTransformers
        self._openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._cross_encoder = CrossEncoder(config.cross_encoder_name)

    async def add(self, content: MemoryContent) -> None:
        """
        No-op: the system relies on preprocessed chunks already loaded into Chroma (scripts 1–3).
        """
        return None

    async def clear(self) -> None:
        # We deliberately do not mutate the persistent DB here.
        return None

    async def close(self) -> None:
        # Nothing special to close for chroma + sbert in this simple case.
        return None

    async def query(self, query_text: str) -> List[MemoryContent]:
        """
        Retrieve top-K relevant chunks (with metadata filters) and rerank with a Cross-Encoder.
        Returns MemoryContent entries that can be appended to the agent's context.
        """
        where_cond = {}
        if self.config.min_year is not None:
            where_cond["year"] = {"$gte": self.config.min_year}
        if self.config.type_filter:
            where_cond["type"] = {"$eq": self.config.type_filter}

        # Use OpenAI embeddings
        embedding_response = self._openai_client.embeddings.create(
            model=self.config.embedding_model_name,
            input=query_text
        )
        qvec = embedding_response.data[0].embedding
        args = {
            "query_embeddings": [qvec],
            "n_results": self.config.k_initial,
            "include": ["documents", "metadatas", "distances"]
        }
        if where_cond:
            args["where"] = where_cond

        results = self._collection.query(**args)
        if not results["documents"]:
            return []

        docs = []
        for i in range(len(results["documents"][0])):
            docs.append({
                "text": results["documents"][0][i],
                "meta": results["metadatas"][0][i],
            })

        # Cross-encoder reranking
        pairs = [(query_text, d["text"]) for d in docs]
        scores = self._cross_encoder.predict(pairs)
        ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)[: self.config.k_final]

        contents: List[MemoryContent] = []
        for d, s in ranked:
            meta = d["meta"]
            doc_title = meta.get("doc_title", "Unknown")
            section = meta.get("section_title", "No Section")
            year = meta.get("year", "Unknown")
            chunk_id = meta.get("chunk_id", "")
            # Short preview
            snippet = d["text"].strip().replace("\n", " ")
            if len(snippet) > 500:
                snippet = snippet[:500] + "..."

            body = (
                f"{snippet}\n"
                f"[source: {doc_title} ({year}); section: {section}; chunk: {chunk_id}; score: {s:.3f}]"
            )
            contents.append(
                MemoryContent(
                    content=body,
                    mime_type=MemoryMimeType.TEXT,
                    metadata={"doc_title": doc_title, "year": year, "section_title": section, "score": float(s)}
                )
            )
        return contents

    async def update_context(self, model_context) -> None:
        """
        Called by AssistantAgent before it reasons. We build a patient-aware query from the task text,
        retrieve evidence, and inject a concise, citable 'EVIDENCE' block as a SystemMessage.
        """
        # Obtain the last task text to derive query signals
        # model_context.get_messages() returns User/System/Assistant messages; we derive a textual query
        try:
            messages = await model_context.get_messages()  # AutoGen returns a list of message objects
            task_text = ""
            for m in messages[::-1]:
                if getattr(m, "type", "").lower() in ("textmessage", "usermessage"):
                    task_text = str(m.content)
                    break
            if not task_text:
                return

            # Build queries (simple heuristic; you can extend with structured PatientData)
            subqueries = [
                "Alzheimer's 5-year progression risk evidence and thresholds",
                "CSF Aβ42 and p-tau thresholds for progression risk",
                "Amyloid PET SUVR threshold MCI to dementia",
                "ApoE4 copies risk multiplier longitudinal progression",
                "Hippocampal atrophy threshold conversion risk",
            ]
            # Blend patient/agent task text to anchor retrieval
            subqueries = [f"{q} | Context: {task_text}" for q in subqueries]

            # Retrieve & pool evidence
            pooled: List[MemoryContent] = []
            seen = set()
            for q in subqueries:
                results = await self.query(q)
                for c in results:
                    key = (c.metadata.get("doc_title"), c.metadata.get("section_title"))
                    if key not in seen:
                        pooled.append(c)
                        seen.add(key)

            if not pooled:
                return

            # Compose a compact system message
            bullets = []
            for c in pooled[: self.config.k_final]:
                meta = c.metadata or {}
                bullets.append(f"• {c.content}")

            evidence_block = (
                "Relevant evidence from Alzheimer’s guidelines/studies (RAG):\n"
                + "\n".join(bullets)
                + "\nUse the above only as evidence; if uncertain, state limitations explicitly."
            )

            # Append as a SystemMessage to the model context
            await model_context.add_system_message(evidence_block)

        except Exception:
            # Be silent on context update failures; do not break the agent
            return
