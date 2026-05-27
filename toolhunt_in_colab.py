## Download the required model for semantic search
from sentence_transformers import SentenceTransformer
import os
import subprocess
import sys
import threading
import time
from pyngrok import ngrok
sentences = ["This is an example sentence", "Each sentence is converted"]

model = SentenceTransformer('sentence-transformers/all-MiniLM-L12-v2')
embeddings = model.encode(sentences)
print(embeddings)

## Download dependencises
subprocess.run(['git', 'clone', 'https://github.com/cyberytti/ToolHunt'], check=True)
os.chdir("ToolHunt")
subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyngrok'], check=True)

# =========================
# Directly Run ToolHunt in Colab (Debugging Mode)
# =========================

# --- 1. Set up paths and environment ---
project_root = "/content" # Standard Colab working directory
toolhunt_dir = os.path.join(project_root, "ToolHunt")

if not os.path.isdir(toolhunt_dir):
    raise FileNotFoundError(f"ToolHunt directory not found at {toolhunt_dir}")

# Crucially, add the project root to Python's path
# This allows 'from backend.main import ...' to work when app.py is run
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added {project_root} to sys.path")

print(f"Project root: {project_root}")
print(f"ToolHunt dir: {toolhunt_dir}")
print(f"sys.path (relevant parts): {[p for p in sys.path if 'content' in p]}")

# Set ngrok token securely from environment variable
ngrok_token = os.environ.get('NGROK_AUTH_TOKEN')
if ngrok_token:
    ngrok.set_auth_token(ngrok_token)
else:
    print("⚠️ WARNING: NGROK_AUTH_TOKEN environment variable not set.")
    print("   Please set it securely (e.g., using Google Colab secrets) to avoid hardcoding credentials.")
    print("   Example: import os; os.environ['NGROK_AUTH_TOKEN'] = 'your_token_here'")

# --- 2. Import and run Flask app ---
try:
    # Change working directory to ToolHunt so relative paths inside app.py work
    # (like loading templates)
    os.chdir(toolhunt_dir)
    print(f"Changed working directory to: {os.getcwd()}")

    # Now we can import app.py as a module because we added /content to sys.path
    # and we are running from within the ToolHunt directory for relative file paths.
    import app

    print("✅ Successfully imported app.py")

    # --- 3. Run Flask in a separate thread ---
    def run_flask():
        print("🚀 Starting Flask app...")
        # Run Flask app. Note: debug=True might cause issues in threads/Colab,
        # but let's try it first. If problems occur, remove debug=True.
        app.app.run(host='127.0.0.1', port=5000, debug=False) # Start without debug first

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True # Dies when main thread dies
    flask_thread.start()
    print("🧵 Flask thread started.")

    # --- 4. Wait and check ---
    # Give Flask time to start (especially for model download on first run)
    print("⏳ Waiting for Flask to initialize...")
    time.sleep(8) # Adjust if needed

    # A simple check if the thread is still alive (not a guarantee the server is up)
    if flask_thread.is_alive():
        print("✅ Flask thread is running.")
    else:
        print("⚠️ Flask thread has stopped. Check for errors in the logs above.")

    # --- 5. Create ngrok tunnel ---
    print("🚇 Starting ngrok tunnel...")
    tunnel = ngrok.connect(5000, "http")
    print("\n🎉 ToolHunt is ready!")
    print(f"🔗 Public URL: {tunnel.public_url}")
    print("\nPress the 'Interrupt Execution' button (⏹️) in Colab to stop.")

    # --- 6. Keep alive ---
    # Keep the main thread alive to maintain the tunnel
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user.")
    finally:
        print("🧹 Cleaning up...")
        ngrok.kill()
        # Note: Stopping the Flask thread cleanly from here is tricky in Colab.
        # The daemon thread will stop when the main program ends.
        print("✅ Done.")

except Exception as e:
    print(f"❌ An error occurred during startup: {e}")
    import traceback
    traceback.print_exc()
