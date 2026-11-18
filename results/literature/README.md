# Literature source receipts

Retrieved 2026-11-18 (Africa/Cairo). Read with `docs/LITERATURE_MATRIX_VERIFIED.md` and `docs/NOVELTY_RISKS.md`.

- `retrieval_manifest.json`: actual HTTP retrieval status, URL, response byte length and SHA-256 for supplied abstract/metadata pages and added primary precedents. Zenodo's API succeeded although its web page failed in the browsing tool.
- `paper_fulltext_receipts.json`: SHA-256 of inspected full HTML/PDF responses and short exact source excerpts. The temporary full responses were used for reading; full copyrighted papers are not redistributed here.
- `github_receipts.json`: connector-fetched repository metadata, directory entries with Git object identifiers, file lengths and short exact snapshots. File object identifiers are linked where a fetched directory supplied them. Branches may subsequently move; object identifiers identify the inspected file content, not a claim to a full experiment checkout.
- `longfunceval_repository_metadata.json`: repository-level license field and metadata, retained separately.
- `zenodo_record.json`: API-reported artifact title, access, declared license and downloadable file metadata. The record's creator field is Anonymous; that field is preserved rather than inferred from the paper authors.
- `pipeline_archive_receipt.json`, when present: independently downloaded archive size/checksum and code-file inventory. Only source and documentation were inspected; published traces were not analyzed.

No prior-work experiment was rerun. No third-party source was imported into the pilot implementation, no model weights were downloaded by this audit, and no paid APIs were called. GitHub README claims about model/data availability are distinguished from independently verified checkpoints and licenses in the matrix. HTTP/API availability, license declarations and code inspection do not prove that a paper's numerical results reproduce.

The paper retrieval step had one tooling limitation: local `pdftotext` was unavailable. The ACL PDF was successfully read through the browsing tool's extracted full text. Zenodo additionally had a transient API timeout between successful retrievals; status and successful retry metadata are retained without treating the failure as evidence that no artifact exists.
