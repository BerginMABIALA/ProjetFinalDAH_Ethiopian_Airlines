import os
import json
import pandas as pd
import streamlit as st
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import streamlit.components.v1 as components

# Code pour Google Analytics
ga_html = """

<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-7E2J9BHSCS"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-7E2J9BHSCS');
</script>
"""
components.html(ga_html, height=0, width=0)

# Nom du fichier JSON d'entrée avec les articles
input_file_sentiments = 'nyt_articles2019_dates_reformatted.json'

# Vérifier si le fichier existe
if not os.path.isfile(input_file_sentiments):
    st.error(f"Le fichier '{input_file_sentiments}' est introuvable. Vérifiez le chemin du fichier.")
else:
    # Fonction pour extraire la date au format YYYY-MM-DD
    def format_date(date_str):
        try:
            # Convertir la chaîne de caractères en objet datetime
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            # Retourner uniquement la partie date au format YYYY-MM-DD
            return dt.date().isoformat()
        except ValueError:
            # Retourner None si le format de la date est incorrect
            return None

    # Charger le contenu du fichier JSON d'entrée
    with open(input_file_sentiments, 'r', encoding='utf-8') as file:
        articles_with_sentiments = json.load(file)

    # Dictionnaire pour stocker les scores de sentiment par date
    sentiments_by_date = defaultdict(list)

    # Réorganiser les dates et stocker les scores de sentiment
    for article in articles_with_sentiments:
        pub_date = article.get("pub_date", "")
        formatted_date = format_date(pub_date)
        sentiment_score = article.get("sentiment_score", 0)
        
        if formatted_date:  # Assurer que la date est valide
            sentiments_by_date[formatted_date].append(sentiment_score)

    # Calculer la moyenne des scores de sentiment par date
    average_sentiments_by_date = {date: sum(scores)/len(scores) for date, scores in sentiments_by_date.items()}

    # Convertir les données en DataFrame
    df = pd.DataFrame(list(average_sentiments_by_date.items()), columns=['Date', 'Average_Sentiment'])

    # Convertir la colonne 'Date' en type datetime
    df['Date'] = pd.to_datetime(df['Date'])

    # Trier le DataFrame par date
    df = df.sort_values('Date')

    # Extraction des scores de sentiment pour l'histogramme
    all_sentiment_scores = [score for scores in sentiments_by_date.values() for score in scores]

    # Page d'Accueil : Présentation Générale
    st.title("Analyse des Sentiments pour Ethiopian Airlines")
    st.write("Bienvenue dans cette application qui analyse les sentiments exprimés dans les articles "
             "de presse relatifs à Ethiopian Airlines. L'application se concentre sur l'extraction des "
             "sentiments à partir des articles et leur visualisation pour observer les tendances au fil du temps.")

    # Sélection des dates
    st.sidebar.header("Filtres de Date")
    start_date = st.sidebar.date_input("Date de Début", min(df['Date']), min(df['Date']), max(df['Date']))
    end_date = st.sidebar.date_input("Date de Fin", min(df['Date']), min(df['Date']), max(df['Date']))

    # Sélection des plages de scores de sentiment
    st.sidebar.header("Filtres de Scores de Sentiment")
    min_score, max_score = st.sidebar.slider(
        "Plage des Scores de Sentiment",
        min_value=float(min(all_sentiment_scores)),
        max_value=float(max(all_sentiment_scores)),
        value=(float(min(all_sentiment_scores)), float(max(all_sentiment_scores))),
        step=0.01
    )

    # Filtrer les données en fonction des dates et des scores de sentiment sélectionnés
    filtered_df = df[(df['Date'] >= pd.Timestamp(start_date)) & (df['Date'] <= pd.Timestamp(end_date))]
    filtered_sentiment_scores = [score for date, scores in sentiments_by_date.items()
                                 if pd.to_datetime(date) >= pd.Timestamp(start_date) and pd.to_datetime(date) <= pd.Timestamp(end_date)
                                 for score in scores if min_score <= score <= max_score]

    # Section 1 : Graphique de l'Évolution des Sentiments
    st.subheader("Répartition des Scores de Sentiment par Date")
    st.write("Ce graphique montre comment les scores de sentiment ont évolué au fil du temps, avec une ligne reliant "
             "les scores moyens de sentiment pour chaque date.")

    if not filtered_df.empty:
        st.line_chart(filtered_df.set_index('Date'))
    else:
        st.write("Aucune donnée disponible pour la période sélectionnée.")

    # Section 2 : Distribution des Scores de Sentiment
    st.subheader("Distribution des Scores de Sentiment")
    st.write("Cet histogramme montre la répartition des scores de sentiment parmi les articles. Il permet de visualiser "
             "si les sentiments exprimés sont majoritairement positifs, négatifs, ou neutres.")

    if filtered_sentiment_scores:
        plt.figure(figsize=(10, 6))
        plt.hist(filtered_sentiment_scores, bins=20, edgecolor='black', alpha=0.7)
        plt.title('Histogramme des Scores de Sentiment')
        plt.xlabel('Scores de Sentiment')
        plt.ylabel('Nombre d\'Articles')
        plt.grid(True)
        st.pyplot(plt)
    else:
        st.write("Aucun score de sentiment disponible pour la plage sélectionnée.")

    # Section 3 : Répartition des Scores de Sentiment (Négatif, Neutre, Positif)
    st.subheader("Répartition des Scores de Sentiment : Négatif, Neutre, Positif")
    st.write("Cet histogramme montre la répartition des scores de sentiment en trois catégories : Négatif, Neutre, et Positif.")

    def categorize_sentiment(score):
        if score < 0:
            return 'Négatif'
        elif score == 0:
            return 'Neutre'
        else:
            return 'Positif'

    # Catégoriser les scores de sentiment
    categorized_scores = [categorize_sentiment(score) for score in filtered_sentiment_scores]

    # Créer un DataFrame pour la répartition des catégories
    categorized_df = pd.DataFrame(categorized_scores, columns=['Sentiment_Category'])
    category_counts = categorized_df['Sentiment_Category'].value_counts()

    # Créer un histogramme avec matplotlib pour la répartition des catégories
    plt.figure(figsize=(10, 6))
    plt.bar(category_counts.index, category_counts.values, color=['red', 'gray', 'green'])
    plt.title('Répartition des Scores de Sentiment')
    plt.xlabel('Catégorie de Sentiment')
    plt.ylabel('Nombre d\'Articles')
    plt.grid(axis='y')
    st.pyplot(plt)

    # Section 4 : Diagramme Circulaire de Répartition des Scores de Sentiment
    st.subheader("Diagramme Circulaire de Répartition des Scores de Sentiment")
    st.write("Ce diagramme circulaire montre la répartition proportionnelle des scores de sentiment en trois catégories : "
             "Négatif, Neutre, et Positif.")

    # Créer un diagramme circulaire avec matplotlib pour la répartition des catégories
    plt.figure(figsize=(8, 8))
    plt.pie(category_counts, labels=category_counts.index, autopct='%1.1f%%', colors=['red', 'gray', 'green'])
    plt.title('Répartition Proportionnelle des Scores de Sentiment')
    st.pyplot(plt)

    # Section 5 : Statistiques Descriptives
    st.subheader("Statistiques Descriptives des Scores de Sentiment")
    st.write("Voici les statistiques descriptives pour les scores de sentiment filtrés.")

    if filtered_sentiment_scores:
        # Calcul des statistiques descriptives
        sentiment_series = pd.Series(filtered_sentiment_scores)
        mean_score = sentiment_series.mean()
        median_score = sentiment_series.median()
        std_dev = sentiment_series.std()
        min_score = sentiment_series.min()
        max_score = sentiment_series.max()

        # Affichage des statistiquesst.write(f"**Moyenne des Scores de Sentiment :** {mean_score:.2f}")
        st.write(f"**Moyenne des Scores de Sentiment :** {mean_score:.2f}")
        st.write(f"**Médiane des Scores de Sentiment :** {median_score:.2f}")
        st.write(f"**Écart Type des Scores de Sentiment :** {std_dev:.2f}")
        st.write(f"**Score Minimum :** {min_score:.2f}")
        st.write(f"**
