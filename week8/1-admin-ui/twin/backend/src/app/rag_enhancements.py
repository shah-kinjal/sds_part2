"""
RAG Enhancements Module
Provides query rewriting and reranking capabilities for improved retrieval.
"""

import boto3
import json
import logging
import os
from typing import List, Dict, Any, Optional
from strands.models import BedrockModel

logger = logging.getLogger(__name__)


class QueryRewriter:
    """
    Rewrites user queries to improve retrieval quality.
    Uses an LLM to rephrase queries for better semantic matching.
    """

    def __init__(self, model_id: Optional[str] = None):
        """
        Initialize the query rewriter.

        Args:
            model_id: Bedrock model ID for query rewriting.
                     Defaults to QUERY_REWRITE_MODEL_ID env var or falls back to main model.
        """
        self.model_id = model_id or os.environ.get(
            "QUERY_REWRITE_MODEL_ID",
            os.environ.get("MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
        )
        self.model = BedrockModel(model_id=self.model_id)
        logger.info(f"QueryRewriter initialized with model: {self.model_id}")

    def rewrite(self, query: str, conversation_history: Optional[List[Dict]] = None) -> str:
        """
        Rewrite a query to improve retrieval quality.

        Args:
            query: The original user query
            conversation_history: Optional conversation context for better rewriting

        Returns:
            The rewritten query optimized for semantic search
        """
        logger.info(f"QueryRewriter rewrite cladded with " + query)
        # Build context from conversation history if available
        context = ""
        if conversation_history:
            # Get last 3 messages for context
            recent_messages = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
            for msg in recent_messages:
                role = msg.get("role", "")
                if msg.get("content") and len(msg["content"]) > 0 and "text" in msg["content"][0]:
                    text = msg["content"][0]["text"]
                    context += f"{role}: {text}\n"

        # Create the rewrite prompt
        if context:
            system_prompt = """You are a query optimization expert. Your task is to rewrite user queries to improve semantic search results.
Given a conversation context and a user query, rewrite the query to:
1. Make it more specific and detailed
2. Include relevant context from the conversation
3. Expand abbreviations and clarify ambiguous terms
4. Maintain the original intent
5. keep the size of the query same as the original query.
Return ONLY the rewritten query, nothing else.
"""

            user_prompt = f"""Conversation context:
{context}

Current query: {query}

Rewritten query:"""
        else:
            system_prompt = """You are a query optimization expert. Your task is to rewrite user queries to improve semantic search results.
Rewrite the query to be more specific, detailed, and optimized for semantic search while maintaining the original intent.
Return ONLY the rewritten query, nothing else."""

            user_prompt = f"""Query: {query}

Rewritten query:"""

        try:
            # Use the model to rewrite the query
            messages = [{"role": "user", "content": user_prompt}]

            # For Bedrock models, we need to use the invoke method appropriately
            # The BedrockModel should handle this, but we'll do a simple invocation
            response = self.model.generate(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=200,
                temperature=0.3  # Lower temperature for more focused rewrites
            )

            rewritten_query = response.strip()
            logger.info(f"Original query: '{query}' -> Rewritten: '{rewritten_query}'")
            return rewritten_query

        except Exception as e:
            logger.error(f"Error rewriting query: {str(e)}", exc_info=True)
            # Fall back to original query on error
            return query


class Reranker:
    """
    Reranks retrieved documents to improve relevance.
    Uses Bedrock's Cohere rerank model or a custom LLM-based approach.
    """

    def __init__(self, model_id: Optional[str] = None, method: str = "bedrock"):
        """
        Initialize the reranker.

        Args:
            model_id: Model ID for reranking.
                     For 'bedrock' method: Cohere rerank model (e.g., 'cohere.rerank-v3-5:0')
                     For 'llm' method: Any Bedrock LLM model
            method: Reranking method - 'bedrock' (Cohere) or 'llm' (LLM-based)
        """
        self.method = method or os.environ.get("RERANK_METHOD", "bedrock")

        if self.method == "bedrock":
            self.model_id = model_id or os.environ.get(
                "RERANK_MODEL_ID",
                "cohere.rerank-v3-5:0"
            )
            self.boto_client = boto3.client('bedrock-runtime')
        else:  # llm method
            self.model_id = model_id or os.environ.get(
                "RERANK_MODEL_ID",
                os.environ.get("MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
            )
            self.model = BedrockModel(model_id=self.model_id)

        logger.info(f"Reranker initialized with method: {self.method}, model: {self.model_id}")

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents based on relevance to the query.

        Args:
            query: The search query
            documents: List of retrieved documents with 'content' or 'text' field
            top_k: Number of top documents to return (None = return all, reranked)

        Returns:
            Reranked list of documents with relevance scores
        """
        logger.info(f"Reranker rerank called with " + query)
        if not documents:
            return documents

        try:
            if self.method == "bedrock":
                return self._rerank_with_bedrock(query, documents, top_k)
            else:
                return self._rerank_with_llm(query, documents, top_k)
        except Exception as e:
            logger.error(f"Error reranking documents: {str(e)}", exc_info=True)
            # Fall back to original order on error
            return documents[:top_k] if top_k else documents

    def _rerank_with_bedrock(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Rerank using Bedrock's Cohere rerank model."""
        # Extract text from documents
        doc_texts = []
        for doc in documents:
            text = doc.get('content') or doc.get('text') or doc.get('page_content') or str(doc)
            doc_texts.append(text)

        # Prepare request for Cohere rerank
        request_body = {
            "query": query,
            "documents": doc_texts,
            "top_n": top_k if top_k else len(documents)
        }

        try:
            response = self.boto_client.invoke_model(
                modelId=self.model_id,
                cache_prompt="default",
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )

            response_body = json.loads(response['body'].read())
            results = response_body.get('results', [])

            # Reorder documents based on rerank results
            reranked_docs = []
            for result in results:
                idx = result.get('index')
                score = result.get('relevance_score', 0)
                if idx < len(documents):
                    doc = documents[idx].copy()
                    doc['rerank_score'] = score
                    reranked_docs.append(doc)

            logger.info(f"Reranked {len(reranked_docs)} documents using Bedrock Cohere")
            return reranked_docs

        except Exception as e:
            logger.error(f"Bedrock rerank error: {str(e)}", exc_info=True)
            raise

    def _rerank_with_llm(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Rerank using an LLM to score relevance."""
        scored_docs = []

        for idx, doc in enumerate(documents):
            text = doc.get('content') or doc.get('text') or doc.get('page_content') or str(doc)

            # Truncate very long documents for scoring
            text_preview = text[:500] if len(text) > 500 else text

            system_prompt = """You are a relevance scoring expert. Given a query and a document, score the document's relevance to the query on a scale of 0-10.
Return ONLY a single number between 0 and 10, nothing else."""

            user_prompt = f"""Query: {query}

Document: {text_preview}

Relevance score (0-10):"""

            try:
                messages = [{"role": "user", "content": user_prompt}]
                response = self.model.generate(
                    messages=messages,
                    cache_prompt="default",
                    system_prompt=system_prompt,
                    max_tokens=10,
                    temperature=0.1
                )

                # Parse the score
                score_str = response.strip()
                score = float(score_str)

                doc_copy = doc.copy()
                doc_copy['rerank_score'] = score
                scored_docs.append((score, doc_copy))

            except Exception as e:
                logger.warning(f"Error scoring document {idx}: {str(e)}")
                doc_copy = doc.copy()
                doc_copy['rerank_score'] = 0
                scored_docs.append((0, doc_copy))

        # Sort by score descending
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        # Return top_k documents
        result = [doc for _, doc in scored_docs]
        if top_k:
            result = result[:top_k]

        logger.info(f"Reranked {len(result)} documents using LLM scoring")
        return result


class RAGEnhancer:
    """
    Combines query rewriting and reranking for enhanced RAG pipeline.
    """

    def __init__(
        self,
        enable_query_rewrite: bool = True,
        enable_reranking: bool = True,
        query_rewrite_model_id: Optional[str] = None,
        rerank_model_id: Optional[str] = None,
        rerank_method: str = "bedrock",
        rerank_top_k: Optional[int] = None
    ):
        """
        Initialize the RAG enhancer.

        Args:
            enable_query_rewrite: Whether to enable query rewriting
            enable_reranking: Whether to enable reranking
            query_rewrite_model_id: Model for query rewriting
            rerank_model_id: Model for reranking
            rerank_method: Reranking method ('bedrock' or 'llm')
            rerank_top_k: Number of top documents to return after reranking
        """
        self.enable_query_rewrite = enable_query_rewrite
        self.enable_reranking = enable_reranking
        self.rerank_top_k = rerank_top_k or int(os.environ.get("RERANK_TOP_K", "5"))

        if self.enable_query_rewrite:
            self.query_rewriter = QueryRewriter(model_id=query_rewrite_model_id)

        if self.enable_reranking:
            self.reranker = Reranker(model_id=rerank_model_id, method=rerank_method)

        logger.info(
            f"RAGEnhancer initialized - "
            f"query_rewrite: {enable_query_rewrite}, "
            f"reranking: {enable_reranking}, "
            f"rerank_top_k: {self.rerank_top_k}"
        )

    def enhance_query(
        self,
        query: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Enhance a query through rewriting.

        Args:
            query: Original query
            conversation_history: Optional conversation context

        Returns:
            Enhanced query (rewritten if enabled, otherwise original)
        """
        if self.enable_query_rewrite:
            return self.query_rewriter.rewrite(query, conversation_history)
        return query

    def enhance_results(
        self,
        query: str,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enhance retrieval results through reranking.

        Args:
            query: The search query
            documents: Retrieved documents

        Returns:
            Enhanced documents (reranked if enabled, otherwise original)
        """
        if self.enable_reranking:
            return self.reranker.rerank(query, documents, self.rerank_top_k)
        return documents
