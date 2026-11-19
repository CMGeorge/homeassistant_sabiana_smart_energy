# Releasing

Releases are built by two manually-run GitHub Actions workflows: first a
**beta** that you install and test on a real unit, then a **stable release**
of exactly the code you tested.

Tags follow the existing convention: no `v` prefix (`1.1.0`, `1.1.0-beta.1`).

## 1. Publish a beta

1. **Actions → Beta release → Run workflow**.
2. Fill in:
   - **ref**: the branch to test. Use a PR branch to test before merging
     (e.g. `claude/peaceful-noether-4zhak8`), or `master`.
   - **version**: a pre-release version newer than the latest stable release,
     e.g. `1.1.0-beta.1`. Use `-beta.2`, `-beta.3`, … for later rounds.
3. The workflow:
   - runs `ruff check` and `pytest`;
   - creates a commit that only sets `manifest.json` `version` to the beta
     version and tags it. **The branch itself is not changed**; the commit
     exists only on the tag;
   - publishes a GitHub **pre-release** with `sabiana_energy_smart.zip` and
     testing instructions. It is never marked as "Latest", so normal users don't
     get it.

If publishing fails, the tag is deleted again so the run can be repeated.

## 2. Test the beta with HACS

1. **Settings → Devices & services → HACS**, open the *Sabiana Energy Smart*
   entry and enable its **Pre-release** switch entity (disabled by default).
   This makes HACS offer pre-releases for this repository only.
2. **HACS → Sabiana Energy Smart → ⋮ → Redownload**, pick the beta version,
   download, and restart Home Assistant.
3. **Settings → Devices & services → Sabiana Energy Smart** shows the beta
   version.

To roll back, redownload the previous stable version the same way. Read the
README "Upgrade notes" first: some releases (e.g. 1.1.0) migrate entity unique
IDs, and rolling back across such a release creates duplicate entities.

## 3. Publish the stable release

When the beta works:

1. Merge the tested PR into `master` **without further changes to
   `custom_components/`**.
2. **Actions → Stable release → Run workflow** with:
   - **beta_tag**: the beta you confirmed, e.g. `1.1.0-beta.1`;
   - **version**: leave empty to use the beta's version without the suffix
     (`1.1.0`);
   - **allow_untested_changes**: leave off.
3. The workflow:
   - checks that `beta_tag` is a published pre-release and that the version is
     newer than the latest stable release;
   - compares `custom_components/sabiana_energy_smart/` and `hacs.json` on
     `master` with the beta tag (ignoring only the manifest `version`), and
     **stops if anything differs**, listing the files. Publish a new beta in
     that case, or re-run with `allow_untested_changes` if you accept the risk;
   - runs `ruff check` and `pytest`;
   - tags `master`. If `manifest.json` on `master` has a different version, it
     tags a release commit carrying the release version and warns you to bump
     `manifest.json` in a PR;
   - publishes the release as **Latest**, with the zip and notes generated
     since the previous stable release.

## Notes

- The workflows only appear in the Actions tab once they are on the default
  branch (`master`). After that they can build any branch.
- Releases created by these workflows don't trigger `release.yaml`, because
  GitHub doesn't start workflows for releases created with `GITHUB_TOKEN`.
  `release.yaml` still uploads the zip for releases you publish by hand in the
  GitHub UI.
- If tag protection rules are added to the repository, the workflows need
  permission to push tags.
