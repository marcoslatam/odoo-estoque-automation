# enviar_estoque_whatsapp.py

import os
import odoorpc
from twilio.rest import Client
from datetime import datetime

# Carrega credenciais do GitHub Secrets
USER         = os.environ['ODOO_USER']
PASSWORD     = os.environ['ODOO_PASS']
ACCOUNT_SID  = os.environ['TWILIO_SID']
AUTH_TOKEN   = os.environ['TWILIO_TOKEN']
FROM_WHATS   = os.environ['TWILIO_FROM']   # ex: 'whatsapp:+14155238886'
TO_WHATS     = os.environ['TWILIO_TO']     # ex: 'whatsapp:+55SEUNUMERO'

# ----- busca dados no Odoo e monta message_body (igual ao seu imprimir_message_body.py) -----
HOST, PORT, PROTO = 'latamerp-15-0-6624961.dev.odoo.com', 443, 'jsonrpc+ssl'
odoo = odoorpc.ODOO(HOST, port=PORT, protocol=PROTO)
odoo.login('latamerp-15-0-6624961', USER, PASSWORD)

Category = odoo.env['product.category']
cat = Category.search_read([('name', '=', 'PRODUCTO TERMINADO')], ['id'], limit=1)
cat_id = cat[0]['id']

Quant = odoo.env['stock.quant']
records = Quant.search_read([
    ('location_id.usage', '=', 'internal'),
    ('quantity', '>', 0),
    ('product_id.categ_id', '=', cat_id),
    ('product_id.name', 'ilike', 'POD%'),
], ['product_id', 'quantity'])

estoque = {}
for r in records:
    _, nome = r['product_id']
    estoque.setdefault(nome, 0)
    estoque[nome] += int(r['quantity'])

hoje = datetime.now().strftime("%d/%m/%Y")
if not estoque:
    message_body = f"*Produtos em estoque (POD)*\n_Data: {hoje}_\n\nNenhum produto 'POD' com estoque disponível."
else:
    lines = ["*Produtos em estoque (POD)*", f"_Data: {hoje}_", ""]
    for nome in sorted(estoque):
        lines.append(f"- {nome}: {estoque[nome]}")
    message_body = "\n".join(lines)

# ----- envia via Twilio -----
client = Client(ACCOUNT_SID, AUTH_TOKEN)
msg = client.messages.create(
    body=message_body,
    from_=FROM_WHATS,
    to=TO_WHATS,
)
print(f"✅ WhatsApp enviado! SID: {msg.sid}")
