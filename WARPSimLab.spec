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
        ('src/warpsimlab/exampleFiles/financialDataAverage.json', 'exampleFiles'),
        ('src/warpsimlab/exampleFiles/financialDataUpper.json', 'exampleFiles'),
        ('src/warpsimlab/exampleFiles/financialDataThirties.json', 'exampleFiles'),
        ('src/warpsimlab/exampleFiles/financialDataFifties.json', 'exampleFiles'),
        ('src/warpsimlab/exampleFiles/financialDataSeventies.json', 'exampleFiles'),
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