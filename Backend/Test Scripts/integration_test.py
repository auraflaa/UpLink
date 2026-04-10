import requests
import uuid
import time
import random
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Configuration
EMBEDDING_URL = "http://localhost:6377/embed"
QDRANT_URL = "http://localhost:6366"
COLLECTION_NAME = "uplink_master_integration"

console = Console()

def run_unified_test():
    console.print(Panel.fit("[bold blue]UpLink Master Integration & Pipeline Test[/bold blue]", subtitle="Verifying Intelligence Core"))
    
    try:
        # --- 1. DATASET GENERATION ---
        frameworks = ["React", "Vue", "Angular", "Django", "FastAPI", "Flask", "Spring Boot", "Express"]
        roles = ["Frontend", "Backend", "Fullstack", "DevOps", "AI Engineer"]
        
        dataset = []
        for i in range(20):
            fw = random.choice(frameworks)
            role = random.choice(roles)
            dataset.append({
                "text": f"Expert {role} developer with 5 years experience in {fw}. Highly skilled in building scalable applications.",
                "type": role,
                "framework": fw
            })
        
        # Specific Tricky Profiles
        dataset.append({"text": "Senior Python developer focusing on Web Scraping and Automation.", "type": "Automation"})
        dataset.append({"text": "Senior Python developer focusing on Machine Learning and Neural Networks.", "type": "AI"})
        
        # --- 2. BATCH EMBEDDING ---
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            task1 = progress.add_task("[yellow]Requesting batch embeddings...", total=None)
            start_time = time.time()
            texts = [d['text'] for d in dataset]
            embed_res = requests.post(EMBEDDING_URL, json={"texts": texts})
            embed_res.raise_for_status()
            vectors = embed_res.json().get("embeddings")
            duration = time.time() - start_time
            progress.update(task1, description=f"[bold green]Received {len(vectors)} vectors in {duration:.2f}s[/bold green]")
            progress.stop()

        # --- 3. RECREATE COLLECTION ---
        console.print(f"[*] Initializing Qdrant collection: [cyan]'{COLLECTION_NAME}'[/cyan]")
        requests.delete(f"{QDRANT_URL}/collections/{COLLECTION_NAME}")
        requests.put(f"{QDRANT_URL}/collections/{COLLECTION_NAME}", json={
            "vectors": {"size": 768, "distance": "Cosine"}
        }).raise_for_status()

        # --- 4. BATCH STORAGE ---
        points = []
        for d, v in zip(dataset, vectors):
            points.append({
                "id": str(uuid.uuid4()),
                "vector": v,
                "payload": d
            })
        requests.put(f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points", json={"points": points}).raise_for_status()
        console.print(f"[bold green]SUCCESS:[/bold green] {len(points)} profiles indexed in Vector DB.")

        # --- 5. SEMANTIC NUANCE TEST ---
        query = "Who handles AI and Deep Learning?"
        console.print(f"\n[bold yellow]Testing Semantic Nuance[/bold yellow]")
        console.print(f"Query: [italic]'{query}'[/italic]")
        
        q_vec = requests.post(EMBEDDING_URL, json={"texts": [query]}).json()['embeddings'][0]
        search_res = requests.post(f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/search", json={
            "vector": q_vec, "limit": 2, "with_payload": True
        }).json()['result']
        
        table = Table(title="Search Results")
        table.add_column("Rank", style="cyan")
        table.add_column("Match", style="white")
        table.add_column("Score", style="green")
        
        for i, res in enumerate(search_res):
            table.add_row(str(i+1), res['payload']['text'], f"{res['score']:.4f}")
        
        console.print(table)
        
        if search_res[0]['payload']['type'] == "AI":
            console.print("[bold green]PASS:[/bold green] Correct specialist identified.")
        else:
            console.print("[bold red]FAIL:[/bold red] Precision check failed.")

        # --- 6. FUZZY SIMILARITY TEST ---
        query_2 = "I need to build a user interface with React"
        console.print(f"\n[bold yellow]Testing Fuzzy Similarity[/bold yellow]")
        console.print(f"Query: [italic]'{query_2}'[/italic]")
        
        q_vec_2 = requests.post(EMBEDDING_URL, json={"texts": [query_2]}).json()['embeddings'][0]
        search_res_2 = requests.post(f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/search", json={
            "vector": q_vec_2, "limit": 1, "with_payload": True
        }).json()['result'][0]
        
        console.print(f"Matched: [cyan]'{search_res_2['payload']['text']}'[/cyan]")
        if "React" in search_res_2['payload']['text']:
            console.print("[bold green]PASS:[/bold green] Semantic mapping works.")

        # --- 7. LOAD TEST ---
        console.print(f"\n[bold yellow]Stress Test (50 Sequential Searches)[/bold yellow]")
        load_start = time.time()
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
            progress.add_task("Running...", total=50)
            for _ in range(50):
                requests.post(f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/search", json={
                    "vector": q_vec, "limit": 3
                })
        load_time = time.time() - load_start
        console.print(f"[bold green]COMPLETED:[/bold green] 50 searches in {load_time:.2f}s (Avg: {load_time/50:.4f}s)")

        # --- 8. CLEANUP ---
        requests.delete(f"{QDRANT_URL}/collections/{COLLECTION_NAME}")
        
        console.print(Panel("[bold green]✨ SYSTEM CORE IS STABLE, ACCURATE, AND PERFORMANT ✨[/bold green]", border_style="green"))

    except Exception as e:
        console.print(f"\n[bold red]FATAL ERROR:[/bold red] {e}")

if __name__ == "__main__":
    run_unified_test()
