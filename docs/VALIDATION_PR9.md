# Validation — fiabilisation PR #9

Base auditée : `0610ef1669567212a708a4724bc62716798044b7` (`main` et `v2.20.0-beta.6` au démarrage).

Cette PR est un lot de correction et de validation. Elle n'est pas une release et ne publie aucun artefact.

## Portée

Le lot couvre :

- pompe Tk et réarmement des scans après exception ;
- arrêt et annulation des mutations différées ;
- cycle de vie des fenêtres OBS et séparation simulation/production ;
- coordonnées négatives absolues multi-écran ;
- identité/revalidation HWND avant focus ;
- générations de scan et de hook Win32 ;
- sémantique de timeout des commandes Stream Deck non idempotentes ;
- sauvegarde Settings/Profile et schémas futurs ;
- générations des captures du watcher Retro facultatif.

## Validation automatisée

Les workflows GitHub exécutent :

- suite Python complète ;
- Ruff ;
- tests du plugin Stream Deck ;
- typecheck TypeScript ;
- build, validation et packaging du plugin ;
- build PyInstaller principal ;
- build PyInstaller `--with-popup` dans un environnement séparé ;
- relevé de la version effectivement résolue de `windows-capture`.

### Résultats

À compléter à partir du head final de la PR.

Un premier passage intermédiaire a confirmé le succès complet du job Stream Deck, puis a révélé trois régressions de fixtures/détection Python. Elles ont été corrigées avant la validation finale. Ce passage intermédiaire ne constitue pas le résultat final.

## Validation réelle non couverte par les mocks

Les tests automatisés ne valident pas réellement :

- le comportement Win32 de focus sur des clients Dofus réels ;
- le refus de focus par Windows selon les niveaux de privilège ;
- la stabilité de Window Capture dans OBS ;
- le comportement de huit clients Unity/Retro ;
- les topologies multi-écrans/DPI réelles ;
- la détection visuelle d'une invitation Retro avec une fenêtre de jeu réelle ;
- le matériel Stream Deck.

La campagne à réaliser avant une prochaine bêta est décrite dans `BETA_TESTING.md`.

## Critères avant fusion

- [ ] suite Python finale réussie ;
- [ ] Ruff final réussi ;
- [ ] tests Stream Deck réussis ;
- [ ] typecheck/build/validate/pack Stream Deck réussis ;
- [ ] build principal PyInstaller réussi ;
- [ ] build popup facultatif PyInstaller réussi ;
- [ ] version `windows-capture` du build facultatif consignée ;
- [ ] aucune régression détectée lors de la revue statique du diff ;
- [ ] PR maintenue sans tag, release ou déploiement.

## Critères avant publication d'une prochaine bêta

En plus de la validation automatisée :

- [ ] essai Windows de focus actif/minimisé/refusé ;
- [ ] scan pendant Combobox et arrêt sous rafale ;
- [ ] essais Unity et Retro avec 0, 1 et 8 clients ;
- [ ] essais OBS de stabilité des deux fenêtres capturables ;
- [ ] essais Stream Deck avec backend absent/redémarré et requête retardée ;
- [ ] essais écran gauche/haut, déconnexion et DPI mixtes ;
- [ ] essai du watcher Retro facultatif avec invitations réelles.

Un élément non essayé doit rester indiqué comme **non testé**, jamais comme validé.
