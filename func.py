import io
import json
import logging
import requests 

from fdk import response
from utilidades.seguridad.core import verificarSeguridadMCU
from utilidades.seguridad.core import completarRequestSeguridad
from utilidades.errores.core import extraerErroresV2

def handler(ctx, data: io.BytesIO = None):
    logging.getLogger().info('***Q81PO_validarSeguridadCC **handler * INICIO')
    try:
        logging.getLogger().info('***Q81PO_validarSeguridadCC **handler * Ingresa try')
        cfg = ctx.Config()
        url = cfg["urlLogin"]
        params = json.loads(data.getvalue())

    except (Exception, ValueError) as ex:
        logging.getLogger().info('error parsing json payload: ' + str(ex))

    logging.getLogger().info('***Q81PO_validarSeguridadCC **handler * pre sendQuery')
    respuesta   = sendQuery(params, url, 'Q71PO_ORCH_ValidarSeguridadCC')
    respJson    = respuesta.json()
    logging.getLogger().info('***Q81PO_validarSeguridadCC **handler * respJson %s',respJson)

    if (respuesta.status_code == 444):
        logging.getLogger().info('***Q81PO_validarSeguridadCC **handler * Ingresa if status_code = 444')
        respJson = {
            "success"         : False,
            "rowset"          : [],
            "tokenExpirado"   : True,
            "data"            : None,
            "errorJde"        : True,
            "errorsList"      : []
        }
    else:
        logging.getLogger().info('***Q81PO_validarSeguridadCC **handler * Else del if status_code = 444')
        respJson    = procesarRespuesta(respJson, params['unidadNegocio'], params['seguridadInclusiva'] if 'seguridadInclusiva' in params else False,  params['seguridadCCActivada'] if 'seguridadCCActivada' in params else False)
  
    logging.getLogger().info('***Q81PO_validarSeguridadCC **handler * Fin')
    return response.Response(
        ctx, response_data=json.dumps(respJson),
        headers={"Content-Type": "application/json"}
    )

def sendQuery(params, urlOrc, orchestation):
    logging.getLogger().info('***Q81PO_validarSeguridadCC **sendQuery * Inicio')
    url = urlOrc + '/v3/orchestrator/' + orchestation
    jsonCompleto = completarRequestSeguridad(params,params["accionJDE"])
    logging.getLogger().info('***Q81PO_validarSeguridadCC **sendQuery * jsonCompleto %s',jsonCompleto)
    try:
        logging.getLogger().info('***Q81PO_validarSeguridadCC **sendQuery * ingresa try')
        resp = requests.post(url, json=jsonCompleto)
        logging.getLogger().info('***Q81PO_validarSeguridadCC **sendQuery * resp %s',resp)
    except Exception as e:
        resp = "Falló: " + str(e)

    logging.getLogger().info('***Q81PO_validarSeguridadCC **sendQuery * fin')
    return resp

def procesarRespuesta(respuesta, unidadNegocio, seguridadInclusiva, seguridadCCActivada):
    logging.getLogger().info('***Q81PO_validarSeguridadCC **procesarRespuesta * Inicio')
    try:

        if "jde__status" in respuesta:

            if respuesta["jde__status"].strip() in ["SUCCESS", "WARN"]:
                logging.getLogger().info('***Q81PO_validarSeguridadCC **procesarRespuesta * jde_status SUCCESS o WARN')
                rangoMCU = respuesta.get("rangoMCU", [])
                logging.getLogger().info("RANGO MCU: %s",json.dumps(rangoMCU))
                
                if seguridadCCActivada:
                    logging.getLogger().info('***Q81PO_validarSeguridadCC **procesarRespuesta * ingresa if seguridadCCActivada = true')
                    unidadNegocioOK = verificarSeguridadMCU(
                        unidadNegocio,
                        seguridadInclusiva,
                        rangoMCU
                    )

                else:
                    # Si la seguridad por CC no está activada,
                    # la unidad de negocio siempre es válida
                    logging.getLogger().info('***Q81PO_validarSeguridadCC **procesarRespuesta * ingresa else seguridadCCActivada = false')
                    unidadNegocioOK = True

                resultado = {
                    "success": True,
                    "tokenExpirado": False,
                    "data": {
                        "unidadNegocioOK": unidadNegocioOK
                    },
                    "errorJde": False,
                    "rowset": [],
                    "errorsList": []
                }

            else:
                logging.getLogger().info('***Q81PO_validarSeguridadCC **procesarRespuesta * ingresa else jde_status = ERROR')
                resultado = {
                    "success": False,
                    "tokenExpirado": False,
                    "data": None,
                    "errorJde": True,
                    "rowset": [],
                    "errorsList": procesarErrores(respuesta)
                }

        else:
            logging.getLogger().info('***Q81PO_validarSeguridadCC **procesarRespuesta * Ingresa else si jde_status no esta en la respuesta')
            resultado = {
                "success": False,
                "tokenExpirado": False,
                "data": None,
                "errorJde": True,
                "rowset": [],
                "errorsList": procesarErrores(respuesta)
            }

    except Exception as e:

        logging.getLogger().info(
            '** error procesarRespuesta: ' + str(e)
        )

        resultado = {
            "success": False,
            "tokenExpirado": False,
            "data": None,
            "errorJde": True,
            "rowset": [],
            "errorsList": [{
                "code": "999",
                "title": "ERROR",
                "desc": str(e)
            }]
        }

    logging.getLogger().info('***Q81PO_validarSeguridadCC **procesarRespuesta * fin: resultado %s',resultado)
    return resultado

def procesarErrores(respuesta):
    errorsList  = extraerErroresV2(respuesta) 
    logging.getLogger().info(errorsList)
    return errorsList