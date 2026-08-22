# Guide de test — bêta 2.19.0

Merci de participer à la bêta de Dofus Window Manager. Un retour indiquant que tout fonctionne est aussi utile qu'un rapport de bug : il permet d'identifier les configurations réellement couvertes.

## Avant de commencer

1. Téléchargez uniquement la [préversion officielle v2.19.0-beta.1](https://github.com/Ducrosr/Dofus-Retro-64-Window-Manager/releases/tag/v2.19.0-beta.1).
2. Vérifiez le SHA-256 si possible.
3. Sauvegardez une configuration existante avec **Sauvegarder/restaurer…**.
4. N'utilisez pas de compte ou d'identifiant Ankama dans un rapport de test.

L'exécutable standard ne contient pas la détection visuelle expérimentale des invitations Retro. Ne signalez donc pas son absence comme un défaut de cette variante.

## Parcours conseillé

Il n'est pas nécessaire de tout tester. Indiquez simplement les parties réellement essayées.

### Installation et premier lancement

- lancer l'exécutable sans Python installé ;
- choisir Unity ou Retro et mémoriser ce choix ;
- fermer puis relancer l'application ;
- vérifier la présence de tous les boutons avec une mise à l'échelle Windows habituelle.

### Fenêtres et rotation

- ouvrir une à huit fenêtres Dofus puis effectuer un scan manuel ;
- contrôler le nom et la classe détectés ;
- activer chaque personnage depuis la liste ;
- tester Suivant, Précédent et les raccourcis globaux ;
- placer Stream Deck au premier plan puis vérifier que Dofus reprend bien le focus ;
- ignorer une fenêtre, vérifier qu'elle sort de la rotation, puis la réintégrer.

### Organisation et persistance

- déplacer les personnages et les colonnes par glisser-déposer ;
- définir puis supprimer un alias ;
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

## Transmettre le résultat

- session globalement réussie : utilisez **[Partager un retour de bêta](https://github.com/Ducrosr/Dofus-Retro-64-Window-Manager/issues/new?template=beta_feedback.yml)** ;
- problème précis et reproductible : utilisez **[Signaler un bug](https://github.com/Ducrosr/Dofus-Retro-64-Window-Manager/issues/new?template=bug_report.yml)** ;
- idée d'ergonomie : utilisez **[Proposer une amélioration](https://github.com/Ducrosr/Dofus-Retro-64-Window-Manager/issues/new?template=feature_request.yml)** ;
- vulnérabilité ou doute de sécurité : suivez [SECURITY.md](../SECURITY.md) sans publier de détail sensible.

Le rapport de diagnostic peut contenir des noms de personnages et des chemins locaux. Relisez-le avant de le publier.
