from pymongo import MongoClient
from pymongo import ReturnDocument

from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import pandas as pd
import time
import os

class DBMongo:
    def __init__(self):
        load_dotenv() 
        self.srv = os.getenv("MONGO_URI")
        self.client = None

    def connect(self):
        try:
            start_time = time.time()
            self.client = MongoClient(self.srv, serverSelectionTimeoutMS=5000)
            self.client.admin.command("ping") 
            self.eiBusiness = self.client["eiBusiness"]
            end_time = time.time()
            print(f"Succesfull connection with DB-Sancao {end_time -start_time:.4f} s" )
        except Exception as e:
            print("Error al conectar a MongoDB:", e)
            self.client = None

    def getGastos(self):

        expenses = self.eiBusiness["expenses"].find({
        },
        {
            "_id" : 0,
            "Fecha" : "$datepurchasedAt",
            "Tipo" : "$type",
            "Producto" : "$product",
            "Descripcion" : "$description",
            "Monto Total" : "$amount",
            "Cantidad": "$quantity"
        }
        ).sort({"createdAt" : -1})
        df_expenses = pd.DataFrame(list(expenses))
        df_expenses["Fecha"] = pd.to_datetime(df_expenses["Fecha"], errors="coerce").dt.strftime("%Y-%m-%d")
        df_expenses["Monto Total"] = pd.to_numeric(df_expenses["Monto Total"], errors="coerce").fillna(0.0)
        df_expenses["Cantidad"] = pd.to_numeric(df_expenses["Cantidad"], errors="coerce").fillna(0.0)
        #print(df_expenses)
        return df_expenses
    
    def getSummaryAmountGastos(self):
        expenses = self.eiBusiness["expenses"].find(
            {},
            {
                "_id" : 0,
                "Fecha" : "$datepurchasedAt",
                "Producto" : "$product",
                "Monto Total" : "$amount"
        })
        
        df_expenses = pd.DataFrame(list(expenses))
        df_expenses["Fecha"] = pd.to_datetime(df_expenses["Fecha"], errors="coerce")
        df_expenses["Fecha"] = df_expenses["Fecha"].dt.tz_localize(None)
        df_expenses["Fecha Inicio"] = df_expenses["Fecha"].dt.to_period("W").apply(lambda r: r.start_time)
        df_expenses["Fecha Fin"] = df_expenses["Fecha"].dt.to_period("W").apply(lambda r: r.end_time)
        resumen_gastos = df_expenses.groupby(["Fecha Inicio", "Fecha Fin"]).agg({
            "Monto Total": "sum",
        }).rename(columns={'Monto Total': 'Gastos'}).reset_index()
        resumen_gastos["Fecha Inicio"] = resumen_gastos["Fecha Inicio"].dt.strftime("%Y-%m-%d")
        resumen_gastos["Fecha Fin"] = resumen_gastos["Fecha Fin"].dt.strftime("%Y-%m-%d")
        return resumen_gastos
    
    def getSumaryAmountJornales(self):
        jornales = self.eiBusiness['planilla_jornales'].find(
            {},
            {
                "_id" : 0,
                "Fecha" : "$date_journal",
                "Tipo" : "$type",
                "Monto Total" : "$amount"
            }
        )
        df_jornales = pd.DataFrame(list(jornales))
        df_jornales["Fecha"] = pd.to_datetime(df_jornales["Fecha"], errors="coerce")
        df_jornales["Fecha"] = df_jornales["Fecha"].dt.tz_localize(None)
        df_jornales["Fecha Inicio"] = df_jornales["Fecha"].dt.to_period("W").apply(lambda r: r.start_time)
        df_jornales["Fecha Fin"] = df_jornales["Fecha"].dt.to_period("W").apply(lambda r: r.end_time)
        resumen_jornal = df_jornales.groupby(["Fecha Inicio", "Fecha Fin"]).agg({
            "Monto Total": "sum",
        }).rename(columns={'Monto Total': 'Jornal'}).reset_index()
        resumen_jornal["Fecha Inicio"] = resumen_jornal["Fecha Inicio"].dt.strftime("%Y-%m-%d")
        resumen_jornal["Fecha Fin"] = resumen_jornal["Fecha Fin"].dt.strftime("%Y-%m-%d")
        resumen_jornal
        return resumen_jornal
    
    def uploadSendMoney(self, data: dict):
        PERU_TZ = timezone(timedelta(hours=-5))
        data["createdAt"] = datetime.now(PERU_TZ).isoformat()

        # Obtener el siguiente ID incremental desde la colección `counters`
        counter = self.eiBusiness["sendMoney_counter"].find_one_and_update(
            {"_id": "sendMoney"},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        # Generar ID con formato S00001, S00002, ...
        numero = counter["seq"]
        data["scode"] = f"S{numero:05d}"

        # Insertar en la colección principal
        result = self.eiBusiness["envios_dinero"].insert_one(data)
        
        # También actualizamos el campo s_code con el formato
        self.eiBusiness["sendMoney_counter"].update_one(
            {"_id": "sendMoney"},
            {"$set": {"s_code": f"S{numero:05d}"}}
        )
        return result
    
    def getEnvios(self):
        sendMoney = self.eiBusiness["envios_dinero"].find({
        },
        {
            "_id" : 0,
            "Monto Total" : "$amount",
            "COD" : "$scode",
            "Fecha" : "$sentAt",
            "Descripcion" : "$description"
        }
        ).sort({"createdAt" : -1})
        df_sendMoney = pd.DataFrame(list(sendMoney))
        df_sendMoney["Fecha"] = pd.to_datetime(df_sendMoney["Fecha"], errors="coerce")
        return df_sendMoney