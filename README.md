mon_projet/
│
├── app/                        # Application principale (logique métier & serveur)
│   ├── __init__.py             # Rend le dossier importable en package Python
│   ├── app.py                  # Point d'entrée Flask (ex : création et config de l'app)
│   ├── config.py               # Configuration (variables d'env, clés API, constantes)
│   ├── memory.py               # Gestion mémoire (cache, accès thread-safe)
│   └── routes.py               # (Optionnel) séparation des routes Flask
│
├── utils/                      # Fonctions utilitaires & modules métier
│   ├── __init__.py
│   ├── google_search.py        # Requêtes Google Custom Search API
│   ├── wikipedia_search.py     # Requêtes Wikipédia avec cache/mémoization
│   ├── monchatbot.py           # Logique principale du chatbot (réponses, gestion mémoire)
│   ├── neural_net.py           # Réseau de neurones, embeddings, entraînement
│
├── data/                       # Données persistantes
│   ├── memoire_du_chatbot.json # Base mémoire des questions/réponses
│
├── templates/                 
│   └── index.html              # Page d’accueil / interface chat
│
├── static/                     # Ressources statiques front-end
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│
└── README.md                   # Documentation générale du projet
