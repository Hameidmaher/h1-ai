"""قياس أداء Advisory Engine."""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from knowledge.engine import advisory_engine


QUERIES = [
    "هل عندكم بانادول؟",
    "بكام فيتامين سي؟",
    "عندي صداع",
    "عايز حاجة للبرد",
    "هل فيه توصيل؟",
    "بانادول إكسترا متوفر؟",
    "أوجمنتين 1 جم",
    "فيتامين د",
    "كريم مرطب",
    "جهاز ضغط",
]


def main():
    print("🔄 تهيئة...")
    advisory_engine.initialize()
    print()
    print("⚡ قياس الأداء...")
    print("─" * 60)

    times = []
    for q in QUERIES:
        start = time.perf_counter()
        advisory_engine.search(q, top_k=5)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
        print(f"  {q[:40]:<40} → {elapsed:6.2f} ms")

    print("─" * 60)
    avg = sum(times) / len(times)
    print(f"  متوسط: {avg:.2f} ms")
    print(f"  أدنى:  {min(times):.2f} ms")
    print(f"  أعلى:  {max(times):.2f} ms")


if __name__ == "__main__":
    main()
