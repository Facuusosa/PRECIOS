import subprocess
import re
import sys

CREDENTIAL_PATTERNS = [
    r'PHPSESSID\s*=\s*["\']?[a-zA-Z0-9]{10,}',
    r'cf_clearance\s*=\s*["\']?[a-zA-Z0-9._-]{10,}',
    r'password\s*=\s*["\'][^"\']{4,}["\']',
    r'passwd\s*=\s*["\'][^"\']{4,}["\']',
    r'secret\s*=\s*["\'][^"\']{4,}["\']',
    r'api_key\s*=\s*["\'][^"\']{4,}["\']',
    r'Bearer\s+[a-zA-Z0-9._-]{20,}',
]

EXTENSIONS_TO_CHECK = {'.py', '.ts', '.tsx', '.js', '.jsx', '.json', '.yaml', '.yml', '.txt'}
SKIP_FILES = {'.env', 'check_env_leak.py'}

def get_staged_files():
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only'],
        capture_output=True, text=True
    )
    return result.stdout.strip().split('\n') if result.stdout.strip() else []

def check_file(path: str) -> list[str]:
    suffix = '.' + path.rsplit('.', 1)[-1] if '.' in path else ''
    if suffix not in EXTENSIONS_TO_CHECK:
        return []
    if any(skip in path for skip in SKIP_FILES):
        return []
    try:
        result = subprocess.run(
            ['git', 'show', f':{path}'],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        content = result.stdout or ''
    except Exception:
        return []
    hits = []
    for i, line in enumerate(content.splitlines(), 1):
        for pattern in CREDENTIAL_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                hits.append(f"  {path}:{i}: {line.strip()[:80]}")
                break
    return hits

def main():
    staged = get_staged_files()
    if not staged or staged == ['']:
        sys.exit(0)
    all_hits = []
    for f in staged:
        all_hits.extend(check_file(f))
    if all_hits:
        print("[SECURITY] Posibles credenciales detectadas en archivos staged:")
        for hit in all_hits:
            print(hit)
        print("\nSi es un falso positivo, hacer commit con --no-verify (usar con cuidado).")
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main()
