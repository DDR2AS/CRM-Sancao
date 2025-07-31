import os
import base64
import gspread
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from oauth2client.service_account import ServiceAccountCredentials

class GoogleService:
    def __init__(self):
        load_dotenv()
        self.scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        ruta_json = os.path.join(os.getcwd(), "keys", "google.json")
        print(f"Leyendo credenciales desde: {ruta_json}")
        
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(ruta_json, self.scopes)

        try:
            self.client = gspread.authorize(self.creds)
        except Exception as e:
            print(f"ERROR-AUTH-GOOGLE (gspread): {e}")
            self.client = None

        self.drive_service = build('drive', 'v3', credentials=self.creds)
        self.parentFolder_id_comprobantes = os.getenv("ID_COMPROBANTES_FOLDER_DRIVE")

        self.meses_es = [
            "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
            "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
        ]

    def getPathFolderByDates(self, fecha):
        PERU_TZ = timezone(timedelta(hours=-5))
        if isinstance(fecha, str):
            fecha = datetime.strptime(fecha, "%Y-%m-%d")
        fecha = fecha.replace(tzinfo=PERU_TZ)
        year = str(fecha.year)
        month = self.meses_es[fecha.month - 1]
        week = f"S{((fecha.day - 1) // 7 + 1)}"
        return f"{year}/{month}/{week}"
    
    def uploadToDriveByDate(self, fecha: str, file_info: dict):
        """
        Crea la ruta AÑO/MES/Sx en Drive basada en la fecha,
        sube el archivo y retorna un dict con ID y URL.
        """
        path = self.getPathFolderByDates(fecha)
        year, month, week = path.split("/")

        # Crear carpetas jerárquicamente
        carpeta_root = self.get_or_create_Folder("Comprobantes-n8n", "root")
        carpeta_year = self.get_or_create_Folder(year, carpeta_root["id"])
        carpeta_month = self.get_or_create_Folder(month, carpeta_year["id"])
        carpeta_week = self.get_or_create_Folder(week, carpeta_month["id"])

        # Crear archivo temporal
        filepath = f"out/temp_{file_info['nombre']}"
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(file_info["base64"]))

        try:
            # Subir archivo
            file_id = self.uploadToDrive(
                filepath_local=filepath,
                filename_drive=file_info["nombre"],
                id_parent_folder=carpeta_week["id"],
                mime_type=self.obtener_mime_type(file_info["tipo"])
            )
        finally:
            try:
                os.remove(filepath)
            except Exception as e:
                print(f"⚠️ No se pudo eliminar el archivo temporal: {e}")

        return {
            "id": file_id,
            "url": f"https://drive.google.com/file/d/{file_id}/view"
        }


    def uploadToDrive(self, filepath_local, filename_drive, id_parent_folder, mime_type="image/jpeg"):
        metadata = {
            'name': filename_drive,
            'parents': [id_parent_folder]
        }

        media = MediaFileUpload(filepath_local, mimetype=mime_type)

        file = self.drive_service.files().create(
            body=metadata,
            media_body=media,
            fields='id'
        ).execute()

        print(f"✅ Archivo subido con ID: {file['id']}")
        return file["id"]

    def get_or_create_Folder(self, nombre_carpeta, id_padre):
        carpetas = self.buscar_carpeta(nombre_carpeta, id_padre)
        if carpetas:
            print(f"📁 Carpeta encontrada: {carpetas[0]['name']} (ID: {carpetas[0]['id']})")
            return carpetas[0]
        else:
            nueva = self.crear_carpeta(nombre_carpeta, id_padre)
            print(f"📁 Carpeta creada: {nueva['name']} (ID: {nueva['id']})")
            return nueva

    def buscar_carpeta(self, nombre_carpeta, id_padre):
        query = f"""
            mimeType='application/vnd.google-apps.folder' and
            name='{nombre_carpeta}' and
            '{id_padre}' in parents and
            trashed=false
        """
        resultado = self.drive_service.files().list(
            q=query,
            spaces='drive',
            fields="files(id, name)"
        ).execute()
        return resultado.get("files", [])

    def crear_carpeta(self, nombre_carpeta, id_padre):
        metadata = {
            'name': nombre_carpeta,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [id_padre]
        }
        carpeta = self.drive_service.files().create(
            body=metadata,
            fields='id, name'
        ).execute()
        return carpeta

    def obtener_mime_type(self, tipo_archivo):
        tipos = {
            "jpg": "image/jpeg",
            "png": "image/png",
            "pdf": "application/pdf",
            "txt": "text/plain",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        return tipos.get(tipo_archivo.lower(), "application/octet-stream")
