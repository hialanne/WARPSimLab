# -*- mode: python ; coding: utf-8 -*-
# WARPSimLab.spec


a = Analysis(
    ['WARPSimLab.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/warpsimlab/dataFiles/financialMarketHistory.json', 'dataFiles'),
        ('src/warpsimlab/dataFiles/us_asset_returns_1876_2025.csv', 'dataFiles'),
        ('src/warpsimlab/dataFiles/us_inflation_1876_2025_real.csv', 'dataFiles'),
        ('src/warpsimlab/docs/getting_started.pdf', 'docs'),
        ('src/warpsimlab/docs/getting_started_advanced.pdf', 'docs'),
        ('src/warpsimlab/docs/faq.pdf', 'docs'),
        ('src/warpsimlab/exampleFiles/financialDataAverageSingle.json', 'exampleFiles'),
        ('src/warpsimlab/exampleFiles/financialDataAverageMarried.json', 'exampleFiles'),
        ('src/warpsimlab/exampleFiles/financialDataFiftiesSingle.json', 'exampleFiles'),
        ('src/warpsimlab/exampleFiles/financialDataFiftiesMarried.json', 'exampleFiles'),
        ('src/warpsimlab/exampleFiles/financialDataThirtiesSingle.json', 'exampleFiles'),
        ('src/warpsimlab/exampleFiles/financialDataThirtiesMarried.json', 'exampleFiles'),
        ('src/warpsimlab/exampleFiles/financialDataSeventiesSingle.json', 'exampleFiles'),
        ('src/warpsimlab/exampleFiles/financialDataSeventiesMarried.json', 'exampleFiles'),
        ('src/warpsimlab/exampleFiles/financialDataUpperSingle.json', 'exampleFiles'),
        ('src/warpsimlab/exampleFiles/financialDataUpperMarried.json', 'exampleFiles'),
        ('LICENSE.txt', '.'),
        ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WARPSimLab',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    contents_directory="Internal",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WARPSimLab',
)