import os
import odoorpc
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from twilio.rest import Client

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

cat = odoo.env['product.category'].search_read(
    [('name', '=', 'PRODUCTO TERMINADO')], ['id'], limit=1
)
if not cat:
    raise SystemExit('Categoria "PRODUCTO TERMINADO" não encontrada.')
cat_id = cat[0]['id']

records = odoo.env['stock.quant'].search_read([
    ('location_id.usage', '=', 'internal'),
    ('quantity', '>', 0),
    ('product_id.categ_id', '=', cat_id),
    ('product_id.name', 'ilike', 'POD%'),
], ['product_id', 'quantity'])

estoque = {}
for r in records:
    _, nome = r['product_id']
    estoque[nome] = estoque.get(nome, 0) + int(r['quantity'])

# data para o relatório
hoje = datetime.now().strftime("%d/%m/%Y")

# ============================
# 3) Gerar PDF localmente
# ============================
pdf_path = 'report.pdf'
c = canvas.Canvas(pdf_path, pagesize=letter)
width, height = letter
y = height - 40

c.setFont('Helvetica-Bold', 14)
c.drawString(40, y, f"Relatório de Estoque POD — {hoje}")
y -= 30

c.setFont('Helvetica', 12)
if not estoque:
    c.drawString(40, y, "Nenhum produto 'POD' com estoque disponível.")
else:
    for nome in sorted(estoque):
        line = f"- {nome}: {estoque[nome]}"
        c.drawString(40, y, line)
        y -= 18
        if y < 50:            # nova página
            c.showPage()
            y = height - 40
            c.setFont('Helvetica', 12)

c.save()
print(f"✅ PDF gerado em {pdf_path}")

# ============================
# 4) Enviar PDF via WhatsApp
# ============================
# substitua abaixo pelo link RAW do seu PDF hospedado (Gist ou Pages)
file_url = (
    'https://gist.githubusercontent.com/marcoslatam/'
    '5ca5f12bcc14dc282c9faedd20221922/raw/'
    '90251728df93a4c4d23fc60dad113c1fbfac216d/report.pdf'
)

body = (
    f"*Produtos em estoque (POD)*\n"
    f"_Data: {hoje}_\n\n"
    "Segue em anexo o PDF completo com todos os itens."
)

client = Client(ACCOUNT_SID, AUTH_TOKEN)
msg = client.messages.create(
    body=body,
    from_=FROM_WHATS,
    to=TO_WHATS,
    media_url=[file_url]
)

print(f"✅ Mensagem única enviada! SID: {msg.sid}")
