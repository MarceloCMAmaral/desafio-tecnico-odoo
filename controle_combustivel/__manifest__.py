# -*- coding: utf-8 -*-
{
    'name': 'Controle de Combustível',
    'version': '19.0.1.0.0',
    'category': 'Fleet',
    'summary': 'Gestão de abastecimentos e estoque de combustível',
    'description': """
Módulo para controle de combustível da Machado Pré-Moldados.

Funcionalidades:
- Registro de abastecimentos com integração Fleet (equipamentos/placas)
- Controle de estoque de combustível (tanque 6.000L)
- Entradas de combustível com rastreabilidade
- Permissões por perfil (usuário/gerente)
- Integração com recebimento de compras
    """,
    'author': 'Candidato — Desafio Machado ERP',
    'website': 'https://machadoerp.com.br',
    'license': 'LGPL-3',
    'depends': [
        'fleet',      # Equipamentos/placas cadastrados no Odoo
        'stock',      # stock.picking herdado em purchase_picking.py
        'purchase',   # Integração com recebimento de compras
    ],
    'data': [
        # 1. Segurança (grupos e ACLs) — carregados primeiro
        'security/security.xml',
        'security/ir.model.access.csv',
        # 2. Dados iniciais
        'data/tanque_data.xml',
        # 3. Views e menus
        'views/tanque_views.xml',
        'views/abastecimento_views.xml',
        'views/entrada_views.xml',
        'views/purchase_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
