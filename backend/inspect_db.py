import chromadb

# Path to your DB
DB_PATH = "./chroma_db"


def inspect():
    print(f"Inspecting Database at: {DB_PATH}")

    try:
        client = chromadb.PersistentClient(path=DB_PATH)
        collection = client.get_collection("script_knowledge_base")

        # Get all data (metadata only to keep it fast)
        data = collection.get()

        if not data['ids']:
            print("Database is EMPTY.")
            return

        # Group by Script ID to avoid duplicates
        scripts = {}

        for meta in data['metadatas']:
            sid = meta.get('script_id')
            if sid not in scripts:
                scripts[sid] = {
                    "Title": meta.get('title', 'Unknown'),
                    "Mode": meta.get('mode', 'Unknown'),
                    "Hook Type": meta.get('hook_type', 'Unknown'),
                    "ID": sid
                }

        print(f"\nFound {len(scripts)} unique scripts:\n")

        # Print simplified list
        for i, (sid, info) in enumerate(scripts.items(), 1):
            print(f"{i}. [{info['Mode'].upper()}] {info['Title']}")
            print(f"   Hook: {info['Hook Type']} | ID: {info['ID']}")
            print("-" * 40)

    except Exception as e:
        print(f"Error reading database: {e}")


if __name__ == "__main__":
    inspect()
