# arquivo: recomendador_git.py
# Para rodar: streamlit run recomendador_git.py

import streamlit as st
import pandas as pd
import ast
import os
from abc import ABC, abstractmethod
from typing import List, Union, Dict, Set, Tuple
from collections import deque, defaultdict

# =========================
# CONFIG STREAMLIT
# =========================
st.set_page_config(page_title="Recomendador de Filmes & Séries", layout="centered")

# =========================
# 1) MODELO DE DADOS
# =========================
class Midia(ABC):
    def __init__(self, title: str, genres: List[str], vote_average: float):
        self._title = str(title)
        self._genres = [g for g in (genres or []) if str(g).strip()]
        self._vote_average = float(vote_average) if pd.notna(vote_average) else 0.0

    @property
    def title(self): return self._title
    @property
    def genres(self): return self._genres
    @property
    def vote_average(self): return self._vote_average

    @abstractmethod
    def exibir_info(self) -> str: ...

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

# =========================
# 2) INTERFACES / SOLID
# =========================
class Recomendavel(ABC):
    @abstractmethod
    def recomendar(self, criterio: Union[str, Midia], n=5) -> List[Midia]: ...

class RecomendadorMidias(Recomendavel):
    """Alta coesão e baixo acoplamento: trabalha contra abstrações (Midia)."""
    def __init__(self, midias: List[Midia]):
        self._midias = midias

    def recomendar(self, criterio: Union[str, Midia], n=5) -> List[Midia]:
        if isinstance(criterio, str):
            return self._por_genero(criterio, n)
        elif isinstance(criterio, Midia):
            return self._por_item(criterio, n)
        return []

    def _por_genero(self, genero: str, n=5) -> List[Midia]:
        alvo = genero.strip().lower()
        flt = [m for m in self._midias if any(g.lower() == alvo for g in m.genres)]
        return sorted(flt, key=lambda x: x.vote_average, reverse=True)[:n]

    def _por_item(self, base: Midia, n=5) -> List[Midia]:
        base_gen = set(g.lower() for g in base.genres)
        cand = [m for m in self._midias if m.title.lower() != base.title.lower()]
        scored = []
        for m in cand:
            inter = len(base_gen.intersection(g.lower() for g in m.genres))
            scored.append((m, inter))
        scored = sorted(scored, key=lambda x: (x[1], x[0].vote_average), reverse=True)
        return [m for m, s in scored if s > 0][:n]

# =========================
# 3) TABELA HASH + GRAFO + BFS
# =========================
class GenreGraph:
    """Grafo não-direcionado de coocorrência de gêneros usando dict/set (hash)."""
    def __init__(self):
        self.adj: Dict[str, Set[str]] = defaultdict(set)

    def add_midia(self, midia: Midia):
        gs = [g.lower() for g in midia.genres]
        for i in range(len(gs)):
            for j in range(i + 1, len(gs)):
                a, b = gs[i], gs[j]
                self.adj[a].add(b)
                self.adj[b].add(a)

    def bfs(self, start: str, max_depth: int = 2) -> List[Tuple[str, int]]:
        start = start.lower()
        visitados: Set[str] = set([start])
        ordem: List[Tuple[str, int]] = []
        fila = deque([(start, 0)])
        while fila:
            g, d = fila.popleft()
            ordem.append((g, d))
            if d == max_depth:
                continue
            for viz in self.adj[g]:
                if viz not in visitados:
                    visitados.add(viz)
                    fila.append((viz, d + 1))
        return ordem

def recomendar_por_bfs(grafo: GenreGraph, base_genero: str, universo: List[Midia], n: int = 10) -> List[Midia]:
    """Usa distâncias de gêneros via BFS para ranquear recomendações."""
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

# =========================
# 4) RECURSÃO (demonstração simples)
# =========================
def recomendar_recursivo(midia_base: Midia, universo: List[Midia], profundidade: int, visitados: Set[str] = None) -> List[Midia]:
    if visitados is None:
        visitados = set([midia_base.title.lower()])
    if profundidade == 0:
        return []
    rec_nivel = RecomendadorMidias(universo).recomendar(midia_base, n=5)
    rec_filtradas = [m for m in rec_nivel if m.title.lower() not in visitados]
    for m in rec_filtradas:
        visitados.add(m.title.lower())
    resultado = rec_filtradas[:]
    for m in rec_filtradas:
        resultado += recomendar_recursivo(m, universo, profundidade - 1, visitados)
    seen, dedup = set(), []
    for x in resultado:
        if x.title not in seen:
            dedup.append(x)
            seen.add(x.title)
    return dedup

