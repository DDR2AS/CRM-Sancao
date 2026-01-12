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