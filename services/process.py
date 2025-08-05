from services.drive_manager import GoogleService 
from services.mongodb import DBMongo
import pandas as pd
import threading
from datetime import datetime


class Pipelines:
    def __init__(self, database_service: DBMongo, google_service: GoogleService):
        self.mongo_service = database_service
        self.google_service = google_service

    def getGastos(self):
        table_expenses = self.mongo_service.getGastos()
        return table_expenses
    
    def getSummaryByWeek(self):
        sum_expenses = self.mongo_service.getSummaryAmountGastos()
        sum_jornales = self.mongo_service.getSumaryAmountJornales()
        sum_sendMoney = self.mongo_service.getSummaryAmountEnvios()

        df_consolidado = pd.merge(sum_expenses,sum_jornales, on=['Fecha Inicio', 'Fecha Fin'], how='outer')
        df_consolidado = pd.merge(df_consolidado,sum_sendMoney, on=['Fecha Inicio', 'Fecha Fin'], how='outer')
        return df_consolidado
    
    def postSentMoney(self, data: dict, file_info=None):
        def tarea():
            print(data)
            fecha = data["sentAt"]
            fecha_str = datetime.strptime(fecha[:10], "%Y-%m-%d")
            if file_info:
                try:
                    # Subir archivo al Drive y obtener ID y URL
                    resultado = self.google_service.uploadToDriveByDate(
                        fecha=fecha_str,
                        file_info=file_info
                    )
                    data["fileDriveId"] = resultado["id"]
                    data["fileDriveUrl"] = resultado["url"]

                except Exception as e:
                    print(f"Error al subir archivo a Drive: {e}")

            # Guardar en MongoDB
            self.mongo_service.uploadSendMoney(data)

            print("Envío guardado correctamente")

        threading.Thread(target=tarea, daemon=True).start()

    def getEnvios(self):
        table_sendMoney = self.mongo_service.getEnvios()
        print(table_sendMoney)
        return table_sendMoney
    
    def getJornales(self):
        table_jornales = self.mongo_service.getJornales()
        print(table_jornales)
        return table_jornales