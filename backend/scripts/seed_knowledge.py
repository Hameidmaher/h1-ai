"""تهيئة قاعدة المعرفة."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge.engine import advisory_engine
from knowledge.loader import knowledge_loader


def main():
    print("🔄 تهيئة قاعدة المعرفة...")
    knowledge_loader.load_all()
    advisory_engine.initialize()
    print(f"✅ Products: {len(knowledge_loader.products)}")
    print(f"✅ Interactions: {len(knowledge_loader.interactions)}")
    print(f"✅ Drugs: {len(knowledge_loader.drugs)}")
    print(f"✅ Symptoms: {len(knowledge_loader.symptoms)}")
    conditions = knowledge_loader.medical_rules.get("conditions", {})
    print(f"✅ Conditions: {len(conditions)}")
    print("✅ Advisory Engine: ready")


if __name__ == "__main__":
    main()
