# app_streamlit.py
import io
import ast
import zipfile
from pathlib import Path
from typing import List, Union, Dict, Set, Tuple
from collections import deque, defaultdict

import pandas as pd
import streamlit as st

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Recomendador de Filmes & Séries", layout="centered")

BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
ZIP_FILMES_PATH = DATA_DIR / "archive.zip"                  # deve conter movies_metadata.csv
IMDB_BASICS_PATH = DATA_DIR / "title.basics.min.tsv.gz"     # recomendado (minificado)
IMDB_RATINGS_PATH = DATA_DIR / "title.ratings.min.tsv.gz"

# =========================
# 1) MODELO / LÓGICA
# =========================
class Midia:
    def __init__(self, title: str, genres: List[str], vote_average: float):
        self._title = str(title)
        self._genres = [g for g in genres if g]
        self._vote_average = float(vote_average) if pd.notna(vote_average) else 0.0

    @property
    def title(self): return self._title
    @property
    def genres(self): return self._genres
    @property
    def vote_average(self): return self._vote_average
    def exibir_info(self) -> str: raise NotImplementedError

class Filme(Midia):
    def __init__(self, title, genres, vote_average, diretor=None, year=None):
        super().__init__(title, genres, vote_average)
        self._diretor = diretor
        self._year = year
    def exibir_info(self):
        year_txt = f" ({self._year})" if self._year else ""
        gen = ", ".join(self.genres) if self.genres else "—"
        return f"🎬 {self.title}{year_txt} | Gêneros: {gen} | Nota: {self.vote_average:.1f}"

class Serie(Midia):
    def __init__(self, tconst, title, genres, vote_average, start_year=None, end_year=None, num_votes=None):
        super().__init__(title, genres, vote_average)
        self._tconst = tconst
        self._start_year = start_year
        self._end_year = end_year
        self._num_votes = int(num_votes) if pd.notna(num_votes) else None
    def exibir_info(self):
        anos = ""
        if self._start_year and self._end_year:
            anos = f" ({self._start_year}–{self._end_year})"
        elif self._start_year:
            anos = f" ({self._start_year}–)"
        gen = ", ".join(self.genres) if self.genres else "—"
        votos = f" | Votos: {self._num_votes}" if self._num_votes else ""
        return f"📺 {self.title}{anos} | Gêneros: {gen} | Nota: {self.vote_average:.1f}{votos}"

class RecomendadorMidias:
    def __init__(self, midias: List[Midia]):
        self._midias = midias
    def recomendar(self, criterio: Union[str, Midia], n=5) -> List[Midia]:
        if isinstance(criterio, str):
            alvo = criterio.strip().lower()
            flt = [m for m in self._midias if any(g.lower() == alvo for g in m.genres)]
            return sorted(flt, key=lambda x: x.vote_average, reverse=True)[:n]
        elif isinstance(criterio, Midia):
            base_gen = set(g.lower() for g in criterio.genres)
            cand = [m for m in self._midias if m.title.lower() != criterio.title.lower()]
            scored = []
            for m in cand:
                inter = len(base_gen.intersection(g.lower() for g in m.genres))
                scored.append((m, inter))
            scored = sorted(scored, key=lambda x: (x[1], x[0].vote_average), reverse=True)
            return [m for m, s in scored if s > 0][:n]
        return []

class GenreGraph:
    def __init__(self):
        self.adj: Dict[str, Set[str]] = defaultdict(set)
    def add_midia(self, midia: Midia):
        gs = [g.lower() for g in midia.genres]
        for i in range(len(gs)):
            for j in range(i + 1, len(gs)):
                a, b = gs[i], gs[j]
                self.adj[a].add(b); self.adj[b].add(a)
    def bfs(self, start: str, max_depth: int = 2) -> List[Tuple[str, int]]:
        start = start.lower()
        visitados: Set[str] = {start}
        ordem: List[Tuple[str, int]] = []
        fila = deque([(start, 0)])
        while fila:
            g, d = fila.popleft()
            ordem.append((g, d))
            if d == max_depth: continue
            for viz in self.adj[g]:
                if viz not in visitados:
                    visitados.add(viz)
                    fila.append((viz, d + 1))
        return ordem

