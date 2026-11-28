# Building and Releasing WARPSimLab

Release Windows (x86_64 ZIP) and macOS (Apple Silicon ARM64 DMG) from GitHub Actions. Linux runs from source. Use `main` and the same version tag for both distributions.

## Websites
https://github.com/
https://github.com/hialanne/WARPSimLab

## 1. Prepare the Release

- Update the version in `gui_init.py`.
- Review `requirements.txt`, PyInstaller specs and GitHub Actions workflows.
- Review the following documentation; update where necessary:
  - `README.md`: features, reports, supported platforms and installation.
  - FAQ and Getting Started guides (including bundled PDFs).
  - Built-in tutorials, sample scenarios and user documentation.
  - Known limitations, financial assumptions, statutory data years and disclaimers.
  - Packaged `README-FIRST.txt`: version, installation and signing instructions.
  - `BUILDING.md`: changes to the build and release process.
  - Website: feature descriptions, documentation, installation and download pages (`website/downloads.html`). Publish download links after the release is available.
- Prepare release notes: highlights, corrections, known limitations, installation, documentation links and educational-use disclaimer.

## 2. Local Testing

Create a clean release environment using the Python version used by the build workflow (macOS: 3.13).

Windows (PowerShell):

```powershell
python3 -m venv .venv-release
.\.venv-release\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m venv .venv-release
source .venv-release/bin/activate
python -m pip install -r requirements.txt
```

On macOS use Python 3.13 (`python3.13 -m venv .venv-release`). Install `pyobjc-framework-Cocoa` separately if it is not yet included in `requirements.txt` for Darwin.

Run on each supported platform:

```bash
python -m pytest
python WARPSimLab.py
```

Record pytest results and any platform-specific failures. Fix missing dependencies in `requirements.txt`.

### Application test checklist

Use this checklist for source regression and for the final Windows and macOS packages:

- Basic and Advanced modes; interactive tutorials.
- Load distributed sample scenarios; save and reopen a scenario.
- Deterministic, Monte Carlo and historical-window simulations.
- Scenario Explorer, plots and every report; open generated HTML and CSV files.
- Display scaling, window redraw and shutdown; no orphan windows.
- Correct version, labels and links; no unexpected console windows or debug output.

## 3. Tag and Build

Commit the release changes and push the annotated tag (replace `X.Y.Z` with the release version):

```bash
git push origin main
git tag -a vX.Y.Z -m "WARPSimLab vX.Y.Z"
git push origin vX.Y.Z
```

```bash
git push origin main
git tag -a v4.6.1 -m "WARPSimLab v4.6.1"
git push origin v4.6.1
```

In GitHub Actions, run **Build Windows Release** and the macOS release workflow for the release tag. Download the resulting 
  artifacts and extract the outer GitHub Actions ZIP; distribute the release ZIP and DMG inside it, not the outer artifact container.

**Pending for 4.6.1:** macOS workflow name, runner, signing/notarization and Windows signing integration. Document their 
  actual configuration here once implemented. The local macOS build procedure below is already tested.

Expected release assets:

```text
WARPSimLab-vX.Y.Z-Win-x86_64.zip
WARPSimLab-vX.Y.Z-macOS-arm64.dmg
SHA-256 checksum file(s) covering both distributions
```

Windows ZIP contents: one top-level directory containing `WARPSimLab.exe`, `Internal/`, `README-FIRST.txt` and `LICENSE.txt` 
  (verify exact layout against the workflow).

Use GitHub-built assets for publication. If the source or build configuration changes, rebuild from the corrected commit. Never move a published release tag.

## 4. Local macOS Build (Development)

Python 3.13, Apple Silicon ARM64. From the repository root, create the environment once:

```bash
python3.13 -m venv .venv-mac
source .venv-mac/bin/activate
python -m pip install -r requirements.txt
python -m pip install pyobjc-framework-Cocoa  # omit when declared in requirements.txt
```

For subsequent builds, activate `.venv-mac` and refresh dependencies as needed.

```bash
source .venv-mac/bin/activate
python -m PyInstaller --clean --noconfirm WARPSimLab-macOS.spec
open dist/WARPSimLab.app
```

The spec includes Matplotlib's TkAgg backend. Stage the app and Applications shortcut, then create the DMG:

```bash
rm -rf dmg
mkdir -p dmg
cp -R dist/WARPSimLab.app dmg/
ln -s /Applications dmg/Applications
hdiutil create -volname "WARPSimLab" -srcfolder dmg -ov -format UDZO WARPSimLab-vX.Y.Z-macOS-arm64.dmg
```

Open the DMG and drag the application into `/Applications`. No Python installation is required on the user's Mac.

This is the local development build, not the signed, notarized release procedure.

## 5. Validate the Release Packages

Test the exact GitHub-built distributions on clean systems, without the development environment or internet access. 
  Use the application test checklist in Section 2. On Windows, extract the complete ZIP to a path containing spaces. 
  On macOS, install the downloaded DMG through Finder and launch from `/Applications`. Check that user-created files 
  are written outside the application directory.

### Code signing

Windows (PowerShell, from the extracted application directory):

```powershell
Get-AuthenticodeSignature .\WARPSimLab.exe
```

Verify `Valid` status and the expected signer. A paid Windows signing service is planned; setup details are pending.

macOS (on the installed application and downloaded DMG):

```bash
codesign --verify --deep --strict --verbose=2 /Applications/WARPSimLab.app
spctl --assess --type execute --verbose=4 /Applications/WARPSimLab.app
xcrun stapler validate WARPSimLab-vX.Y.Z-macOS-arm64.dmg
```

The intended release process is Developer ID signing, notarization and stapling. Verify Gatekeeper behavior using a normally downloaded copy. Signing and notarization are not yet configured; these commands are proposed verification steps.

### Security and checksums

- Scan the final Windows executable and ZIP with Microsoft Defender and VirusTotal; retain results and assess detections.
- Compare the final distribution hashes with the workflow-generated checksum file(s):

```powershell
Get-FileHash .\WARPSimLab-vX.Y.Z-Win-x86_64.zip -Algorithm SHA256
```

```bash
shasum -a 256 WARPSimLab-vX.Y.Z-macOS-arm64.dmg
```

Generate checksums after signing, notarization and stapling are complete. Do not alter the validated assets.

## 6. Publish

- Create a draft GitHub release for `vX.Y.Z`, titled `WARPSimLab vX.Y.Z`.
- Add release notes, Windows ZIP, macOS DMG and checksum file(s). GitHub generates the source archives.
- Verify the uploaded assets match the validated hashes, then publish.
- Update warpsimlab.org: version, release date, direct GitHub asset links, checksums, installation instructions, signing/security information and limitations. Update `sitemap.xml` only if URLs change.
- Test the public download links in a private browser window. Verify the downloaded files against the published checksums.
- Announce the release on Bogleheads and other project channels.
