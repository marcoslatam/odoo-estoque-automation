import os
import odoorpc
from twilio.rest import Client
from datetime import datetime
import time

# ============================
# Configurações via Secrets
# ============================
USER        = os.environ['ODOO_USER']
PASSWORD    = os.environ['ODOO_PASS']
ACCOUNT_SID = os.environ['TWILIO_SID']
AUTH_TOKEN  = os.environ['TWILIO_TOKEN']
FROM_WHATS  = os.environ['TWILIO_FROM']  # ex: 'whatsapp:+14155238886'
TO_WHATS    = os.environ['TWILIO_TO']    # ex: 'whatsapp:+55SEUNUMERO'

# ============================
# Conectar e buscar dados Odoo
# ============================
odoo = odoorpc.ODOO('latamerp-15-0-6624961.dev.odoo.com', port=443, protocol='jsonrpc+ssl')
odoo.login('latamerp-15-0-6624961', USER, PASSWORD)

Category = odoo.env['product.category']
cat = Category.search_read([('name', '=', 'PRODUCTO TERMINADO')], ['id'], limit=1)
if not cat:
    raise SystemExit('Categoria "PRODUCTO TERMINADO" não encontrada.')
cat_id = cat[0]['id']

Quant = odoo.env['stock.quant']
records = Quant.search_read([
    ('location_id.usage', '=', 'internal'),
    ('quantity', '>', 0),
    ('product_id.categ_id', '=', cat_id),
    ('product_id.name', 'ilike', 'POD%'),
], ['product_id', 'quantity'])

# ============================
# Agregar quantidades
# ============================
estoque = {}
for r in records:
    _, nome = r['product_id']
    estoque.setdefault(nome, 0)
    estoque[nome] += int(r['quantity'])

# ============================
# Montar message_body
# ============================
hoje = datetime.now().strftime("%d/%m/%Y")
if not estoque:
    message_body = f"*Produtos em estoque (POD)*\n_Data: {hoje}_\n\nNenhum produto 'POD' com estoque disponível."
else:
    lines = ["*Produtos em estoque (POD)*", f"_Data: {hoje}_", ""]
    for nome in sorted(estoque):
        lines.append(f"- {nome}: {estoque[nome]}")
    message_body = "\n".join(lines)

# ============================
# Envio via Twilio com chunking
# ============================
client = Client(ACCOUNT_SID, AUTH_TOKEN)

MAX_LEN = 1600
chunks = []
if len(message_body) <= MAX_LEN:
    chunks = [message_body]
else:
    current = ""
    for line in message_body.split("\n"):
        # se a próxima linha ultrapassar o limite, finalize o chunk atual
        if len(current) + len(line) + 1 > MAX_LEN:
            chunks.append(current)
            current = line
        else:
            current = current + "\n" + line if current else line
    if current:
        chunks.append(current)

# enviar cada parte com atraso para não exceder rate limit
for idx, chunk in enumerate(chunks, 1):
    msg = client.messages.create(
        body=chunk,
        from_=FROM_WHATS,
        to=TO_WHATS,
    )
    print(f"✅ Parte {idx}/{len(chunks)} enviada! SID: {msg.sid}")
    time.sleep(1)  # pausa de 1s entre envios
