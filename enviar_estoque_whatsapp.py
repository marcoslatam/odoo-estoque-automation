import os
import odoorpc
from twilio.rest import Client
from datetime import datetime

# ============================
# 1) Configurações via Secrets
# ============================
ODOO_HOST   = 'latamerp-15-0-6624961.dev.odoo.com'
ODOO_DB     = 'latamerp-15-0-6624961'
ODOO_USER   = os.environ['ODOO_USER']
ODOO_PASS   = os.environ['ODOO_PASS']

ACCOUNT_SID = os.environ['TWILIO_SID']
AUTH_TOKEN  = os.environ['TWILIO_TOKEN']
FROM_WHATS  = os.environ['TWILIO_FROM']  # ex: 'whatsapp:+14155238886'
TO_WHATS    = os.environ['TWILIO_TO']    # ex: 'whatsapp:+55SEUNUMERO'

# ============================
# 2) Conectar e buscar dados Odoo
# ============================
odoo = odoorpc.ODOO(ODOO_HOST, port=443, protocol='jsonrpc+ssl')
odoo.login(ODOO_DB, ODOO_USER, ODOO_PASS)

# pega o ID da categoria “PRODUCTO TERMINADO”
cat = odoo.env['product.category'].search_read(
    [('name', '=', 'PRODUCTO TERMINADO')], ['id'], limit=1
)
if not cat:
    raise SystemExit('Categoria "PRODUCTO TERMINADO" não encontrada.')
cat_id = cat[0]['id']

# busca quants internos com qty>0 e nome começando com POD
records = odoo.env['stock.quant'].search_read([
    ('location_id.usage', '=', 'internal'),
    ('quantity', '>', 0),
    ('product_id.categ_id', '=', cat_id),
    ('product_id.name', 'ilike', 'POD%'),
], ['product_id', 'quantity'])

# agrega quantidades por nome
estoque = {}
for r in records:
    _, nome = r['product_id']
    estoque[nome] = estoque.get(nome, 0) + int(r['quantity'])

# monta a data
hoje = datetime.now().strftime("%d/%m/%Y")

# ============================
# 3) Disparo único com anexo CSV via Gist
# ============================

# URL raw do seu CSV hospedado no Gist
file_url = (
    'https://gist.githubusercontent.com/marcoslatam/'
    '5ca5f12bcc14dc282c9faedd20221922/raw/'
    '90251728df93a4c4d23fc60dad113c1fbfac216d/report.csv'
)

# Corpo da mensagem (texto curto)
if not estoque:
    body = (
        f"*Produtos em estoque (POD)*\n"
        f"_Data: {hoje}_\n\n"
        "Nenhum produto 'POD' com estoque disponível.\n"
        "Veja o CSV em anexo."
    )
else:
    body = (
        f"*Produtos em estoque (POD)*\n"
        f"_Data: {hoje}_\n\n"
        "Segue em anexo o CSV completo com todos os itens."
    )

# cria cliente Twilio e dispara
client = Client(ACCOUNT_SID, AUTH_TOKEN)
msg = client.messages.create(
    body=body,
    from_=FROM_WHATS,
    to=TO_WHATS,
    media_url=[file_url]
)

print(f"✅ Mensagem única enviada! SID: {msg.sid}")
