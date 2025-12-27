# VEAF Community Forum

Application web pour consulter et naviguer dans les archives du forum de la communauté VEAF (Virtual European Air Force).

## Description

Ce projet expose le contenu exporté d'un forum NodeBB sous forme de :
- **Interface web HTML/CSS** pour naviguer dans les catégories et lire les topics
- **API REST** pour accéder aux données programmatiquement

### Fonctionnalités

- Navigation hiérarchique dans les catégories et sous-catégories
- Affichage des topics avec rendu Markdown vers HTML
- Recherche par mots-clés dans les titres des topics
- Pagination des résultats
- API REST complète avec documentation OpenAPI

## Prérequis

- Python 3.12+
- Poetry (gestionnaire de dépendances)

## Installation

```bash
# Cloner le projet
git clone <repository-url>
cd community

# Installer les dépendances
poetry install

# Installer aussi les dépendances de développement (pour les tests)
poetry install --with dev
```

## Configuration

Les données du forum doivent se trouver dans `var/data/` avec la structure suivante :

```
var/data/
├── _export.yml              # Métadonnées de l'export
├── images/                  # Images référencées dans les topics
├── <category-slug>/
│   ├── _category.yml        # Métadonnées de la catégorie
│   ├── <topic-id>-<slug>.md # Topics (Markdown avec frontmatter YAML)
│   └── <subcategory>/       # Sous-catégories (structure récursive)
```

Vous pouvez personnaliser les chemins via les variables d'environnement ou un fichier `.env` :

```env
DATA_PATH=/chemin/vers/var/data
IMAGES_PATH=/chemin/vers/var/data/images
HOST=0.0.0.0
PORT=8000
```

## Lancement

### Mode développement (avec rechargement automatique)

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Mode production

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

L'application sera accessible sur http://localhost:8000

## Utilisation

### Interface Web

| URL | Description |
|-----|-------------|
| `/` | Page d'accueil avec l'arbre des catégories |
| `/category/{id}` | Liste des topics d'une catégorie |
| `/topic/{id}` | Affichage d'un topic |
| `/search?q=...` | Recherche de topics |

### API REST

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Vérification de l'état du serveur |
| `GET /api/info` | Statistiques de l'export |
| `GET /api/categories` | Liste des catégories racines |
| `GET /api/categories/tree` | Arbre complet des catégories |
| `GET /api/categories/{id}` | Détail d'une catégorie |
| `GET /api/categories/{id}/topics` | Topics d'une catégorie (paginé) |
| `GET /api/topics` | Liste de tous les topics (paginé) |
| `GET /api/topics/{id}` | Détail d'un topic avec contenu |
| `GET /api/search?q=...` | Recherche de topics |

La documentation interactive de l'API est disponible sur :
- Swagger UI : http://localhost:8000/docs
- ReDoc : http://localhost:8000/redoc

### Paramètres de pagination

Les endpoints paginés acceptent les paramètres suivants :
- `page` : numéro de page (défaut: 1)
- `page_size` : nombre d'éléments par page (défaut: 20, max: 100)
- `sort_by` : champ de tri (`created`, `last_post`, `view_count`, `rating`)
- `order` : ordre de tri (`asc`, `desc`)

## Tests

```bash
# Exécuter tous les tests
poetry run pytest

# Tests avec affichage détaillé
poetry run pytest -v

# Tests avec couverture de code
poetry run pytest --cov=app --cov-report=term-missing

# Tests par catégorie
poetry run pytest tests/unit/          # Tests unitaires
poetry run pytest tests/integration/   # Tests d'intégration
poetry run pytest tests/e2e/           # Tests end-to-end
```

## Linting et formatage

Le projet utilise **ruff** pour le linting et le formatage, et **mypy** pour la vérification des types.

```bash
# Linting
poetry run ruff check app/ tests/       # Vérifier le code
poetry run ruff check app/ tests/ --fix # Corriger automatiquement

# Formatage
poetry run ruff format app/ tests/      # Formater le code

# Vérification des types
poetry run mypy app/                    # Mode strict
```

## Structure du projet

```
community/
├── app/
│   ├── main.py              # Point d'entrée FastAPI
│   ├── config.py            # Configuration
│   ├── models/              # Modèles Pydantic
│   │   ├── category.py
│   │   ├── topic.py
│   │   └── common.py
│   ├── services/            # Logique métier
│   │   ├── data_loader.py   # Chargement des données
│   │   └── search.py        # Service de recherche
│   ├── routers/             # Routes FastAPI
│   │   ├── api.py           # Endpoints REST
│   │   └── web.py           # Pages HTML
│   ├── templates/           # Templates Jinja2
│   └── static/css/          # Feuilles de style
├── tests/
│   ├── unit/                # Tests unitaires
│   ├── integration/         # Tests d'intégration
│   └── e2e/                 # Tests end-to-end
├── var/data/                # Données du forum
└── pyproject.toml           # Configuration du projet
```

## Technologies utilisées

- **FastAPI** : Framework web moderne et performant
- **Uvicorn** : Serveur ASGI
- **Jinja2** : Moteur de templates HTML
- **Pydantic** : Validation des données
- **python-frontmatter** : Parsing du frontmatter YAML des fichiers Markdown
- **Markdown** : Conversion Markdown vers HTML
- **pytest** : Framework de tests

## Licence

Ce projet est destiné à un usage interne par la communauté VEAF.
