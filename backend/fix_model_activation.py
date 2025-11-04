#!/usr/bin/env python3
"""
Fix Model Activation Status
This script ensures only ONE model is marked as active at a time.
"""

import sys
sys.path.insert(0, '/run/media/spidey/35f48b83-0fe4-4b1f-ba92-81ad5e6b81f61/M.A.R.L.IN-edna-species-classifier/backend')

from app.database.session import SessionLocal
from app.models.database_models import Model

def fix_model_activation():
    """Fix model activation status - only one should be active."""
    db = SessionLocal()
    
    try:
        # Get all models
        models = db.query(Model).order_by(Model.created_at.desc()).all()
        
        print("=" * 80)
        print("Fix Model Activation Status")
        print("=" * 80)
        
        if not models:
            print("\n❌ No models found in database")
            return
        
        print(f"\n📊 Found {len(models)} model(s):\n")
        
        for i, model in enumerate(models, 1):
            print(f"   {i}. ID={model.id}, Name={model.name}, Version={model.version}")
            print(f"      Status={model.status}, Active={model.is_active}")
            print(f"      Created={model.created_at}")
            print()
        
        # Count active models
        active_models = [m for m in models if m.is_active]
        
        if len(active_models) == 0:
            print("⚠️  No models are marked as active!")
            print("\n🔧 Activating the most recent model...")
            models[0].is_active = True
            db.commit()
            print(f"✅ Activated model {models[0].id} ({models[0].name} {models[0].version})")
            
        elif len(active_models) == 1:
            print(f"✅ Correct! Only 1 model is active: {active_models[0].id} ({active_models[0].name})")
            
        else:
            print(f"❌ Problem! {len(active_models)} models are marked as active:")
            for m in active_models:
                print(f"   - ID={m.id}, {m.name} {m.version}")
            
            print("\n🔧 Fixing: Deactivating all except the most recent...")
            
            # Deactivate all
            db.query(Model).update({"is_active": False})
            
            # Activate most recent
            models[0].is_active = True
            db.commit()
            
            print(f"✅ Fixed! Now only model {models[0].id} ({models[0].name} {models[0].version}) is active")
        
        # Also fix legacy 'active' status -> 'completed'
        print("\n🔧 Fixing legacy status values...")
        updated = 0
        for model in models:
            if model.status == "active":
                model.status = "completed"
                updated += 1
        
        if updated > 0:
            db.commit()
            print(f"✅ Updated {updated} model(s) from status='active' to status='completed'")
        else:
            print("✅ No legacy status values found")
        
        print("\n" + "=" * 80)
        print("Final State:")
        print("=" * 80)
        
        models = db.query(Model).order_by(Model.created_at.desc()).all()
        for i, model in enumerate(models, 1):
            active_marker = "🟢 ACTIVE" if model.is_active else "⚪ Inactive"
            print(f"{i}. {active_marker} | ID={model.id} | {model.name} {model.version}")
            print(f"   Status={model.status}, Created={model.created_at}")
            print()
        
        print("✅ Done!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    fix_model_activation()
