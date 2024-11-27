
# SDK de Mercado Pago
import mercadopago

class Controller:

    def pagar(self):
        #credenciales vendedor
        #{"id":1145307387,"nickname":"TESTW4MEIAYK","password":"qatest8744","site_status":"active","email":"test_user_80875557@testuser.com"}
        # Agrega credenciales
        sdk = mercadopago.SDK("TEST-1806542489241268-061815-630c376f47340917ec1bcd617ee7c638-1143785844")
        # datos comprador
        
        # Crea un ítem en la preferencia
        preference_data = {
            "items": [
                {
                    "title": "Termografías",
                    "quantity": 1,
                    "unit_price": 15000
                }
            ],
            "back_url":{
                "success":"http://127.0.0.1:8000/",
                "failure":"http://127.0.0.1:8000/",
                "pending":"http://127.0.0.1:8000/"
            }
        }

        preference_response = sdk.preference().create(preference_data)
        #preference = preference_response["response"]
        return preference_response