
# SDK de Mercado Pago
import mercadopago

class Controller:

    def pagar(self):
        
        
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
