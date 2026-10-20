
# ED-ANTAQ-01 | Pipeline de Engenharia de Dados Portuários

## 1. Objetivo

Desenvolver um pipeline de Engenharia de Dados em Python e SQL para extrair, transformar, validar e disponibilizar informações de movimentação de cargas do Complexo Portuário de Santos.

O projeto utiliza os microdados da ANTAQ referentes ao arquivo-base de 2024 e implementa um fluxo de processamento com controle de qualidade, armazenamento SQLite, consultas analíticas e testes automatizados.

## 2. Tecnologias

- Python
- Pandas
- SQLite
- SQL
- unittest
- Git e GitHub
- Visual Studio Code

## 3. Fontes de dados

Fonte: Agência Nacional de Transportes Aquaviários (ANTAQ).

Arquivos utilizados:

- `2024Carga.txt`
- `2024Atracacao.txt`

Arquivo adicional disponível para futuras análises:

- `2024TemposAtracacao.txt`

Os arquivos originais não são incluídos no repositório Git.

## 4. Abrangência

Recorte geográfico: Complexo Portuário de Santos.

O recorte das cargas é realizado a partir dos identificadores `IDAtracacao` presentes no arquivo de atracações, selecionando os registros cujo campo `Complexo Portuário` corresponde a Santos.

Essa abordagem permite incluir instalações integrantes do complexo que não seriam necessariamente contempladas por um filtro exclusivamente baseado no nome do porto de atracação.

## 5. Arquitetura

```text
ANTLR RAW (TXT)
      |
      v
EXTRACT / TRANSFORM
      |
      v
SILVER (CSV tratado)
      |
      v
LOAD (SQLite)
      |
      +--> carga_santos
      |
      +--> atracacoes
      |
      v
GOLD (Agregacao mensal)
      |
      v
VIEW ANALITICA 2024
      |
      v
TESTES / VALIDACOES / PUBLICACAO
```

## 6. Resultados do piloto

| Indicador | Resultado |
|---|---:|
| Registros de carga selecionados | 760.354 |
| Atracações do complexo | 6.292 |
| Peso bruto total, nas unidades da fonte | 177.073.928,08 |
| Competências presentes na Gold | 13 |
| Registros na VIEW de 2024 | 757.413 |
| Competências na VIEW de 2024 | 12 |
| Testes automatizados | 12 aprovados |

## 7. Estruturas SQLite

### carga_santos

Tabela com informações das cargas selecionadas e seus atributos operacionais.

### atracacoes

Dimensão com os identificadores, instalações e datas de atracação.

### gold_movimentacao_mensal

Agregação por:

- Competencia
- PortoAtracacao
- NaturezaCarga
- Sentido

Principais métricas:

- QtdRegistrosCarga
- PesoBrutoTotal

### vw_movimentacao_2024

VIEW que seleciona competências entre janeiro e dezembro de 2024.

## 8. Qualidade de dados

O pipeline inclui verificações de:

- Identificadores obrigatórios;
- Unicidade das chaves primárias;
- Conversão numérica e tratamento de decimais;
- Integridade dos relacionamentos;
- Reconciliação de quantidades e peso bruto;
- Integridade SQLite;
- Equivalência de resultados entre ambientes;
- Testes unitários e de integração.

## 9. Execução

Instalar as dependências:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Os arquivos de origem devem estar na pasta `data/raw`.

Gerar a camada Silver:

```powershell
.\.venv\Scripts\python.exe src\gerar_silver.py
```

Executar a reconstrução integrada:

```powershell
.\.venv\Scripts\python.exe src\reconstruir_pipeline.py
```

A reconstrução utiliza um banco candidato independente e impede a sobrescrita automática de um arquivo candidato existente.

Executar os testes:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

## 10. Limitações metodológicas

A competência mensal utilizada nesta versão é derivada da data de atracação, não tendo sido estabelecida sua equivalência à competência oficial de movimentação divulgada pela ANTAQ.

O arquivo-base de 2024 inclui registros associados à competência de dezembro de 2023.

A unidade da variável de peso bruto deve ser confirmada no dicionário oficial da fonte antes de sua apresentação como toneladas.

Os totais esperados nas validações estão fixados para o piloto de 2024 e precisarão ser parametrizados para uma expansão histórica.

## 11. Próximos desenvolvimentos

- Generalização do processamento para 2020 a 2025;
- Validações por ano e competência;
- Modelagem dimensional;
- Disponibilização em PostgreSQL;
- Integração com ferramentas de BI;
- Evolução dos controles de execução e monitoramento.

## 12. Finalidade

Projeto de estudo aplicado em Engenharia de Dados, utilizando informações de logística portuária para explorar técnicas de tratamento, integração, validação e disponibilização de dados.
