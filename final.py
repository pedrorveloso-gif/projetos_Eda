import streamlit as st # Biblioteca para criar interface
import pandas as pd # Manipulação de dados com DataFrames
import zipfile # Leitura de arquivos zip
import ast  # Para interpretar strings como estruturas Python (ex: listas, dicionários)

zip_path = "C:/Users/pedro/OneDrive/Documentos/projeto eda/archive.zip"

with zipfile.ZipFile(zip_path) as z:
    credits= pd.read_csv(z.open('credits.csv'))
    keywords= pd.read_csv(z.open('keywords.csv'))
    links= pd.read_csv(z.open('links.csv'))
    links_small= pd.read_csv(z.open('links_small.csv'))
    movies_metadata= pd.read_csv(z.open('movies_metadata.csv'), low_memory=False)
    ratings= pd.read_csv(z.open('ratings.csv'))
    ratings_small= pd.read_csv(z.open('ratings_small.csv'))

#Escolha do arquivo movies_metadata por ser mais útil para o sistema
movies = movies_metadata


# ======================
# CLASSE RECOMENDADOR
# ======================

class Recomendador:
    def __init__(self, df):
        self.df = df.copy()
        self._preparar_dados()

    def _preparar_dados(self):
        self.df = self.df[['title', 'genres', 'vote_average']].dropna()
        self.df['genres'] = self.df['genres'].apply(self._converter_generos)

    def _converter_generos(self, generos_str):
        try:
            generos = ast.literal_eval(generos_str)
            return [g['name'] for g in generos]
        except:
            return []

    def recomendar_por_filme(self, titulo, n=5):
        filme_base = self.df[self.df['title'].str.lower().str.contains(titulo.lower(), regex=False)]

        if filme_base.empty:
            return None, f"❌ Filme contendo '{titulo}' não encontrado."

        filme_escolhido = filme_base.iloc[0]
        generos_base = set(filme_escolhido['genres'])
        
        # Auxilio do gpt para escolha do método intersections
        def score(filme):
            return len(generos_base.intersection(set(filme['genres'])))

        self.df['score'] = self.df.apply(score, axis=1)
        recomendados = self.df[self.df['title'].str.lower() != filme_escolhido['title'].lower()]
        recomendados = recomendados[recomendados['score'] > 0]
        recomendados = recomendados.sort_values(by=['score', 'vote_average'], ascending=False)

        info_filme = {
            "title": filme_escolhido['title'],
            "genres": filme_escolhido['genres'],
            "vote_average": filme_escolhido['vote_average']
        }

        return recomendados[['title', 'genres', 'vote_average']].head(n), info_filme

    def recomendar_por_genero(self, genero, n=5):
        genero = genero.capitalize()
        filtrados = self.df[self.df['genres'].apply(lambda g: genero in g)]

        if filtrados.empty:
            return None, f"❌ Nenhum filme encontrado com o gênero '{genero}'."

        recomendados = filtrados.sort_values(by='vote_average', ascending=False).head(n)
        return recomendados[['title', 'genres', 'vote_average']], None

# ======================
# STREAMLIT APP
# ======================

st.set_page_config(page_title="Recomendador de Filmes", layout="centered")
st.title("🎬 Sistema de Recomendação de Filmes")

# Carregando dados

recomendador = Recomendador(movies)

# Opções do usuário
tipo = st.radio("📌 Escolha o tipo de recomendação:", ["Por filme", "Por gênero"])

entrada = st.text_input("Digite o nome do filme ou o gênero:")

n = st.slider("Quantidade de recomendações:", min_value=1, max_value=20, value=5)

if st.button("🔍 Obter recomendações"):
    if tipo == "Por filme":
        resultado, info = recomendador.recomendar_por_filme(entrada, n=n)

        if resultado is None:
            st.warning(info)
        else:
            st.success(f"🎯 Baseado no filme: {info['title']}")
            st.write(f"🎭 Gêneros: {info['genres']}")
            st.write(f"⭐ Nota média: {info['vote_average']}")
            st.subheader("📽️ Recomendações:")
            st.dataframe(resultado)
    else:
        resultado, erro = recomendador.recomendar_por_genero(entrada, n=n)

        if resultado is None:
            st.warning(erro)
        else:
            st.success(f"🎬 Melhores filmes do gênero '{entrada.capitalize()}':")
            st.dataframe(resultado)

