# Building and Releasing WARPSimLab

This document describes how to create, test, package, and publish a WARPSimLab Windows release.
All commands are PowerShell.

## 1. Freeze the Release

If we find issues past this point, fix them and return here again.


## 2. Make sure git is clean

```
git status
```


## 3. Create a Clean Build Environment

Use a clean Python virtual environment for the release build.  We do this to make sure we don't have 
unexpected dependencies that are being masked by the current windows environment.

Lets create a virtual environment.  

```
py -m venv .venv-release
.\.venv-release\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Record the build environment:

```
python --version 2>&1 | Tee-Object -FilePath build-environment.txt
python -m PyInstaller --version 2>&1 | Tee-Object -FilePath build-environment.txt -Append
python -m pip freeze 2>&1 | Tee-Object -FilePath build-environment.txt -Append
```

Keep `build-environment.txt` with the release records; do not distribute it.


## 4. Run the Complete Test Suite

```
python -m pytest 2>&1 | Tee-Object -FilePath test-results.txt
```

Keep `test-results.txt` with the release records; do not distribute it.

## 5. Run a Source Smoke Test

Before building the executable, run WARPSimLab from Python and verify:

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


## 6. Remove Previous Build Output


```
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
```

## 7. Build the Windows Distribution

```
python -m PyInstaller --clean --noconfirm WARPSimLab.spec
```

The resulting directory should resemble:

```text
dist\
    WARPSimLab\
        WARPSimLab.exe
        Internal\
        ...
```

## 8. Test the Frozen Application

Copy the frozen application to a clean Windows computer or virtual machine.

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
14. Confirm no console windows appear unexpectedly.
15. Confirm no debug messages appear.
16. Run WARPSimLab with the internet disconnected.
17. Close and restart WARPSimLab.
18. Confirm the displayed version is correct.
19. Confirm user-created files are not written inside the installed application directory unless explicitly intended.


## 9. Sign the Executable

If code signing is available, sign the final executable before creating the ZIP file.

If signing is not yet available, the release may still be published, but the website and installation instructions should explain that Windows may display an unrecognized-app warning.

Do not use a self-signed certificate for the public release.

After signing, verify the signature and rerun a basic launch and simulation test.


## 10. Create the Release Package

Create one canonical Windows ZIP file.  Create the ZIP from the completed `dist\WARPSimLab` directory using Windows File Explorer.

```text
WARPSimLab-v[X.Y.Z]-Windows-x64.zip
```

The ZIP should contain one top-level directory:

```text
WARPSimLab-v[X.Y.Z]\
    WARPSimLab.exe
    Internal\
    README-FIRST.txt
    LICENSE.txt
```

The user must extract the complete ZIP before running WARPSimLab.

Suggested `README-FIRST.txt` contents:

```text
WARPSimLab v[X.Y.Z]

INSTALLATION

1. Extract the complete ZIP file.
2. Keep WARPSimLab.exe and the Internal directory together.
3. Run WARPSimLab.exe.
4. Windows may display a warning for newly published software.

WARPSimLab is an educational personal-finance simulation tool.
It does not provide financial, tax, legal, or investment advice.

Documentation:
https://warpsimlab.org/

Source code:
https://github.com/[GITHUB-ACCOUNT]/[REPOSITORY]
```

## 11. Scan the Release

Scan the release files:

* `WARPSimLab.exe`
* `WARPSimLab-v[X.Y.Z]-Windows-x64.zip`

Use:

* Microsoft Defender
* VirusTotal

Record:

* Scan date
* WARPSimLab version
* Filename
* VirusTotal result
* Any detections
* Assessment of any apparent false positives


## 12. Generate the SHA-256 Checksum

From PowerShell:

```powershell
Get-FileHash `
    .\WARPSimLab-v[X.Y.Z]-Windows-x64.zip `
    -Algorithm SHA256
```

Save the result in:

```text
WARPSimLab-v[X.Y.Z]-SHA256.txt
```

Suggested format:

```text
WARPSimLab v[X.Y.Z]

File:
WARPSimLab-v[X.Y.Z]-Windows-x64.zip