def recomendar_por_bfs(grafo: GenreGraph, base_genero: str, universo: List[Midia], n: int = 10) -> List[Midia]:
    fronteira = grafo.bfs(base_genero, max_depth=2)
    prioridades = {g: d for g, d in fronteira}
    candidatos = []
    for m in universo:
        inter = [g.lower() for g in m.genres if g.lower() in prioridades]
        if inter:
            melhor = min(prioridades[g] for g in inter)
            candidatos.append((melhor, -m.vote_average, m))
    candidatos.sort(key=lambda t: (t[0], t[1]))
    return [m for _, _, m in candidatos][:n]

def recomendar_recursivo(midia_base: Midia, universo: List[Midia], profundidade: int, visitados: Set[str] = None) -> List[Midia]:
    if visitados is None: visitados = {midia_base.title.lower()}
    if profundidade == 0: return []
    rec_nivel = RecomendadorMidias(universo).recomendar(midia_base, n=5)
    rec_filtradas = [m for m in rec_nivel if m.title.lower() not in visitados]
    for m in rec_filtradas: visitados.add(m.title.lower())
    resultado = rec_filtradas[:]
    for m in rec_filtradas:
        resultado += recomendar_recursivo(m, universo, profundidade - 1, visitados)
    seen, dedup = set(), []
    for x in resultado:
        if x.title not in seen:
            dedup.append(x); seen.add(x.title)
    return dedup

# =========================
# 2) LOADERS + CACHE
# =========================
def _limpa_generos_tmdb(cell):
    try:
        lista = ast.literal_eval(cell)
        return [d.get("name", "").strip() for d in lista if d.get("name")]
    except Exception:
        return []

@st.cache_data(show_spinner=False)
def carregar_filmes_de_zip_path(path: str) -> List[Filme]:
    with zipfile.ZipFile(path) as z:
        df = pd.read_csv(z.open("movies_metadata.csv"), low_memory=False)
    cols = [c for c in ["title", "genres", "vote_average", "release_date"] if c in df.columns]
    df = df[cols].dropna(subset=["title", "genres"]).copy()
    filmes: List[Filme] = []
    for _, row in df.iterrows():
        generos = _limpa_generos_tmdb(row["genres"])
        year = None
        if pd.notna(row.get("release_date")) and str(row["release_date"]).strip():
            year = str(row["release_date"])[:4]
        filmes.append(Filme(row["title"], generos, row.get("vote_average", 0), year=year))
    return filmes

@st.cache_data(show_spinner=False)
def carregar_filmes_de_zip_bytes(zip_bytes: bytes) -> List[Filme]:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        df = pd.read_csv(z.open("movies_metadata.csv"), low_memory=False)
    cols = [c for c in ["title", "genres", "vote_average", "release_date"] if c in df.columns]
    df = df[cols].dropna(subset=["title", "genres"]).copy()
    filmes: List[Filme] = []
    for _, row in df.iterrows():
        generos = _limpa_generos_tmdb(row["genres"])
        year = None
        if pd.notna(row.get("release_date")) and str(row["release_date"]).strip():
            year = str(row["release_date"])[:4]
        filmes.append(Filme(row["title"], generos, row.get("vote_average", 0), year=year))
    return filmes

@st.cache_data(show_spinner=False)
def carregar_series_de_paths(basics_path: str, ratings_path: str, min_votes: int) -> List[Serie]:
    basics = pd.read_csv(basics_path, sep="\t", low_memory=False, na_values="\\N", compression="infer")
    ratings = pd.read_csv(ratings_path, sep="\t", low_memory=False, na_values="\\N", compression="infer")
    basics = basics[basics["titleType"].isin(["tvSeries", "tvMiniSeries"])].copy()
    df = basics.merge(ratings, on="tconst", how="left")
    df["averageRating"] = pd.to_numeric(df["averageRating"], errors="coerce")
    df["numVotes"] = pd.to_numeric(df["numVotes"], errors="coerce")
    if min_votes > 0: df = df[df["numVotes"] >= min_votes]
    def split_gen(gen):
        if pd.isna(gen): return []
        return [g.strip() for g in str(gen).split(",") if g and g.strip() != "\\N"]
    out = []
    for _, r in df.iterrows():
        out.append(Serie(
            tconst=r["tconst"],
            title=str(r["primaryTitle"]),
            genres=split_gen(r.get("genres")),
            vote_average=r.get("averageRating", 0),
            start_year=int(r["startYear"]) if pd.notna(r.get("startYear")) else None,
            end_year=int(r["endYear"]) if pd.notna(r.get("endYear")) else None,
            num_votes=r.get("numVotes"),
        ))
    return out

