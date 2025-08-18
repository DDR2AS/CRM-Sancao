from services.drive_manager import GoogleService 
from datetime import datetime, timedelta, timezone
from services.mongodb import DBMongo
import pandas as pd
import threading


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
    
    def uploadFile(self, file_info=None):
        data = {"fileDriveId": "", "fileDriveUrl": ""}
        if file_info:
            try:
                tz = timezone(timedelta(hours=-5))
                upload_with_time = datetime.now(tz)
                uploadDate = upload_with_time.strftime("%Y-%m-%d")
                resultado = self.google_service.uploadToDriveByDate(
                    fecha=uploadDate,
                    file_info=file_info
                )
                data["fileDriveId"] = resultado.get("id", "")
                data["fileDriveUrl"] = resultado.get("url", "")
            except Exception as e:
                print(f"Error al subir archivo a Drive: {e}")
        return data

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
        #print(table_sendMoney)
        return table_sendMoney
    
    def getJornales(self):
        table_jornales = self.mongo_service.getJornales()
        #print(table_jornales)
        return table_jornales
    
    def getTransactions(self):
        table_expenses = self.mongo_service.getGastos()
        table_sendMoney = self.mongo_service.getEnvios()
        table_jornales = self.mongo_service.getJornales()
        #table_sales = self.mongo_service.getSales()
        
        # Formateando Tabla gastos
        # Filtrar abonos
        df_abono = table_expenses[table_expenses['Producto'] == 'Abono'][['Fecha','Tipo','Producto','Actividad','Descripcion','Monto Total']].rename(columns={'Producto': 'Nombre', 'Monto Total': 'GastoAbono'})
        # Filtrar los demás gastos
        df_gastos = table_expenses[table_expenses['Producto'] != 'Abono'][['Fecha','Tipo','Producto','Actividad','Descripcion','Monto Total']].rename(columns={'Producto': 'Nombre', 'Monto Total': 'Monto'})

        # Formateando Tabla Jornales
        table_jornales = table_jornales[['Fecha Trabajo','Tipo','Trabajador','Actividad','Monto Total']].rename(columns={
            'Fecha Trabajo' : 'Fecha',
            'Trabajador' : 'Nombre',
            'Monto Total' : 'Jornal'
        })

        # Formateando Tabla Enviado
        table_sendMoney = table_sendMoney[['Fecha', 'Tipo','Descripcion', 'Monto Total']].rename(columns={
            'Descripcion' : 'Nombre',
            'Monto Total' : 'Enviado'
        }) 
        df_consolidado = pd.concat([df_gastos,df_abono,table_jornales,table_sendMoney],axis=0)
        df_consolidado.sort_values(by='Fecha',ascending=True)
        df_consolidado['Actividad'] = df_consolidado['Actividad'].fillna('')
        return df_consolidado

    def updateExpenses(self, e_code, data):
        self.mongo_service.update_Expenses(e_code,data)
        return True

    def deleteExpense(self, e_code):
        self.mongo_service.delete_Expense(e_code)
        return True

    def getSales(self):
        table_sales = self.mongo_service.getSales()
        print(table_sales)
        return table_sales
    
    def updateSale(self, v_code, data):
        print(data)
        self.mongo_service.update_Sales(v_code,data)
        return True

    def deleteSale(self, v_code):
        self.mongo_service.delete_Sales(v_code)
        return True
    
    def updateSendMoney(self, s_code, data):
        print(data)
        self.mongo_service.update_SendMoney(s_code,data)
        return True

    def deleteSendMoney(self, s_code):
        self.mongo_service.delete_SendMoney(s_code)
        return True