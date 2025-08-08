Claro! Aqui está uma versão do `README.md` **sem trechos de código**, com foco apenas em texto descritivo:

---

# 🎬 Sistema de Recomendação de Filmes

Este projeto é um sistema de recomendação de filmes desenvolvido com Python, utilizando bibliotecas como Pandas e Streamlit. A proposta é fornecer sugestões de filmes com base em um título ou gênero informado pelo usuário.

## 📦 Descrição

O sistema utiliza dados do The Movie Database (TMDB), disponibilizados em um arquivo compactado `.zip`, contendo informações como título, gêneros e avaliação média dos filmes. O usuário pode interagir com uma interface gráfica para obter recomendações personalizadas.

## 🚀 Funcionalidades

* Recomendação baseada em um filme de referência
* Recomendação baseada em um gênero cinematográfico
* Ordenação por similaridade de gênero e nota média
* Interface interativa feita com Streamlit

## 🧠 Como funciona

Os dados são lidos a partir de arquivos `.csv` presentes em um arquivo `.zip`. A classe principal, chamada `Recomendador`, realiza o pré-processamento dos dados, convertendo os gêneros em listas legíveis e organizando os filmes conforme a similaridade e popularidade. O Streamlit permite que o usuário selecione o tipo de recomendação e visualize os resultados de forma simples e intuitiva.

## 📁 Estrutura do Projeto

O projeto é composto por um único arquivo Python que concentra tanto a lógica do recomendador quanto a construção da interface. O conjunto de dados necessário deve estar em um arquivo `.zip`, com os arquivos esperados pelo sistema.

## 🛠️ Instruções de Uso

Para utilizar o sistema, é necessário ter o Python instalado e as bibliotecas Pandas e Streamlit. Após isso, basta executar o arquivo principal e interagir com a aplicação por meio da interface exibida no navegador. O usuário escolhe se deseja recomendações baseadas em um filme ou em um gênero e informa o número de sugestões desejadas.

## 📝 Exemplo de Funcionamento

Ao informar um filme, o sistema identifica seus gêneros e busca outros filmes com gêneros semelhantes, priorizando os mais bem avaliados. Se o usuário optar por buscar por gênero, o sistema retorna os filmes mais bem avaliados dentro da categoria escolhida.

## 📌 Observações

* O sistema depende de um conjunto de dados externo, que deve estar disponível localmente em formato `.zip`.
* O código faz uso da função `ast.literal_eval` para interpretar corretamente os gêneros no formato de string.

