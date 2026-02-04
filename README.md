# Steps for deployment 

1. Check current status
``` 
  git status 
  git commit -m "[feat] changes"
  git push origin main
``` 

2. Rebuild .exe

Comando para compilar a `.exe`
``` 
pip install pyinstaller
pyinstaller --onefile --windowed --icon=cacao_1.ico --name="CRM-Sancao" --add-data "keys;keys" app.py
``` 

3. Copy new .exe to root
``` 
  copy dist\CRM-Sancao.exe CRM-Sancao.exe
``` 

4. Commit and push the new .exe
``` 
  git add CRM-Sancao.exe
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