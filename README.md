# Dofus Window Manager

[![Version](https://img.shields.io/badge/version-2.19.0-22b8f0)](CHANGELOG.md)
[![Windows](https://img.shields.io/badge/Windows-10%20%7C%2011-0078D4?logo=windows)](docs/INSTALLATION.md)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Tests](https://github.com/Ducrosr/Dofus-Retro-64-Window-Manager/actions/workflows/tests.yml/badge.svg)](https://github.com/Ducrosr/Dofus-Retro-64-Window-Manager/actions/workflows/tests.yml)
[![Licence GPL-3.0](https://img.shields.io/badge/licence-GPL--3.0-green)](LICENSE)

Gestionnaire de fenêtres local pour **Dofus Unity** et **Dofus Retro**, conçu pour rendre le jeu multicompte plus lisible et plus rapide sous Windows. Il détecte les fenêtres Dofus ouvertes, conserve leur ordre et permet de passer de l’une à l’autre avec des raccourcis ou un Stream Deck.

> [!WARNING]
> **Ce dépôt est l’unique source officielle du projet :**
> <https://github.com/Ducrosr/Dofus-Retro-64-Window-Manager>
>
> Ne téléchargez jamais Dofus Window Manager depuis un site, un message privé ou un miroir tiers. Une copie modifiée peut chercher à voler un identifiant Ankama, un mot de passe, un jeton de session ou d’autres données personnelles. **La version officielle ne demande jamais vos identifiants Ankama, votre code de double authentification ni l’accès à votre compte.**

La version 2.19.0 est proposée en **bêta publique**. Les retours de bugs, d’ergonomie et de compatibilité sont les bienvenus dans les [Issues GitHub](https://github.com/Ducrosr/Dofus-Retro-64-Window-Manager/issues).

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
- thème sombre moderne et interface à défilement vertical ;
- détection visuelle facultative des invitations sur Retro.

## Intégration Stream Deck

Le plugin 0.4.1 fourni avec le projet comprend :

- huit touches Personnage avec numéro, nom, classe et alias ;
- choix individuel des lignes de texte et de leur visibilité ;
- couleur de bordure par personnage : Terre, Feu, Eau, Air, Neutre ou Violet ;
- actions Précédent, Suivant, Monter, Descendre, Ignorer/réintégrer et Actualiser ;
- touche Lancer/afficher Dofus Window Manager ;
- profil prêt à l’emploi pour le Stream Deck standard à 15 touches ;
- aperçu interactif de la disposition directement dans l’application.

Les préférences visuelles suivent le personnage lorsqu’il change de position. Une fenêtre ignorée reste associée à sa touche et directement activable ; elle est seulement retirée de la rotation automatique.

## Installation rapide depuis les sources

### Prérequis

- Windows 10 ou 11 en 64 bits ;
- Python 3.12 ou ultérieur ;
- Git facultatif si le dépôt est téléchargé en ZIP ;
- Stream Deck 7.1 ou ultérieur uniquement pour le plugin.

Dans PowerShell :

~~~powershell
git clone https://github.com/Ducrosr/Dofus-Retro-64-Window-Manager.git
cd Dofus-Retro-64-Window-Manager
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
~~~

Python 3.14 peut être remplacé par une autre version installée à partir de Python 3.12.

Pour installer le plugin Stream Deck, lancez d’abord le gestionnaire puis utilisez **Application → Installer le plugin Stream Deck**. Acceptez ensuite le profil proposé par Stream Deck. Aucun téléchargement supplémentaire du plugin n’est nécessaire.

Le guide détaillé couvre l’installation depuis un ZIP, les mises à jour, la fonction Retro facultative et les problèmes les plus courants : **[Guide d’installation](docs/INSTALLATION.md)**.

## Premiers pas

1. Lancez Dofus Window Manager et choisissez Unity ou Retro.
2. Ouvrez les clients Dofus puis cliquez sur **Rafraîchir**.
3. Vérifiez les noms et les classes détectés.
4. Réorganisez les personnages par glisser-déposer.
5. Ajoutez si besoin des alias courts comme Terre, Feu, Mineur ou Alchimiste.
6. Testez les raccourcis F5, F6, F7 et Ctrl+Alt+R.
7. Enregistrez un profil lorsque l’ordre vous convient.
8. Ouvrez **Aperçu Stream Deck…** pour contrôler la disposition avant ou après l’installation du plugin.

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
- le pont utilisé par le plugin Stream Deck écoute uniquement sur 127.0.0.1:32145 ;
- les pages web ne peuvent pas piloter ce pont, car les requêtes portant une origine navigateur sont refusées ;
- les réglages, profils et journaux restent dans %APPDATA%\DofusUnityWindowManager\.

Le gestionnaire et Dofus doivent fonctionner au même niveau de privilèges Windows. Ne lancez pas l’application en administrateur sauf si Dofus l’est également, et ne désactivez jamais votre antivirus sur recommandation d’un distributeur tiers.

Lisez **[SECURITY.md](SECURITY.md)** avant d’installer un binaire ou de transmettre un rapport de bug.

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

Avant de signaler un problème :

1. vérifiez qu’il existe toujours en version 2.19.0 ;
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

Ce projet communautaire n’est ni affilié, ni approuvé, ni sponsorisé par Ankama. Dofus, Dofus Retro et Ankama sont des marques appartenant à leurs propriétaires respectifs.
