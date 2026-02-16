# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockPicking(models.Model):
    """Extensão do recebimento de compras para integração com estoque de combustível.

    Decisão arquitetural: herda stock.picking e estende button_validate()
    para, ao confirmar o recebimento de uma compra que contenha produtos
    marcados como combustível, criar automaticamente uma entrada no tanque.

    Isso conecta o fluxo de compras ao controle de combustível sem
    modificar o comportamento padrão do módulo de estoque.
    """

    _inherit = 'stock.picking'

    # -------------------------------------------------------------------------
    # Campos
    # -------------------------------------------------------------------------
    combustivel_entrada_count = fields.Integer(
        string='Entradas de Combustível',
        compute='_compute_combustivel_entrada_count',
    )

    # -------------------------------------------------------------------------
    # Computed Fields
    # -------------------------------------------------------------------------
    def _compute_combustivel_entrada_count(self):
        """Conta quantas entradas de combustível foram geradas por este picking."""
        for picking in self:
            picking.combustivel_entrada_count = self.env[
                'controle.combustivel.entrada'
            ].search_count([
                ('referencia', 'like', picking.name),
            ]) if picking.name else 0

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------
    def action_view_combustivel_entradas(self):
        """Abre as entradas de combustível geradas por este recebimento."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Entradas de Combustível',
            'res_model': 'controle.combustivel.entrada',
            'view_mode': 'list,form',
            'domain': [('referencia', 'like', self.name)],
            'context': {'default_referencia': f'Compra: {self.name}'},
        }

    def button_validate(self):
        """Estende a validação do recebimento para criar entradas de combustível.

        Fluxo:
        1. Executa a validação padrão do stock.picking (super)
        2. Verifica se o picking é do tipo recebimento (incoming)
        3. Para cada linha cujo produto tem a categoria 'Combustível',
           cria uma entrada no tanque configurado
        """
        result = super().button_validate()

        for picking in self:
            # Apenas pickings de recebimento (incoming)
            if picking.picking_type_code != 'incoming':
                continue

            for move_line in picking.move_ids:
                product = move_line.product_id
                # Verifica se o produto pertence à categoria 'Combustível'
                if product.categ_id and product.categ_id.name == 'Combustível':
                    # Busca o tanque ativo (primeiro encontrado)
                    tanque = self.env['controle.combustivel.tanque'].search(
                        [('active', '=', True)], limit=1
                    )
                    if tanque:
                        self.env['controle.combustivel.entrada'].create({
                            'tanque_id': tanque.id,
                            'litros': move_line.quantity,
                            'referencia': f'Compra: {picking.name}',
                            'responsavel_id': self.env.uid,
                        })

        return result
