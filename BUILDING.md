# Building and Releasing WARPSimLab

This document describes how to test, build, package, and publish a WARPSimLab Windows release.

The official Windows distribution is built by GitHub Actions. Local testing is performed before the release tag is created, and the GitHub-built distribution is tested before the GitHub release is published.

All local commands are PowerShell.

## 1. Freeze the Release

UPDATE THE VERSION NUMBER

Freeze the release feature set.

Select the version number and update all locations that display or record it, including:

* gui_init.py
* website/downloads.html
* README
* Release notes
* Documentation
* Known limitations
* Disclaimers
* Sample installation text

If an issue is found after this point, fix it and restart the release process from this step.

## 2. Confirm That Git Is Clean

Run:

```powershell
git status
```

Confirm that:

* All intended changes have been committed.
* No unintended files are staged.
* No required changes remain uncommitted.
* The working tree is clean.

Do not create the release tag until the source has passed local testing.

## 3. Create a Clean Local Test Environment

Use a clean Python virtual environment for local release testing. This helps detect dependencies that may be present in the normal development environment but missing from `requirements.txt`.

Create and activate the environment:

```powershell
python3 -m venv .venv-release
.\.venv-release\Scripts\Activate.ps1
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

The current required packages include:

```text
matplotlib==3.10.7
numpy==2.3.5
pyinstaller==6.18.0
pytest==9.0.1
```

Run WARPSimLab from source:

```powershell
python3 WARPSimLab.py
```

If WARPSimLab fails because a required package is missing, add that package to `requirements.txt`, recreate the clean environment, and repeat the test.

The GitHub Actions workflow, rather than this local environment, produces the official Windows release build.

## 4. Record the Local Test Environment

Record the Python version and installed packages:

```powershell
python3 --version 2>&1 | Tee-Object -FilePath build-environment.txt
python3 -m pip freeze 2>&1 | Tee-Object -FilePath build-environment.txt -Append
```

The PyInstaller version may also be recorded:

```powershell
python3 -m PyInstaller --version 2>&1 | Tee-Object -FilePath build-environment.txt -Append
```

Keep `build-environment.txt` with the release records. Do not distribute it as part of the application.

The GitHub Actions run provides the authoritative record of the environment used to create the official build.

## 5. Run the Complete Test Suite

Run:

```powershell
python3 -m pytest 2>&1 | Tee-Object -FilePath test-results.txt
```

Confirm that the results are acceptable before continuing.

Keep `test-results.txt` with the release records. Do not distribute it as part of the application.

## 6. Run a Source Smoke Test

Run WARPSimLab from Python and verify:

1. The application starts.
2. Basic mode works.
3. Advanced mode works.
4. A scenario can be loaded.
5. A scenario can be saved and reopened.
6. A deterministic simulation runs.
7. A Monte Carlo simulation runs.
8. A historical-window simulation runs.
9. Scenario Explorer works.
10. Every report can be generated.
11. Generated plots and reports use the correct labels.
12. No unexpected debug output appears.
13. The displayed version number is correct.

Do not continue until the source test succeeds.

## 7. Record the Release Commit

Confirm that the repository points to the commit that will be used for the official build:

```powershell
git status
git rev-parse HEAD
```

The working tree must be clean.

Save the commit hash with the release records. The release tag must point to this exact commit.

Push the final release commit:

```powershell
git push origin main
```

## 8. Create and Push the Git Tag

Create an annotated tag for the exact release commit:

```powershell
git tag -a vX.Y.Z -m "WARPSimLab vX.Y.Z"
git push origin vX.Y.Z
```

For example:

```powershell
git tag -a v4.0.3 -m "WARPSimLab v4.0.3"
git push origin v4.0.3
```

Confirm that the tag points to the intended commit:

```powershell
git rev-list -n 1 vX.Y.Z
git rev-parse HEAD
```

The two commit hashes should match.

Do not move or reuse a published release tag.

## 9. Run the GitHub Actions Release Build

Open the WARPSimLab repository on GitHub.

1. Select **Actions**.
2. Select the Windows release-build workflow.
3. Select **Run workflow**.
4. Select the correct release tag or enter the requested version.
5. Use the release tag as the build version when the workflow requests one.
6. Start the workflow.

Confirm that the workflow:

* Checks out the intended release tag.
* Installs the documented dependencies.
* Runs the required tests.
* Builds WARPSimLab using the checked-in PyInstaller specification.
* Creates the versioned Windows ZIP.
* Creates the SHA-256 checksum file.
* Uploads the build output as a GitHub Actions artifact.

The official Windows distribution must come from this GitHub Actions run, not from a local PyInstaller build.

If the workflow fails, correct the problem in the source or workflow, commit the correction, and restart the release process with a new release commit and tag.

Do not silently rebuild a published tag from changed source.

## 10. Download the GitHub Actions Build

After the workflow succeeds:

1. Open the completed workflow run.
2. Confirm that the run used the correct tag and commit.
3. Download the Windows build artifact.
4. Extract the outer GitHub Actions artifact ZIP.
5. Locate the actual WARPSimLab release ZIP inside it.

GitHub Actions wraps uploaded artifacts in an additional ZIP layer. The outer ZIP is only the workflow artifact container and is not the file distributed to users.

The distributable file should use the following naming format:

```text
WARPSimLab-vX.Y.Z-Win-x86_64.zip
```

For example:

```text
WARPSimLab-v4.0.3-Win-x86_64.zip
```

The distributable ZIP should contain one top-level directory:

```text
WARPSimLab-v4.0.3-Win-x86_64\
    WARPSimLab.exe
    Internal\
    README-FIRST.txt
    LICENSE.txt
