import asyncio
import json
from httpx import AsyncClient
from typing import List, Dict
import sys

API_BASE_URL = "http://localhost:8000"
API_KEY = "dev-secret-key"

async def load_eval_set() -> List[Dict]:
    """Load evaluation questions."""
    with open("eval/eval_set.json", "r") as f:
        data = json.load(f)
    return data["evaluation_set"]

async def run_evaluation():
    """Run evaluation against the API."""
    print("Loading evaluation set...")
    eval_questions = await load_eval_set()
    
    results = []
    
    async with AsyncClient(base_url=API_BASE_URL) as client:
        for item in eval_questions:
            print(f"\nEvaluating question {item['id']}: {item['question']}")
            
            try:
                response = await client.post(
                    "/api/v1/ask",
                    json={
                        "question": item["question"],
                        "top_k": 5
                    },
                    headers={"X-API-Key": API_KEY},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Simple evaluation: check if answer is non-empty and has citations
                    has_answer = len(data["answer"]) > 10
                    has_citations = len(data["citations"]) > 0
                    
                    score = 1.0 if (has_answer and has_citations) else 0.5 if has_answer else 0.0
                    
                    results.append({
                        "id": item["id"],
                        "question": item["question"],
                        "answer": data["answer"][:200],
                        "citation_count": len(data["citations"]),
                        "score": score
                    })
                    
                    print(f"  Score: {score}")
                    print(f"  Citations: {len(data['citations'])}")
                else:
                    print(f"  Error: {response.status_code}")
                    results.append({
                        "id": item["id"],
                        "question": item["question"],
                        "error": f"HTTP {response.status_code}",
                        "score": 0.0
                    })
            
            except Exception as e:
                print(f"  Exception: {str(e)}")
                results.append({
                    "id": item["id"],
                    "question": item["question"],
                    "error": str(e),
                    "score": 0.0
                })
    
    # Calculate overall score
    total_score = sum(r["score"] for r in results)
    max_score = len(results)
    percentage = (total_score / max_score) * 100 if max_score > 0 else 0
    
    print("\n" + "="*60)
    print(f"EVALUATION RESULTS")
    print("="*60)
    print(f"Total Questions: {len(results)}")
    print(f"Total Score: {total_score}/{max_score} ({percentage:.1f}%)")
    print("="*60)
    
    # Save results
    with open("eval/results.txt", "w") as f:
        f.write(f"Evaluation Score: {total_score}/{max_score} ({percentage:.1f}%)\n\n")
        for r in results:
            f.write(f"Q{r['id']}: {r['question']}\n")
            f.write(f"Score: {r['score']}\n")
            if "answer" in r:
                f.write(f"Answer: {r['answer']}...\n")
            if "error" in r:
                f.write(f"Error: {r['error']}\n")
            f.write("\n")
    
    print(f"\nResults saved to eval/results.txt")
    return percentage

if __name__ == "__main__":
    score = asyncio.run(run_evaluation())
    sys.exit(0 if score >= 70 else 1) 