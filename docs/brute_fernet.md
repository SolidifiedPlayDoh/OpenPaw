# Brute Fernet Module - Encryption and Brute Force

## Overview
Handles Fernet encryption/decryption with SHA256 key derivation, and brute-force decryption using common passwords and system wordlists. Uses only SHA256 - no PBKDF2.

## Key Derivation
The Fernet key is derived by: SHA256 hash of the password (UTF-8 encoded) → raw digest → base64url encoding. This produces a valid 32-byte Fernet key. PBKDF2 and other methods are not used.

## encrypt(text, key)
Encrypts plaintext with the given key (password). Derives the Fernet key via SHA256, encrypts the UTF-8 encoded text, returns the encrypted string. Used by the !encrypt command.

## decrypt(encrypted, key)
Decrypts a Fernet token with the given key. Same SHA256 derivation. Returns plaintext or raises InvalidToken if the key is wrong. Used by the !decrypt command.

## try_decrypt (Brute Force)
Attempts to decrypt by trying many passwords. Two phases:

### Phase 1: Common Passwords
A built-in list of ~75 common passwords (password, 123456, secret, admin, etc.) is tried first. Single-threaded, very fast since SHA256 is quick. Progress is reported for each attempt.

### Phase 2: System Wordlist
Loads words from multiple file paths in order: project wordlist.txt, rockyou.txt, system dict (words, web2), and common wordlist locations. Up to 500k unique words, max length 64 chars. Words are deduplicated across files.

### Parallelism (Zeta Force)
The wordlist is split into chunks that pair from both ends: first chunk has words from the start AND end of the list, second chunk has next block from start and end, etc. This means a password near the end of the list is found much sooner than sequential search. Uses ProcessPoolExecutor with all CPU cores. Chunk size is tuned for progress updates and speed.

### Progress
A progress dict can be passed with keys: phase (common/wordlist), current, total, last_tried. Updated as chunks complete. The Discord bot uses this for heartbeat status updates.

### Returns
(success: bool, plaintext or None, password or None). Only succeeds if SHA256-derived key decrypts the token.