# =========================
# 5) LOADERS ROBUSTOS (pandas 2.x, IMDb, CSV/TSV/GZIP)
# =========================
IMDB_NA = ["", "NA", "NaN", r"\N"]  # r"\N" evita erro de unicodeescape

def _read_any(path: str, sep_hint: str = "\t") -> pd.DataFrame:
    """
    Lê CSV/TSV (normal ou .gz) com opções seguras para pandas 2.x.
    """
    # 1) tenta com separador sugerido
    try:
        return pd.read_csv(
            path,
            sep=sep_hint,
            low_memory=False,
            encoding="utf-8",
            na_values=IMDB_NA,
            on_bad_lines="skip",
            compression="infer",
        )
    except Exception:
        pass
    # 2) inferir separador
    try:
        return pd.read_csv(
            path,
            sep=None,
            engine="python",
            low_memory=False,
            encoding="utf-8",
            na_values=IMDB_NA,
            on_bad_lines="skip",
            compression="infer",
        )
    except Exception as e:
        raise RuntimeError(f"Falha ao ler arquivo '{path}': {e}")

def _parse_genres_any(cell) -> List[str]:
    """Aceita JSON (TMDB), string separada por vírgulas ou por pipes."""
    if pd.isna(cell): return []
    s = str(cell).strip()
    if not s: return []
    # JSON estilo TMDB: [{"id":..,"name":"Action"}, ...] ou ["Action","Comedy"]
    try:
        val = ast.literal_eval(s)
        if isinstance(val, list):
            if val and isinstance(val[0], dict):
                return [str(d.get("name", "")).strip() for d in val if d.get("name")]
            return [str(x).strip() for x in val if str(x).strip()]
    except Exception:
        pass
    # "Action, Comedy" ou "Action|Comedy"
    parts = s.split("|") if "|" in s else s.split(",")
    return [p.strip() for p in parts if p.strip() and p.strip() != r"\N"]

