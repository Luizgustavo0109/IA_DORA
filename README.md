# Chatbot Web (DORA)
<p> Este projeto implementa um chatbot web capaz de responder a perguntas do usuário utilizando diversas fontes de informação, como Wikipedia, Bing e DuckDuckGo. Além disso, o bot aprende e armazena novas perguntas e respostas no banco de dados para melhorar suas respostas futuras.</p>

## Funcionalidades
* Processamento de Linguagem Natural (NLP): Utiliza o modelo de embeddings SentenceTransformer para gerar representações vetoriais semânticas de perguntas e respostas.
* Banco de Dados: O conhecimento aprendido é armazenado em um banco de dados SQLite, utilizando SQLAlchemy para persistência de dados.
* Fontes Externas de Conhecimento: O chatbot busca respostas na Wikipedia, Wolfram Alpha, e motores de busca como Bing e DuckDuckGo.
* Aprendizado Contínuo: Quando o chatbot não encontra uma resposta diretamente no banco de dados, ele consulta fontes externas e armazena a nova resposta para melhorar no futuro.
* Interface Web: A aplicação web foi desenvolvida com Flask, com uma interface simples para interação com o usuário.

# Requisitos
* Python 3.8 ou superior
* Flask
* SentenceTransformers
* SQLAlchemy
* NLTK
* Wikipedia-API
* WolframAlpha API

# Instalação

1. Clone o repositório:
~~~
git clone https://github.com/seu-usuario/chatbot-web.git
cd chatbot-web
~~~

2. Crie um ambiente virtual:

~~~~
python -m venv venv
source venv/bin/activate  # No Windows, use 'venv\Scripts\activate'
~~~~

3. Instale as dependências:
~~~~
pip install -r requirements.txt
~~~~

4. Configuração da API Wolfram Alpha:

* Obtenha uma chave de API no Wolfram Alpha Developer Portal.
* Substitua sua chave no código:
~~~~
wolfram_client = wolframalpha.Client('SUA-CHAVE-AQUI')
~~~~

## Execução

1. Baixar pacotes NLTK necessários: Antes de rodar o projeto, baixe os pacotes do NLTK:
~~~~
python -m nltk.downloader punkt stopwords wordnet
~~~~

2. Inicie o servidor Flask:
~~~~
python app.py
~~~~
3. Acesse a aplicação: Abra o navegador e vá para http://localhost:5000.

## Uso

* Fazendo perguntas: Basta inserir uma pergunta na interface do chatbot e o sistema tentará buscar uma resposta nos bancos de dados internos ou nas fontes externas.
* Atualização automática: Perguntas novas são automaticamente salvas no banco de dados para futuras consultas.

## Contribuições
Fique à vontade para contribuir com melhorias para o projeto! Abra uma issue ou faça um pull request.
