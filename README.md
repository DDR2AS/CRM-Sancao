# Steps for deployment 

1. Rebuild .exe

Comando para compilar a `.exe` <br>
`Edit version.py to new version (e.g., 1.0.5)`
``` 
pip install pyinstaller
pyinstaller --onefile --windowed --icon=cacao_1.ico --name="CRM-Sancao" --add-data "keys;keys" app.py
``` 
2. Create a GitHub Release

  1. Go to: https://github.com/DDR2AS/CRM-Sancao/releases/new
  2. Tag: v1.0.5 (must match version.py)
  3. Title: v1.0.5
  4. Description: What changed
  5. Attach binary: Upload dist/CRM-Sancao.exe
  6. Click "Publish release"


3. Commit and push the new .exe
``` 
  git commit -m "build: update exe v1.0.x"
  git push origin main
``` 

   ---
  Version Numbering Guide
  ┌──────────────┬───────────────┐
  │ Change Type  │    Example    │
  ├──────────────┼───────────────┤
  │ Bug fix      │ 1.0.4 → 1.0.5 │
  ├──────────────┼───────────────┤
  │ New feature  │ 1.0.5 → 1.1.0 │
  ├──────────────┼───────────────┤
  │ Major change │ 1.1.0 → 2.0.0 │
  └──────────────┴───────────────┘