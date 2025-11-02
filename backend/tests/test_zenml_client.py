"""
Test ZenML client initialization and pipeline execution.
"""

import logging
from zenml.client import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_zenml_client():
    """Test ZenML client initialization."""
    try:
        client = Client()
        logger.info(f"✅ ZenML client initialized successfully")
        logger.info(f"  Active store: {client.zen_store.url}")
        logger.info(f"  Active stack: {client.active_stack_model.name}")
        logger.info(f"  Active workspace: {client.active_workspace.name}")
        
        # Check if we have a default project/workspace
        workspaces = client.list_workspaces()
        logger.info(f"  Available workspaces: {[w.name for w in workspaces]}")
        
        return True
    except Exception as e:
        logger.error(f"❌ ZenML client initialization failed: {e}")
        return False


def test_simple_pipeline():
    """Test a simple ZenML pipeline."""
    from zenml import step, pipeline
    
    @step
    def simple_step(x: int) -> int:
        return x * 2
    
    @pipeline
    def simple_pipeline(x: int):
        return simple_step(x)
    
    try:
        # Initialize client
        client = Client()
        
        # Run pipeline
        result = simple_pipeline(x=5)
        logger.info(f"✅ Simple pipeline executed successfully")
        logger.info(f"  Pipeline run ID: {result.id if hasattr(result, 'id') else 'N/A'}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Simple pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing ZenML setup...")
    print("=" * 50)
    
    print("\n1. Testing ZenML Client:")
    client_ok = test_zenml_client()
    
    print("\n2. Testing Simple Pipeline:")
    pipeline_ok = test_simple_pipeline()
    
    print("\n" + "=" * 50)
    if client_ok and pipeline_ok:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
