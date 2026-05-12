# Input Dropzone

Place decrypted IPA files locally under:

```text
input/ipa/
```

Example:

```text
input/ipa/Instagram.decrypted.ipa
```

The directory is intentionally git-ignored for IPA, ZIP, `.app`, `Payload/` and extracted content.

Do **not** commit decrypted IPA files to GitHub.

Reasons:

- GitHub regular file uploads are not suitable for large IPA artifacts.
- Decrypted IPA files may contain proprietary code and private metadata.
- Analysis outputs can be very large and should be kept under `artifacts/`, which is also ignored.

Run local artifact generation:

```bash
scripts/run_full_ipa_artifact.sh input/ipa/Instagram.decrypted.ipa
```

With Ghidra headless decompile export:

```bash
GHIDRA_HEADLESS=/path/to/ghidra/support/analyzeHeadless \
  scripts/run_full_ipa_artifact.sh input/ipa/Instagram.decrypted.ipa --ghidra --ghidra-max-binaries 3
```

Output:

```text
artifacts/radan-full-YYYYmmdd-HHMMSS/
artifacts/radan-full-YYYYmmdd-HHMMSS.decompile-artifact.zip
```
