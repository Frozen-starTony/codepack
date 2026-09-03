"""
Direct runner script for CodePack.
Usage: python codepack.py [options]
"""

from pathlib import Path
import subprocess
import sys

# Ensure src/ is on sys.path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root / "src"))

from codepack.cli import main


def interactive_menu():
    while True:
        print("\n" + "=" * 60)
        print("                   CodePack Menu")
        print("=" * 60)
        print("[1] Copy entire project to clipboard (Full context)")
        print("[2] Copy compact mode to clipboard (Signatures & outline only)")
        print("[3] Copy to clipboard skipping test suites")
        print("[4] Display project directory tree only")
        print("[5] Run unit tests (unittest)")
        print("[6] Exit\n")

        try:
            choice = input("Select an option (1-6): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            return 0

        if choice == "1":
            main(["-c"])
            input("\nPress Enter to return to menu...")
        elif choice == "2":
            main(["--compact", "-c"])
            input("\nPress Enter to return to menu...")
        elif choice == "3":
            main(["--skip-tests", "-c"])
            input("\nPress Enter to return to menu...")
        elif choice == "4":
            main(["--tree-only"])
            input("\nPress Enter to return to menu...")
        elif choice == "5":
            subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=str(project_root))
            input("\nPress Enter to return to menu...")
        elif choice == "6" or choice.lower() in {"q", "exit"}:
            return 0
        else:
            print("Invalid selection, please try again.")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.exit(interactive_menu())
    else:
        sys.exit(main())
