# Dofus Window Manager 2.19.0 — bêta 1

Première bêta publique du nouveau Dofus Window Manager pour Windows 10 et 11 64 bits.

## Télécharger et installer

1. Téléchargez `DofusWindowManager.exe` dans les fichiers de cette préversion.
2. Conservez-le dans un dossier permanent.
3. Lancez l'exécutable puis choisissez Dofus Unity ou Dofus Retro.
4. Installez si besoin le plugin avec **Application → Installer le plugin Stream Deck**.

Python, Git et la compilation ne sont pas nécessaires.

## Contenu de cette bêta

- gestion et réorganisation des fenêtres Dofus Unity et Dofus Retro ;
- raccourcis globaux et rotation des personnages ;
- profils, alias, sauvegarde et diagnostic ;
- thème sombre et interface à défilement vertical ;
- plugin Stream Deck 0.4.1 et profil générique 15 touches inclus ;
- installation du plugin directement depuis l'application.

L'exécutable est la variante standard. Il gère les fenêtres Retro, mais n'inclut pas la détection visuelle expérimentale des invitations Retro.

## Vérification et sécurité

SHA-256 de `DofusWindowManager.exe` :

`01f9c139acaebdcca8ca4df85daa8c4e034b24be1859728b39788658b34840f9`

Le binaire n'est pas encore signé numériquement et peut déclencher Windows SmartScreen. Téléchargez-le uniquement depuis ce dépôt officiel et ne désactivez jamais votre antivirus pour une copie provenant d'ailleurs.

Dofus Window Manager ne demande jamais d'identifiant Ankama, de mot de passe, de code 2FA ou de jeton de session.

## Signaler un problème

Utilisez le bouton **Diagnostic… → Copier** puis ouvrez un [rapport de bug](https://github.com/Ducrosr/Dofus-Retro-64-Window-Manager/issues/new?template=bug_report.yml). Retirez les noms de personnages et chemins personnels que vous ne souhaitez pas publier.

Le comportement Retro complet et l'import du profil sur différents modèles de Stream Deck restent parmi les principaux points à tester.
