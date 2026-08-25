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

### Installateur Windows

L’installateur est construit avec [Inno Setup](https://jrsoftware.org/isinfo.php). Installez Inno Setup 6 depuis sa source officielle, copiez d’abord l’exécutable compilé dans `release-assets`, puis lancez :

~~~powershell
New-Item -ItemType Directory -Force release-assets | Out-Null
Copy-Item dist\DofusWindowManager.exe release-assets\DofusWindowManager.exe
.\installer\build_installer.ps1 -AppVersion "2.20.0"
~~~

Le résultat `release-assets\DofusWindowManager-Setup.exe` installe l’application pour l’utilisateur courant dans `%LOCALAPPDATA%\Programs\DofusWindowManager`, sans demander les droits administrateur. Une icône Bureau reste facultative.

### Signature Authenticode facultative

Le script `installer\sign_windows.ps1` ne signe rien sans certificat. Pour une signature locale ou dans GitHub Actions, fournissez uniquement par variables protégées :

- `WINDOWS_SIGNING_CERTIFICATE_BASE64` : contenu base64 du fichier PFX ;
- `WINDOWS_SIGNING_CERTIFICATE_PASSWORD` : mot de passe du PFX ;
- `WINDOWS_SIGNING_TIMESTAMP_URL` : serveur d’horodatage facultatif.

~~~powershell
.\installer\sign_windows.ps1 -FilePath dist\DofusWindowManager.exe
.\installer\sign_windows.ps1 -FilePath release-assets\DofusWindowManager-Setup.exe
~~~

Le certificat temporaire est créé dans le dossier temporaire du runner puis supprimé dans un bloc `finally`. N’ajoutez jamais un PFX, son mot de passe ou sa version base64 au dépôt. En l’absence de certificat, les builds restent volontairement non signés et les empreintes SHA-256 demeurent obligatoires.

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
npm run build:profiles
npm run build
npm run validate
npm run pack
~~~

- **npm test** exécute les tests Node ;
- **npm run typecheck** contrôle TypeScript ;
- **npm run build:profiles** régénère les profils Standard, Mini, XL, Plus et Neo ;
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

Une publication normale se déclenche lorsque `__release_tag__` dans `dwm/__init__.py` est mis à jour sur `main`. Le workflow compile d’abord le commit exact, puis crée automatiquement le tag et la Release si tous les contrôles réussissent.

Il reste également possible de déclencher la compilation en poussant manuellement un tag dont la version de base correspond à `pyproject.toml` :

~~~powershell
git tag v2.20.0-beta.4
git push origin v2.20.0-beta.4
~~~

Le workflow crée ou complète ensuite la Release avec :

- `DofusWindowManager.exe` ;
- `DofusWindowManager.exe.sha256` ;
- `DofusWindowManager-Setup.exe` ;
- `DofusWindowManager-Setup.exe.sha256` ;
- `DofusWindowManager-StreamDeck.streamDeckPlugin` ;
- l’empreinte SHA-256 du plugin ;
- `SHA256SUMS.txt` pour vérifier les trois fichiers.

Un tag contenant un suffixe comme `-beta.2` est automatiquement publié comme préversion. Le workflow peut aussi être relancé manuellement depuis l’onglet **Actions**, en sélectionnant un tag qui existe déjà. Aucun exécutable ni jeton personnel ne doit être ajouté au dépôt : la publication utilise le `GITHUB_TOKEN` temporaire limité au projet.
