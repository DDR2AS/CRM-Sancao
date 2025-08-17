from oauth2client.service_account import ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build

from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import base64
import gspread
import time
import os

class GoogleService:
    def __init__(self):
        load_dotenv()
        self.email_oauth = os.getenv("EMAIL_OAUTH")
        self.scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        ruta_json = os.path.join(os.getcwd(), "keys", "google.json")
        print(f"Leyendo credenciales desde: {ruta_json}")
        
        # Inicialización de credenciales
        self.creds_service = ServiceAccountCredentials.from_json_keyfile_name(ruta_json, self.scopes)
        self.creds_oauth = self.autenticar_oauth_user()

        # Servicio de Google Sheets
        try:
            self.client = gspread.authorize(self.creds_service)
        except Exception as e:
            print(f"ERROR-AUTH-GOOGLE (gspread): {e}")
            self.client = None

        # Servicios de Google Drive
        self.drive_service = build('drive', 'v3', credentials=self.creds_service)
        self.oauth_drive = build('drive', 'v3', credentials=self.creds_oauth)

        self.parentFolder_id_comprobantes = os.getenv("ID_COMPROBANTES_FOLDER_DRIVE")

        self.meses_es = [
            "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
            "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
        ]

    def autenticar_oauth_user(self):
        token_path = "keys/token-oauth.json"
        client_secret_path = "keys/oauth-google.json"
        creds = None

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, self.scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, self.scopes)
                creds = flow.run_local_server(port=0)

            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        return creds

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
        path = self.getPathFolderByDates(fecha)
        year, month, _ = path.split("/")

        carpeta_root = self.get_or_create_Folder("Comprobantes-n8n", "root")
        
        # Crear carpeta del mes con el nombre formato: JULIO-2025
        nombre_mes = f"{month}-{year}"
        carpeta_mes_anio = self.get_or_create_Folder(nombre_mes, carpeta_root["id"])

        # Compartir carpeta con el usuario OAuth
        email_usuario = self.get_oauth_user_email()
        if email_usuario:
            self.shareFolderwithOauth(carpeta_mes_anio["id"], email_usuario)

        # Guardar archivo temporal
        filepath = f"out/temp_{file_info['nombre']}"
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(file_info["base64"]))

        try:
            file_id = self.uploadToDrive(
                filepath_local=filepath,
                filename_drive=file_info["nombre"],
                id_parent_folder=carpeta_mes_anio["id"],
                id_subfolder=carpeta_mes_anio["id"],
                mime_type=self.obtener_mime_type(file_info["tipo"])
            )
        finally:
            try:
                time.sleep(0.5)
                os.remove(filepath)
            except Exception as e:
                print(f"No se pudo eliminar el archivo temporal: {e}")

        return {
            "id": file_id,
            "url": f"https://drive.google.com/file/d/{file_id}/view"
        }

    def uploadToDrive(self, filepath_local, filename_drive, id_parent_folder, id_subfolder=None, mime_type="image/jpeg"):
        parent_id = id_subfolder or id_parent_folder

        if not parent_id:
            raise ValueError("Debe proporcionarse al menos un folder ID.")

        archivo_metadata = {
            'name': filename_drive,
            'parents': [parent_id]
        }

        media = MediaFileUpload(filepath_local, mimetype=mime_type)

        archivo = self.oauth_drive.files().create(
            body=archivo_metadata,
            media_body=media,
            fields='id'
        ).execute()

        print(f"Archivo subido con ID: {archivo.get('id')}")
        return archivo.get('id')

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
            q=query.strip(),
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

    def shareFolderwithOauth(self, folder_id, user_mail=None):
        user_mail=self.email_oauth
        try:
            permiso = {
                'type': 'user',
                'role': 'writer',
                'emailAddress': user_mail
            }

            self.drive_service.permissions().create(
                fileId=folder_id,
                body=permiso,
                sendNotificationEmail=False
            ).execute()

            print(f"Carpeta {folder_id} compartida con {user_mail}")
        except Exception as e:
            print(f"Error al compartir carpeta: {e}")

    def get_oauth_user_email(self):
        try:
            info = self.oauth_drive.about().get(fields="user(emailAddress)").execute()
            return info['user']['emailAddress']
        except Exception as e:
            print(f"No se pudo obtener correo del usuario OAuth: {e}")
            return None
