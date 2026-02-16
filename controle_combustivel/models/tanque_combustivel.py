# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class TanqueCombustivel(models.Model):
    """Representa um tanque físico de armazenamento de combustível.

    Decisão arquitetural: o estoque_atual é um campo computado com store=True
    baseado no somatório de entradas menos o somatório de abastecimentos.
    Isso garante integridade mesmo se registros forem editados via shell/XML-RPC,
    ao contrário de uma abordagem incremental (estoque += litros) que seria
    propensa a dessincronização.
    """

    _name = 'controle.combustivel.tanque'
    _description = 'Tanque de Combustível'
    _order = 'name'

    # -------------------------------------------------------------------------
    # Campos
    # -------------------------------------------------------------------------
    name = fields.Char(
        string='Nome do Tanque',
        required=True,
        help='Identificação do tanque (ex: Tanque Principal 6.000L)',
    )
    capacidade_maxima = fields.Float(
        string='Capacidade Máxima (L)',
        required=True,
        default=6000.0,
        help='Capacidade máxima do tanque em litros',
    )
    estoque_atual = fields.Float(
        string='Estoque Atual (L)',
        compute='_compute_estoque_atual',
        store=True,
        help='Estoque atual calculado: soma das entradas menos soma dos abastecimentos confirmados',
    )
    percentual_estoque = fields.Float(
        string='Nível (%)',
        compute='_compute_percentual_estoque',
        store=True,
        help='Percentual de ocupação do tanque',
    )
    entrada_ids = fields.One2many(
        'controle.combustivel.entrada',
        'tanque_id',
        string='Entradas',
    )
    abastecimento_ids = fields.One2many(
        'controle.combustivel.abastecimento',
        'tanque_id',
        string='Abastecimentos',
    )
    active = fields.Boolean(
        string='Ativo',
        default=True,
        help='Desmarque para arquivar o tanque sem excluí-lo',
    )

    # -------------------------------------------------------------------------
    # Computed Fields
    # -------------------------------------------------------------------------
    @api.depends('entrada_ids.litros', 'abastecimento_ids.litros', 'abastecimento_ids.state')
    def _compute_estoque_atual(self):
        """Calcula o estoque atual do tanque.

        Soma de todas as entradas menos a soma dos abastecimentos confirmados.
        Decisão: apenas abastecimentos com state='done' são contabilizados,
        permitindo que rascunhos existam sem afetar o estoque.
        """
        for tanque in self:
            total_entradas = sum(tanque.entrada_ids.mapped('litros'))
            total_abastecimentos = sum(
                tanque.abastecimento_ids.filtered(
                    lambda a: a.state == 'done'
                ).mapped('litros')
            )
            tanque.estoque_atual = total_entradas - total_abastecimentos

    @api.depends('estoque_atual', 'capacidade_maxima')
    def _compute_percentual_estoque(self):
        """Calcula o percentual de ocupação para widget progressbar."""
        for tanque in self:
            if tanque.capacidade_maxima > 0:
                tanque.percentual_estoque = (
                    tanque.estoque_atual / tanque.capacidade_maxima
                ) * 100
            else:
                tanque.percentual_estoque = 0.0

    # -------------------------------------------------------------------------
    # Constraints
    # -------------------------------------------------------------------------
    @api.constrains('estoque_atual', 'capacidade_maxima')
    def _check_estoque(self):
        """Valida que o estoque não exceda limites físicos."""
        for tanque in self:
            if tanque.estoque_atual < 0:
                raise ValidationError(
                    f'O estoque do tanque "{tanque.name}" não pode ficar negativo. '
                    f'Estoque atual: {tanque.estoque_atual:.2f}L'
                )
            if tanque.estoque_atual > tanque.capacidade_maxima:
                raise ValidationError(
                    f'O estoque do tanque "{tanque.name}" excede a capacidade máxima. '
                    f'Estoque: {tanque.estoque_atual:.2f}L / '
                    f'Capacidade: {tanque.capacidade_maxima:.2f}L'
                )
