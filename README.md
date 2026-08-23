# Dofus Window Manager

**Français** · [English](README.en.md) · [Español](README.es.md)

> [!NOTE]
> Les versions anglaise et espagnole ont été traduites avec l’aide d’une IA et peuvent contenir des erreurs. Les corrections sont bienvenues dans les Issues ou Pull Requests du dépôt officiel.

[![Version](https://img.shields.io/badge/version-2.20.0--beta-22b8f0)](CHANGELOG.md)
[![Windows](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D4?logo=windows)](docs/INSTALLATION.md)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Tests](https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay/actions/workflows/tests.yml/badge.svg)](https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay/actions/workflows/tests.yml)
[![Licence GPL-3.0](https://img.shields.io/badge/licence-GPL--3.0-green)](LICENSE)

Gestionnaire de fenêtres local pour **Dofus Unity** et **Dofus Retro**, conçu pour rendre le jeu multicompte plus lisible et plus rapide sous Windows. Il détecte les fenêtres Dofus ouvertes, conserve leur ordre et permet de passer de l’une à l’autre avec des raccourcis ou un Stream Deck.

> [!WARNING]
> **Ce dépôt est l’unique source officielle du projet :**
> <https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay>
>
> Ne téléchargez jamais Dofus Window Manager depuis un site, un message privé ou un miroir tiers. Une copie modifiée peut chercher à voler un identifiant Ankama, un mot de passe, un jeton de session ou d’autres données personnelles. **La version officielle ne demande jamais vos identifiants Ankama, votre code de double authentification ni l’accès à votre compte.**
>
> Consultez également les recommandations officielles d’Ankama : **[Reconnaître le phishing et s’en protéger](https://support.ankama.com/hc/fr/articles/201376953-Reconna%C3%AEtre-le-phishing-et-s-en-prot%C3%A9ger)**.

Le code source 2.20.0 est proposé en **bêta publique**. Il réunit l’interface multilingue, les overlays, les demandes d’attention, les portraits, les icônes officielles et les thèmes Unity/Retro. Les retours de bugs, d’ergonomie et de compatibilité sont les bienvenus dans les [Issues GitHub](https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay/issues).

## Ce que fait l’application

- détection native des fenêtres Dofus Unity et Dofus Retro ;
- passage au personnage suivant ou précédent avec des raccourcis globaux ;
- ordre personnalisable par boutons ou glisser-déposer ;
- alias par personnage, utiles pour indiquer un élément ou un métier ;
- exclusion temporaire d’une fenêtre de la rotation sans supprimer son association Stream Deck ;
- profils de personnages enregistrés en JSON ;
- tableau réorganisable : classe, nom, alias et identifiant de fenêtre ;
- bascule Unity/Retro sans redémarrer l’application ;
- actualisation automatique par événements Windows et scan manuel ;
- fonctionnement dans la zone de notification et démarrage Windows facultatif ;
- sauvegarde/restauration des réglages, profils, alias et ordre courant ;
- rapport de diagnostic copiable pour les bêta-testeurs ;
- vérification facultative des nouvelles Releases officielles, sans téléchargement automatique ;
- douze thèmes disponibles dans les deux modes : Standard, Bonta, Brakmar, Tribute, Gold and Steel, Belladone, Unicorn, Emerald Mine, Sufokia, Pandala, Wabbit et Retro ;
- interface en français par défaut, anglais ou espagnol, sélectionnable en un clic avec les trois drapeaux ;
- réinitialisation séparée de l’affichage, sans supprimer les profils ni les personnalisations des personnages ;
- mode compact toujours visible avec uniquement la rotation active et un bouton de retour explicite ;
- notification de changement de personnage et overlay de rotation transparent, configurables, désactivables et ajustés automatiquement à la largeur de leur contenu ;
- contenu de l’overlay et de la notification personnalisable : numéro, nom, classe et alias peuvent être déplacés ou masqués ;
- portraits et icônes affichables ou masquables indépendamment dans la notification, l’overlay et le Stream Deck ;
- signalement orange avec `!` et léger clignotement facultatif des fenêtres demandant l’attention ;
- file d’attente chronologique `!1`, `!2`… et action **Prochaine alerte** dans l’application, l’overlay, le raccourci F8 et le Stream Deck ;
- portrait local, 38 portraits de classes, 39 icônes officielles de caractéristiques et 20 icônes officielles de métiers personnalisables par personnage ;
- ordre modifiable depuis l’overlay par flèches ou glisser-déposer, avec taille ajustable directement à la souris ;
- thème sombre moderne et interface à défilement vertical ;
- détection visuelle facultative des invitations sur Retro.

## Intégration Stream Deck

Le plugin 0.7.0 fourni avec le projet comprend :

- huit touches Personnage avec numéro, nom, classe et alias ;
- choix individuel des lignes de texte et de leur visibilité ;
- couleur de bordure par personnage : Terre, Feu, Eau, Air, Neutre ou Violet ;
- bordure orange, repère `!` et léger clignotement facultatif lorsqu’une fenêtre demande l’attention ;
- ordre des alertes visible sur chaque touche et action **Prochaine alerte** affichant le nombre de demandes en attente ;
- portrait et icône du personnage en arrière-plan, selon les préférences définies dans l’application ;
- actions Précédent, Suivant, Prochaine alerte, Monter, Descendre, Ignorer/réintégrer et Actualiser ;
- touche Lancer/afficher Dofus Window Manager ;
- profil prêt à l’emploi pour le Stream Deck standard à 15 touches ;
- aperçu interactif de la disposition directement dans l’application.
- reprise automatique du thème et de la langue de l’application sur les touches dynamiques.

Les préférences visuelles suivent le personnage lorsqu’il change de position. Une fenêtre ignorée reste associée à sa touche et directement activable ; elle est seulement retirée de la rotation automatique.

## Installation rapide

### Exécutable Windows — méthode recommandée

Pour utiliser l'application sans installer Python ni compiler le projet :

1. ouvrez la **[préversion officielle v2.20.0-beta.1](https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay/releases/tag/v2.20.0-beta.1)** puis téléchargez `DofusWindowManager.exe` ;
2. vérifiez si possible son empreinte SHA-256 à l'aide du fichier [`DofusWindowManager.exe.sha256`](https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay/releases/download/v2.20.0-beta.1/DofusWindowManager.exe.sha256) ;
3. placez l'exécutable dans un dossier permanent puis lancez-le.

> [!IMPORTANT]
> L’exécutable `v2.20.0-beta.1` contient les nouveautés de la bêta 2.20. Il s’agit de la variante standard, sans détection visuelle expérimentale des invitations Retro.

Cette bêta n'est pas encore signée numériquement. Windows SmartScreen peut donc afficher un avertissement, même pour le fichier officiel. Ne contournez jamais cet avertissement pour une copie obtenue ailleurs que sur ce dépôt.

L'exécutable fourni est la version standard : il gère Dofus Unity et Dofus Retro, mais n'inclut pas la détection visuelle expérimentale des invitations Retro. Cette fonction facultative nécessite une installation depuis les sources avec les dépendances décrites dans le guide.

### Installation depuis les sources

### Prérequis

- Windows 10 ou 11 en 64 bits ;
- Python 3.12 ou ultérieur ;
- Git facultatif si le dépôt est téléchargé en ZIP ;
- Stream Deck 7.1 ou ultérieur uniquement pour le plugin.

Dans PowerShell :

~~~powershell
git clone https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay.git
cd Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
~~~

Python 3.14 peut être remplacé par une autre version installée à partir de Python 3.12.

Pour installer le plugin Stream Deck, lancez d’abord le gestionnaire puis utilisez **Application → Installer le plugin Stream Deck**. Acceptez ensuite le profil proposé par Stream Deck. Aucun téléchargement supplémentaire du plugin n’est nécessaire.

Le guide détaillé couvre l'exécutable, l’installation depuis un ZIP, les mises à jour, la fonction Retro facultative et les problèmes les plus courants : **[Guide d’installation](docs/INSTALLATION.md)**.

## Premiers pas

1. Lancez Dofus Window Manager et choisissez Unity ou Retro.
2. Ouvrez les clients Dofus puis cliquez sur **Rafraîchir**.
3. Vérifiez les noms et les classes détectés.
4. Réorganisez les personnages par glisser-déposer.
5. Dans **Personnaliser…**, ajoutez si besoin un alias, un portrait personnel ou de classe et une icône.
6. Testez les raccourcis F5, F6, F7, F8 et Ctrl+Alt+R.
7. Enregistrez un profil lorsque l’ordre vous convient.
8. Ouvrez **Aperçu Stream Deck…** pour contrôler la disposition avant ou après l’installation du plugin.
9. Essayez **Mode compact** ou **Afficher l’overlay**, puis ajustez leur comportement dans **Paramètres → Affichage en jeu**.

Consultez le **[guide complet d’utilisation](docs/UTILISATION.md)** pour les profils, les fenêtres ignorées, les sauvegardes, la zone de notification, les diagnostics et le Stream Deck.

## Raccourcis par défaut

| Action | Raccourci |
|---|---|
| Personnage suivant | F5 |
| Personnage précédent | F6 |
| Ignorer/réintégrer la fenêtre | F7 |
| Actualiser les fenêtres | Ctrl+Alt+R |

Les raccourcis sont personnalisables dans les paramètres.

## Sécurité et confidentialité

Dofus Window Manager est un outil de gestion de fenêtres :

- il ne lit ni la mémoire ni les paquets réseau de Dofus ;
- il ne saisit aucune commande dans le jeu ;
- il ne demande et ne stocke aucun identifiant Ankama ;
- les notifications et overlays sont des fenêtres locales distinctes : aucun code n’est injecté dans Dofus ;
- les portraits choisis sont redimensionnés et enregistrés uniquement dans les réglages locaux ;
- le pont utilisé par le plugin Stream Deck écoute uniquement sur 127.0.0.1:32145 ;
- les pages web ne peuvent pas piloter ce pont, car les requêtes portant une origine navigateur sont refusées ;
- le contrôle de mise à jour contacte uniquement l’API publique du dépôt GitHub officiel, au maximum une fois par jour par défaut ;
- aucune mise à jour n’est téléchargée ou installée automatiquement et ce contrôle peut être désactivé dans les paramètres ;
- les réglages, profils et journaux restent dans %APPDATA%\DofusUnityWindowManager\.

Le gestionnaire et Dofus doivent fonctionner au même niveau de privilèges Windows. Ne lancez pas l’application en administrateur sauf si Dofus l’est également, et ne désactivez jamais votre antivirus sur recommandation d’un distributeur tiers.

Lisez **[SECURITY.md](SECURITY.md)** et la page Ankama **[Reconnaître le phishing et s’en protéger](https://support.ankama.com/hc/fr/articles/201376953-Reconna%C3%AEtre-le-phishing-et-s-en-prot%C3%A9ger)** avant d’installer un binaire reçu en dehors du dépôt officiel.

## Compilation et développement

Le dépôt contient le code Python, les tests, le projet PyInstaller et les sources TypeScript du plugin Stream Deck.

~~~powershell
# Tests Python
py -3.14 -m unittest discover -s tests -v

# Contrôle statique
py -3.14 -m pip install -r requirements-dev.txt
py -3.14 -m ruff check .

# Exécutable Windows léger
py -3.14 build_exe.py
~~~

Le résultat PyInstaller est créé dans **dist\DofusWindowManager.exe**. La compilation avec la détection visuelle Retro et celle du plugin sont détaillées dans le **[guide de compilation](docs/COMPILATION.md)**.

## Participer à la bêta

Pour la bêta 2.20.0, utilisez l’**[exécutable officiel v2.20.0-beta.1](https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay/releases/tag/v2.20.0-beta.1)** ou installez les sources, puis suivez le **[guide de test bêta](docs/BETA_TESTING.md)**. Vous pouvez transmettre un **[retour de session](https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay/issues/new?template=beta_feedback.yml)** même si tout a fonctionné.

Avant de signaler un problème :

1. vérifiez qu’il existe toujours avec le code source 2.20.0 le plus récent ;
2. utilisez **Diagnostic… → Copier** dans l’application ;
3. retirez de votre rapport toute information personnelle ou sensible ;
4. recherchez un ticket similaire ;
5. ouvrez un rapport de bug avec les étapes permettant de reproduire le problème.

Les journaux peuvent contenir les noms de vos personnages et les titres de fenêtres. Ne publiez jamais d’identifiant, mot de passe, jeton de session, adresse électronique ou code d’authentification.

Voir **[CONTRIBUTING.md](CONTRIBUTING.md)** pour tester, proposer une amélioration ou contribuer au code.

## Limites et statut du projet

- Windows uniquement ;
- profil fourni pour le Stream Deck standard à 15 touches ;
- la détection des invitations Retro est expérimentale et facultative ;
- Windows peut refuser ponctuellement le premier plan selon les privilèges et l’application actuellement active ; plusieurs mécanismes de secours sont inclus ;
- cette bêta peut encore contenir des défauts : sauvegardez vos profils avant une mise à jour importante.

## Licence et marques

Le code est distribué sous licence **GNU GPL v3**, voir [LICENSE](LICENSE).

Ce projet communautaire n’est ni affilié, ni approuvé, ni sponsorisé par Ankama. Dofus, Dofus Retro, Ankama, ainsi que les portraits et icônes de jeu fournis dans `assets/ankama`, sont la propriété de leurs titulaires respectifs. Ces ressources graphiques ne sont pas couvertes par la GPL-3.0 du code ; consultez leur [notice dédiée](assets/ankama/NOTICE.md) avant toute redistribution.
