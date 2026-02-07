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
            self.eiAccounts = self.client["eiAccounts"]
            end_time = time.time()
            print(f"Succesfull connection with DB-Sancao {end_time -start_time:.4f} s" )
        except Exception as e:
            print("Error al conectar a MongoDB:", e)
            self.client = None

    def getGastos(self):

        pipeline = [
            {
                "$lookup": {
                    "from": "attachments",
                    "localField": "attachmentId",
                    "foreignField": "_id",
                    "as": "attachment"
                }
            },
            {
                "$addFields": {
                    "attachmentUrl": {
                        "$ifNull": [
                            {"$arrayElemAt": ["$attachment.url", 0]},
                            "$fileDriveUrl"
                        ]
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "COD": "$e_code",
                    "Fecha": "$datepurchasedAt",
                    "Tipo": "$type",
                    "Producto": "$product",
                    "Descripcion": "$description",
                    "Monto Total": "$amount",
                    "Cantidad": "$quantity",
                    "Actividad": "$activity",
                    "Responsable": "$createdBy",
                    "Url": "$attachmentUrl"
                }
            },
            {"$sort": {"Fecha": -1}}
        ]

        result = self.eiBusiness["expenses"].aggregate(pipeline)
        df_expenses = pd.DataFrame(list(result))

        # Handle empty DataFrame - ensure columns exist
        expected_columns = ["COD", "Fecha", "Tipo", "Producto", "Descripcion", "Monto Total", "Cantidad", "Actividad", "Responsable", "Url"]
        if df_expenses.empty:
            df_expenses = pd.DataFrame(columns=expected_columns)

        df_expenses["Fecha"] = pd.to_datetime(df_expenses["Fecha"], errors="coerce")
        df_expenses["Monto Total"] = pd.to_numeric(df_expenses["Monto Total"], errors="coerce")
        df_expenses["Cantidad"] = pd.to_numeric(df_expenses["Cantidad"], errors="coerce")
        return df_expenses
    
    def getJornales(self):
        # Obteniendo los usuarios registrados
        users = self.eiAccounts["res_users"].find(
            {
                "role": { "$in": ["worker", "supervisor_pro"] }
            },
            {
                "_id" : 0,
                "fullname" : "$name",
                "u_code" : 1
            }
        )
        df_users = pd.DataFrame(list(users))

        jornals = self.eiBusiness["planilla_jornales"].find(
            {},
            {
                "_id" : 0,
                "Fecha Trabajo" : "$date_journal",
                "Trabajador" : "$fullname",
                "Descripcion" : "$description",
                "u_code" : "$u_code_worker",
                "Monto Total": "$amount",
                "Actividad" : "$activity",
                "COD" : "$j_code",
                "Tipo": "$type",
                "Periodo" : "$payroll_type",
                "Responsable" : "$createdBy"
            }
            ).sort({"Fecha": -1})
        
        df_journals = pd.DataFrame(list(jornals))

        # Handle empty DataFrame - ensure columns exist
        expected_columns = ["Fecha Trabajo", "Trabajador", "Descripcion", "u_code", "Monto Total", "Actividad", "COD", "Tipo", "Periodo", "Responsable"]
        if df_journals.empty:
            df_journals = pd.DataFrame(columns=expected_columns)

        # Concatenando con nueva data
        df_merged = df_journals.merge(df_users, on='u_code', how='left')
        if 'fullname' in df_merged.columns:
            df_merged['Trabajador'] = df_merged['Trabajador'].fillna(df_merged['fullname'])
            df_merged = df_merged.drop(columns=['fullname'], errors='ignore')
        if 'u_code' in df_merged.columns:
            df_merged = df_merged.drop(columns=['u_code'], errors='ignore')

        df_merged["Fecha Trabajo"] = pd.to_datetime(df_merged["Fecha Trabajo"], errors="coerce")
        df_merged["Monto Total"] = pd.to_numeric(df_merged["Monto Total"], errors="coerce").fillna(0.0)
        return df_merged
    
    def getSales(self):
        pipeline = [
            {
                "$lookup": {
                    "from": "attachments",
                    "localField": "attachmentId",
                    "foreignField": "_id",
                    "as": "attachment"
                }
            },
            {
                "$addFields": {
                    "attachmentUrl": {
                        "$ifNull": [
                            {"$arrayElemAt": ["$attachment.url", 0]},
                            "$fileDriveUrl"
                        ]
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "Fecha Venta": "$saleAt",
                    "Producto": "$product",
                    "Peso": "$weight",
                    "PrecioxKg": "$price_by_kg",
                    "Monto": "$amount",
                    "COD": "$v_code",
                    "Tipo": "$type",
                    "Responsable": "$createdBy",
                    "Url": "$attachmentUrl"
                }
            },
            {"$sort": {"Fecha Venta": -1}}
        ]

        result = self.eiBusiness["sales"].aggregate(pipeline)
        df_sales = pd.DataFrame(list(result))

        # Handle empty DataFrame - ensure columns exist
        expected_columns = ["Fecha Venta", "Producto", "Peso", "PrecioxKg", "Monto", "COD", "Tipo", "Responsable", "Url"]
        if df_sales.empty:
            df_sales = pd.DataFrame(columns=expected_columns)

        df_sales["Fecha Venta"] = pd.to_datetime(df_sales["Fecha Venta"], errors="coerce")
        return df_sales
    
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
    
    def getSummaryAmountJornales(self):
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
            "Url" : "$fileDriveUrl",
            "Responsable" : "$createdBy"
        }
        ).sort({"Fecha" : -1})
        df_sendMoney = pd.DataFrame(list(sendMoney))

        # Handle empty DataFrame - ensure columns exist
        expected_columns = ["Tipo", "Monto Total", "COD", "Fecha", "Descripcion", "Url", "Responsable"]
        if df_sendMoney.empty:
            df_sendMoney = pd.DataFrame(columns=expected_columns)

        df_sendMoney["Fecha"] = pd.to_datetime(df_sendMoney["Fecha"], errors="coerce")
        df_sendMoney["Monto Total"] = pd.to_numeric(df_sendMoney["Monto Total"], errors="coerce").fillna(0.0)
        return df_sendMoney
    
    def update_Expenses(self, e_code: str, data):
        field_map = {
            "COD": "e_code",
            "Fecha": "datepurchasedAt",
            "Tipo": "type",
            "Producto": "product",
            "Descripción": "description",
            "Monto Total": "amount",
            "Cantidad": "quantity",
            "Actividad": "activity"
            # Url/fileDriveUrl deprecated - attachments are now stored in attachments collection
        }
        update_doc = {}
        for key, value in data.items():
            if key in field_map:
                mongo_field = field_map[key]

                # Conversión de tipos
                if key == "Monto Total" or key == "Cantidad":
                    try:
                        update_doc[mongo_field] = float(value)
                    except ValueError:
                        update_doc[mongo_field] = 0.0

                else:
                    update_doc[mongo_field] = value

        print(f"update doc : {update_doc}")
        # Ejecutar actualización
        result = self.eiBusiness["expenses"].update_one(
            {"e_code": e_code},
            {"$set": update_doc}           
        )
        return result
    
    def delete_Expense(self, e_code: str): 
        try:
            result = self.eiBusiness["expenses"].delete_one({"e_code": e_code})
            if result.deleted_count > 0:
                print(f"Gasto con COD={e_code} eliminado.")
                return True
            else:
                print(f"No se encontró gasto con COD={e_code}.")
                return False
        except Exception as e:
            print("Error en eliminar registro:", e)
            return False
        
    def update_Sales(self, v_code: str, data):
        field_map = {
            "COD": "v_code",
            "Fecha Venta": "saleAt",
            "Tipo": "type",
            "Producto": "product",
            "Monto (S/)": "amount",
            "Precio x Kg": "price_by_kg",
            "Peso (kg)": "weight",
            "Url": "fileDriveUrl",
            "fileDriveId": "fileDriveId"
        }

        update_doc = {}
        for key, value in data.items():
            if key in field_map:
                mongo_field = field_map[key]

                # Conversión de tipos solo para campos numéricos
                if key in ["Monto (S/)", "Peso (kg)", "Precio x Kg"]:
                    try:
                        update_doc[mongo_field] = float(value)
                    except (ValueError, TypeError):
                        update_doc[mongo_field] = 0.0
                else:
                    update_doc[mongo_field] = value

        print(f"update doc : {update_doc}")

        # Ejecutar actualización
        result = self.eiBusiness["sales"].update_one(
            {"v_code": v_code},
            {"$set": update_doc}
        )
        return result

    def delete_Sales(self, v_code: str): 
        try:
            result = self.eiBusiness["sales"].delete_one({"v_code": v_code})
            if result.deleted_count > 0:
                print(f"Venta con COD={v_code} eliminado.")
                return True
            else:
                print(f"No se encontró venta con COD={v_code}.")
                return False
        except Exception as e:
            print("Error en eliminar registro:", e)
            return False
        
    def update_SendMoney(self, s_code: str, data):
        field_map = {
                "COD": "s_code",
                "Fecha envío": "sentAt",
                "Descripción" : "description",
                "Tipo": "type",
                "Monto (S/)": "amount",
                "Url": "fileDriveUrl",
                "fileDriveId": "fileDriveId"
            }

        update_doc = {}
        for key, value in data.items():
            if key in field_map:
                mongo_field = field_map[key]
            # Conversión de tipos solo para campos numéricos
            if key in ["Monto (S/)"]:
                try:
                    update_doc[mongo_field] = float(value)
                except (ValueError, TypeError):
                    update_doc[mongo_field] = 0.0
            else:
                update_doc[mongo_field] = value
        # Ejecutar actualización
        result = self.eiBusiness["envios_dinero"].update_one(
            {"s_code": s_code},
            {"$set": update_doc}
        )
        return result
    
    def delete_SendMoney(self, s_code: str): 
        try:
            result = self.eiBusiness["envios_dinero"].delete_one({"s_code": s_code})
            if result.deleted_count > 0:
                print(f"Venta con COD={s_code} eliminado.")
                return True
            else:
                print(f"No se encontró venta con COD={s_code}.")
                return False
        except Exception as e:
            print("Error en eliminar registro:", e)
            return False
        
    def update_Jornal(self, j_code: str, data):
        field_map = {
                "COD": "j_code",
                "Fecha Trabajo": "date_journal",
                "Actividad" : "activity",
                "Descripción" : "description",
                "Monto Total": "amount",
                "Trabajador" : "fullname",
                "Tipo" : "payroll_type"
            }

        update_doc = {}
        for key, value in data.items():
            if key in field_map:
                mongo_field = field_map[key]
            # Conversión de tipos solo para campos numéricos
            if key in ["Monto Total"]:
                try:
                    update_doc[mongo_field] = float(value)
                except (ValueError, TypeError):
                    update_doc[mongo_field] = 0.0
            else:
                update_doc[mongo_field] = value
        # Ejecutar actualización
        result = self.eiBusiness["planilla_jornales"].update_one(
            {"j_code": j_code},
            {"$set": update_doc}
        )
        return result
    
    def delete_Jornal(self, j_code: str):
        try:
            result = self.eiBusiness["planilla_jornales"].delete_one({"j_code": j_code})
            if result.deleted_count > 0:
                print(f"Venta con COD={j_code} eliminado.")
                return True
            else:
                print(f"No se encontró venta con COD={j_code}.")
                return False
        except Exception as e:
            print("Error en eliminar registro:", e)
            return False

    # ==================== PRODUCCION ====================

    def getProduccion(self):
        pipeline = [
            {
                "$lookup": {
                    "from": "attachments",
                    "localField": "attachmentId",
                    "foreignField": "_id",
                    "as": "attachment"
                }
            },
            {
                "$addFields": {
                    "attachmentUrl": {
                        "$ifNull": [
                            {"$arrayElemAt": ["$attachment.url", 0]},
                            None
                        ]
                    }
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "COD": "$p_code",
                    "Fecha": "$registerAt",
                    "Lugar": "$origin_place",
                    "N° Baldes": "$amount_buckets",
                    "Tipo Balde": "$bucket_type",
                    "Peso (kg)": "$weight",
                    "Estado": "$status",
                    "Responsable": "$createdBy",
                    "Url": "$attachmentUrl"
                }
            },
            {"$sort": {"Fecha": -1}}
        ]

        result = self.eiBusiness["production_cacao"].aggregate(pipeline)
        df_produccion = pd.DataFrame(list(result))

        df_produccion["Fecha"] = pd.to_datetime(df_produccion["Fecha"], errors="coerce")
        df_produccion["Peso (kg)"] = pd.to_numeric(df_produccion["Peso (kg)"], errors="coerce").fillna(0)
        df_produccion["N° Baldes"] = pd.to_numeric(df_produccion["N° Baldes"], errors="coerce").fillna(0)
        return df_produccion

    # ==================== ATTACHMENTS ====================

    def create_attachment(self, attachment_data: dict) -> ObjectId:
        """
        Create a new attachment record.

        Args:
            attachment_data: dict with url, fileGsUrl, mimeType, fileSize, recordType, recordCode

        Returns:
            ObjectId of the created attachment
        """
        now = datetime.now(PERU_TZ)
        attachment_data["createdAt"] = now
        attachment_data["updatedAt"] = now

        result = self.eiBusiness["attachments"].insert_one(attachment_data)
        print(f"Attachment created: {result.inserted_id}")
        return result.inserted_id

    def update_expense_attachment(self, e_code: str, attachment_id: ObjectId):
        """
        Update expense record with attachmentId.

        Args:
            e_code: Expense code (e.g., "E00035")
            attachment_id: ObjectId of the attachment
        """
        result = self.eiBusiness["expenses"].update_one(
            {"e_code": e_code},
            {"$set": {"attachmentId": attachment_id, "updatedAt": datetime.now(PERU_TZ)}}
        )
        print(f"Expense {e_code} updated with attachmentId: {attachment_id}")
        return result

    def get_attachment_by_id(self, attachment_id: ObjectId) -> dict:
        """Get attachment by ID."""
        return self.eiBusiness["attachments"].find_one({"_id": attachment_id})

    def update_attachment(self, attachment_id: ObjectId, attachment_data: dict):
        """
        Update an existing attachment record.

        Args:
            attachment_id: ObjectId of the attachment to update
            attachment_data: dict with url, fileGsUrl, mimeType, fileSize, etc.
        """
        attachment_data["updatedAt"] = datetime.now(PERU_TZ)
        result = self.eiBusiness["attachments"].update_one(
            {"_id": attachment_id},
            {"$set": attachment_data}
        )
        print(f"Attachment {attachment_id} updated")
        return result

    def get_expense_by_code(self, e_code: str) -> dict:
        """Get expense by code."""
        return self.eiBusiness["expenses"].find_one({"e_code": e_code})

    def get_sale_by_code(self, v_code: str) -> dict:
        """Get sale by code."""
        return self.eiBusiness["sales"].find_one({"v_code": v_code})

    def update_sale_attachment(self, v_code: str, attachment_id: ObjectId):
        """
        Update sale record with attachmentId.

        Args:
            v_code: Sale code (e.g., "V00035")
            attachment_id: ObjectId of the attachment
        """
        result = self.eiBusiness["sales"].update_one(
            {"v_code": v_code},
            {"$set": {"attachmentId": attachment_id, "updatedAt": datetime.now(PERU_TZ)}}
        )
        print(f"Sale {v_code} updated with attachmentId: {attachment_id}")
        return result

    def delete_attachment(self, attachment_id: ObjectId) -> bool:
        """Delete attachment by ID."""
        try:
            result = self.eiBusiness["attachments"].delete_one({"_id": attachment_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting attachment: {e}")
            return False