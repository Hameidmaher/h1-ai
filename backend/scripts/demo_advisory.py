"""عرض توضيحي."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge.engine import advisory_engine


QUERIES = [
    "هل عندكم بانادول؟",
    "بكام فيتامين سي؟",
    "عندي صداع",
    "عايز حاجة للبرد",
]


def main():
    advisory_engine.initialize()
    for q in QUERIES:
        print(f"\n👤 {q}")
        result = advisory_engine.analyze(q)
        print(f"📊 ثقة: {result.confidence:.2f} | طريقة: {result.method}")
        print(f"💡 {result.advice or 'لا توجد نصيحة'}")
        if result.products:
            for p in result.products[:3]:
                print(f"   • {p}")


if __name__ == "__main__":
    main()
