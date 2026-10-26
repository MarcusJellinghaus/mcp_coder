# Step 6 — Signed release assets job

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_6.md`. Add the `attach-signed-artifacts` job to `.github/workflows/publish.yml` exactly as specified. Do not change the `build` or `publish` jobs. Run pylint, pytest (`-n auto`, unit markers), mypy and `run_format_code`; all must pass. Produce one commit.

## WHERE
- `.github/workflows/publish.yml` (append a third job)

## WHAT
```yaml
  attach-signed-artifacts:
    needs: publish
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      attestations: write
      contents: write
    steps:
      - name: Download artifact
        uses: actions/download-artifact@9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2
        with:
          name: dist
          path: dist/

      - name: Attest build provenance
        id: attest
        uses: actions/attest-build-provenance@4d101475d8b20a2381f78447822ac1eab6504dd8 # v4.2.2
        with:
          subject-path: dist/*

      - name: Upload signed assets to release
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          cp "${{ steps.attest.outputs.bundle-path }}" provenance.sigstore.json
          gh release upload "${{ github.event.release.tag_name }}" dist/* provenance.sigstore.json --repo "${{ github.repository }}" --clobber
```

## HOW
- Separate job, so the PyPI job keeps only `id-token: write` and the bundle never enters `dist/`.
- No checkout, which is why `--repo` is needed. `--clobber` makes re-runs safe. Keyless Sigstore: no secrets.
- The top-level `permissions: contents: read` stays; the job-level block overrides it for this job only.
- No backfill of old releases.

## Precondition
- If the `publish.yml` job names are not `build`/`publish`, or the artifact name is not `dist`, write one line to `pr_info/.blocked.txt` and stop.

## ALGORITHM / DATA
None (workflow YAML). Verification happens after the next release (maintainer): the release has `dist/*` and `provenance.sigstore.json` attached, and PyPI is unaffected.
