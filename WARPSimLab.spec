# -*- mode: python ; coding: utf-8 -*-
# WARPSimLab.spec


a = Analysis(
    ['WARPSimLab.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('warp_sim/dataFiles/financialMarketHistory.json', 'dataFiles'),
        ('warp_sim/dataFiles/us_asset_returns_1876_2025.csv', 'dataFiles'),
        ('warp_sim/dataFiles/us_inflation_1876_2025_real.csv', 'dataFiles'),
        ('warp_sim/docs/getting_started.pdf', 'docs'),
        ('warp_sim/docs/getting_started_advanced.pdf', 'docs'),
        ('warp_sim/docs/faq.pdf', 'docs'),
        ('warp_sim/exampleFiles/financialDataAverage.json', 'exampleFiles'),
        ('warp_sim/exampleFiles/financialDataUpper.json', 'exampleFiles'),
        ('warp_sim/exampleFiles/financialDataThirties.json', 'exampleFiles'),
        ('warp_sim/exampleFiles/financialDataFifties.json', 'exampleFiles'),
        ('warp_sim/exampleFiles/financialDataSeventies.json', 'exampleFiles'),
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