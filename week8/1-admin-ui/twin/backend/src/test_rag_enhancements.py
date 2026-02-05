"""
Test script for RAG enhancements (query rewriting and reranking)
Run this script to verify the implementation works correctly.
"""

import os
import sys
import logging

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.rag_enhancements import QueryRewriter, Reranker, RAGEnhancer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger(__name__)


def test_query_rewriter():
    """Test the QueryRewriter functionality."""
    print("\n" + "=" * 60)
    print("Testing Query Rewriter")
    print("=" * 60)

    # Set a test model (using Haiku for speed)
    os.environ['QUERY_REWRITE_MODEL_ID'] = 'anthropic.claude-3-haiku-20240307-v1:0'

    try:
        rewriter = QueryRewriter()

        # Test queries
        test_queries = [
            "What did you do?",
            "Tell me about Google",
            "What projects?",
            "Experience with AI?"
        ]

        print("\nRewriting queries without context:")
        for query in test_queries:
            try:
                rewritten = rewriter.rewrite(query)
                print(f"\nOriginal:  {query}")
                print(f"Rewritten: {rewritten}")
            except Exception as e:
                print(f"\nError rewriting '{query}': {str(e)}")

        # Test with conversation context
        print("\n\nRewriting queries with conversation context:")
        conversation_history = [
            {
                "role": "user",
                "content": [{"text": "Tell me about your work at Google"}]
            },
            {
                "role": "assistant",
                "content": [{"text": "I worked at Google as a Senior Software Engineer..."}]
            }
        ]

        query_with_context = "What about the projects?"
        rewritten_with_context = rewriter.rewrite(query_with_context, conversation_history)
        print(f"\nOriginal:  {query_with_context}")
        print(f"Rewritten: {rewritten_with_context}")

        print("\n✅ Query Rewriter test completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Query Rewriter test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_reranker_bedrock():
    """Test the Reranker with Bedrock (Cohere) method."""
    print("\n" + "=" * 60)
    print("Testing Reranker (Bedrock/Cohere Method)")
    print("=" * 60)

    try:
        reranker = Reranker(model_id="cohere.rerank-v3-5:0", method="bedrock")

        query = "machine learning experience"

        # Sample documents
        documents = [
            {"content": "I have experience with traditional software development and databases."},
            {"content": "My work includes machine learning projects using TensorFlow and PyTorch."},
            {"content": "I enjoy cooking and traveling in my free time."},
            {"content": "Deep learning and neural networks are my primary areas of expertise."},
            {"content": "I worked on a project involving natural language processing and transformers."}
        ]

        print(f"\nQuery: {query}")
        print(f"Number of documents: {len(documents)}")

        # Rerank
        reranked = reranker.rerank(query, documents, top_k=3)

        print("\nTop 3 reranked documents:")
        for i, doc in enumerate(reranked, 1):
            score = doc.get('rerank_score', 'N/A')
            content = doc.get('content', '')[:80]
            print(f"{i}. Score: {score:.4f} | {content}...")

        print("\n✅ Reranker (Bedrock) test completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Reranker (Bedrock) test failed: {str(e)}")
        print("This might fail if you don't have access to Cohere models.")
        import traceback
        traceback.print_exc()
        return False


def test_reranker_llm():
    """Test the Reranker with LLM method."""
    print("\n" + "=" * 60)
    print("Testing Reranker (LLM Method)")
    print("=" * 60)

    try:
        reranker = Reranker(
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            method="llm"
        )

        query = "python programming skills"

        # Sample documents
        documents = [
            {"content": "I am proficient in Python with 5 years of experience building web applications."},
            {"content": "My expertise is in JavaScript and React development."},
            {"content": "I have basic knowledge of Python but mainly work with Java."}
        ]

        print(f"\nQuery: {query}")
        print(f"Number of documents: {len(documents)}")

        # Rerank
        reranked = reranker.rerank(query, documents, top_k=3)

        print("\nReranked documents:")
        for i, doc in enumerate(reranked, 1):
            score = doc.get('rerank_score', 'N/A')
            content = doc.get('content', '')[:80]
            print(f"{i}. Score: {score} | {content}...")

        print("\n✅ Reranker (LLM) test completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Reranker (LLM) test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_enhancer():
    """Test the complete RAGEnhancer."""
    print("\n" + "=" * 60)
    print("Testing RAG Enhancer (Complete Pipeline)")
    print("=" * 60)

    try:
        # Set environment for testing
        os.environ['ENABLE_QUERY_REWRITE'] = 'true'
        os.environ['ENABLE_RERANKING'] = 'true'
        os.environ['RERANK_METHOD'] = 'llm'  # Use LLM method for broader compatibility
        os.environ['RERANK_TOP_K'] = '3'

        enhancer = RAGEnhancer(
            enable_query_rewrite=True,
            enable_reranking=True,
            query_rewrite_model_id="anthropic.claude-3-haiku-20240307-v1:0",
            rerank_model_id="anthropic.claude-3-haiku-20240307-v1:0",
            rerank_method="llm",
            rerank_top_k=3
        )

        # Test query enhancement
        query = "What did you do?"
        enhanced_query = enhancer.enhance_query(query)
        print(f"\nQuery Enhancement:")
        print(f"Original:  {query}")
        print(f"Enhanced:  {enhanced_query}")

        # Test result enhancement (reranking)
        documents = [
            {"content": "I led a team of 10 engineers building cloud infrastructure."},
            {"content": "In my spare time, I enjoy hiking and photography."},
            {"content": "My primary role involved architecting scalable systems using AWS and Kubernetes."}
        ]

        enhanced_results = enhancer.enhance_results(enhanced_query, documents)
        print(f"\nResult Enhancement (Reranking):")
        for i, doc in enumerate(enhanced_results, 1):
            score = doc.get('rerank_score', 'N/A')
            content = doc.get('content', '')[:60]
            print(f"{i}. Score: {score} | {content}...")

        print("\n✅ RAG Enhancer test completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ RAG Enhancer test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("RAG Enhancements Test Suite")
    print("=" * 60)

    # Make sure we have the required environment variable
    if not os.environ.get('MODEL_ID'):
        os.environ['MODEL_ID'] = 'anthropic.claude-3-haiku-20240307-v1:0'

    results = []

    # Run tests
    results.append(("Query Rewriter", test_query_rewriter()))
    results.append(("Reranker (Bedrock)", test_reranker_bedrock()))
    results.append(("Reranker (LLM)", test_reranker_llm()))
    results.append(("RAG Enhancer", test_rag_enhancer()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    print(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
