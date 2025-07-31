from services.mongodb import DBMongo
import pandas as pd

class Pipelines:
    def __init__(self, database_service: DBMongo):
        self.mongo_service = database_service

    def getGastos(self):
        table_expenses = self.mongo_service.getGastos()
        return table_expenses
    
    def getSummaryByWeek(self):
        sum_expenses = self.mongo_service.getSummaryAmountGastos()
        sum_jornales = self.mongo_service.getSumaryAmountJornales()

        df_consolidado = pd.merge(sum_expenses,sum_jornales, on=['Fecha Inicio', 'Fecha Fin'], how='outer')
        return df_consolidado
    
    def postSentMoney(self,data: dict, file_info=None):
        print(data)
        self.mongo_service.uploadSendMoney(data)

    def getEnvios(self):
        table_sendMoney = self.mongo_service.getEnvios()
        print(table_sendMoney)
        return table_sendMoney