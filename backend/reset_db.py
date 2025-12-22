import shutil
import os

# Path to the ChromaDB folder
# Assuming this script is run from the 'backend' directory
DB_PATH = "./chroma_db"


def reset_database():
    print(f"Attempting to wipe database at: {DB_PATH}")

    if os.path.exists(DB_PATH):
        try:
            shutil.rmtree(DB_PATH)
            print("SUCCESS: Brain wiped. All memories deleted.")
            print("You can now restart the server and begin fresh training.")
        except PermissionError:
            print("ERROR: Permission denied.")
            print("STOP THE SERVER FIRST! (Ctrl+C in your terminal)")
        except Exception as e:
            print(f"ERROR: Could not delete folder. Reason: {e}")
    else:
        print("NOTE: Database was already empty.")


if __name__ == "__main__":
    print("WARNING: This will delete all training data!")
    confirm = input("Are you sure? (y/n): ")
    if confirm.lower() == 'y':
        reset_database()
    else:
        print("Cancelled.")
