print("Testing import...")
try:
    from app import app
    print("Import successful!")
    print(f"App object: {app}")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()