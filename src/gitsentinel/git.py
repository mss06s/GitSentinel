def get_diff():
    import subprocess
    try:
        result = subprocess.run(['git', 'diff'], capture_output=True, text=True)

        if result.returncode in [0,1]:
            return result.stdout

        return f"Git Error: {result.stderr.strip()}"

    except FileNotFoundError:
        return "Error: Git is not installed or not found in the system PATH."