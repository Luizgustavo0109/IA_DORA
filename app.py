from flask import Flask, request, jsonify, render_template
from sentence_transformers import SentenceTransformer, util
from sqlalchemy import create_engine, Column, Integer, String, Text, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from scipy.spatial.distance import cosine
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import wikipedia
import wolframalpha
import re
import requests
from bs4 import BeautifulSoup
import json
import numpy as np

app = Flask(__name__)

# Baixar pacotes necessários do NLTK
nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('wordnet')
nltk.download('punkt_tab')

# Carregar modelo de embeddings
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# Banco de dados local
engine = create_engine('sqlite:///chatbot.db')
Base = declarative_base()

# Modelo para armazenamento de perguntas e respostas
class Knowledge(Base):
    __tablename__ = 'knowledge_base'
    id = Column(Integer, primary_key=True)
    pergunta = Column(String, unique=True)
    resposta = Column(Text)
    embedding = Column(LargeBinary)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Configurações do Wolfram Alpha
wolfram_client = wolframalpha.Client('SUA-API-KEY')

# Função para gerar embedding semântico
def gerar_embedding(frase):
    return model.encode(frase, convert_to_tensor=True)


# Função para salvar ou atualizar conhecimento
def salvar_conhecimento(pergunta, resposta, embedding):
    # Verificar se a pergunta já existe
    conhecimento_existente = session.query(Knowledge).filter_by(pergunta=pergunta).first()
    
    if conhecimento_existente:
        # Atualizar a resposta e o embedding
        conhecimento_existente.resposta = resposta
        conhecimento_existente.embedding = np.array(embedding).astype(np.float32).tobytes()
        session.commit()
        print(f"Pergunta '{pergunta}' atualizada no banco de dados.")
    else:
        # Se não existe, inserir o novo conhecimento
        conhecimento = Knowledge(
            pergunta=pergunta,
            resposta=resposta,
            embedding=np.array(embedding).astype(np.float32).tobytes()  
        )
        session.add(conhecimento)
        session.commit()

# Função para carregar conhecimentos
def carregar_conhecimento():
    return session.query(Knowledge).all()

# Função de pré-processamento com NLTK (tokenização, remoção de stopwords, lematização)
def preprocessar_pergunta(pergunta):
    # Tokenizar a frase
    palavras = word_tokenize(pergunta.lower())  # Converter para minúsculas e tokenizar
    
    # Remover stopwords
    stop_words = set(stopwords.words('portuguese'))  # Usando o idioma português
    palavras_filtradas = [palavra for palavra in palavras if palavra.isalnum() and palavra not in stop_words]
    
    # Lematização
    lemmatizer = WordNetLemmatizer()
    palavras_lemmatizadas = [lemmatizer.lemmatize(palavra) for palavra in palavras_filtradas]
    
    # Juntar novamente as palavras em uma frase
    frase_preprocessada = ' '.join(palavras_lemmatizadas)
    
    return frase_preprocessada

# Função para buscar pergunta similar no banco de dados
def buscar_resposta_similar(pergunta, knowledge_base):
    pergunta_preprocessada = preprocessar_pergunta(pergunta)  # Pré-processar a pergunta
    pergunta_embedding = gerar_embedding(pergunta_preprocessada)  # Gerar embedding da pergunta
    similaridade_max = -1
    resposta_similar = None
    
    for item in knowledge_base:
        # Convertendo o embedding armazenado de volta para numpy array e garantindo a dimensão correta
        embedding_conhecimento = np.frombuffer(item.embedding, dtype=np.float32).reshape(-1)
        
        if pergunta_embedding.shape != embedding_conhecimento.shape:
            print(f"Dimensões incompatíveis: {pergunta_embedding.shape} vs {embedding_conhecimento.shape}")
            continue
        
        similaridade = 1 - cosine(pergunta_embedding, embedding_conhecimento)
        
        if similaridade > similaridade_max:
            similaridade_max = similaridade
            resposta_similar = item.resposta

    return resposta_similar, similaridade_max

# Função para resumir conteúdo da web em tópicos
def resumir_conteudo(conteudo):
    topicos = "\n".join([f"- {c}" for c in conteudo if c])
    return topicos if topicos else "Nenhum conteúdo relevante encontrado."

# Função atualizada para buscar informações na web (usando Bing e DuckDuckGo)
def rastrear_web(query):
    resultados = []

    # Adicionar Bing
    resultados_bing = rastrear_bing(query)
    resultados += resultados_bing

    # Adicionar DuckDuckGo
    resultados_duckduckgo = rastrear_duckduckgo(query)
    resultados += resultados_duckduckgo

    # Retornar conteúdo formatado como tópicos e links ao final
    resumo_topicos = resumir_conteudo(resultados)
    links = [f"[Fonte {i+1}]({link})" for i, link in enumerate([res["link"] for res in resultados if 'link' in res])]
    
    return resumo_topicos, links