@st.cache_data(show_spinner=False)
def carregar_series_de_bytes(basics_bytes: bytes, ratings_bytes: bytes, min_votes: int) -> List[Serie]:
    basics = pd.read_csv(io.BytesIO(basics_bytes), sep="\t", low_memory=False, na_values="\\N", compression="infer")
    ratings = pd.read_csv(io.BytesIO(ratings_bytes), sep="\t", low_memory=False, na_values="\\N", compression="infer")
    basics = basics[basics["titleType"].isin(["tvSeries", "tvMiniSeries"])].copy()
    df = basics.merge(ratings, on="tconst", how="left")
    df["averageRating"] = pd.to_numeric(df["averageRating"], errors="coerce")
    df["numVotes"] = pd.to_numeric(df["numVotes"], errors="coerce")
    if min_votes > 0: df = df[df["numVotes"] >= min_votes]
    def split_gen(gen):
        if pd.isna(gen): return []
        return [g.strip() for g in str(gen).split(",") if g and g.strip() != "\\N"]
    out = []
    for _, r in df.iterrows():
        out.append(Serie(
            tconst=r["tconst"],
            title=str(r["primaryTitle"]),
            genres=split_gen(r.get("genres")),
            vote_average=r.get("averageRating", 0),
            start_year=int(r["startYear"]) if pd.notna(r.get("startYear")) else None,
            end_year=int(r["endYear"]) if pd.notna(r.get("endYear")) else None,
            num_votes=r.get("numVotes"),
        ))
    return out

@st.cache_data(show_spinner=False)
def construir_grafo(filmes: List[Filme], series: List[Serie]):
    G = GenreGraph()
    for m in filmes + series:
        G.add_midia(m)
    return G

# =========================
# 3) CARGA COM FALLBACK
# =========================
def carregar_dados_interativo(min_votes=500):
    st.caption("Se os arquivos não estiverem em `data/`, você pode enviá-los por upload.")
    filmes = series = None

    if ZIP_FILMES_PATH.exists():
        filmes = carregar_filmes_de_zip_path(str(ZIP_FILMES_PATH))
    if IMDB_BASICS_PATH.exists() and IMDB_RATINGS_PATH.exists():
        series = carregar_series_de_paths(str(IMDB_BASICS_PATH), str(IMDB_RATINGS_PATH), min_votes)

    if filmes is None:
        st.warning("Arquivo de filmes não encontrado em `data/archive.zip`. Envie o ZIP com `movies_metadata.csv` dentro.")
        up_zip = st.file_uploader("📦 Envie `archive.zip`", type=["zip"], key="zip_filmes")
        if up_zip is not None:
            filmes = carregar_filmes_de_zip_bytes(up_zip.getbuffer())

    if series is None:
        st.warning("Arquivos de séries não encontrados em `data/`. Envie `title.basics*.tsv.gz` e `title.ratings*.tsv.gz`.")
        up_basics = st.file_uploader("📝 Envie `title.basics.min.tsv.gz`", type=["gz", "tsv", "tsv.gz"], key="up_basics")
        up_ratings = st.file_uploader("⭐ Envie `title.ratings.min.tsv.gz`", type=["gz", "tsv", "tsv.gz"], key="up_ratings")
        if up_basics is not None and up_ratings is not None:
            series = carregar_series_de_bytes(up_basics.getbuffer(), up_ratings.getbuffer(), min_votes)

    if filmes is None or series is None:
        st.stop()

    grafo = construir_grafo(filmes, series)
    return filmes, series, grafo

