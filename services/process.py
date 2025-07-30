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