SHA-256:
[CHECKSUM]
```


## 13. Record the Release Commit

Confirm that the repository still points to the commit used for the final build:

```
git status
git rev-parse HEAD
```

The working tree should be clean. Save the commit hash with the release records. 
The version tag created in the next step must point to this commit.


## 14. Create the Git Tag

Create an annotated tag for the exact release commit:

```
git tag -a v[X.Y.Z] -m "WARPSimLab v[X.Y.Z]"
git push origin main
git push origin v[X.Y.Z]
```

## 15. Create the GitHub Release

Create a draft GitHub release using the new version tag.

Upload:

* `WARPSimLab-v[X.Y.Z]-Windows-x64.zip`
* `WARPSimLab-v[X.Y.Z]-SHA256.txt`

Optionally upload:

* A sample report
* A text record of the security scan results

The release notes should include:

* Release highlights
* Important corrections
* Known limitations
* Installation instructions
* Website link
* Documentation link
* Educational-use disclaimer

Example structure:

```markdown
# WARPSimLab v[X.Y.Z]

## Highlights

- Added ...
- Added ...
- Improved ...

## Corrections

- Fixed ...
- Corrected ...

## Known Limitations

- Limitations

## Installation

1. Download `WARPSimLab-v[X.Y.Z]-Windows-x64.zip`.
2. Extract the complete ZIP file.
3. Keep `WARPSimLab.exe` and the `Internal` directory together.
4. Run `WARPSimLab.exe`.

Windows may display a warning for newly published software.

WARPSimLab is an educational simulation tool and does not provide financial, tax, legal, or investment advice.
```

GitHub automatically creates source-code ZIP and tar.gz archives for the release tag. Do not upload a separately created source tarball.

Before publishing the release:

1. Confirm the tag is correct.
2. Confirm the release title and version number are correct.
3. Confirm the uploaded Windows ZIP is the final scanned file.
4. Confirm the checksum file is correct.
5. Download `WARPSimLab-v[X.Y.Z]-Windows-x64.zip` from the draft release.
6. Generate its SHA-256 checksum.
7. Confirm it matches the published checksum.
8. Publish the release.
1. 
Publish the GitHub release only after verification succeeds.

## 16. Update the Website

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

The website should preferably link to the GitHub release asset rather than hosting a separate copy. This provides 
one canonical binary and reduces the possibility of publishing different files in different locations.

Update `sitemap.xml` only when URLs are added, removed, or changed. Updating the contents of an existing release page 
does not normally require a new sitemap entry.

## 17. Test the Public Release

After the GitHub release and website update are public:

1. Open the WARPSimLab website in a private browser window.
2. Follow the normal user download path.
3. Download the Windows ZIP.
4. Verify its SHA-256 checksum.
5. Extract the complete ZIP.
6. Start WARPSimLab.
7. Confirm the displayed version.
8. Run a basic simulation.
9. Generate at least one report.
10. Verify all website and documentation links.
11. Verify the GitHub tag contains the source used to build the executable.

## Condensed Release Checklist

### Build and Validation

* [ ] Freeze the release feature set.
* [ ] Select and update the version number.
* [ ] Update README, release notes, limitations, and disclaimers.
* [ ] Confirm the Git working tree is clean.
* [ ] Create or activate the clean release environment.
* [ ] Install documented dependencies.
* [ ] Run the complete pytest suite.
* [ ] Run the source smoke test.
* [ ] Delete previous `build` and `dist` directories.
* [ ] Build using the checked-in PyInstaller spec file.
* [ ] Test the frozen application on a clean Windows system.
* [ ] Sign the executable, if signing is available.
* [ ] Create the versioned Windows ZIP.
* [ ] Scan the final executable and ZIP.
* [ ] Generate the ZIP SHA-256 checksum.
* [ ] Confirm the package has not changed after hashing.

### Publication

* [ ] Confirm the release commit.
* [ ] Create and push the version tag.
* [ ] Create a draft GitHub release.
* [ ] Upload the Windows ZIP and checksum.
* [ ] Download the GitHub asset and verify its checksum.
* [ ] Publish the GitHub release.
* [ ] Update the WARPSimLab website.
* [ ] Test the complete public download process.
* [ ] Announce the release.
