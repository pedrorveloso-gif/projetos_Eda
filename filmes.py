import streamlit as st
import pandas as pd
import ast
import zipfile
import sys
from abc import ABC, abstractmethod

# =========================
# MODELO DE DADOS
# =========================

# Criação de uma hierarquia 
class Midia(ABC):
    def __init__(self, title, genres, vote_average):
        self._title = title
        self._genres = genres
        self._vote_average = vote_average

    # Encapsulamento com properties, atribuindo atributos privados
    @property
    def title(self):
        return self._title

    @property
    def genres(self):
        return self._genres

    @property
    def vote_average(self):
        return self._vote_average

    @abstractmethod
    def exibir_info(self):
        pass

# Herança: Filme herda de Midia e reaproveita/expande o comportamento.
class Filme(Midia):
    def __init__(self, title, genres, vote_average, diretor=None):
        super().__init__(title, genres, vote_average)
        self._diretor = diretor

    @property
    def diretor(self):
        return self._diretor
    # Polimorfismo (um mesmo método (exibir_info) pode ter comportamentos diferentes dependendo da subclasse.)
    def exibir_info(self):
        return f"🎬 {self.title} | Gêneros: {', '.join(self.genres)} | Nota: {self.vote_average}"


# =========================
# INTERFACE RECOMENDÁVEL
# =========================

class Recomendavel(ABC):
    @abstractmethod
    def recomendar(self, criterio, n=5):
        pass


# =========================
# SISTEMA DE RECOMENDAÇÃO
# =========================

#  Camada de regras de negócio: mantém o catálogo e calcula recomendações.
class RecomendadorFilmes(Recomendavel):
    def __init__(self, filmes):
        self._filmes = filmes  # lista de objetos Filme
    # Branch 1: ordenar por similaridade e desempatar por nota
    def recomendar(self, criterio, n=5):
        if isinstance(criterio, str):
            return self._recomendar_por_genero(criterio, n)
        elif isinstance(criterio, Filme):
            return self._recomendar_por_filme(criterio, n)
        else:
            return []
    # Branch 2: filtra por gênero e ordena por nota
    def _recomendar_por_genero(self, genero, n=5):
        genero = genero.capitalize()
        filtrados = [f for f in self._filmes if genero in f.genres]
        filtrados = sorted(filtrados, key=lambda x: x.vote_average, reverse=True)
        return filtrados[:n]
    # Branch 3: filtra por filme e ordena por nota
    def _recomendar_por_filme(self, filme_base, n=5):
        generos_base = set(filme_base.genres)
        similares = [f for f in self._filmes if f.title != filme_base.title]

        # cálculo de score baseado em gêneros
        similares = [(f, len(generos_base.intersection(f.genres))) for f in similares]
        similares = [f for f, score in sorted(similares, key=lambda x: (x[1], x[0].vote_average), reverse=True) if score > 0]
        return similares[:n]


# =========================
# FUNÇÃO DE CARREGAR DADOS
# =========================

# Carregamos o caminho zip e monstamos a tabela
def carregar_filmes(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        movies_metadata = pd.read_csv(z.open('movies_metadata.csv'), low_memory=False)

    filmes = []
    # normalização dos gêneros 
    for _, row in movies_metadata[['title', 'genres', 'vote_average']].dropna().iterrows():
        try:
            generos = ast.literal_eval(row['genres'])
            generos = [g['name'] for g in generos]
        except:
            generos = []
        filmes.append(Filme(row['title'], generos, row['vote_average']))
    return filmes


# =========================
# INTERFACE TERMINAL
# =========================

# Opcão da UI (interface do usuário) pelo terminal
def modo_terminal(recomendador):
    print("📢 Escolha o tipo de recomendação:")
    print("1 - Por filme")
    print("2 - Por gênero")
    opcao = input("Digite 1 ou 2: ")

    if opcao == "1":
        filme = input("Digite o nome do filme: ")
        filme_obj = next((f for f in recomendador._filmes if f.title.lower() == filme.lower()), None)
        if not filme_obj:
            print(f"❌ Filme '{filme}' não encontrado.")
            return
        resultados = recomendador.recomendar(filme_obj, n=5)
        print(f"\n🎯 Baseado no filme: {filme_obj.exibir_info()}")
        print("\n📽️ Recomendações:")
        for r in resultados:
            print(r.exibir_info())

    elif opcao == "2":
        genero = input("Digite o gênero (ex: Action, Drama, Comedy): ")
        resultados = recomendador.recomendar(genero, n=5)
        if not resultados:
            print(f"❌ Nenhum filme encontrado com o gênero '{genero}'.")
        else:
            print(f"\n🎬 Melhores filmes do gênero '{genero.capitalize()}':")
            for r in resultados:
                print(r.exibir_info())
    else:
        print("❌ Opção inválida.")


# =========================
# INTERFACE STREAMLIT
# =========================

# Opção da UI no streamlit
def modo_streamlit(recomendador):
    st.set_page_config(page_title="Recomendador de Filmes", layout="centered")
    st.title("🎬 Sistema de Recomendação de Filmes")

    tipo = st.radio("📌 Escolha o tipo de recomendação:", ["Por filme", "Por gênero"])
    entrada = st.text_input("Digite o nome do filme ou o gênero:")
    n = st.slider("Quantidade de recomendações:", min_value=1, max_value=20, value=5)

    if st.button("🔍 Obter recomendações"):
        if not entrada.strip():
            st.warning("Por favor, digite um nome válido.")
        else:
            if tipo == "Por filme":
                filme_obj = next((f for f in recomendador._filmes if f.title.lower() == entrada.lower()), None)
                if not filme_obj:
                    st.warning(f"❌ Filme '{entrada}' não encontrado.")
                else:
                    resultados = recomendador.recomendar(filme_obj, n=n)
                    st.success(f"🎯 Baseado no filme: {filme_obj.title}")
                    st.write(f"🎭 Gêneros: {', '.join(filme_obj.genres)}")
                    st.write(f"⭐ Nota média: {filme_obj.vote_average}")
                    st.subheader("📽️ Recomendações:")
                    for r in resultados:
                        st.write(r.exibir_info())
            else:
                resultados = recomendador.recomendar(entrada, n=n)
                if not resultados:
                    st.warning(f"❌ Nenhum filme encontrado com o gênero '{entrada}'.")
                else:
                    st.success(f"🎬 Melhores filmes do gênero '{entrada.capitalize()}':")
                    for r in resultados:
                        st.write(r.exibir_info())


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    zip_path = "C:/Users/pedro/OneDrive/Documentos/projeto eda/archive.zip"  # <-- ajusta se mudar caminho
    filmes = carregar_filmes(zip_path)
    recomendador = RecomendadorFilmes(filmes)

    if len(sys.argv) > 1 and sys.argv[1] == "terminal":
        modo_terminal(recomendador)
    else:
        # Rodar no terminal: python arquivo.py terminal
        # Rodar no streamlit: streamlit run arquivo.py
        modo_streamlit(recomendador)


