# Installer Dofus Window Manager

Ce guide installe le code source ou l’exécutable public 2.20.0 depuis le dépôt officiel.

> [!CAUTION]
> Utilisez uniquement <https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay>. Le programme officiel ne demande jamais d’identifiant Ankama, de mot de passe, de code de double authentification ou de jeton de session. N’exécutez pas une copie reçue en message privé et ne désactivez pas votre antivirus pour l’installer.
>
> Consultez aussi la page officielle Ankama : [Reconnaître le phishing et s’en protéger](https://support.ankama.com/hc/fr/articles/201376953-Reconna%C3%AEtre-le-phishing-et-s-en-prot%C3%A9ger).

## Méthode A — exécutable Windows

Cette méthode ne nécessite ni Python, ni Git, ni compilation.

1. Ouvrez la [préversion officielle v2.20.0-beta.2](https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay/releases/tag/v2.20.0-beta.2) puis téléchargez `DofusWindowManager.exe`.
2. Vérifiez si possible son empreinte avec la commande PowerShell suivante :

~~~powershell
Get-FileHash .\DofusWindowManager.exe -Algorithm SHA256
~~~

Comparez la valeur obtenue avec le fichier `DofusWindowManager.exe.sha256` fourni dans la même Release.

3. Déplacez le fichier dans un dossier permanent, par exemple `%LOCALAPPDATA%\Programs\DofusWindowManager\`.
4. Lancez `DofusWindowManager.exe`.

Le binaire n'est pas encore signé numériquement. SmartScreen peut donc demander une confirmation au premier lancement. Cela ne constitue pas une garantie de sécurité : vérifiez toujours l'adresse du dépôt et l'empreinte du fichier.

Cet exécutable est la version standard. La gestion des fenêtres Dofus Retro est incluse, mais pas la détection visuelle expérimentale des invitations Retro. Pour utiliser cette fonction facultative, installez l'application depuis les sources puis suivez la section correspondante de ce guide.

L’exécutable publié correspond à la bêta 2.20.0 et contient l’interface multilingue, les overlays, les thèmes et les visuels présentés dans ce dépôt.

## Installation depuis les sources

### Prérequis

- Windows 10 ou 11 64 bits ;
- Python 3.12 ou ultérieur ;
- Git facultatif ;
- Stream Deck 7.1 ou ultérieur si le plugin doit être utilisé.

Pour vérifier Python dans PowerShell :

~~~powershell
py --version
~~~

### Méthode B — télécharger le ZIP officiel

1. Ouvrez la page officielle du dépôt.
2. Sélectionnez **Code → Download ZIP**.
3. Décompressez entièrement l’archive dans un dossier permanent.
4. Ouvrez PowerShell dans ce dossier.
5. Exécutez les commandes suivantes.

~~~powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
~~~

Remplacez 3.14 par votre version de Python si nécessaire, sans descendre sous Python 3.12.

### Méthode C — cloner avec Git

~~~powershell
git clone https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay.git
cd Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
~~~

## Premier lancement

1. Choisissez **Dofus Unity** ou **Dofus Retro**.
2. Laissez l’option de mémorisation activée si ce choix doit être repris au prochain lancement.
3. Ouvrez vos fenêtres Dofus.
4. Cliquez sur **Rafraîchir**.
5. Vérifiez que chaque personnage apparaît avec son nom et sa classe.

Le mode peut ensuite être changé directement dans la section **Application**, sans redémarrer le gestionnaire.

## Installer le plugin Stream Deck

1. Lancez Dofus Window Manager au moins une fois.
2. Ouvrez **Application → Installer le plugin Stream Deck**.
3. Confirmez l’installation dans Stream Deck.
4. Acceptez le profil **Dofus Window Manager** proposé lors de la première installation.
5. Revenez dans le gestionnaire et ouvrez **Aperçu Stream Deck…** pour comparer la disposition.

Le paquet officiel est également présent dans :

~~~text
streamdeck-plugin\com.remyducros.dofuswindowmanager.streamDeckPlugin
~~~

Le plugin dialogue uniquement avec le gestionnaire sur 127.0.0.1:32145. Il n’a besoin d’aucun identifiant Ankama.

## Fonction visuelle Retro facultative

La détection visuelle des invitations Retro nécessite des dépendances supplémentaires :

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-popup.txt
~~~

Cette fonction est expérimentale. Elle n’apparaît dans les paramètres qu’en mode Retro et lorsque ses dépendances sont disponibles.

## Mettre à jour une installation clonée

Le bouton **Application → Rechercher une mise à jour…** signale les nouvelles Releases sans télécharger de fichier. Le contrôle automatique, effectué au maximum une fois par jour, peut être désactivé dans **Paramètres**. Dans tous les cas, vérifiez la provenance et l’empreinte du nouveau binaire avant de remplacer l’ancien.

Fermez l’application puis exécutez :

~~~powershell
git pull --ff-only
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
~~~

Avant une bêta importante, utilisez **Sauvegarder/restaurer…** pour exporter vos réglages et profils.

## Données locales

Les réglages, profils, sauvegardes et journaux sont conservés dans :

~~~text
%APPDATA%\DofusUnityWindowManager\
~~~

La désinstallation du dossier du programme ne supprime pas automatiquement ces données.

## Dépannage

### Aucune fenêtre Unity détectée

- vérifiez que les clients sont déjà ouverts ;
- sélectionnez Unity dans **Version de Dofus** ;
- cliquez sur **Rafraîchir** ;
- ouvrez **Diagnostic…** et vérifiez les candidats visibles.

### Le focus change dans l’application mais pas vers Dofus

Windows limite les changements de premier plan entre processus. Dofus, Stream Deck et Dofus Window Manager doivent fonctionner au même niveau de privilèges. Évitez le mode administrateur sauf si Dofus est lui-même lancé ainsi.

### Le plugin affiche « DWM fermé »

- lancez d’abord le gestionnaire ;
- vérifiez dans le journal la ligne indiquant que Stream Deck est prêt ;
- assurez-vous qu’aucun autre programme n’utilise le port local 32145 ;
- réinstallez le plugin depuis le bouton intégré si sa version n’est pas 0.4.1.

### Windows SmartScreen ou l’antivirus affiche un avertissement

Ne contournez pas l’avertissement pour une copie provenant d’ailleurs. Revenez au dépôt officiel, comparez la version et analysez le fichier. Les futures versions binaires peuvent être non signées et donc déclencher SmartScreen ; ce comportement ne prouve ni l’innocuité ni la dangerosité d’un fichier.

### Obtenir un rapport utile

Ouvrez **Diagnostic…**, copiez le rapport puis suivez [CONTRIBUTING.md](../CONTRIBUTING.md). Retirez les noms de personnages ou chemins personnels que vous ne souhaitez pas publier.
