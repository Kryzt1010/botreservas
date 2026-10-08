import requests
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


URL_LOOKUP = "https://crm-vikingos-radical-production.up.railway.app/api/v1/portal/lookup"
URL_BOOKING = "https://crm-vikingos-radical-production.up.railway.app/api/v1/portal/bookings"

EMAIL = "marcelitasoledad@gmail.com"

# ===== CONFIGURACIÓN =====

CLASE = "Factor F"
HORA = "09:00"


# Cada cuántos segundos vuelve a revisar
INTERVALO = 30

# Hora desde la que empieza a buscar
HORA_INICIO = "21:00"
SEGUNDOS_ANTES = 15       
MAX_HORAS_ESPERA = 4

# Hora máxima hasta la que seguirá buscando
HORA_FIN = "23:00"

# ==========================

def ahora_chile():
    return datetime.now(ZoneInfo("America/Santiago"))

def hora_de_hoy(hhmm):
    h, m = map(int, hhmm.split(":"))
    return ahora_chile().replace(hour=h, minute=m, second=0, microsecond=0)

def obtener_schedule():

    datos = {
        "email": EMAIL
    }

    try:
        respuesta = requests.post(URL_LOOKUP, json=datos, timeout=10)

        if respuesta.status_code != 200:
            print("Error en lookup:", respuesta.status_code)
            print(respuesta.text)
            return None

        return respuesta.json()

    except requests.RequestException as e:
        print("Error de conexión:", e)
        return None


def buscar_clase(datos,fecha):

    for dia in datos["schedule"]["days"]:

        if dia["date"] != fecha:
            continue

        for clase in dia["slots"]:

            if clase["title"] == CLASE and clase["start_time"] == HORA:
                return clase

    return None


def ya_esta_reservada(datos,fecha):

    for reserva in datos.get("my_bookings", []):

        if (
            reserva["booking_date"] == fecha
            and reserva["start_time"] == HORA
            and reserva["class_title"] == CLASE
        ):
            return True

    return False


def reservar_clase(clase):

    datos = {
        "email": EMAIL,
        "class_id": clase["class_id"],
        "booking_date": clase["date"]
    }

    try:

        respuesta = requests.post(
            URL_BOOKING,
            json=datos,
            timeout=10
        )

        print("\n==============================")
        print("       RESPUESTA RESERVA")
        print("==============================")

        print("Código:", respuesta.status_code)
        print(respuesta.text)

        if respuesta.status_code == 201:
            print("\n🎉 ¡RESERVA CONFIRMADA!")
            return True

        return False

    except requests.RequestException as e:

        print("Error al intentar reservar:", e)
        return False

def obtener_fecha_clase():
    hoy = ahora_chile()

    # Solo trabajamos domingo, martes y jueves
    if hoy.weekday() not in [1, 3, 6]:
        return None

    # La clase siempre es al día siguiente
    fecha_clase = hoy + timedelta(days=1)

    return fecha_clase.strftime("%Y-%m-%d")

def main():

    print("==============================")
    print("       BOT DE RESERVAS")
    print("==============================")

    print("Clase:", CLASE)
    print("Hora:", HORA)
    print("Revisión cada:", INTERVALO, "segundos")

    print("Buscará desde:", HORA_INICIO)
    print("Hasta:", HORA_FIN)

    while True:

        ahora = ahora_chile()
        dia = ahora.weekday()

        # --------------------------------
        # Comprobar si hoy corresponde
        # --------------------------------

        if dia not in [1, 3, 6]:
            print("\nHoy no corresponde buscar.")
            print("El bot termina.")
            break

        # --------------------------------
        # Calcular tiempos (hora Chile)
        # --------------------------------

        inicio = hora_de_hoy(HORA_INICIO)
        fin = hora_de_hoy(HORA_FIN)
        falta = (inicio - ahora).total_seconds()

        # Si faltan más de 4 horas, cerrar
        if falta > MAX_HORAS_ESPERA * 3600:
            print(f"\nFaltan más de {MAX_HORAS_ESPERA} horas para las {HORA_INICIO}.")
            print("El bot termina.")
            break

        # Si falta tiempo, dormir hasta 15 segundos antes
        if falta > SEGUNDOS_ANTES:
            espera = falta - SEGUNDOS_ANTES
            print(f"\nFaltan {int(falta // 60)} min para las {HORA_INICIO}.")
            print(f"Durmiendo {int(espera)} segundos...")
            time.sleep(espera)
            continue

        # Si ya pasó la hora final
        if ahora >= fin:
            print("\nHorario terminado.")
            print("El bot termina.")
            break

        # --------------------------------
        # Obtener fecha de la clase
        # --------------------------------

        FECHA = obtener_fecha_clase()

        if FECHA is None:
            print("No corresponde buscar hoy.")
            break

        # --------------------------------
        # Obtener información
        # --------------------------------

        datos = obtener_schedule()

        if datos is None:
            print("No se pudo obtener el schedule.")
            time.sleep(INTERVALO)
            continue

        # --------------------------------
        # Comprobar si ya está reservada
        # --------------------------------

        if ya_esta_reservada(datos, FECHA):

            print("\nYa tienes esta clase reservada.")
            print("Bot terminado.")
            break

        # --------------------------------
        # Buscar clase
        # --------------------------------

        clase = buscar_clase(datos, FECHA)

        if clase is None:

            print("\nNo se encontró la clase.")
            time.sleep(INTERVALO)
            continue

        # --------------------------------
        # Mostrar información
        # --------------------------------

        ahora = ahora_chile().strftime("%H:%M:%S")

        print(
            f"\n[{ahora}] "
            f"{clase['title']} "
            f"{clase['date']} "
            f"{clase['start_time']}"
        )

        print("Cupos disponibles:", clase["available"])
        print("Reservable:", clase["reservable"])

        # --------------------------------
        # Comprobar cupo
        # --------------------------------

        if clase["available"] <= 0:

            print("❌ Sin cupos.")
            print(
                "Volveré a revisar en",
                INTERVALO,
                "segundos."
            )

            time.sleep(INTERVALO)
            continue

        # --------------------------------
        # HAY CUPO → RESERVAR
        # --------------------------------

        print("\n🚨 ¡HAY CUPO!")
        print("Intentando reservar...")

        if reservar_clase(clase):
            break

        print("La reserva falló.")
        print("Volviendo a revisar...")

        time.sleep(INTERVALO)

if __name__ == "__main__":
    main()
