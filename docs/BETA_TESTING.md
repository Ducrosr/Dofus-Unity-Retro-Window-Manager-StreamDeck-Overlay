# Guide de test — bêta source 2.20.0

Merci de participer à la bêta de Dofus Window Manager. Un retour indiquant que tout fonctionne est aussi utile qu'un rapport de bug : il permet d'identifier les configurations réellement couvertes.

## Avant de commencer

1. Clonez ou téléchargez le ZIP uniquement depuis le [dépôt officiel](https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay).
2. Installez les dépendances puis lancez `main.py` comme indiqué dans le [guide d’installation](INSTALLATION.md).
3. Sauvegardez une configuration existante avec **Sauvegarder/restaurer…**.
4. N'utilisez pas de compte ou d'identifiant Ankama dans un rapport de test.

L’exécutable public `v2.20.0-beta.4` contient les nouveautés 2.20.0, mais pas la détection visuelle expérimentale des invitations Retro. Vous pouvez tester l’exécutable standard ou l’installation depuis les sources en indiquant la méthode utilisée dans votre retour.

## Parcours conseillé

Il n'est pas nécessaire de tout tester. Indiquez simplement les parties réellement essayées.

### Installation et premier lancement

- lancer l’application depuis l’environnement Python 3.12 ou ultérieur ;
- choisir Unity ou Retro et mémoriser ce choix ;
- fermer puis relancer l'application ;
- vérifier la présence de tous les boutons avec une mise à l'échelle Windows habituelle.
- tester les drapeaux français, anglais et espagnol, puis vérifier l’avertissement de traduction ;
- vérifier que les douze thèmes sont disponibles en Unity comme en Retro ;

### Fenêtres et rotation

- ouvrir une à huit fenêtres Dofus puis effectuer un scan manuel ;
- contrôler le nom et la classe détectés ;
- activer chaque personnage depuis la liste ;
- tester Suivant, Précédent et les raccourcis globaux ;
- placer Stream Deck au premier plan puis vérifier que Dofus reprend bien le focus ;
- ignorer une fenêtre, vérifier qu'elle sort de la rotation, puis la réintégrer.

### Organisation et persistance

- déplacer les personnages et les colonnes par glisser-déposer ;
- définir puis supprimer un alias, un portrait et une icône ;
- tester une icône officielle de caractéristique puis une icône officielle de métier ;
- enregistrer un profil, modifier l'ordre et recharger le profil ;
- fermer l'application et vérifier que les préférences attendues sont conservées ;
- exporter puis restaurer une sauvegarde.

### Stream Deck

- installer le plugin depuis l'application ;
- accepter le profil générique proposé ;
- contrôler le numéro, le nom, l'alias et la classe sur les touches ;
- déplacer un personnage depuis le Stream Deck ;
- tester Actualiser, Ignorer, Suivant, Précédent et Lancer l'application ;
- si possible, préciser le modèle de Stream Deck utilisé.

### Overlay, notification et attention

- personnaliser séparément le contenu de l’overlay et de la notification ;
- masquer indépendamment portrait et icône dans chacun des deux affichages, puis vérifier leur largeur automatique ;
- déplacer l’overlay par son en-tête, réordonner une ligne par glisser-déposer et par ▲/▼ ;
- redimensionner l’overlay avec la poignée ◢ puis relancer l’application pour vérifier la persistance ;
- saisir temporairement des coordonnées X/Y très éloignées pour l’overlay, puis vérifier qu’il revient automatiquement sur un écran visible et que cette position est conservée ;
- provoquer si possible un clignotement réel d’une fenêtre Dofus dans la barre des tâches ;
- vérifier le repère orange dans l’overlay et sur le Stream Deck, puis sa disparition après focus.
- désactiver le clignotement et vérifier que la couleur orange et le repère `!` restent visibles.

## Transmettre le résultat

- session globalement réussie : utilisez **[Partager un retour de bêta](https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay/issues/new?template=beta_feedback.yml)** ;
- problème précis et reproductible : utilisez **[Signaler un bug](https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay/issues/new?template=bug_report.yml)** ;
- idée d'ergonomie : utilisez **[Proposer une amélioration](https://github.com/Ducrosr/Dofus-Unity-Retro-Window-Manager-StreamDeck-Overlay/issues/new?template=feature_request.yml)** ;
- vulnérabilité ou doute de sécurité : suivez [SECURITY.md](../SECURITY.md) sans publier de détail sensible.

Le rapport de diagnostic peut contenir des noms de personnages et des chemins locaux. Relisez-le avant de le publier.