# =========================
# 4) UI
# =========================
def main():
    st.title("🍿 Recomendador de Filmes & Séries")

    universo_escolhido = st.radio(
        "Você quer recomendação de **Filmes** ou **Séries**?",
        ["Filmes", "Séries"], horizontal=True,
    )

    min_votes = st.slider("Filtro mínimo de votos (séries)", 0, 10000, 500, step=100)
    with st.spinner("Carregando dados..."):
        filmes, series, grafo = carregar_dados_interativo(min_votes=min_votes)

    # Painel do grafo
    with st.expander("🔎 Visualização lógica do grafo de gêneros (BFS)"):
        todos_generos = sorted({g for m in filmes + series for g in m.genres}) or ["Drama"]
        genero_seed = st.selectbox("Gênero inicial", todos_generos)
        depth = st.slider("Profundidade BFS", 1, 3, 2)
        st.write("Ordem (gênero, distância):", grafo.bfs(genero_seed, max_depth=depth))

    if universo_escolhido == "Filmes":
        rec_filmes = RecomendadorMidias(filmes)
        st.subheader("🎬 Recomendações de Filmes")
        modo = st.radio("Tipo de recomendação", ["Por título", "Por gênero"], key="modo_filmes")
        n = st.slider("Quantidade", 1, 20, 5, key="n_filmes")

        if modo == "Por título":
            tit = st.selectbox("Escolha um filme", sorted([m.title for m in filmes]), key="sel_filme")
            alvo = next(m for m in filmes if m.title == tit)
            c1, c2 = st.columns(2)
            if c1.button("Obter recomendações (simples)", key="btn_f_t"):
                for r in rec_filmes.recomendar(alvo, n=n): st.write(r.exibir_info())
            if c2.button("Explorar recursivo (2 níveis)", key="btn_f_r"):
                for r in recomendar_recursivo(alvo, filmes, profundidade=2)[:n]: st.write(r.exibir_info())

            st.markdown("#### 📺 Séries parecidas (pelos mesmos gêneros)")
            seed = alvo.genres[0] if alvo.genres else "Drama"
            for c in recomendar_por_bfs(grafo, seed, series, n=min(5, n)): st.write(c.exibir_info())

        else:
            genero = st.selectbox("Escolha um gênero", sorted({g for m in filmes for g in m.genres}), key="gen_filmes")
            modo_gen = st.radio("Como recomendar por gênero?", ["Simples", "Via BFS (grafo)"], key="modo_gen_filmes")
            if st.button("Obter recomendações", key="btn_filmes_gen"):
                if modo_gen == "Via BFS (grafo)":
                    resultados = recomendar_por_bfs(grafo, genero, filmes, n=n)
                else:
                    resultados = rec_filmes.recomendar(genero, n=n)
                if resultados:
                    for r in resultados: st.write(r.exibir_info())
                    st.markdown("#### 📺 Séries parecidas (mesmo gênero/BFS)")
                    for c in recomendar_por_bfs(grafo, genero, series, n=min(5, n)): st.write(c.exibir_info())
                else:
                    st.warning("Nada encontrado para esse gênero nos filmes.")

    else:
        rec_series = RecomendadorMidias(series)
        st.subheader("📺 Recomendações de Séries")
        modo = st.radio("Tipo de recomendação", ["Por título", "Por gênero"], key="modo_series")
        n = st.slider("Quantidade", 1, 20, 5, key="n_series")

        if modo == "Por título":
            tit = st.selectbox("Escolha uma série", sorted([s.title for s in series]), key="sel_serie")
            alvo = next(s for s in series if s.title == tit)
            c1, c2 = st.columns(2)
            if c1.button("Obter recomendações (simples)", key="btn_s_t"):
                for r in rec_series.recomendar(alvo, n=n): st.write(r.exibir_info())
            if c2.button("Explorar recursivo (2 níveis)", key="btn_s_r"):
                for r in recomendar_recursivo(alvo, series, profundidade=2)[:n]: st.write(r.exibir_info())

            st.markdown("#### 🎬 Filmes parecidos (pelos mesmos gêneros)")
            seed = alvo.genres[0] if alvo.genres else "Drama"
            for c in recomendar_por_bfs(grafo, seed, filmes, n=min(5, n)): st.write(c.exibir_info())

        else:
            genero = st.selectbox("Escolha um gênero", sorted({g for s in series for g in s.genres}), key="gen_series")
            modo_gen = st.radio("Como recomendar por gênero?", ["Simples", "Via BFS (grafo)"], key="modo_gen_series")
            if st.button("Obter recomendações", key="btn_series_gen"):
                if modo_gen == "Via BFS (grafo)":
                    resultados = recomendar_por_bfs(grafo, genero, series, n=n)
                else:
                    resultados = rec_series.recomendar(genero, n=n)
                if resultados:
                    for r in resultados: st.write(r.exibir_info())
                    st.markdown("#### 🎬 Filmes parecidos (mesmo gênero/BFS)")
                    for c in recomendar_por_bfs(grafo, genero, filmes, n=min(5, n)): st.write(c.exibir_info())
                else:
                    st.warning("Nada encontrado para esse gênero nas séries.")

if __name__ == "__main__":
    main()