```

Confirm that:

* `LICENSE.txt` is at the intended level.
* `README-FIRST.txt` is present.
* `WARPSimLab.exe` and the `Internal` directory remain together.
* The version in the filenames and documentation is correct.
* No local development files are included.
* No second unnecessary release ZIP is contained inside the distributable ZIP.

The user must extract the complete release ZIP before running WARPSimLab.

## 11. Review README-FIRST.txt

The packaged `README-FIRST.txt` should resemble:

```text
WARPSimLab vX.Y.Z

INSTALLATION

1. Extract the complete ZIP file.
2. Keep WARPSimLab.exe and the Internal directory together.
3. Run WARPSimLab.exe.
4. Windows may display a warning for newly published software.
5. Click More Info.
6. Click Run Anyway.

WARPSimLab is an educational personal-finance simulation tool.
It does not provide financial, tax, legal, or investment advice.

Documentation:
https://warpsimlab.org/

Source code:
https://github.com/hialanne/warpsimlab
```

Confirm that the version number in this file matches the release.

## 12. Test the GitHub-Built Application

Test the application produced by GitHub Actions, not a locally built copy.

Copy the extracted application to a clean Windows computer or virtual machine.

Test from a path containing spaces, for example:

```text
C:\Users\Alan\Downloads\WARPSimLab Release Test\
```

Verify the following:

1. Start `WARPSimLab.exe`.
2. Run the interactive tutorial.
3. Run Basic mode.
4. Run Advanced mode.
5. Load every distributed sample scenario.
6. Save and reopen a scenario.
7. Run a deterministic simulation.
8. Run a Monte Carlo simulation.
9. Run a historical-window simulation.
10. Open Scenario Explorer.
11. Generate every report.
12. Open all generated HTML, CSV, and other output files.
13. Verify Income, Cash Flow, Operating Balance, Roth, and HSA labels.
14. Confirm that no console windows appear unexpectedly.
15. Confirm that no debug messages appear.
16. Run WARPSimLab with the internet disconnected.
17. Close and restart WARPSimLab.
18. Confirm that the displayed version is correct.
19. Confirm that user-created files are not written inside the application directory unless explicitly intended.
20. Confirm that documentation and website links work.
21. Confirm that the program runs after being extracted through the normal user installation process.

If the GitHub-built application fails, do not replace it with a local build. Correct the source or GitHub Actions workflow and create a new build from a new release commit and tag.

## 13. Verify Code Signing

If the GitHub Actions workflow signs the executable, verify the signature on the downloaded executable before publishing the release.

Confirm that:

* The signature is present.
* The signer is correct.
* Windows reports that the signature is valid.
* The file has not changed since it was signed.

After verifying the signature, run a basic launch and simulation test.

If code signing is not available, the release may still be published, but the website and installation instructions should explain that Windows may display an unrecognized-app warning.

Do not use a self-signed certificate for a public release.

## 14. Scan the GitHub-Built Release

Scan the exact files that will be distributed:

* `WARPSimLab.exe`
* `WARPSimLab-vX.Y.Z-Win-x86_64.zip`

Use:

* Microsoft Defender
* VirusTotal

Record:

* Scan date
* WARPSimLab version
* Commit hash
* Release tag
* Filename
* File SHA-256
* VirusTotal result
* Any detections
* Assessment of any apparent false positives

Do not rebuild or alter the ZIP after scanning it. Any change creates a different file and invalidates the scan and checksum records.

## 15. Verify the SHA-256 Checksum

The GitHub Actions workflow should produce a checksum file for the distributable ZIP.

Verify the checksum locally:

```powershell
Get-FileHash .\WARPSimLab-vX.Y.Z-Win-x86_64.zip -Algorithm SHA256
```

Compare the result with the checksum produced by GitHub Actions.

The checksum file should use a versioned filename, for example:

```text
WARPSimLab-vX.Y.Z-SHA256.txt
```

Suggested contents:

```text
WARPSimLab vX.Y.Z