# Função para buscar informações em múltiplas fontes (retorna resumo e links)
def buscar_informacoes(frase):
    resultado_wikipedia = consultar_wikipedia(frase)
    resultado_web, links = rastrear_web(frase)

    return {
        "wikipedia": resultado_wikipedia,
        "web": resultado_web
    }, links

# Função para processar a pergunta
def processar_pergunta(pergunta):
    # Pré-processar a pergunta
    pergunta_preprocessada = preprocessar_pergunta(pergunta)
    
    # Carregar conhecimentos do banco de dados
    knowledge_base = carregar_conhecimento()

    # Verifica se há uma pergunta similar
    if knowledge_base:
        resposta_similar, similaridade_max = buscar_resposta_similar(pergunta_preprocessada, knowledge_base)
        if similaridade_max > 0.75:
            return resposta_similar, []  # Caso encontre uma resposta similar, retorna a resposta e uma lista vazia de links

    # Busca informações em fontes externas
    respostas, links = buscar_informacoes(pergunta_preprocessada)
    embedding = gerar_embedding(pergunta_preprocessada)
    salvar_conhecimento(pergunta_preprocessada, json.dumps(respostas), embedding)

    return respostas, links

# Função para formatar as respostas (inclui links das fontes ao final)
def formatar_resposta(resposta, links):
    resposta_formatada = "# Aqui está o que encontrei:\n\n"
    if isinstance(resposta, dict):
        resposta_wikipedia = resposta.get("wikipedia", "Nenhuma resposta da Wikipedia.")
        resposta_formatada += "## Fonte: Wikipedia\n" + resposta_wikipedia + "\n\n"
        resposta_formatada += "## Fontes da Web (Resumido em tópicos)\n"
        resposta_formatada += resposta.get("web", "Nenhum conteúdo encontrado.") + "\n\n"
    else:
        resposta_formatada += resposta

    resposta_formatada += "\n### Links das fontes:\n"
    for idx, link in enumerate(links, 1):
        resposta_formatada += f"{idx}. [Visite o site]({link})\n"

    return resposta_formatada

# Função para consultar Wikipedia
def consultar_wikipedia(frase):
    wikipedia.set_lang("pt")
    try:
        pesquisa = wikipedia.search(frase, results=1)
    except wikipedia.exceptions.WikipediaException:
        return "Erro ao realizar a pesquisa na Wikipedia."
    
    if not pesquisa:
        return "Nenhum resultado encontrado na Wikipedia."
    
    wikipage = wikipedia.page(pesquisa[0])
    resumo = wikipedia.summary(wikipage.title, sentences=5)
    
    resposta = f"**Wikipedia**: \n**Título**: {wikipage.title}\n**Resumo**: {resumo}\n**Link**: {wikipage.url}\n"
    return resposta

# Funções de rastreamento na web (Bing e DuckDuckGo)
def rastrear_bing(query):
    url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        resultados = [
            {
                "titulo": item.find('h2').get_text(),
                "descricao": item.find('p').get_text(),
                "link": item.find('a')['href']
            }
            for item in soup.find_all('li', {'class': 'b_algo'}, limit=3)
        ]
        return resultados if resultados else ["Nenhum resultado encontrado."]
    except requests.exceptions.RequestException as e:
        return [f"Erro ao acessar a web: {e}"]

def rastrear_duckduckgo(query):
    url = f"https://duckduckgo.com/html/?q={query.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        resultados = [
            {
                "titulo": item.get_text(),
                "descricao": item.get('title', 'Sem descrição'),
                "link": item['href']
            }
            for item in soup.find_all('a', {'class': 'result__a'}, limit=3)
        ]
        return resultados if resultados else ["Nenhum resultado encontrado."]
    except requests.exceptions.RequestException as e:
        return [f"Erro ao acessar a web: {e}"]

# Rota para processar perguntas
@app.route('/pergunta', methods=['POST'])
def perguntar():
    dados = request.get_json()
    pergunta = dados.get("pergunta", "")
    
    if not pergunta:
        return jsonify({"erro": "Nenhuma pergunta foi recebida."}), 400
    
    resposta, links = processar_pergunta(pergunta)  # Agora retorna tanto resposta quanto os links
    return jsonify({"resposta": formatar_resposta(resposta, links)})

# Rota inicial
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)