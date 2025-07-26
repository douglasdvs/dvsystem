import requests
from django.core.management.base import BaseCommand

from pedidos.models import Pedido

MELHOR_ENVIO_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiYzljZGE2NjM4Njk4NjljOGRhODA0NTQ1ZDg2NzgwMTg1MzRhNGUzOTA3YTg0MmM2NzUxMjQ0YjVmNDgzMGQ2NDcwMzRhMjc4MjFlZDQxZTIiLCJpYXQiOjE3NTE0MTExMDYuMzA5MzgsIm5iZiI6MTc1MTQxMTEwNi4zMDkzODIsImV4cCI6MTc4Mjk0NzEwNi4yOTU3NTYsInN1YiI6IjlkYjczMWQzLWZhZjItNDdlZi1hZDQzLTAyODZmZmIzZmI1OSIsInNjb3BlcyI6WyJjYXJ0LXJlYWQiLCJjYXJ0LXdyaXRlIiwiY29tcGFuaWVzLXJlYWQiLCJjb21wYW5pZXMtd3JpdGUiLCJjb3Vwb25zLXJlYWQiLCJjb3Vwb25zLXdyaXRlIiwibm90aWZpY2F0aW9ucy1yZWFkIiwib3JkZXJzLXJlYWQiLCJwcm9kdWN0cy1yZWFkIiwicHJvZHVjdHMtZGVzdHJveSIsInByb2R1Y3RzLXdyaXRlIiwicHVyY2hhc2VzLXJlYWQiLCJzaGlwcGluZy1jYWxjdWxhdGUiLCJzaGlwcGluZy1jYW5jZWwiLCJzaGlwcGluZy1jaGVja291dCIsInNoaXBwaW5nLWNvbXBhbmllcyIsInNoaXBwaW5nLWdlbmVyYXRlIiwic2hpcHBpbmctcHJldmlldyIsInNoaXBwaW5nLXByaW50Iiwic2hpcHBpbmctc2hhcmUiLCJzaGlwcGluZy10cmFja2luZyIsImVjb21tZXJjZS1zaGlwcGluZyIsInRyYW5zYWN0aW9ucy1yZWFkIiwidXNlcnMtcmVhZCIsInVzZXJzLXdyaXRlIiwid2ViaG9va3MtcmVhZCIsIndlYmhvb2tzLXdyaXRlIiwid2ViaG9va3MtZGVsZXRlIiwidGRlYWxlci13ZWJob29rIl19.HidxrBUg3vgU4L2WYBulzZc_V-L4shacC2g6v0SHMKB8xGg8wNrTr2RSMBnF26M1-Gggzd__o-AZZqC7QLDKnZcmurY390wIAgNwAF30Snp_g1eDBw4nz1hW4lUUbE9saFHzo87vt-rQN4WjAupo7Xm8c9_uytWtCdsnLVlG0vkp7CxzXiHt3GkRV27PMhh_lgB8-cLYI7LZwamEpEWYiQBBEnlqi_JgUQaX6DoibNhH4P07VsgZyIOUmESzr8WNLSXzNtBK_30Jwrig--vnC2md5BJz7_rnWrqfMZXOKYhQ258OUKAci9ZAmwr6HwjWbL3LpWszpkyI3gI00B9fOZu4qN5meRx-ROrUlgOkd2SJ8re3vMrNhbnkhyAQeduRgQXjUDY23fOSP3QGdcTkw3NW4t2SolakQgSuDdgZsqwslS30Hu8ALATrT2Y8I_dVnkeCdZGUHXYnX_Bjg7GLKCxsnZBl5YidNG_SQvr9m8Eh3bU9O_f8bLTutwHGZ4fqBKMOQvv5yaUdeL1tUacwawEkazfBQ-rgXNz_AukNYfwdivTwuUNDLaEdD-0_ULT9r7A2JykIS05fm6xRqLLl-1V4AyGp1c-rU4q-WTs7AHZLClnyAh1qTfboCUpfAPPgxUY4xWJxlWKrr8v5JtfotkKWvvj_746fpnVDF5U_qTk"


class Command(BaseCommand):
    help = "Sincroniza códigos de rastreio do Melhor Envio com os pedidos locais"

    def handle(self, *args, **kwargs):
        url = "https://api.melhorenvio.com.br/api/v2/me/shipments"
        headers = {
            "Authorization": f"Bearer {MELHOR_ENVIO_TOKEN}",
            "Accept": "application/json",
        }
        page = 1
        atualizados = 0
        while True:
            params = {
                "per_page": 100,
                "page": page,
            }
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f"Erro ao buscar envios: {response.text}"))
                break

            envios = response.json()
            if not envios:
                break

            for envio in envios:
                codigo_pedido = envio.get("code")  # O código de referência que você colocou ao criar a etiqueta!
                codigo_rastreio = envio.get("tracking")
                if codigo_pedido and codigo_rastreio:
                    try:
                        pedido = Pedido.objects.get(codigo=codigo_pedido)
                        if pedido.codigo_rastreio != codigo_rastreio:
                            pedido.codigo_rastreio = codigo_rastreio
                            pedido.save()
                            atualizados += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"Pedido {codigo_pedido}: atualizado código de rastreio para {codigo_rastreio}"
                                )
                            )
                    except Pedido.DoesNotExist:
                        continue
            page += 1
        self.stdout.write(self.style.SUCCESS(f"Sincronização concluída! Pedidos atualizados: {atualizados}"))
