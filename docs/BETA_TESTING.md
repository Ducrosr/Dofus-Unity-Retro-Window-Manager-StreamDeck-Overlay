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


## Lot en développement : profils, raccourcis et reconnexion

Les tests automatisés couvrent les transitions de contexte via des API Windows simulées et les parcours de détection, reconnexion, annulation et publication vers les affichages. Les essais Windows réels suivants restent nécessaires avant une release :

1. Charger automatiquement une équipe déjà ouverte dans un ordre différent : vérifier immédiatement tableau, overlay, alias et Stream Deck, sans autre scan.
2. Choisir le mode contextuel et un chiffre seul : passer de Dofus au Bloc-notes et vérifier la saisie normale, puis revenir au jeu. Tester la pause depuis l’application et la zone de notification, ainsi que la capture dans les paramètres.
3. En mode fixe, fermer le personnage 2, utiliser le 3, puis reconnecter le 2 : les cases doivent rester stables et le 2 retrouver sa cible. Répéter avec un personnage ignoré, puis avec le hook désactivé pour utiliser les scans.
4. Déplacer un personnage depuis l’application, l’overlay et le Stream Deck ; vérifier l’ordre après rafraîchissement, puis annuler avant et après reconnexion. Changer de profil et confirmer la remise à zéro de l’historique.
5. Exporter/restaurer une configuration avec un membre absent, des cases réattribuées et un personnage ignoré ; vérifier leur conservation. Tester également un profil JSON v2.
6. Vérifier les nouveaux contrôles en FR/EN/ES, à 100 % et 150 %, et tester la reprise après veille.

### Dispositions d’overlay par profil

- Enregistrer deux équipes avec des orientations et positions différentes ; les charger manuellement puis via la reconnaissance automatique.
- Vérifier le titre, les flèches, la taille automatique et les portraits après chaque chargement.
- Charger un ancien profil : conserver l’affichage courant. Décocher la mémorisation et enregistrer : obtenir le même comportement.
- Vérifier que charger une disposition Unity ne modifie pas la disposition Retro enregistrée ; tester également une position provenant d’un écran débranché.

### Menu de la zone de notification

- Réduire l’application ; charger successivement deux profils, dont un pour l’autre mode, et vérifier l’overlay et le Stream Deck.
- Contrôler les coches du profil, du mode et de l’overlay après une action dans l’application, puis via le menu. Vérifier également la pause/reprise et les trois langues.
- Ouvrir les paramètres : les changements par le menu doivent être grisés. Fermer les paramètres et vérifier leur réactivation.
- Supprimer un profil externe puis utiliser Actualiser les fenêtres : vérifier son retrait du menu. Quitter depuis le menu et vérifier la disparition de l’icône.

### Aperçu des importations et restaurations

- Importer un profil existant avec un ordre ou des alias différents : vérifier les valeurs avant/après, annuler, puis vérifier que le profil et les paramètres sont inchangés.
- Importer une sauvegarde modifiant le mode, l’overlay et les raccourcis : vérifier le tableau, appliquer puis vérifier le point de restauration créé.
- Restaurer depuis le gestionnaire déjà ouvert ; annuler avec Échap et vérifier que le gestionnaire reste utilisable.
- Tester les textes longs, les portraits incorporés, les trois langues, les thèmes et le redimensionnement de la fenêtre d’aperçu.

### Recherche des paramètres

- Rechercher `opacite overlay`, `fenetre` et une option de Général ; vérifier l’ouverture du bon onglet et le défilement.
- Modifier une option sans appliquer, rechercher une autre option, puis effacer : vérifier que la modification initiale est conservée.
- Tester Ctrl+F, Entrée, Échap, un terme absent, les trois langues et la fermeture immédiate après saisie.

### Écrans et ancrage

- Choisir chaque écran, notamment un écran à gauche ou au-dessus, puis tester les six ancrages avec les deux orientations de l’overlay.
- Vérifier que la barre des tâches reste dégagée ; modifier la taille de l’overlay et contrôler que le bord choisi reste respecté.
- Débrancher puis rebrancher l’écran choisi : contrôler le repli sur le principal puis le retour après environ deux secondes.
- Tester différentes mises à l’échelle Windows, la position libre, le réordonnancement des personnages avec ancrage et la restauration d’un profil sur un autre écran.
