import odoorpc
from datetime import datetime

# ============================
# 1) Configurações Odoo
# ============================
HOST     = 'latamerp-15-0-6624961.dev.odoo.com'
PORT     = 443
PROTOCOL = 'jsonrpc+ssl'
DB_NAME  = 'latamerp-15-0-6624961'
USER     = 'Marcos@latinamericavapelab.co'
PASSWORD = 'semsenha**'

# ============================
# 2) Conexão e autenticação
# ============================
odoo = odoorpc.ODOO(HOST, port=PORT, protocol=PROTOCOL)
odoo.login(DB_NAME, USER, PASSWORD)

# ============================
# 3) Buscar produtos “PRODUCTO TERMINADO” com estoque que começam com “POD”
# ============================
Category = odoo.env['product.category']
cat = Category.search_read(
    [('name', '=', 'PRODUCTO TERMINADO')],
    ['id'],
    limit=1
)
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
# 4) Agregar quantidades
# ============================
estoque = {}
for r in records:
    _, name = r['product_id']
    estoque.setdefault(name, 0)
    estoque[name] += int(r['quantity'])

# ============================
# 5) Montar o corpo da mensagem com data
# ============================
hoje = datetime.now().strftime("%d/%m/%Y")
if not estoque:
    message_body = (
        f"*Produtos em estoque (POD)*\n"
        f"_Data: {hoje}_\n\n"
        "Nenhum produto 'POD' com estoque disponível."
    )
else:
    lines = [
        "*Produtos em estoque (POD)*",
        f"_Data: {hoje}_",
        ""
    ]
    for nome in sorted(estoque):
        lines.append(f"- {nome}: {estoque[nome]}")
    message_body = "\n".join(lines)

# ============================
# 6) Apenas imprimir
# ============================
print(message_body)
