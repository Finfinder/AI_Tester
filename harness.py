"""Simple harness to build and run the Docker runner and capture output."""
import subprocess
import os
import sys

ROOT = os.path.dirname(__file__)

def build_image():
    subprocess.check_call(["docker","build","-t","ai_tester_runner","."], cwd=ROOT)

def run_container():
    mount = f"{ROOT}\\task:/app/task"
    subprocess.check_call(["docker","run","--rm","-v", mount, "ai_tester_runner"], cwd=ROOT)

if __name__ == '__main__':
    try:
        build_image()
        run_container()
    except subprocess.CalledProcessError as e:
        print('Command failed:', e)
        sys.exit(1)
