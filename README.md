## COMPILACIÓN
```
pip install pyinstaller
``` 
Comando para compilar a `.exe`
``` 
pyinstaller --onefile --noconsole --icon=cacao_1.ico --version-file=version.txt app.py 
``` 
Mejor versión
``` 
pyinstaller --onefile --windowed --icon=cacao_1.ico --name="CRM-Sancao" --add-data "keys;keys" app.py
``` 

# Deploy

  1. Check current status

  ``` 
  git status 
  ```

  2. Stage the files
```
  git add version.py ui/sidebar.py ui/configuracion.py ui/ViewSalesFrame.py
```
  3. Commit with a descriptive message
```
  git commit -m "feat: add auto-update feature and centralize version"
```
  4. Push to remote
```
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