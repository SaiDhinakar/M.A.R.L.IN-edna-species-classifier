#!/usr/bin/env python3
"""
Setup ZenML for M.A.R.L.IN Backend in local mode.
"""

import os
import sys
import shutil
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))


def cleanup_zenml_config():
    """Remove any existing ZenML configuration."""
    print("🧹 Cleaning previous ZenML configuration...")
    
    # Remove global config
    global_config = Path.home() / ".config" / "zenml"
    if global_config.exists():
        shutil.rmtree(global_config)
        print(f"   Removed: {global_config}")
    
    # Remove local config
    local_config = Path(__file__).parent / ".zenml"
    if local_config.exists():
        shutil.rmtree(local_config)
        print(f"   Removed: {local_config}")


def setup_zenml_local():
    """Initialize ZenML in local mode."""
    print("\n📦 Initializing ZenML with local database...")
    
    try:
        # Disable analytics
        os.environ['ZENML_ANALYTICS_OPT_IN'] = 'false'
        os.environ['ZENML_LOGGING_VERBOSITY'] = 'INFO'
        
        from zenml.client import Client
        
        # Initialize local store (uses default local SQLite)
        print("   Creating local ZenML store...")
        
        # Get or create client (will initialize local store automatically)
        client = Client()
        
        print(f"\n✅ ZenML initialized successfully!")
        print(f"   Active Stack: {client.active_stack_model.name}")
        
        # Try to get store info if available
        try:
            if hasattr(client, 'zen_store'):
                print(f"   Store Type: {type(client.zen_store).__name__}")
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error initializing ZenML: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_zenml():
    """Verify ZenML is working."""
    print("\n🔍 Verifying ZenML installation...")
    
    try:
        from zenml import __version__ as zenml_version
        from zenml.client import Client
        
        print(f"   ZenML Version: {zenml_version}")
        
        client = Client()
        print(f"   Client Status: Connected")
        
        # Try to access store info
        try:
            if hasattr(client, 'zen_store'):
                print(f"   Store Type: {type(client.zen_store).__name__}")
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"   ❌ Verification failed: {e}")
        return False


def main():
    print("=" * 60)
    print("ZenML Setup for M.A.R.L.IN Backend (Local Mode)")
    print("=" * 60)
    
    # Step 1: Clean up
    cleanup_zenml_config()
    
    # Step 2: Setup
    if not setup_zenml_local():
        print("\n⚠️  Setup failed. Please check the errors above.")
        return 1
    
    # Step 3: Verify
    if not verify_zenml():
        print("\n⚠️  Verification failed. ZenML may not be working correctly.")
        return 1
    
    print("\n" + "=" * 60)
    print("✅ ZenML Setup Complete!")
    print("=" * 60)
    print("\nZenML is now configured in LOCAL mode.")
    print("No server is required - all data is stored locally.")
    print("\nConfiguration:")
    print("  - Store: Local SQLite database")
    print("  - Location: ~/.config/zenml/")
    print("  - Artifacts: ./data/zenml_artifacts/")
    print("\nYou can now run training pipelines!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
