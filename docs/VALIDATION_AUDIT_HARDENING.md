# Validation — durcissement après audit technique

## Référence

- Base auditée : `0610ef1669567212a708a4724bc62716798044b7`.
- Cette base correspond à `main` et au tag public `v2.20.0-beta.6` au démarrage des travaux.
- Branche de correction : `fix/audit-hardening-beta7`.
- Pull Request : #10.
- Aucun tag, déploiement ou publication n'est inclus dans ce lot.

## Portée

Le lot couvre les neuf axes du handoff Astra :

1. pompe Tk / réarmement du refresh ;
2. blocage des mutations après début de fermeture ;
3. propriété explicite et cycle de vie des surfaces OBS ;
4. coordonnées virtuelles négatives ;
5. identité et revalidation des HWND ;
6. rejet des scans/événements périmés par génération ;
7. suppression des doubles effets Stream Deck ;
8. protection des backups et schémas futurs ;
9. générations du watcher Retro facultatif.

## Validation automatisée

Un premier passage GitHub Actions de la PR #10 a réellement exécuté les runners Windows et a trouvé quatre problèmes de test/intégration :

- deux compatibilités de tests construisant partiellement `WindowManagerApp` ;
- une attente de test incorrecte qui supprimait le placeholder fixe `-2` du Stream Deck ;
- une propriété de paramètre TypeScript non supportée par le mode strip-only de Node 24.

Ces quatre points ont été corrigés sans modifier le comportement fonctionnel demandé.

Le second passage automatisé est en cours sur le code corrigé. Les résultats définitifs doivent être consignés ici avant fusion.

## Ce que les tests automatisés ne valident pas

Même si la suite mockée réussit, elle ne constitue pas une validation réelle de :

- la politique de focus imposée par Windows ;
- Dofus Unity ou Dofus Retro réels ;
- la stabilité d'une source Window Capture OBS déjà configurée ;
- un Stream Deck physique ou une différence réelle de niveau de privilèges ;
- les dispositions multi-écrans/DPI physiques ;
- la bibliothèque `windows-capture` sur un build facultatif réel.

La campagne correspondante est détaillée dans `docs/BETA_TESTING.md`.

## Packaging

Le build principal doit être vérifié avec le workflow existant ou localement avant fusion.

Le watcher visuel Retro reste facultatif. Son build doit être validé séparément avec `build_exe.py --with-popup` et la version exacte de `windows-capture` réellement installée doit être relevée. Les dépendances popup ne doivent pas être ajoutées au build principal.
