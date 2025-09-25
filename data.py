import pandas as pd

# ---- MINIFICAR FILMES ----
import zipfile
with zipfile.ZipFile(r"C:\Users\pedro\OneDrive\Documentos\projeto eda\archive.zip") as z:
    df = pd.read_csv(z.open("movies_metadata.csv"), low_memory=False)

cols = ["title", "genres", "vote_average", "release_date"]
df = df[cols].dropna(subset=["title", "genres"])
df.to_csv("archive_min.csv", index=False)

import zipfile
with zipfile.ZipFile("archive_min.zip", "w", zipfile.ZIP_DEFLATED) as z:
    z.write("archive_min.csv")

print("Gerado archive_min.zip")

# ---- MINIFICAR SÉRIES ----
basics = pd.read_csv(r"C:\Users\pedro\OneDrive\Documentos\projeto eda\title.basics.tsv.gz", sep="\t", na_values="\\N", low_memory=False)
ratings = pd.read_csv(r"C:\Users\pedro\OneDrive\Documentos\projeto eda\title.ratings.tsv.gz", sep="\t", na_values="\\N", low_memory=False)

# pega só séries / minisséries
basics = basics[basics["titleType"].isin(["tvSeries", "tvMiniSeries"])]

# junta ratings
df = basics.merge(ratings, on="tconst", how="left")

# filtra séries com pelo menos 500 votos
df = df[df["numVotes"].fillna(0).astype(int) >= 500]

# salva reduzido
df[["tconst","primaryTitle","startYear","endYear","genres","averageRating","numVotes"]]\
    .to_csv("title.basics.min.tsv.gz", sep="\t", index=False, compression="gzip")

ratings[ratings["tconst"].isin(df["tconst"])]\
    .to_csv("title.ratings.min.tsv.gz", sep="\t", index=False, compression="gzip")

print("Gerados title.basics.min.tsv.gz e title.ratings.min.tsv.gz")
