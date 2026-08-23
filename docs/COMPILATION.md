# Compiler le projet

Les builds Windows doivent être produits sous Windows. Ce dépôt contient deux composants indépendants : l’application Python et le plugin Stream Deck TypeScript.

## Application Python

### Prérequis

- Windows 10 ou 11 64 bits ;
- Python 3.12 ou ultérieur ;
- PowerShell ;
- environ 1 Go libre pour l’environnement de compilation.

### Vérifications avant compilation

~~~powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m ruff check .
~~~

### Build léger recommandé

~~~powershell
py -3.14 build_exe.py
~~~

Le script crée un environnement isolé **.venv-build-core**, installe les versions définies dans les fichiers requirements puis lance PyInstaller avec **main.spec**.

Résultat :

~~~text
dist\DofusWindowManager.exe
~~~

### Build avec détection visuelle Retro

~~~powershell
py -3.14 build_exe.py --with-popup
~~~

Cette variante utilise **.venv-build-popup** et ajoute NumPy, OpenCV et Windows Graphics Capture. Elle est plus volumineuse et ne doit être diffusée que si la fonction expérimentale Retro est nécessaire.

### Nettoyer un build

Les dossiers **build**, **dist**, **.venv-build-core** et **.venv-build-popup** sont des sorties locales ignorées par Git. Supprimez uniquement la variante à reconstruire lorsque PyInstaller conserve un cache incohérent.

## Plugin Stream Deck

### Prérequis

- Node.js 24 ou ultérieur ;
- npm ;
- Stream Deck 7.1 ou ultérieur ;
- le CLI Elgato, installé localement par npm ci ou globalement si souhaité.

~~~powershell
cd streamdeck-plugin
npm ci
npm test
npm run typecheck
npm run build
npm run validate
npm run pack
~~~

- **npm test** exécute les tests Node ;
- **npm run typecheck** contrôle TypeScript ;
- **npm run build** génère le bundle du plugin ;
- **npm run validate** utilise le CLI Elgato ;
- **npm run pack** produit le paquet .streamDeckPlugin.

Pour le développement local avec rechargement :

~~~powershell
npm run watch
streamdeck link com.remyducros.dofuswindowmanager.sdPlugin
~~~

## Contenu inclus par PyInstaller

Le fichier **main.spec** inclut :

- l’icône de l’application ;
- le paquet Stream Deck prêt à installer ;
- les modules nécessaires à l’interface et à la gestion Windows ;
- les dépendances visuelles uniquement lorsqu’elles sont installées dans l’environnement de build correspondant.

Testez toujours sur un compte Windows distinct ou une machine virtuelle avant de proposer un binaire à des bêta-testeurs.

## Diffusion sûre

- publiez les binaires uniquement dans les Releases du dépôt officiel ;
- indiquez la version de l’application et celle du plugin ;
- publiez un SHA-256 pour chaque binaire ;
- ne republiez jamais un exécutable reçu d’un tiers ;
- signalez clairement toute compilation personnelle ou tout fork comme non officiel ;
- n’incluez jamais le contenu de %APPDATA%\DofusUnityWindowManager\ dans une archive de diffusion.

## Publication automatisée

Le workflow GitHub Actions **Compiler et publier une version** reproduit ces contrôles sur un environnement Windows propre. Il exécute les tests Python et Stream Deck, Ruff, le contrôle TypeScript, la validation Elgato, la compilation du plugin et le build PyInstaller standard.

Une publication normale se déclenche en poussant un tag dont la version de base correspond à `pyproject.toml` :

~~~powershell
git tag v2.20.0-beta.2
git push origin v2.20.0-beta.2
~~~

Le workflow crée ou complète ensuite la Release avec :

- `DofusWindowManager.exe` ;
- `DofusWindowManager.exe.sha256` ;
- `DofusWindowManager-StreamDeck.streamDeckPlugin` ;
- l’empreinte SHA-256 du plugin ;
- `SHA256SUMS.txt` pour vérifier les deux fichiers.

Un tag contenant un suffixe comme `-beta.2` est automatiquement publié comme préversion. Le workflow peut aussi être relancé manuellement depuis l’onglet **Actions**, en sélectionnant un tag qui existe déjà. Aucun exécutable ni jeton personnel ne doit être ajouté au dépôt : la publication utilise le `GITHUB_TOKEN` temporaire limité au projet.
