# Conlicit Service

Serviço de coleta e processamento automatizado de editais de licitações públicas a partir da plataforma Conlicitação.

## O que o serviço faz

O serviço acessa a API da Conlicitação, coleta os boletins mais recentes de licitações públicas e realiza o download dos editais associados. O pipeline completo segue as etapas abaixo:

1. **Coleta de filtros** — obtém os filtros cadastrados na conta do cliente
2. **Listagem de boletins** — para cada filtro, busca os boletins disponíveis em ordem cronológica decrescente
3. **Extração de licitações** — de cada boletim, extrai as licitações e seus documentos
4. **Download dos editais** — faz o download dos arquivos (`.zip`, `.pdf`, etc.) de forma paralela usando threads
5. **Processamento** — converte os documentos para Markdown e executa um pipeline de RAG sobre o conteúdo

As etapas de download e processamento são distribuídas como tarefas assíncronas via **Celery**, com RabbitMQ como broker de mensagens e Redis como backend de resultados.

> **Atenção:** os links de download dos editais expiram em **24 horas** após a emissão do boletim. O pipeline completo (desde a coleta dos links até o download dos arquivos) deve ser concluído dentro desse prazo.

## Estrutura do projeto

```
conlicit_service/
├── api/
│   ├── client.py       # Cliente principal da API (coleta de dados)
│   └── downloader.py   # Downloader com suporte a threads paralelas
├── workers/
│   └── tasks.py        # Tarefas Celery (download, conversão, RAG)
├── utils/
│   └── debug.py        # Utilitários de debug e logging
├── data/
│   └── filtros.json    # Cache local dos filtros da conta
├── notebooks/
│   └── notebook.ipynb  # Exploração e prototipagem da API
└── archive/
    ├── client_v1.py    # Versão anterior do cliente
    └── tasks_example.py # Exemplo genérico de tarefas Celery
```

## Dependências

- Python 3.11+
- [requests](https://pypi.org/project/requests/)
- [tqdm](https://pypi.org/project/tqdm/)
- [celery](https://pypi.org/project/celery/)
- RabbitMQ
- Redis

Instale as dependências Python:

```bash
pip install requests tqdm celery
```

## Como executar

### 1. Suba os serviços de infraestrutura

O serviço depende de RabbitMQ e Redis em execução. Com Docker:

```bash
docker run -d -p 9972:5672 rabbitmq
docker run -d -p 9963:6379 redis
```

### 2. Inicie os workers Celery

Worker do servidor (responsável por buscar os links):

```bash
celery -A workers.tasks worker --loglevel=info -n worker_server@%h -Q server_queue
```

Worker local (responsável pelo download e processamento):

```bash
celery -A workers.tasks worker --loglevel=info -n worker_local@%h -Q local_queue
```

### 3. Executar o cliente diretamente (sem Celery)

Para uso simples sem filas, o cliente pode ser executado diretamente:

```bash
python -m api.client
```

Ou usando o downloader com threads:

```bash
python -m api.downloader
```