def _first_existing(df: pd.DataFrame, candidates: List[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None

@st.cache_data(show_spinner=False)
def carregar_filmes(filmes_path: str) -> List[Filme]:
    df = _read_any(filmes_path, sep_hint=",")
    title_col    = _first_existing(df, ["title", "original_title", "name"])
    genres_col   = _first_existing(df, ["genres", "listed_in", "genre_names"])
    rating_col   = _first_existing(df, ["vote_average", "rating", "averageRating", "score"])
    date_col     = _first_existing(df, ["release_date", "year", "releaseYear"])
    director_col = _first_existing(df, ["director", "diretor"])

    if title_col is None or genres_col is None:
        st.warning("Colunas obrigatórias não encontradas no CSV de filmes (title/genres).")
        return []

    keep = [c for c in [title_col, genres_col, rating_col, date_col, director_col] if c]
    df = df[keep].copy()
    df["_genres_parsed"] = df[genres_col].apply(_parse_genres_any)

    def _year_from(x):
        s = str(x)
        try:
            if len(s) >= 4 and s[:4].isdigit():
                return int(s[:4])
        except Exception:
            pass
        return None

    df["_year"] = df[date_col].apply(_year_from) if date_col else None
    df["_rating"] = pd.to_numeric(df[rating_col], errors="coerce").fillna(0.0) if rating_col else 0.0

    df = df.dropna(subset=[title_col]).copy()
    df = df[df["_genres_parsed"].apply(lambda g: len(g) > 0)]

    filmes: List[Filme] = []
    for _, row in df.iterrows():
        filmes.append(
            Filme(
                title=row[title_col],
                genres=row["_genres_parsed"],
                vote_average=row["_rating"],
                diretor=row.get(director_col) if director_col else None,
                year=row.get("_year"),
            )
        )
    return filmes

@st.cache_data(show_spinner=False)
def carregar_series(imdb_basics_path: str, imdb_ratings_path: str, min_votes: int = 500) -> List[Serie]:
    basics = _read_any(imdb_basics_path, sep_hint="\t")
    ratings = _read_any(imdb_ratings_path, sep_hint="\t")

    if "titleType" not in basics.columns:
        st.warning("Coluna 'titleType' ausente em basics.")
        return []

    basics = basics[basics["titleType"].isin(["tvSeries", "tvMiniSeries"])].copy()

    if "startYear" in basics.columns:
        basics["startYear"] = pd.to_numeric(basics["startYear"], errors="coerce")
    if "endYear" in basics.columns:
        basics["endYear"] = pd.to_numeric(basics["endYear"], errors="coerce")

    if "genres" in basics.columns:
        basics["genres"] = (
            basics["genres"]
            .fillna("")
            .replace(r"\N", "", regex=False)
            .astype(str)
            .apply(_parse_genres_any)
        )

    df = basics.merge(ratings, on="tconst", how="left")
    df["averageRating"] = pd.to_numeric(df.get("averageRating", 0.0), errors="coerce")
    df["numVotes"] = pd.to_numeric(df.get("numVotes", 0), errors="coerce").fillna(0).astype("Int64")

    if min_votes:
        df = df[df["numVotes"] >= int(min_votes)]

    series: List[Serie] = []
    for _, r in df.iterrows():
        series.append(
            Serie(
                tconst=r.get("tconst"),
                title=r.get("primaryTitle"),
                genres=r.get("genres", []),
                vote_average=float(r.get("averageRating")) if pd.notna(r.get("averageRating")) else 0.0,
                start_year=int(r.get("startYear")) if pd.notna(r.get("startYear")) else None,
                end_year=int(r.get("endYear")) if pd.notna(r.get("endYear")) else None,
                num_votes=int(r.get("numVotes")) if pd.notna(r.get("numVotes")) else None,
            )
        )
    return series

def construir_grafo(filmes: List[Filme], series: List[Serie]) -> GenreGraph:
    G = GenreGraph()
    for m in filmes + series:
        G.add_midia(m)
    return G

# =========================
# 6) CAMINHOS DOS DADOS
# =========================
FILMES_CSV = "data/archive_min.csv"
IMDB_BASICS = "data/title.basics.tsv"
IMDB_RATINGS = "data/title.ratings.min.tsv"

# =========================
# 7) UI
# =========================
def main():
    st.title("🍿 Recomendador de Filmes & Séries")

    universo_escolhido = st.radio(
        "Você quer recomendação de **Filmes** ou **Séries**?",
        ["Filmes", "Séries"], horizontal=True
    )

    # Mensagem clara se faltar arquivo no deploy
    missing = [p for p in [FILMES_CSV, IMDB_BASICS, IMDB_RATINGS] if not os.path.exists(p)]
    if missing:
        st.warning("Arquivos ausentes: " + ", ".join(f"`{m}`" for m in missing))

    with st.spinner("Carregando dados..."):
        filmes = carregar_filmes(FILMES_CSV)
        series = carregar_series(IMDB_BASICS, IMDB_RATINGS, min_votes=500)
        grafo = construir_grafo(filmes, series)

    with st.expander("🔎 Visualização lógica do grafo de gêneros (BFS)"):
        todos_generos = sorted({g for m in filmes+series for g in m.genres}) or ["Drama"]
        genero_seed = st.selectbox("Gênero inicial", todos_generos)
        depth = st.slider("Profundidade BFS", 1, 3, 2)
        ordem = grafo.bfs(genero_seed, max_depth=depth)
        st.write("Ordem (gênero, distância):", ordem)

    if universo_escolhido == "Filmes":
        rec_filmes = RecomendadorMidias(filmes)

        st.subheader("🎬 Recomendações de Filmes")
        modo = st.radio("Tipo de recomendação", ["Por título", "Por gênero"], key="modo_filmes")
        n = st.slider("Quantidade", 1, 20, 5, key="n_filmes")

        if modo == "Por título":
            titulos = sorted([m.title for m in filmes]) if filmes else []
            tit = st.selectbox("Escolha um filme", titulos, key="sel_filme")
            alvo_filme = next((m for m in filmes if m.title == tit), None)

            if alvo_filme:
                col1, col2 = st.columns(2)
                if col1.button("Obter recomendações (simples)", key="btn_filmes_title"):
                    resultados = rec_filmes.recomendar(alvo_filme, n=n)
                    st.success(f"🎯 Baseado em: {alvo_filme.title}")
                    for r in resultados:
                        st.write(r.exibir_info())

                if col2.button("Explorar recursivo (2 níveis)", key="btn_filmes_rec"):
                    recs = recomendar_recursivo(alvo_filme, filmes, profundidade=2)
                    for r in recs[:n]:
                        st.write(r.exibir_info())

                st.markdown("#### 📺 Séries parecidas (pelos mesmos gêneros)")
                base_gen = alvo_filme.genres[0] if alvo_filme.genres else "Drama"
                cross = recomendar_por_bfs(grafo, base_gen, series, n=min(5, n))
                if cross:
                    for c in cross: st.write(c.exibir_info())
                else:
                    st.caption("Sem séries com gêneros compatíveis.")

        else:
            generos = sorted({g for m in filmes for g in m.genres}) if filmes else []
            genero = st.selectbox("Escolha um gênero", generos, key="gen_filmes")
            modo_gen = st.radio("Como recomendar por gênero?", ["Simples", "Via BFS (grafo)"], key="modo_gen_filmes")

            if st.button("Obter recomendações", key="btn_filmes_gen"):
                if modo_gen == "Via BFS (grafo)":
                    resultados = recomendar_por_bfs(grafo, genero, filmes, n=n)
                else:
                    resultados = rec_filmes.recomendar(genero, n=n)

                if resultados:
                    for r in resultados: st.write(r.exibir_info())
                    st.markdown("#### 📺 Séries parecidas (mesmo gênero/BFS)")
                    rec_series = recomendar_por_bfs(grafo, genero, series, n=min(5, n))
                    if rec_series:
                        for c in rec_series: st.write(c.exibir_info())
                    else:
                        st.caption("Sem séries desse gênero com votos suficientes.")
                else:
                    st.warning("Nada encontrado para esse gênero nos filmes.")

    else:
        rec_series = RecomendadorMidias(series)

        st.subheader("📺 Recomendações de Séries")
        modo = st.radio("Tipo de recomendação", ["Por título", "Por gênero"], key="modo_series")
        n = st.slider("Quantidade", 1, 20, 5, key="n_series")

        if modo == "Por título":
            titulos = sorted([s.title for s in series]) if series else []
            tit = st.selectbox("Escolha uma série", titulos, key="sel_serie")
            alvo_serie = next((s for s in series if s.title == tit), None)

            if alvo_serie:
                col1, col2 = st.columns(2)
                if col1.button("Obter recomendações (simples)", key="btn_series_title"):
                    resultados = rec_series.recomendar(alvo_serie, n=n)
                    st.success(f"🎯 Baseado em: {alvo_serie.title}")
                    for r in resultados:
                        st.write(r.exibir_info())

                if col2.button("Explorar recursivo (2 níveis)", key="btn_series_rec"):
                    recs = recomendar_recursivo(alvo_serie, series, profundidade=2)
                    for r in recs[:n]:
                        st.write(r.exibir_info())
                
                st.markdown("#### 🎬 Filmes parecidos (pelos mesmos gêneros)")
                base_gen = alvo_serie.genres[0] if alvo_serie.genres else "Drama"
                cross = recomendar_por_bfs(grafo, base_gen, filmes, n=min(5, n))
                if cross:
                    for c in cross: st.write(c.exibir_info())
                else:
                    st.caption("Sem filmes com gêneros compatíveis.")

        else:
            generos = sorted({g for s in series for g in s.genres}) if series else []
            genero = st.selectbox("Escolha um gênero", generos, key="gen_series")
            modo_gen = st.radio("Como recomendar por gênero?", ["Simples", "Via BFS (grafo)"], key="modo_gen_series")

            if st.button("Obter recomendações", key="btn_series_gen"):
                if modo_gen == "Via BFS (grafo)":
                    resultados = recomendar_por_bfs(grafo, genero, series, n=n)
                else:
                    resultados = rec_series.recomendar(genero, n=n)

                if resultados:
                    for r in resultados: st.write(r.exibir_info())
                    st.markdown("#### 🎬 Filmes parecidos (mesmo gênero/BFS)")
                    rec_filmes = recomendar_por_bfs(grafo, genero, filmes, n=min(5, n))
                    if rec_filmes:
                        for c in rec_filmes: st.write(c.exibir_info())
                    else:
                        st.caption("Sem filmes desse gênero.")
                else:
                    st.warning("Nada encontrado para esse gênero nas séries.")

if __name__ == "__main__":
    main()