File:
WARPSimLab-vX.Y.Z-Win-x86_64.zip

SHA-256:
[CHECKSUM]
```

Confirm that:

* The checksum names the correct ZIP file.
* The locally calculated checksum matches the workflow-generated checksum.
* The ZIP has not changed since the checksum was generated.
* The scanned ZIP and checksummed ZIP are the same file.

## 16. Create a Draft GitHub Release

On GitHub, create a draft release using the new version tag.

Use:

```text
Tag: vX.Y.Z
Release title: WARPSimLab vX.Y.Z
```

Upload:

* `WARPSimLab-vX.Y.Z-Win-x86_64.zip`
* `WARPSimLab-vX.Y.Z-SHA256.txt`

Optionally upload:

* A sample report
* A text record of the security-scan results

Do not upload the outer GitHub Actions artifact ZIP.

GitHub automatically creates source-code ZIP and tar.gz archives for the release tag. Do not upload a separately created source archive.

## 17. Prepare the GitHub Release Notes

The release notes should include:

* Release highlights
* Important corrections
* Known limitations
* Installation instructions
* Website link
* Documentation link
* Educational-use disclaimer

Example:

```markdown
# WARPSimLab vX.Y.Z

## Highlights

- Added ...
- Added ...
- Improved ...

## Corrections

- Fixed ...
- Corrected ...

## Known Limitations

- ...

## Installation

1. Download `WARPSimLab-vX.Y.Z-Win-x86_64.zip`.
2. Extract the complete ZIP file.
3. Keep `WARPSimLab.exe` and the `Internal` directory together.
4. Run `WARPSimLab.exe`.

Windows may display a warning for newly published software.

