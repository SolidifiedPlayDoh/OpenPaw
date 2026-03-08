"""
Try to brute-force decrypt a Fernet message using common passwords + system wordlists.
Uses SHA256 only (password -> digest -> base64url). Fast - no PBKDF2.
"""
import base64
import hashlib
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from cryptography.fernet import Fernet, InvalidToken

# Top-level for multiprocessing pickling
def _try_password_chunk(args: tuple) -> tuple[bool, str, str] | None:
    """Worker: try a chunk of passwords. Returns (True, plaintext, password) or None."""
    encrypted_bytes, passwords = args
    for pwd in passwords:
        result = _attempt_password(encrypted_bytes, pwd)
        if result:
            return result
    return None


def _attempt_password(encrypted_bytes: bytes, pwd: str) -> tuple[bool, str, str] | None:
    """Try one password with SHA256 key derivation only."""
    try:
        key = _password_to_key_sha256(pwd)
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_bytes)
        return True, decrypted.decode("utf-8", errors="replace"), pwd
    except (InvalidToken, Exception):
        return None

# Wordlist paths - try project dir first, then data/, then system
def _get_wordlist_paths():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return [
        os.path.join(script_dir, "wordlist.txt"),
        os.path.join(script_dir, "data", "wordlist.txt"),
        os.path.join(script_dir, "rockyou.txt"),
        os.path.join(script_dir, "data", "rockyou.txt"),
        "/usr/share/dict/words",
        "/usr/share/dict/web2",
        "/usr/share/wordlists/rockyou.txt",
        "/usr/share/wordlists/rockyou-75.txt",
    ]

# Common passwords first (fast)
COMMON_PASSWORDS = [
    "password", "123456", "12345678", "qwerty", "abc123", "monkey", "1234567",
    "letmein", "trustno1", "dragon", "baseball", "iloveyou", "master", "sunshine",
    "ashley", "bailey", "passw0rd", "shadow", "123123", "654321", "superman",
    "qazwsx", "michael", "football", "password1", "password123", "admin", "root",
    "secret", "test", "guest", "default", "changeme", "welcome", "hello", "1234",
    "fernet", "encryption", "key", "crypto", "aes", "secret123", "password2",
    "admin123", "root123", "test123", "user", "temp", "tmp", "backup", "data",
    "key123", "encrypt", "decrypt", "cipher", "token", "api", "apikey", "sk-",
    "bot", "discord", "token123", "supersecret", "mypassword", "p@ssw0rd",
    "Password1", "Admin123", "Root123", "Qwerty123", "Summer2024", "Winter2024",
    "Spring2024", "Fall2024", "January", "February", "March", "April", "May",
    "June", "July", "August", "September", "October", "November", "December",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    "123456789", "1234567890", "qwerty123", "1q2w3e4r", "zaq1zaq1", "abc123456",
    "password!", "P@ssw0rd", "P@ssword", "Passw0rd!", "Welcome1", "Welcome123",
    "Summer", "Winter", "Spring", "Autumn", "secretkey", "private", "public",
]


def _password_to_key_sha256(password: str) -> bytes:
    """Derive Fernet key: SHA256(password) -> base64url."""
    digest = hashlib.sha256(password.encode("utf-8", errors="ignore")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt(text: str, key: str) -> str:
    """Encrypt text with Fernet using SHA256(key) as the Fernet key. Returns encrypted string."""
    fernet_key = _password_to_key_sha256(key)
    f = Fernet(fernet_key)
    return f.encrypt(text.encode("utf-8")).decode("utf-8")


def decrypt(encrypted: str, key: str) -> str:
    """Decrypt Fernet string using SHA256(key). Returns plaintext or raises InvalidToken."""
    fernet_key = _password_to_key_sha256(key)
    f = Fernet(fernet_key)
    return f.decrypt(encrypted.encode("utf-8")).decode("utf-8")


def _load_system_wordlist(max_words: int = 500000) -> list[str]:
    """Load words from system dict/wordlist files. Returns unique words, max_words limit."""
    seen = set()
    words = []
    for path in _get_wordlist_paths():
        if len(words) >= max_words:
            break
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    w = line.strip()
                    if w and not w.startswith("#") and w not in seen and len(w) <= 64:
                        seen.add(w)
                        words.append(w)
                        if len(words) >= max_words:
                            break
        except (OSError, IOError):
            continue
    return words


def try_decrypt(
    encrypted: str,
    progress: dict | None = None,
) -> tuple[bool, str | None, str | None]:
    """
    Try to decrypt Fernet message with common passwords + system wordlist.
    SHA256 only. Always uses dict/wordlist. Uses all CPU cores.
    If progress dict is provided, updates it: {phase, current, total, last_tried}.
    Returns (success, plaintext, password_used).
    """
    encrypted = encrypted.strip()
    if not encrypted:
        return False, None, None
    try:
        token = encrypted.encode("utf-8")
    except Exception:
        return False, None, None

    def update_prog(phase: str, current: int, total: int, last: str):
        if progress is not None:
            progress["phase"] = phase
            progress["current"] = current
            progress["total"] = total
            progress["last_tried"] = last

    n_workers = max(1, (os.cpu_count() or 4))

    # Fast SHA256-only pass for common (instant - most common derivation)
    update_prog("common", 0, len(COMMON_PASSWORDS), "")
    for i, pwd in enumerate(COMMON_PASSWORDS):
        try:
            key = _password_to_key_sha256(pwd)
            f = Fernet(key)
            decrypted = f.decrypt(token)
            return True, decrypted.decode("utf-8", errors="replace"), pwd
        except (InvalidToken, Exception):
            pass
        update_prog("common", i + 1, len(COMMON_PASSWORDS), pwd)

    def run_parallel(passwords: list[str], phase: str, total: int):
        if not passwords:
            return None
        # Zeta force: pair from both ends {1,n},{2,n-1},{3,n-2}... target found in fewer moves
        # Bigger chunks = less overhead (SHA256 is fast)
        n = len(passwords)
        chunk_size = max(500, n // (n_workers * 4))
        chunks = []
        i = 0
        while i + chunk_size <= n - i - chunk_size:
            start_block = passwords[i : i + chunk_size]
            end_block = passwords[n - i - chunk_size : n - i]
            chunks.append(start_block + end_block)
            i += chunk_size
        if i <= n - i - 1:
            chunks.append(passwords[i : n - i])
        completed = 0
        with ProcessPoolExecutor(max_workers=n_workers) as ex:
            futures = {ex.submit(_try_password_chunk, (token, chunk)): chunk for chunk in chunks}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    for f in futures:
                        f.cancel()
                    return result
                chunk = futures[future]
                completed += len(chunk)
                last = chunk[-1][:30] if chunk else ""
                update_prog(phase, completed, total, last)
        return None

    # System wordlist (SHA256 only) - always runs
    words = _load_system_wordlist()
    n = len(words)
    update_prog("wordlist", 0, n, "")
    result = run_parallel(words, "wordlist", n)
    if result:
        return result

    return False, None, None
