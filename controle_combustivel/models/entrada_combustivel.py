# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EntradaCombustivel(models.Model):
    """Registro de entrada de combustível no tanque.

    Cada entrada representa um recebimento de combustível que aumenta
    o estoque do tanque. A referência permite rastrear a origem
    (nota fiscal, pedido de compra, etc.).
    """

    _name = 'controle.combustivel.entrada'
    _description = 'Entrada de Combustível'
    _order = 'data desc'

    # -------------------------------------------------------------------------
    # Campos
    # -------------------------------------------------------------------------
    tanque_id = fields.Many2one(
        'controle.combustivel.tanque',
        string='Tanque',
        required=True,
        ondelete='restrict',
        help='Tanque que receberá o combustível',
    )
    data = fields.Datetime(
        string='Data/Hora',
        required=True,
        default=fields.Datetime.now,
        help='Data e hora do recebimento do combustível',
    )
    litros = fields.Float(
        string='Litros',
        required=True,
        digits=(10, 2),
        help='Quantidade de litros recebidos',
    )
    referencia = fields.Char(
        string='Referência',
        help='Número da nota fiscal, pedido de compra ou outra referência',
    )
    responsavel_id = fields.Many2one(
        'res.users',
        string='Responsável',
        required=True,
        default=lambda self: self.env.uid,
        help='Usuário que registrou a entrada',
    )
    observacao = fields.Text(
        string='Observação',
    )

    # -------------------------------------------------------------------------
    # Constraints
    # -------------------------------------------------------------------------
    @api.constrains('litros')
    def _check_litros(self):
        """Valida que a quantidade de litros é positiva."""
        for record in self:
            if record.litros <= 0:
                raise ValidationError(
                    'A quantidade de litros da entrada deve ser maior que zero.'
                )
