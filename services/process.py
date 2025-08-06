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
        table_expenses["Fecha"] = table_expenses["Fecha"].dt.strftime("%Y-%m-%d")
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
            if file_info:
                try:
                    # Subir archivo al Drive y obtener ID y URL
                    resultado = self.google_service.uploadToDriveByDate(
                        fecha=fecha,
                        file_info=file_info
                    )
                    data["fileDriveId"] = resultado["id"]
                    data["fileDriveUrl"] = resultado["url"]

                except Exception as e:
                    print(f"Error al subir archivo a Drive: {e}")
            else:
                data["fileDriveId"] = ""
                data["fileDriveUrl"] = ""
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
    
    def getTransactions(self):
        table_expenses = self.mongo_service.getGastos()
        table_sendMoney = self.mongo_service.getEnvios()
        table_jornales = self.mongo_service.getJornales()

        # Formateando Tabla gastos
        table_expenses = table_expenses[['Fecha','Tipo','Producto','Actividad', 'Monto Total']].rename(columns={
            'Producto' : 'Nombre',
            'Monto Total' : 'Monto'
        })

        # Formateando Tabla Jornales
        table_jornales = table_jornales[['Fecha Trabajo','Tipo','Trabajador','Actividad','Monto Total']].rename(columns={
            'Fecha Trabajo' : 'Fecha',
            'Trabajador' : 'Nombre',
            'Monto Total' : 'Monto'
        })

        # Formateando Tabla Enviado
        table_sendMoney = table_sendMoney[['Fecha', 'Tipo','Descripcion', 'Monto Total']].rename(columns={
            'Descripcion' : 'Nombre',
            'Monto Total' : 'Enviado'
        }) 
        print(table_expenses.info())
        print(table_jornales.info())
        print(table_sendMoney.info())
        print(table_expenses)
        print(table_jornales)
        print(table_sendMoney)

        df_consolidado = pd.concat([table_expenses,table_jornales,table_sendMoney],axis=0)
        df_consolidado.sort_values(by='Fecha',ascending=True)
        df_consolidado['Actividad'] = df_consolidado['Actividad'].fillna('')
        print(df_consolidado)
        return df_consolidado
