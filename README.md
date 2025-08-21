
# 🎬 Sistema de Recomendação de Filmes

Este projeto é um sistema de recomendação de filmes desenvolvido em Python, utilizando **Programação Orientada a Objetos (POO)**, **Pandas** e **Streamlit**.
A proposta é fornecer sugestões de filmes com base em um título ou gênero informado pelo usuário, através de uma interface gráfica ou pelo terminal.

## 📦 Descrição

O sistema carrega dados do The Movie Database (TMDB), armazenados em um arquivo compactado `.zip` contendo o arquivo `movies_metadata.csv`.
Com essas informações (título, gêneros e nota média), o programa cria objetos de filmes e aplica regras de recomendação.

A arquitetura faz uso de:

* **Herança e polimorfismo** (classes `Midia` e `Filme`);
* **Encapsulamento** (atributos privados com `@property`);
* **Interface abstrata** (`Recomendavel`) para padronizar os critérios de recomendação.

## 🚀 Funcionalidades

* Recomendação baseada em um **filme de referência**
* Recomendação baseada em um **gênero cinematográfico**
* Ordenação por similaridade de gêneros e nota média
* **Interface em Streamlit** para interação gráfica
* **Interface em terminal** para execução via linha de comando

## 🧠 Como funciona

1. Os dados são carregados a partir de `movies_metadata.csv` (contido no `.zip`).
2. Cada filme é instanciado como um objeto da classe `Filme`.
3. O **RecomendadorFilmes** recebe a lista de filmes e aplica duas lógicas:

   * **Por gênero:** retorna os melhores avaliados dentro da categoria.
   * **Por filme:** busca outros títulos com gêneros semelhantes, ordenando pela proximidade e nota.
4. O usuário pode interagir via **terminal** ou **Streamlit**.

## 📁 Estrutura do Projeto

```
filmes.py               # Arquivo principal com toda a lógica
archive.zip             # Arquivo com o dataset (movies_metadata.csv)
```

Principais componentes:

* **Midia (classe abstrata):** modelo genérico de mídia.
* **Filme (herda de Midia):** representa um filme com título, gêneros, nota e diretor.
* **RecomendadorFilmes:** aplica as regras de recomendação.
* **modo\_terminal:** interface de linha de comando.
* **modo\_streamlit:** interface gráfica interativa.

## 🛠️ Instruções de Uso

### Requisitos

* Python 3.x
* Bibliotecas: `pandas`, `streamlit`

Instale os pacotes:

```bash
pip install pandas streamlit
```

### Execução

* **Via Terminal:**

```bash
python filmes.py terminal
```

* **Via Streamlit:**

```bash
streamlit run filmes.py
```

⚠️ Certifique-se de ajustar o caminho do arquivo `.zip` em:

```python
zip_path = "C:/Users/pedro/OneDrive/Documentos/projeto eda/archive.zip"
```

## 📝 Exemplo de Funcionamento

* **Por Filme:**
  Entrada: `"Toy Story"`
  Saída: lista de filmes com gêneros semelhantes, priorizando os mais bem avaliados.

* **Por Gênero:**
  Entrada: `"Action"`
  Saída: os filmes de ação mais bem avaliados.

## 📌 Observações

* O sistema depende de um dataset externo (`archive.zip`) com `movies_metadata.csv`.
* O código usa `ast.literal_eval` para converter corretamente os gêneros em listas.
* A arquitetura aplica princípios de **SOLID** em POO para modularidade e extensibilidade.

---

👉 Quer que eu também prepare uma versão **em inglês** do README (pra ficar pronto pro GitHub internacional) ou você prefere deixar só em português?


* O sistema depende de um conjunto de dados externo, que deve estar disponível localmente em formato `.zip`.
* O código faz uso da função `ast.literal_eval` para interpretar corretamente os gêneros no formato de string.