WARPSimLab is an educational simulation tool and does not provide financial, tax, legal, or investment advice.
```

## 18. Verify the Draft GitHub Release

Before publishing:

1. Confirm that the tag is correct.
2. Confirm that the tag points to the intended release commit.
3. Confirm that the release title and version number are correct.
4. Confirm that the uploaded Windows ZIP is the GitHub Actions build.
5. Confirm that the outer GitHub Actions artifact layer was removed.
6. Confirm that the uploaded ZIP is the final scanned file.
7. Confirm that the checksum file names the correct ZIP.
8. Confirm that the release notes describe the correct version.
9. Download the Windows ZIP from the draft release.
10. Calculate its SHA-256 checksum.
11. Confirm that it matches the uploaded checksum file.
12. Extract the downloaded ZIP.
13. Start WARPSimLab.
14. Confirm that the displayed version is correct.
15. Run a basic simulation.
16. Generate at least one report.

Publish the GitHub release only after this verification succeeds.

## 19. Publish the GitHub Release

Publish the verified draft release.

After publication, confirm that:

* The release appears under the correct tag.
* The Windows ZIP can be downloaded.
* The checksum file can be downloaded.
* The source-code archives correspond to the correct tag.
* The release notes display correctly.

The published GitHub release asset is the canonical WARPSimLab Windows distribution.

## 20. Update the Website

Update the WARPSimLab website with:

* Current version
* Release date
* Windows download link
* GitHub release link
* Source repository link
* SHA-256 checksum
* Installation instructions
* Windows warning explanation
* Known limitations
* Security-scan information
* MIT license information
* Educational-use disclaimer

The website should link directly to the GitHub release asset rather than hosting a separate copy. This provides one canonical binary and reduces the possibility of publishing different files in different locations.

Update `sitemap.xml` only when URLs are added, removed, or changed. Updating the contents of an existing page does not normally require a new sitemap entry.

## 21. Test the Public Release

After the GitHub release and website update are public:

1. Open the WARPSimLab website in a private browser window.
2. Follow the normal user download path.
3. Confirm that the download comes from the intended GitHub release.
4. Download the Windows ZIP.
5. Verify its SHA-256 checksum.
6. Extract the complete ZIP.
7. Start WARPSimLab.
8. Confirm the displayed version.
9. Run a basic simulation.
10. Generate at least one report.
11. Verify all website and documentation links.
12. Verify that the GitHub tag contains the source used to build the executable.
13. Confirm that the Windows ZIP and checksum filenames are correct.
14. Confirm that an older release is not presented as the current release.

## 22. Announce the Release

After the public release has been tested successfully, announce it through the appropriate project channels.

Include:

* Version number
* Major changes
* Important corrections
* Download page
* Release notes
* Relevant limitations

Do not announce the release until the public download path has been tested.

# Condensed Release Checklist

## Source Preparation and Local Validation

* [ ] Freeze the release feature set.
* [ ] Select and update the version number.
* [ ] Update README, release notes, limitations, and disclaimers.
* [ ] Confirm the Git working tree is clean.
* [ ] Create or activate a clean local test environment.
* [ ] Install the documented dependencies.
* [ ] Record the local test environment.
* [ ] Run the complete pytest suite.
* [ ] Run the source smoke test.
* [ ] Confirm the displayed version number.
* [ ] Commit all final release changes.
* [ ] Push the final release commit.

## Tag and GitHub Actions Build

* [ ] Record the release commit hash.
* [ ] Create an annotated release tag.
* [ ] Push the release tag.
* [ ] Confirm that the tag points to the release commit.
* [ ] Run the GitHub Actions release workflow.
* [ ] Confirm that the workflow used the correct tag and commit.
* [ ] Confirm that all required workflow steps passed.
* [ ] Download the GitHub Actions artifact.
* [ ] Remove the outer artifact ZIP layer.
* [ ] Locate the distributable Windows ZIP.
* [ ] Inspect the release-package contents.

## Release Validation

* [ ] Test the GitHub-built application on a clean Windows system.
* [ ] Test from a path containing spaces.
* [ ] Test with the internet disconnected.
* [ ] Verify the code signature, if signing is available.
* [ ] Scan the final executable and ZIP.
* [ ] Review any security detections.
* [ ] Verify the workflow-generated SHA-256 checksum.
* [ ] Confirm that the package has not changed after scanning and hashing.

## Publication

* [ ] Create a draft GitHub release using the correct tag.
* [ ] Upload the Windows ZIP.
* [ ] Upload the checksum file.
* [ ] Add the release notes.
* [ ] Download the asset from the draft release.
* [ ] Verify the downloaded asset checksum.
* [ ] Test the downloaded draft-release build.
* [ ] Publish the GitHub release.
* [ ] Update the WARPSimLab website.
* [ ] Test the complete public download process.
* [ ] Announce the release.
