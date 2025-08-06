from pymongo import MongoClient
from pymongo import ReturnDocument

from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from bson import ObjectId
import pandas as pd
import time
import os

PERU_TZ = timezone(timedelta(hours=-5))

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
            "Cantidad": "$quantity",
            "Actividad" : "$activity"
        }
        ).sort({"createdAt" : -1})
        df_expenses = pd.DataFrame(list(expenses))
        df_expenses["Fecha"] = pd.to_datetime(df_expenses["Fecha"], errors="coerce")
        df_expenses["Monto Total"] = pd.to_numeric(df_expenses["Monto Total"], errors="coerce").fillna(0.0)
        df_expenses["Cantidad"] = pd.to_numeric(df_expenses["Cantidad"], errors="coerce").fillna(0.0)
        return df_expenses
    
    def getJornales(self):
        jornals = self.eiBusiness["planilla_jornales"].find(
            {},
            {
                "_id" : 0,
                "Fecha Trabajo" : "$date_journal",
                "Trabajador" : "$fullname",
                "Monto Total": "$amount",
                "Actividad" : "$activity",
                "Tipo": "$type"
            }
            ).sort({"Fecha": -1})
        
        df_journals = pd.DataFrame(list(jornals))
        df_journals["Fecha Trabajo"] = pd.to_datetime(df_journals["Fecha Trabajo"], errors="coerce")
        df_journals["Monto Total"] = pd.to_numeric(df_journals["Monto Total"], errors="coerce").fillna(0.0)
        return df_journals
    
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
        return resumen_jornal
    
    def getSummaryAmountEnvios(self):
        sendMoney = self.eiBusiness['envios_dinero'].find({},
            {
                "_id" : 0,
                "Fecha" : "$sentAt",
                "Monto Total" : "$amount"
            }
        ).sort({"Fecha" : -1})
        df_sendMoney = pd.DataFrame(list(sendMoney))
        df_sendMoney["Fecha"] = pd.to_datetime(df_sendMoney["Fecha"], errors="coerce")
        df_sendMoney["Fecha"] = df_sendMoney["Fecha"].dt.tz_localize(None)
        df_sendMoney["Fecha Inicio"] = df_sendMoney["Fecha"].dt.to_period("W").apply(lambda r: r.start_time)
        df_sendMoney["Fecha Fin"] = df_sendMoney["Fecha"].dt.to_period("W").apply(lambda r: r.end_time)
        resumen_sendMoney = df_sendMoney.groupby(["Fecha Inicio", "Fecha Fin"]).agg({
            "Monto Total": "sum",
        }).rename(columns={'Monto Total': 'sendMoney'}).reset_index()
        resumen_sendMoney["Fecha Inicio"] = resumen_sendMoney["Fecha Inicio"].dt.strftime("%Y-%m-%d")
        resumen_sendMoney["Fecha Fin"] = resumen_sendMoney["Fecha Fin"].dt.strftime("%Y-%m-%d")
        return resumen_sendMoney

    
    def uploadSendMoney(self, data: dict):
        # ID del documento a actualizar
        _id = ObjectId(os.getenv('REGISTER_COUNT_ENV_ID'))

        # Obtener el siguiente número secuencial
        counter = self.eiBusiness["counter_collection"].find_one_and_update(
            {"_id": _id},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        # Crear el nuevo código S0000X
        numero = counter["seq"]
        data['s_code'] = f"S{numero:05d}"

        # Insertar en la colección principal
        result = self.eiBusiness["envios_dinero"].insert_one(data)

        # Update s_code en counter
        self.eiBusiness["counter_collection"].update_one(
            {"_id": _id},
            {"$set": {"s_code": f"S{numero:05d}"}}
        )
        return result
    
    def getEnvios(self):
        sendMoney = self.eiBusiness["envios_dinero"].find({
        },
        {
            "_id" : 0,
            "Tipo" : "$type",
            "Monto Total" : "$amount",
            "COD" : "$s_code",
            "Fecha" : "$sentAt",
            "Descripcion" : "$description",
            "Url" : "$fileDriveUrl"
        }
        ).sort({"Fecha" : -1})
        df_sendMoney = pd.DataFrame(list(sendMoney))
        df_sendMoney["Fecha"] = pd.to_datetime(df_sendMoney["Fecha"], errors="coerce")
        df_sendMoney["Monto Total"] = pd.to_numeric(df_sendMoney["Monto Total"], errors="coerce").fillna(0.0)
        return df_sendMoney