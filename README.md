
# 🎬 Recomendador de Filmes & Séries

Um sistema interativo de **recomendações de filmes e séries**, desenvolvido em **Python** com **Streamlit**, aplicando conceitos de **Programação Orientada a Objetos (POO)**, estruturas clássicas de **Ciência da Computação** e integração de dados reais (TMDB/IMDB).

👉 **Acesse o app online:**
🔗 [Recomendador de Filmes & Séries](https://projetoseda-yweiv9g9k5bdkb69dq8daj.streamlit.app)

---

## 🚀 Funcionalidades

* **Escolha entre Filmes ou Séries** na interface.
* **Dois modos de recomendação clássica:**

  * Por **gênero** (lista títulos ordenados pela nota média).
  * Por **título** (identifica gêneros do título escolhido e calcula similaridade com outros).
* **Cross-Recs (recomendações cruzadas):** sugere séries parecidas a partir de filmes e vice-versa.
* **Algoritmos adicionais:**

  * **Grafo de gêneros** (gêneros como nós e conexões quando aparecem juntos).
  * **Busca em Largura (BFS)** (explora gêneros relacionados em camadas).
  * **Recursão** (expansão de recomendações em múltiplos níveis).

---

## 🧩 Arquitetura

* **POO:**

  * `Midia` (abstrata)
  * `Filme` e `Serie` (subclasses)
  * `Recomendavel` (interface)
  * `RecomendadorMidias` (implementa a lógica de recomendação)

* **Estruturas de Dados:**

  * **Tabelas Hash:** mapeamento rápido de gêneros e conexões.
  * **Grafo de Coocorrência:** representa relações entre gêneros.

* **Princípios SOLID aplicados:**

  * **Responsabilidade Única:** cada classe tem uma função clara.
  * **Aberto/Fechado:** sistema expansível sem alterar código já existente.
  * **Substituição de Liskov:** `Filme` e `Serie` substituem `Midia` sem problemas.
  * **Segregação de Interfaces:** interface `Recomendavel` é simples e focada.
  * **Inversão de Dependência:** lógica trabalha contra abstrações, não contra implementações específicas.

---

## 📊 Tecnologias Utilizadas

* **Python 3.10+**
* **Pandas** → tratamento de dados.
* **Streamlit** → interface web interativa.
* **AST & Zipfile** → leitura de arquivos.
* **IMDB/TMDB datasets** → base real de filmes e séries.

---

## 📈 Extensões Futuras

* Pesos no grafo de gêneros (frequência de coocorrência).
* Integração de embeddings de descrição ou elenco para recomendações mais sofisticadas.
* Suporte a outros tipos de mídia (músicas, livros).

---

## 👨‍💻 Autores

**Desenvolvido por [Pedro](https://github.com/pedroveloso-gif) e [João Filipe](https://github.com/Jotafdc)**
 como projeto acadêmico e prático de recomendação de mídias, unindo **programação orientada a objetos** com **estrutura de dados**
