# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Abastecimento(models.Model):
    """Registro de abastecimento de veículo/equipamento.

    Decisões técnicas documentadas:
    - valor_litro com 4 casas decimais: combustível frequentemente tem preço
      como R$ 6,2590. Usar apenas 2 casas causaria erros de arredondamento.
    - total com store=True: permite uso em filtros, agrupamentos e ordenação.
    - motorista_id como res.partner: permite terceirizados sem login no sistema.
    - responsavel_id como res.users: sempre é um operador do sistema.
    - state com workflow draft→done: permite revisão antes de afetar estoque.
    """

    _name = 'controle.combustivel.abastecimento'
    _description = 'Registro de Abastecimento'
    _order = 'data_hora desc'

    # -------------------------------------------------------------------------
    # Campos
    # -------------------------------------------------------------------------
    name = fields.Char(
        string='Referência',
        readonly=True,
        copy=False,
        default='Novo',
        help='Sequência automática gerada ao confirmar',
    )
    equipamento_id = fields.Many2one(
        'fleet.vehicle',
        string='Equipamento/Placa',
        required=True,
        help='Veículo ou equipamento cadastrado no módulo Fleet',
    )
    data_hora = fields.Datetime(
        string='Data e Hora',
        required=True,
        default=fields.Datetime.now,
        help='Data e hora do abastecimento',
    )
    horimetro_odometro = fields.Float(
        string='Horímetro/Odômetro',
        digits=(10, 1),
        help='Leitura do horímetro (máquinas) ou odômetro (veículos) no momento do abastecimento',
    )
    litros = fields.Float(
        string='Litros',
        required=True,
        digits=(10, 2),
        help='Quantidade de litros abastecidos',
    )
    valor_litro = fields.Float(
        string='Valor por Litro (R$)',
        required=True,
        digits=(10, 4),
        help='Preço por litro do combustível (4 casas decimais para precisão)',
    )
    total = fields.Float(
        string='Total (R$)',
        compute='_compute_total',
        store=True,
        digits=(10, 2),
        help='Valor total calculado automaticamente: litros × valor por litro',
    )
    responsavel_id = fields.Many2one(
        'res.users',
        string='Responsável',
        required=True,
        default=lambda self: self.env.uid,
        help='Usuário do sistema que registrou o abastecimento',
    )
    motorista_id = fields.Many2one(
        'res.partner',
        string='Motorista',
        help='Motorista que realizou o abastecimento (pode ser terceirizado)',
    )
    tanque_id = fields.Many2one(
        'controle.combustivel.tanque',
        string='Tanque',
        required=True,
        ondelete='restrict',
        help='Tanque de onde o combustível foi retirado',
    )
    state = fields.Selection(
        [
            ('draft', 'Rascunho'),
            ('done', 'Confirmado'),
            ('cancel', 'Cancelado'),
        ],
        string='Estado',
        default='draft',
        required=True,

        help='Rascunho: não afeta estoque. Confirmado: desconta do tanque.',
    )
    observacao = fields.Text(
        string='Observação',
    )

    # -------------------------------------------------------------------------
    # Computed Fields
    # -------------------------------------------------------------------------
    @api.depends('litros', 'valor_litro')
    def _compute_total(self):
        """Calcula o total do abastecimento.

        Decisão: usa @api.depends e não @api.onchange.
        @api.depends garante recálculo tanto na UI quanto via API/importação.
        @api.onchange só funciona na interface web.
        """
        for record in self:
            record.total = record.litros * record.valor_litro

    # -------------------------------------------------------------------------
    # Constraints
    # -------------------------------------------------------------------------
    @api.constrains('litros')
    def _check_litros(self):
        """Valida que a quantidade de litros é positiva."""
        for record in self:
            if record.litros <= 0:
                raise ValidationError(
                    'A quantidade de litros deve ser maior que zero.'
                )

    @api.constrains('valor_litro')
    def _check_valor_litro(self):
        """Valida que o valor por litro é positivo."""
        for record in self:
            if record.valor_litro <= 0:
                raise ValidationError(
                    'O valor por litro deve ser maior que zero.'
                )

    # -------------------------------------------------------------------------
    # Actions (Workflow)
    # -------------------------------------------------------------------------
    def action_confirm(self):
        """Confirma o abastecimento, descontando do estoque do tanque.

        Decisão: o estoque é descontado indiretamente — ao mudar o state
        para 'done', o campo computed estoque_atual do tanque recalcula
        automaticamente (pois depende de abastecimento_ids.state).
        Isso evita manipulação direta do estoque e garante consistência.
        """
        for record in self:
            if record.state != 'draft':
                raise ValidationError(
                    'Apenas abastecimentos em rascunho podem ser confirmados.'
                )
            # Gerar sequência
            if record.name == 'Novo':
                record.name = self.env['ir.sequence'].next_by_code(
                    'controle.combustivel.abastecimento'
                ) or 'Novo'
            record.state = 'done'

    def action_cancel(self):
        """Cancela o abastecimento, devolvendo ao estoque do tanque.

        Ao cancelar, o state muda para 'cancel', e o computed field
        estoque_atual recalcula excluindo registros cancelados e drafts.
        """
        for record in self:
            if record.state != 'done':
                raise ValidationError(
                    'Apenas abastecimentos confirmados podem ser cancelados.'
                )
            record.state = 'cancel'

    def action_draft(self):
        """Retorna o abastecimento ao estado de rascunho."""
        for record in self:
            if record.state != 'cancel':
                raise ValidationError(
                    'Apenas abastecimentos cancelados podem voltar a rascunho.'
                )
            record.state = 'draft'
