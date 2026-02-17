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
├── docs/                          # Documentação técnica
│   ├── defesa_tecnica.txt
│   └── proposta_nfe.md
└── static/
    └── description/
        ├── icon.png               # Ícone do módulo (PNG)
        └── icon.svg               # Ícone do módulo (SVG fonte)
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
| Hierarquia de grupos | Manager herda User (`implied_ids`), `base.group_user` implica User, `base.group_system` implica Manager | Padrão Odoo: todos os usuários internos recebem acesso básico automaticamente |
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

- **Configuração do ambiente Docker/Odoo 19.0** — O healthcheck do PostgreSQL precisou ser ajustado para verificar o banco correto (`-d postgres`). Volumes nomeados foram necessários no Windows para evitar problemas com PGDATA.
- **Permissões e grupos de segurança** — O `implied_ids` no Odoo funciona de forma não-intuitiva: para auto-atribuir um grupo a todos os usuários internos, é necessário modificar `base.group_user` para implicar o grupo customizado (e não o contrário). O grupo do módulo implicando `base.group_user` apenas garante que membros do grupo são usuários internos, sem reciprocidade.
- **Ícone do módulo** — O Odoo 19.0 exige que o campo `web_icon` do menu raiz aponte para um PNG válido em `static/description/icon.png`. A ausência do arquivo impede a exibição no app switcher.
- **Tradução pt_BR nos menus** — O Odoo 19.0 armazena nomes de menus em JSONB multidioma. Menus sem tradução `pt_BR` podem não aparecer corretamente em interfaces configuradas em português.

---

## Como Instalar

### Via Docker (recomendado)

1. **Clone o repositório:**
   ```bash
   git clone <https://github.com/MarceloCMAmaral/desafio-tecnico-odoo.git>
   cd Desafio\ Machado\ ERP
   ```

2. **Suba os containers:**
   ```bash
   docker compose up -d
   ```

3. **Na primeira execução**, acesse http://localhost:8069 e crie o banco de dados:  
   - Database Name: `odoo_machado`
   - Email: `admin@admin.com`
   - Password: escolha uma senha

4. **Instale o módulo** pelo painel de Apps (busque "Combustível")

5. **Pré-requisitos:** os módulos **Fleet** e **Purchase** devem estar instalados antes.

### Via instalação local (alternativa)

1. **Copie o módulo** para a pasta de addons:
   ```bash
   cp -r controle_combustivel /opt/odoo/custom_addons/
   ```

2. **Configure o `addons_path`** no `odoo.conf`:
   ```ini
   addons_path = /opt/odoo/odoo/addons,/opt/odoo/custom_addons
   ```

3. **Reinicie o Odoo** e instale pelo painel de Apps.

---

## Tecnologias

- **Odoo 19.0 Community** (Python 3.10+, PostgreSQL)
- **Framework Odoo** — ORM, Views XML, Security (ACLs), Actions
- **Módulo Fleet** — cadastro de veículos/equipamentos
- **Módulo Purchase + Stock** — integração com recebimento de compras

---

*Desenvolvido como parte do processo seletivo - Machado ERP.*
