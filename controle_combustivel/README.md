# Controle de Combustível — Módulo Odoo 19.0 Community

## Visão Geral

Módulo customizado para a **Desafio Machado ERP**, desenvolvido para gerenciar o controle de abastecimentos de veículos/equipamentos e o estoque de combustível da empresa.

**Funcionalidades principais:**
- ⛽ Registro de abastecimentos com integração ao módulo Fleet (equipamentos/placas)
- 🛢️ Controle de estoque de combustível com tanque de 6.000L
- 📥 Registro de entradas de combustível com rastreabilidade
- 🔒 Permissões por perfil (Usuário / Gerente)
- 🛒 Integração com recebimento de compras (diferencial)

---

## Estrutura do Módulo

```
controle_combustivel/
├── __init__.py                    # Importa o pacote models
├── __manifest__.py                # Manifesto: deps, dados, metadados
├── models/
│   ├── __init__.py                # Importa os 4 modelos
│   ├── tanque_combustivel.py      # Tanque com estoque computado
│   ├── entrada_combustivel.py     # Entradas (receitas no tanque)
│   ├── abastecimento.py           # Abastecimentos (saídas do tanque)
│   └── purchase_picking.py        # Integração compras
├── views/
│   ├── tanque_views.xml           # Form + List + Search + Action
│   ├── abastecimento_views.xml    # Form + List + Search + Action
│   ├── entrada_views.xml          # Form + List + Search + Action
│   └── menu_views.xml             # Hierarquia de menus
├── security/
│   ├── security.xml               # Grupos + Sequência
│   └── ir.model.access.csv        # Matriz de permissões (ACLs)
├── data/
│   └── tanque_data.xml            # Tanque padrão de 6.000L
├── docs/                          # Documentação técnica por fase
│   ├── fase1_estrutura.md
│   ├── fase2_modelos.md
│   ├── fase3_views.md
│   ├── fase4_seguranca.md
│   ├── fase5_fleet.md
│   ├── fase6_compras.md
│   ├── fase7_entrega.md
│   ├── ambiente_tecnico.md
│   └── proposta_nfe.md
└── static/
    └── description/
        └── icon.png               # Ícone do módulo
```

---

## Modelos de Dados

### Diagrama ER

```
┌────────────────────────┐       ┌───────────────────────────────┐
│  controle.combustivel  │       │   controle.combustivel        │
│       .tanque          │       │      .abastecimento           │
├────────────────────────┤       ├───────────────────────────────┤
│ name (Char)            │◄──┐   │ name (Char) - sequência       │
│ capacidade_maxima (Fl) │   │   │ equipamento_id → fleet.vehicle│
│ estoque_atual (comp.)  │   ├───│ tanque_id → tanque            │
│ percentual (comp.)     │   │   │ data_hora (Datetime)          │
│ active (Boolean)       │   │   │ horimetro_odometro (Float)    │
└────────────────────────┘   │   │ litros (Float 10,2)           │
                             │   │ valor_litro (Float 10,4)      │
┌────────────────────────┐   │   │ total (comp. store=True)      │
│  controle.combustivel  │   │   │ responsavel_id → res.users    │
│       .entrada         │   │   │ motorista_id → res.partner    │
├────────────────────────┤   │   │ state (Selection)             │
│ tanque_id → tanque     │───┘   └───────────────────────────────┘
│ data (Datetime)        │
│ litros (Float 10,2)    │
│ referencia (Char)      │
│ responsavel_id → users │
└────────────────────────┘
```

### `controle.combustivel.tanque`
Representa o tanque físico de combustível. O **estoque_atual é computado** pela soma das entradas menos a soma dos abastecimentos confirmados (state='done'). Esta abordagem garante integridade por recalcular o saldo a partir das movimentações, ao contrário de uma atualização incremental que seria propensa a dessincronização.

### `controle.combustivel.abastecimento`
Registro de cada abastecimento de veículo. Implementa workflow **Rascunho → Confirmado → Cancelado** com botões de ação. O campo `total` é computado (`litros × valor_litro`) com `store=True` para permitir filtros e relatórios. O `valor_litro` usa 4 casas decimais para precisão (ex: R$ 6,2590).

### `controle.combustivel.entrada`
Registra cada recebimento de combustível no tanque, com campo de referência para rastreabilidade (nº da NF, pedido de compra, etc.).

---

## Decisões Técnicas

| Decisão | Escolha | Justificativa |
|---------|---------|---------------|
| Estoque do tanque | Computado (`store=True`) | Integridade: recalcula a partir das movimentações. Sem risco de dessincronização |
| `total` do abastecimento | `@api.depends` + `store=True` | Permite uso em filtros e agrupamentos (SQL). `@api.onchange` não funcionaria via API |
| `valor_litro` | `Float(digits=(10,4))` | Preço de combustível frequentemente tem 4 decimais (R$ 6,2590) |
| `motorista_id` | `Many2one('res.partner')` | Permite motoristas terceirizados sem login no sistema |
| `responsavel_id` | `Many2one('res.users')` | Sempre é um operador do sistema com acesso |
| Referência equipamento | `Many2one('fleet.vehicle')` | Reutiliza cadastro existente do Odoo, evita duplicação |
| Hierarquia de grupos | Manager herda User (`implied_ids`) | Padrão Odoo: concessão automática de permissões base |
| Usuário: deletar abastecimento | Proibido (`perm_unlink=0`) | Evita inconsistência de estoque |
| Workflow | `draft → done → cancel` | Permite revisão antes de afetar estoque |
| Integração compras | Herança `stock.picking.button_validate()` | Ponto exato do recebimento físico |

---

## Melhorias Possíveis

- **Relatórios PDF** consumo por período, por equipamento
- **Dashboard** com gráficos de consumo e nível do tanque
- **Alertas automáticos** quando estoque < 20% da capacidade
- **Integração GPS** para validar leitura do odômetro
- **Múltiplos tipos de combustível** (diesel, gasolina, etc.) por tanque
- **Relatório de custo por km/hora** cruzando abastecimento com odômetro

---

## Dificuldades e Aprendizados

*(Preencher durante o desenvolvimento com dificuldades reais encontradas)*

- Configuração do ambiente Odoo 19.0
- Entendimento da relação entre `store=True` e `@api.depends`
- Testes de integração com o módulo Fleet
- Debugging de permissões e ACLs

---

## Como Instalar

1. **Clone o repositório** na pasta de addons customizados:
   ```bash
   git clone <url-repositorio> /opt/odoo/custom_addons/controle_combustivel
   ```

2. **Configure o `addons_path`** no `odoo.conf`:
   ```ini
   addons_path = /opt/odoo/odoo/addons,/opt/odoo/custom_addons
   ```

3. **Reinicie o Odoo** e atualize a lista de módulos:
   ```bash
   sudo systemctl restart odoo
   ```

4. **Instale o módulo** pelo painel de Apps (busque "Combustível")

5. **Pré-requisitos:** os módulos **Fleet** e **Purchase** devem estar instalados antes.

---

## Tecnologias

- **Odoo 19.0 Community** (Python 3.10+, PostgreSQL)
- **Framework Odoo** — ORM, Views XML, Security (ACLs), Actions
- **Módulo Fleet** — cadastro de veículos/equipamentos
- **Módulo Purchase + Stock** — integração com recebimento de compras

---

*Desenvolvido como parte do processo seletivo da Machado Pré-Moldados.*
