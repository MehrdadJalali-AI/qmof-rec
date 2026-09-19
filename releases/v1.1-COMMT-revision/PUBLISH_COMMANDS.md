# Manual publication commands

Run after authenticating GitHub CLI for `MehrdadJalali-AI/qmof-rec`:

```bash
git push origin v1.1-COMMT-revision
gh release create v1.1-COMMT-revision \
  releases/v1.1-COMMT-revision/qmof-rec-v1.1-COMMT-revision.tar.gz \
  releases/v1.1-COMMT-revision/SHA256SUMS \
  --repo MehrdadJalali-AI/qmof-rec \
  --verify-tag \
  --title "QMOF-Rec v1.1-COMMT-revision" \
  --notes-file releases/v1.1-COMMT-revision/RELEASE_NOTES.md
```

Expected release URL after successful publication:
`https://github.com/MehrdadJalali-AI/qmof-rec/releases/tag/v1.1-COMMT-revision`
