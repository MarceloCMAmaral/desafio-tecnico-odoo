# Proposta de Integração NF-e / NFS-e

## Contexto

A Machado Pré-Moldados precisa emitir/receber NF-e para compras de combustível e potencialmente NFS-e para serviços de transporte relacionados. Esta proposta analisa as opções disponíveis para integração com o módulo `controle_combustivel`.

---

## Opções Arquiteturais

### Opção 1: Módulos OCA Brasil (l10n-brazil)

**Repositório:** https://github.com/OCA/l10n-brazil

**Módulos relevantes:**
- `l10n_br_base` — CPF/CNPJ, endereços BR
- `l10n_br_fiscal` — Framework fiscal brasileiro
- `l10n_br_nfe` — Emissão/recebimento de NF-e
- `l10n_br_purchase` — Localização do módulo de compras

| Prós | Contras |
|------|---------|
| Mantido por comunidade ativa (OCA) | Complexo: muitas dependências |
| Testado em produção por empresas reais | Curva de aprendizado alta |
| Gratuito e open source | Requer certificado digital A1 |
| Integração nativa com Odoo | Atualizações podem atrasar vs versão Odoo |

**Recomendado para:** empresas que usarão Odoo como sistema principal em produção.

---

### Opção 2: API de Terceiros (SaaS)

**Serviços:**
- [Focus NFe](https://focusnfe.com.br/) — API REST para emissão
- [Bling](https://www.bling.com.br/) — ERP com API
- [Tiny ERP](https://www.tiny.com.br/) — gestão com emissão
- [Notazz](https://notazz.com/) — API especializada em NF-e

| Prós | Contras |
|------|---------|
| Implementação rápida | Custo mensal (por NF emitida) |
| SaaS: sem infraestrutura de certificado | Dependência de terceiros |
| Suporte profissional incluído | Limites de uso por plano |
| Atualizações automáticas SEFAZ | Dados fiscais fora do Odoo |

**Recomendado para:** start rápido, equipes pequenas, baixo volume de NFs.

---

### Opção 3: Módulo Custom com PyNFe

**Biblioteca:** https://github.com/TadaSoftware/PyNFe

| Prós | Contras |
|------|---------|
| Controle total do código | Manutenção complexa |
| Sem dependência de SaaS | Acompanhar mudanças SEFAZ |
| Customização livre | Requer certificado digital |
| Integração direta com Odoo | Mais horas de desenvolvimento |

**Recomendado para:** cenários muito específicos, equipe com expertise fiscal.

---

## Recomendação

| Cenário | Opção Recomendada |
|---------|-------------------|
| Produção com volume | **Opção 1** (OCA l10n-brazil) |
| MVP / Prova de conceito | **Opção 2** (API terceiros) |
| Requisitos muito específicos | **Opção 3** (Custom PyNFe) |

---

## Integração com `controle_combustivel`

### Campos adicionais propostos

```python
# No modelo controle.combustivel.entrada
nfe_numero = fields.Char(string='Número NF-e')
nfe_chave = fields.Char(string='Chave de Acesso NF-e', size=44)
nfe_data_emissao = fields.Date(string='Data Emissão NF-e')
```

### Fluxo proposto

1. Compra de combustível gera NF-e de entrada
2. Ao validar recebimento (`stock.picking`), preencher dados da NF-e
3. Entrada no tanque registra número e chave da NF-e
4. Relatório de movimentações cruza NF-e × abastecimentos

### Relatórios fiscais possíveis

- Consumo de combustível por período com NF-e vinculada
- Custo médio por litro com base nas NF-e de compra
- Rastreamento fiscal completo: NF-e → estoque → abastecimento → equipamento
