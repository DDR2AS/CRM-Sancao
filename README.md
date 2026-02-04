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
  To Test the Update Feature

  1. On the deployed machine, open the app
  2. Go to Configuración
  3. Click "Verificar actualizaciones"
  4. If updates are found, click "Actualizar ahora"
  5. The app will pull changes and restart automatically

  ---
  For Future Releases

  When you release a new version:

  1. Edit version.py and change:
  APP_VERSION = "1.0.4"  # or whatever version
  2. Commit and push:
  git add version.py
  git commit -m "bump version to 1.0.4"
  git push origin main
  3. On deployed machines, users click "Verificar actualizaciones" → "Actualizar ahora"